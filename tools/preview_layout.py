#!/usr/bin/env python3
"""Preview badge layouts locally without the badge hardware.

Usage:
    python tools/preview_layout.py badge_info "Carl Schmidt" "AI Advisor" "" "ACETECH 2026"
    python tools/preview_layout.py custom "Talk to me about..." "AI governance for Canadian companies"
    python tools/preview_layout.py qr "https://carlschmidt.ca" "carlschmidt.ca"
    python tools/preview_layout.py test  # Renders all three and opens them
"""

import sys
import os

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

from renderer import render_badge_info, render_custom_message, render_qr_code, render_preview_png


def save_and_open(bitmap_b64, filename):
    png_bytes = render_preview_png(bitmap_b64)
    with open(filename, "wb") as f:
        f.write(png_bytes)
    print(f"Saved: {filename}")
    # Try to open on macOS
    os.system(f"open {filename} 2>/dev/null")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    mode = sys.argv[1]

    if mode == "badge_info":
        name = sys.argv[2] if len(sys.argv) > 2 else "Carl Schmidt"
        title = sys.argv[3] if len(sys.argv) > 3 else "AI Advisor"
        company = sys.argv[4] if len(sys.argv) > 4 else ""
        event = sys.argv[5] if len(sys.argv) > 5 else "ACETECH 2026"
        bitmap = render_badge_info(name, title, company, event)
        save_and_open(bitmap, "/tmp/badge_info.png")

    elif mode == "custom":
        heading = sys.argv[2] if len(sys.argv) > 2 else "Talk to me about..."
        body = sys.argv[3] if len(sys.argv) > 3 else "AI governance for Canadian companies"
        bitmap = render_custom_message(heading, body)
        save_and_open(bitmap, "/tmp/badge_custom.png")

    elif mode == "qr":
        url = sys.argv[2] if len(sys.argv) > 2 else "https://carlschmidt.ca"
        label = sys.argv[3] if len(sys.argv) > 3 else "carlschmidt.ca"
        bitmap = render_qr_code(url, label)
        save_and_open(bitmap, "/tmp/badge_qr.png")

    elif mode == "test":
        print("Rendering all layouts...")
        b1 = render_badge_info("Carl Schmidt", "AI Advisor", "", "ACETECH 2026")
        save_and_open(b1, "/tmp/badge_info.png")

        b2 = render_custom_message(
            "Talk to me about...",
            "AI governance for Canadian companies"
        )
        save_and_open(b2, "/tmp/badge_custom.png")

        b3 = render_qr_code("https://carlschmidt.ca", "carlschmidt.ca")
        save_and_open(b3, "/tmp/badge_qr.png")

        print("Done! Check /tmp/badge_*.png")
    else:
        print(f"Unknown mode: {mode}")
        print(__doc__)


if __name__ == "__main__":
    main()
