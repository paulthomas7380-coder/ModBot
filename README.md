# ModBot - Telegram Moderation Bot

A powerful moderation bot for Telegram inspired by the Discord ModBot.

## Features
- 🛡️ Auto-moderation (bad words filtering)
- 🔗 Phishing URL detection
- ⚡ Strike system
- ⚠️ Warning system
- 🔨 Ban management
- 📊 Statistics tracking

## Commands
- `/start` - Welcome menu
- `/help` - Show help
- `/warn @user` - Warn a user
- `/strike @user` - Add a strike
- `/strikes @user` - Check strikes
- `/ban @user` - Ban user
- `/unban @user` - Unban user
- `/clear N` - Clear N messages
- `/stats` - Bot statistics
- `/ping` - Check bot status

## Deployment

### Prerequisites
- Python 3.8+
- Telegram Bot Token from @BotFather

### Local Setup
1. Clone the repository
2. Create `.env` file with `TELEGRAM_BOT_TOKEN=your_token_here`
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`

### Railway Deployment
1. Push code to GitHub
2. Connect GitHub repo to Railway
3. Add environment variable: `TELEGRAM_BOT_TOKEN`
4. Deploy!

## License
MIT License
