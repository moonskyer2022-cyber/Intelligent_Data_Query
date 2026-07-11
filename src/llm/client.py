import json
import re
from typing import Any

from jinja2 import Template
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from settings import CONFIG_DIR, DEMO_MODE, LLM_API_KEY, LLM_BASE_URL, LLM_MAX_RESPONSE_CHARS, LLM_MODEL, LLM_TIMEOUT_SECONDS
from storage.db_meta import load_columns


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
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=0,
    )


def invoke_llm(messages: list[BaseMessage], cfg: dict[str, Any]) -> str:
    llm_cfg = cfg.get("config", {})
    llm = get_llm(temperature=llm_cfg.get("temperature", 0.1))
    return extract_text(llm.invoke(messages).content)


def run_llm_cfg(cfg_name: str, **prompt_vars: Any) -> str:
    if DEMO_MODE:
        return run_demo_cfg(cfg_name, prompt_vars)
    cfg = load_llm_cfg(cfg_name)
    prompt = Template(cfg["up"]).render(**prompt_vars)
    messages = [SystemMessage(content=cfg["sp"]), HumanMessage(content=prompt)]
    return invoke_llm(messages, cfg)


def run_demo_cfg(cfg_name: str, prompt_vars: dict[str, Any]) -> str:
    """Return deterministic responses for a repeatable local demonstration."""
    if cfg_name == "intent_analysis_llm_cfg":
        question = str(prompt_vars.get("user_question", ""))
        if "商品" in question and ("价格" in question or "名称" in question):
            return json.dumps(
                {
                    "query_type": "single",
                    "table_name": "商品表",
                    "field_names": ["product_name", "price"],
                    "page_size": 100,
                },
                ensure_ascii=False,
            )
        if "类目" in question and "销量" in question:
            return json.dumps(
                {
                    "query_type": "aggregate",
                    "primary_table": "订单明细表",
                    "join_tables": [{"table_name": "商品表", "join_type": "left"}],
                    "group_by": ["category_name"],
                    "aggregates": [{"field": "quantity", "func": "sum", "alias": "sales"}],
                    "order_by": [{"field": "sales", "direction": "desc"}],
                    "page_size": 100,
                    "chart_config": {"chart_type": "bar", "x_field": "category_name", "y_field": "sales"},
                },
                ensure_ascii=False,
            )
        if "省" in question or "地区" in question or "排名" in question:
            order_columns = load_columns().get("orders", set())
            dimension = "province" if "province" in order_columns else "region"
            return json.dumps(
                {
                    "query_type": "aggregate",
                    "table_name": "订单主表",
                    "group_by": [dimension],
                    "aggregates": [{"field": "total_amount", "func": "sum", "alias": "gmv"}],
                    "order_by": [{"field": "gmv", "direction": "desc"}],
                    "page_size": 100,
                    "chart_config": {"chart_type": "bar", "x_field": dimension, "y_field": "gmv"},
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "query_type": "aggregate",
                "table_name": "订单主表",
                "aggregates": [{"field": "total_amount", "func": "sum", "alias": "gmv"}],
                "page_size": 100,
            },
            ensure_ascii=False,
        )

    if cfg_name == "result_format_llm_cfg":
        question = str(prompt_vars.get("user_question", "本次问题"))
        query_result = str(prompt_vars.get("query_result", ""))
        has_chart = str(prompt_vars.get("has_chart", "未"))
        chart_note = "，并已生成图表" if has_chart == "已" else ""
        return f"演示模式已完成“{question}”查询{chart_note}。\n{query_result}"

    raise ValueError(f"Demo 模式不支持配置: {cfg_name}")


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
    cleaned = text.strip()
    if len(cleaned) > LLM_MAX_RESPONSE_CHARS:
        raise ValueError(f"LLM 响应超过 {LLM_MAX_RESPONSE_CHARS} 字符限制")
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start : end + 1]

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM 返回的查询计划不是有效 JSON，请重试或换一种更明确的问法") from exc

    if not isinstance(payload, dict):
        raise ValueError("LLM 返回的查询计划必须是 JSON 对象")
    return payload
