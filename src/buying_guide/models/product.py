from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class RatingHistogram:
    """
    Histogram of star ratings for a product (1–5).
    """
    one_star: int = 0
    two_star: int = 0
    three_star: int = 0
    four_star: int = 0
    five_star: int = 0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RatingHistogram":
        return cls(
            one_star=int(d.get("1", 0)),
            two_star=int(d.get("2", 0)),
            three_star=int(d.get("3", 0)),
            four_star=int(d.get("4", 0)),
            five_star=int(d.get("5", 0)),
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            "1": self.one_star,
            "2": self.two_star,
            "3": self.three_star,
            "4": self.four_star,
            "5": self.five_star,
        }


@dataclass
class ProductMetadata:
    """
    Core metadata for a headphone product as used during retrieval.
    """
    asin: str
    main_category: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    price: Optional[float] = None
    average_rating: Optional[float] = None
    rating_number: Optional[int] = None
    store: Optional[str] = None
    review_count: int = 0
    avg_rating_from_reviews: Optional[float] = None
    rating_hist: RatingHistogram = field(default_factory=RatingHistogram)
    meta_average_rating: Optional[float] = None
    meta_rating_number: Optional[int] = None
    sample_pros: List[str] = field(default_factory=list)
    sample_cons: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, meta: Dict[str, Any]) -> "ProductMetadata":
        hist = meta.get("rating_hist") or {}
        extra_keys = {
            "asin",
            "main_category",
            "categories",
            "price",
            "average_rating",
            "rating_number",
            "store",
            "review_count",
            "avg_rating_from_reviews",
            "rating_hist",
            "meta_average_rating",
            "meta_rating_number",
            "sample_pros",
            "sample_cons",
        }

        extra = {k: v for k, v in meta.items() if k not in extra_keys}
        return cls(
            asin=meta.get("asin"),
            main_category=meta.get("main_category"),
            categories=list(meta.get("categories") or []),
            price=meta.get("price"),
            average_rating=meta.get("average_rating"),
            rating_number=meta.get("rating_number"),
            store=meta.get("store"),
            review_count=int(meta.get("review_count", 0)),
            avg_rating_from_reviews=meta.get("avg_rating_from_reviews"),
            rating_hist=RatingHistogram.from_dict(hist),
            meta_average_rating=meta.get("meta_average_rating"),
            meta_rating_number=meta.get("meta_rating_number"),
            sample_pros=list(meta.get("sample_pros") or []),
            sample_cons=list(meta.get("sample_cons") or []),
            extra=extra,
        )

    def to_json(self) -> Dict[str, Any]:
        base = {
            "asin": self.asin,
            "main_category": self.main_category,
            "categories": self.categories,
            "price": self.price,
            "average_rating": self.average_rating,
            "rating_number": self.rating_number,
            "store": self.store,
            "review_count": self.review_count,
            "avg_rating_from_reviews": self.avg_rating_from_reviews,
            "rating_hist": self.rating_hist.to_dict(),
            "meta_average_rating": self.meta_average_rating,
            "meta_rating_number": self.meta_rating_number,
            "sample_pros": self.sample_pros,
            "sample_cons": self.sample_cons,
        }
        base.update(self.extra)
        return base


@dataclass
class ProductDocument:
    """
    Full product document as stored in headphones_aggregated_index.jsonl.
    """
    id: str
    title: str
    text: str
    metadata: ProductMetadata

    @classmethod
    def from_json(cls, d: Dict[str, Any]) -> "ProductDocument":
        return cls(
            id=d.get("id"),
            title=d.get("title") or "",
            text=d.get("text") or "",
            metadata=ProductMetadata.from_json(d.get("metadata") or {}),
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "metadata": self.metadata.to_json(),
        }


@dataclass
class RankedProduct(ProductDocument):
    """
    Product extended with scoring information.
    """
    score: float = 0.0
    base_score: float = 0.0
    aspect_score: float = 0.0
