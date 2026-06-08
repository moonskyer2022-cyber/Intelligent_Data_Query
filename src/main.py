from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from graphs.graph import main_graph
from graphs.state import GraphInput, GraphOutput
from session import session_store
from settings import CHART_OUTPUT_DIR, PORT, PROJECT_ROOT
from storage.db_meta import load_examples, list_tables_for_ui

FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="AIQuery", description="本地智能问数 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/charts", StaticFiles(directory=str(CHART_OUTPUT_DIR)), name="charts")
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend_assets")


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
async def run_query(req: GraphInput):
    try:
        result = await main_graph.ainvoke(
            {
                "user_question": req.user_question,
                "session_id": req.session_id,
                "chat_history": session_store.get_history(req.session_id),
            }
        )
        return GraphOutput(
            final_answer=result.get("final_answer", ""),
            chart_url=result.get("chart_url"),
            session_id=req.session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


def start_server():
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        reload_dirs=[str(PROJECT_ROOT / "src"), str(FRONTEND_DIR)],
    )
