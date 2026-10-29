"""Deterministic, idempotent synthetic seed data. Never use real student data here."""
import random
from datetime import date, timedelta
from sqlalchemy import select
from argon2 import PasswordHasher
from app.db.session import SessionLocal
from app.models import (Hostel, Floor, Wing, Location, Asset, AssetLocation,
                        Category, ProblemType, User, Issue, IssueUpdate, IssueConfirmation,
                        IssueResolutionFeedback, Notification)

random.seed(20261029)
SEED_DATE = date(2026, 10, 29)
DEMO_PASSWORD_HASH = PasswordHasher().hash("HostelFix-Demo-2026!")
AREAS = ["toilet", "bathroom", "washing_machine_area", "cloth_drying_area", "corridor", "lift_lobby", "drinking_water_area", "room"]
PROBLEMS = {
    "Maintenance": [
        "Electrical", "Plumbing", "Lift malfunction", "Door/lock", "Furniture damage",
        "Water dispenser", "Washing machine", "Drainage", "Ceiling damage", "Window damage",
        "Bed repair", "Desk repair", "Chair repair", "Power socket", "Fan repair",
        "Light fixture", "Switch repair", "Internet point", "Leakage", "Other",
    ],
    "Housekeeping": [
        "Cleaning", "Waste disposal", "Water area hygiene", "Pest issue", "Toilet cleaning",
        "Bathroom cleaning", "Corridor cleaning", "Dustbin overflow", "Wet floor", "Bad odour",
        "Cloth drying area cleaning", "Washing machine area cleaning", "Drinking water area cleaning",
        "Spillage", "Cobwebs", "Stain removal", "Disinfection", "Common area cleaning",
        "Unclean lift lobby", "Other",
    ],
}
TITLES = ["Leaking tap", "Light not working", "Lift not responding", "Floor needs cleaning", "Broken door latch",
          "Water purifier issue", "Washing machine unavailable", "Drain blockage", "Waste bin full", "Damaged furniture"]
DESCRIPTIONS = ["The issue has been observed repeatedly and needs attention.",
                "This area requires maintenance. Please inspect and resolve it.",
                "The problem is affecting residents using this common area.",
                "Please arrange an inspection and update the status when work begins."]

def seed():
    db = SessionLocal()
    try:
        if db.scalar(select(Hostel.id).limit(1)):
            print("Seed data already exists; skipping.")
            return
        hostels = [Hostel(name="Hostel 1"), Hostel(name="Hostel 2")]
        db.add_all(hostels); db.flush()
        location_rows = []
        for hostel in hostels:
            for floor_no in range(1, 9):
                floor = Floor(hostel=hostel, floor_number=floor_no); db.add(floor); db.flush()
                for wing_name in ["A","B","C","D","E"]:
                    wing = Wing(floor=floor, wing_name=wing_name); db.add(wing); db.flush()
                    for area in AREAS:
                        loc = Location(wing=wing, area_type=area, description=f"{area.replace('_',' ').title()} - {hostel.name}, Floor {floor_no}, Wing {wing_name}")
                        db.add(loc); location_rows.append(loc)
        categories = [Category(name=name, description=f"{name} complaint category") for name in PROBLEMS]
        db.add_all(categories); db.flush()
        ptypes = []
        for category in categories:
            for name in PROBLEMS[category.name]:
                ptypes.append(ProblemType(category_id=category.id, name=name, requires_description=(name == "Other")))
        db.add_all(ptypes)
        users = []
        for i in range(1, 41):
            users.append(User(name=f"Demo Student {i:02d}", email=f"student{i:02d}@example.test", role="student", password_hash=DEMO_PASSWORD_HASH))
        for cat in categories:
            for staff_number in (1, 2):
                users.append(User(name=f"Demo {cat.name} Staff {staff_number}", email=f"{cat.name.lower()}-staff{staff_number}@example.test", role="staff", category_id=cat.id, password_hash=DEMO_PASSWORD_HASH))
        users.append(User(name="Demo Administrator", email="admin@example.test", role="administrator", password_hash=DEMO_PASSWORD_HASH))
        db.add_all(users)
        assets = []
        for hostel in hostels:
            for lift_number in range(1, 7):
                assets.append(Asset(hostel=hostel, name=f"Lift {lift_number}", asset_type="lift", description="Synthetic lift asset"))
        db.add_all(assets); db.flush()
        # Lift 1 serves wing A; lifts 2-3 serve B/C; lifts 4-6 serve D/E on each floor.
        for asset in assets:
            hostel_locations = [loc for loc in location_rows if loc.area_type == "lift_lobby"
                               and loc.wing.floor.hostel_id == asset.hostel_id]
            if asset.name == "Lift 1":
                target_wings = {"A"}
            elif asset.name in ("Lift 2", "Lift 3"):
                target_wings = {"B", "C"}
            else:
                target_wings = {"D", "E"}
            for loc in hostel_locations:
                if loc.wing.wing_name in target_wings:
                    db.add(AssetLocation(asset_id=asset.id, location_id=loc.id))
        db.flush()
        students = [u for u in users if u.role == "student"]
        staff = [u for u in users if u.role == "staff"]
        status_options = ["submitted", "acknowledged", "in_progress", "resolved", "closed"]
        issues = []
        for i in range(200):
            cat = random.choice(categories)
            problem = random.choice([p for p in ptypes if p.category_id == cat.id])
            loc = random.choice(location_rows)
            reporter = random.choice(students)
            status = random.choice(status_options)
            issue = Issue(title=f"{random.choice(TITLES)} #{i+1:03d}", description=random.choice(DESCRIPTIONS),
                          location_id=loc.id, problem_type_id=problem.id, reporter_id=reporter.id,
                          status=status, is_public=(i % 7 != 0),
                          room_label=(f"Room {100 + i % 30}" if loc.area_type == "room" else None),
                          service_date=(SEED_DATE - timedelta(days=i % 14) if cat.name == "Housekeeping" else None),
                          due_date=(SEED_DATE+timedelta(days=random.randint(-5,14))))
            db.add(issue); db.flush(); issues.append(issue)
            db.add(IssueUpdate(issue_id=issue.id, actor_id=reporter.id, old_status=None, new_status="submitted", comment="Synthetic initial report"))
            if status != "submitted":
                actor = next((s for s in staff if s.category_id == cat.id), staff[0])
                db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, old_status="submitted", new_status=status, comment="Synthetic status history"))
            if i % 4 == 0:
                db.add(IssueConfirmation(issue_id=issue.id, user_id=random.choice(students).id))
            if status in ("resolved","closed") and i % 3 == 0:
                db.add(IssueResolutionFeedback(issue_id=issue.id, user_id=reporter.id, outcome="resolved", comment="Synthetic feedback"))
            db.add(Notification(user_id=reporter.id, issue_id=issue.id, title="Issue update", message=f"Demo issue #{issue.id} is currently {status}.", is_read=(i % 2 == 0)))
        db.commit()
        print(f"Seeded {len(hostels)} hostels, 16 floors, 80 wings, {len(location_rows)} locations, {len(assets)} lifts, {len(users)} users and {len(issues)} issues.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
