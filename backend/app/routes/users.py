from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import user as crud_user

# Инициализиране на рутер (APIRouter) за управление на заявките, свързани с потребителите.
# Префиксът "/users" автоматично се добавя пред всеки маршрут, а тагът "users" групира 
# тези маршрути в автоматично генерираната Swagger документация.
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """
    Създава нов потребител. 
    Изисква активен потребител с роля "admin".
    """
    # Използваме CRUD (Create, Read, Update, Delete) модула за създаване на потребителя
    # в базата данни чрез подадената SQLAlchemy сесия (db) и Pydantic модела (user).
    # Резултатът автоматично ще бъде валидиран и сериализиран спрямо schemas.UserRead.
    return crud_user.create(db=db, obj_in=user)


@router.get("/", response_model=list[schemas.UserRead])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща списък от потребители с възможност за странициране (pagination).
    Изисква автентикация (всеки вписан потребител има достъп).
    """
    # Извикваме метода за вземане на множество записи (get_multi).
    # Параметрите 'skip' и 'limit' контролират кои записи да бъдат върнати
    # (полезно за ограничаване на мрежовия трафик при голям брой потребители).
    return crud_user.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=schemas.UserRead)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща детайли за конкретен потребител по неговото ID.
    Изисква автентикация.
    """
    # Опитваме се да намерим потребителя в базата данни чрез неговото ID
    db_user = crud_user.get(db=db, id=user_id)
    
    # Ако потребител с такова ID не съществува, хвърляме HTTP изключение 404 (Not Found).
    # Това информира клиента, че заявеният ресурс липсва, вместо да възникне вътрешна грешка.
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Връщаме намерения потребител, който ще се сериализира към schemas.UserRead
    return db_user
