import os
import bcrypt
import jwt as pyjwt
from datetime import datetime, timedelta
from fastapi import Header, HTTPException

SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "cambia-esto-en-produccion")
ALGORITHM = "HS256"
EXPIRA_HORAS = 24 * 7  # sesión válida 7 días


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: str, business_id: str) -> str:
    payload = {
        "user_id": user_id,
        "business_id": business_id,
        "exp": datetime.utcnow() + timedelta(hours=EXPIRA_HORAS),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No autenticado")
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # contiene user_id y business_id
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesión caducada, vuelve a iniciar sesión")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")