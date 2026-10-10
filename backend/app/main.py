"""FastAPI application entry point for Sit Spot backend."""
import platform
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .api.routes_session import router as session_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure local data and recording storage directories exist
    settings.recordings_dir.mkdir(parents=True, exist_ok=True)
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local backend for Sit Spot nature listening companion. No external network requests.",
    lifespan=lifespan,
)

# Local CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint reporting system status and safety parameters."""
    model_path = settings.model_path
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "0.1.0",
        "environment": settings.environment,
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "limits": {
            "max_duration_seconds": settings.max_duration_seconds,
            "min_duration_seconds": settings.min_duration_seconds,
            "max_file_size_bytes": settings.max_file_size_bytes,
        },
        "local_model": {
            "configured_model": "Google YAMNet (ONNX)",
            "license": "Apache-2.0",
            "weights_present": model_path.exists(),
            "model_path": str(model_path),
        },
    }
