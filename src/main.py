import asyncio
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from graphs.graph import main_graph
from graphs.state import GraphInput, GraphOutput
from session import session_store
from settings import API_KEY, CHART_OUTPUT_DIR, CORS_ORIGINS, LLM_API_KEY, PORT, PROJECT_ROOT, REQUEST_TIMEOUT_SECONDS
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
    protected_paths = {"/run", "/examples", "/tables"}
    if API_KEY and request.url.path in protected_paths and request.headers.get("X-API-Key") != API_KEY:
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
        return GraphOutput(
            final_answer=result.get("final_answer", ""),
            chart_url=result.get("chart_url"),
            session_id=req.session_id,
            query_plan=result.get("query_plan"),
            rows=result.get("rows", result.get("query_result", [])),
            execution_ms=round((time.perf_counter() - started) * 1000),
            request_id=request_id,
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
    llm = {
        "status": "ok" if LLM_API_KEY else "warning",
        "message": "LLM_API_KEY 已配置" if LLM_API_KEY else "未配置 LLM_API_KEY，/run 无法调用智能分析服务",
    }
    status = "ok" if database["status"] == "ok" and llm["status"] == "ok" else "warning"
    return {"status": status, "service": {"status": "ok"}, "database": database, "llm": llm, "security": {"api_key_enabled": bool(API_KEY)}}


def start_server():
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "src"), str(FRONTEND_DIR)],
    )

