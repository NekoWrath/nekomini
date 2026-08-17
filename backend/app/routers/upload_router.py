import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/upload", tags=["Upload"])

UPLOAD_DIR = Path(__file__).parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Uploads an image file from the user's device and returns static access URL."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла. Разрешены только: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Размер файла превышает 10 МБ")

    # Generate unique filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    target_path = UPLOAD_DIR / unique_name

    with open(target_path, "wb") as f:
        f.write(content)

    return {
        "success": True,
        "filename": unique_name,
        "url": f"/static/uploads/{unique_name}"
    }
