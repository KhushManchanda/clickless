"""
Explainer agent:

Takes user query + plan + ranked products, and returns a
natural-language explanation of recommendations.

Uses Chat Completions API.
"""

import json
from typing import List

from ..config import EXPLAINER_MODEL, MAX_PRODUCTS_FOR_EXPLAINER
from ..models import BuyingGuidePlan, RankedProduct
from .client import get_openai_client


def explain_recommendations(
    user_query: str, plan: BuyingGuidePlan, products: List[RankedProduct]
) -> str:
    """
    Ask the Explainer LLM to generate a conversational answer based on
    the top-ranked products.
    """
    client = get_openai_client()

    simple_products = []
    for p in products[:MAX_PRODUCTS_FOR_EXPLAINER]:
        m = p.metadata
        simple_products.append(
            {
                "asin": m.asin,
                "title": p.title,
                "price": m.price,
                "avg_rating": m.avg_rating_from_reviews or m.meta_average_rating,
                "review_count": m.review_count,
                "sample_pros": m.sample_pros[:3],
                "sample_cons": m.sample_cons[:3],
                "score": p.score,
            }
        )

    system_prompt = """
You are the Explainer agent for a headphone buying guide.

You will receive:
- The original user query
- A structured plan describing budget, use_case, and aspects
- A small list of candidate products with price, rating, review_count, pros/cons, and a score

Your job:
- Briefly restate what the user is looking for.
- Recommend 3–5 products in an ordered list.
- For each, mention:
  - price and how it fits the budget
  - rating + review_count
  - 1–2 key pros (from sample_pros)
  - 1 key tradeoff or con (from sample_cons) if available
- End with a short guidance like:
  - "If you want maximum value, pick #1; if you care more about comfort, #2", etc.

Keep it concise and friendly. Do NOT invent products; only use the ones given.
"""

    user_payload = {
        "user_query": user_query,
        "plan": plan.to_dict(),
        "products": simple_products,
    }

    resp = client.chat.completions.create(
        model=EXPLAINER_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
    )

    return resp.choices[0].message.content
