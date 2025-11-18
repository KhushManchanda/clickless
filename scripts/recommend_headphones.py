import json
import math
import argparse
from typing import List, Dict, Any

INDEX_PATH = "headphones_aggregated_index.jsonl"

MIN_REVIEWS_DEFAULT = 10   # ignore super low-signal products by default


def load_index(path: str) -> List[Dict[str, Any]]:
    products = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            products.append(json.loads(line))
    print(f"[INFO] Loaded products with reviews: {len(products)}")
    return products


def filter_candidates(products: List[Dict[str, Any]],
                      budget: float,
                      span_lower: float = 0.5,
                      span_upper: float = 1.5,
                      min_reviews: int = MIN_REVIEWS_DEFAULT) -> List[Dict[str, Any]]:
    """
    Keep products whose price is within [budget * span_lower, budget * span_upper]
    and with at least min_reviews.
    """
    low = budget * span_lower
    high = budget * span_upper

    candidates = []
    for p in products:
        m = p["metadata"]
        price = m.get("price")
        rc = m.get("review_count", 0)
        if price is None:
            continue
        if price < low or price > high:
            continue
        if rc < min_reviews:
            continue
        candidates.append(p)

    print(
        f"[INFO] Candidates in price window [{low:.2f}, {high:.2f}] "
        f"and ≥{min_reviews} reviews: {len(candidates)}"
    )
    return candidates


def score_product(p: Dict[str, Any], budget: float) -> float:
    """
    Heuristic scoring:
      - price_score: closer to budget, slightly biased to <= budget
      - rating_score: from avg_rating_from_reviews (fallback to meta_average_rating)
      - popularity_score: log-scaled review_count

    Returns a number ~0–1 (not strictly bounded but roughly).
    """
    m = p["metadata"]
    price = float(m["price"])
    review_count = int(m.get("review_count", 0) or 0)
    avg = m.get("avg_rating_from_reviews") or m.get("meta_average_rating") or 0.0

    # --- price_score ---
    # relative price to budget
    if budget > 0:
        rel = price / budget
    else:
        rel = 1.0

    if rel <= 1.0:
        # Cheaper than or equal to budget, closer is better
        price_score = 1.0 - (1.0 - rel) ** 2  # 1 at rel=1, dropping smoothly towards 0
    else:
        # Above budget: penalize harder the farther above
        over = rel - 1.0
        price_score = max(0.0, 1.0 - over * 1.2)

    # --- rating_score ---
    # map 3–5 stars → 0–1; below 3 is 0 or negative, clamp
    try:
        avg_f = float(avg)
    except Exception:
        avg_f = 0.0
    rating_norm = (avg_f - 3.0) / 2.0  # 3→0, 5→1
    rating_score = max(0.0, min(1.0, rating_norm))

    # --- popularity_score ---
    # log-scaled review count, ~0–1 for typical ranges
    pop_score = math.log10(review_count + 1) / 4.0  # 10k→1, 100→0.5-ish
    pop_score = max(0.0, min(1.0, pop_score))

    # Weighted sum – tweak weights as you like
    return 0.5 * price_score + 0.35 * rating_score + 0.15 * pop_score


def rank_products(candidates: List[Dict[str, Any]], budget: float, top_k: int) -> List[Dict[str, Any]]:
    scored = []
    for p in candidates:
        s = score_product(p, budget)
        scored.append((s, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]
    print(f"[INFO] Returning top {len(top)} products by score.")
    # attach score to each product for display
    return [{"score": s, **p} for (s, p) in top]


def print_recommendations(results: List[Dict[str, Any]], budget: float):
    if not results:
        print("No recommendations found for this budget / filters.")
        return

    print("\n" + "=" * 80)
    print(f"Top {len(results)} recommendations around budget ${budget:.2f}")
    print("=" * 80)

    for idx, res in enumerate(results, start=1):
        title = res.get("title", "")[:160]
        m = res["metadata"]
        price = m.get("price")
        avg = m.get("avg_rating_from_reviews") or m.get("meta_average_rating")
        rc = m.get("review_count", m.get("meta_rating_number"))
        score = res["score"]

        print("\n" + "-" * 80)
        print(f"#{idx}  {title}")
        print(f"    Price: ${price:.2f} | Avg rating: {avg:.2f} | Reviews: {rc} | Score: {score:.3f}")
        print(f"    ASIN: {m.get('asin')} | Brand: {m.get('Brand', m.get('store'))}")
        cats = m.get("categories") or []
        if cats:
            print(f"    Categories: {', '.join(cats)}")

        pros = (m.get("sample_pros") or [])[:2]
        cons = (m.get("sample_cons") or [])[:2]

        if pros:
            print("    Pros:")
            for ptxt in pros:
                one_line = ptxt.replace("\n", " ").replace("<br />", " ").replace("<br/>", " ")
                print(f"      • {one_line[:200]}{'...' if len(one_line) > 200 else ''}")

        if cons:
            print("    Cons:")
            for ctxt in cons:
                one_line = ctxt.replace("\n", " ").replace("<br />", " ").replace("<br/>", " ")
                print(f"      • {one_line[:200]}{'...' if len(one_line) > 200 else ''}")


def main():
    parser = argparse.ArgumentParser(description="Recommend headphones based on budget using aggregated index.")
    parser.add_argument("--budget", type=float, required=True, help="Target budget in USD (e.g., 50)")
    parser.add_argument("--top_k", type=int, default=5, help="Number of recommendations to show")
    parser.add_argument("--min_reviews", type=int, default=MIN_REVIEWS_DEFAULT,
                        help="Minimum number of reviews per product")
    parser.add_argument("--span_lower", type=float, default=0.5,
                        help="Lower multiplier for price window (default 0.5*budget)")
    parser.add_argument("--span_upper", type=float, default=1.5,
                        help="Upper multiplier for price window (default 1.5*budget)")

    args = parser.parse_args()

    products = load_index(INDEX_PATH)

    candidates = filter_candidates(
        products,
        budget=args.budget,
        span_lower=args.span_lower,
        span_upper=args.span_upper,
        min_reviews=args.min_reviews
    )

    results = rank_products(candidates, budget=args.budget, top_k=args.top_k)
    print_recommendations(results, budget=args.budget)


if __name__ == "__main__":
    main()
