import os
from dotenv import load_dotenv

load_dotenv()

PAYMOB_API_KEY = os.getenv("PAYMOB_API_KEY")
PAYMOB_PUBLIC_KEY = os.getenv("PAYMOB_PUBLIC_KEY")
PAYMOB_INTEGRATION_ID = int(
    os.getenv("PAYMOB_INTEGRATION_ID")
)
PAYMOB_HMAC_SECRET = os.getenv("PAYMOB_HMAC_SECRET")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not PAYMOB_API_KEY:
    raise ValueError("PAYMOB_API_KEY is missing")

if not PAYMOB_PUBLIC_KEY:
    raise ValueError("PAYMOB_PUBLIC_KEY is missing")

if not PAYMOB_INTEGRATION_ID:
    raise ValueError("PAYMOB_INTEGRATION_ID is missing")

if not PAYMOB_HMAC_SECRET:
    raise ValueError("PAYMOB_HMAC_SECRET is missing")

PAYMOB_BASE_URL = "https://accept.paymob.com"