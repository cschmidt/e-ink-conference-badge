"""Telegram bot webhook handler for badge updates."""

import logging

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_CHAT_IDS
from vision import extract_badge_text, parse_custom_message
from renderer import render_badge_info, render_custom_message, render_qr_code, render_from_extracted_text

log = logging.getLogger(__name__)


def send_telegram_message(chat_id, text):
    """Send a message back to the user via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)


def download_telegram_photo(file_id):
    """Download a photo from Telegram by file_id."""
    # Get file path
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
    resp = requests.get(url, params={"file_id": file_id}, timeout=10)
    file_path = resp.json()["result"]["file_path"]

    # Download file
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    resp = requests.get(download_url, timeout=30)
    return resp.content


def _is_authorized(chat_id):
    """Check if the chat_id is in the allowed list."""
    if not TELEGRAM_ALLOWED_CHAT_IDS:
        return True  # No restriction if list is empty
    return chat_id in TELEGRAM_ALLOWED_CHAT_IDS


def handle_webhook(update):
    """Process an incoming Telegram webhook update.

    Returns:
        tuple: (bitmap_base64, layout_type) or (None, None) if no update needed
    """
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return None, None

    if not _is_authorized(chat_id):
        send_telegram_message(chat_id, "Not authorized for badge updates.")
        return None, None

    # Photo message — extract badge info from photo
    if message.get("photo"):
        # Get the largest photo
        photo = message["photo"][-1]
        file_id = photo["file_id"]

        send_telegram_message(chat_id, "Processing badge photo...")

        try:
            image_bytes = download_telegram_photo(file_id)
            extracted = extract_badge_text(image_bytes)
            bitmap = render_from_extracted_text(extracted)
            name = extracted.get("name", "Unknown")
            send_telegram_message(
                chat_id,
                f"Badge updated! Extracted: {name}\n"
                f"Title: {extracted.get('title', '-')}\n"
                f"Company: {extracted.get('company', '-')}"
            )
            return bitmap, "badge_info"
        except Exception as e:
            log.exception("Failed to process badge photo")
            send_telegram_message(chat_id, f"Failed to process photo: {e}")
            return None, None

    # Text message — custom display or QR
    if text:
        text_lower = text.lower().strip()

        # QR code command
        if text_lower.startswith("qr:") or text_lower.startswith("qr "):
            url = text[3:].strip()
            if not url:
                send_telegram_message(chat_id, "Usage: qr:<url>")
                return None, None
            bitmap = render_qr_code(url, label="Scan me")
            send_telegram_message(chat_id, f"Badge updated with QR code for {url}")
            return bitmap, "qr"

        # Badge info command
        if text_lower.startswith("badge:") or text_lower.startswith("badge "):
            parts = text[6:].strip()
            # Parse "name | title | company" format
            fields = [p.strip() for p in parts.split("|")]
            name = fields[0] if len(fields) > 0 else ""
            title = fields[1] if len(fields) > 1 else ""
            company = fields[2] if len(fields) > 2 else ""
            bitmap = render_badge_info(name, title, company)
            send_telegram_message(chat_id, f"Badge updated: {name}")
            return bitmap, "badge_info"

        # Default: custom message
        parsed = parse_custom_message(text)
        bitmap = render_custom_message(parsed["heading"], parsed["body"])
        send_telegram_message(chat_id, "Badge updated with custom message!")
        return bitmap, "custom"

    return None, None
