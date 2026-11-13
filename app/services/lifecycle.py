from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Issue, IssueUpdate, Notification, User
from app.services.security import utcnow

AUTO_CLOSE_DAYS = 7


def auto_close_resolved_issues(db: Session, now: datetime | None = None) -> int:
    now = now or utcnow()
    cutoff = now - timedelta(days=AUTO_CLOSE_DAYS)
    system_actor = (
        db.query(User)
        .filter(User.role == "administrator", User.deleted_at.is_(None))
        .order_by(User.id)
        .first()
    )
    if system_actor is None:
        return 0
    issues = (
        db.query(Issue)
        .filter(
            Issue.status == "resolved",
            Issue.resolved_at.is_not(None),
            Issue.resolved_at <= cutoff,
        )
        .all()
    )
    for issue in issues:
        issue.status = "closed"
        db.add(
            IssueUpdate(
                issue_id=issue.id,
                actor_id=system_actor.id,
                actor_role="administrator",
                old_status="resolved",
                new_status="closed",
                comment="auto-closed: no response",
                is_internal=False,
            )
        )
        db.add(
            Notification(
                user_id=issue.reporter_id,
                issue_id=issue.id,
                title="Issue auto-closed",
                message=f"Issue #{issue.id} was automatically closed after 7 days without a response.",
            )
        )
    if issues:
        db.commit()
    return len(issues)
