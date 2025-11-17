from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, Field
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, require_role, admin_required, ACCESS_TOKEN_EXPIRE_MINUTES
from app.crud import user as crud_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["authentication"])

# ---- Pydantic схеми ----
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="viewer")  # admin|researcher|viewer

class LoginRequest(BaseModel):
    """Схема за login request."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    set_cookie: bool = Field(default=False, description="Ако True, сетва HttpOnly cookie")

class UserPublic(BaseModel):
    id: int
    username: str
    role: str

class TokenResponse(BaseModel):
    """Схема за token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # в секунди

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

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Автентикира потребител и връща JWT access token.
    
    Приема username и password, проверява ги срещу базата данни,
    и връща JWT token. Опционално може да сетне HttpOnly cookie.
    
    Args:
        login_data: Login credentials (username, password, set_cookie)
        response: FastAPI Response обект за сетване на cookies
        db: Database session
        
    Returns:
        TokenResponse с access_token и метаданни
        
    Raises:
        HTTPException: 401 UNAUTHORIZED при невалидни credentials
        
    TODO:
        - Добави rate limiting за защита срещу brute-force атаки (провер на брой опити от IP адрес, redis или in-memory cache за броене на опити)
          (например: максимум 5 опита за 15 минути от един IP)
        - Добави logging на неуспешни опити за login за мониторинг и сигурност
        - Разгледай възможност за refresh token механизъм за по-добра UX
          (дълготрайни refresh tokens + късоживеещи access tokens)
    """

    # Автентикация на потребителя
    user = crud_user.authenticate(
        db=db,
        username=login_data.username,
        password=login_data.password
    )
    
    if not user:
        # TODO: Logging - логвай неуспешен опит за login
        # Пример: logger.warning(f"Failed login attempt for username: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Създаване на JWT token
    token_data = {
        "sub": user.username,
        "role": user.role,
        "id": user.id  # Опционално, за по-бърз достъп
    }
    access_token = create_access_token(data=token_data)
    
    # Сетване на cookie ако е поискано
    if login_data.set_cookie:
        expires_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # В продукция трябва да е True (HTTPS)
            samesite="lax",
            max_age=expires_seconds,
            path="/",
        )
    
    # TODO: Token refresh - ако се добави refresh token механизъм,
    # може да се върне и refresh_token в response-а
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    """Връща информация за текущия автентикиран потребител."""
    return {"id": user.id, "username": user.username, "role": user.role}

@router.get("/secure-ping")
def secure_ping(user: User = Depends(get_current_user)):
    """Тестов endpoint за проверка на автентикация."""
    return {"ok": True, "user": {"id": user.id, "username": user.username, "role": user.role}}

@router.get("/admin-only")
def admin_only(user: User = Depends(admin_required)):
    """Тестов endpoint само за администратори."""
    return {"ok": True, "admin": user.username}
