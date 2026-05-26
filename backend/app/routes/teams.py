from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.database import get_db
from app.core.security import get_current_user as get_current_active_user
from app.models.user import User

# Инициализиране на рутер (APIRouter) за управление на заявките, свързани с екипи (teams).
router = APIRouter(
    prefix="/teams",
    tags=["teams"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.TeamRead])
def read_teams(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Връща списък от всички екипи в системата.
    """
    # Използваме CRUD операцията за взимане на списък от екипи,
    # като поддържаме странициране чрез 'skip' и 'limit' параметрите.
    teams = crud.team.get_multi(db, skip=skip, limit=limit)
    return teams

@router.post("/", response_model=schemas.TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(
    *,
    db: Session = Depends(get_db),
    team_in: schemas.TeamCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Създава нов екип в системата.
    """
    # Първо проверяваме дали вече съществува екип с такова име.
    team = crud.team.get_by_name(db, name=team_in.name)
    if team:
        # Ако съществува, хвърляме грешка 409 Conflict.
        raise HTTPException(
            status_code=409,
            detail="The team with this name already exists in the system.",
        )
    
    # Ако името е свободно, създаваме новия екип.
    team = crud.team.create(db=db, obj_in=team_in)
    
    # Потребителят, който създава екипа, автоматично се добавя като 'admin' в него.
    # Това създава свързващ запис в таблицата TeamMembership.
    membership_in = schemas.TeamMembershipCreate(
        user_id=current_user.id,
        team_id=team.id,
        role="admin"
    )
    crud.team_membership.create(db=db, obj_in=membership_in)
    
    return team

@router.get("/{team_id}", response_model=schemas.TeamRead)
def read_team(
    *,
    db: Session = Depends(get_db),
    team_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Връща информация за конкретен екип по неговото ID.
    """
    # Търсене на екипа в базата данни
    team = crud.team.get(db=db, id=team_id)
    
    # Ако екипът не бъде открит, хвърляме изключение 404 Not Found.
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/{team_id}/members", response_model=schemas.TeamMembershipRead)
def add_team_member(
    *,
    db: Session = Depends(get_db),
    team_id: int,
    member_in: schemas.TeamMembershipCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Добавя нов потребител към съществуващ екип.
    """
    # Уверяваме се, че целевият екип съществува.
    team = crud.team.get(db=db, id=team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Проверка дали текущият потребител има право да добавя членове.
    # За момента логиката проверява дали текущият потребител е част от екипа
    # или дали има глобална роля 'admin'.
    current_membership = crud.team_membership.get_by_user_and_team(
        db, user_id=current_user.id, team_id=team_id
    )
    
    if not current_membership and not current_user.role == "admin": 
         # Тук в бъдеще може да се реализира по-строга логика: 
         # например `if not current_membership: raise 403 Forbidden`
         pass 
    
    # Проверка дали целевият потребител (когото добавяме) действително съществува в базата.
    user = crud.user.get(db=db, id=member_in.user_id)
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    # Проверка дали потребителят вече не е член на този екип.
    # Това предотвратява дублирането на членства (conflict).
    existing_membership = crud.team_membership.get_by_user_and_team(
        db, user_id=member_in.user_id, team_id=team_id
    )
    if existing_membership:
        raise HTTPException(status_code=409, detail="User is already a member of this team")

    # Създаване на нов запис за членство в екипа.
    membership = crud.team_membership.create(db=db, obj_in=member_in)
    return membership

@router.get("/{team_id}/members", response_model=List[schemas.TeamMembershipRead])
def read_team_members(
    *,
    db: Session = Depends(get_db),
    team_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Връща списък от всички членове на даден екип.
    """
    # Използваме специализиран метод, който зарежда екипа заедно с неговите членове 
    # (вероятно чрез joinedload или връзки в SQLAlchemy модела).
    team = crud.team.get_with_members(db=db, id=team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    return team.members
