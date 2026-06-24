from langchain_core.runnables import RunnableConfig

from graphs.state import GlobalState
from llm.client import parse_json_response, run_llm_cfg
from query.schema import parse_query_plan
from session import session_store
from storage.db_meta import schema_prompt
from tools.chart_generator import should_generate_chart


def intent_analysis_node(state: GlobalState, _config: RunnableConfig) -> dict:
    try:
        text = run_llm_cfg(
            "intent_analysis_llm_cfg",
            user_question=state.user_question,
            chat_history=session_store.format_messages(state.chat_history),
            db_schema=schema_prompt(),
        )
        raw = parse_json_response(text)
        if not isinstance(raw, dict):
            raise ValueError("解析结果不是 JSON 对象")
        plan = parse_query_plan(raw)
        chart_config = raw.get("chart_config")
    except ValueError as e:
        return {
            "error_message": f"无法生成可执行的查询计划：{e}",
            "query_plan": None,
            "chart_config": None,
        }
    except Exception:
        return {
            "error_message": "调用智能分析服务失败，请确认 LLM_API_KEY、LLM_BASE_URL 和网络连接是否正常。",
            "query_plan": None,
            "chart_config": None,
        }

    if chart_config is None and should_generate_chart(state.user_question):
        chart_config = {"user_question": state.user_question, "chart_type": "bar"}

    return {"query_plan": plan.model_dump(), "chart_config": chart_config, "error_message": None}
