"""Application configuration with strict privacy and security limits."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sit Spot"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000

    # Local storage paths
    data_dir: Path = Path("./data")
    recordings_dir: Path = Path("./data/recordings")
    models_dir: Path = Path("./models")

    # Safety bounds for audio recordings
    max_duration_seconds: float = 300.0  # 5 minutes maximum
    min_duration_seconds: float = 1.0    # 1 second minimum
    max_file_size_bytes: int = 25 * 1024 * 1024  # 25 MB cap

    # Supported audio input formats
    allowed_mime_types: list[str] = [
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/ogg",
        "audio/mpeg",
        "audio/mp4",
        "audio/aac",
    ]

    # CORS origins (strictly local)
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_prefix="SITSPOT_")

    @property
    def model_path(self) -> Path:
        p = self.models_dir / "yamnet.onnx"
        if not p.exists() and (Path("../models/yamnet.onnx")).exists():
            return Path("../models/yamnet.onnx").resolve()
        return p.resolve()

    @property
    def class_map_path(self) -> Path:
        p = self.models_dir / "yamnet_class_map.csv"
        if not p.exists() and (Path("../models/yamnet_class_map.csv")).exists():
            return Path("../models/yamnet_class_map.csv").resolve()
        return p.resolve()


settings = Settings()
