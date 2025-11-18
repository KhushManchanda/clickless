"""
Planner agent:

Takes a natural-language user query (plus optional chat history)
and returns a BuyingGuidePlan.

Uses Chat Completions with JSON mode.
"""

import json
from typing import Dict, Any, List, Optional

from ..config import PLANNER_MODEL, DEFAULT_MIN_REVIEWS, DEFAULT_BUDGET_FLEX_PCT
from ..models import BuyingGuidePlan
from .client import get_openai_client


def _build_planner_user_message(
    user_query: str, chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Build the content for the user message sent to the planner LLM.

    If chat_history is provided, we treat the latest query as a refinement
    of the previous conversation.
    """
    if not chat_history:
        # Simple, single-turn prompt
        return user_query

    # Convert chat history into a simple text transcript
    lines = []
    for m in chat_history:
        role = m.get("role", "user")
        content = m.get("content", "")
        # Just a loose transcript for context
        lines.append(f"{role}: {content}")

    history_text = "\n".join(lines)

    # Tell the planner to interpret the conversation as a whole,
    # with the latest user_query as a refinement.
    return (
        "Conversation so far:\n"
        f"{history_text}\n\n"
        "User's latest message (a refinement of the above):\n"
        f"{user_query}\n\n"
        "Your task: infer the user's CURRENT headphone shopping request as a single, "
        "coherent set of preferences (budget, use_case, aspects, etc.) and output only "
        "a single JSON object describing that plan."
    )


def plan_from_query(
    user_query: str, chat_history: Optional[List[Dict[str, str]]] = None
) -> BuyingGuidePlan:
    """
    Call the planner LLM to convert the latest user message (plus optional
    chat history) into a structured BuyingGuidePlan.
    """
    client = get_openai_client()

    system_prompt = """
You are the Planner agent for a headphone buying guide.

Your job:
- Read the user's query about headphones.
- Possibly use earlier conversation turns as context (for refinements like
  "make it wireless", "raise budget to 100", "same as before but for gym").
- Infer the CURRENT desired specification:
  - budget (numeric, or null if no obvious budget)
  - a reasonable budget_flex_pct (0.2–0.5)
  - min_reviews (e.g., 10–50 depending on how strict the user seems)
  - use_case: commute, gym, audiophile, gaming, or general
  - priority_aspects: e.g., "bass", "comfort", "noise_cancelling", "battery", "mic_quality"
  - must_have_keywords: hard textual constraints (e.g., "noise cancelling") that MUST appear
  - boost_keywords: soft textual hints that SHOULD influence ranking
  - notes: short natural language explanation of how you interpreted the request.

Output rules:
- You MUST output **only** a single JSON object matching this structure:

{
  "budget": number or null,
  "budget_flex_pct": number,
  "min_reviews": integer,
  "use_case": "commute" | "gym" | "audiophile" | "gaming" | "general",
  "priority_aspects": [string, ...],
  "must_have_keywords": [string, ...],
  "boost_keywords": [string, ...],
  "notes": string
}

- Do not wrap it in any extra text.
- Do not include comments.
"""

    user_content = _build_planner_user_message(user_query, chat_history)

    resp = client.chat.completions.create(
        model=PLANNER_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    content = resp.choices[0].message.content
    raw_plan: Dict[str, Any] = json.loads(content)

    # Basic safety defaults
    if raw_plan.get("min_reviews") is None:
        raw_plan["min_reviews"] = DEFAULT_MIN_REVIEWS
    if raw_plan.get("budget_flex_pct") is None:
        raw_plan["budget_flex_pct"] = DEFAULT_BUDGET_FLEX_PCT

    return BuyingGuidePlan.from_llm_dict(user_query, raw_plan)
