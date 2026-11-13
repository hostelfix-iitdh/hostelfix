from fastapi import APIRouter, Depends, HTTPException, Query, Response, Header
from sqlalchemy import or_, and_
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Issue, IssueUpdate, IssueConfirmation, IssueResolutionFeedback, Location, ProblemType, Notification, User, Asset, AssetLocation, Category
from app.schemas.issue import IssueCreate, IssuePatch, IssueOut, StaffIssueOut, IssueUpdateOut, StatusUpdate, ResolutionFeedbackCreate
from app.routers.deps import get_actor, require_role
from app.core.taxonomy import validate_problem_location
from app.services.security import utcnow

router = APIRouter(tags=["Issues"])

ALLOWED_TRANSITIONS = {
    "submitted": {"acknowledged", "rejected"},
    "acknowledged": {"rejected", "in_progress"},
    "in_progress": {"resolved"},
    "resolved": {"closed", "reopened"},
    "reopened": {"in_progress"},
    "closed": set(),
    "rejected": set(),
}

OPEN_SIMILAR_STATUSES = {"submitted", "acknowledged", "in_progress", "reopened"}

def _validate_asset_location(db: Session, asset_id: int | None, location_id: int) -> None:
    if asset_id is None:
        return
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(422, "Unknown asset_id")
    if not db.query(AssetLocation).filter_by(asset_id=asset_id, location_id=location_id).first():
        raise HTTPException(422, "The selected asset does not serve the selected location")

def _due_date_for(db: Session, problem_type_id: int) -> datetime.date:
    problem = db.get(ProblemType, problem_type_id)
    hours = problem.category.resolution_target_hours if problem and problem.category else 168
    return (utcnow() + timedelta(hours=hours)).date()
@router.get("/issues")
def list_issues(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                status: str | None = None, location_id: int | None = None, problem_type_id: int | None = None,
                q: str | None = Query(None, max_length=100), db: Session = Depends(get_db)):
    query = db.query(Issue).filter(Issue.is_public.is_(True))
    if status: query = query.filter(Issue.status == status)
    if location_id: query = query.filter(Issue.location_id == location_id)
    if problem_type_id: query = query.filter(Issue.problem_type_id == problem_type_id)
    if q: query = query.filter(or_(Issue.title.ilike(f"%{q}%"), Issue.description.ilike(f"%{q}%")))
    total = query.count()
    items = query.order_by(Issue.created_at.desc(), Issue.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"items": [IssueOut.model_validate(x).model_dump(mode="json") for x in items],
            "page": page, "size": size, "total": total}

@router.get("/my/issues")
def my_issues(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
              status: str | None = None, db: Session = Depends(get_db), actor: User = Depends(get_actor)):
    query = db.query(Issue).filter(Issue.reporter_id == actor.id)
    if status:
        query = query.filter(Issue.status == status)
    total = query.count()
    items = query.order_by(Issue.created_at.desc(), Issue.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"items": [IssueOut.model_validate(x).model_dump(mode="json") for x in items],
            "page": page, "size": size, "total": total}

@router.get("/issues/{issue_id}/confirmations")
def confirmation_summary(issue_id: int, db: Session = Depends(get_db), actor: User = Depends(get_actor)):
    issue = db.get(Issue, issue_id)
    if not issue or not issue.is_public:
        raise HTTPException(404, "Issue not found")
    query = db.query(IssueConfirmation).filter_by(issue_id=issue_id)
    return {"issue_id": issue_id, "count": query.count(),
            "confirmed": query.filter_by(user_id=actor.id).first() is not None,
            "is_reporter": issue.reporter_id == actor.id}

@router.get("/issues/similar")
def similar_issues(location_id: int = Query(..., gt=0), problem_type_id: int = Query(..., gt=0),
                   service_date: date | None = None, db: Session = Depends(get_db), actor: User = Depends(get_actor)):
    """Return open, non-room complaints matching the exact location and problem type."""
    location = db.get(Location, location_id)
    problem = db.get(ProblemType, problem_type_id)
    if not location or not problem:
        raise HTTPException(422, "Unknown location or problem type")
    if location.area_type == "room":
        return {"items": [], "reason": "Similar-complaint matching is disabled for Room-area reports."}
    query = db.query(Issue).join(Location, Issue.location_id == Location.id).filter(
        Issue.is_public.is_(True), Issue.location_id == location_id,
        Issue.problem_type_id == problem_type_id, Issue.status.in_(OPEN_SIMILAR_STATUSES),
        Issue.reporter_id != actor.id
    )
    if problem.category.name == "Housekeeping" and service_date:
        query = query.filter(Issue.service_date == service_date)
    items = query.order_by(Issue.created_at.desc(), Issue.id.desc()).limit(5).all()
    return {"items": [IssueOut.model_validate(x).model_dump(mode="json") for x in items]}

@router.post("/issues", response_model=IssueOut, status_code=201)
def create_issue(payload: IssueCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    location = db.get(Location, payload.location_id)
    if not location: raise HTTPException(422, "Unknown location_id")
    problem_type = db.get(ProblemType, payload.problem_type_id)
    if not problem_type: raise HTTPException(422, "Unknown problem_type_id")
    _validate_asset_location(db, payload.asset_id, payload.location_id)
    validate_problem_location(problem_type, location)
    if payload.room_label and location.area_type != "room": raise HTTPException(422, "room_label is only allowed for Room-area complaints")
    if payload.service_date and problem_type.category.name != "Housekeeping": raise HTTPException(422, "service_date is only allowed for housekeeping complaints")
    issue = Issue(**payload.model_dump(), reporter_id=actor.id, status="submitted", due_date=_due_date_for(db, payload.problem_type_id))
    db.add(issue); db.flush()
    db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, actor_role=actor.role, old_status=None, new_status="submitted", comment="Issue submitted"))
    db.commit(); db.refresh(issue)
    return issue
@router.get("/issues/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db), x_user_id: int | None = Header(default=None, alias="X-User-Id")):
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found")
    if not issue.is_public:
        actor = db.get(User, x_user_id) if x_user_id is not None else None
        allowed = bool(actor and not actor.deleted_at and (issue.reporter_id == actor.id or actor.role == "administrator" or
                       (actor.role == "staff" and actor.category_id == issue.problem_type.category_id)))
        if not allowed:
            raise HTTPException(404, "Issue not found")
    return issue
@router.patch("/issues/{issue_id}", response_model=IssueOut)
def patch_issue(issue_id: int, payload: IssuePatch, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if issue.reporter_id != actor.id: raise HTTPException(403, "Only the reporter may edit this issue")
    if issue.status != "submitted":
        raise HTTPException(409, "A complaint can only be edited before it is acknowledged")
    data = payload.model_dump(exclude_unset=True)
    if "location_id" in data and data["location_id"] is None:
        raise HTTPException(422, "location_id cannot be null")
    if "problem_type_id" in data and data["problem_type_id"] is None:
        raise HTTPException(422, "problem_type_id cannot be null")

    target_location = db.get(Location, data.get("location_id", issue.location_id))
    if target_location is None:
        raise HTTPException(422, "Unknown location_id")

    target_problem = db.get(ProblemType, data.get("problem_type_id", issue.problem_type_id))
    if target_problem is None:
        raise HTTPException(422, "Unknown problem_type_id")

    validate_problem_location(target_problem, target_location)
    _validate_asset_location(db, data.get("asset_id", issue.asset_id), target_location.id)

    # Clear location/category-specific fields when an edit makes them irrelevant.
    if target_location.area_type != "room":
        data["room_label"] = None
    elif "room_label" in data and data["room_label"] == "":
        data["room_label"] = None

    if target_problem.category.name != "Housekeeping":
        data["service_date"] = None

    for key, value in data.items():
        setattr(issue, key, value)
    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/issues/{issue_id}", status_code=204)
def delete_issue(
    issue_id: int,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
):
    """Allow a reporter to withdraw a complaint only before staff acknowledge it."""
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    if issue.reporter_id != actor.id:
        raise HTTPException(403, "Only the reporter may delete this complaint")
    if issue.status != "submitted":
        raise HTTPException(409, "A complaint cannot be deleted after it is acknowledged")

    db.delete(issue)
    db.commit()
    return Response(status_code=204)
@router.get("/issues/{issue_id}/updates")
def issue_updates(issue_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                  db: Session = Depends(get_db), x_user_id: int | None = Header(default=None, alias="X-User-Id")):
    issue = db.get(Issue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found")
    if not issue.is_public:
        actor = db.get(User, x_user_id) if x_user_id is not None else None
        allowed = bool(actor and not actor.deleted_at and (issue.reporter_id == actor.id or actor.role == "administrator" or
                       (actor.role == "staff" and actor.category_id == issue.problem_type.category_id)))
        if not allowed:
            raise HTTPException(404, "Issue not found")
    query = db.query(IssueUpdate).filter_by(issue_id=issue_id, is_internal=False)
    total = query.count()
    items = query.order_by(IssueUpdate.created_at, IssueUpdate.id).offset((page - 1) * size).limit(size).all()
    return {"items": [IssueUpdateOut.model_validate(x).model_dump(mode="json") for x in items], "page": page, "size": size, "total": total}
@router.post("/issues/{issue_id}/confirmations", status_code=201)
def confirm_issue(issue_id: int, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue or not issue.is_public: raise HTTPException(404, "Issue not found")
    if issue.status != "submitted":
        raise HTTPException(409, "Me too confirmations are only available while the complaint is submitted")
    if issue.location.area_type == "room":
        raise HTTPException(409, "Me too confirmations are disabled for Room-area complaints")
    if issue.reporter_id == actor.id:
        raise HTTPException(403, "You cannot confirm your own report")
    existing = db.query(IssueConfirmation).filter_by(issue_id=issue_id, user_id=actor.id).first()
    if existing: raise HTTPException(409, "You have already confirmed this issue")
    db.add(IssueConfirmation(issue_id=issue_id, user_id=actor.id)); db.commit()
    count = db.query(IssueConfirmation).filter_by(issue_id=issue_id).count()
    return {"issue_id": issue_id, "confirmed": True, "confirmation_count": count}
@router.delete("/issues/{issue_id}/confirmations", status_code=204)
def unconfirm_issue(issue_id: int, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if issue.status != "submitted":
        raise HTTPException(409, "Me too confirmations are only available while the complaint is submitted")
    if issue.location.area_type == "room":
        raise HTTPException(409, "Me too confirmations are disabled for Room-area complaints")
    row = db.query(IssueConfirmation).filter_by(issue_id=issue_id, user_id=actor.id).first()
    if not row: raise HTTPException(404, "Confirmation not found")
    db.delete(row); db.commit(); return Response(status_code=204)
@router.post("/issues/{issue_id}/resolution-feedback", status_code=201)
def resolution_feedback(issue_id: int, payload: ResolutionFeedbackCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if issue.reporter_id != actor.id: raise HTTPException(403, "Only the reporter may submit resolution feedback")
    if issue.status != "resolved":
        raise HTTPException(409, "Resolution feedback is available only for resolved complaints")
    if payload.outcome not in {"resolved", "reopen_requested"}:
        raise HTTPException(422, "Choose either confirm the fix or request reopening")
    feedback = IssueResolutionFeedback(issue_id=issue_id, user_id=actor.id, outcome=payload.outcome, comment=payload.comment)
    db.add(feedback)
    old = issue.status
    new_status = "closed" if payload.outcome == "resolved" else "reopened"
    issue.status = new_status
    if new_status == "closed":
        issue.resolved_at = None
        comment = payload.comment or "Reporter confirmed the resolution"
    else:
        comment = payload.comment or "Reporter requested reopening"
    db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, actor_role=actor.role, old_status=old, new_status=new_status, comment=comment))
    db.add(Notification(user_id=issue.reporter_id, issue_id=issue.id, title="Issue status updated", message=f"Issue #{issue.id} is now {new_status.replace('_', ' ')}."))
    db.commit()
    return {"id": feedback.id, "issue_id": issue_id, "outcome": payload.outcome, "status": new_status}

@router.get("/staff/issues")
def staff_queue(status: str | None = None, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                actor: User = Depends(require_role("staff", "administrator")), db: Session = Depends(get_db)):
    query = db.query(Issue)
    if actor.role == "staff" and actor.category_id:
        query = query.join(ProblemType).filter(ProblemType.category_id == actor.category_id)
    if status: query = query.filter(Issue.status == status)
    total = query.count()
    items = query.order_by(Issue.created_at.desc(), Issue.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"items": [StaffIssueOut.model_validate(x).model_dump(mode="json") for x in items], "page": page, "size": size, "total": total}
@router.patch("/staff/issues/{issue_id}/status", response_model=StaffIssueOut)
def update_status(issue_id: int, payload: StatusUpdate, actor: User = Depends(require_role("staff", "administrator")), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if actor.role == "staff" and actor.category_id != issue.problem_type.category_id: raise HTTPException(403, "Issue belongs to another staff category")
    old = issue.status
    if payload.status == old:
        raise HTTPException(409, "The complaint is already in that status")
    if payload.status not in ALLOWED_TRANSITIONS.get(old, set()):
        raise HTTPException(409, f"Invalid status transition: {old} -> {payload.status}")
    if payload.status == "rejected" and not (payload.comment or "").strip():
        raise HTTPException(422, "A rejection reason is required")
    issue.status = payload.status
    issue.resolved_at = utcnow() if payload.status == "resolved" else None
    db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, actor_role=actor.role, old_status=old, new_status=payload.status, comment=payload.comment, is_internal=payload.is_internal))
    db.add(Notification(user_id=issue.reporter_id, issue_id=issue.id, title="Issue status updated", message=f"Issue #{issue.id} status changed to {payload.status.replace('_', ' ')}."))
    db.commit(); db.refresh(issue); return issue
