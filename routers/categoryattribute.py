from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import CategoryAttribute
from schemas import CategoryAttributeCreate , CategoryAttributeRead

router = APIRouter(
    prefix="/category-attribute",
    tags=["CategoryAttributes"]
)



# ✅ CREATE — إضافة مستخدم
@router.post("/", response_model=CategoryAttributeRead, status_code=201)
def create_categoryattribute(category_attribute: CategoryAttributeCreate,                         
                 session: Session = Depends(get_session)
                 ):
    
    
    
    db_category_attribute = CategoryAttribute.model_validate(category_attribute)
    session.add(db_category_attribute)
    session.commit()
    session.refresh(db_category_attribute)
    return db_category_attribute

# ✅ READ ALL — جلب كل المستخدمين
@router.get("/", response_model=List[CategoryAttributeRead])
def get_categoryattributes(session: Session = Depends(get_session)):
    statement = select(CategoryAttribute)
    category_attributes = session.exec(statement).all()
    return category_attributes



# ✅ DELETE — حذف مستخدم
@router.delete("/{categoryattribute_id}")
def delete_user(categoryattribute_id: int, session: Session = Depends(get_session)):
    category_attribute = session.get(CategoryAttribute, categoryattribute_id)
    if not category_attribute:
        raise HTTPException(status_code=404, detail="غير موجود")
    
    session.delete(category_attribute)
    session.commit()
    return {"message": "تم الحذف بنجاح"}
