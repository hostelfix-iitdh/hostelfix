from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Session as UserSession
from app.models import User
from app.services.security import token_hash, utcnow


def get_actor(
    request: Request,
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    raw = request.cookies.get("hf_session")
    if raw:
        session = (
            db.query(UserSession)
            .filter(UserSession.token_hash == token_hash(raw), UserSession.expires_at > utcnow())
            .first()
        )
        if session:
            user = db.get(User, session.user_id)
            if user and not user.deleted_at:
                return user
    if settings.environment != "production" and x_user_id is not None:
        user = db.get(User, x_user_id)
        if user and not user.deleted_at:
            return user
    raise HTTPException(401, "Authentication required")


def require_csrf(request: Request):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    cookie = request.cookies.get("hf_csrf")
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or cookie != header:
        raise HTTPException(403, "CSRF validation failed")


def require_role(*roles):
    def checker(user: User = Depends(get_actor)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role for this operation.")
        return user

    return checker
