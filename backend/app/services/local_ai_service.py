import json
import logging

import requests

from backend.app.core.config import settings


logger = logging.getLogger(__name__)


def generate_json_with_ollama(prompt: str, model: str | None = None) -> dict | list | None:
    if settings.ai_provider != "ollama":
        return None

    try:
        response = requests.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": model or settings.ollama_model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        text = str(payload.get("response", "")).strip()
        if not text:
            return None
        return json.loads(text)
    except Exception:
        logger.exception("Ollama request failed")
        return None
