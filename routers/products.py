from fastapi import Depends, HTTPException, APIRouter , Query
from sqlmodel import Session, select,func
from typing import List
from database import get_session
from models import Product , ProductAttribute, User
from schemas import ProductCreate , ProductRead , ProductUpdate ,ProductPagination
from routers.auth import require_admin
import math

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ✅ CREATE — إضافة منتج
@router.post("/", response_model=ProductRead, status_code=201)
def create_product(product_data: ProductCreate,                         
                 session: Session = Depends(get_session)
                 ):
    # تحقق من عدم تكرار المنتج
    existing = session.exec(select(Product).where
                             (Product.name == product_data.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="المنتج مسجل مسبقاً")
    
    product = Product(
        name=product_data.name,
        price=product_data.price,
        warranty=product_data.warranty,
        in_stock=product_data.in_stock,
        discount=product_data.discount,
        category_id=product_data.category_id
    )

    # 2. حفظ المنتج للحصول على id
    session.add(product)
    session.flush()
    
    # 3. إنشاء خصائص المنتج
    for attribute in product_data.attributes:
        product_attribute = ProductAttribute(
            product_id=product.id,
            attribute_id=attribute.attribute_id,
            value=attribute.value
        )

        session.add(product_attribute)

    # 4. حفظ جميع الخصائص
    session.commit()
    session.refresh(product)
    return product

# ✅ READ ALL — جلب كل المنتجات
@router.get("/", response_model=ProductPagination)
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category_id: int | None = None,
    search: str | None = None,
    session: Session = Depends(get_session),
):
    offset = (page - 1) * limit

    # Count
    count_statement = select(func.count()).select_from(Product)

    if category_id is not None:
        count_statement = count_statement.where(
            Product.category_id == category_id
        )

    if search is not None:
        count_statement = count_statement.where(
            Product.name.contains(search)
        )

    total = session.exec(count_statement).one()

    pages = math.ceil(total / limit)

    if page > pages and total > 0:
        raise HTTPException(
            status_code=404,
            detail="Page not found",
        )

    # Products
    statement = select(Product)

    if category_id is not None:
        statement = statement.where(
            Product.category_id == category_id
        )

    if search is not None:
        statement = statement.where(
            Product.name.contains(search)
        )

    statement = statement.offset(offset).limit(limit)

    products = session.exec(statement).all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


# ✅ READ ONE — جلب منتج محدد
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, 
             session: Session = Depends(get_session)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="المنتج غير موجود")
    return product

# ✅ UPDATE — تعديل منتج
@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    # البحث عن المنتج
    db_product = session.get(Product, product_id)

    if not db_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # استخراج البيانات المرسلة فقط
    update_data = product_data.model_dump(exclude_unset=True)

    # استخراج attributes بشكل منفصل
    attributes_data = update_data.pop("attributes", None)

    # التحقق من عدم تكرار الاسم
    if "name" in update_data:
        existing_product = session.exec(
            select(Product).where(
                Product.name == update_data["name"]
            )
        ).first()

        if existing_product and existing_product.id != db_product.id:
            raise HTTPException(
                status_code=409,
                detail="Product already exists"
            )

    # تحديث بيانات Product
    db_product.sqlmodel_update(update_data)

    # إذا أرسل المستخدم attributes
    if attributes_data is not None:

        # حذف الخصائص القديمة
        old_attributes = session.exec(
            select(ProductAttribute).where(
                ProductAttribute.product_id == product_id
            )
        ).all()

        for old_attribute in old_attributes:
            session.delete(old_attribute)

        # إضافة الخصائص الجديدة
        for attribute in attributes_data:
            new_attribute = ProductAttribute(
                product_id=product_id,
                attribute_id=attribute["attribute_id"],
                value=attribute["value"]
            )

            session.add(new_attribute)

    # حفظ كل شيء
    session.commit()
    session.refresh(db_product)

    return db_product
# ✅ DELETE — حذف منتج
@router.delete("/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_session),current_user: User = Depends(require_admin)):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="غير موجود")
    
    session.delete(product)
    session.commit()
    return {"message": "تم الحذف بنجاح"}
