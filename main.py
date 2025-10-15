from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from bson import ObjectId
from db import users_col, overlays_col, streams_col
from helpers import hash_password, verify_password, to_dict, create_access_token 
from models import UserOut, UserCreate, OverlayCreate, OverlayOut, StreamCreate, StreamOut, TokenOut, LoginIn
from dependencies import admin_required, get_current_user
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="Stream One", version="1.0")

print(users_col.find_one({"email": "admin@example.com"}))

@app.on_event("startup")
def create_default_admin():
    if users_col.count_documents({}) == 0:
        admin = {
            "name": "Admin",
            "email": "admin@example.com",
            "password": hash_password("admin"),
            "role": "admin",
        }
        users_col.insert_one(admin)
        print("Created default admin: admin@example.com / admin (change immediately)")

# Auth
@app.post("/users/register", response_model=UserOut, status_code=201)
def register_user(user: UserCreate):
    if users_col.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    doc = {"name": user.name, "email": user.email, "password": hash_password(user.password), "role": user.role}
    res = users_col.insert_one(doc)
    doc_db = users_col.find_one({"_id": res.inserted_id})
    return to_dict(doc_db)

@app.post("/users/login", response_model=TokenOut, status_code=201)
def login_user(data: LoginIn):
    user = users_col.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/users", response_model=List[UserOut], dependencies=[Depends(admin_required)])
def list_users():
    return [to_dict(u) for u in users_col.find({}, {"password": 0})]

@app.get("/users/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    current_user.pop("password", None)
    return current_user

@app.put("/users/me", response_model=UserOut)
def update_me(payload: UserCreate = Body(...), current_user: dict = Depends(get_current_user)):
    update = {"name": payload.name, "email": payload.email, "password": hash_password(payload.password)}
    users_col.update_one({"_id": ObjectId(current_user["id"])}, {"$set": update})
    updated = users_col.find_one({"_id": ObjectId(current_user["id"])}, {"password": 0})
    return to_dict(updated)

@app.delete("/users/{user_id}", dependencies=[Depends(admin_required)], status_code=204)
def delete_user(user_id: str):
    res = users_col.delete_one({"_id": ObjectId(user_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {}

# Streams
@app.post("/streams", response_model=StreamOut, status_code=201, dependencies=[Depends(admin_required)])
def create_stream(payload: StreamCreate):
    res = streams_col.insert_one(payload.dict())
    doc = streams_col.find_one({"_id": res.inserted_id})
    return to_dict(doc)

@app.get("/streams", response_model=List[StreamOut])
def list_streams(current_user: dict = Depends(get_current_user)):
    return [to_dict(s) for s in streams_col.find()]

@app.get("/streams/{stream_id}", response_model=StreamOut)
def get_stream(stream_id: str, current_user: dict = Depends(get_current_user)):
    stream = streams_col.find_one({"_id": ObjectId(stream_id)})
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    return to_dict(stream)

@app.put("/streams/{stream_id}", response_model=StreamOut, dependencies=[Depends(admin_required)])
def update_stream(stream_id: str, payload: StreamCreate):
    res = streams_col.update_one({"_id": ObjectId(stream_id)}, {"$set": payload.dict()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Stream not found")
    return to_dict(streams_col.find_one({"_id": ObjectId(stream_id)}))

@app.delete("/streams/{stream_id}", dependencies=[Depends(admin_required)], status_code=204)
def delete_stream(stream_id: str):
    streams_col.delete_one({"_id": ObjectId(stream_id)})
    overlays_col.delete_many({"stream_id": stream_id})
    return {}

# Overlay
@app.post("/overlays", response_model=OverlayOut, status_code=201)
def create_overlay(payload: OverlayCreate, current_user: dict = Depends(get_current_user)):
    if payload.stream_id:
        stream = streams_col.find_one({"_id": ObjectId(payload.stream_id)})
        if not stream:
            raise HTTPException(status_code=404, detail="Stream not found")
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admin can create overlays for a stream")
        doc = payload.dict()
        doc["owner_id"] = None
        res = overlays_col.insert_one(doc)
        return to_dict(overlays_col.find_one({"_id": res.inserted_id}))
    else:
        doc = payload.dict()
        doc.pop("stream_id", None)
        doc["owner_id"] = current_user["id"]
        res = overlays_col.insert_one(doc)
        return to_dict(overlays_col.find_one({"_id": res.inserted_id}))

@app.get("/overlays", response_model=List[OverlayOut])
def list_overlays(current_user: dict = Depends(get_current_user)):
    stream_overlays = list(overlays_col.find({"stream_id": {"$exists": True}}))
    user_overlays = list(overlays_col.find({"owner_id": current_user["id"]}))
    combined = stream_overlays + user_overlays
    return [to_dict(o) for o in combined]

@app.get("/overlays/{overlay_id}", response_model=OverlayOut)
def get_overlay(overlay_id: str, current_user: dict = Depends(get_current_user)):
    ov = overlays_col.find_one({"_id": ObjectId(overlay_id)})
    if not ov:
        raise HTTPException(status_code=404, detail="Overlay not found")
    if ov.get("owner_id") and ov["owner_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    return to_dict(ov)

@app.put("/overlays/{overlay_id}", response_model=OverlayOut)
def update_overlay(overlay_id: str, payload: OverlayCreate, current_user: dict = Depends(get_current_user)):
    ov = overlays_col.find_one({"_id": ObjectId(overlay_id)})
    if not ov:
        raise HTTPException(status_code=404, detail="Overlay not found")
    if ov.get("stream_id"):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admin can update stream overlays")
    else:
        if ov.get("owner_id") != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only owner or admin can update this overlay")
    update_doc = payload.dict()
    overlays_col.update_one({"_id": ObjectId(overlay_id)}, {"$set": update_doc})
    return to_dict(overlays_col.find_one({"_id": ObjectId(overlay_id)}))

@app.delete("/overlays/{overlay_id}", status_code=204)
def delete_overlay(overlay_id: str, current_user: dict = Depends(get_current_user)):
    ov = overlays_col.find_one({"_id": ObjectId(overlay_id)})
    if not ov:
        raise HTTPException(status_code=404, detail="Overlay not found")
    if ov.get("stream_id"):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admin can delete stream overlays")
    else:
        if ov.get("owner_id") != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only owner or admin can delete this overlay")
    overlays_col.delete_one({"_id": ObjectId(overlay_id)})
    return {}
