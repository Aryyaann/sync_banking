from sqlalchemy import create_engine, text
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from auth import hash_password

DATABASE_URL = "postgresql://postgres:MJxAMgWBOtQPpefwPUqvwgvPyaePcpnG@kodama.proxy.rlwy.net:50752/railway"
BUSINESS_ID = "160a1f57-26d2-497f-a190-1219f0da11e0"

EMAIL = "PON_AQUI_TU_EMAIL_REAL"
PASSWORD = "ElígeUnaContraseñaSegura123"

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