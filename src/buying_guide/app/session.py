"""
Session orchestration: one full "turn" of the buying guide.
"""

from typing import Dict, Any, List, Optional

from ..models import BuyingGuidePlan, RankedProduct
from ..llm import plan_from_query, explain_recommendations
from ..index import load_index
from ..index.retriever import retrieve_ranked_products


def _extract_image_url(rp: RankedProduct) -> Optional[str]:
    """
    Try to extract a representative image URL from metadata, if available.

    Assumes that any `images` field (if present) follows the structure from
    the original metadata:
      images: [{ "hi_res": ..., "large": ..., "thumb": ... }, ...]
    """
    # Extra fields preserved from original metadata
    extra = rp.metadata.extra or {}

    images = extra.get("images") or extra.get("Images") or []
    if not isinstance(images, list):
        return None

    for img in images:
        if not isinstance(img, dict):
            continue
        url = img.get("hi_res") or img.get("large") or img.get("thumb")
        if url:
            return url

    return None


def run_agentic_session(
    user_query: str,
    top_k: int = 5,
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Orchestrate a full agentic cycle:

    - Planner LLM → BuyingGuidePlan (using optional chat_history for refinements)
    - Retriever → top_k RankedProduct
    - Explainer LLM → answer text
    """
    # Plan
    plan: BuyingGuidePlan = plan_from_query(user_query, chat_history=chat_history)

    # Retrieve
    products = load_index()
    ranked: List[RankedProduct] = retrieve_ranked_products(
        plan, top_k=top_k, products=products
    )

    # Explain
    answer: str = explain_recommendations(user_query, plan, ranked)

    # Shape a lightweight product list for UI / API
    product_payload = []
    for p in ranked:
        image_url = _extract_image_url(p)
        product_payload.append(
            {
                "title": p.title,
                "price": p.metadata.price,
                "avg_rating": p.metadata.avg_rating_from_reviews
                or p.metadata.meta_average_rating,
                "review_count": p.metadata.review_count,
                "asin": p.metadata.asin,
                "score": p.score,
                "base_score": p.base_score,
                "aspect_score": p.aspect_score,
                "image_url": image_url,
            }
        )

    return {
        "plan": plan.to_dict(),
        "products": product_payload,
        "answer": answer,
    }
