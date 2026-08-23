import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import User, Order, Payment
from schemas import PaymentCreate, PaymentRead
from routers.auth import get_current_user
import hmac
import hashlib
from config import PAYMOB_HMAC_SECRET
from fastapi import APIRouter, Depends, HTTPException, Request
from config import (
    PAYMOB_API_KEY,
    PAYMOB_PUBLIC_KEY,
    PAYMOB_INTEGRATION_ID,
    PAYMOB_BASE_URL,
)



router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


def verify_paymob_hmac(
    data: dict,
    received_hmac: str
) -> bool:

    obj = data["obj"]

    fields = [
        obj["amount_cents"],
        obj["created_at"],
        obj["currency"],
        obj["error_occured"],
        obj["has_parent_transaction"],
        obj["id"],
        obj["integration_id"],
        obj["is_3d_secure"],
        obj["is_auth"],
        obj["is_capture"],
        obj["is_refunded"],
        obj["is_standalone_payment"],
        obj["is_voided"],
        obj["order"]["id"],
        obj["owner"],
        obj["pending"],
        obj["source_data"]["pan"],
        obj["source_data"]["sub_type"],
        obj["source_data"]["type"],
        obj["success"],
    ]

    concatenated = "".join(
        str(field).lower() if isinstance(field, bool)
        else str(field)
        for field in fields
    )

    calculated_hmac = hmac.new(
        PAYMOB_HMAC_SECRET.encode(),
        concatenated.encode(),
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(
        calculated_hmac,
        received_hmac
    )


@router.post("/webhook")
async def paymob_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    # --------------------------------------------------
    # 1. قراءة البيانات
    # --------------------------------------------------

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload"
        )

    received_hmac = request.query_params.get("hmac")

    if not received_hmac:
        raise HTTPException(
            status_code=401,
            detail="Missing HMAC"
        )

    # --------------------------------------------------
    # 2. التحقق من HMAC
    # --------------------------------------------------

    if not verify_paymob_hmac(data, received_hmac):
        raise HTTPException(
            status_code=401,
            detail="Invalid HMAC"
        )

    # --------------------------------------------------
    # 3. التأكد من وجود obj
    # --------------------------------------------------

    obj = data.get("obj")

    if not isinstance(obj, dict):
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload"
        )

    # --------------------------------------------------
    # 4. استخراج order_id الخاص بمشروعنا
    # --------------------------------------------------

    extra = (
        obj
        .get("payment_key_claims", {})
        .get("extra", {})
    )

    order_id = extra.get("order_id")

    if not order_id:
        raise HTTPException(
            status_code=400,
            detail="Order ID not found"
        )

    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid Order ID"
        )

    # --------------------------------------------------
    # 5. استخراج Transaction ID
    # --------------------------------------------------

    transaction_id = obj.get("id")

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID not found"
        )

    transaction_id = str(transaction_id)

    # --------------------------------------------------
    # 6. البحث عن Order
    # --------------------------------------------------

    order = session.get(Order, order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # --------------------------------------------------
    # 7. البحث عن Payment
    # --------------------------------------------------

    payment = session.exec(
        select(Payment).where(
            Payment.order_id == order.id
        )
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    # --------------------------------------------------
    # 8. منع معالجة Webhook مكرر
    # --------------------------------------------------

    if payment.status == "paid":
        return {
            "received": True
        }

    # --------------------------------------------------
    # 9. التحقق من العملة
    # --------------------------------------------------

    currency = obj.get("currency")

    if currency != "EGP":
        raise HTTPException(
            status_code=400,
            detail="Invalid currency"
        )

    # --------------------------------------------------
    # 10. التحقق من المبلغ
    # --------------------------------------------------

    amount_cents = obj.get("amount_cents")

    if amount_cents is None:
        raise HTTPException(
            status_code=400,
            detail="Amount not found"
        )

    expected_amount_cents = int(
        payment.amount * 100
    )

    if int(amount_cents) != expected_amount_cents:
        raise HTTPException(
            status_code=400,
            detail="Payment amount mismatch"
        )

    # --------------------------------------------------
    # 11. التأكد من Integration ID
    # --------------------------------------------------

    integration_id = obj.get("integration_id")

    if integration_id is None:
        raise HTTPException(
            status_code=400,
            detail="Integration ID not found"
        )

    # --------------------------------------------------
    # 12. تحديث حالة الدفع
    # --------------------------------------------------

    if obj.get("success") is True:

        payment.status = "paid"
        order.status = "paid"

    else:

        payment.status = "failed"

    payment.transaction_id = transaction_id

    # --------------------------------------------------
    # 13. حفظ التغييرات
    # --------------------------------------------------

    try:

        session.add(payment)
        session.add(order)

        session.commit()

    except Exception:

        session.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update payment"
        )

    # --------------------------------------------------
    # 14. الرد على Paymob
    # --------------------------------------------------

    return {
        "received": True
    }


@router.post("/{order_id}", status_code=201)
def create_payment(
    order_id: int,
    payment_data: PaymentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # 1. الحصول على الطلب والتأكد أنه يخص المستخدم الحالي
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

    # 2. منع الدفع على طلب مدفوع بالفعل
    if order.status == "paid":
        raise HTTPException(
            status_code=400,
            detail="Order is already paid"
        )

    # 3. التحقق من عدم وجود Payment لهذا الطلب
    existing_payment = session.exec(
        select(Payment).where(
            Payment.order_id == order.id
        )
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=409,
            detail="Payment already exists for this order"
        )

    # 4. تحويل الجنيه إلى أصغر وحدة (قرش)
    amount = int(order.total_amount * 100)

    # 5. بيانات الطلب المرسلة إلى Paymob
    payload = {
        "amount": amount,
        "currency": "EGP",
        "payment_methods": [
            PAYMOB_INTEGRATION_ID
        ],
        "items": [
            {
                "name": f"Order #{order.id}",
                "amount": amount,
                "description": f"Payment for order #{order.id}",
                "quantity": 1
            }
        ],
        "billing_data": {
            "first_name": current_user.name,
            "last_name": "User",
            "email": current_user.email,
            "phone_number": "01000000000"
        },
        "customer": {
            "first_name": current_user.name,
            "last_name": "User",
            "email": current_user.email
        },
        "extras": {
            "order_id": str(order.id)
        }
    }

    # 6. إرسال الطلب إلى Paymob
    try:
        response = httpx.post(
            f"{PAYMOB_BASE_URL}/v1/intention/",
            headers={
                "Authorization": f"Token {PAYMOB_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20.0
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Could not connect to payment provider"
        )

    # إذا أعاد Paymob خطأ
    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail=response.text
        )

    data = response.json()

    client_secret = data.get("client_secret")

    if not client_secret:
        raise HTTPException(
            status_code=502,
            detail="Payment provider did not return client_secret"
        )

    # 7. إنشاء Payment محليًا بحالة pending
    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        status="pending",
        payment_method=payment_data.payment_method
    )

    session.add(payment)
    session.commit()
    session.refresh(payment)

    # 8. إنشاء رابط Paymob Unified Checkout
    checkout_url = (
        f"{PAYMOB_BASE_URL}/unifiedcheckout/"
        f"?publicKey={PAYMOB_PUBLIC_KEY}"
        f"&clientSecret={client_secret}"
    )

    return {
        "payment": payment,
        "checkout_url": checkout_url
    }



