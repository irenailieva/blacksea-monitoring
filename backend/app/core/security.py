"""
Модул за автентикация и авторизация.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# pwd_context removed as passlib is incompatible with modern bcrypt
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хешира потребителска парола с bcrypt.
    Генерира случаен "солт" (salt) и го комбинира с паролата преди хеширане,
    което предпазва от речникови атаки и атаки с предварително изчислени таблици (rainbow tables).
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверява дали дадена парола (в явен текст) съвпада с хешираната версия,
    съхранена в базата данни. Използва bcrypt.checkpw за сигурна проверка.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class TokenError(Exception):
    """Грешка при валидация на JWT token."""
    pass


def create_access_token(
    data: dict,
    expires_minutes: Optional[int] = None
) -> str:
    """
    Създава JWT (JSON Web Token) за удостоверяване на потребителя (access token).
    
    Args:
        data: Данни за включване в токена. Трябва да съдържа поне "sub" (subject/username).
              Може да включва и "role", "email" и др.
        expires_minutes: Продължителност в минути на валидността на токена. 
                         Ако е None, се използва стойността по подразбиране (ACCESS_TOKEN_EXPIRE_MINUTES).
        
    Returns:
        Криптографски подписан JWT token като стринг (string).
        
    Raises:
        ValueError: Ако data не съдържа полето "sub" (subject).
    """
    if not data or "sub" not in data:
        raise ValueError("Token data must contain 'sub' field")
    
    # Копираме данните, за да не променяме оригиналния речник
    to_encode = data.copy()
    
    # Изчисляваме времето на изтичане (expiration time) на токена в UTC
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # Добавяне на стандартни (reserved) JWT claims (полета)
    to_encode.update({
        "exp": expire, # Време на изтичане на токена
        "iat": datetime.now(timezone.utc)  # Време на издаване (Issued at timestamp)
    })
    
    # Кодиране на токена с избрания таен ключ (secret) и алгоритъм
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Декодира и валидира JWT токена.
    Ако токенът е невалиден, манипулиран или с изтекъл срок, хвърля TokenError.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise TokenError(str(e))


def get_token_from_request(request: Request) -> str:
    """
    Извлича JWT токена от HTTP заявката (request).
    Първо проверява Authorization header-а, а ако липсва, проверява в cookies.
    """
    # 1) Проверка в хедъра (Authorization: Bearer <token>)
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
        
    # 2) Проверка в бисквитките (HttpOnly cookie 'access_token') - важно за сигурността в браузъра
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
        
    # Ако токенът не е намерен нито в хедъра, нито в бисквитката, се връща 401 Unauthorized
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing token"
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Извлича текущия автентикиран потребител.
    
    Използва се като зависимост (dependency) във FastAPI routes за защита на endpoints.
    Автоматично извлича токена, валидира го, и зарежда потребителя от базата данни.
    Ако някоя от тези стъпки се провали, връща грешка (HTTPException).
    """
    # Стъпка 1: Извличане на токена от заявката (headers или cookies)
    token = get_token_from_request(request)
    
    # Стъпка 2: Декодиране и криптографска валидация на токена
    try:
        payload = decode_token(token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Стъпка 3: Извличане на идентификатора на потребителя ('sub') от полезния товар (payload)
    username = payload.get("sub")
    if not username or not isinstance(username, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing or invalid 'sub' field",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Стъпка 4: Зареждане на потребителя от базата данни и проверка дали съществува
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account may have been deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(required: str) -> Callable:
    """
    Фабрична функция (factory function) за създаване на зависимост (dependency), 
    която изисква потребителят да има точно определена роля.
    Ако ролята не съвпада, връща 403 Forbidden.
    """
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role != required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: requires role '{required}'"
            )
        return user
    return dep


def require_any_role(*roles: str) -> Callable:
    """
    Фабрична функция за създаване на зависимост, която изисква 
    потребителят да има поне една от посочените роли.
    Полезно за маршрути, достъпни например за 'researcher' и 'admin'.
    """
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: requires one of roles {roles}"
            )
        return user
    return dep


def admin_required(user: User = Depends(get_current_user)) -> User:
    """
    Специфична зависимост, която проверява дали текущият потребител е администратор.
    Използва се директно в маршрути: @router.get(..., dependencies=[Depends(admin_required)])
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: requires admin role"
        )
    return user


def researcher_required(user: User = Depends(get_current_user)) -> User:
    """
    Специфична зависимост, която проверява дали текущият потребител е изследовател (researcher).
    """
    if user.role != "researcher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: requires researcher role"
        )
    return user
