"""
API routes за Region ресурс.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_any_role
from app.models.user import User
from app import schemas
from app.crud import region as crud_region

# Рутерът за регионите (Area of Interest - AOI), като заливи, езера и други наблюдаеми зони.
router = APIRouter(prefix="/regions", tags=["regions"])


@router.post("", response_model=schemas.RegionRead, status_code=status.HTTP_201_CREATED)
def create_region(
    region_in: schemas.RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Създава нов географски регион (Area of Interest - AOI). 
    Тези региони се използват за филтриране и ограничаване на сателитния анализ до конкретни географски полигони.
    Изисква researcher или admin роля.
    """
    # Добавя новия регион в базата (като включва геометрията му - обикновено GeoJSON или WKT формат).
    return crud_region.create(db=db, obj_in=region_in)


@router.get("", response_model=List[schemas.RegionRead])
def read_regions(
    skip: int = 0,
    limit: int = 100,
    with_geometry: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща списък от региони. 
    Тъй като геометрията (geometry - полигон) може да бъде много тежка като обем данни,
    е въведен флагът 'with_geometry'. По подразбиране е False, което връща само метаданните.
    Ако клиентът изрично подаде with_geometry=True, ще се зареди и върне пълният полигон
    за визуализация върху картата (напр. в Leaflet).
    """
    if with_geometry:
        # Извличане на регионите заедно с техните пространствени геометрии
        return crud_region.get_multi_with_geometry(db=db, skip=skip, limit=limit)
        
    # Извличане на регионите без тежката геометрия, полезно за падащи менюта и списъци
    return crud_region.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{region_id}", response_model=schemas.RegionRead)
def read_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Връща детайлна информация за конкретен регион по неговото ID.
    Обикновено този метод също връща геометрията, защото се отнася само за един обект.
    """
    db_region = crud_region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return db_region


@router.put("/{region_id}", response_model=schemas.RegionRead)
def update_region(
    region_id: int,
    region_in: schemas.RegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("researcher", "admin"))
):
    """
    Обновява данните за даден регион (име, граници, тип).
    Изисква високо ниво на права (researcher или admin).
    """
    db_region = crud_region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    return crud_region.update(db=db, db_obj=db_region, obj_in=region_in)


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_region(
    region_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_role("admin"))
):
    """
    Изтрива регион от базата. 
    Всички свързани с него сцени и резултати могат също да бъдат изтрити каскадно 
    (в зависимост от конфигурацията на базата данни).
    Затова операцията е ограничена само до 'admin'.
    """
    db_region = crud_region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    crud_region.delete(db=db, id=region_id)
    return None
