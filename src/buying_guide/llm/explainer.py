"""
Explainer agent:

Takes user query + plan + products (+ optional chat history),
and returns a natural-language explanation of recommendations.

Uses Chat Completions API.
"""

import json
from typing import List, Dict, Optional, Any

from ..config import EXPLAINER_MODEL, MAX_PRODUCTS_FOR_EXPLAINER
from ..models import BuyingGuidePlan
from .client import get_openai_client


def _normalize_products_for_explainer(
    products: List[Any],
) -> List[Dict[str, Any]]:
    """
    Accept either a list of RankedProduct objects OR a list of already-simple
    product dicts, and return a uniform list of simple dicts.
    """
    simple: List[Dict[str, Any]] = []

    if not products:
        return simple

    # If these look like RankedProduct instances (have .metadata), convert them.
    first = products[0]
    if hasattr(first, "metadata"):
        from ..models import RankedProduct  # type: ignore

        for p in products[:MAX_PRODUCTS_FOR_EXPLAINER]:
            if not isinstance(p, RankedProduct):
                continue
            m = p.metadata
            simple.append(
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
    else:
        # Assume they're already the compact dict form used by the app
        for p in products[:MAX_PRODUCTS_FOR_EXPLAINER]:
            if not isinstance(p, dict):
                continue
            simple.append(
                {
                    "asin": p.get("asin"),
                    "title": p.get("title"),
                    "price": p.get("price"),
                    "avg_rating": p.get("avg_rating"),
                    "review_count": p.get("review_count"),
                    "sample_pros": (p.get("sample_pros") or [])[:3],
                    "sample_cons": (p.get("sample_cons") or [])[:3],
                    "score": p.get("score"),
                }
            )

    return simple


def explain_recommendations(
    user_query: str,
    plan: BuyingGuidePlan,
    products: List[Any],
    chat_history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Ask the Explainer LLM to generate a conversational answer based on
    the products plus the user's latest message.

    chat_history lets the explainer handle follow-ups such as:
    - "how did you come up with this decision?"
    - "give me 5 more options"
    - "quote a few reviews for #2"
    """
    client = get_openai_client()

    simple_products = _normalize_products_for_explainer(products)

    system_prompt = """
You are a concise, witty headphone expert. Be helpful, straight to the point, and occasionally charming.

TONE RULES:
- Be conversational and natural, like a knowledgeable friend
- Add subtle wit when appropriate (not forced)
- NO emojis
- Be direct - get to the point quickly
- Use short sentences and paragraphs

INPUT:
- chat_history: previous conversation
- user_query: latest user message
- plan: structured preferences (budget, use_case, aspects)
- products: candidate headphones with price, rating, reviews, pros/cons

RESPONSE PATTERNS:

1) INITIAL RECOMMENDATIONS:
   - One line summarizing what they want
   - List 3 products, each with:
     **Product Name** — $price
     Rating: X.X / 5.0 (N reviews)
     Why: One punchy sentence on why it fits
   
   - End with quick guidance (1 sentence)
   - Keep it under 150 words total
   - NO pros/cons lists here
   - NO technical score mentions

2) "TELL ME MORE" QUERIES:
   - Focus on unique features they haven't seen
   - 2-3 short sentences max
   - Don't repeat price/rating unless comparing
   - Add personality: "This one's a crowd favorite" or "Battery life here is impressive"

3) REVIEW REQUESTS:
   Format as:
   **What customers love:**
   1. [snippet]
   2. [snippet]
   3. [snippet]
   
   **What they don't:**
   1. [snippet]
   2. [snippet]
   
   Keep snippets to one sentence each. Add a witty note if appropriate.

4) COMPARISONS:
   Create a simple table:
   
   | Feature | #1 | #2 |
   |---------|----|----|
   | Price | $X | $Y |
   | Rating | X.X | X.X |
   | Best For | [brief] | [brief] |
   
   End with: "Pick #1 if [reason]. Go with #2 if [reason]."

5) "WHY/HOW" QUESTIONS:
   - 2-3 sentences explaining the decision
   - Mention key factors (price, rating, fit to use-case)
   - Be direct, no fluff

CRITICAL RULES:
- BREVITY IS KEY - shorter is better
- Never repeat info from chat_history
- Recognize references: "#1", "first one", "the [name]"
- NO emojis anywhere
- Add subtle wit, not jokes
- Professional but friendly
- Get in, deliver value, get out
""".strip()

    user_payload = {
        "user_query": user_query,
        "plan": plan.to_dict(),
        "products": simple_products,
    }

    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # Include prior conversation so the explainer can handle follow-ups
    if chat_history:
        messages.extend(chat_history)

    messages.append(
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}
    )

    resp = client.chat.completions.create(
        model=EXPLAINER_MODEL,
        messages=messages,
    )

    return resp.choices[0].message.content
