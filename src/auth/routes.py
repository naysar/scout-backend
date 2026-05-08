import os
import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .models import User, get_db, init_db
from .security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token
)
from collections import defaultdict
import time

router = APIRouter(prefix="/auth")
init_db()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"

login_attempts: dict = defaultdict(list)

def check_rate_limit(ip: str):
    now = time.time()
    attempts = [t for t in login_attempts[ip] if now - t < 300]
    login_attempts[ip] = attempts
    if len(attempts) >= 5:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 5 minutes.")
    login_attempts[ip].append(now)

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = User(
        name=req.name,
        email=req.email,
        password_hash=hash_password(req.password),
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Account created. Please log in."}

@router.post("/login")
def login(req: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host
    check_rate_limit(ip)
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    user.refresh_token = refresh_token
    db.commit()
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", max_age=1800)
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=604800)
    return {"message": "Logged in.", "name": user.name, "email": user.email}

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token.")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or user.refresh_token != token:
        raise HTTPException(status_code=401, detail="Token revoked.")
    new_access = create_access_token(user.id, user.email)
    response.set_cookie("access_token", new_access, httponly=True, samesite="lax", max_age=1800)
    return {"message": "Token refreshed."}

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        payload = decode_token(token)
        if payload:
            user = db.query(User).filter(User.id == payload["sub"]).first()
            if user:
                user.refresh_token = None
                db.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out."}

@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"id": user.id, "name": user.name, "email": user.email}

@router.get("/google")
def google_login():
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&scope=openid email profile"
    )
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str, response: Response, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        tokens = token_res.json()
        userinfo_res = await client.get("https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": "Bearer " + tokens["access_token"]})
        userinfo = userinfo_res.json()
    user = db.query(User).filter(User.email == userinfo["email"]).first()
    if not user:
        user = User(
            name=userinfo.get("name", ""),
            email=userinfo["email"],
            google_id=userinfo["sub"],
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    user.refresh_token = refresh_token
    db.commit()
    response.set_cookie("access_token", access_token, httponly=True, samesite="lax", max_age=1800)
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=604800)
    return RedirectResponse("http://localhost:3000/dashboard")
