"""/api/teams — teams and their members."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from tokenpulse.api.deps import get_session
from tokenpulse.api.schemas import MemberOut, TeamOut
from tokenpulse.db.models import Team

router = APIRouter(prefix="/api", tags=["teams"])


@router.get("/teams", response_model=list[TeamOut])
def list_teams(session: Session = Depends(get_session)) -> list[TeamOut]:
    teams = session.scalars(
        select(Team).options(selectinload(Team.members)).order_by(Team.id)
    ).all()
    return [
        TeamOut(
            id=t.id,
            name=t.name,
            members=[
                MemberOut(id=m.id, display_name=m.display_name, is_unattributed=m.is_unattributed)
                for m in sorted(t.members, key=lambda m: m.id)
            ],
        )
        for t in teams
    ]
