from sqlalchemy import create_engine, text
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from auth import hash_password

DATABASE_URL = "postgresql://postgres:sync2026testXYZ@kodama.proxy.rlwy.net:50752/railway"
BUSINESS_ID = "9c47c269-62f5-41f8-9f8b-b6b6e65d5076"

EMAIL = "hnarwani8@gmail.com"
PASSWORD = "sync2026testXYZ"

print(f"[debug] DATABASE_URL = {repr(DATABASE_URL)}")

engine = create_engine(DATABASE_URL)
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO users (id, business_id, email, password_hash)
        VALUES (:id, :bid, :email, :hash)
    """), {
        "id": str(uuid.uuid4()),
        "bid": BUSINESS_ID,
        "email": EMAIL,
        "hash": hash_password(PASSWORD),
    })
print(f"✅ Usuario creado: {EMAIL}")