from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


# =========================
# User Schemas
# =========================

class UserCreate(SQLModel):
    name: str
    email: str
    password: str
    age: Optional[int] = None


class UserRead(SQLModel):
    id: int
    name: str
    email: str
    age: Optional[int]
    is_active: bool
    created_at: datetime
    role : str


class UserUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None


class UserLogin(SQLModel):
    email: str
    password: str


# =========================
# Category Schemas
# =========================

class CategoryCreate(SQLModel):
    name: str


class CategoryRead(SQLModel):
    id: int
    name: str


class CategoryUpdate(SQLModel):
    name: Optional[str] = None


# =========================
# Attribute Schemas
# =========================

class AttributeCreate(SQLModel):
    name: str


class AttributeRead(SQLModel):
    id: int
    name: str


class AttributeUpdate(SQLModel):
    name: Optional[str] = None


# =========================
# CategoryAttribute Schemas
# =========================

class CategoryAttributeCreate(SQLModel):
    category_id: int
    attribute_id: int


class CategoryAttributeRead(SQLModel):
    id: int
    category_id: int
    attribute_id: int




# =========================
# Product Schemas
# =========================

# =========================
# ProductAttribute Input
# يستخدم عند إنشاء Product
# =========================
class ProductAttributeInput(SQLModel):
    attribute_id: int
    value: str



class ProductCreate(SQLModel):
    name: str
    price: Decimal
    warranty: Optional[int] = None
    in_stock: int = 0
    discount: float = 0.0
    category_id: int

    attributes: list[ProductAttributeInput]


class ProductRead(SQLModel):
    id: int
    name: str
    price: Decimal
    warranty: Optional[int]
    in_stock: int
    discount: float
    category_id: int


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    warranty: Optional[int] = None
    in_stock: Optional[int] = None
    discount: Optional[float] = None

    category_id: Optional[int] = None
    attributes: list[ProductAttributeInput] | None = None

# =========================
# ProductAttribute Schemas
# =========================

class ProductAttributeCreate(SQLModel):
    product_id: int
    attribute_id: int
    value: str


class ProductAttributeRead(SQLModel):
    id: int
    product_id: int
    attribute_id: int
    value: str


class ProductAttributeUpdate(SQLModel):
    value: str



class PasswordUpdate(SQLModel):
    current_password: str
    new_password: str


class RoleUpdate(SQLModel):
    role: str


class ProductPagination(SQLModel):
    items: list[ProductRead]
    total: int
    page: int
    limit: int
    pages: int


#cart schemas
class CartItemCreate(SQLModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(SQLModel):
    quantity: int = Field(ge=1)


class CartItemDetail(SQLModel):
    id: int
    product_id: int
    name: str
    price: Decimal
    quantity: int
    subtotal: Decimal

class CartItemRead(SQLModel):
    id: int
    product_id: int
    quantity: int


class CartRead(SQLModel):
    items: list[CartItemDetail]
    total: Decimal


class OrderItemRead(SQLModel):
    id: int
    product_id: int
    quantity: int
    price: Decimal


class OrderRead(SQLModel):
    id: int
    user_id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemRead]


class PaymentRead(SQLModel):
    id: int
    order_id: int
    amount: Decimal
    status: str
    payment_method: str
    transaction_id: str | None
    created_at: datetime


class PaymentCreate(SQLModel):
    payment_method: str



class ProductImageRead(SQLModel):
    id: int
    product_id: int
    url: str
    public_id: str
    image_type: str
    sort_order: int


class ProductImageCreate(SQLModel):
    image_type: str
    sort_order: int = 0

