from typing import Any, Optional

from query.schema import JoinSpec, QueryPlan
from storage.db_meta import JOIN_RELATIONS, check_field, load_columns, sql_table


def _alias(i: int) -> str:
    return f"t{i}"


def _field_ref(field: str, table_map: list[tuple[str, str, str]]) -> str:
    if "." in field:
        _, field = field.split(".", 1)
    for _, sql_t, alias in table_map:
        if field in load_columns().get(sql_t, set()):
            check_field(sql_t, field)
            return f"`{alias}`.`{field}`"
    raise ValueError(f"未知字段: {field}")


def _aggregate_order_ref(field: str, plan: QueryPlan, table_map: list[tuple[str, str, str]]) -> str:
    aliases = {agg.alias for agg in plan.aggregates if agg.alias}
    if field in aliases:
        return f"`{field}`"
    return _field_ref(field, table_map)


def _build_filter(table_map: list[tuple[str, str, str]], filt: Optional[dict], params: list[Any]) -> str:
    if not filt or not filt.get("conditions"):
        return ""
    parts = []
    for cond in filt["conditions"]:
        col = _field_ref(cond["field_name"], table_map)
        op, val = cond["operator"], cond.get("value")
        if op == "is":
            parts.append(f"{col} = %s")
            params.append(val)
        elif op == "isNot":
            parts.append(f"{col} <> %s")
            params.append(val)
        elif op == "contains":
            parts.append(f"{col} LIKE %s")
            params.append(f"%{val}%")
        elif op == "isEmpty":
            parts.append(f"({col} IS NULL OR {col} = '')")
        elif op == "isNotEmpty":
            parts.append(f"({col} IS NOT NULL AND {col} <> '')")
        elif op == "isGreater":
            parts.append(f"{col} > %s")
            params.append(val)
        elif op == "isGreaterEqual":
            parts.append(f"{col} >= %s")
            params.append(val)
        elif op == "isLess":
            parts.append(f"{col} < %s")
            params.append(val)
        elif op == "isLessEqual":
            parts.append(f"{col} <= %s")
            params.append(val)
    if not parts:
        return ""
    conj = " AND " if filt.get("conjunction", "and") == "and" else " OR "
    return " WHERE " + conj.join(parts)


def _from_join(primary_logical: str, joins: list[JoinSpec]) -> tuple[str, list[tuple[str, str, str]]]:
    primary_sql = sql_table(primary_logical)
    table_map = [(primary_logical, primary_sql, _alias(0))]
    sql = f"`{primary_sql}` AS `{table_map[0][2]}`"
    prev_sql = primary_sql

    for join in joins:
        join_sql = sql_table(join.table_name)
        rel = JOIN_RELATIONS.get((prev_sql, join_sql))
        pk = join.primary_field or (rel[0] if rel else None)
        fk = join.join_field or (rel[1] if rel else None)
        if not pk or not fk:
            raise ValueError(f"缺少表关联: {prev_sql} -> {join_sql}")
        alias = _alias(len(table_map))
        table_map.append((join.table_name, join_sql, alias))
        join_type = "LEFT JOIN" if join.join_type == "left" else "INNER JOIN"
        sql += f" {join_type} `{join_sql}` AS `{alias}` ON `{table_map[-2][2]}`.`{pk}` = `{alias}`.`{fk}`"
        prev_sql = join_sql

    return sql, table_map


def build_sql(plan: QueryPlan) -> tuple[str, list[Any]]:
    params: list[Any] = []
    columns = load_columns()

    if plan.query_type == "single":
        sql_t = sql_table(plan.table_name)
        table_map = [(plan.table_name, sql_t, _alias(0))]
        cols = plan.field_names or sorted(columns.get(sql_t, []))
        sql = f"SELECT {', '.join(_field_ref(col, table_map) for col in cols)} FROM `{sql_t}` AS `{table_map[0][2]}`"
        filt = plan.filter.model_dump() if plan.filter else None
        sql += _build_filter(table_map, filt, params)
        if plan.order_by:
            sql += " ORDER BY " + ", ".join(
                f"{_field_ref(order.field, table_map)} {order.direction.upper()}" for order in plan.order_by
            )
        sql += " LIMIT %s"
        params.append(plan.page_size)
        return sql, params

    if plan.query_type == "multi":
        primary_conditions = plan.primary_conditions
        from_sql, table_map = _from_join(plan.primary_table, plan.join_tables)
        fields = (primary_conditions.field_names if primary_conditions else []) or [
            field for _, sql_t, _ in table_map for field in sorted(columns.get(sql_t, []))
        ]
        sql = f"SELECT {', '.join(_field_ref(field, table_map) for field in fields)} FROM {from_sql}"
        filt = primary_conditions.filter.model_dump() if primary_conditions and primary_conditions.filter else None
        sql += _build_filter(table_map, filt, params)
        sql += " LIMIT %s"
        params.append(plan.page_size)
        return sql, params

    if plan.join_tables:
        from_sql, table_map = _from_join(plan.primary_table, plan.join_tables)
    else:
        sql_t = sql_table(plan.table_name)
        table_map = [(plan.table_name, sql_t, _alias(0))]
        from_sql = f"`{sql_t}` AS `{table_map[0][2]}`"

    select_parts = [_field_ref(field, table_map) for field in plan.group_by]
    for agg in plan.aggregates:
        col = _field_ref(agg.field, table_map)
        alias = agg.alias or f"{agg.func}_{agg.field}"
        select_parts.append(f"{agg.func.upper()}({col}) AS `{alias}`")
    if not select_parts:
        raise ValueError("聚合查询缺少 group_by 或 aggregates")

    sql = f"SELECT {', '.join(select_parts)} FROM {from_sql}"
    filt = plan.filter.model_dump() if plan.filter else None
    sql += _build_filter(table_map, filt, params)
    if plan.group_by:
        sql += " GROUP BY " + ", ".join(_field_ref(field, table_map) for field in plan.group_by)
    if plan.order_by:
        sql += " ORDER BY " + ", ".join(
            f"{_aggregate_order_ref(order.field, plan, table_map)} {order.direction.upper()}" for order in plan.order_by
        )
    sql += " LIMIT %s"
    params.append(plan.page_size)
    return sql, params
