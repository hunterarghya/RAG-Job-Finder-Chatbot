from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.db import users_col
from api.auth import hash_password, verify_password, create_access_token, decode_token
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterIn(BaseModel):
    email: str
    password: str
    name: str = None

class LoginIn(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(payload: RegisterIn):
    if users_col.find_one({"email": payload.email}):
        raise HTTPException(400, "User already exists")
    user = {
        "email": payload.email,
        "name": payload.name or "",
        "password": hash_password(payload.password),
        "created_at": __import__("datetime").datetime.utcnow()
    }
    res = users_col.insert_one(user)
    user_id = str(res.inserted_id)
    token = create_access_token({"sub": user_id, "email": payload.email})
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}



@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_col.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")

    user_id = str(user["_id"])
    token = create_access_token({"sub": user_id, "email": user["email"]})
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}
