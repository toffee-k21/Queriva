
import logging

from ollama import chat
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_text(
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
) -> str:
    """Generate text using Ollama, falling back to Gemini on failure."""

    ollama_error = None

    # Primary provider: Ollama
    try:
        kwargs = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if json_mode:
            kwargs["format"] = "json"

        response = chat(**kwargs)
        result = response.message.content

        if not result or not result.strip():
            raise ValueError("Ollama returned an empty response.")

        return result.strip()

    except Exception as exc:
        ollama_error = exc
        logger.warning(
            "Ollama generation failed; attempting Gemini fallback: %s",
            exc,
        )

    # Fallback provider: Gemini
    if not settings.GEMINI_API_KEY:
        raise RuntimeError(
            "Ollama failed and GEMINI_API_KEY is not configured."
        ) from ollama_error

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json" if json_mode else "text/plain",
        )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_prompt,
            config=config,
        )

        result = response.text

        if not result or not result.strip():
            raise ValueError("Gemini returned an empty response.")

        logger.info("Successfully generated response using Gemini fallback.")
        return result.strip()

    except Exception as exc:
        logger.exception("Gemini fallback also failed.")

        raise RuntimeError(
            "Both Ollama and Gemini failed to generate a response."
        ) from exc
