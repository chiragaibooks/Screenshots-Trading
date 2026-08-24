import base64, json, os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def _client() -> Groq:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise EnvironmentError("GROQ_API_KEY not set. Add it to your .env file.")
    return Groq(api_key=key)

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

PROMPT = """You are a financial data extractor. Analyze this TradingView NIFTY screenshot.

RULES:
- Extract ONLY values that are clearly visible in the image.
- Do NOT invent, estimate, or fill in any value that is not explicitly shown.
- Use null for every field that is not visible.

Return ONLY a valid JSON object — no explanation, no markdown:
{
  "symbol": "NIFTY",
  "timestamp": "{ts}",
  "spot_price": null,
  "options": [
    {
      "strike": null,
      "expiry": null,
      "ce": {"delta": null, "gamma": null, "theta": null, "vega": null, "rho": null, "iv": null, "volume": null, "ltp": null},
      "pe": {"delta": null, "gamma": null, "theta": null, "vega": null, "rho": null, "iv": null, "volume": null, "ltp": null}
    }
  ]
}
Include one entry per visible strike row."""


def parse_screenshot(image_path: str, timestamp: str) -> dict:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    response = _client().chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text",      "text": PROMPT.replace("{ts}", timestamp)},
            ],
        }],
        max_tokens=4096,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {"raw_response": raw, "timestamp": timestamp, "parse_error": True}
