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


class LLMError(Exception):
    pass


def enabled() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def model_name() -> str:
    return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def chat(messages, tools=None, temperature=0.3, max_tokens=900, json_mode=False, timeout=45):
    """Return the assistant message dict: {"content": str|None, "tool_calls": [...]}."""
    if not enabled():
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
                                          "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"].strip()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise LLMError(f"Model provider returned HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LLMError(f"Model provider unreachable: {e}") from None
    try:
        return data["choices"][0]["message"]
    except (KeyError, IndexError):
        raise LLMError("Unexpected response from model provider") from None
