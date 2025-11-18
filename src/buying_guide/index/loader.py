"""
Functions for loading the aggregated headphone index from disk.
"""

import json
from functools import lru_cache
from typing import List

from ..config import AGGREGATED_INDEX_PATH
from ..models import ProductDocument


@lru_cache(maxsize=1)
def load_index(path: str | None = None) -> List[ProductDocument]:
    """
    Load the aggregated headphone index into memory.

    Uses an LRU cache so repeated calls are cheap.
    """
    index_path = AGGREGATED_INDEX_PATH if path is None else path
    products: List[ProductDocument] = []

    with open(index_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            products.append(ProductDocument.from_json(data))

    return products
