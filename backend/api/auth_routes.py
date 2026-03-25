from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from pydantic import BaseModel

router = APIRouter()

# ---------- DB SESSION ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- REGISTER MODEL ----------
class RegisterRequest(BaseModel):
    email: str
    password: str


# ---------- LOGIN MODEL ----------
class LoginRequest(BaseModel):
    email: str
    password: str


# ---------- REGISTER API ----------
@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == req.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = User(
        email=req.email,
        password=req.password
    )

    db.add(new_user)
    db.commit()

    return {"message": "User registered successfully"}


# ---------- LOGIN API ----------
@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == req.email).first()

    if not user or user.password != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "email": user.email
    }