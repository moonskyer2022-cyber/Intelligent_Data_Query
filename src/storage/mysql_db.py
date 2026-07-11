from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from query.schema import QueryPlan
from query.sql import build_sql
from settings import (
    DB_CONNECT_TIMEOUT,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_READ_TIMEOUT,
    DB_USER,
    DB_WRITE_TIMEOUT,
)


def _serialize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


class MySQLDataStore:
    def __init__(self):
        self._conn_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "connect_timeout": DB_CONNECT_TIMEOUT,
            "read_timeout": DB_READ_TIMEOUT,
            "write_timeout": DB_WRITE_TIMEOUT,
        }

    def execute(self, plan: QueryPlan) -> list[dict[str, Any]]:
        sql, params = build_sql(plan)
        if not sql.lstrip().upper().startswith("SELECT"):
            raise ValueError("仅允许执行只读 SELECT 查询")
        with pymysql.connect(**self._conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        records = []
        for i, row in enumerate(rows):
            fields = {_k: _serialize(v) for _k, v in row.items()}
            records.append({"record_id": str(i + 1), "fields": fields})
        return records
