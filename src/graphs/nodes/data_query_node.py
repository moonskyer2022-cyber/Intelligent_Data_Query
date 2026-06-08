from langchain_core.runnables import RunnableConfig

from graphs.state import GlobalState
from query.schema import QueryPlan
from storage.mysql_db import MySQLDataStore


def data_query_node(state: GlobalState, _config: RunnableConfig) -> dict:
    if state.error_message or not state.query_plan:
        return {}

    try:
        query_result = MySQLDataStore().execute(QueryPlan(**state.query_plan))
    except ValueError as e:
        return {"error_message": str(e), "query_result": []}
    except Exception as e:
        return {"error_message": f"数据查询失败: {e}", "query_result": []}

    return {"query_result": query_result, "error_message": None}
