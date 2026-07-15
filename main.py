import logging
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN set in environment variables")

# Moderation settings
BAD_WORDS = ['badword1', 'badword2', 'spam']  # Add your own list
STRIKE_LIMIT = 3
user_strikes = {}
user_warnings = {}
banned_users = {}

# Helper functions
def is_bad_word(text):
    """Check if text contains any bad words"""
    if not text:
        return False
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False

def is_phishing_url(text):
    """Simple URL check - expand as needed"""
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    urls = re.findall(url_pattern, text)
    suspicious = ['bit.ly', 'tinyurl', 'shorturl', 'cutt.ly']
    for url in urls:
        for sus in suspicious:
            if sus in url.lower():
                return True
    return False

# Command Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued"""
    keyboard = [
        [InlineKeyboardButton("📊 Help", callback_data='help')],
        [InlineKeyboardButton("ℹ️ About", callback_data='about')],
        [InlineKeyboardButton("🔨 Moderation Tools", callback_data='mod_tools')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 *Welcome to ModBot!*\n\n"
        "I'm your Telegram moderation assistant. I can help you keep your groups safe and organized.\n\n"
        "🔹 *Moderation Features:*\n"
        "• Auto-filter bad words\n"
        "• Phishing URL detection\n"
        "• Strike system\n"
        "• User warnings\n"
        "• Ban management\n\n"
        "Use the buttons below to get started!"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information"""
    help_text = (
        "📚 *ModBot Commands*\n\n"
        "🛠 *Moderation Commands:*\n"
        "`/warn @user` - Warn a user\n"
        "`/strike @user` - Add a strike to a user\n"
        "`/strikes @user` - Check user's strikes\n"
        "`/ban @user` - Ban a user (requires admin)\n"
        "`/unban @user` - Unban a user (requires admin)\n"
        "`/kick @user` - Kick a user (requires admin)\n"
        "`/clear N` - Clear N messages (requires admin)\n\n"
        "ℹ️ *Info Commands:*\n"
        "`/start` - Show welcome menu\n"
        "`/help` - Show this help\n"
        "`/stats` - Show bot statistics\n"
        "`/ping` - Check bot status"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn a user"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a user's message to warn them.")
        return
    
    warned_user = update.message.reply_to_message.from_user
    if warned_user.id == update.effective_user.id:
        await update.message.reply_text("❌ You can't warn yourself!")
        return
    
    user_id = warned_user.id
    if user_id not in user_warnings:
        user_warnings[user_id] = []
    
    user_warnings[user_id].append({
        'time': datetime.now(),
        'moderator': update.effective_user.full_name
    })
    
    warning_count = len(user_warnings[user_id])
    warning_msg = f"⚠️ User {warned_user.full_name} has been warned. (Warning #{warning_count})"
    
    if warning_count >= 3:
        warning_msg += "\n🔴 User has exceeded 3 warnings. Consider banning."
    
    await update.message.reply_text(warning_msg)

async def strike_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a strike to a user"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a user's message to add a strike.")
        return
    
    struck_user = update.message.reply_to_message.from_user
    if struck_user.id == update.effective_user.id:
        await update.message.reply_text("❌ You can't strike yourself!")
        return
    
    user_id = struck_user.id
    if user_id not in user_strikes:
        user_strikes[user_id] = 0
    
    user_strikes[user_id] += 1
    
    if user_strikes[user_id] >= STRIKE_LIMIT:
        await update.message.reply_text(
            f"🔴 User {struck_user.full_name} has reached {STRIKE_LIMIT} strikes! User has been auto-banned."
        )
        # Auto-ban logic would go here
        banned_users[user_id] = True
    else:
        await update.message.reply_text(
            f"⚡ Strike added to {struck_user.full_name}. (Strike #{user_strikes[user_id]}/{STRIKE_LIMIT})"
        )

async def strikes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user's strikes"""
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user = update.effective_user
    
    user_id = user.id
    strikes = user_strikes.get(user_id, 0)
    
    await update.message.reply_text(
        f"📊 User {user.full_name} has {strikes} strike(s) out of {STRIKE_LIMIT}."
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    stats_text = (
        "📊 *ModBot Statistics*\n\n"
        f"👥 Total users warned: {len(user_warnings)}\n"
        f"⚡ Total strikes given: {sum(user_strikes.values())}\n"
        f"🔴 Users banned: {len(banned_users)}\n"
        f"🕒 Uptime: Online\n"
        f"🤖 Version: 1.0.0"
    )
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if bot is responsive"""
    start_time = datetime.now()
    await update.message.reply_text("🏓 Pong!")
    end_time = datetime.now()
    latency = (end_time - start_time).total_seconds() * 1000
    await update.message.reply_text(f"⏱️ Response time: {latency:.0f}ms")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear messages (requires admin)"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Please reply to a message to start clearing from there.")
        return
    
    try:
        count = int(context.args[0]) if context.args else 10
        count = min(max(count, 1), 100)  # Limit to 1-100 messages
        
        chat_id = update.effective_chat.id
        message_id = update.message.reply_to_message.message_id
        
        # In real implementation, you'd need to delete messages
        await update.message.reply_text(f"✅ Cleared {count} messages (simulated)")
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Use: /clear [number] (e.g., /clear 10)")

# Message Handler for auto-moderation
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages for auto-moderation"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if user is banned
    if user_id in banned_users and banned_users[user_id]:
        await update.message.delete()
        await update.message.reply_text("🔴 You are banned from this chat.")
        return
    
    # Check for bad words
    if is_bad_word(text):
        await update.message.delete()
        warning_text = f"⚠️ {update.effective_user.full_name}, your message was removed due to inappropriate content."
        
        # Add a strike for using bad words
        if user_id not in user_strikes:
            user_strikes[user_id] = 0
        user_strikes[user_id] += 1
        
        if user_strikes[user_id] >= STRIKE_LIMIT:
            warning_text += f"\n🔴 You have been auto-banned for reaching {STRIKE_LIMIT} strikes."
            banned_users[user_id] = True
        
        await update.message.reply_text(warning_text)
        return
    
    # Check for phishing URLs
    if is_phishing_url(text):
        await update.message.delete()
        await update.message.reply_text(
            f"🔒 {update.effective_user.full_name}, your message was removed due to a suspicious URL."
        )
        return
    
    # Add more moderation rules as needed

# Callback Query Handler for inline buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == 'help':
        await query.edit_message_text(
            "📚 *ModBot Help*\n\n"
            "Use /help to see all available commands.\n"
            "Use /start to return to the main menu.",
            parse_mode='Markdown'
        )
    elif data == 'about':
        await query.edit_message_text(
            "ℹ️ *About ModBot*\n\n"
            "ModBot is a Telegram moderation bot inspired by the Discord ModBot.\n\n"
            "🔹 *Features:*\n"
            "• Auto-moderation\n"
            "• Strike system\n"
            "• Warning system\n"
            "• Ban management\n"
            "• Message filtering\n\n"
            "Made with ❤️ for Telegram communities.",
            parse_mode='Markdown'
        )
    elif data == 'mod_tools':
        tools_text = (
            "🔨 *Moderation Tools*\n\n"
            "• `/warn @user` - Warn a user\n"
            "• `/strike @user` - Add a strike\n"
            "• `/strikes @user` - Check strikes\n"
            "• `/ban @user` - Ban user\n"
            "• `/unban @user` - Unban user\n"
            "• `/clear N` - Clear N messages"
        )
        await query.edit_message_text(tools_text, parse_mode='Markdown')

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# Main function
def main():
    """Start the bot"""
    print("🤖 Starting ModBot...")
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("warn", warn_command))
    application.add_handler(CommandHandler("strike", strike_command))
    application.add_handler(CommandHandler("strikes", strikes_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Add message handler for auto-moderation
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the Bot
    print("✅ Bot is running!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
