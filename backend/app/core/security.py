"""
Модул за автентикация и авторизация.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable

from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

# Контекст за хеширане на пароли с bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хешира потребителска парола с bcrypt.
    
    Args:
        password: Паролата в plaintext
        
    Returns:
        Хеширана парола като string (включва salt и rounds)
        
    Example:
        >>> hash_password("mySecurePassword123")
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5Y'
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверява дали дадена парола съвпада с хешираната версия.
    
    Args:
        password: Паролата в plaintext за проверка
        hashed: Хешираната парола от базата данни
        
    Returns:
        True ако паролите съвпадат, False иначе
    """
    return pwd_context.verify(password, hashed)


class TokenError(Exception):
    """Грешка при валидация на JWT token."""
    pass


def create_access_token(
    data: dict,
    expires_minutes: Optional[int] = None
) -> str:
    """
    Създава JWT access token.
    
    Args:
        data: Данни за включване в токена. Трябва да съдържа поне "sub" (subject/username).
              Може да включва и "role", "email" и др.
        expires_minutes: Продължителност в минути. 
                         Ако None, използва ACCESS_TOKEN_EXPIRE_MINUTES от environment.
        
    Returns:
        JWT token като string
        
    Raises:
        ValueError: Ако data не съдържа "sub"
        
    Example:
        >>> claims = {"sub": "john_doe", "role": "analyst"}
        >>> token = create_access_token(claims)
        >>> # С персонализирана продължителност
        >>> token = create_access_token(claims, expires_minutes=60)
    """
    if not data or "sub" not in data:
        raise ValueError("Token data must contain 'sub' field")
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    # Добавяне на стандартни JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)  # Issued at timestamp
    })
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Декодира и валидира JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise TokenError(str(e))


def get_token_from_request(request: Request) -> str:
    """Извлича JWT token от request headers или cookies."""
    # 1) Authorization: Bearer <token>
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    # 2) HttpOnly cookie 'access_token'
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing token"
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Извлича текущия потребител от JWT token и базата данни.
    
    Използва се като dependency във FastAPI routes за защита на endpoints.
    Автоматично извлича токена от Authorization header или cookie, валидира го,
    и зарежда потребителя от базата данни.
    
    Args:
        request: FastAPI Request обект
        db: SQLAlchemy database session
        
    Returns:
        User обект от базата данни
        
    Raises:
        HTTPException: 
            - 401 UNAUTHORIZED: Ако токенът липсва, е невалиден или изтекъл
            - 401 UNAUTHORIZED: Ако payload-ът не съдържа "sub" или е невалиден
            - 401 UNAUTHORIZED: Ако потребителят не е намерен в базата данни
            
    Example:
        >>> @router.get("/protected")
        >>> def protected_route(user: User = Depends(get_current_user)):
        >>>     return {"message": f"Hello {user.username}"}
    """
    # Извличане на токена от request
    token = get_token_from_request(request)
    
    # Декодиране и валидация на токена
    try:
        payload = decode_token(token)
    except TokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Извличане и валидация на username от payload
    username = payload.get("sub")
    if not username or not isinstance(username, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing or invalid 'sub' field",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Зареждане на потребителя от базата данни
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account may have been deleted",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Ако в бъдеще се добави is_active поле, добави проверка:
    # if not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User account is inactive"
    #     )
    
    return user


def require_role(required: str) -> Callable:
    """
    Factory функция за създаване на dependency, която изисква определена роля.
    
    Пример:
        @router.get("/admin-only")
        def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
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
    Factory функция за dependency, която изисква една от посочените роли.
    
    Пример:
        @router.get("/analyst-or-admin")
        def endpoint(user: User = Depends(require_any_role("analyst", "admin"))):
            ...
    """
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: requires one of roles {roles}"
            )
        return user
    return dep
