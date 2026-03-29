# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Custom e-ink conference badge for ACETECH (April 13, 2026). A Pimoroni Badger 2350 (264×176 4-level grayscale e-ink) that Carl can update on-the-fly from his phone via Telegram → CLARA → badge.

## Architecture

Three-tier system:

1. **Badge firmware** (MicroPython/Badgeware on Badger 2350 / RP2350): WiFi connection, MQTT subscribe for instant updates (with HTTP polling fallback), renders PNGs to e-ink display, 5 button handlers for mode switching (A=badge info, B=custom message, C=QR code, UP=force poll/reconnect, DOWN=sleep). Stores layouts locally as PNGs for offline fallback.

2. **Badge server** (Flask on bill-cipher): Renders 264×176 grayscale PNGs (Pillow + QR code generation), serves them via HTTP polling endpoints and publishes to MQTT. CLARA calls this server's HTTP API; the server handles MQTT publishing transparently.

3. **CLARA** is a NanoClaw agent running Claude Opus 4.6, connected to Telegram via a channel skill. Badge integration is a CLARA skill that calls the badge server's HTTP API (`http://host.docker.internal:5555`) to process photos (Vision API), render layouts, and queue updates.

4. **Data flow**: Carl (Telegram) → CLARA (NanoClaw skill) → badge server HTTP API → MQTT publish to `badge/carl/display` → badge subscribes and renders. Fallback: badge polls `GET /badge/pending` every 30s.

## Hardware

- **Device**: Pimoroni Badger 2350 — RP2350, 16MB flash, 8MB PSRAM, WiFi + BT 5.0, 1000mAh battery, translucent polycarbonate case
- **Display**: 2.7" 264×176 pixels, 4-level grayscale (black/dark gray/light gray/white)
- **Firmware**: MicroPython with Pimoroni Badgeware framework (NOT PicoGraphics)
- **Buttons**: 5 front-facing — A, B, C, UP, DOWN

## Key Technical Decisions

- **MQTT primary, polling fallback**: MQTT via `umqtt.simple` for instant updates (~3s end-to-end). HTTP polling every 30s as fallback if broker is unreachable.
- **MQTT broker on mabel (TrueNAS)**: Mosquitto on mabel, port-forwarded via `clara.schmidthaus.ca:1883`. Badge connects outbound — works through any NAT/firewall.
- **Tailscale rejected**: No MicroPython WireGuard support on RP2350; would require weeks of porting work.
- **4-level grayscale over 4-color**: Faster refresh (2-3s vs 15s), still provides visual hierarchy.
- **Badgeware framework**: Badge uses Pimoroni's Badgeware (not PicoGraphics). Key globals: `screen`, `badge`, `image`, `color`, `rom_font`, `State`, `rtc`. PNGs loaded via `image.load()`, display updated via `badge.update()`.
- **WiFi credentials**: Override `secrets.WIFI_SSID`/`secrets.WIFI_PASSWORD` at runtime (system partition is read-only).
- **App deployment**: App lives at `/data/apps/eink_badge/` (writable). System partition `/system/` is read-only.

## Network Topology

- **bill-cipher** (Ubuntu server): Runs badge Flask server on port 5555. LAN: 192.168.86.165, Tailscale: 100.110.201.90
- **mabel** (TrueNAS): Runs Mosquitto MQTT broker. Public via `clara.schmidthaus.ca:1883` (port-forwarded)
- **Badge**: Connects to WiFi (SchmidtHaus / phone hotspot / conference). Reaches MQTT broker at `clara.schmidthaus.ca:1883`. Reaches Flask server at LAN IP for HTTP polling fallback.

## Polling Protocol (fallback)

- Badge polls: `GET http://<server>/badge/pending` → `{"pending": true, "layout_type": "..."}`
- Badge downloads: `GET http://<server>/badge/image` → raw PNG bytes
- After rendering: `POST http://<server>/badge/clear`

## MQTT Protocol (primary)

- Topic: `badge/carl/display`
- Payload: raw PNG bytes (264×176 grayscale)
- Badge subscribes on boot, renders on message receipt

## Full Specification

See `~/Documents/Obsidian Vault/Projects/E-Ink-Conference-Badge.md` for comprehensive project spec including hardware comparison, architecture rationale, sourcing strategy, timeline, and open technical questions.

Also checked into the repo as `E-Ink-Conference-Badge.md` (may be slightly behind the Obsidian version).
