# E-Ink Badge Control

Carl has an e-ink conference badge (Pimoroni Badger 2350, 264x176 grayscale display). You can update what it shows by calling the badge server API at `http://host.docker.internal:5555`.

The badge polls the server every 30 seconds and displays whatever you queue.

## When to Use

When Carl asks to update his badge, change his badge, or anything related to his conference badge display. Common triggers:

- Sends a photo of a conference badge and says "update my badge" → use the photo endpoint
- "Display: Talk to me about AI governance" → custom message
- "Show my QR code" or "qr: https://..." → QR code layout
- "Update my badge to Carl Schmidt, AI Advisor" → badge info layout

## API Reference

### Update with structured data

```bash
curl -s -X POST http://host.docker.internal:5555/badge/update \
  -H "Content-Type: application/json" \
  -d '{"type": "badge_info", "name": "Carl Schmidt", "title": "AI Advisor", "event": "ACETECH 2026"}'
```

Types:
- `badge_info`: `{"type": "badge_info", "name": "...", "title": "...", "company": "...", "event": "..."}`
- `custom`: `{"type": "custom", "heading": "Talk to me about...", "body": "AI governance for Canadian companies"}`
- `qr`: `{"type": "qr", "url": "https://carlschmidt.ca", "label": "carlschmidt.ca"}`

### Update from a badge photo

When Carl sends a photo of a conference badge, the server extracts text via Vision API and renders it:

```bash
curl -s -X POST http://host.docker.internal:5555/badge/photo \
  -H "Content-Type: application/json" \
  -d '{"path": "/workspace/group/attachments/photo_123.jpg"}'
```

The path should be the attachment path from the incoming message (e.g., `/workspace/group/attachments/photo_12345.jpg`).

### Check status

```bash
curl -s http://host.docker.internal:5555/health
```

## Response Handling

After a successful API call, confirm to Carl briefly. Examples:
- "Badge updated! Showing your name and title."
- "Badge updated with your custom message."
- "QR code queued — badge will refresh in up to 30 seconds."

If the API returns an error, tell Carl what went wrong.
