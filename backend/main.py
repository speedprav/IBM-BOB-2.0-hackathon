"""
DevTwin FastAPI application entry point.
"""
import os
from pathlib import Path

# Load .env.example if present (user may paste key there), then .env
_here = Path(__file__).parent
for _env_file in (_here / ".env", _here / ".env.example"):
    if _env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_env_file, override=False)
        except ImportError:
            # Manual parse fallback
            for line in _env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v
        break

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import router

app = FastAPI(
    title="DevTwin API",
    description="Pre-merge software change simulator",
    version="1.0.0",
)

# Allow localhost for dev + any Vercel deployment URL for production.
# ALLOWED_ORIGINS env var can be a comma-separated list of extra origins.
_extra = os.getenv("ALLOWED_ORIGINS", "")
_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if _extra:
    _origins += [o.strip() for o in _extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel preview URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "devtwin"}
