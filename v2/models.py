"""Data models for Version 2 of Zookout AI deal search."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Deal:
    id: int
    brand: str
    merchant: str
    category: str
    title: str
    offer: str
    description: str
    price: int
    original_price: int
    discount_percent: int
    location: str
    website: str
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class SearchRequest:
    query: str
    category: str = ""
    brand: str = ""
    max_price: int = 0
    min_discount: int = 0
    location: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    deal: Deal
    score: float
