from fastapi import APIRouter , HTTPException, Depends
from models import Cart, CartItem, Product, User
from schemas import CartItemCreate, CartItemDetail, CartRead, CartItemUpdate,CartItemRead
from routers.auth import get_current_user , get_session 
from sqlmodel import Session , select
from decimal import Decimal

router= APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post("/items", response_model=CartItemDetail, status_code=201)
def add_to_cart(
    item_data: CartItemCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # 1. التأكد من وجود المنتج
    product = session.get(Product, item_data.product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 2. التأكد أن الكمية المطلوبة متوفرة
    if item_data.quantity > product.in_stock:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    # 3. البحث عن Cart الخاصة بالمستخدم
    cart = session.exec(
        select(Cart).where(
            Cart.user_id == current_user.id
        )
    ).first()

    # 4. إذا لم تكن موجودة، أنشئ Cart
    if not cart:
        cart = Cart(user_id=current_user.id)

        session.add(cart)
        session.flush()

    # 5. هل المنتج موجود بالفعل في السلة؟
    cart_item = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id
        )
    ).first()

    if cart_item:
        # الكمية الجديدة
        new_quantity = cart_item.quantity + item_data.quantity

        # التأكد من المخزون مرة أخرى
        if new_quantity > product.in_stock:
            raise HTTPException(
                status_code=400,
                detail="Total quantity exceeds available stock"
            )

        # زيادة الكمية
        cart_item.quantity = new_quantity

    else:
        # إنشاء عنصر جديد
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=item_data.quantity
        )

        session.add(cart_item)

    # 6. حفظ التغييرات
    session.commit()
    session.refresh(cart_item)

    return {
    "id": cart_item.id,
    "product_id": product.id,
    "name": product.name,
    "price": product.price,
    "quantity": cart_item.quantity,
    "subtotal": product.price * cart_item.quantity
}


@router.get("/", response_model=CartRead)
def get_cart(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # 1. الحصول على Cart الخاصة بالمستخدم
    cart = session.exec(
        select(Cart).where(
            Cart.user_id == current_user.id
        )
    ).first()

    # إذا لم يكن لديه Cart
    if not cart:
        return {
            "items": [],
            "total": Decimal("0")
        }

    # 2. جلب CartItems مع Products
    statement = (
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.cart_id == cart.id)
    )

    results = session.exec(statement).all()

    # 3. تجهيز البيانات
    items = []
    total = Decimal("0")

    for cart_item, product in results:
        subtotal = product.price * cart_item.quantity

        items.append(
            {
                "id": cart_item.id,
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "quantity": cart_item.quantity,
                "subtotal": subtotal,
            }
        )

        total += subtotal

    return {
        "items": items,
        "total": total
    }




@router.patch("/items/{item_id}", response_model=CartItemRead)
def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # 1. الحصول على Cart الخاصة بالمستخدم
    cart = session.exec(
        select(Cart).where(
            Cart.user_id == current_user.id
        )
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    # 2. الحصول على CartItem والتأكد أنه تابع لهذه السلة
    cart_item = session.exec(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    # 3. الحصول على المنتج للتحقق من المخزون
    product = session.get(Product, cart_item.product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 4. التحقق من المخزون
    if item_data.quantity > product.in_stock:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock"
        )

    # 5. تحديث الكمية
    cart_item.quantity = item_data.quantity

    # 6. الحفظ
    session.commit()
    session.refresh(cart_item)

    return cart_item



@router.delete("/items/{item_id}")
def delete_cart_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # 1. الحصول على Cart الخاصة بالمستخدم
    cart = session.exec(
        select(Cart).where(
            Cart.user_id == current_user.id
        )
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    # 2. البحث عن العنصر والتأكد أنه تابع لسلة المستخدم
    cart_item = session.exec(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    ).first()

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    # 3. حذف العنصر
    session.delete(cart_item)
    session.commit()

    return {
        "message": "Item removed from cart successfully"
    }