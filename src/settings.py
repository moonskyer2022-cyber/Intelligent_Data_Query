from pathlib import Path
import os

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CONFIG_DIR = PROJECT_ROOT / "config"
CHART_OUTPUT_DIR = Path(os.getenv("CHART_OUTPUT_DIR", PROJECT_ROOT / "output" / "charts"))

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ai_query")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes", "on"}
API_KEY = os.getenv("API_KEY", "")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "demo")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "change-me")
AUTH_SECRET = os.getenv("AUTH_SECRET", "change-me-in-production")
AUTH_TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "3600"))
CORS_ORIGINS = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",") if item.strip()]
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "3"))
DB_READ_TIMEOUT = int(os.getenv("DB_READ_TIMEOUT", "20"))
DB_WRITE_TIMEOUT = int(os.getenv("DB_WRITE_TIMEOUT", "20"))
PORT = int(os.getenv("PORT", "8000"))
APP_ENV = os.getenv("APP_ENV", "demo").lower()
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", "1000"))
SESSION_BACKEND = os.getenv("SESSION_BACKEND", "memory").lower()
QUERY_MAX_ROWS = int(os.getenv("QUERY_MAX_ROWS", "500"))
SENSITIVE_FIELDS = {item.strip().lower() for item in os.getenv("SENSITIVE_FIELDS", "password,phone,email,id_card,token").split(",") if item.strip()}
LLM_MAX_RESPONSE_CHARS = int(os.getenv("LLM_MAX_RESPONSE_CHARS", "20000"))
CHART_RETENTION_SECONDS = int(os.getenv("CHART_RETENTION_SECONDS", "86400"))
CHART_MAX_FILES = int(os.getenv("CHART_MAX_FILES", "200"))

CHART_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
