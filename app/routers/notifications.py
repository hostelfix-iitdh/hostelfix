from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Notification, User
from app.routers.deps import get_actor
from app.schemas.notification import NotificationOut, MarkRead
router = APIRouter(tags=["Notifications"])
@router.get("/notifications")
def notifications(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                  actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    q = db.query(Notification).filter_by(user_id=actor.id)
    total = q.count()
    items = q.order_by(Notification.is_read.asc(), Notification.created_at.desc(), Notification.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"items":[NotificationOut.model_validate(x).model_dump(mode="json") for x in items],"page":page,"size":size,"total":total}
@router.patch("/notifications/{notification_id}", response_model=NotificationOut)
def mark_notification(notification_id: int, payload: MarkRead, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    item = db.get(Notification, notification_id)
    if not item: raise HTTPException(404, "Notification not found")
    if item.user_id != actor.id: raise HTTPException(403, "Cannot update another user's notification")
    item.is_read = payload.is_read; db.commit(); db.refresh(item); return item
