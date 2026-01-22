# teabot

A Telegram bot for tea reminders.

## Setup

1. Clone the repository
2. Run `make setup` to create the `.env` file
3. Edit `.env` and add your Telegram bot token
4. Run `make install` to install dependencies
5. Run `make run` to start the bot

## Available Commands

| Command | Description |
|---------|-------------|
| `make setup` | Create `.env` configuration file |
| `make install` | Install Python dependencies |
| `make run` | Run the bot |
| `make clean` | Remove cache files |

## Configuration

The bot uses environment variables for configuration:

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (required)
- `DATABASE_PATH` - Path to SQLite database (default: `./data/tea_bot.db`)
- `TIMEZONE` - Timezone for reminders (default: `Asia/Almaty`)
