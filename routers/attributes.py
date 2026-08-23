from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import Attribute
from schemas import AttributeCreate , AttributeRead, AttributeUpdate

router = APIRouter(
    prefix="/attributes",
    tags=["Attributes"]
)



# ✅ CREATE — إضافة خاصيه
@router.post("/", response_model=AttributeRead, status_code=201)
def create_attribute(attribute: AttributeCreate,                         
                 session: Session = Depends(get_session)
                 ):
    # تحقق من عدم تكرار الخاصيه
    existing = session.exec(select(Attribute).where
                             (Attribute.name == attribute.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="الخاصيه مسجل مسبقاً")
    
    db_attribute = Attribute.model_validate(attribute)
    session.add(db_attribute)
    session.commit()
    session.refresh(db_attribute)
    return db_attribute

# ✅ READ ALL — جلب كل الخواص
@router.get("/", response_model=List[AttributeRead])
def get_attributes(session: Session = Depends(get_session)):
    statement = select(Attribute)
    attribute = session.exec(statement).all()
    return attribute

# ✅ READ ONE — جلب خاصيه محدد
@router.get("/{attribute_id}", response_model=AttributeRead)
def get_attribute(attribute_id: int, 
             session: Session = Depends(get_session)):
    attribute = session.get(Attribute, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="attribute not founded")
    return attribute

# ✅ UPDATE — تعديل خاصيه
@router.put("/{attribute_id}", response_model=AttributeRead)
def update_attribute(
    attribute_id: int,
    attribute_data: AttributeUpdate,
    session: Session = Depends(get_session),
):
    db_attribute = session.get(Attribute, attribute_id)

    if not db_attribute:
        raise HTTPException(
            status_code=404,
            detail="attribute not found",
        )

    update_data = attribute_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing_attribute = session.exec(
            select(Attribute).where(
                Attribute.name == update_data["name"])
        ).first()

        if existing_attribute and existing_attribute.id != db_attribute.id:
            raise HTTPException(
                status_code=409,
                detail="attribute already exists",
            )

    db_attribute.sqlmodel_update(update_data)

    session.commit()
    session.refresh(db_attribute)

    return db_attribute

# ✅ DELETE — حذف خاصيه
@router.delete("/{attribute_id}")
def delete_attribute(attribute_id: int, session: Session = Depends(get_session)):
    attribute = session.get(Attribute, attribute_id)
    if not attribute:
        raise HTTPException(status_code=404, detail="غير موجود")
    
    session.delete(attribute)
    session.commit()
    return {"message": "تم الحذف بنجاح"}
