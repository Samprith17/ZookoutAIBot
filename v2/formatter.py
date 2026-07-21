"""Formatter for Version 2 Telegram deal cards."""
import html
from typing import Dict


def format_deal_card(deal: Dict[str, object]) -> str:
    lines = [
        "━━━━━━━━━━━━━━━━━━",
        "",
        "🏢 Brand",
        html.escape(str(deal.get("brand", "Unknown"))),
        "",
        "📂 Category",
        html.escape(str(deal.get("category", ""))),
        "",
        "🎁 Offer",
        html.escape(str(deal.get("title", "Deal"))),
        "",
        "💰 Price",
        f"₹{deal.get('price', 0)}",
    ]

    discount = deal.get("discount_percent", 0)
    if discount:
        lines.extend(["", "🎉 Discount", f"{discount}%"])

    lines.extend([
        "",
        "📍 Location",
        html.escape(str(deal.get("location", ""))),
        "",
        "🔗 Website",
        html.escape(str(deal.get("website", ""))),
        "",
        "━━━━━━━━━━━━━━━━━━",
    ])

    return "\n".join(lines)
