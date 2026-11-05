from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.routers.deps import get_actor

router = APIRouter(tags=["Profile"])

@router.get("/me")
def get_profile(actor: User = Depends(get_actor)):
    return {"id": actor.id, "name": actor.name, "email": actor.email, "role": actor.role,
            "category_id": actor.category_id, "created_at": actor.created_at}

@router.delete("/me", status_code=204)
def delete_profile(actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    actor.deleted_at = datetime.utcnow()
    db.commit()
    return None
