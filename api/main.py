from __future__ import annotations

import html
import re

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from app.chatbot import bot
from app.ingest import ingest_dataset
from app.mysql_ingestor import ingest_mysql
from api.auth import verify_api_key
from api.schemas import ChatRequest, ChatResponse, ImageChatRequest

app = FastAPI(title="Vee Food Chatbot", version="0.1.0")


@app.on_event("startup")
async def ensure_chroma_seeded() -> None:
    """Load knowledge base on startup."""
    from app.config import settings
    
    try:
        # Always load JSON data if available
        ingest_dataset(reset=False)
    except FileNotFoundError:
        # JSON file is optional if MySQL is used
        pass
    
    # Optionally load MySQL data on startup
    if settings.ingest_mysql_on_startup:
        try:
            ingest_mysql(reset=False)
        except Exception as e:
            # Log but don't fail startup if MySQL ingestion fails
            import logging
            logging.warning(f"MySQL ingestion on startup failed: {e}")


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key),
) -> ChatResponse:
    """Chat endpoint - requires API key authentication."""
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        answer = bot.answer(payload.message, history=payload.history, user_id=payload.user_id)
    except Exception as exc:  # pragma: no cover - propagate LLM errors with context
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ChatResponse(answer=answer)


@app.post(
    "/chat/html",
    response_class=HTMLResponse,
    responses={200: {"content": {"text/html": {}}}},
)
async def chat_html_endpoint(
    payload: ChatRequest,
    api_key: str = Depends(verify_api_key),
) -> HTMLResponse:
    """
    Chat endpoint that returns HTML instead of JSON.
    Converts Markdown headers (#, ##, ###) and formatting (*, **) to HTML.
    """
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        answer = bot.answer(payload.message, history=payload.history, user_id=payload.user_id)
    except Exception as exc:  # pragma: no cover - propagate LLM errors with context
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Convert Markdown headers to HTML
    # ### Header -> <h3>Header</h3>
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', answer, flags=re.MULTILINE)
    # ## Header -> <h2>Header</h2>
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    # # Header -> <h1>Header</h1>
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    
    # Convert bold (**text**)
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
    
    # Convert italic (*text*)
    html_content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', html_content)
    
    # Escape HTML and convert newlines
    safe_html = html.escape(html_content).replace("\n", "<br>")
    
    # Unescape our HTML tags
    safe_html = safe_html.replace("&lt;h1&gt;", "<h1>").replace("&lt;/h1&gt;", "</h1>")
    safe_html = safe_html.replace("&lt;h2&gt;", "<h2>").replace("&lt;/h2&gt;", "</h2>")
    safe_html = safe_html.replace("&lt;h3&gt;", "<h3>").replace("&lt;/h3&gt;", "</h3>")
    safe_html = safe_html.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
    safe_html = safe_html.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
    
    return HTMLResponse(content=f"<div>{safe_html}</div>")


@app.post("/chat/image", response_model=ChatResponse)
async def chat_image_endpoint(
    image: UploadFile = File(..., description="Food image to analyze"),
    question: str = "What is in this image? Estimate the calories.",
    user_id: str | None = None,
    api_key: str = Depends(verify_api_key),
) -> ChatResponse:
    """Analyze a food image and answer questions about it - requires API key authentication."""
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Analyze image
        answer = bot.answer_with_image(image_data, question=question, user_id=user_id)
        return ChatResponse(answer=answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
async def reingest(
    reset: bool = True,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Reingest the knowledge base from JSON file - requires API key authentication (admin endpoint)."""
    count = ingest_dataset(reset=reset)
    return {"documents": count, "reset": reset, "source": "json"}


@app.post("/ingest/mysql")
async def reingest_mysql(
    reset: bool = False,
    tables: str | None = None,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """
    Ingest MySQL database into knowledge base - requires API key authentication (admin endpoint).
    
    Args:
        reset: If True, reset the vector store before adding MySQL data
        tables: Comma-separated list of table names to ingest. If None, ingests all tables.
    """
    table_list = [t.strip() for t in tables.split(",")] if tables else None
    count = ingest_mysql(reset=reset, table_names=table_list)
    return {
        "documents": count,
        "reset": reset,
        "source": "mysql",
        "tables": table_list or "all"
    }
