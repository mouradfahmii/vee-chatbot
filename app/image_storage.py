from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from app.config import settings


def save_image(
    image_data: bytes,
    conversation_id: str,
    original_filename: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Save image to filesystem organized by conversation_id.
    
    Args:
        image_data: Image file bytes
        conversation_id: Conversation identifier for organizing images
        original_filename: Optional original filename to preserve extension
        
    Returns:
        Tuple of (relative_path, full_url)
        - relative_path: Path relative to uploads/images/ (e.g., "conv_id/filename.jpg")
        - full_url: Full URL for accessing the image (e.g., "https://chatbot.veeapp.online/images/conv_id/filename.jpg")
    """
    # Get upload directory from settings
    upload_dir = Path(settings.image_upload_dir)
    
    # Create conversation-specific directory
    conversation_dir = upload_dir / conversation_id
    conversation_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine file extension
    if original_filename:
        # Extract extension from original filename
        ext = Path(original_filename).suffix.lower()
        if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'  # Default to jpg if extension is missing or invalid
    else:
        ext = '.jpg'  # Default extension
    
    # Generate unique filename: timestamp_uuid.ext
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{timestamp}_{unique_id}{ext}"
    
    # Save image file
    image_path = conversation_dir / filename
    with open(image_path, "wb") as f:
        f.write(image_data)
    
    # Generate relative path (for internal use)
    relative_path = f"{conversation_id}/{filename}"
    
    # Generate full URL
    base_url = settings.image_base_url.rstrip("/")
    full_url = f"{base_url}/{relative_path}"
    
    return relative_path, full_url
