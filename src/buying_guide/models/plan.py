from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class BuyingGuidePlan:
    """
    Structured representation of what the user is asking for.

    This is produced by the Planner LLM from a raw natural-language query.
    """
    raw_query: str
    budget: Optional[float]
    budget_flex_pct: float
    min_reviews: int
    use_case: str  # commute | gym | audiophile | gaming | general
    priority_aspects: List[str] = field(default_factory=list)
    must_have_keywords: List[str] = field(default_factory=list)
    boost_keywords: List[str] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_llm_dict(cls, raw_query: str, d: Dict[str, Any]) -> "BuyingGuidePlan":
        """Create a BuyingGuidePlan from a dict returned by the LLM."""
        return cls(
            raw_query=raw_query,
            budget=d.get("budget"),
            budget_flex_pct=float(d.get("budget_flex_pct", 0.3)),
            min_reviews=int(d.get("min_reviews", 10)),
            use_case=d.get("use_case", "general"),
            priority_aspects=list(d.get("priority_aspects") or []),
            must_have_keywords=list(d.get("must_have_keywords") or []),
            boost_keywords=list(d.get("boost_keywords") or []),
            notes=d.get("notes", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict (useful for logging / JSON)."""
        return {
            "raw_query": self.raw_query,
            "budget": self.budget,
            "budget_flex_pct": self.budget_flex_pct,
            "min_reviews": self.min_reviews,
            "use_case": self.use_case,
            "priority_aspects": self.priority_aspects,
            "must_have_keywords": self.must_have_keywords,
            "boost_keywords": self.boost_keywords,
            "notes": self.notes,
        }
