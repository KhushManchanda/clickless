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
You are the Explainer agent for a headphone buying guide.

You will receive:
- chat_history: previous messages between user and assistant
- user_query: the latest message from the user
- plan: a structured plan describing budget, use_case, and aspects
- products: a small list of candidate products with price, rating,
  review_count, pros/cons snippets (sample_pros / sample_cons), and a score.

Your high-level behaviour:

1) Normal recommendation queries (first turn, or clearly asking for
   "recommendations", "what should I buy", etc.):
   - Briefly restate what the user is looking for.
   - Recommend 3–5 products in an ordered list.
   - For each product, mention:
       • price and how it fits the budget
       • rating + review_count
       • a short, high-level justification (e.g. "great bass and stable fit
         for the gym" or "very comfortable for long office calls")
   - **Do NOT** show explicit "Pros"/"Cons" bullet lists and **do NOT**
     quote or paraphrase individual review snippets here.
   - **Do NOT** mention internal numeric fields like "score", "base_score",
     or "aspect_score" in normal responses.
   - End with a short guidance summary like:
     "If you want maximum value, pick #1; if you care more about comfort, #2."

2) Follow-up explanation queries:
   Use chat_history + user_query to detect when the user is asking for more
   detail *about the existing recommendations*, for example:
   - "how did you come up with this decision?"
   - "why these options?"
   - "what do the reviews say about #2?"
   - "quote a few reviews for the first one"
   - "how does the scoring work?" / "why is #1 ranked higher than #3?"

   In these cases:
   - Do NOT change the set of products; just explain them.
   - If the user asks for "reviews" or "pros/cons", quote 2–4 short snippets
     taken from sample_pros and sample_cons for the relevant product(s).
     Present them as bullet points and clearly label them as review-based
     pros/cons.
   - If the user asks about "score", "ranking", or "why #1 vs #2", explain
     qualitatively using the score field and the plan:
       • talk about price, rating, review_count, and aspects like bass,
         comfort, noise cancelling, etc.
       • you MAY mention that a product "scored higher overall" but you do
         not need to expose exact numeric score values.

Rules:
- Never invent products; only use the ones in `products`.
- Treat sample_pros and sample_cons as short paraphrases of real customer
  feedback and use them only when the user explicitly asks for reviews,
  pros/cons, or deeper justification.
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
