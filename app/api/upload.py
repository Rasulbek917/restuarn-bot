import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.utils.deps import require_role, require_staff_auth

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_staff_auth), Depends(require_role("ADMIN"))],
)
@router.post(
    "/",
    status_code=201,
    include_in_schema=False,
    dependencies=[Depends(require_staff_auth), Depends(require_role("ADMIN"))],
)
async def upload_image(image: UploadFile):
    if not image:
        raise HTTPException(400, "Fayl yuborilmadi")

    ext = os.path.splitext(image.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Faqat jpg/png/webp rasm fayllariga ruxsat")

    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "Fayl hajmi 5MB dan katta bo'lmasligi kerak")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/{filename}"}
