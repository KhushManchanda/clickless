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


def _build_simple_products(ranked: List[RankedProduct]) -> List[Dict[str, Any]]:
    """
    Build the compact product representation used by the explainer.

    NOTE: This is *not* the full metadata; only the fields the explainer needs.
    """
    simple_products: List[Dict[str, Any]] = []
    for p in ranked:
        m = p.metadata
        simple_products.append(
            {
                "asin": m.asin,
                "title": p.title,
                "price": m.price,
                "avg_rating": m.avg_rating_from_reviews or m.meta_average_rating,
                "review_count": m.review_count,
                "sample_pros": (m.sample_pros or [])[:3],
                "sample_cons": (m.sample_cons or [])[:3],
                "score": p.score,
            }
        )
    return simple_products


def run_agentic_session(
    user_query: str,
    top_k: int = 5,
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Orchestrate a full agentic cycle for an *initial* recommendation query:

    - Planner LLM → BuyingGuidePlan (using optional chat_history for refinements)
    - Retriever → top_k RankedProduct
    - Explainer LLM → answer text

    This function *also* returns a compact product list for the explainer so
    that follow-up questions can reuse the same products without re-ranking.
    """
    # Plan
    plan: BuyingGuidePlan = plan_from_query(user_query, chat_history=chat_history)

    # Retrieve
    products = load_index()
    ranked: List[RankedProduct] = retrieve_ranked_products(
        plan, top_k=top_k, products=products
    )

    # Compact list for explainer (pros/cons, score, etc.)
    explainer_products: List[Dict[str, Any]] = _build_simple_products(ranked)

    # Natural-language answer
    answer: str = explain_recommendations(
        user_query,
        plan,
        explainer_products,
        chat_history=chat_history,
    )

    # Shape a lightweight product list for UI / API cards
    product_payload: List[Dict[str, Any]] = []
    for p, sp in zip(ranked, explainer_products):
        image_url = _extract_image_url(p)
        product_payload.append(
            {
                "title": p.title,
                "price": sp["price"],
                "avg_rating": sp["avg_rating"],
                "review_count": sp["review_count"],
                "asin": sp["asin"],
                "score": sp["score"],
                "base_score": p.base_score,
                "aspect_score": p.aspect_score,
                "image_url": image_url,
                # keep pros/cons around for follow-ups, even if UI doesn't show them
                "sample_pros": sp.get("sample_pros") or [],
                "sample_cons": sp.get("sample_cons") or [],
            }
        )

    return {
        "plan": plan.to_dict(),
        "products": product_payload,
        "answer": answer,
        # extra field used for follow-up turns (no new retrieval)
        "explainer_products": explainer_products,
    }


def continue_agentic_session(
    user_query: str,
    last_result: Dict[str, Any],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Handle a *follow-up* user message without changing the underlying
    recommendations.

    We:
    - Rebuild a BuyingGuidePlan object from last_result["plan"]
    - Reuse last_result["explainer_products"] (same products / scores)
    - Call the explainer again with updated chat_history

    Returned structure mirrors run_agentic_session so the UI code can treat
    both paths uniformly.
    """
    plan_dict = last_result.get("plan") or {}
    explainer_products = last_result.get("explainer_products") or []

    # Reconstruct a BuyingGuidePlan from the stored dict
    plan = BuyingGuidePlan.from_llm_dict(
        raw_query=plan_dict.get("raw_query", user_query),
        d=plan_dict,
    )

    answer: str = explain_recommendations(
        user_query,
        plan,
        explainer_products,
        chat_history=chat_history,
    )

    # Do *not* change products or plan – keep them stable for the conversation
    return {
        "plan": plan_dict,
        "products": last_result.get("products") or [],
        "answer": answer,
        "explainer_products": explainer_products,
    }
