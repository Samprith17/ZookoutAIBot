"""Filter definitions for Version 2 search requests."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SearchFilters:
    category: str = ""
    brand: str = ""
    max_price: int = 0
    min_discount: int = 0
    location: str = ""
    tags: List[str] = field(default_factory=list)


def build_search_request(query: str, filters: SearchFilters):
    return {
        "query": query,
        "category": filters.category,
        "brand": filters.brand,
        "max_price": filters.max_price,
        "min_discount": filters.min_discount,
        "location": filters.location,
        "tags": filters.tags,
    }
