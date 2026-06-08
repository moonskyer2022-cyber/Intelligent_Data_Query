import json
from typing import Any

from jinja2 import Template
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from settings import CONFIG_DIR, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def load_llm_cfg(name: str) -> dict[str, Any]:
    with open(CONFIG_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def get_llm(temperature: float = 0.1) -> ChatOpenAI:
    if not LLM_API_KEY:
        raise ValueError("未配置 LLM_API_KEY，请在 .env 中设置")
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=temperature,
    )


def invoke_llm(messages: list[BaseMessage], cfg: dict[str, Any]) -> str:
    llm_cfg = cfg.get("config", {})
    llm = get_llm(temperature=llm_cfg.get("temperature", 0.1))
    return extract_text(llm.invoke(messages).content)


def run_llm_cfg(cfg_name: str, **prompt_vars: Any) -> str:
    cfg = load_llm_cfg(cfg_name)
    prompt = Template(cfg["up"]).render(**prompt_vars)
    messages = [SystemMessage(content=cfg["sp"]), HumanMessage(content=prompt)]
    return invoke_llm(messages, cfg)


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts).strip()
    return str(content).strip()


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)
