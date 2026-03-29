"""Flask server for e-ink conference badge.

Endpoints:
  GET  /badge/pending   — Badge polls this for updates (lightweight, no image data)
  GET  /badge/image     — Badge fetches raw PNG bytes of the pending update
  POST /badge/clear     — Badge confirms it rendered the update
  POST /badge/update    — Render and queue a badge update (JSON)
  POST /badge/photo     — Process a badge photo (Vision API → render → queue)
  GET  /badge/preview   — Preview current pending bitmap as PNG
  GET  /health          — Health check

Designed to be called by CLARA (NanoClaw agent) from inside a Docker container
via http://host.docker.internal:5555, or directly from the host.
"""

import base64
import io
import logging
import time

from flask import Flask, request, jsonify, send_file
import paho.mqtt.client as mqtt

import config
from renderer import (
    render_badge_info,
    render_custom_message,
    render_qr_code,
    render_preview_png,
    render_from_extracted_text,
)
from vision import extract_badge_text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY

# In-memory state for the pending badge update
_state = {
    "pending": False,
    "bitmap": None,       # base64-encoded PNG data
    "layout_type": None,  # "badge_info", "custom", "qr"
    "updated_at": None,
}


def _mqtt_publish(png_bytes, layout_type):
    """Publish PNG bytes to MQTT topic. Payload format: layout_type + newline + PNG bytes."""
    if not config.MQTT_BROKER:
        return
    try:
        payload = layout_type.encode() + b"\n" + png_bytes
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if config.MQTT_USER:
            client.username_pw_set(config.MQTT_USER, config.MQTT_PASSWORD)
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=10)
        client.publish(config.MQTT_TOPIC, payload, qos=1)
        client.disconnect()
        log.info("MQTT: published %s (%d bytes) to %s", layout_type, len(png_bytes), config.MQTT_TOPIC)
    except Exception as e:
        log.warning("MQTT publish failed (badge will use polling fallback): %s", e)


def _set_pending(bitmap_b64, layout_type):
    """Update state and publish to MQTT."""
    _state["pending"] = True
    _state["bitmap"] = bitmap_b64
    _state["layout_type"] = layout_type
    _state["updated_at"] = time.time()
    _mqtt_publish(base64.b64decode(bitmap_b64), layout_type)


# --- Badge polling endpoints ---

@app.route("/badge/pending", methods=["GET"])
def badge_pending():
    """Badge polls this endpoint every 30s.

    Returns lightweight JSON (no image data). Badge fetches the PNG
    separately via GET /badge/image to avoid base64 overhead.
    """
    if _state["pending"] and _state["bitmap"]:
        return jsonify({
            "pending": True,
            "layout_type": _state["layout_type"],
        })
    return jsonify({"pending": False})


@app.route("/badge/image", methods=["GET"])
def badge_image():
    """Serve the pending update as raw PNG bytes.

    The badge fetches this after seeing pending=true. Returns the PNG
    directly (Content-Type: image/png) so the badge can save it to
    flash and load it with image.load() without base64 decoding.
    """
    if not _state["pending"] or not _state["bitmap"]:
        return jsonify({"error": "No pending image"}), 404

    png_bytes = base64.b64decode(_state["bitmap"])
    return send_file(io.BytesIO(png_bytes), mimetype="image/png")


@app.route("/badge/clear", methods=["POST"])
def badge_clear():
    """Badge calls this after successfully rendering."""
    _state["pending"] = False
    log.info("Badge cleared pending update")
    return jsonify({"ok": True})


# --- Photo processing endpoint ---

@app.route("/badge/photo", methods=["POST"])
def process_photo():
    """Process a badge photo: extract text via Vision API, render, and queue.

    Accepts:
      - File upload: multipart form with 'photo' field
      - File path: JSON {"path": "/workspace/group/attachments/photo_123.jpg"}
      - Raw bytes: JSON {"image_base64": "...", "media_type": "image/jpeg"}
    """
    image_bytes = None
    media_type = "image/jpeg"

    if request.content_type and "multipart" in request.content_type:
        photo = request.files.get("photo")
        if not photo:
            return jsonify({"error": "No 'photo' field in upload"}), 400
        image_bytes = photo.read()
        media_type = photo.content_type or "image/jpeg"

    else:
        data = request.get_json(silent=True) or {}

        if "path" in data:
            file_path = data["path"]
            try:
                with open(file_path, "rb") as f:
                    image_bytes = f.read()
            except (OSError, IOError) as e:
                return jsonify({"error": f"Cannot read file: {e}"}), 400
            if file_path.lower().endswith(".png"):
                media_type = "image/png"

        elif "image_base64" in data:
            image_bytes = base64.b64decode(data["image_base64"])
            media_type = data.get("media_type", "image/jpeg")

    if not image_bytes:
        return jsonify({"error": "No image provided"}), 400

    try:
        extracted = extract_badge_text(image_bytes, media_type)
        bitmap = render_from_extracted_text(extracted)

        _set_pending(bitmap, "badge_info")

        log.info("Photo processed: %s", extracted.get("name", "unknown"))
        return jsonify({
            "ok": True,
            "extracted": extracted,
        })
    except Exception as e:
        log.exception("Photo processing failed")
        return jsonify({"error": str(e)}), 500


# --- Update endpoint ---

@app.route("/badge/update", methods=["POST"])
def badge_update():
    """Render and queue a badge update.

    JSON body options:
      {"type": "badge_info", "name": "...", "title": "...", "company": "...", "event": "..."}
      {"type": "custom", "heading": "...", "body": "..."}
      {"type": "qr", "url": "...", "label": "..."}
      {"type": "raw", "bitmap": "<base64 badge bytes>"}
    """
    data = request.get_json(silent=True) or {}
    log.info("Badge update request: %s", data)
    if not data:
        return jsonify({"error": "Empty request body. Send JSON with 'type' field."}), 400
    update_type = data.get("type", "badge_info")

    if update_type == "badge_info":
        bitmap = render_badge_info(
            name=data.get("name", config.BADGE_NAME),
            title=data.get("title", config.BADGE_TITLE),
            company=data.get("company", config.BADGE_COMPANY),
            event=data.get("event", config.BADGE_EVENT),
        )
    elif update_type == "custom":
        bitmap = render_custom_message(
            heading=data.get("heading", ""),
            body=data.get("body", ""),
        )
    elif update_type == "qr":
        bitmap = render_qr_code(
            url=data.get("url", config.DEFAULT_QR_URL),
            label=data.get("label", config.DEFAULT_QR_LABEL),
        )
    elif update_type == "raw":
        bitmap = data.get("bitmap", "")
    else:
        return jsonify({"error": f"Unknown type: {update_type}"}), 400

    _set_pending(bitmap, update_type)

    return jsonify({"ok": True, "type": update_type})


@app.route("/badge/preview", methods=["GET"])
def badge_preview():
    """Preview the current pending bitmap as a PNG image."""
    if not _state["bitmap"]:
        return jsonify({"error": "No pending bitmap"}), 404

    png_bytes = render_preview_png(_state["bitmap"])
    return send_file(io.BytesIO(png_bytes), mimetype="image/png")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "pending": _state["pending"],
        "layout_type": _state["layout_type"],
        "updated_at": _state["updated_at"],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=config.DEBUG)
