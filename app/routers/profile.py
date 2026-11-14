from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.routers.deps import get_actor
from app.services.security import hash_password

router = APIRouter(tags=["Profile"])

class ProfilePatch(BaseModel):
    name: str = Field(min_length=2, max_length=120)

class ChangePassword(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=5, max_length=128)

@router.get("/me")
def get_profile(actor: User = Depends(get_actor)):
    return {"id": actor.id, "name": actor.name, "email": actor.email, "role": actor.role,
            "category_id": actor.category_id, "is_verified": actor.is_verified, "created_at": actor.created_at}

@router.patch("/me")
def update_profile(payload: ProfilePatch, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    actor.name = payload.name.strip(); db.commit(); db.refresh(actor)
    return get_profile(actor)

@router.post("/me/password")
def change_password(payload: ChangePassword, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    from app.services.security import verify_password
    if not actor.password_hash or not verify_password(payload.current_password, actor.password_hash):
        raise HTTPException(401, "Current password is incorrect")
    actor.password_hash = hash_password(payload.new_password); db.commit()
    return {"message": "Password changed successfully"}

@router.delete("/me", status_code=204)
def delete_profile(actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    # Keep complaint rows for audit/history, but remove account identifiers.
    actor.name = "Deleted user"
    actor.email = f"deleted-{actor.id}@deleted.hostelfix.invalid"
    actor.password_hash = None
    actor.google_sub = None
    actor.deleted_at = __import__("datetime").datetime.utcnow()
    db.commit()
    return None
