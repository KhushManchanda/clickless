import json
import os

# --------- CONFIG: change paths as needed ----------
META_PATH = "meta_Electronic_sample_1000.jsonl"
REVIEWS_PATH = "Electronic_sample_1000.jsonl"

OUT_PRODUCTS = "headphones_products_index.jsonl"
OUT_REVIEWS = "headphones_reviews_index.jsonl"
# --------------------------------------------------


def is_headphone(meta: dict) -> bool:
    """
    Decide if a product is a headphone / earbud / headset based on
    title, categories and details. This is a heuristic filter and
    is designed to be robust when you scale to millions of lines.
    """
    title = (meta.get("title") or "").lower()
    categories = [c.lower() for c in meta.get("categories", [])]
    details = meta.get("details") or {}
    details_text = " ".join(str(v) for v in details.values()).lower()

    keywords = ["headphone", "headphones",
                "earbud", "earbuds",
                "headset", "earphones", "ear phones"]

    def has_kw(text: str) -> bool:
        return any(kw in text for kw in keywords)

    # match in title
    if has_kw(title):
        return True

    # match in categories
    if any(has_kw(c) for c in categories):
        return True

    # match in details (e.g. “Form Factor: Over-Ear Headphones”)
    if has_kw(details_text):
        return True

    return False


def build_product_search_text(meta: dict, reviews: list) -> str:
    """
    Build a single 'text' field that we can use later for embeddings / search:
    - title
    - features
    - description
    - (optionally) a few review snippets
    """
    title = meta.get("title") or ""
    features = " ".join(meta.get("features") or [])
    description = " ".join(meta.get("description") or [])

    # a few review snippets if available
    review_snips = " ".join((r.get("text") or "") for r in (reviews or [])[:5])

    parts = [title, features, description, review_snips]
    parts = [p.strip() for p in parts if p and p.strip()]
    return ". ".join(parts)


def load_headphone_metadata(meta_path: str) -> dict:
    """
    Read metadata JSONL and return a dict:
        { parent_asin: meta_object }
    only for headphone products.
    """
    headphones_meta = {}

    with open(meta_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            asin = item.get("parent_asin") or item.get("asin")
            if not asin:
                continue

            if is_headphone(item):
                headphones_meta[asin] = item

    print(f"[INFO] Headphone products found: {len(headphones_meta)}")
    return headphones_meta


def group_reviews_by_parent_asin(reviews_path: str, valid_asins: set) -> dict:
    """
    Read reviews JSONL and keep only those whose parent_asin is
    in valid_asins (i.e., headphone products). Returns:
        { parent_asin: [review1, review2, ...] }
    """
    reviews_by_asin = {asin: [] for asin in valid_asins}

    with open(reviews_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue

            parent = r.get("parent_asin") or r.get("asin")
            if parent in reviews_by_asin:
                reviews_by_asin[parent].append(r)

    num_prods_with_reviews = sum(1 for rs in reviews_by_asin.values() if rs)
    total_reviews = sum(len(rs) for rs in reviews_by_asin.values())

    print(f"[INFO] Headphone products with ≥1 review: {num_prods_with_reviews}")
    print(f"[INFO] Total headphone reviews found: {total_reviews}")

    return reviews_by_asin


def write_indexes(
    headphones_meta: dict,
    reviews_by_asin: dict,
    out_products: str,
    out_reviews: str
) -> None:
    """
    Produce two JSONL files:
      - out_products: product-level docs (for retrieval / ranking)
      - out_reviews: review-level docs (for sentiment / aspect work)
    """

    with open(out_products, "w", encoding="utf-8") as f_prod, \
         open(out_reviews, "w", encoding="utf-8") as f_rev:

        for parent_asin, meta in headphones_meta.items():
            reviews = reviews_by_asin.get(parent_asin, [])

            # Build product doc
            text = build_product_search_text(meta, reviews)

            details = meta.get("details") or {}

            metadata = {
                "asin": parent_asin,
                "main_category": meta.get("main_category"),
                "categories": meta.get("categories"),
                "price": meta.get("price"),
                "average_rating": meta.get("average_rating"),
                "rating_number": meta.get("rating_number"),
                "store": meta.get("store"),
                # 👇 NEW: carry images through so UI can show thumbnails
                "images": meta.get("images"),
            }

            # Merge 'details' into metadata, without overwriting keys
            for k, v in details.items():
                if k not in metadata:
                    metadata[k] = v

            product_doc = {
                "id": parent_asin,
                "title": meta.get("title"),
                "text": text,
                "metadata": metadata
            }
            f_prod.write(json.dumps(product_doc) + "\n")

            # Build review docs for this product
            for idx, r in enumerate(reviews):
                review_text = (r.get("text") or "").strip()
                if not review_text:
                    continue

                review_doc = {
                    "id": f"{parent_asin}__{idx}",
                    "parent_asin": parent_asin,
                    "asin": r.get("asin"),
                    "rating": r.get("rating"),
                    "title": r.get("title"),
                    "text": review_text,
                    "metadata": {
                        "parent_asin": parent_asin,
                        "asin": r.get("asin"),
                        "product_title": meta.get("title"),
                        "product_price": meta.get("price"),
                        "product_categories": meta.get("categories"),
                        "helpful_vote": r.get("helpful_vote"),
                        "verified_purchase": r.get("verified_purchase"),
                        "timestamp": r.get("timestamp"),
                    }
                }

                f_rev.write(json.dumps(review_doc) + "\n")

    print(f"[INFO] Wrote product index to: {out_products}")
    print(f"[INFO] Wrote review index to:  {out_reviews}")
    print(f"[INFO] Product index size: {os.path.getsize(out_products)} bytes")
    print(f"[INFO] Review index size:  {os.path.getsize(out_reviews)} bytes")


def main():
    # 1) Load headphone metadata from sample meta file
    headphones_meta = load_headphone_metadata(META_PATH)

    if not headphones_meta:
        print("[WARN] No headphone products detected in metadata sample.")
        return

    # 2) Group reviews by parent_asin, only for those headphone products
    valid_asins = set(headphones_meta.keys())
    reviews_by_asin = group_reviews_by_parent_asin(REVIEWS_PATH, valid_asins)

    # 3) Write the two JSONL indexes
    write_indexes(headphones_meta, reviews_by_asin, OUT_PRODUCTS, OUT_REVIEWS)


if __name__ == "__main__":
    main()
