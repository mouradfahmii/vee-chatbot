from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# Disable Chroma telemetry to avoid PostHog capture signature errors during CLI/API runs.
os.environ.setdefault("POSTHOG_DISABLE", "1")
os.environ.setdefault("CHROMA_TELEMETRY_ANONYMIZED", "False")


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
        default=0.2,
        description="Sampling temperature passed to the language model.",
    )


settings = Settings()
