from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.crud.base import CRUDBase
from app.models.team import Team, TeamMembership
from app.schemas import TeamCreate, TeamUpdate, TeamMembershipCreate, TeamMembershipUpdate


class CRUDTeam(CRUDBase[Team]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Team]:
        return db.query(Team).filter(Team.name == name).first()
    
    def get_multi_with_members(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Team]:
        return (
            db.query(Team)
            .options(joinedload(Team.members).joinedload(TeamMembership.user))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_with_members(self, db: Session, id: int) -> Optional[Team]:
        return (
            db.query(Team)
            .options(joinedload(Team.members).joinedload(TeamMembership.user))
            .filter(Team.id == id)
            .first()
        )


class CRUDTeamMembership(CRUDBase[TeamMembership]):
    def get_by_user_and_team(
        self, db: Session, *, user_id: int, team_id: int
    ) -> Optional[TeamMembership]:
        return (
            db.query(TeamMembership)
            .filter(TeamMembership.user_id == user_id, TeamMembership.team_id == team_id)
            .first()
        )

team = CRUDTeam(Team)
team_membership = CRUDTeamMembership(TeamMembership)
