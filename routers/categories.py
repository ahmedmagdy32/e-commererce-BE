from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import Category
from schemas import CategoryCreate , CategoryRead, CategoryUpdate

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)



# ✅ CREATE — إضافة قاموس
@router.post("/", response_model=CategoryRead, status_code=201)
def create_category(category: CategoryCreate,                         
                 session: Session = Depends(get_session)
                 ):
    # تحقق من عدم تكرار القاموس
    existing = session.exec(select(Category).where
                             (Category.name == category.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="القاموس مسجل مسبقاً")
    
    db_category = Category.model_validate(category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

# ✅ READ ALL — جلب كل القواميس
@router.get("/", response_model=List[CategoryRead])
def get_categories(session: Session = Depends(get_session)):
    statement = select(Category)
    categories = session.exec(statement).all()
    return categories

# ✅ READ ONE — جلب مستخدم محدد
@router.get("/{categories_id}", response_model=CategoryRead)
def get_category(category_id: int, 
             session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="القاموس غير موجود")
    return category

# ✅ UPDATE — تعديل قاموس
@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    session: Session = Depends(get_session),
):
    db_category = session.get(Category, category_id)

    if not db_category:
        raise HTTPException(
            status_code=404,
            detail="category not found",
        )

    update_data = category_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing_category = session.exec(
            select(Category).where(
                Category.name == update_data["name"])
        ).first()

        if existing_category and existing_category.id != db_category.id:
            raise HTTPException(
                status_code=409,
                detail="category already exists",
            )

    db_category.sqlmodel_update(update_data)

    session.commit()
    session.refresh(db_category)

    return db_category

# ✅ DELETE — حذف قاموس
@router.delete("/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="غير موجود")
    
    session.delete(category)
    session.commit()
    return {"message": "تم الحذف بنجاح"}
