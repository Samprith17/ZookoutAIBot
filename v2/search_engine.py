"""Version 2 search engine for structured deals."""
from typing import List

from v2.models import Deal, SearchRequest, SearchResult


class SearchEngine:
    def __init__(self, deals: List[Deal]):
        self.deals = deals

    def rank(self, request: SearchRequest) -> List[SearchResult]:
        results: List[SearchResult] = []
        for deal in self.deals:
            score = self._score(deal, request)
            if score > 0:
                results.append(SearchResult(deal=deal, score=score))

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:3]

    def _score(self, deal: Deal, request: SearchRequest) -> float:
        score = 0.0
        if request.category and request.category.lower() == deal.category.lower():
            score += 40
        if request.brand and request.brand.lower() in deal.brand.lower():
            score += 30
        if request.query.lower() in deal.title.lower():
            score += 25
        if any(tag.lower() in deal.tags for tag in request.tags):
            score += 20
        if any(keyword.lower() in deal.keywords for keyword in request.tags):
            score += 18
        if request.location and request.location.lower() in deal.location.lower():
            score += 15
        if request.max_price and deal.price > 0 and deal.price <= request.max_price:
            score += 10
        if request.min_discount and deal.discount_percent >= request.min_discount:
            score += 10
        if request.query.lower() in deal.description.lower():
            score += 12
        return score
