from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Numeric, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


# =========================
# User
# =========================

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: str = Field(
        unique=True,
        index=True,
        max_length=255
    )

    hashed_password: str = Field(
        max_length=255
    )

    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=150
    )

    is_active: bool = Field(
        default=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    role : str = Field(default = "user")


# =========================
# Category
# =========================

class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    name: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=100
    )

    category_attributes: list["CategoryAttribute"] = Relationship(
        back_populates="category"
    )

    products: list["Product"] = Relationship(
        back_populates="category"
    )


# =========================
# Attribute
# =========================

class Attribute(SQLModel, table=True):
    __tablename__ = "attributes"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    name: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=100
    )

    category_attributes: list["CategoryAttribute"] = Relationship(
        back_populates="attribute"
    )

    product_attributes: list["ProductAttribute"] = Relationship(
        back_populates="attribute"
    )


# =========================
# CategoryAttribute
# =========================

class CategoryAttribute(SQLModel, table=True):
    __tablename__ = "category_attributes"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "attribute_id",
            name="uq_category_attribute"
        ),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    category_id: int = Field(
        foreign_key="categories.id",
        nullable=False,
        index=True
    )

    attribute_id: int = Field(
        foreign_key="attributes.id",
        nullable=False,
        index=True
    )

    category: "Category" = Relationship(
        back_populates="category_attributes"
    )

    attribute: "Attribute" = Relationship(
        back_populates="category_attributes"
    )


# =========================
# Product
# =========================

class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    name: str = Field(
        index=True,
        min_length=2,
        max_length=200
    )

    price: Decimal = Field(
        sa_column=Column(
            Numeric(10, 2),
            nullable=False
        )
    )

    warranty: Optional[int] = Field(
        default=None,
        ge=0,
        le=120
    )

    views: int = Field(
        default=0,
        ge=0
    )

    in_stock: int = Field(
        default=0,
        ge=0
    )

    discount: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0
    )

    category_id: int = Field(
        foreign_key="categories.id",
        nullable=False,
        index=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    category: "Category" = Relationship(
        back_populates="products"
    )

    product_attributes: list["ProductAttribute"] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True
        }
    )


# =========================
# ProductAttribute
# =========================

class ProductAttribute(SQLModel, table=True):
    __tablename__ = "product_attributes"

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "attribute_id",
            name="uq_product_attribute"
        ),
    )

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    product_id: int = Field(
        foreign_key="products.id",
        nullable=False,
        index=True,
        ondelete="CASCADE"
    )

    attribute_id: int = Field(
        foreign_key="attributes.id",
        nullable=False,
        index=True
    )

    value: str = Field(
        min_length=1,
        max_length=500
    )

    product: "Product" = Relationship(
        back_populates="product_attributes"
    )

    attribute: "Attribute" = Relationship(
        back_populates="product_attributes"
    )



#cart

class Cart(SQLModel, table=True):
    __tablename__ = "carts"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        unique=True,
        index=True
    )



class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"

    __table_args__ =(
        UniqueConstraint(
            "cart_id",
            "product_id",
            name="uq_cart_product"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    cart_id: int = Field(
        foreign_key="carts.id",
        nullable=False,
        index=True,
        ondelete="CASCADE"
    )

    product_id: int = Field(
        foreign_key="products.id",
        nullable=False,
        index=True
    )

    quantity: int = Field(
        default=1,
        ge=1
    )




class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        index=True
    )

    status: str = Field(
        default="pending",
        max_length=50
    )

    total_amount: Decimal = Field(
        nullable=False
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )



class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "product_id",
            name="uq_order_product"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    order_id: int = Field(
        foreign_key="orders.id",
        nullable=False,
        index=True,
        ondelete="CASCADE"
    )

    product_id: int = Field(
        foreign_key="products.id",
        nullable=False,
        index=True
    )

    quantity: int = Field(
        nullable=False,
        ge=1
    )

    price: Decimal = Field(
        nullable=False
    )



class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: int | None = Field(default=None, primary_key=True)

    order_id: int = Field(
        foreign_key="orders.id",
        nullable=False,
        unique=True,
        index=True
    )

    amount: Decimal = Field(
        nullable=False
    )

    status: str = Field(
        default="pending",
        max_length=50
    )

    payment_method: str = Field(
        max_length=50,
        nullable=False
    )

    transaction_id: str | None = Field(
        default=None,
        max_length=255,
        unique=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )



class ProductImage(SQLModel, table=True):
    __tablename__ = "product_images"

    id: int | None = Field(
        default=None,
        primary_key=True
    )

    product_id: int = Field(
        foreign_key="products.id",
        nullable=False,
        index=True,
        ondelete="CASCADE"
    )

    url: str = Field(
        nullable=False
    )

    public_id: str = Field(
        nullable=False,
        unique=True
    )

    image_type: str = Field(
        nullable=False,
        max_length=20
    )

    sort_order: int = Field(
        default=0,
        ge=0
    )










