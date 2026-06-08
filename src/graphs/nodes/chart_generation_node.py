from typing import Any

from langchain_core.runnables import RunnableConfig

from graphs.state import GlobalState
from tools.chart_generator import generate_chart, infer_chart_config


def chart_generation_node(state: GlobalState, _config: RunnableConfig) -> dict:
    chart_config = state.chart_config
    if not chart_config:
        return {"chart_url": None}

    if not chart_config.get("x_field") or not chart_config.get("y_field"):
        auto = infer_chart_config(chart_config.get("user_question", ""), state.query_result)
        for key in ("chart_type", "title", "x_label", "y_label"):
            if chart_config.get(key):
                auto[key] = chart_config[key]
        chart_config = auto

    x_field = chart_config.get("x_field", "")
    y_field = chart_config.get("y_field", "")
    if not x_field or not y_field:
        return {"chart_url": None}

    try:
        chart_url = generate_chart(
            data=state.query_result,
            chart_type=chart_config.get("chart_type", "bar"),
            x_field=x_field,
            y_field=y_field,
            title=chart_config.get("title", "数据图表"),
            x_label=chart_config.get("x_label", ""),
            y_label=chart_config.get("y_label", ""),
        )
    except Exception:
        chart_url = None

    return {"chart_url": chart_url}
