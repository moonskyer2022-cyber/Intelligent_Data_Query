from typing import Any, Optional

from pydantic import BaseModel, Field


class GlobalState(BaseModel):
    user_question: str = ""
    session_id: Optional[str] = None
    chat_history: list[dict[str, str]] = Field(default_factory=list)
    query_plan: Optional[dict[str, Any]] = None
    query_result: list[dict[str, Any]] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    chart_config: Optional[dict[str, Any]] = None
    chart_url: Optional[str] = None
    error_message: Optional[str] = None
    final_answer: str = ""


class GraphInput(BaseModel):
    user_question: str
    session_id: Optional[str] = None


class GraphOutput(BaseModel):
    final_answer: str
    chart_url: Optional[str] = None
    session_id: Optional[str] = None
    query_plan: Optional[dict[str, Any]] = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_ms: int = 0
    request_id: Optional[str] = None
    error_code: Optional[str] = None
    mode: str = "llm"
    data_source: str = "MySQL"
