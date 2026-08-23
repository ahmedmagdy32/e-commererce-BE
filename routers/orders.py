from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from decimal import Decimal
from database import get_session
from models import User, Cart, CartItem, Product, Order, OrderItem
from schemas import OrderRead
from routers.auth import get_current_user


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)



@router.post("/checkout", response_model=OrderRead, status_code=201)
def checkout(
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

    # 2. جلب عناصر السلة
    cart_items = session.exec(
        select(CartItem).where(
            CartItem.cart_id == cart.id
        )
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # 3. إنشاء Order مؤقتًا
    order = Order(
        user_id=current_user.id,
        status="pending",
        total_amount=Decimal("0")
    )

    session.add(order)
    session.flush()

    total = Decimal("0")

    # 4. تحويل CartItems إلى OrderItems
    for cart_item in cart_items:

        product = session.get(Product, cart_item.product_id)

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {cart_item.product_id} not found"
            )

        # 5. التحقق من المخزون
        if cart_item.quantity > product.in_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product {product.name}"
            )

        # 6. حساب السعر
        subtotal = product.price * cart_item.quantity
        total += subtotal

        # 7. إنشاء OrderItem
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=cart_item.quantity,
            price=product.price
        )

        session.add(order_item)

        # 8. تخفيض المخزون
        product.in_stock -= cart_item.quantity

    # 9. حفظ الإجمالي
    order.total_amount = total

    # 10. إفراغ السلة
    for cart_item in cart_items:
        session.delete(cart_item)

    # 11. حفظ كل العملية
    session.commit()

    session.refresh(order)

    # 12. جلب OrderItems
    order_items = session.exec(
        select(OrderItem).where(
            OrderItem.order_id == order.id
        )
    ).all()

    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "items": order_items
    }



@router.get("/", response_model=list[OrderRead])
def get_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    orders = session.exec(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).all()

    result = []

    for order in orders:
        order_items = session.exec(
            select(OrderItem).where(
                OrderItem.order_id == order.id
            )
        ).all()

        result.append({
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
            "items": order_items
        })

    return result



@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    order = session.exec(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order_items = session.exec(
        select(OrderItem).where(
            OrderItem.order_id == order.id
        )
    ).all()

    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "created_at": order.created_at,
        "items": order_items
    }