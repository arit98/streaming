from fastapi import Depends, HTTPException
from bson import ObjectId
from helpers import oauth2_scheme, decode_token, to_dict
from db import users_col

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = users_col.find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return to_dict(user)

def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user