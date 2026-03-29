# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Custom e-ink conference badge for ACETECH (April 13, 2026). A Pimoroni Badger 2350 (264×176 4-level grayscale e-ink) that Carl can update on-the-fly from his phone via Telegram → CLARA → badge WiFi polling.

## Architecture

Three-tier system:

1. **Badge firmware** (MicroPython on Badger 2350 / RP2350): WiFi connection, polls CLARA every 30s for bitmap updates, renders to e-ink display, 5 button handlers for mode switching (A=badge info, B=custom message, C=QR code, D=cycle fallbacks, E=sleep). Stores 3-5 pre-loaded layouts locally for offline fallback.

2. **CLARA** is a NanoClaw agent running Claude Opus 4.6, connected to Telegram via a channel skill. Badge integration will be implemented as a new CLARA skill that: receives photos/text via Telegram, extracts text using Claude Vision API, renders 264×176 4-level grayscale bitmaps (Pillow + dithering + QR code generation), and serves pending updates at `https://clara.carlschmidt.ca/badge/pending`.

3. **Data flow**: Carl (Telegram) → CLARA (NanoClaw skill: Vision API + layout engine) → badge polls via HTTPS → e-ink display refresh (2-3s).

## Hardware

- **Device**: Pimoroni Badger 2350 — RP2350, 16MB flash, 8MB PSRAM, WiFi + BT 5.0, 1000mAh battery, translucent polycarbonate case
- **Display**: 2.7" 264×176 pixels, 4-level grayscale (black/dark gray/light gray/white)
- **Firmware**: MicroPython with Pimoroni PicoGraphics library
- **Buttons**: 5 front-facing physical buttons

## Key Technical Decisions

- **Polling over push**: Badge initiates all connections (works through any firewall/NAT). 30s latency is acceptable.
- **Tailscale rejected**: No MicroPython WireGuard support on RP2350; would require weeks of porting work.
- **4-level grayscale over 4-color**: Faster refresh (2-3s vs 15s), still provides visual hierarchy.
- **WiFi credentials**: Hardcoded list of SSIDs tried in order (home, phone hotspot, conference).
- **CLARA skill architecture**: Badge functionality lives as a NanoClaw skill, not a standalone backend.

## Expected Dependencies

**Badge (MicroPython)**: Pimoroni PicoGraphics library, MicroPython standard lib (WiFi, HTTP, filesystem)

**CLARA skill (Python)**: `anthropic` (Claude API), `Pillow` (bitmap rendering), `qrcode`, `requests`

## Polling Protocol

- Badge polls: `GET https://clara.carlschmidt.ca/badge/pending`
- No update: `{"pending": false}`
- Update available: `{"pending": true, "bitmap": "<base64 grayscale bitmap>"}`
- After rendering: `POST https://clara.carlschmidt.ca/badge/clear`

## Full Specification

See `E-Ink-Conference-Badge.md` for comprehensive project spec including hardware comparison, architecture rationale, sourcing strategy, timeline, and open technical questions.
