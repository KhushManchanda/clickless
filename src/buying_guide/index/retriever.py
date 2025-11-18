"""
High-level retrieval: filter + score + sort.
"""

from typing import List

from ..models import BuyingGuidePlan, ProductDocument, RankedProduct
from .loader import load_index
from .filters import filter_candidates
from .scoring import base_score, aspect_score, to_ranked


def retrieve_ranked_products(
    plan: BuyingGuidePlan, top_k: int = 5, products: List[ProductDocument] | None = None
) -> List[RankedProduct]:
    """
    Full retrieval pipeline:
    - load index (if not given)
    - apply filters
    - compute scores
    - return top_k ranked products
    """
    if products is None:
        products = load_index()

    candidates = filter_candidates(products, plan)

    scored: List[RankedProduct] = []
    for p in candidates:
        bs = base_score(p, plan)
        ks = aspect_score(p, plan)
        scored.append(to_ranked(p, bs, ks))

    scored.sort(key=lambda rp: rp.score, reverse=True)
    return scored[:top_k]
