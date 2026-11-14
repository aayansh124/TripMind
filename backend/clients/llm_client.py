
"""Manage the Google Gemini client using LangChain."""

from typing import Type

from pydantic import BaseModel
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.config.settings import get_settings
from backend.utils.exceptions import LLMServiceError
from backend.utils.logger import logger


settings = get_settings()

# Cache initialized LLM clients by temperature.
_llm_cache: dict[float, ChatGoogleGenerativeAI] = {}


def get_gemini_client(
    temperature: float | None = None,
) -> ChatGoogleGenerativeAI:
    """Return a configured Gemini client."""

    if not settings.is_gemini_configured:
        raise LLMServiceError(
            "GEMINI_API_KEY is missing or invalid. "
            "Please configure it in your .env file.",
            model=settings.GEMINI_MODEL,
        )

    temp = round(
        temperature
        if temperature is not None
        else settings.GEMINI_TEMPERATURE,
        2,
    )

    if not 0.0 <= temp <= 1.0:
        raise ValueError(
            "Gemini temperature must be between 0.0 and 1.0."
        )

    if temp in _llm_cache:
        return _llm_cache[temp]

    try:
        logger.info(
            "Initializing Gemini client: model=%s, temperature=%.2f",
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

    except Exception as exc:
        logger.exception("Failed to initialize Gemini client.")

        raise LLMServiceError(
            f"Failed to initialize Gemini LLM: {exc}",
            model=settings.GEMINI_MODEL,
        ) from exc


def get_structured_llm(
    schema: Type[BaseModel],
    temperature: float | None = None,
) -> Runnable:
    """Return a Gemini client configured for structured output."""

    llm = get_gemini_client(temperature=temperature)

    try:
        return llm.with_structured_output(schema)

    except Exception as exc:
        logger.exception(
            "Failed to configure structured output for schema %s.",
            schema.__name__,
        )

        raise LLMServiceError(
            f"Failed to configure structured output: {exc}",
            model=settings.GEMINI_MODEL,
        ) from exc
