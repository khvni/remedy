import logging
import os

import google.generativeai as genai


logger = logging.getLogger(__name__)


def gemini_complete(prompt: str) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        # Offline/dev fallback: produce no prioritisation
        return '{"ordered_findings":[]}'

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-2.5-pro")
        resp = model.generate_content(prompt)
        return resp.text or "[]"
    except Exception as exc:  # pragma: no cover - relies on external API
        logger.warning("Gemini request failed: %s", exc)
        return "[]"
