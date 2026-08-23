import cloudinary.uploader

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(
    prefix="/media",
    tags=["Media"]
)


@router.post("/upload")
async def upload_image(
    image: UploadFile = File(...)
):
    # التأكد من أن الملف صورة
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    try:
        result = cloudinary.uploader.upload(
            image.file,
            folder="market/products"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload image"
        )

    return {
        "url": result["secure_url"],
        "public_id": result["public_id"]
    }