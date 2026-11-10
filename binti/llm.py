"""Model gateway (architecture section 2): one place that talks to the model provider.

Provider in the prototype: DeepSeek (OpenAI-compatible chat completions with tool calling).
Configure with environment variables, never in code:
  DEEPSEEK_API_KEY   required for live mode; without it the app runs in scripted mode
  DEEPSEEK_MODEL     optional, default "deepseek-chat"
  DEEPSEEK_BASE_URL  optional, default "https://api.deepseek.com"
Only fictional data is sent. Vendor terms and data residency are an open question (architecture section 8).
"""
import json
import os
import urllib.error
import urllib.request

from . import observability as obs


class LLMError(Exception):
    pass


def enabled() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def model_name() -> str:
    return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def chat(messages, tools=None, temperature=0.3, max_tokens=900, json_mode=False, timeout=45, api_key=None):
    """Return the assistant message dict: {"content": str|None, "tool_calls": [...]}.

    api_key overrides DEEPSEEK_API_KEY for one call. The eval judges use it, so a scripted run can still be graded."""
    with obs.child_span("llm: " + model_name(), "llm", input=messages,
                        metadata={"model": model_name(), "temperature": temperature, "tools": len(tools or [])}) as log:
        msg, usage = _chat(messages, tools, temperature, max_tokens, json_mode, timeout, api_key)
        log(output=msg, metrics={"prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
                                 "tokens": usage.get("total_tokens")})
        return msg


def _chat(messages, tools, temperature, max_tokens, json_mode, timeout, api_key=None):
    key = (api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
    if not key:
        raise LLMError("No DEEPSEEK_API_KEY set")
    body = {"model": model_name(), "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    req = urllib.request.Request(base + "/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LLMError(f"Model provider returned HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LLMError(f"Model provider unreachable: {e}") from None
    try:
        return data["choices"][0]["message"], data.get("usage") or {}
    except (KeyError, IndexError):
        raise LLMError("Unexpected response from model provider") from None
