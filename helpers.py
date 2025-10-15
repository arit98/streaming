from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt, time
from config import ACCESS_TOKEN_EXPIRE_SECONDS, SECRET_KEY, ALGORITHM
from typing import Optional
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# def verify_password(plain: str, hashed: str) -> bool:
#     return pwd_context.verify(plain, hashed)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_seconds: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    payload = data.copy()
    payload.update({"exp": time.time() + expires_seconds})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def to_dict(doc: dict) -> Optional[dict]:
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc