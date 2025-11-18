"""
Global configuration for the buying_guide package.

Edit this file to change:
- paths to data files
- model names
- scoring weights
"""

from pathlib import Path

# ---------- Paths ----------

# project root = two levels up from this file (…/src/buying_guide/config.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Aggregated headphone index (the one you built earlier)
AGGREGATED_INDEX_PATH = DATA_DIR / "headphones_aggregated_index.jsonl"

# ---------- OpenAI models ----------

# LLM used for planning (intent → JSON plan)
PLANNER_MODEL = "gpt-4.1-mini"

# LLM used for explanation (pros/cons, reasoning text)
EXPLAINER_MODEL = "gpt-4.1-mini"

# ---------- Retrieval defaults ----------

# Minimum number of reviews a product must have to be considered
DEFAULT_MIN_REVIEWS = 10

# How far from the budget we allow (±30% by default)
DEFAULT_BUDGET_FLEX_PCT = 0.3

# ---------- Scoring weights ----------

# Weights for base_score components
PRICE_WEIGHT = 0.5
RATING_WEIGHT = 0.35
POPULARITY_WEIGHT = 0.15

# How much of the final score comes from:
#   - base score (price + rating + popularity)
#   - aspect score (keyword match for user prefs)
BASE_SCORE_WEIGHT = 0.7
ASPECT_WEIGHT = 0.3

# ---------- Explainer ----------

# How many top products we pass into the Explainer LLM
MAX_PRODUCTS_FOR_EXPLAINER = 5
