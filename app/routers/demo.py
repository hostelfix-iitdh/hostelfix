"""Development-only endpoints for selecting synthetic demo identities."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User

router = APIRouter(tags=["development demo"])


@router.get("/demo-users")
def list_demo_users(db: Session = Depends(get_db)):
    """Return synthetic demo accounts without exposing password hashes.

    This endpoint is for local coursework demonstrations only. Disable it in production.
    """
    users = (
        db.query(User)
        .filter(User.email.like("%@example.test"), User.deleted_at.is_(None))
        .order_by(User.role, User.id)
        .all()
    )
    return {
        "items": [
            {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
            for user in users
        ]
    }
