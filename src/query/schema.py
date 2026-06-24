from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from storage.db_meta import TABLE_ORDERS, TABLE_PRODUCT, check_field, load_columns, sql_table

ALLOWED_FUNCS = {"sum", "count", "avg", "max", "min"}
ALLOWED_OPS = {
    "is",
    "isNot",
    "contains",
    "isEmpty",
    "isNotEmpty",
    "isGreater",
    "isGreaterEqual",
    "isLess",
    "isLessEqual",
}


class FilterCondition(BaseModel):
    field_name: str
    operator: str
    value: Any = None

    @field_validator("operator")
    @classmethod
    def check_operator(cls, v: str) -> str:
        if v not in ALLOWED_OPS:
            raise ValueError(f"不支持的操作符: {v}")
        return v


class TableFilter(BaseModel):
    conjunction: Literal["and", "or"] = "and"
    conditions: list[FilterCondition] = Field(default_factory=list)


class JoinSpec(BaseModel):
    table_name: str
    join_type: Literal["left", "inner"] = "left"
    primary_field: Optional[str] = None
    join_field: Optional[str] = None


class AggregateSpec(BaseModel):
    field: str
    func: str
    alias: Optional[str] = None

    @field_validator("func")
    @classmethod
    def check_func(cls, v: str) -> str:
        func = v.lower()
        if func not in ALLOWED_FUNCS:
            raise ValueError(f"不支持的聚合函数: {v}")
        return func


class OrderSpec(BaseModel):
    field: str
    direction: Literal["asc", "desc"] = "asc"


class QueryPlan(BaseModel):
    query_type: Literal["single", "multi", "aggregate"]
    table_name: str = TABLE_PRODUCT
    field_names: list[str] = Field(default_factory=list)
    filter: Optional[TableFilter] = None
    page_size: int = Field(default=100, ge=1, le=500)
    order_by: list[OrderSpec] = Field(default_factory=list)
    primary_table: str = TABLE_PRODUCT
    primary_conditions: Optional["QueryPlan"] = None
    join_tables: list[JoinSpec] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    aggregates: list[AggregateSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_plan(self) -> "QueryPlan":
        columns = load_columns()
        if self.query_type == "single":
            sql_t = sql_table(self.table_name)
            for field in self.field_names:
                check_field(sql_t, field)
            if self.filter:
                for condition in self.filter.conditions:
                    check_field(sql_t, condition.field_name)
        elif self.query_type == "multi":
            sql_table(self.primary_table)
            if not self.join_tables:
                raise ValueError("多表查询缺少 join_tables")
            for join in self.join_tables:
                sql_table(join.table_name)
        elif self.query_type == "aggregate":
            tables = [sql_table(self.primary_table if self.join_tables else self.table_name)]
            for join in self.join_tables:
                tables.append(sql_table(join.table_name))
            fields = self.group_by + [agg.field for agg in self.aggregates] + [order.field for order in self.order_by]
            for field in fields:
                if not any(field in columns.get(table, set()) for table in tables):
                    raise ValueError(f"未知字段: {field}")
        return self


def parse_query_plan(raw: dict[str, Any]) -> QueryPlan:
    if not raw:
        raise ValueError("查询条件为空")

    payload = raw if ("query_type" in raw or "table_name" in raw or "primary_table" in raw) else raw.get("query_conditions", raw)
    if not isinstance(payload, dict):
        raise ValueError("查询条件格式无效")

    query_type = payload.get("query_type", "single")

    if query_type == "multi":
        primary = payload.get("primary_conditions") or {}
        return QueryPlan(
            query_type="multi",
            primary_table=payload.get("primary_table", TABLE_PRODUCT),
            primary_conditions=QueryPlan(
                query_type="single",
                table_name=payload.get("primary_table", TABLE_PRODUCT),
                field_names=primary.get("field_names", []),
                filter=primary.get("filter"),
                page_size=primary.get("page_size", payload.get("page_size", 100)),
            ),
            join_tables=payload.get("join_tables", []),
            page_size=payload.get("page_size", 100),
        )

    if query_type == "aggregate":
        default_table = payload.get("table_name") or payload.get("primary_table") or TABLE_ORDERS
        return QueryPlan(
            query_type="aggregate",
            table_name=default_table,
            primary_table=default_table,
            join_tables=payload.get("join_tables", []),
            group_by=payload.get("group_by", []),
            aggregates=payload.get("aggregates", []),
            filter=payload.get("filter"),
            order_by=payload.get("order_by", []),
            page_size=payload.get("page_size", 100),
        )

    nested = payload.get("query_conditions") or {}
    return QueryPlan(
        query_type="single",
        table_name=payload.get("table_name", TABLE_PRODUCT),
        field_names=payload.get("field_names") or nested.get("field_names", []),
        filter=payload.get("filter") or nested.get("filter"),
        order_by=payload.get("order_by", []),
        page_size=payload.get("page_size", 100),
    )
