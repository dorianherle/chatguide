from __future__ import annotations

"""Multi-provider LLM dispatcher; isolates third-party SDKs from core logic."""

from typing import Any, Optional

__all__ = ["run_llm"]


def run_llm(
    prompt: str,
    *,
    model: str = "gemini/gemini-2.5-flash-lite",
    api_key: Optional[str] = None,
    temperature: float = 0.6,
    max_tokens: int = 256,
    extra_config: Optional[dict[str, Any]] = None,
):
    """Route to the correct provider based on model string prefix.
    
    Expected format: "provider/model_name"
    Examples:
        - "gemini/gemini-2.5-flash-lite"
        - "openai/gpt-4"
        - "anthropic/claude-3-5-sonnet"
    """
    if "/" not in model:
        raise ValueError(f"Model must be in format 'provider/model_name', got: {model}")
    
    provider, model_name = model.split("/", 1)
    
    if provider == "gemini":
        return _run_gemini(prompt, model=model_name, api_key=api_key,
                          temperature=temperature, max_tokens=max_tokens,
                          extra_config=extra_config)
    elif provider == "openai":
        return _run_openai(prompt, model=model_name, api_key=api_key,
                          temperature=temperature, max_tokens=max_tokens,
                          extra_config=extra_config)
    elif provider == "anthropic":
        return _run_anthropic(prompt, model=model_name, api_key=api_key,
                             temperature=temperature, max_tokens=max_tokens,
                             extra_config=extra_config)
    else:
        raise NotImplementedError(f"Provider '{provider}' not supported")


# -----------------------------------------------------------------------------
# Provider implementations
# -----------------------------------------------------------------------------

def _run_gemini(prompt: str, *, model: str, api_key: Optional[str],
                temperature: float, max_tokens: int,
                extra_config: Optional[dict[str, Any]]):
    from google import genai
    
    client = genai.Client(api_key=api_key)
    cfg = {
        "response_mime_type": "application/json",
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    if extra_config:
        cfg.update(extra_config)

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=cfg,
    )
    return getattr(resp, "parsed", None) or getattr(resp, "text", None)


def _run_openai(prompt: str, *, model: str, api_key: Optional[str],
                temperature: float, max_tokens: int,
                extra_config: Optional[dict[str, Any]]):
    raise NotImplementedError("OpenAI provider not yet implemented")


def _run_anthropic(prompt: str, *, model: str, api_key: Optional[str],
                   temperature: float, max_tokens: int,
                   extra_config: Optional[dict[str, Any]]):
    raise NotImplementedError("Anthropic provider not yet implemented")
