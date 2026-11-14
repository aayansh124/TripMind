"""Google Gemini LLM client management using langchain-google-genai."""

from functools import lru_cache
from typing import Any, Optional, Type
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.config.settings import get_settings
from backend.utils.exceptions import LLMServiceError
from backend.utils.logger import logger

settings = get_settings()

# Cache for initialized LLM instances by temperature
_llm_cache: dict[float, ChatGoogleGenerativeAI] = {}


def get_gemini_client(temperature: Optional[float] = None) -> ChatGoogleGenerativeAI:
    """Retrieve or initialize a configured ChatGoogleGenerativeAI instance.

    Args:
        temperature: Sampling temperature (0.0 to 1.0). If None, uses configured default.

    Returns:
        ChatGoogleGenerativeAI instance.

    Raises:
        LLMServiceError: If GEMINI_API_KEY is not configured or client creation fails.
    """
    if not settings.is_gemini_configured:
        raise LLMServiceError(
            "GEMINI_API_KEY is not configured. Please supply a valid Google Gemini API key in your .env file.",
            model=settings.GEMINI_MODEL,
        )

    temp = round(temperature if temperature is not None else settings.GEMINI_TEMPERATURE, 2)

    if temp in _llm_cache:
        return _llm_cache[temp]

    try:
        logger.info(
            "Initializing Gemini LLM client: model=%s, temperature=%.2f",
            settings.GEMINI_MODEL,
            temp,
        )
        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temp,
            max_retries=3,
            timeout=30.0,
        )
        _llm_cache[temp] = llm
        return llm
    except Exception as e:
        logger.exception("Failed to initialize Google Gemini LLM client: %s", e)
        raise LLMServiceError(f"Failed to initialize Gemini LLM: {str(e)}", model=settings.GEMINI_MODEL)


def get_structured_llm(schema: Type[BaseModel], temperature: Optional[float] = None) -> Any:
    """Retrieve a Gemini LLM instance bound with Pydantic structured output.

    Args:
        schema: Pydantic model class defining desired structured output.
        temperature: Sampling temperature.

    Returns:
        Runnable pipeline returning validated Pydantic instances.
    """
    llm = get_gemini_client(temperature=temperature)
    try:
        return llm.with_structured_output(schema)
    except Exception as e:
        logger.error("Failed to bind structured output schema %s to Gemini: %s", schema.__name__, e)
        raise LLMServiceError(
            f"Failed to bind structured output schema: {str(e)}",
            model=settings.GEMINI_MODEL,
        )

