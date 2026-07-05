
import asyncio
import time
import math
import json
import os
import sys
import traceback
import logging
from datetime import datetime, timedelta

# â”€â”€ Setup Logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SkullAdsBot")

# â”€â”€ Event Loop Fix â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# â”€â”€ Pyrogram Imports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from pyrogram import Client, filters, idle
    from pyrogram.types import (
        InlineKeyboardMarkup, InlineKeyboardButton,
        Message, CallbackQuery
    )
    from pyrogram.errors import (
        SessionPasswordNeeded, ChatWriteForbidden,
        SlowmodeWait, FloodWait, UserBannedInChannel,
        MessageNotModified, AuthKeyUnregistered,
        PeerIdInvalid, ChannelPrivate, UserNotParticipant,
        BadRequest, Forbidden, RPCError
    )
    from pyrogram.enums import ParseMode, ChatType, ChatMemberStatus
except ImportError:
    logger.error("Pyrogram not installed! Run: pip install pyrogram tgcrypto")
    sys.exit(1)

# â”€â”€ Phone Number Validation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import phonenumbers
    from phonenumbers import NumberParseException
    PHONENUMBERS_AVAILABLE = True
    logger.info("phonenumbers library loaded successfully.")
except ImportError:
    PHONENUMBERS_AVAILABLE = False
    logger.warning("phonenumbers not installed. Basic validation only. Run: pip install phonenumbers")

# â”€â”€ DNS Bypass â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import dns.resolver
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']
    logger.info("DNS bypass configured successfully.")
except ImportError:
    logger.warning("dnspython not installed. DNS bypass skipped.")
except Exception as e:
    logger.warning(f"DNS bypass failed: {e}")


# =====================================================
# âš™ï¸ CONFIGURATION â€” Load from Environment Variables
# =====================================================
API_ID = int(os.getenv("API_ID", "38010847"))
API_HASH = os.getenv("API_HASH", "0c7305952c10ae2ac8b61c9546777fcb")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8254602786:AAE5rVEVEuRCV_cadKDZq-WOfdHWELlQDPI")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "7423951207")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

# Validate required config
_missing = []
if not API_ID:
    _missing.append("API_ID")
if not API_HASH:
    _missing.append("API_HASH")
if not BOT_TOKEN:
    _missing.append("BOT_TOKEN")
if _missing:
    logger.critical(f"Missing required environment variables: {', '.join(_missing)}")
    sys.exit(1)

BOT_USERNAME = "SkullAdsBot"
BOT_VERSION = "3.0"
BOT_START_TIME = time.time()

# â”€â”€ Plan Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
PLANS = {
    "free": {
        "name": "ðŸ†“ Free",
        "accounts": 1,
        "price": "Free",
        "max_targets": 50,
        "max_rounds": 5,
        "priority": 0
    },
    "basic": {
        "name": "âš¡ Basic",
        "accounts": 3,
        "price": "â‚¹99/month",
        "max_targets": 200,
        "max_rounds": 50,
        "priority": 1
    },
    "pro": {
        "name": "ðŸ’Ž Pro",
        "accounts": 10,
        "price": "â‚¹249/month",
        "max_targets": 1000,
        "max_rounds": 500,
        "priority": 2
    },
    "elite": {
        "name": "ðŸ‘‘ Elite",
        "accounts": 999,
        "price": "â‚¹499/month",
        "max_targets": 99999,
        "max_rounds": 99999,
        "priority": 3
    },
}

FREE_ACCOUNT_LIMIT = 1

# â”€â”€ Bot Client â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
bot = Client(
    "SkullAdsBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)


# =====================================================
# ðŸ’¾ JSON STORAGE ENGINE â€” Thread-Safe
# =====================================================
DATA_FILE = "data.json"
DATA_LOCK = asyncio.Lock()

DEFAULT_DATA = {
    "users": {},
    "accounts": {},
    "campaigns": {},
    "stats": {},
    "banned_users": [],
    "premium_users": {},
    "active_account": {},
    "referrals": {},
    "notifications": {},
    "admin_logs": [],
    "settings": {
        "maintenance_mode": False,
        "lifetime_logins": 0,
        "lifetime_logouts": 0,
        "total_broadcasts": 0,
        "total_bans": 0,
        "total_unbans": 0,
        "bot_start_count": 0,
        "last_backup": "",
        "auto_backup": True,
        "max_free_targets": 50,
        "welcome_message": "",
        "force_join_channel": "",
        "global_ad_footer": "",
        "rate_limit_seconds": 5
    }
}


def load_data() -> dict:
    """Load data from JSON file with full validation."""
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA.copy())
        return DEFAULT_DATA.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                save_data(DEFAULT_DATA.copy())
                return DEFAULT_DATA.copy()
            loaded = json.loads(content)

        # Deep merge with defaults
        for key in DEFAULT_DATA:
            if key not in loaded:
                loaded[key] = (
                    DEFAULT_DATA[key].copy()
                    if isinstance(DEFAULT_DATA[key], (dict, list))
                    else DEFAULT_DATA[key]
                )

        # Ensure settings keys
        if isinstance(loaded.get("settings"), dict):
            for skey in DEFAULT_DATA["settings"]:
                if skey not in loaded["settings"]:
                    loaded["settings"][skey] = DEFAULT_DATA["settings"][skey]
        else:
            loaded["settings"] = DEFAULT_DATA["settings"].copy()

        # Ensure banned_users is a list
        if not isinstance(loaded.get("banned_users"), list):
            loaded["banned_users"] = []

        # Convert banned_users to int list
        loaded["banned_users"] = [
            int(b) for b in loaded["banned_users"]
            if str(b).lstrip('-').isdigit()
        ]

        return loaded
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        backup_file = DATA_FILE + ".backup"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    recovered = json.load(f)
                logger.info("Recovered data from backup file.")
                return recovered
            except Exception as be:
                logger.error(f"Backup recovery failed: {be}")
        return DEFAULT_DATA.copy()
    except Exception as e:
        logger.error(f"Load data error: {e}")
        return DEFAULT_DATA.copy()


def save_data(data: dict) -> bool:
    """Save data to JSON file with backup."""
    try:
        # Create backup before saving
        if os.path.exists(DATA_FILE):
            try:
                backup_file = DATA_FILE + ".backup"
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    old_content = f.read()
                if old_content.strip():
                    with open(backup_file, "w", encoding="utf-8") as f:
                        f.write(old_content)
            except Exception as be:
                logger.warning(f"Backup creation warning: {be}")

        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        os.replace(temp_file, DATA_FILE)
        return True
    except Exception as e:
        logger.error(f"Save data error: {e}")
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e2:
            logger.error(f"Fallback save error: {e2}")
            return False


def get_data() -> dict:
    """Get current data (sync)."""
    return load_data()


def update_data(data: dict) -> bool:
    """Update data file (sync)."""
    return save_data(data)


async def async_get_data() -> dict:
    """Get data with async lock to prevent race conditions."""
    async with DATA_LOCK:
        return load_data()


async def async_update_data(data: dict) -> bool:
    """Update data with async lock to prevent race conditions."""
    async with DATA_LOCK:
        return save_data(data)


# =====================================================
# ðŸ› ï¸ GLOBAL STATE MANAGEMENT
# =====================================================
user_state = {}
active_tasks = {}
rate_limit_tracker = {}
command_cooldowns = {}


# =====================================================
# ðŸ“± PHONE NUMBER & OTP HELPERS
# =====================================================
# =====================================================
# ðŸ“± PHONE NUMBER & OTP HELPERS â€” BULLETPROOF
# =====================================================
def normalize_phone_number(raw: str) -> tuple:
    """
    Normalize phone number to E.164 format.
    Returns (normalized_number, error_message)
    normalized_number is None if invalid.
    """
    if not raw:
        return None, "âŒ Please send your phone number."

    cleaned = raw.strip()

    if PHONENUMBERS_AVAILABLE:
        try:
            # Try multiple parse strategies
            parsed = None

            # Strategy 1: Direct parse with +
            if cleaned.startswith("+"):
                try:
                    parsed = phonenumbers.parse(cleaned, None)
                except Exception:
                    pass

            # Strategy 2: Add + if missing
            if parsed is None:
                digits = ''.join(ch for ch in cleaned if ch.isdigit())
                if digits:
                    try:
                        parsed = phonenumbers.parse("+" + digits, None)
                    except Exception:
                        pass

            # Strategy 3: Try with IN region (India default)
            if parsed is None:
                try:
                    parsed = phonenumbers.parse(cleaned, "IN")
                except Exception:
                    pass

            if parsed is None:
                return None, (
                    "âŒ <b>Cannot parse phone number!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ Please send with country code.\n"
                    "â”‚\n"
                    "â”‚ <b>Examples:</b>\n"
                    "â”‚ â€¢ <code>+919876543210</code>\n"
                    "â”‚ â€¢ <code>919876543210</code>\n"
                    "â”‚ â€¢ <code>9876543210</code>\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                )

            if not phonenumbers.is_valid_number(parsed):
                return None, (
                    "âŒ <b>Invalid phone number!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ Number doesn't seem valid.\n"
                    "â”‚ Check and try again.\n"
                    "â”‚\n"
                    "â”‚ <b>Examples:</b>\n"
                    "â”‚ â€¢ <code>+919876543210</code>\n"
                    "â”‚ â€¢ <code>919876543210</code>\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                )

            e164 = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
            return e164, None

        except Exception as e:
            logger.warning(f"Phone normalization error: {e}")
            # Fallback to basic
            pass

    # Basic fallback without phonenumbers library
    digits_only = ''.join(ch for ch in cleaned if ch.isdigit())

    if len(digits_only) < 7 or len(digits_only) > 15:
        return None, (
            "âŒ <b>Invalid phone number!</b>\n\n"
            "Include country code.\n"
            "Example: <code>+919876543210</code>"
        )

    normalized = "+" + digits_only
    return normalized, None


def normalize_otp(raw: str) -> tuple:
    """
    Normalize OTP â€” accept ANY format.
    Extracts only digits. Works with:
    - 12345
    - 1 2 3 4 5
    - 1-2-3-4-5
    - 12 345
    - 1.2.3.4.5
    - otp: 12345
    - "12345"
    Returns (otp_digits, error_message)
    """
    if not raw:
        return None, "âŒ Please send the OTP."

    # Extract ONLY digits from raw text
    digits = ""
    for ch in raw:
        if ch.isdigit():
            digits += ch

    if not digits:
        return None, (
            "âŒ <b>No digits found in OTP!</b>\n\n"
            "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            "â”‚ Just send the OTP digits:\n"
            "â”‚ â€¢ <code>12345</code>\n"
            "â”‚ â€¢ <code>1 2 3 4 5</code>\n"
            "â”‚ â€¢ <code>1-2-3-4-5</code>\n"
            "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
        )

    if len(digits) < 4:
        return None, (
            f"âŒ <b>OTP too short!</b>\n\n"
            f"Got only <code>{len(digits)}</code> digits: <code>{digits}</code>\n"
            f"OTP should be 5-6 digits."
        )

    if len(digits) > 8:
        return None, (
            f"âŒ <b>OTP too long!</b>\n\n"
            f"Got <code>{len(digits)}</code> digits.\n"
            f"OTP should be 5-6 digits.\n"
            f"Send only the OTP, nothing else."
        )

    return digits, None

# =====================================================
# ðŸ› ï¸ HELPER FUNCTIONS
# =====================================================
def get_readable_time(seconds: int) -> str:
    """Convert seconds to human-readable time string."""
    if seconds < 0:
        seconds = 0
    days, remainder = divmod(int(seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def get_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


def sanitize_html(text: str) -> str:
    """Basic HTML sanitization for display."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def truncate_text(text: str, max_len: int = 50) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in ADMIN_IDS


def get_user_account_limit(user_id: int) -> int:
    """Get max accounts allowed for user."""
    if is_admin(user_id):
        return 9999
    data = get_data()
    premium = data.get("premium_users", {}).get(str(user_id))
    if premium:
        plan_key = premium.get("plan", "free")
        plan = PLANS.get(plan_key, PLANS["free"])
        return plan.get("accounts", FREE_ACCOUNT_LIMIT)
    return FREE_ACCOUNT_LIMIT


def get_user_plan_key(user_id: int) -> str:
    """Get user's plan key."""
    if is_admin(user_id):
        return "elite"
    data = get_data()
    premium = data.get("premium_users", {}).get(str(user_id))
    if premium:
        return premium.get("plan", "free")
    return "free"


def get_user_plan_name(user_id: int) -> str:
    """Get user's plan display name."""
    if is_admin(user_id):
        return "ðŸ‘‘ Admin"
    plan_key = get_user_plan_key(user_id)
    return PLANS.get(plan_key, PLANS["free"]).get("name", "ðŸ†“ Free")


def get_user_plan_info(user_id: int) -> dict:
    """Get full plan info for user."""
    plan_key = get_user_plan_key(user_id)
    return PLANS.get(plan_key, PLANS["free"]).copy()


def get_user_accounts(user_id: int) -> dict:
    """Get all accounts belonging to a user."""
    data = get_data()
    return {
        k: v for k, v in data.get("accounts", {}).items()
        if v.get("user_id") == user_id
    }


def get_active_account(user_id: int) -> tuple:
    """Get active account key and data. Returns (key, data) or (None, None)."""
    data = get_data()
    acc_key = data.get("active_account", {}).get(str(user_id))
    if acc_key and acc_key in data.get("accounts", {}):
        return acc_key, data["accounts"][acc_key]
    return None, None


def is_rate_limited(user_id: int, action: str = "general", cooldown: int = 3) -> bool:
    """Check if user is rate limited for a specific action."""
    key = f"{user_id}_{action}"
    now = time.time()
    last_time = rate_limit_tracker.get(key, 0)
    if now - last_time < cooldown:
        return True
    rate_limit_tracker[key] = now
    return False


def add_admin_log(action: str, admin_id: int, details: str = ""):
    """Add entry to admin action log."""
    data = get_data()
    if "admin_logs" not in data:
        data["admin_logs"] = []
    log_entry = {
        "action": action,
        "admin_id": admin_id,
        "details": details,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "epoch": int(time.time())
    }
    data["admin_logs"].insert(0, log_entry)
    data["admin_logs"] = data["admin_logs"][:500]
    update_data(data)


async def check_access(user_id: int, msg_or_query) -> bool:
    """Check if user has access to the bot."""
    if is_admin(user_id):
        return True

    data = get_data()

    # Check ban
    banned = data.get("banned_users", [])
    if user_id in banned:
        msg = (
            "ðŸ’€ <b>Access Denied!</b>\n\n"
            "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            "â”‚ ðŸš« You are <b>permanently banned</b>.\n"
            "â”‚ Contact @securedsitedns for support.\n"
            "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
        )
        try:
            if isinstance(msg_or_query, CallbackQuery):
                await msg_or_query.answer(msg, show_alert=True)
            else:
                await msg_or_query.reply_text(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.debug(f"check_access ban reply error: {e}")
        return False

    # Check maintenance
    if data["settings"].get("maintenance_mode", False):
        msg = (
            "ðŸ”§ <b>Under Maintenance!</b>\n\n"
            "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            "â”‚ âš™ï¸ Bot is being upgraded.\n"
            "â”‚ Please try again later.\n"
            "â”‚ Contact @securedsitedns for info.\n"
            "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
        )
        try:
            if isinstance(msg_or_query, CallbackQuery):
                await msg_or_query.answer(msg, show_alert=True)
            else:
                await msg_or_query.reply_text(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.debug(f"check_access maintenance reply error: {e}")
        return False

    # Check force join channel â€” proper error handling
    force_channel = data["settings"].get("force_join_channel", "")
    if force_channel:
        try:
            member = await bot.get_chat_member(force_channel, user_id)
            # User is banned from channel
            if member.status == ChatMemberStatus.BANNED:
                msg = (
                    "ðŸ’€ <b>Access Restricted!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    f"â”‚ ðŸš« You are banned in our channel.\n"
                    f"â”‚ Contact @securedsitedns for help.\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                )
                try:
                    if isinstance(msg_or_query, CallbackQuery):
                        await msg_or_query.answer(msg, show_alert=True)
                    else:
                        await msg_or_query.reply_text(msg, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return False
            # User has left the channel
            if member.status == ChatMemberStatus.LEFT:
                raise UserNotParticipant
        except UserNotParticipant:
            # User genuinely not in channel
            msg = (
                "ðŸ’€ <b>Join Required!</b>\n\n"
                "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ ðŸ“¢ Join our channel first:\n"
                f"â”‚ {force_channel}\n"
                "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "ðŸ“¢ Join Channel",
                    url=f"https://t.me/{force_channel.replace('@', '')}"
                )],
                [InlineKeyboardButton("âœ… I Joined", callback_data="check_join")]
            ])
            try:
                if isinstance(msg_or_query, CallbackQuery):
                    await msg_or_query.message.edit_text(
                        msg, reply_markup=markup, parse_mode=ParseMode.HTML
                    )
                else:
                    await msg_or_query.reply_text(
                        msg, reply_markup=markup, parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                logger.debug(f"Force join message error: {e}")
            return False
        except (ChannelPrivate, PeerIdInvalid) as e:
            # Channel config error â€” don't block user, log admin warning
            logger.warning(
                f"Force join channel '{force_channel}' config error: {e}. "
                f"Check bot is admin in channel."
            )
            return True
        except Exception as e:
            # Other API errors â€” log but don't block user
            logger.warning(f"Force join check error for user {user_id}: {e}")
            return True

    return True


async def safe_edit(message, text: str, markup=None):
    """Safely edit a message, handling MessageNotModified."""
    try:
        await message.edit_text(
            text, reply_markup=markup, parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass
    except Exception as e:
        logger.warning(f"Safe edit error: {e}")


async def safe_send(user_id: int, text: str, markup=None):
    """Safely send a message to user."""
    try:
        await bot.send_message(
            user_id, text,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Safe send error to {user_id}: {e}")


# =====================================================
# ðŸ  START & WELCOME
# =====================================================
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    u_id = message.from_user.id
    data = await async_get_data()

    # Rate limit /start spam
    if is_rate_limited(u_id, "start", 2):
        return

    # Register new user
    is_new = str(u_id) not in data["users"]
    data["users"][str(u_id)] = {
        "user_id": u_id,
        "name": message.from_user.first_name or "Unknown",
        "username": message.from_user.username or "",
        "joined_date": (
            data["users"].get(str(u_id), {}).get(
                "joined_date", time.strftime('%Y-%m-%d %H:%M:%S')
            )
        ),
        "last_active": time.strftime('%Y-%m-%d %H:%M:%S'),
        "language": message.from_user.language_code or "en"
    }
    data["settings"]["bot_start_count"] = (
        data["settings"].get("bot_start_count", 0) + 1
    )

    # Handle referral
    if len(message.command) > 1 and is_new:
        ref_code = message.command[1]
        if ref_code.startswith("ref_"):
            ref_id = ref_code.replace("ref_", "")
            if ref_id != str(u_id) and ref_id in data["users"]:
                if "referrals" not in data:
                    data["referrals"] = {}
                if ref_id not in data["referrals"]:
                    data["referrals"][ref_id] = []
                data["referrals"][ref_id].append({
                    "user_id": u_id,
                    "date": time.strftime('%Y-%m-%d %H:%M:%S')
                })

    await async_update_data(data)

    # Notify admins about new user
    if is_new:
        total_users = len(data["users"])
        for admin_id in ADMIN_IDS:
            try:
                uname = (
                    f"@{message.from_user.username}"
                    if message.from_user.username
                    else "No Username"
                )
                await bot.send_message(
                    admin_id,
                    f"ðŸ’€ <b>New User Joined!</b>\n\n"
                    f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    f"â”‚ ðŸ‘¤ <b>Name:</b> {sanitize_html(message.from_user.first_name or 'Unknown')}\n"
                    f"â”‚ ðŸ†” <b>ID:</b> <code>{u_id}</code>\n"
                    f"â”‚ ðŸ”— <b>Username:</b> {uname}\n"
                    f"â”‚ ðŸŒ <b>Lang:</b> {message.from_user.language_code or 'N/A'}\n"
                    f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    f"â”‚ ðŸ“ˆ <b>Total Users:</b> <code>{total_users}</code>\n"
                    f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.debug(f"New user notify error: {e}")

    if not await check_access(u_id, message):
        return

    await send_welcome(message)


async def send_welcome(msg_or_query, is_edit: bool = False):
    """Send welcome message."""
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))
    data = get_data()
    total_users = len(data["users"])

    text = (
        "ðŸ’€ <b>Sá´‹á´œÊŸÊŸ Aá´…s Bá´á´› v3.0</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ The most powerful Telegram ad\n"
        "â”‚ automation tool is now in your hands.\n"
        "â”‚ Connect â€¢ Target â€¢ Launch\n"
        "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ Users: <code>{total_users}</code> | â±ï¸ Up: <code>{uptime}</code>\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        "âš¡ <b>Core Features</b>\n"
        "â”œ ðŸŽ¯ Smart Group Targeting\n"
        "â”œ ðŸ”„ Auto Multi-Round Campaigns\n"
        "â”œ ðŸ›¡ï¸ Anti-Flood Protection\n"
        "â”œ ðŸ“Š Live Campaign Tracker\n"
        "â”œ ðŸ‘¥ Multi-Account Support\n"
        "â”œ ðŸ”‘ OTP & 2FA Secure Login\n"
        "â”œ ðŸ“ˆ Advanced Analytics\n"
        "â”” ðŸ”— Referral System\n\n"
        "ðŸ‘¨â€ðŸ’» <b>Group:</b> @securedsitedns\n"
        "ðŸ¤– <b>Owner:</b> @securedsitedns"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ’» Open Dashboard", callback_data="open_dash")],
        [
            InlineKeyboardButton("ðŸ’Ž Premium Plans", callback_data="show_plans"),
            InlineKeyboardButton("ðŸ“– How To Use", callback_data="how_to_use")
        ],
        [
            InlineKeyboardButton("ðŸ”— Referral Link", callback_data="my_referral"),
            InlineKeyboardButton("ðŸ“Š Bot Stats", callback_data="public_stats")
        ],
        [
            InlineKeyboardButton("ðŸ’¬ Support", url="https://t.me/securedsitedns"),
            InlineKeyboardButton("ðŸ¤– Owner", url="https://t.me/securedsitedns")
        ]
    ])

    try:
        if is_edit:
            await safe_edit(msg_or_query, text, markup)
        else:
            await msg_or_query.reply_text(
                text, reply_markup=markup, parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.warning(f"Welcome send error: {e}")


# â”€â”€ Check Force Join â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^check_join$"))
async def check_join_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if await check_access(u_id, query):
        await query.answer("âœ… Verified! Welcome!", show_alert=True)
        await send_welcome(query.message, is_edit=True)


# â”€â”€ Back to Start â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^back_start$"))
async def back_start_cb(client, query: CallbackQuery):
    if not await check_access(query.from_user.id, query):
        return
    if query.from_user.id in user_state:
        # Disconnect any pending client before clearing state
        state = user_state[query.from_user.id]
        tc = state.get("client")
        if tc:
            try:
                await tc.disconnect()
            except Exception:
                pass
        del user_state[query.from_user.id]
    await send_welcome(query.message, is_edit=True)


# â”€â”€ How To Use â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^how_to_use$"))
async def how_to_use_cb(client, query: CallbackQuery):
    text = (
        "ðŸ“– <b>Skull Ads â€” Complete Guide</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ <b>ðŸ”° QUICK START GUIDE</b>\n"
        "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ <b>Step 1:</b> Open Dashboard\n"
        "â”‚ <b>Step 2:</b> Go to Accounts â†’ Add\n"
        "â”‚ <b>Step 3:</b> Login with Phone Number\n"
        "â”‚ <b>Step 4:</b> Select Active Account\n"
        "â”‚ <b>Step 5:</b> Go to Targets\n"
        "â”‚ <b>Step 6:</b> Fetch or Add Group Links\n"
        "â”‚ <b>Step 7:</b> Set your Ad Message\n"
        "â”‚ <b>Step 8:</b> Configure Settings\n"
        "â”‚           (Delay â€¢ Interval â€¢ Rounds)\n"
        "â”‚ <b>Step 9:</b> Hit Launch! ðŸš€\n"
        "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ <b>âš ï¸ PRO TIPS</b>\n"
        "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ â€¢ Use <b>10-30s</b> delay to avoid bans\n"
        "â”‚ â€¢ Set interval <b>60m+</b> for safe cycling\n"
        "â”‚ â€¢ Use <code>/reset</code> if bot gets stuck\n"
        "â”‚ â€¢ Free plan = <b>1 account</b> only\n"
        "â”‚ â€¢ Buy Premium for <b>multi accounts</b>\n"
        "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ <b>ðŸ“‹ AVAILABLE COMMANDS</b>\n"
        "â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ /start â€” Main menu\n"
        "â”‚ /ping â€” Check bot status\n"
        "â”‚ /reset â€” Reset stuck states\n"
        "â”‚ /cancel â€” Cancel current action\n"
        "â”‚ /myid â€” Get your user ID\n"
        "â”‚ /help â€” Show this guide\n"
        "â”‚ /referral â€” Your referral link\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        "ðŸ‘¨â€ðŸ’» <b>Help:</b> @securedsitedns | @securedsitedns"
    )
    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ’Ž Buy Premium", callback_data="show_plans")],
            [InlineKeyboardButton("ðŸ’» Dashboard", callback_data="open_dash")],
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="back_start")]
        ])
    )


# â”€â”€ My Referral â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^my_referral$"))
async def my_referral_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    data = get_data()
    ref_count = len(data.get("referrals", {}).get(str(u_id), []))
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{u_id}"

    text = (
        f"ðŸ’€ <b>Your Referral Link</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ”— <b>Link:</b>\n"
        f"â”‚ <code>{ref_link}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ <b>Total Referrals:</b> <code>{ref_count}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"Share this link and earn rewards!"
    )
    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ“¤ Share Link", url=(
                f"https://t.me/share/url?url={ref_link}"
                f"&text=Join+Skull+Ads+Bot+for+free!"
            ))],
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="back_start")]
        ])
    )


# â”€â”€ Public Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^public_stats$"))
async def public_stats_cb(client, query: CallbackQuery):
    data = get_data()
    total_sent = sum(
        s.get("total_sent", 0) for s in data["stats"].values()
    )
    total_users = len(data["users"])
    total_campaigns = sum(
        1 for c in data["campaigns"].values()
        if c.get("targets")
    )
    uptime = get_readable_time(int(time.time() - BOT_START_TIME))

    text = (
        f"ðŸ’€ <b>Skull Ads â€” Public Stats</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ <b>Total Users:</b> <code>{total_users}</code>\n"
        f"â”‚ ðŸš€ <b>Messages Sent:</b> <code>{total_sent:,}</code>\n"
        f"â”‚ ðŸ“Š <b>Campaigns Created:</b> <code>{total_campaigns}</code>\n"
        f"â”‚ â±ï¸ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"â”‚ ðŸ¤– <b>Version:</b> <code>v{BOT_VERSION}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )
    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="back_start")]
        ])
    )


# =====================================================
# ðŸ’Ž PREMIUM PLANS
# =====================================================
@bot.on_callback_query(filters.regex("^show_plans$"))
async def show_plans_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    current_plan = get_user_plan_name(u_id)
    limit = get_user_account_limit(u_id)
    plan_info = get_user_plan_info(u_id)

    text = (
        f"ðŸ’Ž <b>Skull Ads â€” Premium Plans</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“Š <b>Your Current Plan:</b> {current_plan}\n"
        f"â”‚ ðŸ‘¥ <b>Account Limit:</b> <code>{limit}</code>\n"
        f"â”‚ ðŸŽ¯ <b>Target Limit:</b> <code>{plan_info.get('max_targets', 50)}</code>\n"
        f"â”‚ ðŸ”„ <b>Round Limit:</b> <code>{plan_info.get('max_rounds', 5)}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"ðŸ†“ <b>Free Plan</b>\n"
        f"â”œ 1 Account â€¢ 50 Targets â€¢ 5 Rounds\n"
        f"â”” Basic Features\n\n"
        f"âš¡ <b>Basic Plan â€” â‚¹99/month</b>\n"
        f"â”œ 3 Accounts â€¢ 200 Targets â€¢ 50 Rounds\n"
        f"â”” All Features Unlocked\n\n"
        f"ðŸ’Ž <b>Pro Plan â€” â‚¹249/month</b>\n"
        f"â”œ 10 Accounts â€¢ 1000 Targets â€¢ 500 Rounds\n"
        f"â”” Priority Support\n\n"
        f"ðŸ‘‘ <b>Elite Plan â€” â‚¹499/month</b>\n"
        f"â”œ Unlimited Everything\n"
        f"â”” VIP Support + Custom Features\n\n"
        f"ðŸ“© <b>Contact admin to purchase:</b>"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "ðŸ’¬ Buy â€” @securedsitedns",
            url="https://t.me/securedsitedns"
        )],
        [InlineKeyboardButton(
            "ðŸ¤– Owner",
            url="https://t.me/securedsitedns"
        )],
        [InlineKeyboardButton("ðŸ”™ Back", callback_data="back_start")]
    ])
    await safe_edit(query.message, text, markup)


# =====================================================
# ðŸ’» DASHBOARD
# =====================================================
@bot.on_callback_query(filters.regex("^open_dash$"))
async def open_dash_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return
    # Clear any stuck user_state safely
    if u_id in user_state:
        state = user_state[u_id]
        tc = state.get("client")
        if tc:
            try:
                await tc.disconnect()
            except Exception:
                pass
        del user_state[u_id]
    await send_dash(query.message, u_id, is_edit=True)


async def send_dash(msg_or_query, u_id: int, is_edit: bool = False):
    """Send dashboard view."""
    data = get_data()
    user_accs = get_user_accounts(u_id)
    account_count = len(user_accs)
    limit = get_user_account_limit(u_id)
    plan = get_user_plan_name(u_id)
    active_key, active_acc = get_active_account(u_id)
    camp = data.get("campaigns", {}).get(str(u_id), {})
    camp_status = camp.get("status", "IDLE")
    target_count = len(camp.get("targets", []))
    ad_set = "âœ…" if camp.get("ad_html") else "âŒ"
    settings_set = "âœ…" if camp.get("group_delay") else "âŒ"

    status_map = {
        "RUNNING": "ðŸŸ¢ RUNNING",
        "PAUSED": "ðŸ”´ PAUSED",
        "COMPLETED": "âœ… COMPLETED",
        "IDLE": "âšª IDLE"
    }
    status_display = status_map.get(camp_status, "âšª IDLE")

    acc_display = "âŒ None Selected"
    if active_acc:
        phone = active_acc.get("phone", "Unknown")
        acc_display = f"âœ… <tg-spoiler>{phone}</tg-spoiler>"

    text = (
        f"ðŸ’€ <b>Skull Ads â€” Dashboard</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ’Ž <b>Plan:</b> {plan}\n"
        f"â”‚ ðŸ‘¥ <b>Accounts:</b> <code>{account_count}/{limit}</code>\n"
        f"â”‚ ðŸŽ¯ <b>Active:</b> {acc_display}\n"
        f"â”‚ ðŸ“Š <b>Status:</b> {status_display}\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸŽ¯ Targets: <code>{target_count}</code> | "
        f"ðŸ“ Ad: {ad_set} | âš™ï¸ Config: {settings_set}\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"Select an option below:"
    )

    if camp_status == "RUNNING":
        action_row = [
            InlineKeyboardButton("ðŸ›‘ Stop Campaign", callback_data="stop_ads"),
            InlineKeyboardButton("ðŸ“Š Live Stats", callback_data="show_my_stats")
        ]
    else:
        action_row = [
            InlineKeyboardButton("â–¶ï¸ Launch", callback_data="launch_ads"),
            InlineKeyboardButton("ðŸ“Š My Stats", callback_data="show_my_stats")
        ]

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ‘¥ Accounts", callback_data="accounts_menu"),
            InlineKeyboardButton("ðŸŽ¯ Targets", callback_data="target_menu")
        ],
        [
            InlineKeyboardButton("ðŸ“ Ad Message", callback_data="ask_ad_msg"),
            InlineKeyboardButton("âš™ï¸ Settings", callback_data="start_settings_wizard")
        ],
        action_row,
        [
            InlineKeyboardButton("ðŸ’Ž Premium", callback_data="show_plans"),
            InlineKeyboardButton("ðŸ”— Referral", callback_data="my_referral")
        ],
        [InlineKeyboardButton("ðŸ  Main Menu", callback_data="back_start")]
    ])

    try:
        if is_edit:
            await safe_edit(msg_or_query, text, markup)
        else:
            await msg_or_query.reply_text(
                text, reply_markup=markup, parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.warning(f"Dashboard send error: {e}")


# =====================================================
# ðŸ‘¥ ACCOUNTS MENU
# =====================================================
@bot.on_callback_query(filters.regex("^accounts_menu$"))
async def accounts_menu_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    user_accs = get_user_accounts(u_id)
    limit = get_user_account_limit(u_id)
    plan = get_user_plan_name(u_id)
    data = get_data()
    active_key = data.get("active_account", {}).get(str(u_id))

    text = (
        f"ðŸ’€ <b>Skull Ads â€” Accounts</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ’Ž <b>Plan:</b> {plan}\n"
        f"â”‚ ðŸ‘¥ <b>Used Slots:</b> <code>{len(user_accs)}/{limit}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"<b>ðŸŸ¢ = Active Account</b>\n"
        f"<b>Tap account to set as active</b>"
    )

    buttons = []
    for acc_key, acc in user_accs.items():
        phone = acc.get("phone", "Unknown")
        is_active = "ðŸŸ¢" if acc_key == active_key else "âš«"
        added = acc.get("added_date", "N/A")[:10]
        buttons.append([
            InlineKeyboardButton(
                f"{is_active} {phone} ({added})",
                callback_data=f"select_acc_{acc_key}"
            ),
            InlineKeyboardButton(
                "ðŸ—‘ï¸", callback_data=f"confirm_del_acc_{acc_key}"
            )
        ])

    if not user_accs:
        text += "\n\nðŸ“­ <b>No accounts added yet!</b>"

    if len(user_accs) < limit:
        buttons.append([
            InlineKeyboardButton(
                "âž• Add New Account", callback_data="login_acc"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                "ðŸ’Ž Upgrade for More Slots", callback_data="show_plans"
            )
        ])

    buttons.append([
        InlineKeyboardButton("ðŸ”™ Dashboard", callback_data="open_dash")
    ])

    await safe_edit(
        query.message, text, InlineKeyboardMarkup(buttons)
    )


# â”€â”€ Select Account â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex(r"^select_acc_(.+)$"))
async def select_acc_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    acc_key = query.matches[0].group(1)
    user_accs = get_user_accounts(u_id)

    if acc_key not in user_accs:
        return await query.answer("âŒ Account not found!", show_alert=True)

    data = await async_get_data()
    if "active_account" not in data:
        data["active_account"] = {}
    data["active_account"][str(u_id)] = acc_key
    await async_update_data(data)

    phone = user_accs[acc_key].get("phone", "Unknown")
    await query.answer(f"âœ… Active: {phone}", show_alert=True)
    await accounts_menu_cb(client, query)


# â”€â”€ Confirm Delete Account â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex(r"^confirm_del_acc_(.+)$"))
async def confirm_del_acc_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    acc_key = query.matches[0].group(1)
    user_accs = get_user_accounts(u_id)

    if acc_key not in user_accs:
        return await query.answer("âŒ Account not found!", show_alert=True)

    phone = user_accs[acc_key].get("phone", "Unknown")
    text = (
        f"ðŸ’€ <b>Confirm Account Removal</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“± <b>Phone:</b> {phone}\n"
        f"â”‚ âš ï¸ This will log out the session.\n"
        f"â”‚ This action cannot be undone!\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )
    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "âœ… Yes, Remove",
                    callback_data=f"del_acc_{acc_key}"
                ),
                InlineKeyboardButton(
                    "âŒ Cancel",
                    callback_data="accounts_menu"
                )
            ]
        ])
    )


# â”€â”€ Delete Account â€” Fixed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex(r"^del_acc_(.+)$"))
async def del_acc_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    acc_key = query.matches[0].group(1)

    data = await async_get_data()

    # Verify account belongs to this user
    acc = data["accounts"].get(acc_key)
    if not acc or acc.get("user_id") != u_id:
        return await query.answer("âŒ Account not found!", show_alert=True)

    # Try to restore profile and logout session
    try:
        tc = Client(
            f"del_{u_id}_{int(time.time())}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=acc['session'],
            in_memory=True
        )
        await tc.connect()

        # Restore original profile for non-admins
        if not is_admin(u_id):
            try:
                old_name = acc.get('old_name', '')
                old_bio = acc.get('old_bio', '')
                if old_name:
                    await tc.update_profile(first_name=old_name)
                if old_bio is not None:
                    await tc.update_profile(bio=old_bio)
            except Exception as pe:
                logger.warning(f"Profile restore error during delete: {pe}")

        try:
            await tc.log_out()
        except Exception as lo_e:
            logger.debug(f"Logout error (non-critical): {lo_e}")

        try:
            await tc.disconnect()
        except Exception:
            pass

    except AuthKeyUnregistered:
        logger.info(f"Session already expired for {acc_key}, proceeding with removal.")
    except Exception as e:
        logger.warning(f"Del account cleanup error: {e}")

    # Remove from data using already-loaded data (not stale re-read)
    del data["accounts"][acc_key]

    # Determine remaining accounts for this user using updated in-memory data
    remaining = {
        k: v for k, v in data["accounts"].items()
        if v.get("user_id") == u_id
    }

    # Update active account
    current_active = data.get("active_account", {}).get(str(u_id))
    if current_active == acc_key:
        if remaining:
            data["active_account"][str(u_id)] = list(remaining.keys())[0]
        else:
            data.get("active_account", {}).pop(str(u_id), None)

    # Pause campaign if no accounts left
    if not remaining:
        if data.get("campaigns", {}).get(str(u_id), {}).get("status") == "RUNNING":
            data["campaigns"][str(u_id)]["status"] = "PAUSED"
            logger.info(f"Campaign paused for user {u_id} â€” no accounts left.")

    data["settings"]["lifetime_logouts"] = (
        data["settings"].get("lifetime_logouts", 0) + 1
    )
    await async_update_data(data)

    await query.answer("âœ… Account removed!", show_alert=True)
    await accounts_menu_cb(client, query)


# =====================================================
# ðŸ“± LOGIN FLOW
# =====================================================
@bot.on_callback_query(filters.regex("^login_acc$"))
async def login_btn(client, query: CallbackQuery):
    u_id = query.from_user.id
    user_accs = get_user_accounts(u_id)
    limit = get_user_account_limit(u_id)

    if len(user_accs) >= limit:
        text = (
            f"ðŸ’€ <b>Account Limit Reached!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ ðŸš« You've used all <b>{limit}</b> slot(s).\n"
            f"â”‚ Upgrade your plan to add more.\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
            f"ðŸ†“ <b>Free:</b> 1 account\n"
            f"âš¡ <b>Basic:</b> 3 accounts â€” â‚¹99/m\n"
            f"ðŸ’Ž <b>Pro:</b> 10 accounts â€” â‚¹249/m\n"
            f"ðŸ‘‘ <b>Elite:</b> Unlimited â€” â‚¹499/m"
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "ðŸ’Ž Buy Premium â€” @securedsitedns",
                url="https://t.me/securedsitedns"
            )],
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="accounts_menu")]
        ])
        return await safe_edit(query.message, text, markup)

    user_state[u_id] = {"step": "wait_phone", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Skull Ads â€” Secure Login</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ ðŸ“± Send your phone number.\n"
        "â”‚\n"
        "â”‚ <b>Any format works!</b>\n"
        "â”‚ â€¢ <code>+919876543210</code>\n"
        "â”‚ â€¢ <code>919876543210</code>\n"
        "â”‚ â€¢ <code>9876543210</code>\n"
        "â”‚ â€¢ <code>+1 202 555 1234</code>\n"
        "â”‚ â€¢ <code>91 98765-43210</code>\n"
        "â”‚\n"
        "â”‚ âœ… Bot will auto-format your number.\n"
        "â”‚ ðŸ”’ Your data is encrypted.\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        "âš ï¸ Type /cancel to abort.",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="accounts_menu")]
        ])
    )


async def finish_login(message: Message, tc, u_id: int, phone: str):
    """Complete login process â€” Fixed profile fetch and bio save."""
    try:
        sess = await tc.export_session_string()
    except Exception as e:
        logger.error(f"Export session error: {e}")
        await message.reply_text(
            "âŒ <b>Login failed during session export.</b>\nPlease try again.",
            parse_mode=ParseMode.HTML
        )
        try:
            await tc.disconnect()
        except Exception:
            pass
        if u_id in user_state:
            del user_state[u_id]
        return

    # Properly fetch existing profile before modifying
    old_name = ""
    old_bio = ""
    try:
        me = await tc.get_me()
        old_name = me.first_name or ""
        # Fetch full user info to get bio
        try:
            full_user = await tc.get_chat(me.id)
            old_bio = full_user.bio or ""
        except Exception as bio_e:
            logger.debug(f"Bio fetch error (non-critical): {bio_e}")
            old_bio = ""
    except Exception as me_e:
        logger.warning(f"get_me() error during finish_login: {me_e}")

    # Update profile for non-admins
    if not is_admin(u_id):
        try:
            new_name = old_name
            if old_name and "SkullAdsBot" not in old_name:
                new_name = f"{old_name} | @SkullAdsBot â˜ ï¸"
            elif not old_name:
                new_name = "@SkullAdsBot â˜ ï¸"
            await tc.update_profile(
                first_name=new_name,
                bio="ðŸ’€ Aá´œá´›á´á´á´€á´›á´‡á´… Aá´…s VÉªá´€ @SkullAdsBot â˜ ï¸ | @securedsitedns"
            )
        except Exception as e:
            logger.warning(f"Profile update error (non-critical): {e}")
    else:
        logger.info("ðŸ‘‘ Admin Login: Profile update bypassed.")

    acc_key = f"{u_id}_{phone.replace('+', '').replace(' ', '')}"
    data = await async_get_data()

    data["settings"]["lifetime_logins"] = (
        data["settings"].get("lifetime_logins", 0) + 1
    )
    data["accounts"][acc_key] = {
        "user_id": u_id,
        "phone": phone,
        "session": sess,
        "old_name": old_name,
        "old_bio": old_bio,
        "added_date": time.strftime('%Y-%m-%d %H:%M:%S')
    }

    if "active_account" not in data:
        data["active_account"] = {}
    data["active_account"][str(u_id)] = acc_key

    if str(u_id) not in data["campaigns"]:
        data["campaigns"][str(u_id)] = {"status": "IDLE"}

    await async_update_data(data)

    try:
        await tc.disconnect()
    except Exception:
        pass

    if u_id in user_state:
        del user_state[u_id]

    await message.reply_text(
        f"ðŸ’€ <b>Login Successful!</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âœ… Linked: <tg-spoiler>{phone}</tg-spoiler>\n"
        f"â”‚ ðŸŸ¢ Set as active account.\n"
        f"â”‚ You can now launch campaigns!\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ’» Dashboard", callback_data="open_dash")],
            [InlineKeyboardButton(
                "ðŸ‘¥ Manage Accounts", callback_data="accounts_menu"
            )]
        ]),
        parse_mode=ParseMode.HTML
    )


# =====================================================
# ðŸ“Š MY STATS
# =====================================================
@bot.on_callback_query(filters.regex("^show_my_stats$"))
async def show_my_stats_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    data = get_data()
    stats = data["stats"].get(str(u_id), {"total_sent": 0, "failed": 0})
    camp = data["campaigns"].get(str(u_id), {})
    user_accs = get_user_accounts(u_id)
    limit = get_user_account_limit(u_id)
    plan = get_user_plan_name(u_id)

    target_count = len(camp.get("targets", []))
    ad_status = "âœ… Set" if camp.get("ad_html") else "âŒ Not Set"

    delay = camp.get("group_delay", 0)
    interval_min = int(camp.get("interval", 0) / 60) if camp.get("interval") else 0
    total_rounds = camp.get("total_rounds", 0)
    round_str = "â™¾ï¸ Unlimited" if total_rounds > 9000000 else str(total_rounds)

    settings_str = (
        f"â³ {delay}s â€¢ â±ï¸ {interval_min}m â€¢ ðŸ”„ {round_str}"
        if delay > 0 else "âš™ï¸ Not Configured"
    )

    camp_status = camp.get("status", "IDLE")
    status_map = {
        "RUNNING": "ðŸŸ¢ RUNNING",
        "PAUSED": "ðŸ”´ PAUSED",
        "COMPLETED": "âœ… COMPLETED",
        "IDLE": "âšª IDLE"
    }
    status_display = status_map.get(camp_status, "âšª IDLE")

    c_round = camp.get("current_round", 0)
    round_display = (
        f"{c_round}/â™¾ï¸" if total_rounds > 9000000
        else f"{c_round}/{total_rounds}" if total_rounds > 0
        else "0/0"
    )

    total = stats["total_sent"] + stats["failed"]
    success_rate = round(
        (stats["total_sent"] / total * 100), 1
    ) if total > 0 else 0

    ref_count = len(data.get("referrals", {}).get(str(u_id), []))

    text = (
        f"ðŸ’€ <b>Skull Ads â€” My Stats</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ’Ž <b>Plan:</b> {plan}\n"
        f"â”‚ ðŸ‘¥ <b>Accounts:</b> <code>{len(user_accs)}/{limit}</code>\n"
        f"â”‚ ðŸŽ¯ <b>Targets:</b> <code>{target_count}</code> Groups\n"
        f"â”‚ ðŸ“ <b>Ad Message:</b> {ad_status}\n"
        f"â”‚ âš™ï¸ <b>Settings:</b> {settings_str}\n"
        f"â”‚ ðŸ“Š <b>Campaign:</b> {status_display}\n"
        f"â”‚ ðŸ”„ <b>Round:</b> {round_display}\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸš€ <b>Total Sent:</b> <code>{stats['total_sent']:,}</code>\n"
        f"â”‚ âŒ <b>Failed:</b> <code>{stats['failed']:,}</code>\n"
        f"â”‚ ðŸ“ˆ <b>Success Rate:</b> <code>{success_rate}%</code>\n"
        f"â”‚ ðŸ”— <b>Referrals:</b> <code>{ref_count}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )
    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ”„ Refresh", callback_data="show_my_stats")],
            [InlineKeyboardButton("ðŸ”™ Dashboard", callback_data="open_dash")]
        ])
    )


# =====================================================
# ðŸŽ¯ TARGET SELECTION
# =====================================================
@bot.on_callback_query(filters.regex("^target_menu$"))
async def target_menu_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    data = get_data()
    camp = data.get("campaigns", {}).get(str(u_id), {})
    target_count = len(camp.get("targets", []))
    plan_info = get_user_plan_info(u_id)
    max_targets = plan_info.get("max_targets", 50)

    text = (
        f"ðŸ’€ <b>Skull Ads â€” Target Selection</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸŽ¯ <b>Current Targets:</b> <code>{target_count}</code>\n"
        f"â”‚ ðŸ“Š <b>Max Allowed:</b> <code>{max_targets}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“¥ <b>Auto-Fetch</b> â€” Scan your joined groups\n"
        f"â”‚ ðŸ”— <b>Custom Links</b> â€” Add group links manually\n"
        f"â”‚ ðŸ—‘ï¸ <b>Clear</b> â€” Remove all targets\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    buttons = [
        [InlineKeyboardButton(
            "ðŸ“¥ Auto-Fetch Groups", callback_data="fetch_groups"
        )],
        [InlineKeyboardButton(
            "ðŸ”— Add Custom Links", callback_data="ask_custom_links"
        )],
    ]

    if target_count > 0:
        buttons.append([
            InlineKeyboardButton(
                "ðŸ“‹ View Targets", callback_data="view_targets"
            ),
            InlineKeyboardButton(
                "ðŸ—‘ï¸ Clear All", callback_data="clear_targets"
            )
        ])

    buttons.append([
        InlineKeyboardButton("ðŸ”™ Dashboard", callback_data="open_dash")
    ])

    await safe_edit(query.message, text, InlineKeyboardMarkup(buttons))


# â”€â”€ View Targets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^view_targets$"))
async def view_targets_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    data = get_data()
    targets = data.get("campaigns", {}).get(str(u_id), {}).get("targets", [])

    if not targets:
        return await query.answer("âŒ No targets set!", show_alert=True)

    text = f"ðŸ’€ <b>Current Targets ({len(targets)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for i, t in enumerate(targets[:30], 1):
        display = truncate_text(str(t), 30)
        text += f"â”‚ {i}. <code>{display}</code>\n"
    if len(targets) > 30:
        text += f"â”‚ ... +{len(targets) - 30} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "ðŸ—‘ï¸ Clear All", callback_data="clear_targets"
            )],
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="target_menu")]
        ])
    )


# â”€â”€ Clear Targets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^clear_targets$"))
async def clear_targets_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    data = await async_get_data()
    if str(u_id) in data["campaigns"]:
        data["campaigns"][str(u_id)]["targets"] = []
        data["campaigns"][str(u_id)].pop("cache_grps", None)
        await async_update_data(data)
    await query.answer("âœ… All targets cleared!", show_alert=True)
    await target_menu_cb(client, query)


# â”€â”€ Fetch Groups â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^fetch_groups$"))
async def fetch_groups_cb(client, query: CallbackQuery):
    u_id = query.from_user.id

    # Rate limit to prevent spam clicks
    if is_rate_limited(u_id, "fetch_groups", 10):
        return await query.answer("â³ Please wait before fetching again.", show_alert=True)

    data = get_data()
    active_key, active_acc = get_active_account(u_id)

    if not active_key or not active_acc:
        return await query.answer(
            "âš ï¸ No active account! Add & select an account first.",
            show_alert=True
        )

    await query.answer("Scanning groups...", show_alert=False)
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Fetching Groups...</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ â³ Scanning your account...\n"
        "â”‚ This may take a moment.\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    tc = None
    try:
        tc = Client(
            f"fetch_{u_id}_{int(time.time())}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=active_acc['session'],
            in_memory=True
        )
        await tc.connect()

        grps = []
        try:
            async for d in tc.get_dialogs():
                if d.chat and d.chat.type in [
                    ChatType.GROUP, ChatType.SUPERGROUP
                ]:
                    grps.append({
                        "id": str(d.chat.id),
                        "title": truncate_text(d.chat.title or "Unknown", 25),
                        "sel": True,
                        "members": getattr(d.chat, 'members_count', 0) or 0
                    })
        except Exception as e:
            logger.warning(f"Dialog scan error for user {u_id}: {e}")

        try:
            await tc.disconnect()
        except Exception:
            pass

        if not grps:
            return await safe_edit(
                query.message,
                "ðŸ’€ <b>No Groups Found!</b>\n\n"
                "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                "â”‚ âŒ No joined groups found.\n"
                "â”‚ Try adding custom links instead.\n"
                "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "ðŸ”— Add Custom Links",
                        callback_data="ask_custom_links"
                    )],
                    [InlineKeyboardButton(
                        "ðŸ”™ Back", callback_data="target_menu"
                    )]
                ])
            )

        grps.sort(key=lambda x: x.get("members", 0), reverse=True)

        data = await async_get_data()
        if str(u_id) not in data["campaigns"]:
            data["campaigns"][str(u_id)] = {"status": "IDLE"}
        data["campaigns"][str(u_id)]["cache_grps"] = grps
        await async_update_data(data)

        await show_group_page(query.message, u_id, 0)

    except AuthKeyUnregistered:
        try:
            if tc:
                await tc.disconnect()
        except Exception:
            pass
        data = await async_get_data()
        if active_key and active_key in data["accounts"]:
            del data["accounts"][active_key]
            data.get("active_account", {}).pop(str(u_id), None)
            await async_update_data(data)
        await safe_edit(
            query.message,
            "ðŸ’€ <b>Session Expired!</b>\n\n"
            "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            "â”‚ âš ï¸ Session was revoked/expired.\n"
            "â”‚ Please login again.\n"
            "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "âž• Add Account", callback_data="login_acc"
                )],
                [InlineKeyboardButton(
                    "ðŸ”™ Back", callback_data="target_menu"
                )]
            ])
        )
    except Exception as e:
        try:
            if tc:
                await tc.disconnect()
        except Exception:
            pass
        logger.error(f"Fetch groups error for user {u_id}: {e}")
        await safe_edit(
            query.message,
            f"ðŸ’€ <b>Fetch Error!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âŒ {sanitize_html(str(e)[:100])}\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("ðŸ” Retry", callback_data="fetch_groups")],
                [InlineKeyboardButton("ðŸ”™ Back", callback_data="target_menu")]
            ])
        )


async def show_group_page(message, u_id: int, page: int):
    """Display paginated group selection."""
    data = get_data()
    grps = data["campaigns"].get(str(u_id), {}).get("cache_grps", [])

    if not grps:
        return

    per_page = 8
    total_pages = max(1, math.ceil(len(grps) / per_page))
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    selected_count = sum(1 for g in grps if g.get("sel"))

    buttons = []
    for i, g in enumerate(grps[start:end]):
        idx = start + i
        icon = "âœ…" if g.get("sel") else "â˜‘ï¸"
        members = g.get("members", 0)
        member_str = f" [{members}]" if members > 0 else ""
        buttons.append([
            InlineKeyboardButton(
                f"{icon} {g['title']}{member_str}",
                callback_data=f"tg_sel_{idx}_{page}"
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            "â—€ï¸ Prev", callback_data=f"tg_pg_{page - 1}"
        ))
    nav.append(InlineKeyboardButton(
        f"ðŸ“„ {page + 1}/{total_pages}", callback_data="noop"
    ))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            "Next â–¶ï¸", callback_data=f"tg_pg_{page + 1}"
        ))
    if nav:
        buttons.append(nav)

    all_selected = selected_count == len(grps)
    buttons.extend([
        [InlineKeyboardButton(
            f"ðŸ”„ {'Deselect' if all_selected else 'Select'} All",
            callback_data=f"tg_all_{page}"
        )],
        [InlineKeyboardButton(
            f"âœ… Confirm ({selected_count}/{len(grps)})",
            callback_data="confirm_targets"
        )],
        [InlineKeyboardButton("ðŸ”™ Back", callback_data="target_menu")]
    ])

    text = (
        f"ðŸ’€ <b>Select Target Groups</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“‹ <b>Total Found:</b> <code>{len(grps)}</code>\n"
        f"â”‚ âœ… <b>Selected:</b> <code>{selected_count}</code>\n"
        f"â”‚ ðŸ“„ <b>Page:</b> {page + 1}/{total_pages}\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"Tap groups to toggle:"
    )

    await safe_edit(message, text, InlineKeyboardMarkup(buttons))


@bot.on_callback_query(filters.regex(r"^tg_(sel|pg|all)_(\d+)(?:_(\d+))?$"))
async def tg_handler_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    action = query.matches[0].group(1)
    p1 = int(query.matches[0].group(2))
    p2 = query.matches[0].group(3)

    data = await async_get_data()
    grps = data["campaigns"].get(str(u_id), {}).get("cache_grps", [])

    if not grps:
        return await query.answer("âŒ No groups cached!", show_alert=True)

    page = 0

    if action == "sel":
        if p1 < len(grps):
            grps[p1]["sel"] = not grps[p1]["sel"]
        page = int(p2) if p2 else 0
        data["campaigns"][str(u_id)]["cache_grps"] = grps
        await async_update_data(data)

    elif action == "all":
        all_sel = all(g.get("sel") for g in grps)
        for g in grps:
            g["sel"] = not all_sel
        page = p1
        data["campaigns"][str(u_id)]["cache_grps"] = grps
        await async_update_data(data)

    elif action == "pg":
        page = p1

    await show_group_page(query.message, u_id, page)


@bot.on_callback_query(filters.regex("^confirm_targets$"))
async def confirm_targets_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    data = await async_get_data()
    cache = data["campaigns"].get(str(u_id), {}).get("cache_grps", [])
    selected = [g["id"] for g in cache if g.get("sel")]

    if not selected:
        return await query.answer(
            "âš ï¸ Select at least 1 group!", show_alert=True
        )

    plan_info = get_user_plan_info(u_id)
    max_targets = plan_info.get("max_targets", 50)
    if len(selected) > max_targets and not is_admin(u_id):
        return await query.answer(
            f"âš ï¸ Your plan allows max {max_targets} targets! "
            f"Upgrade to add more.",
            show_alert=True
        )

    data["campaigns"][str(u_id)]["targets"] = selected
    data["campaigns"][str(u_id)].pop("cache_grps", None)
    await async_update_data(data)

    await query.answer(
        f"âœ… {len(selected)} Targets Saved!", show_alert=True
    )
    await send_dash(query.message, u_id, is_edit=True)


# =====================================================
# ðŸ“ AD MESSAGE
# =====================================================
@bot.on_callback_query(filters.regex("^ask_ad_msg$"))
async def ask_ad_msg_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    data = get_data()
    current_ad = data.get("campaigns", {}).get(str(u_id), {}).get("ad_html", "")
    preview = ""
    if current_ad:
        preview = (
            f"\n\n<b>Current Ad Preview:</b>\n"
            f"<blockquote>{truncate_text(current_ad, 150)}</blockquote>"
        )

    user_state[u_id] = {"step": "wait_ad_msg", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Set Ad Message</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ ðŸ“ Send your advertisement message.\n"
        "â”‚\n"
        "â”‚ <b>Supports:</b>\n"
        "â”‚ â€¢ Bold, Italic, Underline\n"
        "â”‚ â€¢ Links & Mentions\n"
        "â”‚ â€¢ Emojis & Special chars\n"
        "â”‚ â€¢ All HTML formatting\n"
        "â”‚ â€¢ Multi-line messages\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€{preview}\n\n"
        "âš ï¸ Send your message now or /cancel:",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="open_dash")]
        ])
    )


# =====================================================
# âš™ï¸ SETTINGS WIZARD
# =====================================================
@bot.on_callback_query(filters.regex("^start_settings_wizard$"))
async def start_wizard_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    data = get_data()
    camp = data.get("campaigns", {}).get(str(u_id), {})
    current = ""
    if camp.get("group_delay"):
        d = camp.get("group_delay", 0)
        i = int(camp.get("interval", 0) / 60)
        r = camp.get("total_rounds", 0)
        r_str = "â™¾ï¸" if r > 9000000 else str(r)
        current = (
            f"\n\n<b>Current Settings:</b>\n"
            f"â³ Delay: {d}s | â±ï¸ Interval: {i}m | ðŸ”„ Rounds: {r_str}"
        )

    user_state[u_id] = {"step": "wiz_delay", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Settings Wizard</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ âš™ï¸ <b>Step 1 of 3 â€” Group Delay</b>\n"
        "â”‚\n"
        "â”‚ â³ How many <b>seconds</b> to wait\n"
        "â”‚ between sending to each group?\n"
        "â”‚\n"
        "â”‚ <b>Recommended:</b> 10 to 30 seconds\n"
        "â”‚ <b>Safe:</b> 15+ seconds\n"
        "â”‚ <b>Minimum:</b> 3 seconds\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€{current}\n\n"
        "Send a number (e.g. <code>15</code>):",
        InlineKeyboardMarkup([
            [
                InlineKeyboardButton("10s", callback_data="quick_delay_10"),
                InlineKeyboardButton("15s", callback_data="quick_delay_15"),
                InlineKeyboardButton("20s", callback_data="quick_delay_20"),
                InlineKeyboardButton("30s", callback_data="quick_delay_30"),
            ],
            [InlineKeyboardButton("âŒ Cancel", callback_data="open_dash")]
        ])
    )


@bot.on_callback_query(filters.regex(r"^quick_delay_(\d+)$"))
async def quick_delay_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    delay = int(query.matches[0].group(1))

    if u_id not in user_state or user_state[u_id].get("step") != "wiz_delay":
        user_state[u_id] = {"step": "wiz_delay", "_created": time.time()}

    user_state[u_id].update({"delay": delay, "step": "wiz_interval"})

    await safe_edit(
        query.message,
        f"ðŸ’€ <b>Settings Wizard</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âœ… Delay set to <b>{delay}s</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âš™ï¸ <b>Step 2 of 3 â€” Cycle Interval</b>\n"
        f"â”‚\n"
        f"â”‚ â±ï¸ How many <b>minutes</b> to wait\n"
        f"â”‚ between each complete round?\n"
        f"â”‚\n"
        f"â”‚ <b>Recommended:</b> 60+ minutes\n"
        f"â”‚ <b>Safe:</b> 120 minutes\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"Send a number (e.g. <code>60</code>):",
        InlineKeyboardMarkup([
            [
                InlineKeyboardButton("30m", callback_data="quick_interval_30"),
                InlineKeyboardButton("60m", callback_data="quick_interval_60"),
                InlineKeyboardButton("120m", callback_data="quick_interval_120"),
            ],
            [InlineKeyboardButton("âŒ Cancel", callback_data="open_dash")]
        ])
    )


@bot.on_callback_query(filters.regex(r"^quick_interval_(\d+)$"))
async def quick_interval_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    interval_min = int(query.matches[0].group(1))

    if u_id not in user_state:
        user_state[u_id] = {"step": "wiz_interval", "_created": time.time()}

    user_state[u_id].update({
        "interval": interval_min * 60,
        "step": "wiz_rounds"
    })

    plan_info = get_user_plan_info(u_id)
    max_rounds = plan_info.get("max_rounds", 5)

    await safe_edit(
        query.message,
        f"ðŸ’€ <b>Settings Wizard</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âœ… Interval set to <b>{interval_min}m</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âš™ï¸ <b>Step 3 of 3 â€” Total Rounds</b>\n"
        f"â”‚\n"
        f"â”‚ ðŸ”„ How many times to cycle\n"
        f"â”‚ through all target groups?\n"
        f"â”‚\n"
        f"â”‚ ðŸ“Š <b>Your limit:</b> {max_rounds} rounds\n"
        f"â”‚ Or choose Unlimited below.\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"Send a number (e.g. <code>10</code>):",
        InlineKeyboardMarkup([
            [
                InlineKeyboardButton("5", callback_data="quick_rounds_5"),
                InlineKeyboardButton("10", callback_data="quick_rounds_10"),
                InlineKeyboardButton("25", callback_data="quick_rounds_25"),
            ],
            [InlineKeyboardButton(
                "â™¾ï¸ Unlimited Rounds",
                callback_data="set_unlimited_rounds"
            )],
            [InlineKeyboardButton("âŒ Cancel", callback_data="open_dash")]
        ])
    )


@bot.on_callback_query(filters.regex(r"^quick_rounds_(\d+)$"))
async def quick_rounds_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    rounds = int(query.matches[0].group(1))

    if u_id not in user_state:
        return await query.answer(
            "âš ï¸ Session expired. Please restart settings.", show_alert=True
        )

    plan_info = get_user_plan_info(u_id)
    max_rounds = plan_info.get("max_rounds", 5)
    if rounds > max_rounds and not is_admin(u_id):
        return await query.answer(
            f"âš ï¸ Your plan allows max {max_rounds} rounds!",
            show_alert=True
        )

    d = user_state[u_id].get("delay", 10)
    i = user_state[u_id].get("interval", 600)

    data = await async_get_data()
    if str(u_id) not in data["campaigns"]:
        data["campaigns"][str(u_id)] = {"status": "IDLE"}

    data["campaigns"][str(u_id)].update({
        "group_delay": d,
        "interval": i,
        "total_rounds": rounds,
        "current_round": 1
    })
    await async_update_data(data)

    if u_id in user_state:
        del user_state[u_id]

    await safe_edit(
        query.message,
        f"ðŸ’€ <b>Settings Saved!</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ â³ <b>Group Delay:</b> {d}s\n"
        f"â”‚ â±ï¸ <b>Cycle Interval:</b> {int(i/60)}m\n"
        f"â”‚ ðŸ”„ <b>Total Rounds:</b> {rounds}\n"
        f"â”‚\n"
        f"â”‚ âœ… All settings configured!\n"
        f"â”‚ Ready to launch your campaign.\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "ðŸš€ Launch Campaign", callback_data="launch_ads"
            )],
            [InlineKeyboardButton(
                "ðŸ’» Dashboard", callback_data="open_dash"
            )]
        ])
    )


@bot.on_callback_query(filters.regex("^set_unlimited_rounds$"))
async def unlimited_rounds_cb(client, query: CallbackQuery):
    u_id = query.from_user.id

    if u_id not in user_state:
        return await query.answer(
            "âš ï¸ Session expired. Please restart settings.", show_alert=True
        )

    plan_info = get_user_plan_info(u_id)
    if plan_info.get("max_rounds", 5) < 9999 and not is_admin(u_id):
        return await query.answer(
            "âš ï¸ Unlimited rounds requires Pro or Elite plan!",
            show_alert=True
        )

    d = user_state[u_id].get("delay", 10)
    i = user_state[u_id].get("interval", 600)

    data = await async_get_data()
    if str(u_id) not in data["campaigns"]:
        data["campaigns"][str(u_id)] = {"status": "IDLE"}

    data["campaigns"][str(u_id)].update({
        "group_delay": d,
        "interval": i,
        "total_rounds": 9999999,
        "current_round": 1
    })
    await async_update_data(data)

    if u_id in user_state:
        del user_state[u_id]

    await safe_edit(
        query.message,
        f"ðŸ’€ <b>Settings Saved!</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ â³ <b>Group Delay:</b> {d}s\n"
        f"â”‚ â±ï¸ <b>Cycle Interval:</b> {int(i/60)}m\n"
        f"â”‚ ðŸ”„ <b>Rounds:</b> â™¾ï¸ Unlimited\n"
        f"â”‚\n"
        f"â”‚ âœ… All settings configured!\n"
        f"â”‚ Ready to launch your campaign.\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "ðŸš€ Launch Campaign", callback_data="launch_ads"
            )],
            [InlineKeyboardButton(
                "ðŸ’» Dashboard", callback_data="open_dash"
            )]
        ])
    )


@bot.on_callback_query(filters.regex("^ask_custom_links$"))
async def ask_custom_links_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    user_state[u_id] = {"step": "wait_custom_links", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Add Custom Group Links</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ ðŸ”— Send group usernames or links.\n"
        "â”‚ One per line, or separated by commas.\n"
        "â”‚\n"
        "â”‚ <b>Accepted Formats:</b>\n"
        "â”‚ â€¢ <code>groupusername</code>\n"
        "â”‚ â€¢ <code>@groupusername</code>\n"
        "â”‚ â€¢ <code>https://t.me/groupname</code>\n"
        "â”‚ â€¢ <code>t.me/groupname</code>\n"
        "â”‚ â€¢ <code>-1001234567890</code> (Chat ID)\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        "Send links now or /cancel:",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="target_menu")]
        ])
    )
 # =====================================================
# ðŸš€ CAMPAIGN LAUNCH & STOP
# =====================================================
@bot.on_callback_query(filters.regex("^launch_ads$"))
async def launch_ads_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    if not await check_access(u_id, query):
        return

    # Rate limit launch button
    if is_rate_limited(u_id, "launch", 5):
        return await query.answer("â³ Please wait before launching again.", show_alert=True)

    data = get_data()
    camp = data["campaigns"].get(str(u_id), {})
    active_key, active_acc = get_active_account(u_id)

    # Validation checks
    errors = []
    if not active_key or not active_acc:
        errors.append("âŒ No active account selected")
    if not camp.get("ad_html"):
        errors.append("âŒ Ad message not set")
    if not camp.get("targets"):
        errors.append("âŒ No targets configured")
    if not camp.get("group_delay"):
        errors.append("âŒ Settings not configured")

    if errors:
        error_text = "\n".join(errors)
        return await query.answer(
            f"âš ï¸ Cannot launch!\n{error_text}",
            show_alert=True
        )

    if camp.get("status") == "RUNNING":
        return await query.answer(
            "âš ï¸ Campaign is already running!", show_alert=True
        )

    total_targets = len(camp.get("targets", []))
    total_rounds = camp.get("total_rounds", 1)
    round_str = "â™¾ï¸" if total_rounds > 9000000 else str(total_rounds)

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ›‘ Stop Campaign", callback_data="stop_ads")],
        [InlineKeyboardButton("ðŸ”„ Refresh", callback_data="refresh_tracker")]
    ])

    try:
        msg = await query.message.reply_text(
            f"ðŸ’€ <b>Live Campaign Tracker</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âš¡ Initializing engine...\n"
            f"â”‚ ðŸŽ¯ Targets: <code>{total_targets}</code>\n"
            f"â”‚ ðŸ”„ Rounds: <code>{round_str}</code>\n"
            f"â”‚ Please wait...\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Tracker message error: {e}")
        return await query.answer("âŒ Failed to create tracker!", show_alert=True)

    # Update campaign state atomically
    data = await async_get_data()
    if str(u_id) not in data["campaigns"]:
        data["campaigns"][str(u_id)] = {}
    data["campaigns"][str(u_id)]["status"] = "RUNNING"
    data["campaigns"][str(u_id)]["progress_msg_id"] = msg.id
    data["campaigns"][str(u_id)]["progress_chat_id"] = u_id
    data["campaigns"][str(u_id)]["current_round"] = camp.get("current_round", 1)
    data["campaigns"][str(u_id)]["active_acc_key"] = active_key
    data["campaigns"][str(u_id)]["launch_time"] = int(time.time())
    await async_update_data(data)

    await query.answer("ðŸš€ Campaign Launched!", show_alert=True)

    try:
        await send_dash(query.message, u_id, is_edit=True)
    except Exception:
        pass


@bot.on_callback_query(filters.regex("^stop_ads$"))
async def stop_ads_cb(client, query: CallbackQuery):
    u_id = query.from_user.id
    data = await async_get_data()

    was_running = False
    if str(u_id) in data["campaigns"]:
        if data["campaigns"][str(u_id)].get("status") == "RUNNING":
            was_running = True
        data["campaigns"][str(u_id)]["status"] = "PAUSED"
        await async_update_data(data)

    if was_running:
        await safe_edit(
            query.message,
            "ðŸ’€ <b>Campaign Stopped!</b>\n\n"
            "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            "â”‚ ðŸ›‘ All engines safely halted.\n"
            "â”‚ Your progress has been saved.\n"
            "â”‚ You can resume anytime.\n"
            "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "â–¶ï¸ Resume", callback_data="launch_ads"
                )],
                [InlineKeyboardButton(
                    "ðŸ”™ Dashboard", callback_data="open_dash"
                )]
            ])
        )
        await query.answer("âœ… Campaign Stopped!", show_alert=True)
    else:
        await query.answer("â„¹ï¸ No active campaign.", show_alert=True)


# â”€â”€ Refresh Tracker â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^refresh_tracker$"))
async def refresh_tracker_cb(client, query: CallbackQuery):
    u_id = query.from_user.id

    # Rate limit refresh spam
    if is_rate_limited(u_id, "refresh_tracker", 3):
        return await query.answer("â³ Wait a moment...", show_alert=False)

    data = get_data()
    camp = data.get("campaigns", {}).get(str(u_id), {})
    stats = data["stats"].get(str(u_id), {"total_sent": 0, "failed": 0})

    if camp.get("status") != "RUNNING":
        return await query.answer(
            "â„¹ï¸ No active campaign running.", show_alert=True
        )

    total_targets = len(camp.get("targets", []))
    total_rounds = camp.get("total_rounds", 1)
    c_round = camp.get("current_round", 1)
    round_str = (
        f"{c_round}/â™¾ï¸" if total_rounds > 9000000
        else f"{c_round}/{total_rounds}"
    )

    launch_time = camp.get("launch_time", int(time.time()))
    elapsed = get_readable_time(int(time.time() - launch_time))

    text = (
        f"ðŸ’€ <b>Live Campaign Tracker</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸŸ¢ <b>Status:</b> RUNNING\n"
        f"â”‚ ðŸ”„ <b>Round:</b> {round_str}\n"
        f"â”‚ ðŸŽ¯ <b>Targets:</b> <code>{total_targets}</code>\n"
        f"â”‚ â±ï¸ <b>Elapsed:</b> <code>{elapsed}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âœ… <b>Sent:</b> <code>{stats['total_sent']:,}</code>\n"
        f"â”‚ âŒ <b>Failed:</b> <code>{stats['failed']:,}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ›‘ Stop", callback_data="stop_ads")],
            [InlineKeyboardButton("ðŸ”„ Refresh", callback_data="refresh_tracker")]
        ])
    )
    await query.answer("âœ… Refreshed!", show_alert=False)


# =====================================================
# ðŸ¤– CAMPAIGN ENGINE
# =====================================================
async def update_tracker(u_id: int, msg_id: int, text: str):
    """Update the live tracker message."""
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ›‘ Stop Campaign", callback_data="stop_ads")],
        [InlineKeyboardButton("ðŸ”„ Refresh", callback_data="refresh_tracker")]
    ])
    try:
        await bot.edit_message_text(
            chat_id=u_id,
            message_id=msg_id,
            text=text,
            reply_markup=markup,
            parse_mode=ParseMode.HTML
        )
    except MessageNotModified:
        pass
    except Exception as e:
        logger.debug(f"Tracker update error for {u_id}: {e}")


async def run_user_campaign(u_id: int):
    """Main campaign execution loop for a user."""
    logger.info(f"Campaign started for user {u_id}")

    try:
        while True:
            data = get_data()
            camp = data["campaigns"].get(str(u_id), {})

            if not camp or camp.get("status") != "RUNNING":
                logger.info(f"Campaign stopped for user {u_id} â€” status changed")
                break

            c_rnd = camp.get("current_round", 1)
            t_rnd = camp.get("total_rounds", 1)

            # Check if all rounds completed
            if c_rnd > t_rnd and t_rnd <= 9000000:
                data = await async_get_data()
                data["campaigns"][str(u_id)]["status"] = "COMPLETED"
                await async_update_data(data)
                await safe_send(
                    u_id,
                    "ðŸ’€ <b>Campaign Complete!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ âœ… All rounds finished!\n"
                    "â”‚ Launch again from dashboard.\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                )
                break

            # Get account
            acc_key = camp.get("active_acc_key") or data.get(
                "active_account", {}
            ).get(str(u_id))
            acc = data["accounts"].get(acc_key) if acc_key else None

            if not acc:
                data = await async_get_data()
                data["campaigns"][str(u_id)]["status"] = "PAUSED"
                await async_update_data(data)
                await safe_send(
                    u_id,
                    "ðŸ’€ <b>Campaign Paused!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ âš ï¸ No active account found.\n"
                    "â”‚ Please add & select an account.\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                )
                break

            # Check maintenance
            if data["settings"].get("maintenance_mode") and not is_admin(u_id):
                data = await async_get_data()
                data["campaigns"][str(u_id)]["status"] = "PAUSED"
                await async_update_data(data)
                break

            target_list = camp.get("targets", [])
            if not target_list:
                data = await async_get_data()
                data["campaigns"][str(u_id)]["status"] = "PAUSED"
                await async_update_data(data)
                break

            ad_html = camp.get("ad_html", "")
            if not ad_html:
                data = await async_get_data()
                data["campaigns"][str(u_id)]["status"] = "PAUSED"
                await async_update_data(data)
                break

            # Add global footer if set
            footer = data["settings"].get("global_ad_footer", "")
            final_ad = ad_html
            if footer:
                final_ad = f"{ad_html}\n\n{footer}"

            # Connect session
            tc = None
            try:
                tc = Client(
                    f"run_{u_id}_{int(time.time())}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=acc['session'],
                    in_memory=True
                )
                await tc.connect()

                # Warmup
                try:
                    count = 0
                    async for _ in tc.get_dialogs():
                        count += 1
                        if count > 5:
                            break
                except Exception:
                    pass

            except AuthKeyUnregistered:
                logger.warning(f"Auth key expired for user {u_id}")
                data = await async_get_data()
                if acc_key and acc_key in data["accounts"]:
                    del data["accounts"][acc_key]
                data.get("active_account", {}).pop(str(u_id), None)
                data["campaigns"][str(u_id)]["status"] = "PAUSED"
                await async_update_data(data)
                await safe_send(
                    u_id,
                    "ðŸ’€ <b>Session Expired!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ âš ï¸ Session was revoked/expired.\n"
                    "â”‚ Please login again.\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                )
                break
            except FloodWait as e:
                wait_secs = min(e.value + 5, 300)
                logger.warning(f"FloodWait on connect for {u_id}: {wait_secs}s")
                await asyncio.sleep(wait_secs)
                continue
            except Exception as e:
                logger.error(f"Campaign connect error ({u_id}): {e}")
                await asyncio.sleep(30)
                continue

            # Execute round
            snt, fld, skipped = 0, 0, 0
            total_targets = len(target_list)
            msg_id = camp.get("progress_msg_id")
            session_expired = False

            round_display = (
                f"<code>{c_rnd}</code>/â™¾ï¸"
                if t_rnd > 9000000
                else f"<code>{c_rnd}</code>/<code>{t_rnd}</code>"
            )

            for i, target in enumerate(target_list, 1):
                # Check if stopped
                check_data = get_data()
                current_status = check_data["campaigns"].get(
                    str(u_id), {}
                ).get("status")
                if current_status != "RUNNING":
                    break

                try:
                    tgt_chat = (
                        int(target)
                        if str(target).lstrip('-').isdigit()
                        else target
                    )
                    await tc.send_message(
                        chat_id=tgt_chat,
                        text=final_ad,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False
                    )
                    snt += 1
                except (ChatWriteForbidden, UserBannedInChannel, ChannelPrivate):
                    skipped += 1
                except SlowmodeWait as e:
                    wait_time = min(e.value + 2, 120)
                    await asyncio.sleep(wait_time)
                    skipped += 1
                except FloodWait as e:
                    wait_time = min(e.value + 5, 300)
                    logger.warning(f"FloodWait for {u_id}: {wait_time}s")
                    if msg_id:
                        await update_tracker(
                            u_id, msg_id,
                            f"ðŸ’€ <b>âš ï¸ Flood Wait!</b>\n\n"
                            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                            f"â”‚ â³ Telegram rate limit hit.\n"
                            f"â”‚ Waiting <code>{wait_time}s</code>...\n"
                            f"â”‚ Campaign will auto-resume.\n"
                            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                        )
                    await asyncio.sleep(wait_time)
                    fld += 1
                except AuthKeyUnregistered:
                    logger.warning(f"Session expired mid-campaign for {u_id}")
                    session_expired = True
                    fld += 1
                    data = await async_get_data()
                    if acc_key and acc_key in data["accounts"]:
                        del data["accounts"][acc_key]
                    data.get("active_account", {}).pop(str(u_id), None)
                    data["campaigns"][str(u_id)]["status"] = "PAUSED"
                    await async_update_data(data)
                    await safe_send(
                        u_id,
                        "ðŸ’€ <b>Session Expired Mid-Campaign!</b>\n"
                        "Please login again."
                    )
                    break
                except PeerIdInvalid:
                    skipped += 1
                except Forbidden:
                    skipped += 1
                except RPCError as e:
                    logger.warning(f"RPC error sending to {target}: {e}")
                    fld += 1
                except Exception as e:
                    logger.debug(f"Send error to {target}: {e}")
                    fld += 1

                # Update tracker every 3 groups or at end
                if msg_id and (i % 3 == 0 or i == total_targets):
                    pct = round((i / total_targets) * 100)
                    filled = int(pct / 10)
                    bar = "â–ˆ" * filled + "â–‘" * (10 - filled)
                    tracker_text = (
                        f"ðŸ’€ <b>Live Campaign Tracker</b>\n\n"
                        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                        f"â”‚ ðŸ”„ <b>Round:</b> {round_display}\n"
                        f"â”‚ ðŸŽ¯ <b>Targets:</b> <code>{total_targets}</code>\n"
                        f"â”‚ ðŸ“ˆ <b>Progress:</b> <code>{i}/{total_targets}</code>\n"
                        f"â”‚ [{bar}] <code>{pct}%</code>\n"
                        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                        f"â”‚ âœ… <b>Sent:</b> <code>{snt}</code>\n"
                        f"â”‚ â­ï¸ <b>Skipped:</b> <code>{skipped}</code>\n"
                        f"â”‚ âŒ <b>Failed:</b> <code>{fld}</code>\n"
                        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                    )
                    await update_tracker(u_id, msg_id, tracker_text)

                # Wait between groups
                group_delay = camp.get("group_delay", 10)
                await asyncio.sleep(group_delay)

            # Disconnect session
            try:
                if tc:
                    await tc.disconnect()
            except Exception:
                pass

            # If session expired mid-round, break out
            if session_expired:
                break

            # Save stats atomically
            data = await async_get_data()
            if str(u_id) not in data["stats"]:
                data["stats"][str(u_id)] = {"total_sent": 0, "failed": 0}
            data["stats"][str(u_id)]["total_sent"] += snt
            data["stats"][str(u_id)]["failed"] += fld

            # Check if still running
            current_status = data["campaigns"].get(
                str(u_id), {}
            ).get("status")

            if current_status == "RUNNING":
                data["campaigns"][str(u_id)]["current_round"] = c_rnd + 1
                await async_update_data(data)

                # Check if more rounds needed
                if c_rnd < t_rnd or t_rnd > 9000000:
                    interval = camp.get("interval", 600)
                    await safe_send(
                        u_id,
                        f"ðŸ’€ <b>Round {c_rnd} Complete!</b>\n\n"
                        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                        f"â”‚ âœ… Sent: <code>{snt}</code>\n"
                        f"â”‚ â­ï¸ Skipped: <code>{skipped}</code>\n"
                        f"â”‚ âŒ Failed: <code>{fld}</code>\n"
                        f"â”‚ â³ Next round in <code>{int(interval/60)}m</code>\n"
                        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                    )

                    # Wait with periodic checks
                    waited = 0
                    check_interval = 30
                    while waited < interval:
                        sleep_time = min(check_interval, interval - waited)
                        await asyncio.sleep(sleep_time)
                        waited += sleep_time
                        # Check if stopped during wait
                        check_data = get_data()
                        if check_data["campaigns"].get(
                            str(u_id), {}
                        ).get("status") != "RUNNING":
                            break
                else:
                    data["campaigns"][str(u_id)]["status"] = "COMPLETED"
                    await async_update_data(data)
                    await safe_send(
                        u_id,
                        "ðŸ’€ <b>Campaign Complete!</b>\n\n"
                        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                        "â”‚ âœ… All rounds finished!\n"
                        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
                    )
                    break
            else:
                await async_update_data(data)
                break

    except asyncio.CancelledError:
        logger.info(f"Campaign cancelled for user {u_id}")
    except Exception as e:
        logger.error(f"Campaign engine error ({u_id}): {e}")
        traceback.print_exc()
        # Try to pause campaign on unhandled error
        try:
            data = await async_get_data()
            if str(u_id) in data["campaigns"]:
                data["campaigns"][str(u_id)]["status"] = "PAUSED"
                await async_update_data(data)
            await safe_send(
                u_id,
                f"ðŸ’€ <b>Campaign Error!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ âŒ Unexpected error occurred.\n"
                f"â”‚ Campaign has been paused.\n"
                f"â”‚ Try resuming from dashboard.\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            )
        except Exception:
            pass
    finally:
        if u_id in active_tasks:
            del active_tasks[u_id]
        logger.info(f"Campaign task ended for user {u_id}")


async def ad_engine():
    """Main engine dispatcher â€” checks for campaigns to run."""
    logger.info("ðŸ”¥ Ad Engine started!")
    while True:
        try:
            data = get_data()
            for uid_str, camp in list(data.get("campaigns", {}).items()):
                if camp.get("status") == "RUNNING":
                    u_id = int(uid_str)
                    if u_id not in active_tasks:
                        task = asyncio.create_task(
                            run_user_campaign(u_id)
                        )
                        active_tasks[u_id] = task
                        logger.info(
                            f"Started campaign task for user {u_id}"
                        )
        except Exception as e:
            logger.error(f"Engine dispatcher error: {e}")
        await asyncio.sleep(5)


# =====================================================
# âŒ¨ï¸ BASIC COMMANDS
# =====================================================
@bot.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client, message: Message):
    u_id = message.from_user.id
    # Safely disconnect any pending login client
    if u_id in user_state:
        state = user_state[u_id]
        tc = state.get("client")
        if tc:
            try:
                await tc.disconnect()
            except Exception:
                pass
        del user_state[u_id]
    await message.reply_text(
        "âŒ <b>Action Cancelled.</b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ’» Dashboard", callback_data="open_dash")],
            [InlineKeyboardButton("ðŸ  Main Menu", callback_data="back_start")]
        ]),
        parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("reset") & filters.private)
async def reset_cmd(client, message: Message):
    u_id = message.from_user.id
    # Safely disconnect any pending login client
    if u_id in user_state:
        state = user_state[u_id]
        tc = state.get("client")
        if tc:
            try:
                await tc.disconnect()
            except Exception:
                pass
        del user_state[u_id]
    data = await async_get_data()
    if str(u_id) in data["campaigns"]:
        data["campaigns"][str(u_id)]["status"] = "PAUSED"
        await async_update_data(data)
    await message.reply_text(
        "ðŸ’€ <b>System Reset!</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ âœ… All stuck states cleared.\n"
        "â”‚ âœ… Campaign paused safely.\n"
        "â”‚ âœ… Ready for fresh start!\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "ðŸ’» Open Dashboard", callback_data="open_dash"
            )]
        ]),
        parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("ping") & filters.private)
async def ping_cmd(client, message: Message):
    # Rate limit ping
    if is_rate_limited(message.from_user.id, "ping", 3):
        return

    start_t = time.time()
    rm = await message.reply_text(
        "ðŸ”„ <b>Checking...</b>", parse_mode=ParseMode.HTML
    )
    ping_ms = round((time.time() - start_t) * 1000, 2)
    up = get_readable_time(int(time.time() - BOT_START_TIME))
    data = get_data()
    running = sum(
        1 for c in data["campaigns"].values()
        if c.get("status") == "RUNNING"
    )
    total_users = len(data["users"])
    total_accounts = len(data["accounts"])
    db_size = get_readable_size(
        os.path.getsize(DATA_FILE)
    ) if os.path.exists(DATA_FILE) else "0 B"

    await rm.edit_text(
        f"ðŸ’€ <b>Skull Ads â€” System Status</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âš¡ <b>Ping:</b> <code>{ping_ms} ms</code>\n"
        f"â”‚ â±ï¸ <b>Uptime:</b> <code>{up}</code>\n"
        f"â”‚ ðŸ–¥ï¸ <b>Server:</b> Online ðŸŸ¢\n"
        f"â”‚ ðŸ’¾ <b>Storage:</b> <code>{db_size}</code> ðŸŸ¢\n"
        f"â”‚ ðŸ¤– <b>Engine:</b> Active ðŸŸ¢\n"
        f"â”‚ ðŸš€ <b>Campaigns:</b> <code>{running}</code> running\n"
        f"â”‚ âš¡ <b>Tasks:</b> <code>{len(active_tasks)}</code> active\n"
        f"â”‚ ðŸ‘¥ <b>Users:</b> <code>{total_users}</code>\n"
        f"â”‚ ðŸ”‘ <b>Sessions:</b> <code>{total_accounts}</code>\n"
        f"â”‚ ðŸ¤– <b>Version:</b> <code>v{BOT_VERSION}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("myid") & filters.private)
async def myid_cmd(client, message: Message):
    u_id = message.from_user.id
    name = message.from_user.first_name or "Unknown"
    uname = f"@{message.from_user.username}" if message.from_user.username else "None"
    await message.reply_text(
        f"ðŸ’€ <b>Your Info</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¤ <b>Name:</b> {sanitize_html(name)}\n"
        f"â”‚ ðŸ†” <b>ID:</b> <code>{u_id}</code>\n"
        f"â”‚ ðŸ”— <b>Username:</b> {uname}\n"
        f"â”‚ ðŸ’Ž <b>Plan:</b> {get_user_plan_name(u_id)}\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
        parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message: Message):
    await message.reply_text(
        "ðŸ“– <b>Commands</b>\n\n"
        "/start â€” Main menu\n"
        "/ping â€” Bot status\n"
        "/reset â€” Reset stuck states\n"
        "/cancel â€” Cancel action\n"
        "/myid â€” Your user ID\n"
        "/help â€” This message\n"
        "/referral â€” Referral link\n\n"
        "<b>Admin Only:</b>\n"
        "/panel â€” Admin panel\n"
        "/ban â€” Ban user\n"
        "/unban â€” Unban user\n"
        "/addpremium â€” Add premium\n"
        "/removepremium â€” Remove premium\n"
        "/broadcast â€” Broadcast msg\n"
        "/maintenance â€” Toggle maintenance\n"
        "/pauseall â€” Pause all campaigns\n"
        "/resumeall â€” Resume campaigns\n"
        "/getdb â€” Download database\n"
        "/uploaddb â€” Restore database\n"
        "/userinfo â€” User details\n"
        "/listusers â€” List all users\n"
        "/listpremium â€” List premium\n"
        "/listbanned â€” List banned\n"
        "/searchuser â€” Search users\n"
        "/resetdb â€” Reset database\n"
        "/globalfooter â€” Set ad footer\n"
        "/forcejoin â€” Set force join\n"
        "/logs â€” Admin action logs",
        parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("referral") & filters.private)
async def referral_cmd(client, message: Message):
    u_id = message.from_user.id
    data = get_data()
    ref_count = len(data.get("referrals", {}).get(str(u_id), []))
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{u_id}"
    await message.reply_text(
        f"ðŸ’€ <b>Your Referral Link</b>\n\n"
        f"ðŸ”— <code>{ref_link}</code>\n\n"
        f"ðŸ‘¥ Total Referrals: <code>{ref_count}</code>",
        parse_mode=ParseMode.HTML
    )


@bot.on_callback_query(filters.regex("^noop$"))
async def noop_cb(client, query: CallbackQuery):
    await query.answer()


# =====================================================
# âŒ¨ï¸ MASTER INPUT HANDLER â€” FIXED OTP & PHONE
# =====================================================
ADMIN_COMMANDS = [
    "start", "cancel", "reset", "ping", "help", "myid", "referral",
    "broadcast", "pbroadcast", "master_broadcast",
    "ban", "unban", "maintenance",
    "pauseall", "resumeall",
    "panel", "getdb", "uploaddb", "resetdb",
    "addpremium", "removepremium",
    "userinfo", "listusers", "listbanned",
    "listpremium", "searchuser",
    "globalfooter", "forcejoin", "logs",
    "setfooter", "setwelcome"
]


@bot.on_message(
    filters.private & ~filters.command(ADMIN_COMMANDS)
)
async def master_handler(client, message: Message):
    u_id = message.from_user.id

    if not await check_access(u_id, message):
        return

    if u_id not in user_state:
        return

    step = user_state[u_id].get("step")
    text = message.text.strip() if message.text else ""

    # â”€â”€ PHONE NUMBER â€” Fixed with normalization â”€â”€â”€
       # â”€â”€ PHONE NUMBER â€” BULLETPROOF â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if step == "wait_phone":
        # Get raw text safely
        raw_text = ""
        if message.text:
            raw_text = message.text
        elif message.caption:
            raw_text = message.caption

        raw_text = raw_text.strip()

        if not raw_text:
            return await message.reply_text(
                "âŒ Please send your phone number as text.",
                parse_mode=ParseMode.HTML
            )

        # Normalize phone number
        phone, error = normalize_phone_number(raw_text)
        if error:
            return await message.reply_text(error, parse_mode=ParseMode.HTML)

        # Check if already logged in with this phone
        existing = get_user_accounts(u_id)
        for acc in existing.values():
            if acc.get("phone") == phone:
                if u_id in user_state:
                    del user_state[u_id]
                return await message.reply_text(
                    f"âš ï¸ <b>This phone is already linked!</b>\n"
                    f"ðŸ“± <tg-spoiler>{phone}</tg-spoiler>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "ðŸ‘¥ Accounts", callback_data="accounts_menu"
                        )]
                    ]),
                    parse_mode=ParseMode.HTML
                )

        w_msg = await message.reply_text(
            f"ðŸ’€ <b>Connecting to Telegram...</b>\n"
            f"ðŸ“± Number: <tg-spoiler>{phone}</tg-spoiler>\n"
            f"â³ Sending OTP...",
            parse_mode=ParseMode.HTML
        )

        tc = Client(
            f"login_{u_id}_{int(time.time())}",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )

        try:
            await tc.connect()
            code = await tc.send_code(phone)

            user_state[u_id] = {
                "step": "wait_otp",
                "phone": phone,
                "hash": code.phone_code_hash,
                "client": tc,
                "_created": time.time()
            }

            logger.info(f"OTP sent successfully to {u_id} for {phone}")

            await w_msg.edit_text(
                "ðŸ’€ <b>OTP Sent! âœ…</b>\n\n"
                "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                "â”‚ ðŸ“© Check your Telegram app.\n"
                "â”‚\n"
                "â”‚ <b>Just type the OTP normally:</b>\n"
                "â”‚\n"
                "â”‚ âœ… <code>12345</code> â€” works!\n"
                "â”‚ âœ… <code>1 2 3 4 5</code> â€” works!\n"
                "â”‚ âœ… <code>1-2-3-4-5</code> â€” works!\n"
                "â”‚ âœ… <code>12 345</code> â€” works!\n"
                "â”‚\n"
                "â”‚ ðŸ’¡ Bot auto-detects digits.\n"
                "â”‚ âš ï¸ OTP expires in 2 minutes!\n"
                "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                parse_mode=ParseMode.HTML
            )

        except FloodWait as e:
            try:
                await tc.disconnect()
            except Exception:
                pass
            if u_id in user_state:
                del user_state[u_id]
            await w_msg.edit_text(
                f"ðŸ’€ <b>Rate Limited!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ â³ Telegram says wait\n"
                f"â”‚ <code>{e.value}</code> seconds.\n"
                f"â”‚ Try again after that.\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("ðŸ” Retry", callback_data="login_acc")]
                ]),
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            try:
                await tc.disconnect()
            except Exception:
                pass
            if u_id in user_state:
                del user_state[u_id]

            error_str = str(e)
            logger.warning(f"Login send_code error for {u_id}: {error_str}")

            # Handle specific errors
            if "PHONE_NUMBER_INVALID" in error_str.upper():
                await w_msg.edit_text(
                    "ðŸ’€ <b>Invalid Phone Number!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ âŒ Telegram rejected this number.\n"
                    "â”‚ Make sure country code is correct.\n"
                    "â”‚\n"
                    "â”‚ <b>Examples:</b>\n"
                    "â”‚ â€¢ <code>+919876543210</code> (India)\n"
                    "â”‚ â€¢ <code>+12025551234</code> (US)\n"
                    "â”‚ â€¢ <code>+447911123456</code> (UK)\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ðŸ” Retry", callback_data="login_acc")]
                    ]),
                    parse_mode=ParseMode.HTML
                )
            elif "PHONE_NUMBER_BANNED" in error_str.upper():
                await w_msg.edit_text(
                    "ðŸ’€ <b>Phone Number Banned!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ ðŸš« This number is banned by Telegram.\n"
                    "â”‚ Try a different number.\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ðŸ” Try Another", callback_data="login_acc")]
                    ]),
                    parse_mode=ParseMode.HTML
                )
            else:
                await w_msg.edit_text(
                    f"ðŸ’€ <b>Connection Failed!</b>\n\n"
                    f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    f"â”‚ âŒ {sanitize_html(error_str[:150])}\n"
                    f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ðŸ” Retry", callback_data="login_acc")]
                    ]),
                    parse_mode=ParseMode.HTML
                )
      # â”€â”€ OTP â€” BULLETPROOF FIX â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wait_otp":
        tc = user_state[u_id].get("client")
        if not tc:
            if u_id in user_state:
                del user_state[u_id]
            return await message.reply_text(
                "âŒ Session expired. Please try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "ðŸ” Retry", callback_data="login_acc"
                    )]
                ]),
                parse_mode=ParseMode.HTML
            )

        # Get raw text â€” handle None safely
        raw_text = ""
        if message.text:
            raw_text = message.text
        elif message.caption:
            raw_text = message.caption

        raw_text = raw_text.strip()

        if not raw_text:
            return await message.reply_text(
                "âŒ <b>Please type the OTP code.</b>\n\n"
                "Example: <code>12345</code>",
                parse_mode=ParseMode.HTML
            )

        # Normalize OTP â€” extracts digits from ANY format
        otp, error = normalize_otp(raw_text)
        if error:
            return await message.reply_text(error, parse_mode=ParseMode.HTML)

        # Show processing message
        proc_msg = await message.reply_text(
            "ðŸ’€ <b>Verifying OTP...</b> â³",
            parse_mode=ParseMode.HTML
        )

        try:
            phone = user_state[u_id].get("phone", "")
            phone_hash = user_state[u_id].get("hash", "")

            logger.info(f"OTP attempt for {u_id}: {len(otp)} digits")

            await tc.sign_in(
                phone_number=phone,
                phone_code_hash=phone_hash,
                phone_code=otp
            )

            try:
                await proc_msg.delete()
            except Exception:
                pass

            await finish_login(
                message, tc, u_id, phone
            )

        except SessionPasswordNeeded:
            try:
                await proc_msg.delete()
            except Exception:
                pass

            user_state[u_id]["step"] = "wait_pass"
            await message.reply_text(
                "ðŸ’€ <b>2FA Password Required!</b>\n\n"
                "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                "â”‚ ðŸ” Your account has Two-Factor\n"
                "â”‚ Authentication enabled.\n"
                "â”‚\n"
                "â”‚ Send your 2FA password now:\n"
                "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                parse_mode=ParseMode.HTML
            )

        except Exception as e:
            try:
                await proc_msg.delete()
            except Exception:
                pass

            error_str = str(e)
            logger.warning(f"OTP sign_in error for {u_id}: {error_str}")

            # Check if OTP expired
            if "PHONE_CODE_EXPIRED" in error_str.upper():
                try:
                    await tc.disconnect()
                except Exception:
                    pass
                if u_id in user_state:
                    del user_state[u_id]
                return await message.reply_text(
                    "ðŸ’€ <b>OTP Expired!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ â° The OTP has expired.\n"
                    "â”‚ Please start login again.\n"
                    "â”‚\n"
                    "â”‚ ðŸ’¡ <b>Next time send OTP like:</b>\n"
                    "â”‚ â€¢ <code>5 0 8 5 9</code>\n"
                    "â”‚ â€¢ <code>1 2 3 4 5</code>\n"
                    "â”‚ â€¢ <code>1-2-3-4-5</code>\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "ðŸ” Login Again", callback_data="login_acc"
                        )]
                    ]),
                    parse_mode=ParseMode.HTML
                )

            # Check if OTP is wrong
            if "PHONE_CODE_INVALID" in error_str.upper():
                return await message.reply_text(
                    "ðŸ’€ <b>Wrong OTP!</b>\n\n"
                    "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                    "â”‚ âŒ The code you entered is wrong.\n"
                    "â”‚ Check your Telegram app and\n"
                    "â”‚ send the correct OTP.\n"
                    "â”‚\n"
                    "â”‚ Just type the digits:\n"
                    "â”‚ Example: <code>12345</code>\n"
                    "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                    parse_mode=ParseMode.HTML
                )

            # Other errors â€” cleanup and retry
            try:
                await tc.disconnect()
            except Exception:
                pass
            if u_id in user_state:
                del user_state[u_id]

            await message.reply_text(
                f"ðŸ’€ <b>Login Error!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ âŒ {sanitize_html(error_str[:150])}\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "ðŸ” Retry", callback_data="login_acc"
                    )]
                ]),
                parse_mode=ParseMode.HTML
            )

    # â”€â”€ 2FA PASSWORD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wait_pass":
        tc = user_state[u_id].get("client")
        if not tc:
            if u_id in user_state:
                del user_state[u_id]
            return await message.reply_text(
                "âŒ Session expired. Please try again.",
                parse_mode=ParseMode.HTML
            )
        try:
            await tc.check_password(text)
            await finish_login(
                message, tc, u_id, user_state[u_id]["phone"]
            )
        except Exception as e:
            try:
                await tc.disconnect()
            except Exception:
                pass
            if u_id in user_state:
                del user_state[u_id]
            logger.warning(f"2FA check_password error for {u_id}: {e}")
            await message.reply_text(
                f"ðŸ’€ <b>Wrong Password!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ âŒ {sanitize_html(str(e)[:150])}\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
                f"Try again with /start",
                parse_mode=ParseMode.HTML
            )

    # â”€â”€ SETTINGS STEP 1: DELAY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wiz_delay":
        if not text.isdigit() or int(text) < 3:
            return await message.reply_text(
                "âŒ <b>Invalid!</b> Minimum 3 seconds.\n"
                "Send a number (e.g. <code>15</code>)",
                parse_mode=ParseMode.HTML
            )
        delay_val = min(int(text), 300)
        user_state[u_id].update({
            "delay": delay_val, "step": "wiz_interval"
        })
        await message.reply_text(
            f"ðŸ’€ <b>Settings Wizard</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âœ… Delay set to <b>{delay_val}s</b>\n"
            f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âš™ï¸ <b>Step 2 of 3 â€” Cycle Interval</b>\n"
            f"â”‚\n"
            f"â”‚ â±ï¸ How many <b>minutes</b> to wait\n"
            f"â”‚ between each complete round?\n"
            f"â”‚\n"
            f"â”‚ <b>Recommended:</b> 60+ minutes\n"
            f"â”‚ <b>Safe:</b> 120 minutes\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
            f"Send a number (e.g. <code>60</code>):",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "30m", callback_data="quick_interval_30"
                    ),
                    InlineKeyboardButton(
                        "60m", callback_data="quick_interval_60"
                    ),
                    InlineKeyboardButton(
                        "120m", callback_data="quick_interval_120"
                    ),
                ],
                [InlineKeyboardButton(
                    "âŒ Cancel", callback_data="open_dash"
                )]
            ]),
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ SETTINGS STEP 2: INTERVAL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wiz_interval":
        if not text.isdigit() or int(text) < 1:
            return await message.reply_text(
                "âŒ <b>Invalid!</b> Minimum 1 minute.\n"
                "Send a number (e.g. <code>60</code>)",
                parse_mode=ParseMode.HTML
            )
        interval_val = min(int(text), 1440) * 60
        user_state[u_id].update({
            "interval": interval_val,
            "step": "wiz_rounds"
        })

        plan_info = get_user_plan_info(u_id)
        max_rounds = plan_info.get("max_rounds", 5)

        await message.reply_text(
            f"ðŸ’€ <b>Settings Wizard</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âœ… Interval set to <b>{int(interval_val/60)}m</b>\n"
            f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âš™ï¸ <b>Step 3 of 3 â€” Total Rounds</b>\n"
            f"â”‚\n"
            f"â”‚ ðŸ”„ How many times to cycle?\n"
            f"â”‚ ðŸ“Š <b>Your limit:</b> {max_rounds}\n"
            f"â”‚ Or choose Unlimited below.\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
            f"Send a number (e.g. <code>10</code>):",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "5", callback_data="quick_rounds_5"
                    ),
                    InlineKeyboardButton(
                        "10", callback_data="quick_rounds_10"
                    ),
                    InlineKeyboardButton(
                        "25", callback_data="quick_rounds_25"
                    ),
                ],
                [InlineKeyboardButton(
                    "â™¾ï¸ Unlimited",
                    callback_data="set_unlimited_rounds"
                )],
                [InlineKeyboardButton(
                    "âŒ Cancel", callback_data="open_dash"
                )]
            ]),
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ SETTINGS STEP 3: ROUNDS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wiz_rounds":
        if not text.isdigit() or int(text) < 1:
            return await message.reply_text(
                "âŒ <b>Invalid!</b> Minimum 1 round.\n"
                "Send a number (e.g. <code>10</code>)",
                parse_mode=ParseMode.HTML
            )

        rounds_val = int(text)
        plan_info = get_user_plan_info(u_id)
        max_rounds = plan_info.get("max_rounds", 5)

        if rounds_val > max_rounds and not is_admin(u_id):
            return await message.reply_text(
                f"âš ï¸ Your plan allows max <b>{max_rounds}</b> rounds!\n"
                f"Upgrade to increase limit.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "ðŸ’Ž Upgrade", callback_data="show_plans"
                    )]
                ]),
                parse_mode=ParseMode.HTML
            )

        d = user_state[u_id].get("delay", 10)
        i = user_state[u_id].get("interval", 600)

        data = await async_get_data()
        if str(u_id) not in data["campaigns"]:
            data["campaigns"][str(u_id)] = {"status": "IDLE"}
        data["campaigns"][str(u_id)].update({
            "group_delay": d,
            "interval": i,
            "total_rounds": rounds_val,
            "current_round": 1
        })
        await async_update_data(data)

        if u_id in user_state:
            del user_state[u_id]

        await message.reply_text(
            f"ðŸ’€ <b>Settings Saved!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ â³ <b>Group Delay:</b> {d}s\n"
            f"â”‚ â±ï¸ <b>Cycle Interval:</b> {int(i/60)}m\n"
            f"â”‚ ðŸ”„ <b>Total Rounds:</b> {rounds_val}\n"
            f"â”‚\n"
            f"â”‚ âœ… All settings configured!\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "ðŸš€ Launch Campaign", callback_data="launch_ads"
                )],
                [InlineKeyboardButton(
                    "ðŸ’» Dashboard", callback_data="open_dash"
                )]
            ]),
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ CUSTOM LINKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wait_custom_links":
        raw = text.replace(",", "\n").replace(" ", "\n").split("\n")
        links = []
        for l in raw:
            l = l.strip()
            if not l:
                continue
            l = l.replace("https://t.me/", "")
            l = l.replace("http://t.me/", "")
            l = l.replace("t.me/", "")
            l = l.replace("@", "")
            if l.startswith("+") or l.startswith("joinchat/"):
                continue
            if l:
                links.append(l)

        if not links:
            return await message.reply_text(
                "âŒ <b>No valid links found!</b>\n\n"
                "Send group usernames or t.me links.",
                parse_mode=ParseMode.HTML
            )

        plan_info = get_user_plan_info(u_id)
        max_targets = plan_info.get("max_targets", 50)
        if len(links) > max_targets and not is_admin(u_id):
            links = links[:max_targets]

        data = await async_get_data()
        if str(u_id) not in data["campaigns"]:
            data["campaigns"][str(u_id)] = {"status": "IDLE"}
        data["campaigns"][str(u_id)]["targets"] = links
        await async_update_data(data)

        if u_id in user_state:
            del user_state[u_id]

        await message.reply_text(
            f"ðŸ’€ <b>Custom Targets Saved!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âœ… <b>{len(links)}</b> group(s) added.\n"
            f"â”‚ Ready to use in campaigns!\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "ðŸš€ Launch Campaign", callback_data="launch_ads"
                )],
                [InlineKeyboardButton(
                    "ðŸ’» Dashboard", callback_data="open_dash"
                )]
            ]),
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ AD MESSAGE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "wait_ad_msg":
        html_content = ""
        if message.text:
            try:
                html_content = message.text.html
            except Exception:
                html_content = message.text
        elif message.caption:
            try:
                html_content = message.caption.html
            except Exception:
                html_content = message.caption

        if not html_content:
            return await message.reply_text(
                "âŒ <b>Please send a text message</b> as your ad.\n\n"
                "Media-only messages are not supported yet.",
                parse_mode=ParseMode.HTML
            )

        data = await async_get_data()
        if str(u_id) not in data["campaigns"]:
            data["campaigns"][str(u_id)] = {"status": "IDLE"}
        data["campaigns"][str(u_id)]["ad_html"] = html_content
        await async_update_data(data)

        if u_id in user_state:
            del user_state[u_id]

        preview = truncate_text(html_content, 100)
        await message.reply_text(
            f"ðŸ’€ <b>Ad Message Saved!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âœ… Ad message is ready.\n"
            f"â”‚ ðŸ“ Length: <code>{len(html_content)}</code> chars\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
            f"<b>Preview:</b>\n<blockquote>{preview}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "ðŸš€ Launch Campaign", callback_data="launch_ads"
                )],
                [InlineKeyboardButton(
                    "ðŸ’» Dashboard", callback_data="open_dash"
                )]
            ]),
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ ADMIN: CONFIRM RESET DB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_confirm_reset":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if text == "CONFIRM RESET":
            if u_id in user_state:
                del user_state[u_id]
            current_data = get_data()
            emergency_file = f"emergency_backup_{int(time.time())}.json"
            try:
                with open(emergency_file, "w", encoding="utf-8") as f:
                    json.dump(current_data, f, indent=2)
            except Exception as be:
                logger.warning(f"Emergency backup error: {be}")
            await async_update_data(DEFAULT_DATA.copy())
            add_admin_log("RESET_DATABASE", u_id, "Full database reset")
            await message.reply_text(
                f"ðŸ’€ <b>DATABASE WIPED!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ âœ… All data deleted.\n"
                f"â”‚ ðŸ’¾ Backup: <code>{emergency_file}</code>\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                parse_mode=ParseMode.HTML
            )
        else:
            if u_id in user_state:
                del user_state[u_id]
            await message.reply_text(
                "âŒ <b>Reset Cancelled.</b> Text didn't match.",
                parse_mode=ParseMode.HTML
            )

    # â”€â”€ ADMIN: SEARCH USER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_search_user":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        data = get_data()
        query_str = text.lower()
        results = []
        for uid_str, u in data["users"].items():
            if (
                query_str in str(u.get("user_id", "")).lower() or
                query_str in u.get("name", "").lower() or
                query_str in u.get("username", "").lower()
            ):
                results.append((uid_str, u))

        if not results:
            return await message.reply_text(
                "ðŸ’€ <b>No users found.</b>",
                parse_mode=ParseMode.HTML
            )

        result_text = (
            f"ðŸ’€ <b>Search Results ({len(results)} found)</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        )
        for uid_str, u in results[:10]:
            uid_int = u.get("user_id", "?")
            name = truncate_text(u.get("name", "N/A"), 15)
            uname = f"@{u['username']}" if u.get("username") else "No @"
            plan = get_user_plan_name(uid_int) if isinstance(uid_int, int) else "?"
            is_banned = uid_int in data.get("banned_users", [])
            tag = " ðŸš«" if is_banned else ""
            result_text += (
                f"â”‚ <code>{uid_int}</code>{tag} â€” {sanitize_html(name)}\n"
                f"â”‚ {uname} | {plan}\nâ”‚\n"
            )
        if len(results) > 10:
            result_text += f"â”‚ ... +{len(results) - 10} more\n"
        result_text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
        await message.reply_text(result_text, parse_mode=ParseMode.HTML)

    # â”€â”€ ADMIN: ADD PREMIUM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_add_premium":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        parts = text.split()
        if len(parts) < 2:
            return await message.reply_text(
                "âŒ Format: <code>[user_id] [plan]</code>\n"
                "Plans: basic | pro | elite",
                parse_mode=ParseMode.HTML
            )
        try:
            target_id = int(parts[0])
            plan_key = parts[1].lower()
            if plan_key not in PLANS or plan_key == "free":
                return await message.reply_text(
                    "âŒ Invalid plan. Use: basic | pro | elite",
                    parse_mode=ParseMode.HTML
                )
            data = await async_get_data()
            data["premium_users"][str(target_id)] = {
                "plan": plan_key,
                "added_by": u_id,
                "added_date": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            await async_update_data(data)
            plan_info = PLANS[plan_key]
            add_admin_log(
                "ADD_PREMIUM", u_id,
                f"User {target_id} â†’ {plan_key}"
            )
            await message.reply_text(
                f"ðŸ’€ <b>Premium Added!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ ðŸ†” {target_id} â†’ {plan_info['name']}\n"
                f"â”‚ ðŸ‘¥ Slots: {plan_info['accounts']}\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
                parse_mode=ParseMode.HTML
            )
            await safe_send(
                target_id,
                f"ðŸ’€ <b>Premium Activated!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ ðŸŽ‰ Plan: {plan_info['name']}\n"
                f"â”‚ ðŸ‘¥ Account Slots: {plan_info['accounts']}\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
                f"@securedsitedns | @securedsitedns"
            )
        except ValueError:
            await message.reply_text(
                "âŒ Invalid user ID.",
                parse_mode=ParseMode.HTML
            )

    # â”€â”€ ADMIN: REMOVE PREMIUM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_remove_premium":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        try:
            target_id = str(int(text.strip()))
            data = await async_get_data()
            removed = target_id in data.get("premium_users", {})
            if removed:
                del data["premium_users"][target_id]
                await async_update_data(data)
                add_admin_log(
                    "REMOVE_PREMIUM", u_id, f"User {target_id}"
                )
            await message.reply_text(
                f"ðŸ’€ <b>{'Premium Removed' if removed else 'Not Found'}!</b>\n"
                f"ðŸ†” ID: <code>{target_id}</code>",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await message.reply_text(
                "âŒ Invalid ID.",
                parse_mode=ParseMode.HTML
            )

    # â”€â”€ ADMIN: SET GLOBAL FOOTER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_set_footer":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        data = await async_get_data()
        if text.lower() in ["none", "clear", "remove", "off"]:
            data["settings"]["global_ad_footer"] = ""
            await async_update_data(data)
            return await message.reply_text(
                "âœ… Global footer cleared!",
                parse_mode=ParseMode.HTML
            )
        data["settings"]["global_ad_footer"] = text
        await async_update_data(data)
        add_admin_log("SET_FOOTER", u_id, truncate_text(text, 50))
        await message.reply_text(
            f"âœ… <b>Global footer set!</b>\n\n"
            f"Preview: {truncate_text(text, 100)}",
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ ADMIN: SET FORCE JOIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_set_forcejoin":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        data = await async_get_data()
        if text.lower() in ["none", "clear", "remove", "off"]:
            data["settings"]["force_join_channel"] = ""
            await async_update_data(data)
            return await message.reply_text(
                "âœ… Force join disabled!",
                parse_mode=ParseMode.HTML
            )
        channel = text.strip()
        if not channel.startswith("@"):
            channel = f"@{channel}"
        data["settings"]["force_join_channel"] = channel
        await async_update_data(data)
        add_admin_log("SET_FORCEJOIN", u_id, channel)
        await message.reply_text(
            f"âœ… <b>Force join set!</b>\n"
            f"Channel: <code>{channel}</code>",
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ ADMIN: BROADCAST MESSAGE TEXT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_broadcast_text":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        data = get_data()
        total = len(data["users"])
        msg = await message.reply_text(
            f"ðŸ“¢ <b>Broadcasting to {total} users...</b>",
            parse_mode=ParseMode.HTML
        )
        s, f_count = 0, 0
        for uid_str in data["users"]:
            try:
                await bot.send_message(
                    int(uid_str), text,
                    parse_mode=ParseMode.HTML
                )
                s += 1
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                try:
                    await bot.send_message(
                        int(uid_str), text,
                        parse_mode=ParseMode.HTML
                    )
                    s += 1
                except Exception:
                    f_count += 1
            except Exception:
                f_count += 1
            await asyncio.sleep(0.05)

        data = await async_get_data()
        data["settings"]["total_broadcasts"] = (
            data["settings"].get("total_broadcasts", 0) + 1
        )
        await async_update_data(data)
        add_admin_log(
            "BROADCAST", u_id,
            f"Sent: {s}, Failed: {f_count}"
        )
        await msg.edit_text(
            f"ðŸ’€ <b>Broadcast Done!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âœ… Sent: <code>{s}</code>\n"
            f"â”‚ âŒ Failed: <code>{f_count}</code>\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            parse_mode=ParseMode.HTML
        )

    # â”€â”€ ADMIN: PREMIUM BROADCAST TEXT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    elif step == "adm_broadcast_premium_text":
        if not is_admin(u_id):
            if u_id in user_state:
                del user_state[u_id]
            return

        if u_id in user_state:
            del user_state[u_id]
        data = get_data()
        premium_ids = list(data.get("premium_users", {}).keys())

        if not premium_ids:
            return await message.reply_text(
                "âŒ No premium users to broadcast to!",
                parse_mode=ParseMode.HTML
            )

        msg = await message.reply_text(
            f"ðŸ“¢ <b>Premium Broadcast...</b>\n"
            f"Target: <code>{len(premium_ids)}</code> premium users",
            parse_mode=ParseMode.HTML
        )

        s, f_count = 0, 0
        for uid_str in premium_ids:
            try:
                await bot.send_message(
                    int(uid_str), text,
                    parse_mode=ParseMode.HTML
                )
                s += 1
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                try:
                    await bot.send_message(
                        int(uid_str), text,
                        parse_mode=ParseMode.HTML
                    )
                    s += 1
                except Exception:
                    f_count += 1
            except Exception:
                f_count += 1
            await asyncio.sleep(0.05)

        data = await async_get_data()
        data["settings"]["total_broadcasts"] = (
            data["settings"].get("total_broadcasts", 0) + 1
        )
        await async_update_data(data)
        add_admin_log(
            "PREMIUM_BROADCAST", u_id,
            f"Sent: {s}, Failed: {f_count}"
        )

        await msg.edit_text(
            f"ðŸ’€ <b>Premium Broadcast Done!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ âœ… Sent: <code>{s}</code>\n"
            f"â”‚ âŒ Failed: <code>{f_count}</code>\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            parse_mode=ParseMode.HTML
        )


# =====================================================
# ðŸ“Š SYSTEM STATS HELPER
# =====================================================
def get_system_stats() -> dict:
    """Get comprehensive system statistics."""
    data = get_data()
    total_users = len(data.get("users", {}))
    banned = len(data.get("banned_users", []))
    premium_count = len(data.get("premium_users", {}))
    total_accounts = len(data.get("accounts", {}))

    campaigns = data.get("campaigns", {})
    running = sum(1 for c in campaigns.values() if c.get("status") == "RUNNING")
    paused = sum(1 for c in campaigns.values() if c.get("status") == "PAUSED")
    completed = sum(1 for c in campaigns.values() if c.get("status") == "COMPLETED")
    idle_camps = sum(1 for c in campaigns.values() if c.get("status") == "IDLE")
    total_targets = sum(len(c.get("targets", [])) for c in campaigns.values())
    total_with_ad = sum(1 for c in campaigns.values() if c.get("ad_html"))
    total_configured = sum(1 for c in campaigns.values() if c.get("group_delay"))

    stats = data.get("stats", {})
    total_sent = sum(s.get("total_sent", 0) for s in stats.values())
    total_failed = sum(s.get("failed", 0) for s in stats.values())

    settings = data.get("settings", {})
    logins = settings.get("lifetime_logins", 0)
    logouts = settings.get("lifetime_logouts", 0)
    m_mode = settings.get("maintenance_mode", False)
    bot_starts = settings.get("bot_start_count", 0)
    total_broadcasts = settings.get("total_broadcasts", 0)
    force_join = settings.get("force_join_channel", "")
    global_footer = settings.get("global_ad_footer", "")

    active_engine_tasks = len(active_tasks)
    file_size = 0
    if os.path.exists(DATA_FILE):
        file_size = os.path.getsize(DATA_FILE)

    plan_dist = {"free": 0, "basic": 0, "pro": 0, "elite": 0}
    for uid_str in data.get("users", {}):
        pk = get_user_plan_key(int(uid_str)) if uid_str.isdigit() else "free"
        if pk in plan_dist:
            plan_dist[pk] += 1

    active_24h = 0
    now = time.time()
    for u in data.get("users", {}).values():
        la = u.get("last_active", "")
        if la:
            try:
                la_time = datetime.strptime(la, '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - la_time).total_seconds() < 86400:
                    active_24h += 1
            except Exception:
                pass

    return {
        "total_users": total_users,
        "banned": banned,
        "premium_count": premium_count,
        "total_accounts": total_accounts,
        "running": running,
        "paused": paused,
        "completed": completed,
        "idle_camps": idle_camps,
        "total_targets": total_targets,
        "total_with_ad": total_with_ad,
        "total_configured": total_configured,
        "total_sent": total_sent,
        "total_failed": total_failed,
        "logins": logins,
        "logouts": logouts,
        "m_mode": m_mode,
        "bot_starts": bot_starts,
        "total_broadcasts": total_broadcasts,
        "active_engine_tasks": active_engine_tasks,
        "file_size": file_size,
        "file_size_str": get_readable_size(file_size),
        "uptime": get_readable_time(int(now - BOT_START_TIME)),
        "plan_dist": plan_dist,
        "active_24h": active_24h,
        "force_join": force_join,
        "global_footer": global_footer,
        "total_referrals": sum(
            len(v) for v in data.get("referrals", {}).values()
        ),
        "admin_log_count": len(data.get("admin_logs", []))
    }
# =====================================================
# ðŸ‘‘ ADMIN PANEL â€” MAIN COMMAND
# =====================================================
@bot.on_message(filters.command("panel") & filters.private)
async def admin_panel_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return await message.reply_text(
            "ðŸ’€ <b>Access Denied!</b>\nðŸš« Admin only command.",
            parse_mode=ParseMode.HTML
        )
    await send_admin_panel(message, is_edit=False)


async def send_admin_panel(msg_or_query, is_edit: bool = False):
    """Send the full admin panel."""
    s = get_system_stats()
    m_mode = "ðŸ”´ ON" if s["m_mode"] else "ðŸŸ¢ OFF"
    success_rate = 0
    total_ops = s["total_sent"] + s["total_failed"]
    if total_ops > 0:
        success_rate = round((s["total_sent"] / total_ops) * 100, 1)

    fj = f"âœ… {s['force_join']}" if s["force_join"] else "âŒ Disabled"
    gf = "âœ… Set" if s["global_footer"] else "âŒ None"

    text = (
        f"ðŸ’€ <b>Skull Ads â€” Admin Control Center</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘‘ <b>SYSTEM OVERVIEW</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ Total Users: <code>{s['total_users']}</code>\n"
        f"â”‚ ðŸŸ¢ Active (24h): <code>{s['active_24h']}</code>\n"
        f"â”‚ ðŸ’Ž Premium: <code>{s['premium_count']}</code>\n"
        f"â”‚ ðŸš« Banned: <code>{s['banned']}</code>\n"
        f"â”‚ ðŸ”‘ Sessions: <code>{s['total_accounts']}</code>\n"
        f"â”‚ ðŸ”— Referrals: <code>{s['total_referrals']}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“Š <b>PLAN DISTRIBUTION</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ†“ Free: <code>{s['plan_dist']['free']}</code> | "
        f"âš¡ Basic: <code>{s['plan_dist']['basic']}</code>\n"
        f"â”‚ ðŸ’Ž Pro: <code>{s['plan_dist']['pro']}</code> | "
        f"ðŸ‘‘ Elite: <code>{s['plan_dist']['elite']}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸš€ <b>CAMPAIGN ENGINE</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸŸ¢ Running: <code>{s['running']}</code> | "
        f"ðŸ”´ Paused: <code>{s['paused']}</code>\n"
        f"â”‚ âœ… Done: <code>{s['completed']}</code> | "
        f"âšª Idle: <code>{s['idle_camps']}</code>\n"
        f"â”‚ âš¡ Tasks: <code>{s['active_engine_tasks']}</code> | "
        f"ðŸŽ¯ Targets: <code>{s['total_targets']}</code>\n"
        f"â”‚ ðŸ“ With Ad: <code>{s['total_with_ad']}</code> | "
        f"âš™ï¸ Config: <code>{s['total_configured']}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“ˆ <b>LIFETIME STATS</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸš€ Sent: <code>{s['total_sent']:,}</code> | "
        f"âŒ Failed: <code>{s['total_failed']:,}</code>\n"
        f"â”‚ ðŸ“ˆ Success: <code>{success_rate}%</code>\n"
        f"â”‚ ðŸ“² Logins: <code>{s['logins']}</code> | "
        f"ðŸ“¤ Logouts: <code>{s['logouts']}</code>\n"
        f"â”‚ ðŸ“¢ Broadcasts: <code>{s['total_broadcasts']}</code> | "
        f"ðŸ”„ Starts: <code>{s['bot_starts']}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ–¥ï¸ <b>SERVER & CONFIG</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ›  Maintenance: {m_mode}\n"
        f"â”‚ â±ï¸ Uptime: <code>{s['uptime']}</code>\n"
        f"â”‚ ðŸ’¾ DB Size: <code>{s['file_size_str']}</code>\n"
        f"â”‚ ðŸ“¢ Force Join: {fj}\n"
        f"â”‚ ðŸ“ Footer: {gf}\n"
        f"â”‚ ðŸ“‹ Logs: <code>{s['admin_log_count']}</code> entries\n"
        f"â”‚ ðŸ¤– Version: <code>v{BOT_VERSION}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ‘¥ Users", callback_data="adm_users"),
            InlineKeyboardButton("ðŸ’Ž Premium", callback_data="adm_premium")
        ],
        [
            InlineKeyboardButton("ðŸš€ Campaigns", callback_data="adm_campaigns"),
            InlineKeyboardButton("ðŸ”‘ Sessions", callback_data="adm_sessions")
        ],
        [
            InlineKeyboardButton("ðŸ“¢ Broadcast", callback_data="adm_broadcast_menu"),
            InlineKeyboardButton("ðŸ’¾ Database", callback_data="adm_db_menu")
        ],
        [
            InlineKeyboardButton("âš™ï¸ Settings", callback_data="adm_settings"),
            InlineKeyboardButton("ðŸ“Š Analytics", callback_data="adm_analytics")
        ],
        [
            InlineKeyboardButton("ðŸ“‹ Logs", callback_data="adm_logs"),
            InlineKeyboardButton("ðŸš« Banned", callback_data="adm_banned_list")
        ],
        [
            InlineKeyboardButton("ðŸ” Search User", callback_data="adm_search"),
            InlineKeyboardButton("ðŸ”„ Refresh", callback_data="adm_refresh_panel")
        ]
    ])

    try:
        if is_edit:
            await safe_edit(msg_or_query, text, markup)
        else:
            await msg_or_query.reply_text(
                text, reply_markup=markup, parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.warning(f"Admin panel send error: {e}")


# =====================================================
# ðŸ‘‘ ADMIN PANEL â€” CALLBACK HANDLERS
# =====================================================

# â”€â”€ Refresh Panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_refresh_panel$"))
async def adm_refresh_panel_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    if is_rate_limited(query.from_user.id, "adm_refresh", 2):
        return await query.answer("â³ Wait...", show_alert=False)
    await send_admin_panel(query.message, is_edit=True)
    await query.answer("âœ… Refreshed!", show_alert=False)


# â”€â”€ Back to Admin Panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_back_panel$"))
async def adm_back_panel_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    # Clear any admin state
    if query.from_user.id in user_state:
        del user_state[query.from_user.id]
    await send_admin_panel(query.message, is_edit=True)


# â”€â”€ Users Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_users$"))
async def adm_users_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    users = list(data.get("users", {}).values())
    total = len(users)
    banned_count = len(data.get("banned_users", []))
    premium_count = len(data.get("premium_users", {}))

    sorted_users = sorted(
        users, key=lambda x: x.get("joined_date", ""), reverse=True
    )

    text = (
        f"ðŸ’€ <b>Admin â€” User Management</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ <b>Total:</b> <code>{total}</code>\n"
        f"â”‚ ðŸ’Ž <b>Premium:</b> <code>{premium_count}</code>\n"
        f"â”‚ ðŸš« <b>Banned:</b> <code>{banned_count}</code>\n"
        f"â”‚ ðŸ†“ <b>Free:</b> <code>{total - premium_count}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ <b>ðŸ“‹ Recent Users:</b>\n"
    )

    for u in sorted_users[:8]:
        uid = u.get("user_id", "?")
        name = truncate_text(sanitize_html(u.get("name", "N/A")), 12)
        is_banned = uid in data.get("banned_users", [])
        is_premium = str(uid) in data.get("premium_users", {})
        tag = ""
        if is_banned:
            tag = " ðŸš«"
        elif is_premium:
            tag = " ðŸ’Ž"
        joined = u.get("joined_date", "N/A")[:10]
        text += f"â”‚ <code>{uid}</code>{tag} â€¢ {name} â€¢ {joined}\n"

    if total > 8:
        text += f"â”‚ ... +{total - 8} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ“‹ List All", callback_data="adm_list_users_0"),
            InlineKeyboardButton("ðŸ” Search", callback_data="adm_search")
        ],
        [
            InlineKeyboardButton("ðŸ’Ž Premium Users", callback_data="adm_premium"),
            InlineKeyboardButton("ðŸš« Banned Users", callback_data="adm_banned_list")
        ],
        [
            InlineKeyboardButton("ðŸ“Š User Stats", callback_data="adm_user_stats"),
            InlineKeyboardButton("ðŸ“¤ Export Users", callback_data="adm_export_users")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


# â”€â”€ List Users Paginated â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex(r"^adm_list_users_(\d+)$"))
async def adm_list_users_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    page = int(query.matches[0].group(1))
    data = get_data()
    users = list(data.get("users", {}).values())
    users.sort(key=lambda x: x.get("joined_date", ""), reverse=True)

    per_page = 15
    total_pages = max(1, math.ceil(len(users) / per_page))
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page

    text = f"ðŸ’€ <b>All Users â€” Page {page + 1}/{total_pages}</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"

    for u in users[start:end]:
        uid = u.get("user_id", "?")
        name = truncate_text(sanitize_html(u.get("name", "N/A")), 10)
        is_banned = uid in data.get("banned_users", [])
        is_premium = str(uid) in data.get("premium_users", {})
        tag = " ðŸš«" if is_banned else (" ðŸ’Ž" if is_premium else "")
        text += f"â”‚ <code>{uid}</code>{tag} â€¢ {name}\n"

    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("â—€ï¸", callback_data=f"adm_list_users_{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("â–¶ï¸", callback_data=f"adm_list_users_{page + 1}"))

    markup = InlineKeyboardMarkup([
        nav,
        [InlineKeyboardButton("ðŸ”™ Back", callback_data="adm_users")]
    ])

    await safe_edit(query.message, text, markup)


# â”€â”€ User Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_user_stats$"))
async def adm_user_stats_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    stats = data.get("stats", {})

    top_senders = sorted(
        stats.items(),
        key=lambda x: x[1].get("total_sent", 0),
        reverse=True
    )[:10]

    text = "ðŸ’€ <b>Top Senders</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for i, (uid_str, st) in enumerate(top_senders, 1):
        user = data["users"].get(uid_str, {})
        name = truncate_text(sanitize_html(user.get("name", "Unknown")), 12)
        sent = st.get("total_sent", 0)
        text += f"â”‚ {i}. <code>{uid_str}</code> â€¢ {name} â€¢ <code>{sent:,}</code> sent\n"

    if not top_senders:
        text += "â”‚ No data yet.\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    await safe_edit(
        query.message, text,
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="adm_users")]
        ])
    )


# â”€â”€ Export Users â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_export_users$"))
async def adm_export_users_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    lines = ["USER_ID,NAME,USERNAME,JOINED,PLAN,BANNED"]
    for uid_str, u in data.get("users", {}).items():
        uid = u.get("user_id", uid_str)
        name = u.get("name", "N/A").replace(",", " ")
        uname = u.get("username", "")
        joined = u.get("joined_date", "N/A")
        plan = get_user_plan_key(int(uid_str)) if uid_str.isdigit() else "free"
        banned = "YES" if int(uid_str) in data.get("banned_users", []) else "NO"
        lines.append(f"{uid},{name},{uname},{joined},{plan},{banned}")

    export_file = f"users_export_{int(time.time())}.csv"
    try:
        with open(export_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        await query.message.reply_document(
            document=export_file,
            caption=f"ðŸ’€ <b>User Export</b>\n{len(lines) - 1} users",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        await query.answer(f"Error: {str(e)[:100]}", show_alert=True)
    finally:
        if os.path.exists(export_file):
            try:
                os.remove(export_file)
            except Exception:
                pass


# â”€â”€ Premium Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_premium$"))
async def adm_premium_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    premium = data.get("premium_users", {})

    text = f"ðŸ’€ <b>Admin â€” Premium Users ({len(premium)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"

    if not premium:
        text += "â”‚ No premium users yet.\n"
    else:
        for uid_str, info in list(premium.items())[:15]:
            plan_key = info.get("plan", "?")
            plan_name = PLANS.get(plan_key, {}).get("name", "?")
            added = info.get("added_date", "N/A")[:10]
            user = data["users"].get(uid_str, {})
            name = truncate_text(sanitize_html(user.get("name", "N/A")), 12)
            text += f"â”‚ <code>{uid_str}</code> â€¢ {name} â€¢ {plan_name} â€¢ {added}\n"
        if len(premium) > 15:
            text += f"â”‚ ... +{len(premium) - 15} more\n"

    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("âž• Add Premium", callback_data="adm_add_premium_btn"),
            InlineKeyboardButton("âž– Remove", callback_data="adm_remove_premium_btn")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_add_premium_btn$"))
async def adm_add_premium_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_add_premium", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Add Premium</b>\n\n"
        "Send: <code>[user_id] [plan]</code>\n\n"
        "Plans: <code>basic</code> | <code>pro</code> | <code>elite</code>\n\n"
        "Example: <code>123456789 pro</code>",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_premium")]
        ])
    )


@bot.on_callback_query(filters.regex("^adm_remove_premium_btn$"))
async def adm_remove_premium_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_remove_premium", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Remove Premium</b>\n\n"
        "Send the user ID to remove premium from:\n\n"
        "Example: <code>123456789</code>",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_premium")]
        ])
    )


# â”€â”€ Campaigns Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_campaigns$"))
async def adm_campaigns_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    campaigns = data.get("campaigns", {})

    running_list = []
    paused_list = []
    for uid_str, camp in campaigns.items():
        status = camp.get("status", "IDLE")
        user = data["users"].get(uid_str, {})
        name = truncate_text(sanitize_html(user.get("name", "N/A")), 10)
        targets = len(camp.get("targets", []))
        c_round = camp.get("current_round", 0)
        t_round = camp.get("total_rounds", 0)

        entry = f"<code>{uid_str}</code> â€¢ {name} â€¢ ðŸŽ¯{targets} â€¢ R{c_round}/{t_round}"

        if status == "RUNNING":
            running_list.append(entry)
        elif status == "PAUSED":
            paused_list.append(entry)

    text = "ðŸ’€ <b>Admin â€” Campaign Manager</b>\n\n"

    text += f"<b>ðŸŸ¢ Running ({len(running_list)}):</b>\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for r in running_list[:8]:
        text += f"â”‚ {r}\n"
    if not running_list:
        text += "â”‚ None\n"
    if len(running_list) > 8:
        text += f"â”‚ ... +{len(running_list) - 8} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"

    text += f"<b>ðŸ”´ Paused ({len(paused_list)}):</b>\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for p in paused_list[:5]:
        text += f"â”‚ {p}\n"
    if not paused_list:
        text += "â”‚ None\n"
    if len(paused_list) > 5:
        text += f"â”‚ ... +{len(paused_list) - 5} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("â¸ï¸ Pause All", callback_data="adm_pauseall_btn"),
            InlineKeyboardButton("â–¶ï¸ Resume All", callback_data="adm_resumeall_btn")
        ],
        [
            InlineKeyboardButton("ðŸ—‘ï¸ Clear Done", callback_data="adm_clear_completed"),
            InlineKeyboardButton("ðŸ”„ Reset All", callback_data="adm_reset_all_camps")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_pauseall_btn$"))
async def adm_pauseall_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    count = 0
    for uid in data["campaigns"]:
        if data["campaigns"][uid].get("status") == "RUNNING":
            data["campaigns"][uid]["status"] = "PAUSED"
            count += 1
    await async_update_data(data)
    add_admin_log("PAUSE_ALL", query.from_user.id, f"{count} campaigns paused")
    await query.answer(f"â¸ï¸ {count} campaigns paused!", show_alert=True)
    await adm_campaigns_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_resumeall_btn$"))
async def adm_resumeall_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    count = 0
    for uid in data["campaigns"]:
        camp = data["campaigns"][uid]
        if (camp.get("status") == "PAUSED" and
                camp.get("targets") and camp.get("ad_html") and
                camp.get("group_delay")):
            data["campaigns"][uid]["status"] = "RUNNING"
            count += 1
    await async_update_data(data)
    add_admin_log("RESUME_ALL", query.from_user.id, f"{count} campaigns resumed")
    await query.answer(f"â–¶ï¸ {count} campaigns resumed!", show_alert=True)
    await adm_campaigns_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_clear_completed$"))
async def adm_clear_completed_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    count = 0
    for uid in list(data["campaigns"].keys()):
        if data["campaigns"][uid].get("status") == "COMPLETED":
            data["campaigns"][uid]["status"] = "IDLE"
            data["campaigns"][uid]["current_round"] = 1
            count += 1
    await async_update_data(data)
    await query.answer(f"ðŸ—‘ï¸ {count} completed campaigns cleared!", show_alert=True)
    await adm_campaigns_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_reset_all_camps$"))
async def adm_reset_all_camps_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    count = 0
    for uid in data["campaigns"]:
        data["campaigns"][uid]["status"] = "IDLE"
        data["campaigns"][uid]["current_round"] = 1
        count += 1
    await async_update_data(data)
    add_admin_log("RESET_ALL_CAMPAIGNS", query.from_user.id, f"{count} reset")
    await query.answer(f"ðŸ”„ {count} campaigns reset!", show_alert=True)
    await adm_campaigns_cb(client, query)


# â”€â”€ Sessions Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_sessions$"))
async def adm_sessions_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    accounts = data.get("accounts", {})

    text = f"ðŸ’€ <b>Admin â€” Session Manager ({len(accounts)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"

    if not accounts:
        text += "â”‚ No active sessions.\n"
    else:
        for acc_key, acc in list(accounts.items())[:12]:
            uid = acc.get("user_id", "?")
            phone = acc.get("phone", "?")
            added = acc.get("added_date", "N/A")[:10]
            user = data["users"].get(str(uid), {})
            name = truncate_text(sanitize_html(user.get("name", "?")), 8)
            text += f"â”‚ {phone} â€¢ {name} (<code>{uid}</code>) â€¢ {added}\n"
        if len(accounts) > 12:
            text += f"â”‚ ... +{len(accounts) - 12} more\n"

    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ”„ Validate All", callback_data="adm_validate_sessions"),
            InlineKeyboardButton("ðŸ—‘ï¸ Clear Invalid", callback_data="adm_clear_invalid")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_validate_sessions$"))
async def adm_validate_sessions_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    await query.answer("â³ Validating sessions... This may take a while.", show_alert=True)

    data = get_data()
    accounts = data.get("accounts", {})
    valid = 0
    invalid = 0
    invalid_keys = []

    for acc_key, acc in list(accounts.items()):
        tc = None
        try:
            tc = Client(
                f"validate_{acc_key[:10]}_{int(time.time())}",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=acc.get("session", ""),
                in_memory=True
            )
            await tc.connect()
            await tc.get_me()
            valid += 1
        except AuthKeyUnregistered:
            invalid += 1
            invalid_keys.append(acc_key)
        except Exception as e:
            logger.warning(f"Session validation error for {acc_key}: {e}")
            invalid += 1
            invalid_keys.append(acc_key)
        finally:
            if tc:
                try:
                    await tc.disconnect()
                except Exception:
                    pass

    # Store invalid keys for clearing
    data = await async_get_data()
    data["settings"]["_invalid_sessions"] = invalid_keys
    await async_update_data(data)

    await safe_send(
        query.from_user.id,
        f"ðŸ’€ <b>Session Validation Complete!</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ âœ… Valid: <code>{valid}</code>\n"
        f"â”‚ âŒ Invalid: <code>{invalid}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )


@bot.on_callback_query(filters.regex("^adm_clear_invalid$"))
async def adm_clear_invalid_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = await async_get_data()
    invalid_keys = data.get("settings", {}).get("_invalid_sessions", [])

    if not invalid_keys:
        return await query.answer("â„¹ï¸ Run 'Validate All' first!", show_alert=True)

    count = 0
    for key in invalid_keys:
        if key in data["accounts"]:
            uid = data["accounts"][key].get("user_id")
            del data["accounts"][key]
            if uid:
                active = data.get("active_account", {}).get(str(uid))
                if active == key:
                    remaining = {
                        k: v for k, v in data["accounts"].items()
                        if v.get("user_id") == uid
                    }
                    if remaining:
                        data["active_account"][str(uid)] = list(remaining.keys())[0]
                    else:
                        data.get("active_account", {}).pop(str(uid), None)
                        # Pause campaign if no accounts left
                        if data.get("campaigns", {}).get(str(uid), {}).get("status") == "RUNNING":
                            data["campaigns"][str(uid)]["status"] = "PAUSED"
            count += 1

    data["settings"].pop("_invalid_sessions", None)
    await async_update_data(data)
    add_admin_log("CLEAR_INVALID_SESSIONS", query.from_user.id, f"{count} removed")
    await query.answer(f"ðŸ—‘ï¸ {count} invalid sessions removed!", show_alert=True)
    await adm_sessions_cb(client, query)


# â”€â”€ Broadcast Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_broadcast_menu$"))
async def adm_broadcast_menu_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    total_users = len(data["users"])
    premium_count = len(data.get("premium_users", {}))
    total_bc = data["settings"].get("total_broadcasts", 0)

    text = (
        f"ðŸ’€ <b>Admin â€” Broadcast Center</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ Total Users: <code>{total_users}</code>\n"
        f"â”‚ ðŸ’Ž Premium Users: <code>{premium_count}</code>\n"
        f"â”‚ ðŸ“¢ Total Broadcasts: <code>{total_bc}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        f"<b>Methods:</b>\n"
        f"â€¢ <b>Reply Broadcast:</b> Reply to a msg with /broadcast\n"
        f"â€¢ <b>Text Broadcast:</b> Type message below\n"
        f"â€¢ <b>Premium Only:</b> Send to premium users only"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ“ Type Message", callback_data="adm_broadcast_text_btn")],
        [InlineKeyboardButton("ðŸ’Ž Premium Only", callback_data="adm_broadcast_premium_btn")],
        [
            InlineKeyboardButton("ðŸ“Š Stats", callback_data="adm_broadcast_stats"),
            InlineKeyboardButton("ðŸ”™ Back", callback_data="adm_back_panel")
        ]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_broadcast_text_btn$"))
async def adm_broadcast_text_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_broadcast_text", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Type Broadcast Message</b>\n\n"
        "Send the message you want to broadcast to all users.\n"
        "HTML formatting is supported.\n\n"
        "âš ï¸ Type /cancel to abort.",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_broadcast_menu")]
        ])
    )


@bot.on_callback_query(filters.regex("^adm_broadcast_premium_btn$"))
async def adm_broadcast_premium_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_broadcast_premium_text", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Premium Broadcast</b>\n\n"
        "Send the message to broadcast to <b>premium users only</b>.\n\n"
        "âš ï¸ Type /cancel to abort.",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_broadcast_menu")]
        ])
    )


@bot.on_callback_query(filters.regex("^adm_broadcast_stats$"))
async def adm_broadcast_stats_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = get_data()
    total_bc = data["settings"].get("total_broadcasts", 0)
    await query.answer(f"ðŸ“Š Total broadcasts: {total_bc}", show_alert=True)


# â”€â”€ Database Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_db_menu$"))
async def adm_db_menu_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    s = get_system_stats()
    backup_exists = os.path.exists(DATA_FILE + ".backup")
    last_backup = "Available" if backup_exists else "None"

    text = (
        f"ðŸ’€ <b>Admin â€” Database Manager</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ’¾ <b>Size:</b> <code>{s['file_size_str']}</code>\n"
        f"â”‚ ðŸ“ <b>File:</b> <code>{DATA_FILE}</code>\n"
        f"â”‚ ðŸ”„ <b>Auto Backup:</b> {last_backup}\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ Users: <code>{s['total_users']}</code>\n"
        f"â”‚ ðŸ”‘ Accounts: <code>{s['total_accounts']}</code>\n"
        f"â”‚ ðŸš€ Campaigns: <code>{s['running'] + s['paused'] + s['completed']}</code>\n"
        f"â”‚ ðŸ“‹ Logs: <code>{s['admin_log_count']}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ“¥ Download DB", callback_data="adm_download_db"),
            InlineKeyboardButton("ðŸ“¤ Upload DB", callback_data="adm_upload_db_info")
        ],
        [
            InlineKeyboardButton("ðŸ’¾ Create Backup", callback_data="adm_create_backup"),
            InlineKeyboardButton("ðŸ”„ Restore Backup", callback_data="adm_restore_backup")
        ],
        [
            InlineKeyboardButton("ðŸ—‘ï¸ Reset DB", callback_data="adm_reset_db_confirm"),
            InlineKeyboardButton("ðŸ§¹ Clean Logs", callback_data="adm_clean_logs")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_download_db$"))
async def adm_download_db_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    backup_file = f"skull_backup_{int(time.time())}.json"
    try:
        data = get_data()
        backup = {
            "backup_info": {
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "version": f"SkullAdsBot_v{BOT_VERSION}",
                "total_users": len(data.get("users", {})),
                "total_accounts": len(data.get("accounts", {}))
            },
            "data": data
        }
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)
        file_size = get_readable_size(os.path.getsize(backup_file))
        await query.message.reply_document(
            document=backup_file,
            caption=(
                f"ðŸ’€ <b>Database Backup</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ ðŸ“… {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"â”‚ ðŸ‘¥ Users: <code>{len(data.get('users', {}))}</code>\n"
                f"â”‚ ðŸ”‘ Accounts: <code>{len(data.get('accounts', {}))}</code>\n"
                f"â”‚ ðŸ’¾ Size: <code>{file_size}</code>\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            ),
            parse_mode=ParseMode.HTML
        )
        add_admin_log("DOWNLOAD_DB", query.from_user.id)
    except Exception as e:
        logger.error(f"DB download error: {e}")
        await query.answer(f"Error: {str(e)[:100]}", show_alert=True)
    finally:
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except Exception:
                pass


@bot.on_callback_query(filters.regex("^adm_upload_db_info$"))
async def adm_upload_db_info_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Upload Database</b>\n\n"
        "Reply to a JSON backup file with <code>/uploaddb</code>\n\n"
        "âš ï¸ This will overwrite current data!\n"
        "A backup will be created automatically.",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ”™ Back", callback_data="adm_db_menu")]
        ])
    )


@bot.on_callback_query(filters.regex("^adm_create_backup$"))
async def adm_create_backup_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    try:
        data = get_data()
        backup_name = f"manual_backup_{int(time.time())}.json"
        with open(backup_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        data = await async_get_data()
        data["settings"]["last_backup"] = time.strftime('%Y-%m-%d %H:%M:%S')
        await async_update_data(data)
        add_admin_log("CREATE_BACKUP", query.from_user.id, backup_name)
        await query.answer(f"âœ… Backup created: {backup_name}", show_alert=True)
    except Exception as e:
        logger.error(f"Backup creation error: {e}")
        await query.answer(f"Error: {str(e)[:100]}", show_alert=True)


@bot.on_callback_query(filters.regex("^adm_restore_backup$"))
async def adm_restore_backup_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    backup_file = DATA_FILE + ".backup"
    if not os.path.exists(backup_file):
        return await query.answer("âŒ No auto-backup found!", show_alert=True)
    try:
        with open(backup_file, "r", encoding="utf-8") as f:
            backup_data = json.load(f)
        current = get_data()
        emergency = f"pre_restore_{int(time.time())}.json"
        with open(emergency, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        await async_update_data(backup_data)
        add_admin_log("RESTORE_BACKUP", query.from_user.id, f"Emergency: {emergency}")
        await query.answer("âœ… Backup restored!", show_alert=True)
        await adm_db_menu_cb(client, query)
    except Exception as e:
        logger.error(f"Restore error: {e}")
        await query.answer(f"Error: {str(e)[:100]}", show_alert=True)


@bot.on_callback_query(filters.regex("^adm_reset_db_confirm$"))
async def adm_reset_db_confirm_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    await safe_edit(
        query.message,
        "ðŸ’€ <b>âš ï¸ DANGER: Database Reset</b>\n\n"
        "â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        "â”‚ This will DELETE ALL DATA:\n"
        "â”‚ â€¢ All users\n"
        "â”‚ â€¢ All accounts/sessions\n"
        "â”‚ â€¢ All campaigns\n"
        "â”‚ â€¢ All stats\n"
        "â”‚ â€¢ All premium entries\n"
        "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
        "Type <code>CONFIRM RESET</code> to proceed.\n"
        "Type anything else to cancel.",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ CANCEL", callback_data="adm_db_menu")]
        ])
    )
    user_state[query.from_user.id] = {"step": "adm_confirm_reset", "_created": time.time()}


@bot.on_callback_query(filters.regex("^adm_clean_logs$"))
async def adm_clean_logs_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    old_count = len(data.get("admin_logs", []))
    data["admin_logs"] = data.get("admin_logs", [])[:50]
    await async_update_data(data)
    cleaned = old_count - len(data["admin_logs"])
    await query.answer(f"ðŸ§¹ Cleaned {cleaned} old log entries!", show_alert=True)


# â”€â”€ Settings Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_settings$"))
async def adm_settings_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    settings = data.get("settings", {})
    m_mode = settings.get("maintenance_mode", False)
    force_join = settings.get("force_join_channel", "") or "Disabled"
    global_footer = settings.get("global_ad_footer", "")
    footer_preview = truncate_text(global_footer, 30) if global_footer else "None"
    rate_limit = settings.get("rate_limit_seconds", 5)

    m_btn_text = "ðŸ”´ Disable Maintenance" if m_mode else "ðŸŸ¢ Enable Maintenance"
    m_btn_data = "adm_maintenance_off" if m_mode else "adm_maintenance_on"

    text = (
        f"ðŸ’€ <b>Admin â€” Bot Settings</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ›  <b>Maintenance:</b> {'ðŸ”´ ON' if m_mode else 'ðŸŸ¢ OFF'}\n"
        f"â”‚ ðŸ“¢ <b>Force Join:</b> <code>{force_join}</code>\n"
        f"â”‚ ðŸ“ <b>Global Footer:</b> {footer_preview}\n"
        f"â”‚ â³ <b>Rate Limit:</b> <code>{rate_limit}s</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(m_btn_text, callback_data=m_btn_data)],
        [
            InlineKeyboardButton("ðŸ“¢ Set Force Join", callback_data="adm_set_forcejoin_btn"),
            InlineKeyboardButton("ðŸ“ Set Footer", callback_data="adm_set_footer_btn")
        ],
        [
            InlineKeyboardButton("ðŸ”„ Clear Footer", callback_data="adm_clear_footer"),
            InlineKeyboardButton("ðŸ”„ Clear Force Join", callback_data="adm_clear_forcejoin")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_maintenance_on$"))
async def adm_maintenance_on_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    data["settings"]["maintenance_mode"] = True
    await async_update_data(data)
    add_admin_log("MAINTENANCE_ON", query.from_user.id)
    await query.answer("ðŸ”´ Maintenance mode ENABLED!", show_alert=True)
    await adm_settings_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_maintenance_off$"))
async def adm_maintenance_off_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    data["settings"]["maintenance_mode"] = False
    await async_update_data(data)
    add_admin_log("MAINTENANCE_OFF", query.from_user.id)
    await query.answer("ðŸŸ¢ Maintenance mode DISABLED!", show_alert=True)
    await adm_settings_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_set_forcejoin_btn$"))
async def adm_set_forcejoin_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_set_forcejoin", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Set Force Join Channel</b>\n\n"
        "Send channel username (e.g. <code>@mychannel</code>)\n"
        "Or send <code>off</code> to disable.\n\n"
        "âš ï¸ Bot must be admin in the channel!",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_settings")]
        ])
    )


@bot.on_callback_query(filters.regex("^adm_set_footer_btn$"))
async def adm_set_footer_btn_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_set_footer", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Set Global Ad Footer</b>\n\n"
        "This text will be appended to all ad messages.\n"
        "Send the footer text, or <code>off</code> to disable.\n\n"
        "Example:\n<code>ðŸ“¢ Powered by @SkullAdsBot</code>",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_settings")]
        ])
    )


@bot.on_callback_query(filters.regex("^adm_clear_footer$"))
async def adm_clear_footer_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    data["settings"]["global_ad_footer"] = ""
    await async_update_data(data)
    add_admin_log("CLEAR_FOOTER", query.from_user.id)
    await query.answer("âœ… Global footer cleared!", show_alert=True)
    await adm_settings_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_clear_forcejoin$"))
async def adm_clear_forcejoin_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    data["settings"]["force_join_channel"] = ""
    await async_update_data(data)
    add_admin_log("CLEAR_FORCEJOIN", query.from_user.id)
    await query.answer("âœ… Force join disabled!", show_alert=True)
    await adm_settings_cb(client, query)


# â”€â”€ Analytics Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_analytics$"))
async def adm_analytics_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    s = get_system_stats()
    data = get_data()

    total_ops = s["total_sent"] + s["total_failed"]
    success_rate = round((s["total_sent"] / total_ops * 100), 1) if total_ops > 0 else 0

    users_with_stats = len(data.get("stats", {}))
    avg_sent = round(s["total_sent"] / max(users_with_stats, 1))

    total_users = s["total_users"]
    active = s["active_24h"]
    active_pct = round((active / max(total_users, 1)) * 100, 1)

    login_logout_ratio = round(s["logins"] / max(s["logouts"], 1), 2)

    text = (
        f"ðŸ’€ <b>Admin â€” Analytics Dashboard</b>\n\n"
        f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“Š <b>PERFORMANCE METRICS</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸš€ Total Sent: <code>{s['total_sent']:,}</code>\n"
        f"â”‚ âŒ Total Failed: <code>{s['total_failed']:,}</code>\n"
        f"â”‚ ðŸ“ˆ Success Rate: <code>{success_rate}%</code>\n"
        f"â”‚ ðŸ“¨ Avg per User: <code>{avg_sent}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ <b>USER METRICS</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ‘¥ Total: <code>{total_users}</code>\n"
        f"â”‚ ðŸŸ¢ Active (24h): <code>{active}</code> ({active_pct}%)\n"
        f"â”‚ ðŸ’Ž Premium: <code>{s['premium_count']}</code>\n"
        f"â”‚ ðŸ“Š Conversion: <code>"
        f"{round(s['premium_count'] / max(total_users, 1) * 100, 1)}%</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ”‘ <b>SESSION HEALTH</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸ“² Login/Logout Ratio: <code>{login_logout_ratio}</code>\n"
        f"â”‚ ðŸ”‘ Active Sessions: <code>{s['total_accounts']}</code>\n"
        f"â”‚ âš¡ Engine Tasks: <code>{s['active_engine_tasks']}</code>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸŽ¯ <b>CAMPAIGN HEALTH</b>\n"
        f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
        f"â”‚ ðŸŸ¢ Running: <code>{s['running']}</code>\n"
        f"â”‚ ðŸŽ¯ Total Targets: <code>{s['total_targets']}</code>\n"
        f"â”‚ ðŸ“ Configured: <code>{s['total_configured']}</code>\n"
        f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    )

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ”„ Refresh", callback_data="adm_analytics")],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


# â”€â”€ Banned Users Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_banned_list$"))
async def adm_banned_list_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    banned = data.get("banned_users", [])

    text = f"ðŸ’€ <b>Banned Users ({len(banned)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"

    if not banned:
        text += "â”‚ No banned users.\n"
    else:
        for b_id in banned[:20]:
            user = data["users"].get(str(b_id), {})
            name = truncate_text(sanitize_html(user.get("name", "Unknown")), 12)
            text += f"â”‚ ðŸš« <code>{b_id}</code> â€¢ {name}\n"
        if len(banned) > 20:
            text += f"â”‚ ... +{len(banned) - 20} more\n"

    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ðŸ”“ Unban All", callback_data="adm_unban_all")],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_unban_all$"))
async def adm_unban_all_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    count = len(data.get("banned_users", []))
    data["banned_users"] = []
    await async_update_data(data)
    add_admin_log("UNBAN_ALL", query.from_user.id, f"{count} users unbanned")
    await query.answer(f"âœ… {count} users unbanned!", show_alert=True)
    await adm_banned_list_cb(client, query)


# â”€â”€ Admin Logs Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_logs$"))
async def adm_logs_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)

    data = get_data()
    logs = data.get("admin_logs", [])

    text = f"ðŸ’€ <b>Admin Action Logs ({len(logs)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"

    if not logs:
        text += "â”‚ No logs yet.\n"
    else:
        for log in logs[:15]:
            action = log.get("action", "?")
            ts = log.get("timestamp", "?")[:16]
            details = truncate_text(log.get("details", ""), 25)
            detail_str = f" â€¢ {details}" if details else ""
            text += f"â”‚ [{ts}] {action}{detail_str}\n"
        if len(logs) > 15:
            text += f"â”‚ ... +{len(logs) - 15} more\n"

    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ðŸ—‘ï¸ Clear Logs", callback_data="adm_clear_all_logs"),
            InlineKeyboardButton("ðŸ“¥ Export", callback_data="adm_export_logs")
        ],
        [InlineKeyboardButton("ðŸ”™ Admin Panel", callback_data="adm_back_panel")]
    ])

    await safe_edit(query.message, text, markup)


@bot.on_callback_query(filters.regex("^adm_clear_all_logs$"))
async def adm_clear_all_logs_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = await async_get_data()
    count = len(data.get("admin_logs", []))
    data["admin_logs"] = []
    await async_update_data(data)
    await query.answer(f"ðŸ—‘ï¸ {count} logs cleared!", show_alert=True)
    await adm_logs_cb(client, query)


@bot.on_callback_query(filters.regex("^adm_export_logs$"))
async def adm_export_logs_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    data = get_data()
    logs = data.get("admin_logs", [])
    if not logs:
        return await query.answer("No logs to export!", show_alert=True)
    log_file = f"admin_logs_{int(time.time())}.json"
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
        await query.message.reply_document(
            document=log_file,
            caption=f"ðŸ’€ Admin Logs â€” {len(logs)} entries",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Log export error: {e}")
        await query.answer(f"Error: {str(e)[:50]}", show_alert=True)
    finally:
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except Exception:
                pass


# â”€â”€ Search User â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
@bot.on_callback_query(filters.regex("^adm_search$"))
async def adm_search_cb(client, query: CallbackQuery):
    if not is_admin(query.from_user.id):
        return await query.answer("âŒ Admin only!", show_alert=True)
    user_state[query.from_user.id] = {"step": "adm_search_user", "_created": time.time()}
    await safe_edit(
        query.message,
        "ðŸ’€ <b>Search Users</b>\n\n"
        "Send a user ID, name, or username to search.\n\n"
        "Example:\n"
        "â€¢ <code>123456789</code>\n"
        "â€¢ <code>John</code>\n"
        "â€¢ <code>username</code>",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("âŒ Cancel", callback_data="adm_back_panel")]
        ])
    )


# =====================================================
# ðŸ‘‘ ADMIN COMMANDS â€” TEXT BASED
# =====================================================
@bot.on_message(filters.command("ban") & filters.private)
async def ban_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply_text(
            "ðŸ’€ <b>Usage:</b> <code>/ban [user_id]</code>",
            parse_mode=ParseMode.HTML
        )
    try:
        ban_id = int(message.command[1])
        if ban_id in ADMIN_IDS:
            return await message.reply_text(
                "âŒ Cannot ban an admin!", parse_mode=ParseMode.HTML
            )
        data = await async_get_data()
        if ban_id not in data["banned_users"]:
            data["banned_users"].append(ban_id)
        if str(ban_id) in data["campaigns"]:
            data["campaigns"][str(ban_id)]["status"] = "PAUSED"
        data["settings"]["total_bans"] = data["settings"].get("total_bans", 0) + 1
        await async_update_data(data)
        add_admin_log("BAN_USER", message.from_user.id, f"Banned {ban_id}")

        user = data["users"].get(str(ban_id), {})
        await message.reply_text(
            f"ðŸ’€ <b>User Banned!</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ ðŸ‘¤ Name: {sanitize_html(user.get('name', 'Unknown'))}\n"
            f"â”‚ ðŸ†” ID: <code>{ban_id}</code>\n"
            f"â”‚ ðŸš« Campaign: Paused\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€",
            parse_mode=ParseMode.HTML
        )
        await safe_send(ban_id, "ðŸ’€ <b>You have been banned from Skull Ads Bot.</b>\nContact @securedsitedns for support.")
    except ValueError:
        await message.reply_text("âŒ Invalid ID.", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("unban") & filters.private)
async def unban_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply_text(
            "ðŸ’€ <b>Usage:</b> <code>/unban [user_id]</code>", parse_mode=ParseMode.HTML
        )
    try:
        unban_id = int(message.command[1])
        data = await async_get_data()
        was_banned = unban_id in data["banned_users"]
        if was_banned:
            data["banned_users"].remove(unban_id)
        data["settings"]["total_unbans"] = data["settings"].get("total_unbans", 0) + 1
        await async_update_data(data)
        add_admin_log("UNBAN_USER", message.from_user.id, f"Unbanned {unban_id}")
        await message.reply_text(
            f"ðŸ’€ <b>User {'Unbanned' if was_banned else 'Was Not Banned'}!</b>\n"
            f"ðŸ†” ID: <code>{unban_id}</code>", parse_mode=ParseMode.HTML
        )
        if was_banned:
            await safe_send(unban_id, "ðŸ’€ <b>You have been unbanned!</b>\nWelcome back. ðŸŽ‰")
    except ValueError:
        await message.reply_text("âŒ Invalid ID.", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("maintenance") & filters.private)
async def maintenance_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply_text(
            "ðŸ’€ <b>Usage:</b> <code>/maintenance on</code> or <code>off</code>", parse_mode=ParseMode.HTML
        )
    st = message.command[1].lower() in ['on', 'true', '1', 'yes']
    data = await async_get_data()
    data["settings"]["maintenance_mode"] = st
    await async_update_data(data)
    add_admin_log(f"MAINTENANCE_{'ON' if st else 'OFF'}", message.from_user.id)
    await message.reply_text(
        f"ðŸ’€ <b>Maintenance: {'ðŸ”´ ON' if st else 'ðŸŸ¢ OFF'}</b>", parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("pauseall") & filters.private)
async def pauseall_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = await async_get_data()
    count = 0
    for uid in data["campaigns"]:
        if data["campaigns"][uid].get("status") == "RUNNING":
            data["campaigns"][uid]["status"] = "PAUSED"
            count += 1
    await async_update_data(data)
    add_admin_log("PAUSE_ALL", message.from_user.id, f"{count} paused")
    await message.reply_text(
        f"ðŸ’€ <b>Emergency Stop!</b>\nâ”‚ ðŸ›‘ {count} campaigns paused.", parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("resumeall") & filters.private)
async def resumeall_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = await async_get_data()
    count = 0
    for uid in data["campaigns"]:
        camp = data["campaigns"][uid]
        if (camp.get("status") == "PAUSED" and camp.get("targets") and
                camp.get("ad_html") and camp.get("group_delay")):
            data["campaigns"][uid]["status"] = "RUNNING"
            count += 1
    await async_update_data(data)
    add_admin_log("RESUME_ALL", message.from_user.id, f"{count} resumed")
    await message.reply_text(
        f"ðŸ’€ <b>Master Resume!</b>\nâ”‚ ðŸš€ {count} campaigns resumed.", parse_mode=ParseMode.HTML
    )


@bot.on_message(filters.command("addpremium") & filters.private)
async def addpremium_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 3:
        return await message.reply_text(
            "ðŸ’€ <b>Usage:</b> <code>/addpremium [user_id] [plan]</code>\n"
            "<b>Plans:</b> basic | pro | elite", parse_mode=ParseMode.HTML
        )
    try:
        target_id = int(message.command[1])
        plan_key = message.command[2].lower()
        if plan_key not in PLANS or plan_key == "free":
            return await message.reply_text("âŒ Invalid plan. Use: basic | pro | elite", parse_mode=ParseMode.HTML)
        data = await async_get_data()
        data["premium_users"][str(target_id)] = {
            "plan": plan_key, "added_by": message.from_user.id,
            "added_date": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        await async_update_data(data)
        plan_info = PLANS[plan_key]
        add_admin_log("ADD_PREMIUM", message.from_user.id, f"{target_id} â†’ {plan_key}")
        await message.reply_text(
            f"ðŸ’€ <b>Premium Granted!</b>\nâ”‚ ðŸ†” {target_id} â†’ {plan_info['name']}\nâ”‚ ðŸ‘¥ Slots: {plan_info['accounts']}",
            parse_mode=ParseMode.HTML
        )
        await safe_send(target_id,
            f"ðŸ’€ <b>Premium Activated!</b>\nâ”‚ ðŸŽ‰ Plan: {plan_info['name']}\nâ”‚ ðŸ‘¥ Slots: {plan_info['accounts']}")
    except ValueError:
        await message.reply_text("âŒ Invalid user ID.", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("removepremium") & filters.private)
async def removepremium_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply_text("ðŸ’€ <b>Usage:</b> <code>/removepremium [user_id]</code>", parse_mode=ParseMode.HTML)
    try:
        target_id = str(int(message.command[1]))
        data = await async_get_data()
        removed = target_id in data.get("premium_users", {})
        if removed:
            del data["premium_users"][target_id]
            await async_update_data(data)
            add_admin_log("REMOVE_PREMIUM", message.from_user.id, f"User {target_id}")
        await message.reply_text(
            f"ðŸ’€ <b>{'Premium Removed' if removed else 'Not Found'}!</b>\nðŸ†” ID: <code>{target_id}</code>",
            parse_mode=ParseMode.HTML)
        if removed:
            await safe_send(int(target_id), "ðŸ’€ <b>Your premium has been removed.</b>\nContact @securedsitedns for renewal.")
    except ValueError:
        await message.reply_text("âŒ Invalid ID.", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("userinfo") & filters.private)
async def userinfo_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply_text("ðŸ’€ <b>Usage:</b> <code>/userinfo [user_id]</code>", parse_mode=ParseMode.HTML)
    try:
        target_id = int(message.command[1])
        data = get_data()
        user = data["users"].get(str(target_id), {})
        if not user:
            return await message.reply_text("âŒ User not found.", parse_mode=ParseMode.HTML)

        user_accs = {k: v for k, v in data["accounts"].items() if v.get("user_id") == target_id}
        camp = data["campaigns"].get(str(target_id), {})
        stats = data["stats"].get(str(target_id), {"total_sent": 0, "failed": 0})
        plan = get_user_plan_name(target_id)
        plan_key = get_user_plan_key(target_id)
        limit = get_user_account_limit(target_id)
        is_banned = target_id in data.get("banned_users", [])
        phones = [acc.get("phone", "?") for acc in user_accs.values()]
        camp_status = camp.get("status", "N/A")
        ref_count = len(data.get("referrals", {}).get(str(target_id), []))

        status_map = {"RUNNING": "ðŸŸ¢", "PAUSED": "ðŸ”´", "COMPLETED": "âœ…", "IDLE": "âšª"}
        status_icon = status_map.get(camp_status, "âšª")
        total_ops = stats["total_sent"] + stats["failed"]
        sr = round((stats["total_sent"] / total_ops * 100), 1) if total_ops > 0 else 0

        text = (
            f"ðŸ’€ <b>User Profile</b>\n\n"
            f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ ðŸ‘¤ {sanitize_html(user.get('name', 'N/A'))}\n"
            f"â”‚ ðŸ†” <code>{target_id}</code> | @{user.get('username', 'None')}\n"
            f"â”‚ ðŸ“… Joined: {user.get('joined_date', 'N/A')}\n"
            f"â”‚ ðŸ• Active: {user.get('last_active', 'N/A')}\n"
            f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ ðŸ’Ž {plan} | ðŸ‘¥ {len(user_accs)}/{limit}\n"
            f"â”‚ ðŸ“± {', '.join(phones) or 'None'}\n"
            f"â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
            f"â”‚ {status_icon} {camp_status} | ðŸŽ¯ {len(camp.get('targets', []))}\n"
            f"â”‚ ðŸš€ Sent: {stats['total_sent']:,} | âŒ {stats['failed']:,} | ðŸ“ˆ {sr}%\n"
            f"â”‚ ðŸ”— Referrals: {ref_count} | {'ðŸš« BANNED' if is_banned else 'âœ… Active'}\n"
            f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
        )
        await message.reply_text(text, parse_mode=ParseMode.HTML)
    except ValueError:
        await message.reply_text("âŒ Invalid ID.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Userinfo error: {e}")
        await message.reply_text(f"âŒ Error: {sanitize_html(str(e)[:200])}", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("listusers") & filters.private)
async def listusers_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = get_data()
    users = list(data["users"].values())
    if not users:
        return await message.reply_text("ðŸ’€ No users found.", parse_mode=ParseMode.HTML)
    users.sort(key=lambda x: x.get("joined_date", ""), reverse=True)
    text = f"ðŸ’€ <b>All Users ({len(users)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for u in users[:30]:
        uid = u.get("user_id", "?")
        name = truncate_text(sanitize_html(u.get("name", "N/A")), 12)
        tag = " ðŸš«" if uid in data.get("banned_users", []) else ""
        text += f"â”‚ <code>{uid}</code>{tag} â€¢ {name}\n"
    if len(users) > 30:
        text += f"â”‚ ... +{len(users) - 30} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("listpremium") & filters.private)
async def listpremium_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = get_data()
    premium = data.get("premium_users", {})
    if not premium:
        return await message.reply_text("ðŸ’€ No premium users.", parse_mode=ParseMode.HTML)
    text = f"ðŸ’€ <b>Premium Users ({len(premium)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for uid_str, info in premium.items():
        plan_name = PLANS.get(info.get("plan", "?"), {}).get("name", "?")
        user = data["users"].get(uid_str, {})
        name = truncate_text(sanitize_html(user.get("name", "N/A")), 12)
        text += f"â”‚ <code>{uid_str}</code> â€¢ {name} â€¢ {plan_name}\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("listbanned") & filters.private)
async def listbanned_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = get_data()
    banned = data.get("banned_users", [])
    if not banned:
        return await message.reply_text("ðŸ’€ No banned users.", parse_mode=ParseMode.HTML)
    text = f"ðŸ’€ <b>Banned Users ({len(banned)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for b_id in banned[:30]:
        user = data["users"].get(str(b_id), {})
        name = truncate_text(sanitize_html(user.get("name", "Unknown")), 12)
        text += f"â”‚ ðŸš« <code>{b_id}</code> â€¢ {name}\n"
    if len(banned) > 30:
        text += f"â”‚ ... +{len(banned) - 30} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("searchuser") & filters.private)
async def searchuser_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        return await message.reply_text("ðŸ’€ <b>Usage:</b> <code>/searchuser [query]</code>", parse_mode=ParseMode.HTML)
    query_str = " ".join(message.command[1:]).lower()
    data = get_data()
    results = []
    for uid_str, u in data["users"].items():
        if (query_str in str(u.get("user_id", "")).lower() or
                query_str in u.get("name", "").lower() or
                query_str in u.get("username", "").lower()):
            results.append((uid_str, u))
    if not results:
        return await message.reply_text("ðŸ’€ No users found.", parse_mode=ParseMode.HTML)
    text = f"ðŸ’€ <b>Search: '{sanitize_html(query_str)}' ({len(results)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for uid_str, u in results[:15]:
        uid = u.get("user_id", "?")
        name = truncate_text(sanitize_html(u.get("name", "N/A")), 12)
        uname = f"@{u['username']}" if u.get("username") else "No @"
        tag = " ðŸš«" if uid in data.get("banned_users", []) else ""
        text += f"â”‚ <code>{uid}</code>{tag} â€¢ {name} â€¢ {uname}\n"
    if len(results) > 15:
        text += f"â”‚ ... +{len(results) - 15} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("broadcast") & filters.private & filters.reply)
async def broadcast_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = get_data()
    total = len(data["users"])
    msg = await message.reply_text(f"ðŸ“¢ <b>Broadcasting to {total} users...</b>", parse_mode=ParseMode.HTML)
    s, f_count = 0, 0
    for uid_str in data["users"]:
        try:
            await message.reply_to_message.copy(int(uid_str))
            s += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            try:
                await message.reply_to_message.copy(int(uid_str))
                s += 1
            except Exception:
                f_count += 1
        except Exception:
            f_count += 1
        await asyncio.sleep(0.05)
    data = await async_get_data()
    data["settings"]["total_broadcasts"] = data["settings"].get("total_broadcasts", 0) + 1
    await async_update_data(data)
    add_admin_log("BROADCAST", message.from_user.id, f"Sent: {s}, Failed: {f_count}")
    await msg.edit_text(
        f"ðŸ’€ <b>Broadcast Done!</b>\nâ”‚ âœ… Sent: {s} | âŒ Failed: {f_count} | ðŸ“Š Total: {total}",
        parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("getdb") & filters.private)
async def getdb_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    backup_file = f"skull_backup_{int(time.time())}.json"
    try:
        data = get_data()
        backup = {"backup_info": {"created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "version": f"v{BOT_VERSION}"}, "data": data}
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)
        await message.reply_document(document=backup_file,
            caption=f"ðŸ’€ <b>DB Backup</b>\nðŸ‘¥ {len(data.get('users', {}))} users | ðŸ”‘ {len(data.get('accounts', {}))} accounts",
            parse_mode=ParseMode.HTML)
        add_admin_log("DOWNLOAD_DB", message.from_user.id)
    except Exception as e:
        logger.error(f"getdb error: {e}")
        await message.reply_text(f"âŒ Error: {sanitize_html(str(e)[:200])}", parse_mode=ParseMode.HTML)
    finally:
        if os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except Exception:
                pass


@bot.on_message(filters.command("uploaddb") & filters.private)
async def uploaddb_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text("ðŸ’€ Reply to a JSON file with <code>/uploaddb</code>", parse_mode=ParseMode.HTML)
    wait_msg = await message.reply_text("â³ <b>Restoring database...</b>", parse_mode=ParseMode.HTML)
    temp_file = f"temp_upload_{int(time.time())}.json"
    try:
        await message.reply_to_message.download(temp_file)
        with open(temp_file, "r", encoding="utf-8") as f:
            uploaded = json.load(f)
        if "backup_info" in uploaded and "data" in uploaded:
            new_data = uploaded["data"]
        elif "users" in uploaded:
            new_data = uploaded
        else:
            return await wait_msg.edit_text("âŒ Invalid format!", parse_mode=ParseMode.HTML)
        current = get_data()
        emergency = f"pre_upload_{int(time.time())}.json"
        with open(emergency, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2)
        await async_update_data(new_data)
        add_admin_log("UPLOAD_DB", message.from_user.id, f"Backup: {emergency}")
        await wait_msg.edit_text(
            f"ðŸ’€ <b>Database Restored!</b>\nâ”‚ ðŸ‘¥ {len(new_data.get('users', {}))} users | ðŸ’¾ {emergency}",
            parse_mode=ParseMode.HTML)
    except json.JSONDecodeError:
        await wait_msg.edit_text("âŒ Invalid JSON file!", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"uploaddb error: {e}")
        await wait_msg.edit_text(f"âŒ Error: {sanitize_html(str(e)[:200])}", parse_mode=ParseMode.HTML)
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


@bot.on_message(filters.command("resetdb") & filters.private)
async def resetdb_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    user_state[message.from_user.id] = {"step": "adm_confirm_reset", "_created": time.time()}
    await message.reply_text(
        "ðŸ’€ <b>âš ï¸ DANGER: Full Database Reset</b>\n\n"
        "Type <code>CONFIRM RESET</code> to proceed.\nAnything else = cancel.",
        parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("globalfooter") & filters.private)
async def globalfooter_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        data = get_data()
        current = data["settings"].get("global_ad_footer", "None")
        return await message.reply_text(
            f"ðŸ’€ <b>Global Footer:</b> <code>{sanitize_html(current or 'None')}</code>\n"
            f"Usage: <code>/globalfooter [text]</code> or <code>off</code>", parse_mode=ParseMode.HTML)
    footer_text = " ".join(message.command[1:])
    data = await async_get_data()
    if footer_text.lower() in ["off", "none", "clear", "remove"]:
        data["settings"]["global_ad_footer"] = ""
        await async_update_data(data)
        return await message.reply_text("âœ… Global footer cleared!", parse_mode=ParseMode.HTML)
    data["settings"]["global_ad_footer"] = footer_text
    await async_update_data(data)
    add_admin_log("SET_FOOTER", message.from_user.id, truncate_text(footer_text, 50))
    await message.reply_text(f"âœ… <b>Footer set!</b>\n<code>{sanitize_html(footer_text)}</code>", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("forcejoin") & filters.private)
async def forcejoin_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    if len(message.command) < 2:
        data = get_data()
        current = data["settings"].get("force_join_channel", "Disabled")
        return await message.reply_text(
            f"ðŸ’€ <b>Force Join:</b> <code>{current or 'Disabled'}</code>\n"
            f"Usage: <code>/forcejoin @channel</code> or <code>off</code>", parse_mode=ParseMode.HTML)
    channel = message.command[1].strip()
    data = await async_get_data()
    if channel.lower() in ["off", "none", "disable", "remove"]:
        data["settings"]["force_join_channel"] = ""
        await async_update_data(data)
        return await message.reply_text("âœ… Force join disabled!", parse_mode=ParseMode.HTML)
    if not channel.startswith("@"):
        channel = f"@{channel}"
    data["settings"]["force_join_channel"] = channel
    await async_update_data(data)
    add_admin_log("SET_FORCEJOIN", message.from_user.id, channel)
    await message.reply_text(
        f"âœ… <b>Force join set!</b> Channel: <code>{channel}</code>\nâš ï¸ Bot must be admin!", parse_mode=ParseMode.HTML)


@bot.on_message(filters.command("logs") & filters.private)
async def logs_cmd(client, message: Message):
    if not is_admin(message.from_user.id):
        return
    data = get_data()
    logs = data.get("admin_logs", [])
    if not logs:
        return await message.reply_text("ðŸ’€ No admin logs.", parse_mode=ParseMode.HTML)
    text = f"ðŸ’€ <b>Recent Logs ({len(logs)})</b>\n\nâ”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
    for log in logs[:20]:
        action = log.get("action", "?")
        ts = log.get("timestamp", "?")[:16]
        details = truncate_text(log.get("details", ""), 30)
        detail_str = f" â€¢ {details}" if details else ""
        text += f"â”‚ [{ts}] {action}{detail_str}\n"
    if len(logs) > 20:
        text += f"â”‚ ... +{len(logs) - 20} more\n"
    text += "â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
    await message.reply_text(text, parse_mode=ParseMode.HTML)


# =====================================================
# ðŸ”§ AUTO BACKUP TASK
# =====================================================
async def auto_backup_task():
    """Periodic auto-backup every 6 hours."""
    while True:
        try:
            await asyncio.sleep(21600)  # 6 hours
            data = get_data()
            if data["settings"].get("auto_backup", True):
                backup_file = f"auto_backup_{int(time.time())}.json"
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                data = await async_get_data()
                data["settings"]["last_backup"] = time.strftime('%Y-%m-%d %H:%M:%S')
                await async_update_data(data)
                logger.info(f"Auto backup created: {backup_file}")

                # Clean old backups (keep last 5)
                backup_files = sorted([
                    f for f in os.listdir(".")
                    if f.startswith("auto_backup_") and f.endswith(".json")
                ])
                while len(backup_files) > 5:
                    oldest = backup_files.pop(0)
                    try:
                        os.remove(oldest)
                        logger.info(f"Removed old backup: {oldest}")
                    except Exception as re:
                        logger.debug(f"Could not remove old backup {oldest}: {re}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Auto backup error: {e}")


# =====================================================
# ðŸ”§ STALE TASK CLEANER
# =====================================================
async def stale_task_cleaner():
    """Clean up stale campaign tasks and user states periodically."""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute

            # Clean finished tasks
            for u_id in list(active_tasks.keys()):
                task = active_tasks[u_id]
                if task.done():
                    del active_tasks[u_id]
                    try:
                        task.result()
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.warning(f"Task for {u_id} ended with error: {e}")

            # Clean stale user states (older than 30 minutes)
            now = time.time()
            for u_id in list(user_state.keys()):
                state = user_state[u_id]
                created = state.get("_created", now)
                if now - created > 1800:  # 30 min
                    tc = state.get("client")
                    if tc:
                        try:
                            await tc.disconnect()
                        except Exception as e:
                            logger.debug(f"Stale client disconnect for {u_id}: {e}")
                    del user_state[u_id]
                    logger.info(f"Cleaned stale state for user {u_id}")

            # Clean old rate limit entries
            for key in list(rate_limit_tracker.keys()):
                if now - rate_limit_tracker[key] > 300:
                    del rate_limit_tracker[key]

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Stale cleaner error: {e}")


# =====================================================
# ðŸ”§ HEALTH CHECK TASK
# =====================================================
async def health_check_task():
    """Periodic health check and reporting."""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            s = get_system_stats()
            logger.info(
                f"ðŸ’€ Health | Users: {s['total_users']} | "
                f"Sessions: {s['total_accounts']} | "
                f"Running: {s['running']} | "
                f"Tasks: {s['active_engine_tasks']} | "
                f"Sent: {s['total_sent']:,} | "
                f"Up: {s['uptime']}"
            )
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Health check error: {e}")


# =====================================================
# ðŸ MAIN EXECUTION
# =====================================================
async def start_bot():
    """Main bot startup function."""
    print("=" * 50)
    print("ðŸ’€ SKULL ADS BOT v3.0")
    print("=" * 50)
    print(f"ðŸ“± API ID: {API_ID}")
    print(f"ðŸ¤– Bot: @{BOT_USERNAME}")
    print(f"ðŸ‘‘ Admins: {ADMIN_IDS}")
    print(f"ðŸ’¾ Data File: {DATA_FILE}")
    print(f"ðŸ“ž phonenumbers: {'âœ…' if PHONENUMBERS_AVAILABLE else 'âŒ (basic mode)'}")
    print("=" * 50)

    # Increment start count
    data = await async_get_data()
    data["settings"]["bot_start_count"] = (
        data["settings"].get("bot_start_count", 0) + 1
    )
    await async_update_data(data)

    logger.info("Starting Pyrogram client...")
    await bot.start()

    try:
        me = await bot.get_me()
        logger.info(f"âœ… @{me.username} is LIVE!")
        print(f"âœ… @{me.username} is LIVE!")
    except Exception as e:
        logger.error(f"Failed to get bot info: {e}")
        print("âœ… Bot started but couldn't get info.")

    # Start background tasks
    logger.info("ðŸ”¥ Starting background tasks...")
    asyncio.create_task(ad_engine())
    asyncio.create_task(auto_backup_task())
    asyncio.create_task(stale_task_cleaner())
    asyncio.create_task(health_check_task())

    logger.info("âœ… All systems operational!")
    print("=" * 50)
    print("ðŸ”¥ Bot is fully operational!")
    print("ðŸ’€ Ad Engine: ACTIVE")
    print("ðŸ’¾ Auto Backup: ACTIVE")
    print("ðŸ§¹ Stale Cleaner: ACTIVE")
    print("ðŸ¥ Health Check: ACTIVE")
    print("=" * 50)

    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            s = get_system_stats()
            await bot.send_message(
                admin_id,
                f"ðŸ’€ <b>Bot Started Successfully!</b>\n\n"
                f"â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n"
                f"â”‚ ðŸ¤– <b>Version:</b> v{BOT_VERSION}\n"
                f"â”‚ ðŸ‘¥ <b>Users:</b> <code>{s['total_users']}</code>\n"
                f"â”‚ ðŸ”‘ <b>Sessions:</b> <code>{s['total_accounts']}</code>\n"
                f"â”‚ ðŸš€ <b>Running:</b> <code>{s['running']}</code>\n"
                f"â”‚ â±ï¸ <b>Start #:</b> <code>{s['bot_starts']}</code>\n"
                f"â”‚ ðŸ’¾ <b>DB Size:</b> <code>{s['file_size_str']}</code>\n"
                f"â”‚ ðŸ“ž <b>PhoneLib:</b> {'âœ…' if PHONENUMBERS_AVAILABLE else 'âŒ'}\n"
                f"â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€\n\n"
                f"All systems operational! âœ…",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.warning(f"Admin startup notify error: {e}")

    await idle()

    logger.info("Stopping bot...")
    await bot.stop()
    logger.info("ðŸ’€ Bot stopped gracefully.")
    print("ðŸ’€ Bot stopped.")


# =====================================================
# ðŸš€ ENTRY POINT
# =====================================================
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        print("\nðŸ’€ Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        traceback.print_exc()
    finally:
        try:
            loop.close()
        except Exception:
            pass

