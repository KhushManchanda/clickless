"""
Scoring functions for ranking headphone products.
"""

import math
from typing import List

from ..config import (
    PRICE_WEIGHT,
    RATING_WEIGHT,
    POPULARITY_WEIGHT,
    BASE_SCORE_WEIGHT,
    ASPECT_WEIGHT,
)
from ..models import BuyingGuidePlan, ProductDocument, RankedProduct


def base_score(p: ProductDocument, plan: BuyingGuidePlan) -> float:
    """
    Compute a base score using:
    - price fit to budget
    - average rating
    - popularity (review_count)
    """
    m = p.metadata
    price = float(m.price or 0.0)
    review_count = int(m.review_count or 0)
    avg = m.avg_rating_from_reviews or m.meta_average_rating or 0.0
    budget = plan.budget

    # price fit
    if budget and budget > 0:
        rel = price / budget
        if rel <= 1.0:
            price_score = 1.0 - (1.0 - rel) ** 2
        else:
            over = rel - 1.0
            price_score = max(0.0, 1.0 - over * 1.2)
    else:
        price_score = 1.0

    # rating score
    try:
        avg_f = float(avg)
    except Exception:
        avg_f = 0.0
    rating_norm = (avg_f - 3.0) / 2.0  # 3→0, 5→1
    rating_score = max(0.0, min(1.0, rating_norm))

    # popularity score (log10)
    pop_score = math.log10(review_count + 1) / 4.0
    pop_score = max(0.0, min(1.0, pop_score))

    return (
        PRICE_WEIGHT * price_score
        + RATING_WEIGHT * rating_score
        + POPULARITY_WEIGHT * pop_score
    )


def aspect_score(p: ProductDocument, plan: BuyingGuidePlan) -> float:
    """
    Simple keyword-based aspect score based on boost_keywords.
    """
    boost_keywords = plan.boost_keywords
    if not boost_keywords:
        return 0.0

    m = p.metadata
    text_parts: List[str] = [p.text or ""]
    text_parts.extend(m.sample_pros or [])
    text_parts.extend(m.sample_cons or [])
    text = " ".join(text_parts).lower()

    hits = 0
    for kw in boost_keywords:
        if kw.lower() in text:
            hits += 1

    return hits / len(boost_keywords)


def combine_scores(base: float, aspect: float) -> float:
    """
    Combine base and aspect scores using weights from config.
    """
    return BASE_SCORE_WEIGHT * base + ASPECT_WEIGHT * aspect


def to_ranked(
    p: ProductDocument, base: float, aspect: float
) -> RankedProduct:
    """
    Wrap a ProductDocument with ranking attributes.
    """
    final = combine_scores(base, aspect)
    return RankedProduct(
        id=p.id,
        title=p.title,
        text=p.text,
        metadata=p.metadata,
        score=final,
        base_score=base,
        aspect_score=aspect,
    )
