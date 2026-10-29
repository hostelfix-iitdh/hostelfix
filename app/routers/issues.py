from datetime import datetime, timedelta
import re
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Issue, IssueUpdate, IssueConfirmation, IssueResolutionFeedback, Location, ProblemType, Notification, User
from app.schemas.issue import IssueCreate, IssuePatch, IssueOut, StaffIssueOut, IssueUpdateOut, StatusUpdate, ResolutionFeedbackCreate
from app.routers.deps import get_actor, require_role

router = APIRouter(tags=["Issues"])
@router.get("/issues")
def list_issues(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                status: str | None = Query(None, pattern="^(submitted|acknowledged|in_progress|resolved|closed|reopened)$"), location_id: int | None = Query(None, ge=1), problem_type_id: int | None = Query(None, ge=1),
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
@router.post("/issues", response_model=IssueOut, status_code=201)
def create_issue(payload: IssueCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    location = db.get(Location, payload.location_id)
    if not location: raise HTTPException(422, "Unknown location_id")
    problem_type = db.get(ProblemType, payload.problem_type_id)
    if not problem_type: raise HTTPException(422, "Unknown problem_type_id")
    if payload.room_label and location.area_type != "room": raise HTTPException(422, "room_label is only allowed for Room-area complaints")
    if payload.service_date and problem_type.category.name != "Housekeeping": raise HTTPException(422, "service_date is only allowed for housekeeping complaints")
    # Prevent repeated Swagger/browser submissions from creating identical complaints.
    # A short window avoids blocking a genuinely recurring issue reported later.
    cutoff = datetime.now() - timedelta(minutes=10)
    candidates = (db.query(Issue)
                  .filter(Issue.reporter_id == actor.id,
                          Issue.location_id == payload.location_id,
                          Issue.problem_type_id == payload.problem_type_id,
                          Issue.status.in_(("submitted", "acknowledged", "in_progress", "reopened")),
                          Issue.created_at >= cutoff)
                  .order_by(Issue.created_at.desc(), Issue.id.desc())
                  .limit(25).all())
    normalize = lambda value: re.sub(r"\s+", " ", value or "").strip().casefold()
    for existing in candidates:
        if (normalize(existing.title) == normalize(payload.title)
                and normalize(existing.description) == normalize(payload.description)
                and existing.room_label == payload.room_label
                and existing.service_date == payload.service_date
                and existing.is_public == payload.is_public):
            raise HTTPException(409, f"Duplicate complaint detected. Reuse existing issue ID {existing.id} instead of creating another.")

    issue = Issue(**payload.model_dump(), reporter_id=actor.id, status="submitted")
    db.add(issue); db.flush()
    db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, old_status=None, new_status="submitted", comment="Issue submitted"))
    db.commit(); db.refresh(issue)
    return issue
@router.get("/issues/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue or (not issue.is_public): raise HTTPException(404, "Issue not found")
    return issue
@router.patch("/issues/{issue_id}", response_model=IssueOut)
def patch_issue(issue_id: int, payload: IssuePatch, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if issue.reporter_id != actor.id: raise HTTPException(403, "Only the reporter may edit this issue")
    if issue.status not in ("submitted", "acknowledged"): raise HTTPException(409, "Issue can no longer be edited")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(422, "Provide at least one field to update")
    for required_field in ("title", "description", "location_id", "problem_type_id"):
        if required_field in data and data[required_field] is None:
            raise HTTPException(422, f"{required_field} cannot be null")
    if "location_id" in data and not db.get(Location, data["location_id"]):
        raise HTTPException(422, "Unknown location_id")
    target_location = db.get(Location, data.get("location_id", issue.location_id))
    if "problem_type_id" in data and not db.get(ProblemType, data["problem_type_id"]):
        raise HTTPException(422, "Unknown problem_type_id")
    target_problem = db.get(ProblemType, data.get("problem_type_id", issue.problem_type_id))
    final_room_label = data.get("room_label", issue.room_label)
    final_service_date = data.get("service_date", issue.service_date)
    if final_room_label and target_location.area_type != "room":
        raise HTTPException(422, "Clear room_label when moving a complaint away from a Room area")
    if final_service_date and target_problem.category.name != "Housekeeping":
        raise HTTPException(422, "Clear service_date when changing to a non-housekeeping problem type")
    for key, value in data.items(): setattr(issue, key, value)
    db.commit(); db.refresh(issue); return issue
@router.get("/issues/{issue_id}/updates")
def issue_updates(issue_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue or not issue.is_public: raise HTTPException(404, "Issue not found")
    query = db.query(IssueUpdate).filter_by(issue_id=issue_id, is_internal=False)
    total = query.count()
    items = query.order_by(IssueUpdate.created_at, IssueUpdate.id).offset((page - 1) * size).limit(size).all()
    return {"items": [IssueUpdateOut.model_validate(x).model_dump(mode="json") for x in items], "page": page, "size": size, "total": total}
@router.post("/issues/{issue_id}/confirmations", status_code=201)
def confirm_issue(issue_id: int, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue or not issue.is_public: raise HTTPException(404, "Issue not found")
    existing = db.query(IssueConfirmation).filter_by(issue_id=issue_id, user_id=actor.id).first()
    if existing: raise HTTPException(409, "You have already confirmed this issue")
    db.add(IssueConfirmation(issue_id=issue_id, user_id=actor.id)); db.commit()
    count = db.query(IssueConfirmation).filter_by(issue_id=issue_id).count()
    return {"issue_id": issue_id, "confirmed": True, "confirmation_count": count}
@router.delete("/issues/{issue_id}/confirmations", status_code=204)
def unconfirm_issue(issue_id: int, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue or not issue.is_public: raise HTTPException(404, "Issue not found")
    row = db.query(IssueConfirmation).filter_by(issue_id=issue_id, user_id=actor.id).first()
    if not row: raise HTTPException(404, "Confirmation not found")
    db.delete(row); db.commit(); return Response(status_code=204)
@router.post("/issues/{issue_id}/resolution-feedback", status_code=201)
def resolution_feedback(issue_id: int, payload: ResolutionFeedbackCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if issue.reporter_id != actor.id: raise HTTPException(403, "Only the reporter may submit resolution feedback")
    if issue.status not in ("resolved", "closed"):
        raise HTTPException(409, "Resolution feedback is available only after an issue is resolved or closed")
    existing_feedback = db.query(IssueResolutionFeedback).filter_by(issue_id=issue_id, user_id=actor.id).first()
    if existing_feedback:
        raise HTTPException(409, "Resolution feedback has already been submitted for this issue")
    feedback = IssueResolutionFeedback(issue_id=issue_id, user_id=actor.id, **payload.model_dump())
    db.add(feedback)
    if payload.outcome == "reopen_requested":
        old = issue.status; issue.status = "reopened"
        db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, old_status=old, new_status="reopened", comment=payload.comment or "Reopen requested"))
    db.commit()
    return {"id": feedback.id, "issue_id": issue_id, "outcome": feedback.outcome}
@router.get("/staff/issues")
def staff_queue(status: str | None = Query(None, pattern="^(submitted|acknowledged|in_progress|resolved|closed|reopened)$"), page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50),
                actor: User = Depends(require_role("staff", "administrator")), db: Session = Depends(get_db)):
    query = db.query(Issue)
    if actor.role == "staff":
        if actor.category_id is None:
            raise HTTPException(403, "Staff account has no assigned category")
        query = query.join(ProblemType).filter(ProblemType.category_id == actor.category_id)
    if status: query = query.filter(Issue.status == status)
    total = query.count()
    items = query.order_by(Issue.created_at.desc(), Issue.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"items": [StaffIssueOut.model_validate(x).model_dump(mode="json") for x in items], "page": page, "size": size, "total": total}
@router.patch("/staff/issues/{issue_id}/status", response_model=StaffIssueOut)
def update_status(issue_id: int, payload: StatusUpdate, actor: User = Depends(require_role("staff", "administrator")), db: Session = Depends(get_db)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(404, "Issue not found")
    if actor.role == "staff":
        if actor.category_id is None:
            raise HTTPException(403, "Staff account has no assigned category")
        if actor.category_id != issue.problem_type.category_id:
            raise HTTPException(403, "Issue belongs to another staff category")
    allowed_transitions = {
        "submitted": {"acknowledged", "in_progress"},
        "acknowledged": {"in_progress", "resolved"},
        "in_progress": {"resolved"},
        "resolved": {"closed", "reopened"},
        "closed": {"reopened"},
        "reopened": {"acknowledged", "in_progress"},
    }
    if payload.status == issue.status:
        raise HTTPException(409, "Issue already has this status")
    if payload.status not in allowed_transitions.get(issue.status, set()):
        raise HTTPException(409, f"Invalid status transition: {issue.status} -> {payload.status}")
    old = issue.status; issue.status = payload.status
    db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, old_status=old, new_status=payload.status, comment=payload.comment, is_internal=payload.is_internal))
    db.add(Notification(user_id=issue.reporter_id, issue_id=issue.id, title="Issue status updated", message=f"Issue #{issue.id} status changed to {payload.status}."))
    db.commit(); db.refresh(issue); return issue
