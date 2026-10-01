from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI, OpenAI
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders

from app.config import settings

# How Portkey routing works here:
#   - The main model, backup model, retries and caching are set in a saved
#     Portkey config (created in the Portkey dashboard).
#   - Every request points to that config with the x-portkey-config-id header.
#   - This workspace does not accept configs sent inside the request, so all
#     routing changes are made in the Portkey dashboard, not in code.


def _make_headers(feature: str = "rag") -> dict:
    """Build the Portkey headers that point to the saved config by its ID."""
    if not settings.PORTKEY_PRIMARY_CONFIG_ID:
        raise ValueError(
            "PORTKEY_PRIMARY_CONFIG_ID is not set in .env. "
            "Get the real pc-... ID from the Portkey dashboard or "
            "run: PYTHONPATH=. python scripts/testing/list_portkey_configs.py"
        )
    return createHeaders(
        api_key=settings.PORTKEY_API_KEY,
        config_id=settings.PORTKEY_PRIMARY_CONFIG_ID,
        metadata={
            "feature": feature,
            "_user": "rag-system",
            "environment": "production",
        },
    )


# OpenAI client that sends every request through Portkey.
# The OpenAI SDK is used instead of the Portkey SDK because it lets us pass the
# config ID as a header, which works reliably with saved-config-only workspaces.
portkey_client = OpenAI(
    api_key=settings.PORTKEY_API_KEY,
    base_url=PORTKEY_GATEWAY_URL,
    default_headers=_make_headers(),
)


def get_langchain_llm(feature: str = "rag") -> ChatOpenAI:
    """
    Return a ChatOpenAI client that sends requests through Portkey, for the agent steps.

    Why ChatOpenAI:
      Portkey sits between the app and the model providers, and accepts the same
      requests as the OpenAI API. ChatOpenAI lets us point base_url at Portkey and send
      Portkey's key and config ID as headers. The model name format (@slug/model) is
      understood by Portkey, which forwards the request to the right provider.
    """
    return ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=f"@{settings.PORTKEY_PRIMARY_SLUG}/gpt-5-mini",
        default_headers=_make_headers(feature),
    )


def get_async_openai_client(feature: str = "rag") -> AsyncOpenAI:
    """
    Return an async OpenAI client that sends requests through Portkey.
    Use it for async LLM calls outside LangChain.
    """
    return AsyncOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        default_headers=_make_headers(feature),
    )


def extract_cache_status(response) -> str:
    """
    Read the x-portkey-cache-status header from the response.

    The OpenAI SDK doesn't always expose response headers, so this checks the
    usual places and returns 'MISS' if the header can't be found.
    """
    for attr in ("_raw_response", "_response", "_http_response", "headers"):
        raw = getattr(response, attr, None)
        if raw is not None:
            headers = getattr(raw, "headers", None)
            if headers is not None:
                status = headers.get("x-portkey-cache-status", "")
                if status:
                    return status.upper()
    return "MISS"
