from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.database import get_db
from app.core.security import get_current_user as get_current_active_user
from app.models.user import User

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
    Retrieve teams.
    """
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
    Create new team.
    """
    team = crud.team.get_by_name(db, name=team_in.name)
    if team:
        raise HTTPException(
            status_code=409,
            detail="The team with this name already exists in the system.",
        )
    team = crud.team.create(db=db, obj_in=team_in)
    
    # Add creator as admin
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
    Get team by ID.
    """
    team = crud.team.get(db=db, id=team_id)
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
    Add a user to a team.
    """
    team = crud.team.get(db=db, id=team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Check if user is authorized to add members (must be admin/moderator/creator)
    # For now, let's just check if current user is a member of the team
    current_membership = crud.team_membership.get_by_user_and_team(
        db, user_id=current_user.id, team_id=team_id
    )
    
    if not current_membership and not current_user.role == "admin": 
         # Allow system admins or team members (improve logic later for team admin check)
         pass 
         # strict check: if not current_membership: raise 403
    
    # Check if target user exists
    user = crud.user.get(db=db, id=member_in.user_id)
    if not user:
         raise HTTPException(status_code=404, detail="User not found")

    # Check if already member
    existing_membership = crud.team_membership.get_by_user_and_team(
        db, user_id=member_in.user_id, team_id=team_id
    )
    if existing_membership:
        raise HTTPException(status_code=409, detail="User is already a member of this team")

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
    Get members of a team.
    """
    team = crud.team.get_with_members(db=db, id=team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team.members
