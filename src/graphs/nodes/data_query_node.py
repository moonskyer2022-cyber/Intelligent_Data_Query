from langchain_core.runnables import RunnableConfig

from graphs.state import GlobalState
from query.schema import QueryPlan
from storage.mysql_db import MySQLDataStore


def data_query_node(state: GlobalState, _config: RunnableConfig | None = None) -> dict:
    if state.error_message or not state.query_plan:
        return {}

    try:
        query_result = MySQLDataStore().execute(QueryPlan(**state.query_plan))
    except ValueError as e:
        return {"error_message": str(e), "query_result": []}
    except Exception:
        return {
            "error_message": "数据查询失败，请确认 MySQL 服务已启动、.env 数据库配置正确，并已执行 scripts/init_mysql.sql 初始化表结构。",
            "query_result": [],
        }

    return {"query_result": query_result, "rows": query_result, "error_message": None}
