.PHONY: setup install run clean

setup:
	@if [ ! -f .env ]; then \
		echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env; \
		echo "Created .env file. Please edit it with your bot token."; \
	else \
		echo ".env file already exists."; \
	fi

install:
	pip install -r requirements.txt

run:
	python bot.py

clean:
	rm -rf __pycache__
	rm -rf handlers/__pycache__
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
