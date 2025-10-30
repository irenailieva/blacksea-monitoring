import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

class TokenError(Exception):
    pass

#TODO: Understand security functions
def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise TokenError(str(e))

def get_token_from_request(request: Request) -> str:
    # 1) Authorization: Bearer <token>
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    # 2) HttpOnly cookie 'access_token' (ако решиш да ползваш cookie)
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

def get_current_user(request: Request):
    token = get_token_from_request(request)
    try:
        payload = decode_token(token)
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    # очакваме да имаме sub (username) и role
    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    # in-memory store ще е достъпен през app state (за лесна подмяна с БД по-късно)
    users = request.app.state.users_store  # задаваме го в main.py
    user = users.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {"username": username, "role": role, "id": user["id"]}

def require_role(required: str) -> Callable:
    def dep(user = Depends(get_current_user)):
        if user["role"] != required:
            raise HTTPException(status_code=403, detail="Forbidden for role")
        return user
    return dep
