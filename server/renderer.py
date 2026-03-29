"""Bitmap layout engine for 264x176 grayscale e-ink display.

Renders badge layouts using Pillow as grayscale PNG images.
Output format: base64-encoded PNG (mode "L", 264x176).
The badge's Badgeware framework loads PNGs natively with image.load()
and handles dithering/quantization on-device.
"""

import base64
import io
import textwrap
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from config import DISPLAY_WIDTH, DISPLAY_HEIGHT

W, H = DISPLAY_WIDTH, DISPLAY_HEIGHT

# Grayscale values for drawing (full 0-255 range; badge dithers on-device)
BLACK = 0
DARK_GRAY = 85
LIGHT_GRAY = 170
WHITE = 255


def _load_font(bold=False, size=20):
    """Load a font, falling back to default if not available."""
    names = (
        ["DejaVuSans-Bold", "LiberationSans-Bold", "Arial Bold"]
        if bold
        else ["DejaVuSans", "LiberationSans", "Arial"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            try:
                return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}.ttf", size)
            except (OSError, IOError):
                continue
    return ImageFont.load_default(size=size)


def _img_to_png_bytes(img):
    """Convert a Pillow image to PNG bytes."""
    img = img.convert("L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _img_to_base64(img):
    """Convert image to base64-encoded PNG data."""
    return base64.b64encode(_img_to_png_bytes(img)).decode("ascii")


def _wrap_text(draw, text, font, max_width):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_badge_info(name, title="", company="", event=""):
    """Render conference badge info layout.

    Layout:
    - Top bar: event name (light gray background, dark text)
    - Center: name (large bold), title, company
    - Bottom accent line
    """
    img = Image.new("L", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Top bar with event name
    bar_h = 32
    draw.rectangle([0, 0, W, bar_h], fill=DARK_GRAY)
    font_event = _load_font(bold=True, size=18)
    if event:
        bbox = draw.textbbox((0, 0), event, font=font_event)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, 6), event, fill=WHITE, font=font_event)

    # Name (large, bold, centered)
    font_name = _load_font(bold=True, size=38)
    name_lines = _wrap_text(draw, name, font_name, W - 20)
    y = 44
    for line in name_lines:
        bbox = draw.textbbox((0, 0), line, font=font_name)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), line, fill=BLACK, font=font_name)
        y += bbox[3] - bbox[1] + 4

    y += 8

    # Title
    if title:
        font_title = _load_font(bold=True, size=22)
        title_lines = _wrap_text(draw, title, font_title, W - 20)
        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, y), line, fill=BLACK, font=font_title)
            y += bbox[3] - bbox[1] + 2

    # Company
    if company:
        y += 4
        font_company = _load_font(bold=False, size=18)
        bbox = draw.textbbox((0, 0), company, font=font_company)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, y), company, fill=DARK_GRAY, font=font_company)

    # Bottom accent line
    draw.rectangle([20, H - 6, W - 20, H - 4], fill=BLACK)

    return _img_to_base64(img)


def render_custom_message(heading, body=""):
    """Render a custom message layout.

    Layout:
    - Top: heading in bold (e.g., "Talk to me about...")
    - Body: message text wrapped
    - Bottom accent
    """
    img = Image.new("L", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Heading
    font_heading = _load_font(bold=True, size=24)
    heading_lines = _wrap_text(draw, heading, font_heading, W - 24)
    y = 12
    for line in heading_lines:
        draw.text((12, y), line, fill=BLACK, font=font_heading)
        bbox = draw.textbbox((0, 0), line, font=font_heading)
        y += bbox[3] - bbox[1] + 4

    # Divider
    y += 4
    draw.rectangle([12, y, W - 12, y + 2], fill=LIGHT_GRAY)
    y += 10

    # Body text
    if body:
        font_body = _load_font(bold=True, size=20)
        body_lines = _wrap_text(draw, body, font_body, W - 24)
        for line in body_lines:
            if y > H - 20:
                break
            draw.text((12, y), line, fill=BLACK, font=font_body)
            bbox = draw.textbbox((0, 0), line, font=font_body)
            y += bbox[3] - bbox[1] + 3

    # Bottom accent
    draw.rectangle([0, H - 3, W, H], fill=BLACK)

    return _img_to_base64(img)


def render_qr_code(url, label=""):
    """Render a QR code with optional label.

    Layout:
    - QR code centered (120x120)
    - Label text below
    """
    img = Image.new("L", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Generate QR code
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("L")

    # Scale to fill available space, leaving room for label
    qr_size = H - 40  # 136px
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    # Center QR code
    qr_x = (W - qr_size) // 2
    qr_y = 4
    img.paste(qr_img, (qr_x, qr_y))

    # Label below QR
    if label:
        font_label = _load_font(bold=True, size=20)
        bbox = draw.textbbox((0, 0), label, font=font_label)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, qr_y + qr_size + 8), label, fill=BLACK, font=font_label)

    return _img_to_base64(img)


def render_from_extracted_text(extracted):
    """Render badge layout from Vision API extracted text.

    Args:
        extracted: dict with keys like 'name', 'title', 'company', 'event'
    """
    return render_badge_info(
        name=extracted.get("name", ""),
        title=extracted.get("title", ""),
        company=extracted.get("company", ""),
        event=extracted.get("event", ""),
    )


def render_preview_png(bitmap_b64):
    """Convert base64-encoded PNG back to PNG bytes for preview/debugging.

    Since the stored format is now base64-encoded PNG, this simply decodes it.
    Returns PNG bytes.
    """
    return base64.b64decode(bitmap_b64)
