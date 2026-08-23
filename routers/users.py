from fastapi import Depends, HTTPException, APIRouter
from sqlmodel import Session, select
from typing import List
from database import get_session
from models import User
from schemas import UserCreate , UserRead, UserUpdate, PasswordUpdate , RoleUpdate
from fastapi.security import OAuth2PasswordRequestForm
from routers.auth import get_current_user ,  verify_password , hash_password, create_access_token ,require_admin
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)



@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "You are an admin",
        "user": current_user.name
    }



# ✅ CREATE — إضافة مستخدم
@router.post("/", response_model=UserRead, status_code=201)
def create_user(user: UserCreate,                         
                 session: Session = Depends(get_session)
                 ):
    # تحقق من عدم تكرار الإيميل
    existing = session.exec(select(User).where
                             (User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="الإيميل مسجل مسبقاً")
    
    db_user = User(
        name=user.name,
        email=user.email,
        age=user.age,
        hashed_password=hash_password(user.password),
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# ✅ READ ALL — جلب كل المستخدمين
@router.get("/", response_model=List[UserRead])
def get_users(session: Session = Depends(get_session)):
    statement = select(User)
    users = session.exec(statement).all()
    return users

# ✅ READ ONE — جلب مستخدم محدد
@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, 
             session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return user

# ✅ UPDATE — تعديل مستخدم
@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    db_user = session.get(User, user_id)

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if current_user.role != "admin" and current_user.id != db_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own account",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing_user = session.exec(
            select(User).where(
                User.email == update_data["email"])
        ).first()

        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=409,
                detail="Email already exists",
            )

    db_user.sqlmodel_update(update_data)

    session.commit()
    session.refresh(db_user)

    return db_user

# ✅ DELETE — حذف مستخدم
@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="غير موجود")
    
    session.delete(user)
    session.commit()
    return {"message": "تم الحذف بنجاح"}



@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    db_user = session.exec(
    select(User).where(User.email == form_data.username)
    ).first()


    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
    )

    if not verify_password(
    form_data.password,
    db_user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
    data={"sub": str(db_user.id)}
    )

    return {
    "access_token": access_token,
    "token_type": "bearer",
}


@router.put("/me/password")
def change_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not verify_password(
        password_data.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(
        password_data.new_password
    )

    session.commit()

    return {"message": "Password updated successfully"}


@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if role_data.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    user.role = role_data.role

    session.commit()
    session.refresh(user)

    return {
        "message": "User role updated successfully",
        "role": user.role,
    }

