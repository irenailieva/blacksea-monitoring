from datetime import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, Field, EmailStr
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, require_role, admin_required, ACCESS_TOKEN_EXPIRE_MINUTES
from app.crud import user as crud_user
from app.models.user import User
from app import schemas

# Инициализиране на APIRouter за маршрутите за автентикация
router = APIRouter(prefix="/auth", tags=["authentication"])

# ---- Pydantic схеми ----
# Pydantic схемите дефинират структурата на входните и изходните данни,
# осигурявайки автоматична валидация на типовете и ограниченията.
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="viewer")  # admin|researcher|viewer

class LoginRequest(BaseModel):
    """Схема за login request (заявка за вход)."""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    set_cookie: bool = Field(default=False, description="Ако True, сетва HttpOnly cookie")

class UserPublic(BaseModel):
    id: int
    username: str
    role: str

class TokenResponse(BaseModel):
    """Схема за token response (отговор с токен)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # в секунди

# ---- Помощни функции (in-memory) ----
def hash_password(password: str) -> str:
    """Хешира паролата използвайки алгоритъма pbkdf2_sha256."""
    return pbkdf2_sha256.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Проверява дали подадената парола съвпада с хешираната."""
    return pbkdf2_sha256.verify(password, hashed)

# ---- МАРШРУТИ ----
@router.post("/register", response_model=UserPublic, status_code=201)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Регистрира нов потребител в базата данни.
    """
    # Създаваме обект от тип UserCreate (Pydantic схема), който съдържа нужните данни
    user_in = schemas.UserCreate(
        username=req.username,
        email=req.email,
        password=req.password,
        role=req.role
    )
    
    # Използваме CRUD модула, за да запишем новия потребител в базата данни.
    # CRUD операциите са изнесени в отделен слой за по-добра архитектура.
    user = crud_user.create(db=db, obj_in=user_in)
    
    # Връщаме публичните данни за създадения потребител.
    return {"id": user.id, "username": user.username, "role": user.role}

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
    """

    # Опит за автентикация: проверява се дали потребителят съществува и дали паролата съвпада.
    print(f"DEBUG LOGIN ATTEMPT: username='{login_data.username}' password='{login_data.password}'")
    user = crud_user.authenticate(
        db=db,
        username=login_data.username,
        password=login_data.password
    )
    
    # Ако автентикацията е неуспешна (потребителят не е намерен или паролата е грешна),
    # хвърляме изключение 401 Unauthorized, което указва липса на права за достъп.
    if not user:
        print(f"DEBUG LOGIN FAILED for {login_data.username}")
        # Тук може да се добави логване на неуспешния опит от съображения за сигурност.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Подготвяме данните (payload), които ще бъдат вградени в JWT токена.
    # Обикновено включват идентификатори и роли (за role-based access control).
    token_data = {
        "sub": user.username,
        "role": user.role,
        "id": user.id  # Опционално, за по-бърз достъп от frontend или middleware
    }
    # Генерираме самия JWT токен, използвайки таен ключ и алгоритъм (обикновено HS256).
    access_token = create_access_token(data=token_data)
    
    # Ако клиентът изрично е поискал (или ако това е стандартната ни практика),
    # записваме токена в HttpOnly cookie. Това е важно за предотвратяване на XSS атаки,
    # тъй като JavaScript няма достъп до HttpOnly cookies.
    if login_data.set_cookie:
        expires_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,  # Предпазва от достъп през JavaScript
            secure=False,   # Трябва да е False за localhost; True само при HTTPS (production)
            samesite="lax", # Предотвратява CSRF атаки
            max_age=expires_seconds,
            path="/",
        )
    
    # Връщаме токена в отговора като JSON.
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    """Връща информация за текущия автентикиран потребител."""
    # Тук използваме Dependency Injection (Depends). 
    # FastAPI първо ще изпълни get_current_user (което валидира токена) и ще подаде намерения потребител.
    return {"id": user.id, "username": user.username, "role": user.role}

@router.get("/secure-ping")
def secure_ping(user: User = Depends(get_current_user)):
    """Тестов endpoint за проверка на автентикация."""
    # Прост маршрут за проверка дали токенът на потребителя е валиден и заявката минава.
    return {"ok": True, "user": {"id": user.id, "username": user.username, "role": user.role}}

@router.get("/admin-only")
def admin_only(user: User = Depends(admin_required)):
    """Тестов endpoint само за администратори."""
    # Depends(admin_required) не само валидира токена, но и проверява дали role == 'admin'.
    return {"ok": True, "admin": user.username}
