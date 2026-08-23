from fastapi import FastAPI
from database import create_db_and_tables
from routers import product_images, users , categories , attributes , categoryattribute , products, cart,orders, payments, media

app = FastAPI(title="project1 API", version="1.0")
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(attributes.router)
app.include_router(categoryattribute.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(media.router)
app.include_router(product_images.router)

# ✅ إنشاء الجداول تلقائياً عند بدء التشغيل
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
