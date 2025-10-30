from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, Field
from passlib.hash import pbkdf2_sha256

from backend.app.core.security import create_access_token, get_current_user, require_role

router = APIRouter()

# ---- Pydantic схеми ----
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="viewer")  # viewer|analyst|admin

class LoginRequest(BaseModel):
    username: str
    password: str
    cookie: bool = False  # ако True – ще сетнем HttpOnly cookie

class UserPublic(BaseModel):
    id: int
    username: str
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# ---- Помощни функции (in-memory) ----
def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pbkdf2_sha256.verify(password, hashed)

# ---- МАРШРУТИ ----
@router.post("/register", response_model=UserPublic, status_code=201)
def register(req: RegisterRequest, request: Request):
    users = request.app.state.users_store
    if req.username in users:
        raise HTTPException(status_code=409, detail="Username already exists")
    new_id = len(users) + 1
    users[req.username] = {
        "id": new_id,
        "username": req.username,
        "password_hash": hash_password(req.password),
        "role": req.role,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"id": new_id, "username": req.username, "role": req.role}

@router.post("/login", response_model=TokenResponse)
def login(resp: Response, req: LoginRequest, request: Request):
    users = request.app.state.users_store
    u = users.get(req.username)
    if not u or not verify_password(req.password, u["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    claims = {"sub": u["username"], "role": u["role"]}
    token = create_access_token(claims)
    # по желание сетваме HttpOnly cookie
    if req.cookie:
        resp.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,    # в продукция → True (HTTPS)
            samesite="lax",
            max_age=60*60,   # 1h
            path="/",
        )
    return {"access_token": token, "expires_in": 60*60}

@router.get("/me", response_model=UserPublic)
def me(user = Depends(get_current_user)):
    return {"id": user["id"], "username": user["username"], "role": user["role"]}

@router.get("/secure-ping")
def secure_ping(user = Depends(get_current_user)):
    return {"ok": True, "user": user}

@router.get("/admin-only")
def admin_only(user = Depends(require_role("admin"))):
    return {"ok": True, "admin": user["username"]}
