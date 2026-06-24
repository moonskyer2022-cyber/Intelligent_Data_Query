from functools import lru_cache

import pymysql
from pymysql.cursors import DictCursor

from settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

TABLES = {
    "商品表": "product",
    "类目表": "category",
    "用户表": "user",
    "订单主表": "orders",
    "订单明细表": "order_item",
    "采购记录表": "purchase_record",
    "对话记录表": "chat_record",
    "问数示例表": "query_example",
}

TABLE_NAME_TO_SQL = {**TABLES, **{v: v for v in TABLES.values()}}
SQL_TO_LOGICAL = {v: k for k, v in TABLES.items()}

TABLE_PRODUCT = "商品表"
TABLE_ORDERS = "订单主表"

JOIN_RELATIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("product", "purchase_record"): ("id", "product_id"),
    ("purchase_record", "product"): ("product_id", "id"),
    ("product", "category"): ("category_id", "id"),
    ("category", "product"): ("id", "category_id"),
    ("orders", "user"): ("user_id", "id"),
    ("user", "orders"): ("id", "user_id"),
    ("order_item", "orders"): ("order_id", "id"),
    ("orders", "order_item"): ("id", "order_id"),
    ("order_item", "product"): ("product_id", "id"),
    ("product", "order_item"): ("id", "product_id"),
}

PROMPT_JOINS = [
    "商品表.id = 采购记录表.product_id",
    "商品表.category_id = 类目表.id",
    "订单主表.user_id = 用户表.id",
    "订单明细表.order_id = 订单主表.id",
    "订单明细表.product_id = 商品表.id",
]


def sql_table(logical: str) -> str:
    sql = TABLE_NAME_TO_SQL.get(logical)
    if not sql:
        raise ValueError(f"未知数据表: {logical}")
    return sql


@lru_cache(maxsize=1)
def load_columns() -> dict[str, set[str]]:
    with pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT TABLE_NAME, COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (DB_NAME,),
            )
            rows = cur.fetchall()

    result: dict[str, set[str]] = {}
    for row in rows:
        result.setdefault(row["TABLE_NAME"], set()).add(row["COLUMN_NAME"])
    return result


def check_field(table: str, field: str) -> None:
    cols = load_columns().get(table, set())
    if field not in cols:
        raise ValueError(f"字段 {field} 不在表 {table} 中")


def schema_prompt() -> str:
    cols = load_columns()
    lines = ["# 数据表（物理表名）"]
    for logical, sql in TABLES.items():
        fields = sorted(cols.get(sql, []))
        lines.append(f"- {logical}({sql})：{', '.join(fields)}")

    lines.append("\n# 表关联")
    lines.extend(f"- {join}" for join in PROMPT_JOINS)

    metrics = _load_metric_hints()
    if metrics:
        lines.append("\n# 常用指标字段")
        lines.extend(f"- {metric}" for metric in metrics)

    lines.append(
        "\n# 查询建议\n"
        "- 订单总额 / GMV / 成交额 -> 订单主表 orders.total_amount\n"
        "- 明细销量 / 行金额 -> 订单明细表 order_item\n"
        "- 商品与类目 -> 商品表 + 类目表\n"
        "- 用户维度 -> 用户表 + 订单主表\n"
        "- 历史采购流水 -> 采购记录表 purchase_record"
    )
    return "\n".join(lines)


def _load_metric_hints() -> list[str]:
    try:
        with pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=DictCursor,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name, column_name, business_name, description
                    FROM schema_metadata
                    WHERE is_metric = 1
                    ORDER BY table_name, sort_order
                    """
                )
                rows = cur.fetchall()
        hints = []
        for row in rows:
            logical = SQL_TO_LOGICAL.get(row["table_name"], row["table_name"])
            name = row["business_name"] or row["column_name"]
            desc = row["description"] or ""
            hints.append(f"{logical}.{row['column_name']}（{name}）：{desc}")
        return hints
    except Exception:
        return []


def load_examples(limit: int = 8) -> list[str]:
    try:
        with pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            cursorclass=DictCursor,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT question FROM query_example
                    WHERE is_active = 1
                    ORDER BY id
                    LIMIT %s
                    """,
                    (limit,),
                )
                return [row["question"] for row in cur.fetchall()]
    except Exception:
        return [
            "查询所有商品名称和价格",
            "本月订单GMV是多少？",
            "各省份订单金额排名",
            "手机数码类有哪些商品？",
        ]


def list_tables_for_ui() -> list[tuple[str, str]]:
    return [(logical, sql) for logical, sql in TABLES.items() if sql != "query_example"]
