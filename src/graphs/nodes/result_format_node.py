from langchain_core.runnables import RunnableConfig

from graphs.state import GlobalState
from llm.client import extract_text, run_llm_cfg
from query.summary import summarize_results
from session import session_store


def result_format_node(state: GlobalState, _config: RunnableConfig | None = None) -> dict:
    if state.error_message:
        answer = state.error_message
    elif not state.query_result:
        answer = "未查询到符合条件的数据，请尝试调整问题描述。"
    else:
        text = run_llm_cfg(
            "result_format_llm_cfg",
            user_question=state.user_question,
            chat_history=session_store.format_messages(state.chat_history),
            query_result=summarize_results(state.query_result),
            has_chart="已" if state.chart_url else "未",
        )
        answer = extract_text(text)

    session_store.add_turn(state.session_id, state.user_question, answer)
    return {"final_answer": answer}
