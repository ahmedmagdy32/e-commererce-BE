import cloudinary.uploader

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlmodel import Session, select
from database import get_session
from models import Product, ProductImage
from schemas import ProductImageRead
from routers.auth import get_current_user


router = APIRouter(
    prefix="/products",
    tags=["Product Images"]
)



@router.post(
    "/{product_id}/images",
    response_model=ProductImageRead,
    status_code=201
)
async def upload_product_image(
    product_id: int,

    image_type: str,
    image: UploadFile = File(...),

    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 1. التأكد من وجود المنتج
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 2. السماح فقط بالأنواع الأربعة
    allowed_types = {
        "front",
        "back",
        "left",
        "right"
    }

    if image_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid image type"
        )

    # 3. منع وجود صورتين من نفس النوع
    existing_image = session.exec(
        select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.image_type == image_type
        )
    ).first()

    if existing_image:
        raise HTTPException(
            status_code=409,
            detail=f"{image_type} image already exists"
        )

    # 4. التأكد أن الملف صورة
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # 5. رفع الصورة إلى Cloudinary
    try:
        result = cloudinary.uploader.upload(
            image.file,
            folder=f"market/products/{product_id}"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload image"
        )

    # 6. حفظ بيانات الصورة في PostgreSQL
    product_image = ProductImage(
        product_id=product_id,
        url=result["secure_url"],
        public_id=result["public_id"],
        image_type=image_type,
    )

    session.add(product_image)
    session.commit()
    session.refresh(product_image)

    return product_image


@router.get(
    "/{product_id}/images",
    response_model=list[ProductImageRead]
)
def get_product_images(
    product_id: int,
    session: Session = Depends(get_session),
):
    # التأكد من وجود المنتج
    product = session.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # جلب صور المنتج
    images = session.exec(
        select(ProductImage)
        .where(ProductImage.product_id == product_id)
        .order_by(ProductImage.sort_order)
    ).all()

    return images


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=204
)
def delete_product_image(
    product_id: int,
    image_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 1. البحث عن الصورة والتأكد أنها تخص المنتج
    image = session.exec(
        select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id
        )
    ).first()

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    # 2. حذف الصورة من Cloudinary
    try:
        result = cloudinary.uploader.destroy(
            image.public_id
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete image from Cloudinary"
        )

    # 3. التأكد من نجاح الحذف في Cloudinary
    if result.get("result") not in ("ok", "not found"):
        raise HTTPException(
            status_code=500,
            detail="Cloudinary failed to delete image"
        )

    # 4. حذف سجل الصورة من PostgreSQL
    session.delete(image)
    session.commit()

    return None


@router.put(
    "/{product_id}/images/{image_id}",
    response_model=ProductImageRead
)
async def update_product_image(
    product_id: int,
    image_id: int,
    image: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    # 1. البحث عن الصورة
    product_image = session.exec(
        select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id
        )
    ).first()

    if not product_image:
        raise HTTPException(
            status_code=404,
            detail="Image not found"
        )

    # 2. التأكد أن الملف صورة
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # 3. حذف الصورة القديمة من Cloudinary
    try:
        delete_result = cloudinary.uploader.destroy(
            product_image.public_id
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete old image"
        )

    if delete_result.get("result") not in ("ok", "not found"):
        raise HTTPException(
            status_code=500,
            detail="Cloudinary failed to delete old image"
        )

    # 4. رفع الصورة الجديدة
    try:
        upload_result = cloudinary.uploader.upload(
            image.file,
            folder=f"market/products/{product_id}"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload new image"
        )

    # 5. تحديث بيانات الصورة
    product_image.url = upload_result["secure_url"]
    product_image.public_id = upload_result["public_id"]

    session.add(product_image)
    session.commit()
    session.refresh(product_image)

    return product_image