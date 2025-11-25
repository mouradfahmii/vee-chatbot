from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image


def encode_image_to_base64(image_path: str | Path | bytes | Image.Image) -> str:
    """Encode an image to base64 string for API usage."""
    if isinstance(image_path, Image.Image):
        img = image_path
    elif isinstance(image_path, bytes):
        img = Image.open(BytesIO(image_path))
    else:
        img = Image.open(image_path)
    
    # Convert to RGB if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Resize if too large (max 2048x2048 for API efficiency)
    max_size = 2048
    if img.width > max_size or img.height > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    img_bytes = buffer.getvalue()
    
    return base64.b64encode(img_bytes).decode("utf-8")


def create_vision_message(image_base64: str, question: str) -> dict:
    """Create a message dict for vision API with image and text."""
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": question,
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}",
                },
            },
        ],
    }

