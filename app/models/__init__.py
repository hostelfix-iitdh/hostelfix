from datetime import datetime, date
from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint,
    func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Hostel(Base):
    __tablename__ = "hostels"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    floors: Mapped[list["Floor"]] = relationship(back_populates="hostel", cascade="all, delete-orphan")

class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (UniqueConstraint("hostel_id", "floor_number", name="uq_floor_hostel_number"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id", ondelete="CASCADE"), index=True)
    floor_number: Mapped[int] = mapped_column(Integer)
    hostel: Mapped["Hostel"] = relationship(back_populates="floors")
    wings: Mapped[list["Wing"]] = relationship(back_populates="floor", cascade="all, delete-orphan")

class Wing(Base):
    __tablename__ = "wings"
    __table_args__ = (UniqueConstraint("floor_id", "wing_name", name="uq_wing_floor_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id", ondelete="CASCADE"), index=True)
    wing_name: Mapped[str] = mapped_column(String(5))
    floor: Mapped["Floor"] = relationship(back_populates="wings")
    locations: Mapped[list["Location"]] = relationship(back_populates="wing", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("wing_id", "area_type", name="uq_location_wing_area"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    wing_id: Mapped[int] = mapped_column(ForeignKey("wings.id", ondelete="CASCADE"), index=True)
    area_type: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wing: Mapped["Wing"] = relationship(back_populates="locations")
    issues: Mapped[list["Issue"]] = relationship(back_populates="location")

class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("hostel_id", "name", name="uq_asset_hostel_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    hostel_id: Mapped[int] = mapped_column(ForeignKey("hostels.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    asset_type: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hostel: Mapped["Hostel"] = relationship()
    locations: Mapped[list["AssetLocation"]] = relationship(back_populates="asset", cascade="all, delete-orphan")

class AssetLocation(Base):
    __tablename__ = "asset_locations"
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True)
    asset: Mapped["Asset"] = relationship(back_populates="locations")
    location: Mapped["Location"] = relationship()

class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    problem_types: Mapped[list["ProblemType"]] = relationship(back_populates="category", cascade="all, delete-orphan")

class ProblemType(Base):
    __tablename__ = "problem_types"
    __table_args__ = (UniqueConstraint("category_id", "name", name="uq_problem_type_category_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requires_description: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped["Category"] = relationship(back_populates="problem_types")
    issues: Mapped[list["Issue"]] = relationship(back_populates="problem_type")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="student")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    category: Mapped["Category | None"] = relationship()

class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_status_created", "status", "created_at"),
        Index("ix_issues_location_problem_status", "location_id", "problem_type_id", "status"),
        Index("ix_issues_problem_status", "problem_type_id", "status"),
        Index("ix_issues_due_status", "due_date", "status"),
        Index("ix_issues_reporter_created", "reporter_id", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)
    problem_type_id: Mapped[int] = mapped_column(ForeignKey("problem_types.id"), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="submitted", index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    room_label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    location: Mapped["Location"] = relationship(back_populates="issues")
    problem_type: Mapped["ProblemType"] = relationship(back_populates="issues")
    reporter: Mapped["User"] = relationship()
    updates: Mapped[list["IssueUpdate"]] = relationship(back_populates="issue", cascade="all, delete-orphan", order_by="IssueUpdate.created_at")
    confirmations: Mapped[list["IssueConfirmation"]] = relationship(back_populates="issue", cascade="all, delete-orphan")
    resolution_feedback: Mapped[list["IssueResolutionFeedback"]] = relationship(back_populates="issue", cascade="all, delete-orphan")

class IssueUpdate(Base):
    __tablename__ = "issue_updates"
    __table_args__ = (Index("ix_issue_updates_issue_created", "issue_id", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    issue: Mapped["Issue"] = relationship(back_populates="updates")
    actor: Mapped["User"] = relationship()

class IssueConfirmation(Base):
    __tablename__ = "issue_confirmations"
    __table_args__ = (UniqueConstraint("issue_id", "user_id", name="uq_confirmation_issue_user"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    issue: Mapped["Issue"] = relationship(back_populates="confirmations")
    user: Mapped["User"] = relationship()

class IssueResolutionFeedback(Base):
    __tablename__ = "issue_resolution_feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    outcome: Mapped[str] = mapped_column(String(30))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    issue: Mapped["Issue"] = relationship(back_populates="resolution_feedback")
    user: Mapped["User"] = relationship()

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    issue_id: Mapped[int | None] = mapped_column(ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(180))
    message: Mapped[str] = mapped_column(String(500))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user: Mapped["User"] = relationship()

class EmailToken(Base):
    __tablename__ = "email_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    purpose: Mapped[str] = mapped_column(String(30))
    expires_at: Mapped[datetime] = mapped_column(DateTime)

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
