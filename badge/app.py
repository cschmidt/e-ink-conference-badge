"""E-Ink Conference Badge - Badgeware App

MQTT subscribe for instant updates from CLARA via Telegram.
Renders server-generated PNGs to 264x176 4-level grayscale e-ink display.

Buttons:
  A - Show badge info (name/title/company)
  B - Show custom message
  C - Show QR code
  UP - Reconnect WiFi/MQTT
  DOWN - Sleep mode
"""

import os
import sys
import gc
import time

sys.path.insert(0, "/system/apps/eink_badge")
os.chdir("/system/apps/eink_badge")

import wifi
from umqtt.simple import MQTTClient

# --- Configuration ---
MQTT_BROKER = "192.168.86.10"  # mabel LAN; use clara.schmidthaus.ca for conference
MQTT_PORT = 1883
MQTT_USER = b"badger"
MQTT_PASSWORD = b"b4dg3r-m4b3l"
MQTT_TOPIC = b"badge/carl/display"
MQTT_CLIENT_ID = b"badger-carl"
MQTT_KEEPALIVE = 120  # seconds; broker disconnects at 1.5x if no ping

DATA_DIR = "/data/eink_badge"

SLOT_BADGE = "badge_info"
SLOT_CUSTOM = "custom"
SLOT_QR = "qr"

# --- State ---
state = {"current_slot": SLOT_BADGE}
State.load("eink_badge", state)

_needs_update = False
_mqtt_client = None
_mqtt_connected = False
_mqtt_pending = None
_last_ping = 0
_last_retry = 0


# --- Helpers ---

def ensure_dirs():
    for d in ["/data", DATA_DIR]:
        try:
            os.mkdir(d)
        except OSError:
            pass


def slot_path(slot):
    return f"{DATA_DIR}/{slot}.png"


def has_layout(slot):
    try:
        os.stat(slot_path(slot))
        return True
    except OSError:
        return False


def save_png(data, slot):
    ensure_dirs()
    with open(slot_path(slot), "wb") as f:
        f.write(data)
    print(f"Saved {len(data)} bytes to {slot}")


def show_layout(slot):
    global _needs_update
    try:
        img = image.load(slot_path(slot))
        screen.blit(img, rect(0, 0, img.width, img.height),
                     rect(0, 0, screen.width, screen.height))
        screen.dither()
        state["current_slot"] = slot
        State.save("eink_badge", state)
        _needs_update = True
        return True
    except Exception as e:
        print(f"Failed to load {slot}: {e}")
        return False


def show_text(title, lines):
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
            print("WiFi: timeout")
            return False
        time.sleep(0.25)
    print(f"WiFi: {wifi.ip()}")
    return True


# --- MQTT ---

def _on_message(topic, msg):
    global _mqtt_pending
    print(f"MQTT recv: {len(msg)} bytes")
    _mqtt_pending = msg


def mqtt_connect():
    global _mqtt_client, _mqtt_connected, _last_ping

    # Clean up old client
    if _mqtt_client:
        try:
            _mqtt_client.disconnect()
        except:
            pass
        _mqtt_client = None
    _mqtt_connected = False

    if not MQTT_BROKER or not MQTT_PASSWORD:
        return False
    try:
        gc.collect()
        print(f"MQTT: connecting to {MQTT_BROKER}...")
        _mqtt_client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER,
                                   port=MQTT_PORT,
                                   user=MQTT_USER,
                                   password=MQTT_PASSWORD,
                                   keepalive=MQTT_KEEPALIVE)
        _mqtt_client.set_callback(_on_message)
        _mqtt_client.connect()
        _mqtt_client.subscribe(MQTT_TOPIC)
        # Set socket timeout so check_msg can't block forever
        _mqtt_client.sock.settimeout(5)
        _mqtt_connected = True
        _last_ping = time.time()
        print("MQTT: connected")
        return True
    except Exception as e:
        print(f"MQTT: failed: {e}")
        _mqtt_client = None
        _mqtt_connected = False
        return False


def mqtt_check():
    global _mqtt_pending, _mqtt_connected, _last_ping
    if not _mqtt_connected or not _mqtt_client:
        return False
    try:
        # Send keepalive ping to prevent broker disconnect
        now = time.time()
        if now - _last_ping >= MQTT_KEEPALIVE // 2:
            _mqtt_client.ping()
            _last_ping = now

        _mqtt_client.check_msg()
    except Exception as e:
        print(f"MQTT check: {e}")
        _mqtt_connected = False
        return False

    if _mqtt_pending:
        raw = _mqtt_pending
        _mqtt_pending = None
        nl = raw.find(b"\n")
        if nl > 0:
            layout_type = raw[:nl].decode()
            png_data = raw[nl + 1:]
        else:
            layout_type = SLOT_BADGE
            png_data = raw
        slot = layout_type if layout_type in (SLOT_BADGE, SLOT_CUSTOM, SLOT_QR) else SLOT_BADGE
        save_png(png_data, slot)
        del raw, png_data
        gc.collect()
        if show_layout(slot):
            flush_display()
            return True
    return False


# --- Boot ---

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

mqtt_ok = False
if wifi_ok:
    show_text("E-INK BADGE", ["", "Connecting to MQTT..."])
    flush_display()
    mqtt_ok = mqtt_connect()

# Show saved layout or default
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


# --- Main loop ---

def update():
    global wifi_ok, mqtt_ok, _last_retry

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
        show_text("E-INK BADGE", ["", "Reconnecting..."])
        flush_display()
        if not wifi_ok:
            wifi_ok = connect_wifi()
        if wifi_ok:
            mqtt_ok = mqtt_connect()
            if mqtt_ok:
                show_text("E-INK BADGE", ["", "MQTT connected!"])
            else:
                show_text("E-INK BADGE", ["", "MQTT failed"])
            flush_display()

    if badge.pressed(BUTTON_DOWN):
        show_text("SLEEP", ["", "Press any button to wake", "", "Battery saving mode"])
        flush_display()
        badge.sleep()
        return

    # Check for MQTT messages + send keepalive ping
    if mqtt_ok:
        mqtt_check()

    # Reconnect MQTT if down
    if wifi_ok and not mqtt_ok:
        if time.time() - _last_retry >= 60:
            _last_retry = time.time()
            mqtt_ok = mqtt_connect()

    # Don't use wait_for_button_or_alarm — it only breaks on button
    # press, so MQTT messages queue until a button is pressed.
    # Instead, sleep briefly and let run() call update() again.
    badge.poll()
    time.sleep(0.5)


def on_exit():
    State.save("eink_badge", state)
    if _mqtt_client:
        try:
            _mqtt_client.disconnect()
        except:
            pass


run(update)
