"""
API routes за IndexType ресурс.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import index_type as crud_index_type

# Инициализация на рутер за типовете спектрални индекси (например: NDVI, NDWI).
router = APIRouter(prefix="/index-types", tags=["index-types"])


@router.post("/", response_model=schemas.IndexTypeRead, status_code=status.HTTP_201_CREATED)
def create_index_type(
    index_type_in: schemas.IndexTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Създава нов тип индекс в системата. 
    Изисква права на достъп: 'researcher' (изследовател) или 'admin' (администратор).
    """
    # Извиква се CRUD метода за запис на новия обект в базата данни.
    return crud_index_type.create(db=db, obj_in=index_type_in)


@router.get("/", response_model=List[schemas.IndexTypeRead])
def read_index_types(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща списък от всички налични типове индекси.
    Достъпно за всеки автентикиран потребител.
    Поддържа странициране (pagination) чрез параметрите 'skip' и 'limit'.
    """
    # Извличане на множество записи от базата данни, спазвайки ограниченията за странициране.
    return crud_index_type.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{index_type_id}", response_model=schemas.IndexTypeRead)
def read_index_type(
    index_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща детайлна информация за конкретен тип индекс въз основа на неговото ID.
    Изисква автентикация.
    """
    # Търсене на обекта в базата.
    db_index_type = crud_index_type.get(db=db, id=index_type_id)
    
    # Ако не съществува такъв индекс, връщаме грешка 404 (Не е намерено).
    if not db_index_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexType not found"
        )
    return db_index_type


@router.put("/{index_type_id}", response_model=schemas.IndexTypeRead)
def update_index_type(
    index_type_id: int,
    index_type_in: schemas.IndexTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Обновява съществуващ тип индекс.
    Изисква 'researcher' или 'admin' роля, тъй като модифицира основни справочни данни.
    """
    # Първо проверяваме дали индексът изобщо съществува.
    db_index_type = crud_index_type.get(db=db, id=index_type_id)
    if not db_index_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexType not found"
        )
        
    # Ако съществува, извикваме метода за актуализация, 
    # който прехвърля новите стойности (obj_in) върху съществуващия обект (db_obj).
    return crud_index_type.update(db=db, db_obj=db_index_type, obj_in=index_type_in)


@router.delete("/{index_type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_index_type(
    index_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """
    Изтрива тип индекс от базата данни.
    Това е деструктивна операция и изисква роля 'admin'.
    """
    # Проверка дали обектът съществува преди да се опитаме да го изтрием.
    db_index_type = crud_index_type.get(db=db, id=index_type_id)
    if not db_index_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IndexType not found"
        )
        
    # Изпълняване на операцията по изтриване.
    crud_index_type.delete(db=db, id=index_type_id)
    
    # Връщаме None, което в комбинация със status_code 204 означава успешно изпълнение без съдържание в отговора.
    return None
