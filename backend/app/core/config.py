import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"

load_dotenv(BACKEND_ROOT / ".env")


class Settings:
    def __init__(self) -> None:
        cors_origins = os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        )
        self.cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

        firebase_credentials_path = os.getenv(
            "FIREBASE_CREDENTIALS_PATH",
            str(REPO_ROOT / "firebase_key.json"),
        )
        firebase_credentials = Path(firebase_credentials_path)
        if not firebase_credentials.is_absolute():
            backend_relative = (BACKEND_ROOT / firebase_credentials).resolve()
            repo_relative = (REPO_ROOT / firebase_credentials).resolve()
            if backend_relative.exists():
                firebase_credentials = backend_relative
            else:
                firebase_credentials = repo_relative
        self.firebase_credentials_path = str(firebase_credentials)

        self.ai_provider = os.getenv("AI_PROVIDER", "ollama")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.ollama_coding_model = os.getenv("OLLAMA_CODING_MODEL", "deepseek-coder")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.redis_url = os.getenv("REDIS_URL", "")
        self.sentry_dsn = os.getenv("SENTRY_DSN", "")
        self.rate_limit_window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "86400"))
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
        self.environment = os.getenv("ENVIRONMENT", "development")


settings = Settings()
