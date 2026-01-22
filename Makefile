.PHONY: setup install run clean

VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

setup:
	@if [ ! -f .env ]; then \
		echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env; \
		echo "Created .env file. Please edit it with your bot token."; \
	else \
		echo ".env file already exists."; \
	fi

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) bot.py

clean:
	rm -rf __pycache__
	rm -rf handlers/__pycache__
	rm -rf $(VENV)
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
