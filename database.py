from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
import os

# تحميل المتغيرات من .env
load_dotenv()

# قراءة رابط الاتصال
DATABASE_URL = os.getenv("DATABASE_URL")

# إنشاء المحرك
engine = create_engine(
    DATABASE_URL,
    echo=True,              # ← يعرض أوامر SQL في التيرمنال (عطّله في الإنتاج)
    pool_pre_ping=True      # ← يتحقق من الاتصال قبل الاستخدام (يمنع انقطاع الاتصال)
)

# إنشاء الجداول تلقائياً عند بدء التشغيل
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Dependency: يُعطي كل طلب Session مستقل ثم يُغلقه تلقائياً
def get_session():
    with Session(engine) as session:
        yield session
