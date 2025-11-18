import json
import os
from collections import defaultdict

PRODUCTS_PATH = "data/headphones_products_index.jsonl"
REVIEWS_PATH = "data/headphones_reviews_index.jsonl"
OUT_PATH      = "data/headphones_aggregated_index.jsonl"

# How many pros / cons snippets to keep per product
MAX_PROS_PER_PRODUCT = 5
MAX_CONS_PER_PRODUCT = 5


def load_products(path):
    """
    Load product docs from headphones_products_index.jsonl into a dict:
      { asin: product_doc }
    """
    products = {}
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            doc = json.loads(line)
            asin = doc["metadata"].get("asin")
            if not asin:
                continue
            products[asin] = doc
            count += 1
    print(f"[AGG] Loaded headphone products (priced): {count}")
    return products


def init_agg():
    """Create an empty aggregation structure for a product."""
    return {
        "review_count": 0,
        "rating_sum": 0.0,
        "rating_hist": {str(i) for i in range(1, 6)},  # placeholder, we’ll override
        "pros": [],  # list of (rating, helpful_vote, text)
        "cons": []   # list of (rating, helpful_vote, text)
    }


def make_empty_hist():
    return {str(i): 0 for i in range(1, 6)}


def maybe_add_snippet(bucket, rating, helpful, text, max_size):
    """
    Maintain a small list of "best" snippets by helpful_vote.
    Simple approach:
      - append until full
      - then replace the lowest-helpful snippet if the new one is more helpful
    """
    if len(bucket) < max_size:
        bucket.append((rating, helpful or 0, text))
        return

    # Find the snippet with min helpful
    min_idx = None
    min_helpful = None
    for i, (_, h, _) in enumerate(bucket):
        if min_helpful is None or (h or 0) < min_helpful:
            min_helpful = h or 0
            min_idx = i

    if (helpful or 0) > (min_helpful or 0):
        bucket[min_idx] = (rating, helpful or 0, text)


def aggregate_reviews(products, reviews_path):
    """
    Stream through reviews and aggregate per parent_asin.
    Returns:
      aggs: { asin: agg_data }
      total_reviews_used: int
    """
    aggs = {}
    count_all = 0
    count_used = 0

    with open(reviews_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            count_all += 1
            if count_all % 1_000_000 == 0:
                print(f"[AGG] Processed {count_all} reviews...")

            r = json.loads(line)
            parent = r.get("parent_asin")
            if parent not in products:
                continue

            rating = r.get("rating")
            if rating is None:
                continue

            try:
                rating_f = float(rating)
            except Exception:
                continue

            # clamp to 1–5 for histogram
            r_int = int(round(rating_f))
            if r_int < 1 or r_int > 5:
                continue

            text = (r.get("text") or "").strip()
            if not text:
                continue

            helpful = r.get("helpful_vote") or 0

            if parent not in aggs:
                aggs[parent] = {
                    "review_count": 0,
                    "rating_sum": 0.0,
                    "rating_hist": make_empty_hist(),
                    "pros": [],
                    "cons": []
                }

            agg = aggs[parent]
            agg["review_count"] += 1
            agg["rating_sum"] += rating_f
            agg["rating_hist"][str(r_int)] += 1

            # Heuristic for pros/cons
            if r_int >= 4:
                maybe_add_snippet(agg["pros"], r_int, helpful, text, MAX_PROS_PER_PRODUCT)
            elif r_int <= 2:
                maybe_add_snippet(agg["cons"], r_int, helpful, text, MAX_CONS_PER_PRODUCT)

            count_used += 1

    print(f"[AGG] Total reviews read: {count_all}")
    print(f"[AGG] Reviews used for aggregation: {count_used}")
    print(f"[AGG] Headphones with ≥1 review: {len(aggs)}")

    # Average reviews per headphone (only those with at least one review)
    if aggs:
        avg_reviews_per_headphone = count_used / len(aggs)
        print(f"[AGG] Average reviews per headphone (with ≥1 review): {avg_reviews_per_headphone:.2f}")
    else:
        print("[AGG] No headphones had reviews; average reviews per headphone = 0")

    return aggs, count_used


def write_aggregated_index(products, aggs, out_path):
    """
    Combine product docs + aggregated review stats into a new index.
    Only write products that have at least one review.
    """
    with open(out_path, "w", encoding="utf-8") as f:
        written = 0

        for asin, agg in aggs.items():
            product = products.get(asin)
            if not product:
                continue

            review_count = agg["review_count"]
            if review_count == 0:
                continue

            avg_rating_from_reviews = agg["rating_sum"] / review_count
            rating_hist = agg["rating_hist"]

            # Sort pros by (rating desc, helpful desc)
            pros = [
                t for _, _, t in
                sorted(agg["pros"], key=lambda x: (-(x[0]), -(x[1] or 0)))
            ]
            # Sort cons by (rating asc, helpful desc)
            cons = [
                t for _, _, t in
                sorted(agg["cons"], key=lambda x: (x[0], -(x[1] or 0)))
            ]

            meta = product["metadata"]
            meta_avg = meta.get("average_rating")
            meta_count = meta.get("rating_number")

            out_doc = {
                "id": asin,
                "title": product.get("title"),
                "text": product.get("text"),
                "metadata": {
                    **meta,
                    "review_count": review_count,
                    "avg_rating_from_reviews": avg_rating_from_reviews,
                    "rating_hist": rating_hist,
                    "meta_average_rating": meta_avg,
                    "meta_rating_number": meta_count,
                    "sample_pros": pros,
                    "sample_cons": cons
                }
            }

            f.write(json.dumps(out_doc) + "\n")
            written += 1

    print(f"[AGG] Wrote aggregated index to: {out_path}")
    print(f"[AGG] Headphones written (with ≥1 review): {written}")
    print(f"[AGG] Aggregated index size: {os.path.getsize(out_path)} bytes")


def main():
    products = load_products(PRODUCTS_PATH)
    aggs, total_reviews_used = aggregate_reviews(products, REVIEWS_PATH)
    write_aggregated_index(products, aggs, OUT_PATH)


if __name__ == "__main__":
    main()
