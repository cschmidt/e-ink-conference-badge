---
type: project
status: active
roles:
  - personal
topics:
  - hardware
  - ai
  - diy
client:
engagement_type: personal-project
started: 2026-02-27
target_end: 2026-04-13
people: []
created: 2026-03-02
updated: 2026-03-12
hardware_decision: pimoroni-badger-2350
architecture_decision: telegram-clara-badge-polling
---

## Context

Carl wants a custom e-ink conference badge for ACETECH (April 13, 2026) that he can update on-the-fly based on room vibe ("Talk to me about..."). Should look professional (not janky), ideally with AI integration to automatically reformat official conference badge photos.

**Why this matters:**
- Walking demo of "I actually build things with AI"
- Conversation starter at conferences
- Demonstrates taking off-the-shelf hardware + AI APIs → useful weekend project
- More compelling than any deck for advisory positioning

## Objectives

**Core functionality:**
1. Display name, title, company info extracted from official badge photo
2. Quick-update capability from phone (text or photo)
3. Multiple "modes" switchable via buttons (badge info, custom message, QR code)
4. Professional appearance (not janky DIY look)

**Success criteria:**
- Ready for ACETECH April 13
- Updates in 2-3 seconds from phone
- Runs full day on battery
- Looks clean and professional

## Hardware Selection (Updated March 2026)

### Recommended: Pimoroni Badger 2350

**Decision: Badger 2350 offers best balance of visual impact, professional appearance, and timeline**

**Specifications:**
- **Display:** 2.7" 264×176 pixels, **4-level grayscale** e-paper
- **MCU:** Raspberry Pi RP2350 (newest generation)
- **Memory:** 16MB flash + 8MB PSRAM (vs 2MB on Badger 2040 W)
- **Connectivity:** WiFi + Bluetooth 5.0
- **Battery:** 1,000 mAh integrated (100-200+ days standby)
- **Buttons:** 5 front-facing
- **Case:** Fully assembled translucent polycarbonate with rear lighting
- **Extras:** I2C connector for expansion, USB-C charging
- **Price:** £49.50 (~$84 CAD) badge only, £67.50 STEM Kit

**Why Badger 2350 is the sweet spot:**
- **4-level grayscale** provides visual hierarchy (not just B&W, but faster than 4-color)
- **Fully assembled** in professional case (no 3D printing, no DIY jank risk)
- **Fast refresh** (2-3 seconds estimated, similar to Badger 2040 W)
- **Superior battery** (1,000 mAh integrated vs AAA batteries)
- **Latest hardware** (RP2350, more memory, Bluetooth)
- **Available now** from Pimoroni (1 week Canadian delivery)
- **Proven ecosystem** (Pimoroni PicoGraphics library)
- **Rear lighting** adds polish (illuminates case)
- **Hits all success criteria:** Professional appearance, fast updates, full-day battery, April 13 deadline

**Trade-offs vs. alternatives:**
- vs. 4-color DIY: No red/yellow, but grayscale hierarchy + faster refresh + zero jank risk
- vs. Badger 2040 W: Slightly smaller (2.7" vs 2.9"), but grayscale + better hardware + integrated battery
- More expensive than DIY (~$84 vs ~$65-95), but guaranteed professional result

**Sources:**
- [Badgeware Badger 2350](https://shop.pimoroni.com/en-us/products/badger-2350)
- [Pimoroni Unveils RP2350 Badgeware - Hackster.io](https://www.hackster.io/news/pimoroni-unveils-the-raspberry-pi-rp2350-powered-badgeware-family-of-wearable-displays-9c43d88872cd)
- [Badgeware Series - LinuxGizmos](https://linuxgizmos.com/pimoroni-unveils-badgeware-series-featuring-new-e-paper-ips-and-led-wearable-devices/)

### Alternative Options Considered (March 2026)

**1. 4-Color eInk Badge (RP2040, DIY)**
- 2.9" 296×128, black/white/red/yellow
- Higher visual impact (4 colors)
- **Rejected:** 15-second refresh too slow, requires soldering/assembly, 3D printing needed, jank risk
- **Sources:** [Hackster.io](https://www.hackster.io/pablotrujillojuan/eink-badge-ca154f), [Hackaday.io](https://hackaday.io/project/203217-eink-badge)

**2. Pimoroni Badger 2040 W (original choice)**
- 2.9" black & white only (1-bit)
- Fast refresh (2-3 seconds)
- Mature ecosystem (Pimoroni PicoGraphics)
- **Rejected:** Superseded by Badger 2350 (grayscale + better hardware)
- **Source:** [Pimoroni Badger 2040](https://shop.pimoroni.com/en-us/products/badger-2040)

**3. XIAO ePaper DIY Kit EE02 (ESP32-S3, Jan 2026)**
- 13.3-inch Spectra 6-color display
- ESP32-S3 (WiFi + Bluetooth)
- **Rejected:** Way too large for badge (13.3" vs 2.7")
- **Note:** Shows latest e-ink tech (6-color displays now available)
- **Source:** [CNX Software](https://www.cnx-software.com/2026/01/10/xiao-epaper-diy-kit-ee02-an-esp32-s3-board-designed-for-13-3-inch-spectra-6-color-e-ink-display/)

**4. Adafruit MagTag 2025 Edition (ESP32-S2)**
- 2.9" grayscale with new SSD1680 driver
- Arduino and CircuitPython 10+ support
- **Rejected:** Superseded by Badger 2350 (better hardware, integrated case/battery)
- **Source:** [Adafruit MagTag](https://www.adafruit.com/product/4800)

**5. Good Display Smart E-Ink Badge (DMN029AB)**
- NFC capabilities
- Commercial solution (not DIY-focused)
- **Rejected:** Likely more expensive, less hackable
- **Source:** [Good Display](https://www.good-display.com/product/738.html)

### Sourcing Strategy

**Pimoroni Badger 2350:**
- Order from Pimoroni (ships to Canada)
- Canadian retailers: PiShop.ca, Elmwood Electronics (check stock)
- Ships fully assembled with case and battery
- 1 week delivery to BC
- £49.50 badge only, £67.50 STEM Kit (includes accessories)

**No additional parts needed:**
- ✅ Case included (translucent polycarbonate)
- ✅ Battery included (1,000 mAh integrated)
- ✅ Buttons included (5 front-facing)
- ✅ USB-C cable for charging/programming
- Optional: Lanyard (if not in STEM Kit)

## Architecture

### Recommended Approach: Telegram → CLARA → Badge

**Flow:**
1. **Carl → Telegram/WhatsApp**
   - Take photo of conference badge with phone
   - Send to CLARA via Telegram (or text message for custom content)
   - Natural language: "Update my badge with this" or "Display: Talk to me about AI governance"

2. **CLARA (Agent processing)**
   - Receives photo via Telegram webhook
   - Uses Claude Vision API to extract text from badge photo
   - Renders 264×176 grayscale bitmap (4-level, optimized for e-ink)
   - Layout engine: Clean typography with grayscale hierarchy
   - Uploads rendered image to badge endpoint (HTTP POST)
   - Confirms to Carl via Telegram: "Badge updated ✅"

3. **Badge (Badger 2350, MicroPython)**
   - Connects to WiFi (conference network or phone hotspot)
   - Runs lightweight HTTP server OR polls endpoint for updates
   - Receives grayscale bitmap from CLARA
   - Renders to e-ink display (~2-3 second refresh)
   - Button handlers for mode switching (badge info / custom message / QR code)

**Why this architecture:**
- **No separate web app needed** - Telegram is the interface (already where Carl talks to CLARA)
- **CLARA does the heavy lifting** - Vision API, layout engine, image rendering
- **Badge stays simple** - Just WiFi + display, minimal firmware
- **Natural language control** - "Update badge" instead of clicking through a form
- **Works anywhere** - Conference WiFi, phone hotspot, home network

### IP Discovery Architecture (Push Model)

**Problem:** Badge gets a dynamic IP address when it connects to WiFi. CLARA needs to know this IP to push bitmap updates.

**Solution: Badge registers itself with CLARA on startup**

**Flow:**

1. **Badge boots up (MicroPython firmware):**
   - Connects to WiFi (tries configured SSIDs in order: home WiFi, phone hotspot, conference WiFi)
   - Gets IP address from DHCP (e.g., 192.168.1.42 on local network)
   - Starts lightweight HTTP server on port 8080 (listens for bitmap POSTs from CLARA)

2. **Badge registers with CLARA:**
   - Makes HTTP POST to CLARA's registration endpoint: `https://clara.carlschmidt.ca/badge/register`
   - Sends JSON payload:
     ```json
     {
       "badge_id": "carl-acetech-2026",
       "ip_address": "192.168.1.42",
       "port": 8080,
       "network_ssid": "Carl's iPhone",
       "battery_level": 98,
       "timestamp": "2026-04-13T09:15:00Z"
     }
     ```
   - CLARA acknowledges registration, stores IP in memory/database

3. **CLARA receives Telegram photo/message:**
   - Carl sends: "Update my badge with this" + photo
   - CLARA extracts text via Vision API
   - Renders 264×176 grayscale bitmap
   - Looks up badge IP from registration: `192.168.1.42:8080`
   - POSTs bitmap to badge: `http://192.168.1.42:8080/update`

4. **Badge receives update:**
   - HTTP server on badge receives POST with bitmap data
   - Validates bitmap format (264×176, 4-level grayscale)
   - Renders to e-ink display (~2-3 seconds)
   - Sends success response to CLARA (HTTP 200)
   - CLARA confirms to Carl via Telegram: "Badge updated ✅"

**Network scenarios:**

**Home WiFi (same network as CLARA):**
- Badge: 192.168.1.42 (local IP)
- CLARA: Running on same network or VPS
- Direct HTTP POST works (both on same LAN or CLARA has public IP)

**Phone hotspot:**
- Badge: 172.20.10.2 (hotspot client IP)
- CLARA: Needs to be able to reach this IP
- **Option A:** CLARA runs on phone (Termux/localhost) → can reach badge directly
- **Option B:** Badge uses ngrok/Tailscale to expose HTTP server publicly → CLARA can reach via tunnel

**Conference WiFi (different network):**
- Badge: 10.50.2.105 (conference network)
- CLARA: Running on VPS (public internet)
- **Problem:** Conference WiFi may block incoming connections (firewall/NAT)
- **Solution:** Badge uses Tailscale to join your tailnet → CLARA can reach via Tailscale IP (100.x.x.x)

**Recommended: Polling mode (simplest, most reliable)**

Badge polls CLARA for updates every 30 seconds:
- Badge checks: `https://clara.carlschmidt.ca/badge/pending`
- If update available, CLARA returns bitmap in response
- Badge renders bitmap to display and clears pending flag
- Badge initiates all connections (works through any firewall/NAT)
- No complex networking, no IP discovery, no VPN required

**Why polling over push:**
- **Works everywhere:** Conference WiFi, phone hotspot, home network (badge initiates all connections)
- **Zero networking complexity:** No Tailscale client (doesn't exist for MicroPython on RP2350), no IP discovery, no incoming firewall issues
- **Reliable:** No push failures, timeouts, or unreachable badge scenarios
- **Simple firmware:** Just HTTP GET polling loop + display rendering
- **Trade-off:** 30-second latency instead of instant (acceptable for conference badge use case)

**Polling flow:**
1. Badge boots, connects to WiFi (tries configured SSIDs)
2. Every 30 seconds, badge polls: `GET https://clara.carlschmidt.ca/badge/pending`
3. CLARA responds:
   - No update: `{"pending": false}`
   - Update available: `{"pending": true, "bitmap": <base64 encoded grayscale bitmap>}`
4. If pending, badge decodes bitmap, renders to display, sends clear: `POST https://clara.carlschmidt.ca/badge/clear`
5. Repeat every 30 seconds

**Alternative (if instant updates needed):**

Hybrid push + polling fallback:
- Badge registers local IP on startup (best effort)
- CLARA tries push first to badge's local IP (succeeds at home, phone hotspot)
- Falls back to pending queue if push fails (conference WiFi with firewall)
- Badge polls every 30s as safety net
- **Trade-off:** More complex firmware, only marginally faster in some scenarios
- **Not recommended for v1:** Ship with polling, add push later if needed

**Why Tailscale was rejected:**
- No MicroPython support for WireGuard/Tailscale on RP2350
- MicroLink (Tailscale for ESP32) exists but uses C/C++ ESP-IDF, not MicroPython
- Would require porting C library to MicroPython or rewriting in MicroPython (weeks of work)
- Overengineered for conference badge use case (30s latency is fine)
- **Sources:** [MicroLink GitHub](https://github.com/CamM2325/microlink), [MicroPython WireGuard Issue](https://github.com/micropython/micropython/issues/17243)

### Update Flow in Practice

**At conference registration:**
1. Get paper badge at registration desk
2. Open Telegram, send photo to CLARA: "Update my badge with this"
3. CLARA extracts text via Vision API: "Carl Schmidt / AI Advisor / ACETECH 2026"
4. CLARA renders clean grayscale layout
5. Badge receives update over WiFi, refreshes in 2-3 seconds
6. CLARA confirms: "Badge updated ✅"

**During sessions (custom messages):**
1. Open Telegram, message CLARA: "Display: Talk to me about AI governance for Canadian companies"
2. CLARA renders custom layout (heading in dark gray, message in black)
3. Badge updates in 2-3 seconds
4. Instant conversation starter

**Button modes (physical buttons on badge):**
- **Button A:** Show conference badge info (name, title, company)
- **Button B:** Show custom "talk to me about..." message (last updated)
- **Button C:** Show QR code (LinkedIn or website)
- **Button D:** Cycle through saved layouts (local fallback if WiFi dies)
- **Button E:** Sleep mode / power save

**Fallback modes:**
- If WiFi dies, badge holds last image (e-ink persists without power)
- Button D cycles through 3-5 pre-loaded layouts (conference badge, 2-3 custom messages, QR code)
- Can update again once WiFi reconnects

## Build Effort Estimate

**Hardware setup:** ~15 minutes
- Charge battery via USB-C
- Flash MicroPython (Badger 2350 support in PicoGraphics)
- Already assembled in case

**Firmware (MicroPython on Badger 2350):** ~1-2 evenings
- WiFi connection (connect to SSID, get IP)
- Lightweight HTTP server (receive bitmap POSTs from CLARA)
- OR polling endpoint (check for updates every 30 seconds)
- Render grayscale bitmap to e-ink display (PicoGraphics)
- Button handlers (A/B/C/D/E for mode switching)
- Local storage for 3-5 fallback layouts
- Uses Pimoroni PicoGraphics library (well-documented, Badger 2350 support confirmed)

**CLARA extension (Python):** ~2-3 evenings
- Telegram webhook handler (receive photos + text from Carl)
- Claude Vision API integration (extract text from badge photos)
- Grayscale layout engine:
  - 264×176 bitmap renderer (Python Pillow)
  - 4-level grayscale palette (black, dark gray, light gray, white)
  - Typography hierarchy (bold headings, clean body text)
  - Dithering for visual richness
  - QR code generation (for LinkedIn/website mode)
- HTTP client to push bitmap to badge (POST to badge's IP or polling endpoint)
- Confirmation message back to Telegram ("Badge updated ✅")

**Most creative part:** Grayscale layout engine (Claude Vision text extraction → intelligent layout → 4-level grayscale bitmap with visual hierarchy)

**Total realistic effort:** 2-3 weekends with April 13 deadline (6 weeks = comfortable margin)

## Bill of Materials

### Pimoroni Badger 2350 (Recommended)

| Item | Est. Cost (CAD) |
|------|----------------|
| Badger 2350 badge | ~$84 (£49.50) |
| STEM Kit upgrade (optional) | ~$115 (£67.50) includes lanyard, accessories |
| **Total** | **~$84-115** |

**What's included:**
- ✅ Fully assembled badge in translucent polycarbonate case
- ✅ 1,000 mAh integrated battery
- ✅ 5 front-facing buttons
- ✅ USB-C cable (charging + programming)
- ✅ Rear case lighting
- ✅ I2C connector for expansion

**Build effort:** None (arrives assembled)
**Visual impact:** High (4-level grayscale, professional case)
**Sourcing time:** 1 week (Pimoroni ships to Canada)
**Jank risk:** Zero

**Plus:** Anthropic API costs (pennies per update)

## Technical Details

### Display Specs

**Pimoroni Badger 2350:**
- Resolution: 264 x 176 pixels
- Colors: 4-level grayscale (black, dark gray, light gray, white)
- Refresh time: ~2-3 seconds (estimated, similar to Badger 2040 W)
- Power: Only draws during refresh
- Battery: 1,000 mAh integrated (100-200+ days standby)

### Badge Layout Considerations
- 264x176 is enough for text and simple graphics
- **4-level grayscale enables visual hierarchy** (bold headings, subtle backgrounds)
- Clean typographic layout preferred
- Name, title, company + custom message
- Optional: QR code, simple logo
- Grayscale dithering can create richer visuals than pure B&W

### Battery Life
- E-ink only draws power during refresh
- WiFi polling every 30 seconds
- **1,000 mAh integrated battery**
- **100-200+ days standby** (conservative estimate)
- Full conference day with frequent updates: no problem
- USB-C charging between sessions

### Network Options
- Conference WiFi (primary)
- Phone hotspot (backup)
- Pre-loaded layouts (offline fallback)

## Risks and Mitigations

**Risk:** Conference WiFi spotty
**Mitigation:** Phone hotspot backup, pre-load badge layouts locally

**Risk:** E-ink resolution limiting
**Mitigation:** Focus on clean typography vs. photo replication (actually looks better)

**Risk:** Battery dies mid-conference
**Mitigation:** E-ink holds image without power, 100+ days standby means battery won't die, USB-C charging available

**Risk:** Not finished by April 13
**Mitigation:** 6 weeks runway, 2-3 weekend effort = comfortable margin

## Status

**Current phase:** Hardware decision made (March 12, 2026) — **Badger 2350 recommended**

**Decision:** Badger 2350 is the clear winner
- Best balance of visual impact (4-level grayscale), professional appearance (assembled case), fast refresh (2-3s), and timeline certainty (available now, 1 week delivery)
- Eliminates all jank risk (no 3D printing, no soldering, no assembly)
- Superior battery (1,000 mAh, 100+ days standby)
- Latest hardware (RP2350, 16MB flash, Bluetooth 5.0)

**Next steps:**
1. **This week:** Order Badger 2350 from Pimoroni (£49.50 badge or £67.50 STEM Kit)
   - Check Canadian retailers (PiShop.ca, Elmwood Electronics) for faster shipping
2. **Week 1 (hardware arrives):**
   - Charge battery via USB-C
   - Flash MicroPython (verify Badger 2350 support in PicoGraphics)
   - Test basic display rendering (hello world)
3. **Week 2-3 (firmware):**
   - WiFi connection (SSID config, get IP address)
   - HTTP server OR polling endpoint (decide which is simpler)
   - Receive grayscale bitmap, render to display
   - Button handlers (A/B/C/D/E mode switching)
   - Local storage for fallback layouts
4. **Week 3-4 (CLARA extension):**
   - Telegram webhook handler (receive photos + text)
   - Claude Vision API integration (text extraction)
   - Grayscale layout engine (264×176 bitmap, 4-level palette, typography, dithering)
   - HTTP client to push to badge
   - Confirmation messages
5. **Week 4:** End-to-end test at home
   - Mock conference badge photo → Telegram → CLARA → badge display
   - Test custom text messages
   - Test QR code generation
   - Verify button modes work
6. **Week 5:** Iterate on layout engine
   - Visual hierarchy refinement (heading vs body text)
   - Grayscale dithering tuning (subtle vs bold)
   - Handle edge cases (long names, multi-line text)
7. **Week 6 (April 7-13):** Final testing, polish
   - Test on conference WiFi (or phone hotspot)
   - Pre-load 3-5 fallback layouts
   - Deploy for ACETECH April 13

**Timeline cushion:** 6 weeks until April 13 = comfortable margin for Badger 2350

## Key Decisions

**Hardware (Updated March 12, 2026):** Pimoroni Badger 2350 — clear winner
- **4-level grayscale** provides visual hierarchy without 15-second color refresh penalty
- **Fully assembled** in professional translucent polycarbonate case (zero jank risk)
- **Fast refresh** (~2-3 seconds, same as Badger 2040 W)
- **Superior battery** (1,000 mAh integrated, 100-200+ days standby)
- **Latest hardware** (RP2350, 16MB flash, 8MB PSRAM, Bluetooth 5.0)
- **Available now** from Pimoroni, 1 week Canadian delivery
- **Hits all success criteria:** Professional, fast updates, full-day battery, April 13 timeline

**Architecture:** Cloud processing (vs badge-only)
- Better for AI integration, easier updates, simpler firmware

**Display strategy:** Clean typography + grayscale hierarchy (vs photo replication or 4-color)
- Better use of 264×176 resolution, more professional look
- **4-level grayscale enables visual hierarchy** (bold headings in dark gray, name in black, background accents in light gray)
- Grayscale dithering creates richer visuals than pure B&W
- Faster refresh than 4-color (2-3s vs 15s) = better UX for on-the-fly updates

## Technical Decisions Needed

**Badge firmware:**
- **Networking strategy:** Hybrid push + polling fallback (see IP Discovery Architecture)
  - Primary: Badge registers via Tailscale, CLARA pushes updates (instant)
  - Fallback: Badge polls if push fails (30-second latency)
- **WiFi credentials:** Hardcode 3-5 known SSIDs (home WiFi, phone hotspot, conference WiFi if known in advance)
  - Badge tries each SSID in order, connects to first available
  - Alternative: Config mode on first boot (press button to enter AP mode, configure via phone)
- **Tailscale integration:** Badge joins your tailnet on startup (stable IP across networks)
- **Fallback layouts:** Store 3-5 locally (badge info + 2-3 custom messages + QR code)

**CLARA layout engine:**
- Font choices for e-ink grayscale? (Need high-legibility, open source fonts)
- Text size hierarchy? (Heading: 24-28pt bold, Body: 18-20pt regular, Fine print: 12-14pt?)
- Grayscale palette mapping? (Black = pure black, Dark gray = 66%, Light gray = 33%, White = pure white?)
- How aggressive should dithering be? (Subtle for professional look vs. bold for maximum visual hierarchy?)
- QR code size/placement? (Bottom-right corner, 80×80px?)

**Integration:**
- Badge IP address discovery (see detailed architecture below)
- Telegram webhook (already implemented in CLARA)
- Error handling? (What if badge is offline? CLARA should queue update and retry?)

**Open questions:**
- Want mockups of 264×176 grayscale layouts before building?
- Specific layout templates needed? (3 modes: badge info, custom message, QR code — anything else?)
- Should buttons have fixed assignments or cycle through modes?

## Related

- ACETECH event (April 13, 2026)
- [[John-Diack]] — introduced Carl to ACETECH
- Conversation starter for advisory positioning
- Hardware + AI integration demonstration
- "Build things" credibility signal

## Strategic Value

**For advisory practice:**
- Walking proof of concept
- "Built this in two weekends" story
- Contrast to over-scoped AI projects
- Practical AI integration example

**For ACETECH:**
- Immediate conversation starter
- Demonstrates technical capability
- Shows AI vision API use case
- Embodies "build don't just talk" philosophy

**For personal brand:**
- Builder identity reinforcement
- Hardware + software + AI integration
- Weekend project → functional tool
- Not just slides, actual working system
