from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User

def get_actor(x_user_id: int = Header(..., alias="X-User-Id"), db: Session = Depends(get_db)) -> User:
    """Development-only identity shim. Replace with real authentication before production."""
    user = db.get(User, x_user_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=401, detail="Unknown development user; provide a valid X-User-Id.")
    return user

def require_role(*roles):
    def checker(user: User = Depends(get_actor)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role for this operation.")
        return user
    return checker
