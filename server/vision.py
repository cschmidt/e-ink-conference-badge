"""Claude Vision API integration for extracting text from badge photos."""

import base64
import json

import anthropic

from config import ANTHROPIC_API_KEY, VISION_MODEL

EXTRACTION_PROMPT = """Look at this conference badge photo and extract the following information.
Return ONLY a JSON object with these keys (use empty string if not found):

{
  "name": "Full name on the badge",
  "title": "Job title or role",
  "company": "Company or organization name",
  "event": "Conference or event name"
}

Return valid JSON only, no markdown fences or explanation."""


def extract_badge_text(image_bytes, media_type="image/jpeg"):
    """Extract text from a conference badge photo using Claude Vision.

    Args:
        image_bytes: Raw image bytes (JPEG or PNG)
        media_type: MIME type of the image

    Returns:
        dict with keys: name, title, company, event
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    b64_image = base64.standard_b64encode(image_bytes).decode("ascii")

    message = client.messages.create(
        model=VISION_MODEL,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {"name": "", "title": "", "company": "", "event": ""}

    return {
        "name": result.get("name", ""),
        "title": result.get("title", ""),
        "company": result.get("company", ""),
        "event": result.get("event", ""),
    }


def parse_custom_message(text):
    """Parse a custom message from the user.

    Supports formats:
    - "Display: Talk to me about AI governance"
    - "Talk to me about AI governance"
    - "heading: Talk to me about | body: AI governance for Canadian companies"

    Returns:
        dict with keys: heading, body
    """
    text = text.strip()

    # Strip "display:" prefix
    for prefix in ["display:", "Display:", "show:", "Show:", "update:", "Update:"]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    # Check for heading|body separator
    if "|" in text:
        parts = text.split("|", 1)
        heading = parts[0].strip()
        body = parts[1].strip()
        # Strip "heading:" and "body:" prefixes
        for prefix in ["heading:", "Heading:"]:
            if heading.startswith(prefix):
                heading = heading[len(prefix):].strip()
        for prefix in ["body:", "Body:"]:
            if body.startswith(prefix):
                body = body[len(prefix):].strip()
        return {"heading": heading, "body": body}

    # Default: use "Talk to me about..." as heading if it fits, else split
    if len(text) <= 60:
        return {"heading": text, "body": ""}
    else:
        # Split at a reasonable point
        words = text.split()
        mid = len(words) // 3
        heading = " ".join(words[:mid])
        body = " ".join(words[mid:])
        return {"heading": heading, "body": body}
