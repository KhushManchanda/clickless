"""
Global configuration for the buying_guide package.
Edit this file to change paths, model names, and scoring weights.
"""

from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Index paths
AGGREGATED_INDEX_PATH = DATA_DIR / "headphones_aggregated_index.jsonl"

# OpenAI models
PLANNER_MODEL = "gpt-4.1-mini"
EXPLAINER_MODEL = "gpt-4.1-mini"

# Default retrieval options
DEFAULT_MIN_REVIEWS = 10
DEFAULT_BUDGET_FLEX_PCT = 0.3  # ±30%

# Scoring weights
PRICE_WEIGHT = 0.5
RATING_WEIGHT = 0.35
POPULARITY_WEIGHT = 0.15
ASPECT_WEIGHT = 0.3        # fraction of final score contributed by aspect match
BASE_SCORE_WEIGHT = 0.7    # fraction from base score (1 - ASPECT_WEIGHT)

# Misc
MAX_PRODUCTS_FOR_EXPLAINER = 5