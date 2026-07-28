import logging
import datetime
import random
from typing import Dict, List, Any
import urllib.parse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from v2.ai.profile import profile_manager

logger = logging.getLogger(__name__)

# User Favourites Storage: user_id -> deal_id -> deal_dict
USER_FAVOURITES: Dict[int, Dict[int, Dict[str, Any]]] = {}

# User Search Cache for Pagination: user_id -> List[deal_dict]
USER_SEARCH_CACHE: Dict[int, List[Dict[str, Any]]] = {}


def save_favourite(user_id: int, deal: Dict[str, Any]) -> bool:
    """Save deal to user favourites & update profile."""
    if user_id not in USER_FAVOURITES:
        USER_FAVOURITES[user_id] = {}

    deal_id = deal.get("id")
    if deal_id in USER_FAVOURITES[user_id]:
        return False

    USER_FAVOURITES[user_id][deal_id] = deal
    profile_manager.update_profile_from_favourite(user_id, deal)
    return True


def remove_favourite(user_id: int, deal_id: int) -> bool:
    """Remove deal from user favourites."""
    if user_id in USER_FAVOURITES and deal_id in USER_FAVOURITES[user_id]:
        del USER_FAVOURITES[user_id][deal_id]
        return True
    return False


def clear_favourites(user_id: int) -> bool:
    """Clear all favourites for a user."""
    if user_id in USER_FAVOURITES:
        USER_FAVOURITES[user_id].clear()
        return True
    return False


def get_favourites(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve list of user favourites."""
    if user_id in USER_FAVOURITES:
        return list(USER_FAVOURITES[user_id].values())
    return []


def build_deal_keyboard(deal: Dict[str, Any], is_favourite: bool = False) -> InlineKeyboardMarkup:
    """Builds interactive inline keyboard for a single deal with Voucher Assistant button."""
    deal_id = deal.get("id")
    website = deal.get("website", "https://zookout.com")
    brand = deal.get("brand", "Zookout Merchant")
    title = deal.get("clean_title", deal.get("title", "Special Deal"))
    price = deal.get("formatted_price", "Price not available")
    discount = deal.get("discount_percent", 0)

    # Telegram Share URL
    share_text = f"Check out this deal on Zookout!\n\n🏷️ Brand: {brand}\n📝 Offer: {title}\n💰 Price: {price}\n🎁 Discount: {discount}%"
    encoded_text = urllib.parse.quote(share_text)
    encoded_url = urllib.parse.quote(website)
    share_url = f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"

    buttons = []

    # Row 1: View Deal & Share Deal
    row1 = [InlineKeyboardButton("🔗 View Deal", url=website), InlineKeyboardButton("📤 Share", url=share_url)]
    buttons.append(row1)

    # Row 2: Save / Remove Favourite & Voucher Assistant Button
    row2 = []
    if is_favourite:
        row2.append(InlineKeyboardButton("❌ Remove", callback_data=f"fav_remove:{deal_id}"))
    else:
        row2.append(InlineKeyboardButton("❤️ Save", callback_data=f"fav_save:{deal_id}"))

    row2.append(InlineKeyboardButton("🎟️ Generate Voucher", callback_data=f"voucher_generate:{deal_id}"))
    buttons.append(row2)

    return InlineKeyboardMarkup(buttons)


def build_pagination_keyboard(offset: int) -> InlineKeyboardMarkup:
    """Builds 'Show More Deals' button keyboard."""
    buttons = [[InlineKeyboardButton("🔄 Show More Deals", callback_data=f"more:{offset}")]]
    return InlineKeyboardMarkup(buttons)


def build_confirm_clear_keyboard() -> InlineKeyboardMarkup:
    """Builds confirmation buttons for clearing all favourites."""
    buttons = [
        [
            InlineKeyboardButton("⚠️ Yes, Clear All", callback_data="fav_clear_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="fav_clear_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def build_confirm_reset_profile_keyboard() -> InlineKeyboardMarkup:
    """Builds confirmation buttons for resetting user profile."""
    buttons = [
        [
            InlineKeyboardButton("⚠️ Yes, Reset Profile", callback_data="profile_reset_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="profile_reset_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback Query Handler for Inline Buttons (Including Voucher Generation)."""
    query = update.callback_query
    if not query:
        return

    user_id = query.from_user.id if query.from_user else update.effective_user.id
    data = query.data or ""

    # 1. Save Favourite
    if data.startswith("fav_save:"):
        deal_id = int(data.split(":")[1])
        cached_deals = USER_SEARCH_CACHE.get(user_id, [])
        target_deal = next((d for d in cached_deals if d.get("id") == deal_id), None)

        if target_deal:
            saved = save_favourite(user_id, target_deal)
            if saved:
                await query.answer(text="❤️ Saved to your Favourites!", show_alert=False)
            else:
                await query.answer(text="Already in your Favourites!", show_alert=False)
        else:
            await query.answer(text="Unable to save deal.", show_alert=False)
        return

    # 2. Remove Favourite
    if data.startswith("fav_remove:"):
        deal_id = int(data.split(":")[1])
        removed = remove_favourite(user_id, deal_id)
        if removed:
            await query.answer(text="❌ Removed from Favourites!", show_alert=False)
            if query.message:
                await query.message.edit_text("❌ This deal has been removed from your favourites.")
        else:
            await query.answer(text="Deal not found in favourites.", show_alert=False)
        return

    # 3. Voucher Assistant: Generate Voucher Code
    if data.startswith("voucher_generate:"):
        deal_id = int(data.split(":")[1])
        cached_deals = USER_SEARCH_CACHE.get(user_id, [])
        target_deal = next((d for d in cached_deals if d.get("id") == deal_id), None)

        if not target_deal:
            # Fallback to search if not in search cache
            from v2.search.search_engine import load_deals, normalize_deal
            all_deals = load_deals()
            target = next((d for d in all_deals if d.get("id") == deal_id), None)
            if target:
                target_deal = normalize_deal(target)

        if target_deal:
            code_num = random.randint(100000, 999999)
            voucher_code = f"ZK-{code_num}"
            expiry = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%d %b %Y")

            brand = target_deal.get("brand", "Zookout Merchant")
            offer = target_deal.get("clean_title", target_deal.get("title", "Special Offer"))
            price = target_deal.get("formatted_price", "Price unavailable")
            disc = target_deal.get("discount_percent", 0)
            loc = target_deal.get("display_location", "Mumbai")

            voucher_msg = (
                "🎟️ ZOOKOUT DIGITAL DEAL VOUCHER\n\n"
                f"🎫 Voucher Code: {voucher_code}\n"
                f"🏷️ Brand: {brand}\n"
                f"📝 Offer: {offer}\n"
                f"💰 Special Price: {price} (Save {disc}% OFF)\n"
                f"📍 Redemption Location: {loc}\n"
                f"⏰ Valid Until: {expiry}\n\n"
                "👉 Present this digital voucher at venue redemption!"
            )
            await query.answer(text="🎟️ Voucher Generated Successfully!", show_alert=False)
            if query.message:
                await query.message.reply_text(voucher_msg)
        else:
            await query.answer(text="Unable to generate voucher.", show_alert=False)
        return

    # 4. Pagination - Show More Deals
    if data.startswith("more:"):
        offset = int(data.split(":")[1])
        cached_deals = USER_SEARCH_CACHE.get(user_id, [])

        if not cached_deals or offset >= len(cached_deals):
            await query.answer(text="No more deals available!", show_alert=False)
            return

        await query.answer()

        next_batch = cached_deals[offset : offset + 4]
        next_offset = offset + 4

        for deal in next_batch:
            profile_manager.add_recently_viewed(user_id, deal)
            title = deal.get("clean_title", deal.get("title", ""))
            reply = (
                f"🏷️ Brand: {deal.get('brand', 'N/A')}\n"
                f"📂 Category: {deal.get('display_category', 'N/A')}\n"
                f"📝 Offer: {title}\n"
                f"💰 Price: {deal.get('formatted_price', 'Price not available')}\n"
                f"🎁 Discount: {deal.get('discount_percent', 0)}%\n"
                f"📍 Location: {deal.get('display_location')}\n"
            )
            keyboard = build_deal_keyboard(deal)
            await query.message.reply_text(reply, reply_markup=keyboard, disable_web_page_preview=True)

        if next_offset < len(cached_deals):
            p_keyboard = build_pagination_keyboard(next_offset)
            await query.message.reply_text(
                f"Showing deals {offset + 1}-{min(next_offset, len(cached_deals))} of {len(cached_deals)}. Click below for more!",
                reply_markup=p_keyboard,
            )
        else:
            await query.message.reply_text("✅ All matching deals have been displayed!")
        return

    # 5. Clear Favourites Confirmation
    if data == "fav_clear_confirm":
        clear_favourites(user_id)
        await query.answer(text="🗑️ All favourites cleared!", show_alert=False)
        if query.message:
            await query.message.edit_text("🗑️ All your saved favourites have been cleared.")
        return

    if data == "fav_clear_cancel":
        await query.answer(text="Cancelled.", show_alert=False)
        if query.message:
            await query.message.edit_text("Action cancelled. Your favourites are safe.")
        return

    # 6. Profile Reset Confirmation
    if data == "profile_reset_confirm":
        profile_manager.reset_profile(user_id)
        await query.answer(text="🗑️ Profile reset!", show_alert=False)
        if query.message:
            await query.message.edit_text("🗑️ Your preferences and search history have been cleared.")
        return

    if data == "profile_reset_cancel":
        await query.answer(text="Cancelled.", show_alert=False)
        if query.message:
            await query.message.edit_text("Action cancelled. Your profile preferences are intact.")
        return
