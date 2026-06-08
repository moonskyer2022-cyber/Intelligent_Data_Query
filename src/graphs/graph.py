from langgraph.graph import END, StateGraph

from graphs.nodes.chart_generation_node import chart_generation_node
from graphs.nodes.data_query_node import data_query_node
from graphs.nodes.intent_analysis_node import intent_analysis_node
from graphs.nodes.result_format_node import result_format_node
from graphs.state import GlobalState, GraphInput, GraphOutput


def _route_after_intent(state: GlobalState) -> str:
    return "result_format" if state.error_message else "data_query"


def _route_after_query(state: GlobalState) -> str:
    if state.error_message or not state.chart_config:
        return "result_format"
    return "chart_generation"


builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

builder.add_node("intent_analysis", intent_analysis_node)
builder.add_node("data_query", data_query_node)
builder.add_node("chart_generation", chart_generation_node)
builder.add_node("result_format", result_format_node)

builder.set_entry_point("intent_analysis")
builder.add_conditional_edges(
    "intent_analysis",
    _route_after_intent,
    {"data_query": "data_query", "result_format": "result_format"},
)
builder.add_conditional_edges(
    "data_query",
    _route_after_query,
    {"chart_generation": "chart_generation", "result_format": "result_format"},
)
builder.add_edge("chart_generation", "result_format")
builder.add_edge("result_format", END)

main_graph = builder.compile()
