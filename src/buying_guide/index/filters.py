"""
Filtering logic for candidate products based on the plan.
"""

from typing import List

from ..models import BuyingGuidePlan, ProductDocument


def _combined_text(p: ProductDocument) -> str:
    m = p.metadata
    parts = [p.text or ""]
    parts.extend(m.sample_pros or [])
    parts.extend(m.sample_cons or [])
    return " ".join(parts).lower()


def filter_candidates(
    products: List[ProductDocument], plan: BuyingGuidePlan
) -> List[ProductDocument]:
    """
    Apply filtering based on budget, min_reviews, and must-have keywords.
    """
    budget = plan.budget
    flex = plan.budget_flex_pct
    min_reviews = plan.min_reviews
    must_keywords = [kw.lower() for kw in plan.must_have_keywords]

    if budget:
        low = budget * (1.0 - flex)
        high = budget * (1.0 + flex)
    else:
        low = high = None

    candidates: List[ProductDocument] = []

    for p in products:
        m = p.metadata
        price = m.price
        review_count = m.review_count

        if price is None or review_count < min_reviews:
            continue

        if low is not None and (price < low or price > high):
            continue

        if must_keywords:
            text = _combined_text(p)
            if not any(kw in text for kw in must_keywords):
                continue

        candidates.append(p)

    return candidates
