"""E-Ink Conference Badge - Badgeware App

MQTT subscribe for instant updates, HTTP polling as fallback.
Renders server-generated PNGs to 264x176 4-level grayscale e-ink display.

Buttons:
  A - Show badge info (name/title/company)
  B - Show custom message
  C - Show QR code
  UP - Force poll for update / reconnect
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
from umqtt.simple import MQTTClient

# --- WiFi credentials (override frozen secrets) ---
secrets.WIFI_SSID = "SchmidtHaus"
secrets.WIFI_PASSWORD = "b1ng0b0ng0"

# --- Configuration ---
# MQTT broker (on mabel/TrueNAS, public via clara.schmidthaus.ca)
MQTT_BROKER = "clara.schmidthaus.ca"
MQTT_PORT = 1883
MQTT_USER = b"badger"
MQTT_PASSWORD = b""  # Set when Mosquitto is configured
MQTT_TOPIC = b"badge/carl/display"
MQTT_CLIENT_ID = b"badger-carl"

# HTTP polling fallback (bill-cipher)
SERVER_URLS = [
    "http://192.168.86.165:5555",  # bill-cipher LAN
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
    "wifi_ok": False,
}

State.load("eink_badge", state)

_server_url = SERVER_URLS[0]
_needs_update = False
_mqtt_client = None
_mqtt_connected = False
_mqtt_pending = None  # (png_bytes, layout_type) received via MQTT


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

    screen.pen = color.black
    screen.rectangle(0, 0, screen.width, 26)
    screen.pen = color.white
    screen.font = rom_font.smart
    w, _ = screen.measure_text(title)
    screen.text(title, (screen.width - w) // 2, 5)

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
    show_text("CONNECTED", ["", f"IP: {ip}", "", "Starting up..."])
    flush_display()
    time.sleep(1)
    return True


# --- MQTT ---

def _on_mqtt_message(topic, msg):
    """MQTT message callback. Receives raw PNG bytes."""
    global _mqtt_pending
    print(f"MQTT: received {len(msg)} bytes on {topic}")
    _mqtt_pending = msg


def mqtt_connect():
    """Connect to MQTT broker. Returns True on success."""
    global _mqtt_client, _mqtt_connected
    if not MQTT_BROKER or not MQTT_PASSWORD:
        print("MQTT: no broker/password configured, skipping")
        return False
    try:
        gc.collect()
        _mqtt_client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER,
                                   port=MQTT_PORT,
                                   user=MQTT_USER,
                                   password=MQTT_PASSWORD)
        _mqtt_client.set_callback(_on_mqtt_message)
        _mqtt_client.connect()
        _mqtt_client.subscribe(MQTT_TOPIC)
        _mqtt_connected = True
        print(f"MQTT: connected to {MQTT_BROKER}, subscribed to {MQTT_TOPIC}")
        return True
    except Exception as e:
        print(f"MQTT connect failed: {e}")
        _mqtt_client = None
        _mqtt_connected = False
        return False


def mqtt_check():
    """Check for MQTT messages. Returns True if a message was processed."""
    global _mqtt_pending, _mqtt_connected
    if not _mqtt_connected or not _mqtt_client:
        return False
    try:
        _mqtt_client.check_msg()
    except Exception as e:
        print(f"MQTT check failed: {e}")
        _mqtt_connected = False
        return False

    if _mqtt_pending:
        png_data = _mqtt_pending
        _mqtt_pending = None
        # Save as badge_info by default (server could add metadata later)
        slot = SLOT_BADGE
        save_png(png_data, slot)
        del png_data
        gc.collect()
        if show_layout(slot):
            flush_display()
            return True
    return False


# --- HTTP Polling (fallback) ---

def _try_get(path, timeout=10):
    global _server_url
    urls = [_server_url] + [u for u in SERVER_URLS if u != _server_url]
    for base in urls:
        try:
            resp = urequests.get(base + path, timeout=timeout)
            _server_url = base
            return resp
        except Exception as e:
            print(f"GET {base}{path} failed: {e}")
            continue
    return None


def _try_post(path, timeout=10):
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
    print("HTTP poll: checking for update...")
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
    """HTTP poll cycle. Only used as fallback when MQTT is unavailable."""
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

# Connect MQTT (primary transport)
mqtt_ok = False
if wifi_ok:
    mqtt_ok = mqtt_connect()
    if mqtt_ok:
        print("Using MQTT (instant updates)")
    else:
        print("MQTT unavailable, using HTTP polling fallback")

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

# Initial poll if no MQTT
if wifi_ok and not mqtt_ok:
    do_poll()


# --- Main loop ---

def update():
    global wifi_ok, mqtt_ok

    # Button A: show badge info
    if badge.pressed(BUTTON_A):
        if has_layout(SLOT_BADGE):
            show_layout(SLOT_BADGE)
        else:
            show_text("BADGE INFO", ["", "No badge info yet", "", "Send photo via Telegram"])
        flush_display()

    # Button B: show custom message
    if badge.pressed(BUTTON_B):
        if has_layout(SLOT_CUSTOM):
            show_layout(SLOT_CUSTOM)
        else:
            show_text("CUSTOM MSG", ["", "No custom message yet", "", "Send text via Telegram"])
        flush_display()

    # Button C: show QR code
    if badge.pressed(BUTTON_C):
        if has_layout(SLOT_QR):
            show_layout(SLOT_QR)
        else:
            show_text("QR CODE", ["", "No QR code yet", "", "Send 'qr:<url>' via Telegram"])
        flush_display()

    # Button UP: force poll / reconnect
    if badge.pressed(BUTTON_UP):
        if not wifi_ok:
            show_text("E-INK BADGE", ["", "Reconnecting WiFi..."])
            flush_display()
            wifi_ok = connect_wifi()

        if wifi_ok:
            # Try MQTT reconnect if it was down
            if not mqtt_ok:
                mqtt_ok = mqtt_connect()

            show_text("E-INK BADGE", ["", "Checking for updates..."])
            flush_display()
            got_update = mqtt_check() if mqtt_ok else False
            if not got_update:
                got_update = do_poll()
            if not got_update:
                show_text("NO UPDATE", ["", "No pending update", "", "Current display kept"])
                flush_display()

    # Button DOWN: sleep
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

    # Check MQTT for incoming messages (primary path)
    if mqtt_ok:
        mqtt_check()
    # Fallback: HTTP poll on timer if no MQTT
    elif wifi_ok:
        do_poll()

    # Try MQTT reconnect periodically if it's down
    if wifi_ok and not mqtt_ok:
        mqtt_ok = mqtt_connect()

    # Sleep until button or alarm
    rtc.set_alarm(seconds=POLL_SECONDS)
    wait_for_button_or_alarm(timeout=POLL_SECONDS * 1000)


def on_exit():
    State.save("eink_badge", state)
    if _mqtt_client:
        try:
            _mqtt_client.disconnect()
        except:
            pass


run(update)
