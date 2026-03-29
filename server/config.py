"""Configuration for the badge server."""

import os

# Flask
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# Telegram bot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_CHAT_IDS = [
    int(x) for x in os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",") if x
]

# Anthropic (Claude Vision API)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
VISION_MODEL = "claude-sonnet-4-6-20250514"

# Badge display
DISPLAY_WIDTH = 264
DISPLAY_HEIGHT = 176
GRAYSCALE_LEVELS = 4  # 0=black, 1=dark gray, 2=light gray, 3=white

# Layout defaults
DEFAULT_FONT = "DejaVuSans"
DEFAULT_FONT_BOLD = "DejaVuSans-Bold"

# QR code defaults
DEFAULT_QR_URL = os.environ.get("DEFAULT_QR_URL", "https://carlschmidt.ca")
DEFAULT_QR_LABEL = os.environ.get("DEFAULT_QR_LABEL", "carlschmidt.ca")

# Badge owner info (defaults, overridden by Vision API extraction)
BADGE_NAME = os.environ.get("BADGE_NAME", "Carl Schmidt")
BADGE_TITLE = os.environ.get("BADGE_TITLE", "AI Advisor")
BADGE_COMPANY = os.environ.get("BADGE_COMPANY", "")
BADGE_EVENT = os.environ.get("BADGE_EVENT", "ACETECH 2026")
