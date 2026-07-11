import asyncio
import logging
import time
import uuid
import secrets

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from graphs.graph import main_graph
from graphs.state import GraphInput, GraphOutput
from demo import DEMO_SCENARIOS
from auth import issue_token, validate_token
from session import session_store
from settings import API_KEY, APP_ENV, AUTH_ENABLED, AUTH_PASSWORD, AUTH_SECRET, AUTH_TOKEN_TTL_SECONDS, AUTH_USERNAME, CHART_OUTPUT_DIR, CORS_ORIGINS, DB_NAME, DB_USER, DEMO_MODE, LLM_API_KEY, PORT, PROJECT_ROOT, REQUEST_TIMEOUT_SECONDS
from storage.db_meta import check_database_health, load_examples, list_tables_for_ui

FRONTEND_DIR = PROJECT_ROOT / "frontend"
logger = logging.getLogger("intelligent_data_query")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="智能问数（Intelligent Data Query）", description="本地智能问数 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/charts", StaticFiles(directory=str(CHART_OUTPUT_DIR)), name="charts")
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_assets")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    protected_paths = {"/run", "/examples", "/tables", "/demo-scenarios"}
    api_key_ok = bool(API_KEY) and secrets.compare_digest(request.headers.get("X-API-Key", ""), API_KEY)
    bearer = request.headers.get("Authorization", "")
    token_ok = AUTH_ENABLED and bearer.startswith("Bearer ") and validate_token(bearer[7:], AUTH_SECRET)
    if (API_KEY or AUTH_ENABLED) and request.url.path in protected_paths and not (api_key_ok or token_ok):
        return JSONResponse(
            status_code=401,
            content={"detail": {"code": "UNAUTHORIZED", "message": "缺少有效的 X-API-Key。", "request_id": request_id}},
            headers={"X-Request-ID": request_id},
        )
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request failed request_id=%s path=%s", request_id, request.url.path)
        raise
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s elapsed_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/examples")
async def examples():
    return {"examples": load_examples()}


@app.get("/demo-scenarios")
async def demo_scenarios():
    return {"scenarios": DEMO_SCENARIOS}


class TokenRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/token")
async def auth_token(req: TokenRequest):
    token = issue_token(req.username, req.password, AUTH_USERNAME, AUTH_PASSWORD, AUTH_SECRET, AUTH_TOKEN_TTL_SECONDS)
    if not token:
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "用户名或密码错误。"})
    return {"access_token": token, "token_type": "bearer", "expires_in": AUTH_TOKEN_TTL_SECONDS}


@app.get("/tables")
async def tables():
    return {"tables": [{"label": a, "name": b} for a, b in list_tables_for_ui()]}


@app.post("/run", response_model=GraphOutput)
async def run_query(req: GraphInput, request: Request):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    started = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            main_graph.ainvoke(
                {
                    "user_question": req.user_question,
                    "session_id": req.session_id,
                    "chat_history": session_store.get_history(req.session_id),
                }
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        rows = result.get("rows", result.get("query_result", []))
        return GraphOutput(
            final_answer=result.get("final_answer", ""),
            chart_url=result.get("chart_url"),
            session_id=req.session_id,
            query_plan=result.get("query_plan"),
            rows=rows,
            row_count=len(rows),
            execution_ms=round((time.perf_counter() - started) * 1000),
            request_id=request_id,
            mode="demo" if DEMO_MODE else "llm",
            data_source=f"MySQL / {DB_NAME}",
        )
    except ValueError as e:
        logger.warning("query validation failed request_id=%s error=%s", request_id, e)
        raise HTTPException(
            status_code=400,
            detail={"code": "QUERY_VALIDATION_ERROR", "message": str(e), "request_id": request_id},
        )
    except asyncio.TimeoutError:
        logger.warning("query timed out request_id=%s", request_id)
        raise HTTPException(
            status_code=504,
            detail={"code": "QUERY_TIMEOUT", "message": "查询超时，请缩小查询范围后重试。", "request_id": request_id},
        )
    except Exception:
        logger.exception("query failed request_id=%s", request_id)
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": "服务暂时无法完成查询，请稍后重试。", "request_id": request_id},
        )


@app.get("/health")
async def health():
    database = check_database_health()
    if DEMO_MODE:
        llm = {"status": "demo", "message": "DEMO_MODE 已启用，使用固定本地查询计划"}
    else:
        llm = {
            "status": "ok" if LLM_API_KEY else "warning",
            "message": "LLM_API_KEY 已配置" if LLM_API_KEY else "未配置 LLM_API_KEY，/run 无法调用智能分析服务",
        }
    status = "ok" if database["status"] == "ok" and llm["status"] in {"ok", "demo"} else "warning"
    return {
        "status": status,
        "service": {"status": "ok"},
        "database": database,
        "llm": llm,
        "security": {"api_key_enabled": bool(API_KEY), "auth_enabled": AUTH_ENABLED, "least_privilege_db_user": DB_USER.lower() not in {"root", ""}},
    }


def start_server():
    import uvicorn

    options = {
        "host": "0.0.0.0",
        "port": PORT,
        "reload": APP_ENV == "development",
    }
    if APP_ENV == "development":
        options["reload_dirs"] = [str(PROJECT_ROOT / "src"), str(FRONTEND_DIR)]
    uvicorn.run("main:app", **options)

