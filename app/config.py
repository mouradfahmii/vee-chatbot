from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Disable Chroma telemetry to avoid PostHog capture signature errors during CLI/API runs.
os.environ.setdefault("POSTHOG_DISABLE", "1")
os.environ.setdefault("CHROMA_TELEMETRY_ANONYMIZED", "False")

# Suppress Pydantic serialization warnings from LiteLLM
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


class Settings(BaseModel):
    """Central configuration for the food chatbot."""

    data_file: Path = Field(
        default=Path(__file__).resolve().parents[1]
        / "data"
        / "synthetic_food_chatbot_data.json",
        description="Path to the synthetic knowledge base JSON.",
    )
    chroma_path: Path = Field(
        default=Path(__file__).resolve().parents[1] / "chromadb_store",
        description="Location for the persistent Chroma database.",
    )
    collection_name: str = Field(
        default="food_recipes_chatbot",
        description="Chroma collection identifier.",
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="SentenceTransformer model for embeddings.",
    )
    llm_model: str = Field(
        default=os.getenv("FOOD_BOT_LLM_MODEL", "openai/gpt-4o-mini"),
        description="Model name understood by LiteLLM (provider/model).",
    )
    vision_model: str = Field(
        default=os.getenv("FOOD_BOT_VISION_MODEL", "openai/gpt-4o"),
        description="Vision model for image analysis (should support vision).",
    )
    llm_api_base: Optional[str] = Field(
        default=os.getenv("FOOD_BOT_LLM_API_BASE"),
        description="Optional override for custom inference endpoints.",
    )
    llm_api_key: Optional[str] = Field(
        default=os.getenv("FOOD_BOT_LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        description="API key picked up automatically from env vars if set.",
    )
    max_context_documents: int = Field(
        default=6,
        description="Number of documents retrieved per question.",
    )
    temperature: float = Field(
        default=float(os.getenv("FOOD_BOT_TEMPERATURE", "0.5")),
        description="Sampling temperature passed to the language model. Higher values (0.5-0.7) create more varied responses.",
    )
    # Timeout configuration
    llm_timeout_seconds: int = Field(
        default=int(os.getenv("FOOD_BOT_LLM_TIMEOUT", "60")),
        description="Timeout in seconds for LLM API calls (text chat). Default: 60 seconds.",
    )
    vision_timeout_seconds: int = Field(
        default=int(os.getenv("FOOD_BOT_VISION_TIMEOUT", "90")),
        description="Timeout in seconds for vision model API calls (image analysis). Default: 90 seconds.",
    )
    # AWS S3 logging configuration
    aws_s3_bucket: Optional[str] = Field(
        default=os.getenv("AWS_S3_LOG_BUCKET"),
        description="S3 bucket name for storing logs. If not set, logs are only stored locally.",
    )
    aws_s3_prefix: str = Field(
        default=os.getenv("AWS_S3_LOG_PREFIX", "vee-chatbot/logs/"),
        description="S3 prefix/path for log files.",
    )
    aws_region: Optional[str] = Field(
        default=os.getenv("AWS_REGION", "us-east-1"),
        description="AWS region for S3 operations.",
    )
    # MySQL ingestion configuration
    ingest_mysql_on_startup: bool = Field(
        default=os.getenv("INGEST_MYSQL_ON_STARTUP", "false").lower() == "true",
        description="If True, ingest MySQL data on application startup.",
    )
    # Voice/TTS configuration
    tts_model: str = Field(
        default=os.getenv("FOOD_BOT_TTS_MODEL", "tts-1"),
        description="OpenAI TTS model to use (tts-1 or tts-1-hd).",
    )
    tts_voice: str = Field(
        default=os.getenv("FOOD_BOT_TTS_VOICE", "alloy"),
        description="TTS voice to use. Options: alloy, echo, fable, onyx, nova, shimmer. For Arabic, nova or alloy work well.",
    )
    max_audio_size_mb: int = Field(
        default=int(os.getenv("FOOD_BOT_MAX_AUDIO_SIZE_MB", "25")),
        description="Maximum audio file size in MB (OpenAI Whisper limit is 25MB).",
    )
    # Image optimization configuration
    image_max_size: int = Field(
        default=int(os.getenv("FOOD_BOT_IMAGE_MAX_SIZE", "1024")),
        description="Maximum image dimension (width or height) in pixels. Images larger than this will be resized. Default: 1024 (aggressive optimization for faster processing).",
    )
    image_quality: int = Field(
        default=int(os.getenv("FOOD_BOT_IMAGE_QUALITY", "75")),
        description="JPEG quality for image compression (1-100). Lower values reduce file size and processing time. Default: 75 (aggressive optimization).",
    )
    skip_image_validation: bool = Field(
        default=os.getenv("FOOD_BOT_SKIP_IMAGE_VALIDATION", "false").lower() == "true",
        description="If True, skip separate validation step and combine validation with analysis (faster, but may process non-food images). Default: False.",
    )
    image_validation_model: str = Field(
        default=os.getenv("FOOD_BOT_IMAGE_VALIDATION_MODEL", "openai/gpt-4o-mini"),
        description="Model to use for image validation (if separate validation is enabled). Use faster/cheaper model for validation. Default: gpt-4o-mini.",
    )
    # Image storage configuration
    image_upload_dir: Path = Field(
        default=Path(__file__).resolve().parents[1] / "uploads" / "images",
        description="Directory for storing uploaded images. Organized by conversation_id.",
    )
    image_base_url: str = Field(
        default=os.getenv("IMAGE_BASE_URL", "https://chatbot.veeapp.online/images"),
        description="Base URL for serving uploaded images. Used to generate full image URLs in history.",
    )


settings = Settings()
