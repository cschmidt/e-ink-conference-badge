"""E-Ink Conference Badge - Badgeware App

Polls a server for badge display updates (PNG images), renders them,
and handles button-based mode switching.

Buttons:
  A - Show badge info (name/title/company)
  B - Show custom message
  C - Show QR code
  UP - Force poll for update
  DOWN - Sleep mode
"""

import os
import sys
import gc
import time
import secrets

sys.path.insert(0, "/data/apps/eink_badge")
os.chdir("/data/apps/eink_badge")

import urequests
import wifi

# --- WiFi credentials (override frozen secrets) ---
secrets.WIFI_SSID = "SchmidtHaus"
secrets.WIFI_PASSWORD = "b1ng0b0ng0"

# --- Configuration ---
SERVER_URLS = [
    "http://192.168.86.165:5555",  # bill-cipher LAN
    "http://100.110.201.90:5555",  # bill-cipher Tailscale (if badge ever gets TS)
]
POLL_SECONDS = 30
DATA_DIR = "/data/eink_badge"

# Layout slots
SLOT_BADGE = "badge_info"
SLOT_CUSTOM = "custom"
SLOT_QR = "qr"

# --- State ---
state = {
    "current_slot": SLOT_BADGE,
    "last_poll": 0,
    "wifi_ok": False,
}

State.load("eink_badge", state)

# Track which server URL works
_server_url = SERVER_URLS[0]
# Track whether we need a display refresh
_needs_update = False


# --- Helpers ---

def ensure_dirs():
    for d in ["/data", DATA_DIR]:
        try:
            os.mkdir(d)
        except OSError:
            pass


def slot_path(slot):
    return f"{DATA_DIR}/{slot}.png"


def save_png(data, slot):
    ensure_dirs()
    path = slot_path(slot)
    with open(path, "wb") as f:
        f.write(data)
    print(f"Saved {len(data)} bytes to {path}")


def has_layout(slot):
    try:
        os.stat(slot_path(slot))
        return True
    except OSError:
        return False


def show_layout(slot):
    """Display a saved layout PNG on screen. Does NOT call badge.update()."""
    global _needs_update
    path = slot_path(slot)
    try:
        img = image.load(path)
        screen.blit(img, rect(0, 0, img.width, img.height),
                     rect(0, 0, screen.width, screen.height))
        screen.dither()
        state["current_slot"] = slot
        State.save("eink_badge", state)
        _needs_update = True
        return True
    except Exception as e:
        print(f"Failed to load {path}: {e}")
        return False


def show_text(title, lines):
    """Draw a simple text status screen. Does NOT call badge.update()."""
    global _needs_update
    screen.pen = color.white
    screen.clear()

    # Title bar
    screen.pen = color.black
    screen.rectangle(0, 0, screen.width, 26)
    screen.pen = color.white
    screen.font = rom_font.smart
    w, _ = screen.measure_text(title)
    screen.text(title, (screen.width - w) // 2, 5)

    # Body text
    screen.pen = color.dark_grey
    screen.font = rom_font.smart
    y = 36
    for line in lines:
        screen.text(line, 10, y)
        y += 18

    _needs_update = True


def flush_display():
    """Only refresh e-ink if content has changed."""
    global _needs_update
    if _needs_update:
        badge.update()
        _needs_update = False


# --- WiFi ---

def connect_wifi():
    show_text("E-INK BADGE", ["", "Connecting to WiFi..."])
    flush_display()

    wifi.connect()
    attempts = 0
    while not wifi.tick():
        attempts += 1
        if attempts > 60:
            print("WiFi: connection timeout")
            state["wifi_ok"] = False
            return False
        time.sleep(0.25)

    state["wifi_ok"] = True
    ip = wifi.ip()
    print(f"WiFi connected: {ip}")
    show_text("CONNECTED", ["", f"IP: {ip}", "", "Polling for updates..."])
    flush_display()
    time.sleep(1)
    return True


# --- Polling ---

def _try_get(path, timeout=10):
    """Try GET request against known server URLs."""
    global _server_url
    # Try current URL first, then fall back to others
    urls = [_server_url] + [u for u in SERVER_URLS if u != _server_url]
    for base in urls:
        try:
            resp = urequests.get(base + path, timeout=timeout)
            _server_url = base  # Remember which one works
            return resp
        except Exception as e:
            print(f"GET {base}{path} failed: {e}")
            continue
    return None


def _try_post(path, timeout=10):
    """Try POST request against known server URLs."""
    global _server_url
    urls = [_server_url] + [u for u in SERVER_URLS if u != _server_url]
    for base in urls:
        try:
            resp = urequests.post(base + path, timeout=timeout)
            _server_url = base
            return resp
        except Exception as e:
            print(f"POST {base}{path} failed: {e}")
            continue
    return None


def poll_server():
    gc.collect()
    print("Polling for update...")
    resp = _try_get("/badge/pending")
    if not resp:
        return None, None
    if resp.status_code != 200:
        print(f"Poll: HTTP {resp.status_code}")
        resp.close()
        return None, None

    data = resp.json()
    resp.close()

    if not data.get("pending"):
        print("Poll: no update pending")
        return None, None

    layout_type = data.get("layout_type", "badge_info")
    print(f"Poll: update pending (type={layout_type})")

    # Download the PNG image
    gc.collect()
    img_resp = _try_get("/badge/image", timeout=15)
    if not img_resp:
        return None, None
    if img_resp.status_code != 200:
        print(f"Image download: HTTP {img_resp.status_code}")
        img_resp.close()
        return None, None

    png_data = img_resp.content
    img_resp.close()
    print(f"Downloaded {len(png_data)} bytes")
    return png_data, layout_type


def clear_pending():
    resp = _try_post("/badge/clear")
    if resp:
        resp.close()
        print("Cleared pending update")


def do_poll():
    png_data, layout_type = poll_server()
    if png_data:
        slot = layout_type if layout_type in (SLOT_BADGE, SLOT_CUSTOM, SLOT_QR) else SLOT_BADGE
        save_png(png_data, slot)
        del png_data
        gc.collect()

        if show_layout(slot):
            flush_display()
            clear_pending()
            return True

    return False


# --- Boot sequence ---

ensure_dirs()

show_text("E-INK BADGE", [
    "",
    "Carl Schmidt",
    "ACETECH 2026",
    "",
    "Starting up...",
])
flush_display()

wifi_ok = connect_wifi()

# Show last saved layout or default
if has_layout(state["current_slot"]):
    show_layout(state["current_slot"])
elif has_layout(SLOT_BADGE):
    show_layout(SLOT_BADGE)
else:
    show_text("E-INK BADGE", [
        "",
        "Carl Schmidt",
        "AI Advisor",
        "",
        "ACETECH 2026",
        "",
        "Send update via Telegram",
    ])

flush_display()

if wifi_ok:
    do_poll()


# --- Main loop ---

def update():
    global wifi_ok

    if badge.pressed(BUTTON_A):
        if has_layout(SLOT_BADGE):
            show_layout(SLOT_BADGE)
        else:
            show_text("BADGE INFO", ["", "No badge info yet", "", "Send photo via Telegram"])
        flush_display()

    if badge.pressed(BUTTON_B):
        if has_layout(SLOT_CUSTOM):
            show_layout(SLOT_CUSTOM)
        else:
            show_text("CUSTOM MSG", ["", "No custom message yet", "", "Send text via Telegram"])
        flush_display()

    if badge.pressed(BUTTON_C):
        if has_layout(SLOT_QR):
            show_layout(SLOT_QR)
        else:
            show_text("QR CODE", ["", "No QR code yet", "", "Send 'qr:<url>' via Telegram"])
        flush_display()

    if badge.pressed(BUTTON_UP):
        if wifi_ok:
            show_text("E-INK BADGE", ["", "Checking for updates..."])
            flush_display()
            if not do_poll():
                show_text("NO UPDATE", ["", "No pending update", "", "Current display kept"])
                flush_display()
        else:
            show_text("E-INK BADGE", ["", "Reconnecting WiFi..."])
            flush_display()
            wifi_ok = connect_wifi()
            if wifi_ok:
                do_poll()

    if badge.pressed(BUTTON_DOWN):
        show_text("SLEEP", [
            "",
            "Press any button to wake",
            "",
            "Battery saving mode",
        ])
        flush_display()
        badge.sleep()
        return

    # Auto-poll on timer
    if wifi_ok:
        do_poll()

    # Sleep until button or alarm
    rtc.set_alarm(seconds=POLL_SECONDS)
    wait_for_button_or_alarm(timeout=POLL_SECONDS * 1000)


def on_exit():
    State.save("eink_badge", state)


run(update)
