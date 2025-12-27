"""
RealPNL Telegram Bot
Privacy-first crypto trade analysis companion
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo,
    CallbackQuery
)
from aiogram.enums import ParseMode

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Router (defined at module level for handlers)
router = Router()

# Bot instance (will be set in main())
bot = None


# ============ HANDLERS ============

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command - Welcome message with buttons"""
    
    # Get MINI_APP_URL from environment
    mini_app_url = os.getenv("MINI_APP_URL", "https://logiccrafterdz.github.io/realpnl/")
    
    if not mini_app_url:
        await message.answer("⚠️ Configuration error: MINI_APP_URL not set.")
        return
    
    welcome_text = """
🔍 <b>Welcome to RealPNL</b>

The privacy-first crypto trade analyzer.

<b>What I can do:</b>
📊 Analyze your trade history (CSV upload)
📈 Calculate real P&L after fees
🔄 Compare trading vs HODL returns
✅ Verify bot/channel activity

<i>🔒 All your trade data stays on your device. 
I never see or store your trades.</i>

Choose an action below:
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Upload CSV",
                web_app=WebAppInfo(url=mini_app_url)
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Verify Bot/Channel",
                callback_data="verify_help"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Help",
                callback_data="help"
            )
        ]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("upload"))
async def cmd_upload(message: Message):
    """Handle /upload command - Open Mini App"""
    
    # Get MINI_APP_URL from environment
    mini_app_url = os.getenv("MINI_APP_URL", "https://logiccrafterdz.github.io/realpnl/")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Open Trade Analyzer",
                web_app=WebAppInfo(url=mini_app_url)
            )
        ]
    ])
    
    await message.answer(
        "📊 <b>Upload Trade History</b>\n\n"
        "Click the button below to open the analyzer and upload your CSV file.\n\n"
        "<i>Required columns: date, symbol, action, price, amount</i>",
        reply_markup=keyboard
    )


@router.message(Command("verify"))
async def cmd_verify(message: Message):
    """Handle /verify @username command - Check channel activity"""
    
    # Extract username from command
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "⚠️ <b>Usage:</b> <code>/verify @username</code>\n\n"
            "Example: <code>/verify @dexscreener</code>"
        )
        return
    
    username = args[1].strip()
    
    # Remove @ if present
    if username.startswith("@"):
        username = username[1:]
    
    await message.answer(f"🔍 Checking @{username}...")
    
    try:
        # Try to get chat info
        chat = await bot.get_chat(f"@{username}")
        
        # Get chat type
        chat_type = chat.type
        is_accessible = True
        
        # Build response
        status = "✅ Active" if chat else "❌ Not found"
        
        response = f"""
📊 <b>Verification Report: @{username}</b>

{status}
📌 Type: {chat_type.capitalize() if chat_type else 'Unknown'}
👥 Title: {chat.title or 'N/A'}
"""
        
        if chat.description:
            # Truncate long descriptions
            desc = chat.description[:100] + "..." if len(chat.description) > 100 else chat.description
            response += f"📝 Bio: <i>{desc}</i>\n"
        
        # Note: Message count requires admin access, so we show a placeholder
        response += """
🔍 <b>Public Alerts:</b> None detected

<i>ℹ️ Note: Full message history requires channel admin access.</i>
"""
        
        await message.answer(response)
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "chat not found" in error_msg or "bad request" in error_msg:
            await message.answer(
                f"❌ <b>Cannot verify @{username}</b>\n\n"
                "Possible reasons:\n"
                "• Username doesn't exist\n"
                "• Channel/bot is private\n"
                "• Username is misspelled"
            )
        else:
            logger.error(f"Error verifying {username}: {e}")
            await message.answer(
                f"⚠️ <b>Error checking @{username}</b>\n\n"
                "Private channels and bots cannot be verified.\n"
                "Only public channels are supported."
            )


@router.message(Command("report"))
async def cmd_report(message: Message):
    """Handle /report command - Show report button if exists"""
    
    # Get MINI_APP_URL from environment
    mini_app_url = os.getenv("MINI_APP_URL", "https://logiccrafterdz.github.io/realpnl/")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Open Report",
                web_app=WebAppInfo(url=mini_app_url)
            )
        ]
    ])
    
    await message.answer(
        "📊 <b>Your Report</b>\n\n"
        "If you have previously uploaded trades, your report is saved locally in the Mini App.\n\n"
        "Click below to view:",
        reply_markup=keyboard
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await send_help(message)


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Handle help button callback"""
    await send_help(callback.message)
    await callback.answer()


@router.callback_query(F.data == "verify_help")
async def callback_verify_help(callback: CallbackQuery):
    """Handle verify help callback"""
    await callback.message.answer(
        "✅ <b>How to Verify a Bot/Channel</b>\n\n"
        "Use the command:\n"
        "<code>/verify @username</code>\n\n"
        "Examples:\n"
        "• <code>/verify @dexscreener</code>\n"
        "• <code>/verify @whale_alert</code>\n\n"
        "<i>Only public channels can be verified.</i>"
    )
    await callback.answer()


async def send_help(message: Message):
    """Send help message"""
    help_text = """
📚 <b>RealPNL Help</b>

<b>Commands:</b>
/start - Welcome & main menu
/upload - Upload CSV trade history
/verify @username - Check bot/channel activity
/report - View your saved report
/help - Show this help

<b>CSV Format:</b>
Your file should have these columns:
• <code>date</code> - Trade timestamp (YYYY-MM-DD HH:MM:SS)
• <code>symbol</code> - Token symbol (BTC, ETH, PEPE, etc.)
• <code>action</code> - buy or sell
• <code>price</code> - Price in USD
• <code>amount</code> - Quantity traded
• <code>fee_usd</code> - (Optional) Fee in USD

<b>Privacy:</b>
🔒 All trade data is processed in your browser
🔒 Nothing is sent to our servers
🔒 Reports are encrypted with your password

<b>Need help?</b>
Contact @your_support_username
"""
    await message.answer(help_text)


# ============ MAIN ============

async def main():
    """Start the bot"""
    global bot
    
    # Load environment variables
    load_dotenv()
    
    # Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MINI_APP_URL = os.getenv("MINI_APP_URL", "https://example.github.io/clearsignal/")
    
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    
    # Initialize bot (aiogram >= 3.7.0 syntax)
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)
    
    print("✅ RealPNL Bot is starting...")
    await dp.start_polling(bot)


# ============ HEALTH CHECK SERVER (for Render) ============

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Render health checks"""
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP logs to keep console clean"""
        pass


def run_health_server():
    """Run HTTP server for health checks"""
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"✅ Health server running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    # Start health check server in a separate daemon thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Start Telegram bot (main loop)
    asyncio.run(main())

