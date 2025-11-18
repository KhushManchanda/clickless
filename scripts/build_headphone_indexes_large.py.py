import json
import os
import re
from typing import Dict, Any

# ---------- CONFIG: filenames for your big dataset ----------
META_PATH = "data/meta_Electronics.jsonl"
REVIEWS_PATH = "data/Electronics.jsonl"

OUT_PRODUCTS = "data/headphones_products_index.jsonl"
OUT_REVIEWS = "data/headphones_reviews_index.jsonl"
# ------------------------------------------------------------


def get_price(meta: Dict[str, Any]):
    """
    Extract a clean float price from the metadata.
    Returns:
      - float price if valid (> 0)
      - None otherwise (missing, invalid, or non-positive)
    """
    raw = meta.get("price")
    if raw is None:
        return None

    # Already numeric
    if isinstance(raw, (int, float)):
        price = float(raw)
        return price if price > 0 else None

    # String like "$19.99" or "19.99"
    if isinstance(raw, str):
        # Remove common currency symbols and thousands separators
        s = raw.replace(",", "")
        # Grab the first number-looking token
        m = re.search(r"[\d.]+", s)
        if not m:
            return None
        try:
            price = float(m.group(0))
            return price if price > 0 else None
        except ValueError:
            return None

    # Anything else we don't trust
    return None


def is_headphone(meta: Dict[str, Any]) -> bool:
    """
    Stricter heuristic:
      - Must LOOK like headphones/earbuds/headset in the title
      - Must be in headphone-ish categories
      - Must NOT look like a cable/adapter/case/watch/accessory
    """
    title = (meta.get("title") or "").lower()
    categories = [c.lower() for c in meta.get("categories", [])]
    details = meta.get("details") or {}
    details_text = " ".join(str(v) for v in details.values()).lower()

    # --- 1. Hard negative phrases (accessories / non-headphones) ---
    NEG_TITLE_PHRASES = [
        # cables & adapters
        "aux cable", "audio cable", "extension cable", "headphone cable",
        "replacement cable", "charging cable", "charging cord",
        "usb c to 3.5mm", "usb-c to 3.5mm", "to 3.5mm", "3.5mm male to male",
        "aux adapter", "audio adapter", "headphone adapter", "splitter",
        "y splitter", "converter",
        # cases & covers
        "phone case", "protective case", "cover case", "case for",
        "earbud case", "headphone case", "storage case", "bag for headphones",
        "pouch for headphones", "carrying case",
        # tips, cushions, hooks, pads
        "ear tips", "ear tip", "earbuds tips", "foam tips",
        "ear hooks", "earhooks", "ear hook", "ear cushions",
        "ear pads", "earpads", "ear pad", "replacement earpads",
        # stands, mounts, holders
        "headphone stand", "headset stand", "hanger", "mount",
        # watches & bands & straps
        "smart watch", "smartwatch", "watch band", "watch strap",
        "watch case",
        # random other accessories
        "screen protector", "protector for", "bumper case"
    ]

    if any(phrase in title for phrase in NEG_TITLE_PHRASES):
        return False

    HARD_NEG_WORDS = ["smart watch", "smartwatch", "phone case", "case for", "cover for"]
    if any(h in title for h in HARD_NEG_WORDS):
        return False

    # --- 2. Positive signals ---
    POS_TITLE_KWS = [
        "headphone", "headphones",
        "earbud", "earbuds",
        "earphone", "earphones",
        "over-ear", "over ear",
        "on-ear", "on ear",
        "in-ear", "in ear",
        "wireless earbuds", "true wireless", "tws earbuds",
        "gaming headset", "headset"
    ]

    POS_CAT_KWS = [
        "headphones", "headphone",
        "earbuds", "earbud",
        "earphones", "earphone"
    ]

    has_pos_title = any(kw in title for kw in POS_TITLE_KWS)

    cats_joined = " | ".join(categories)
    cat_has_headphone = any(kw in cats_joined for kw in POS_CAT_KWS)
    cat_is_obviously_cable_or_accessory = any(
        bad in cats_joined
        for bad in ["cables", "cable", "adapters", "adapter", "accessories", "cases", "covers"]
    )

    if cat_is_obviously_cable_or_accessory and not has_pos_title:
        # Something like "Cables" with no strong headphone words in title
        return False

    # Basic rule: needs positive title AND headphone-ish category
    if has_pos_title and cat_has_headphone and not cat_is_obviously_cable_or_accessory:
        return True

    # Fallback: title clearly headphone-ish and details mention "headphones"
    if has_pos_title and "headphone" in details_text:
        return True

    return False


def build_product_text(meta: Dict[str, Any]) -> str:
    """
    Build a single 'text' field for product index:
    - title
    - features
    - description
    (no reviews here, to keep it scalable)
    """
    title = meta.get("title") or ""
    features = " ".join(meta.get("features") or [])
    description = " ".join(meta.get("description") or [])

    parts = [title, features, description]
    parts = [p.strip() for p in parts if p and p.strip()]
    return ". ".join(parts)


def pass1_build_headphone_products(
    meta_path: str,
    out_products: str
) -> Dict[str, Dict[str, Any]]:
    """
    PASS 1:
      - Stream through metadata JSONL
      - Detect headphone products
      - REQUIRE a valid price
      - Write product index JSONL
      - Return dict {parent_asin: meta_obj} for priced headphones
    """
    headphones_meta: Dict[str, Dict[str, Any]] = {}
    count_all = 0
    count_headphones = 0

    with open(meta_path, "r", encoding="utf-8") as fin, \
         open(out_products, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            count_all += 1
            if count_all % 1_000_000 == 0:
                print(f"[PASS1] Processed {count_all} metadata lines...")

            try:
                meta = json.loads(line)
            except json.JSONDecodeError:
                continue

            asin = meta.get("parent_asin") or meta.get("asin")
            if not asin:
                continue

            # 1) Must be a headphone
            if not is_headphone(meta):
                continue

            # 2) Must have a valid price
            price = get_price(meta)
            if price is None:
                continue

            # Normalize price in-place so downstream uses float
            meta["price"] = price

            # store in memory for review filtering
            headphones_meta[asin] = meta
            count_headphones += 1

            # write product index doc
            text = build_product_text(meta)
            details = meta.get("details") or {}

            metadata = {
                "asin": asin,
                "main_category": meta.get("main_category"),
                "categories": meta.get("categories"),
                "price": price,
                "average_rating": meta.get("average_rating"),
                "rating_number": meta.get("rating_number"),
                "store": meta.get("store"),
                "images": meta.get("images"),  # 👈 NEW: carry image info forward
            }

            # merge details into metadata
            for k, v in details.items():
                if k not in metadata:
                    metadata[k] = v

            product_doc = {
                "id": asin,
                "title": meta.get("title"),
                "text": text,
                "metadata": metadata,
            }

            fout.write(json.dumps(product_doc) + "\n")

    print(f"[PASS1] Total metadata lines read: {count_all}")
    print(f"[PASS1] Priced headphone products found: {count_headphones}")
    print(f"[PASS1] Product index written to: {out_products}")
    print(f"[PASS1] Product index size: {os.path.getsize(out_products)} bytes")

    return headphones_meta


def pass2_build_headphone_reviews(
    reviews_path: str,
    out_reviews: str,
    headphones_meta: Dict[str, Dict[str, Any]],
) -> None:
    """
    PASS 2:
      - Stream through reviews JSONL
      - Keep only reviews where parent_asin is in priced headphone set
      - Write review docs with product metadata attached
    """
    valid_asins = set(headphones_meta.keys())
    count_all = 0
    count_kept = 0

    with open(reviews_path, "r", encoding="utf-8") as fin, \
         open(out_reviews, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            count_all += 1
            if count_all % 1_000_000 == 0:
                print(f"[PASS2] Processed {count_all} review lines...")

            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue

            parent = r.get("parent_asin") or r.get("asin")
            if parent not in valid_asins:
                continue

            meta = headphones_meta[parent]
            product_title = meta.get("title")
            product_price = meta.get("price")  # normalized float
            product_categories = meta.get("categories")

            review_text = (r.get("text") or "").strip()
            if not review_text:
                continue

            rating = r.get("rating")
            review_doc = {
                "id": f"{parent}__{count_kept}",
                "parent_asin": parent,
                "asin": r.get("asin"),
                "rating": rating,
                "title": r.get("title"),
                "text": review_text,
                "metadata": {
                    "parent_asin": parent,
                    "asin": r.get("asin"),
                    "product_title": product_title,
                    "product_price": product_price,
                    "product_categories": product_categories,
                    "helpful_vote": r.get("helpful_vote"),
                    "verified_purchase": r.get("verified_purchase"),
                    "timestamp": r.get("timestamp"),
                },
            }

            fout.write(json.dumps(review_doc) + "\n")
            count_kept += 1

    print(f"[PASS2] Total review lines read: {count_all}")
    print(f"[PASS2] Headphone reviews kept (priced products only): {count_kept}")
    print(f"[PASS2] Review index written to: {out_reviews}")
    print(f"[PASS2] Review index size: {os.path.getsize(out_reviews)} bytes")


def main():
    # PASS 1: metadata -> priced headphone products + product index
    headphones_meta = pass1_build_headphone_products(
        meta_path=META_PATH,
        out_products=OUT_PRODUCTS,
    )

    if not headphones_meta:
        print("[WARN] No priced headphone products detected. Review index will be empty.")
        return

    # PASS 2: reviews -> headphone-only review index
    pass2_build_headphone_reviews(
        reviews_path=REVIEWS_PATH,
        out_reviews=OUT_REVIEWS,
        headphones_meta=headphones_meta,
    )


if __name__ == "__main__":
    main()
