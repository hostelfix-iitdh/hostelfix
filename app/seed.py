"""Deterministic, idempotent synthetic seed data. Never use real student data here."""
import random
import argparse
from datetime import date, timedelta
from sqlalchemy import select
from argon2 import PasswordHasher
from app.db.session import SessionLocal
from app.core.role_credentials import ADMIN_CREDENTIALS, STAFF_CREDENTIALS
from app.models import (Hostel, Floor, Wing, Location, Asset, AssetLocation,
                        Category, ProblemType, User, Issue, IssueUpdate, IssueConfirmation,
                        IssueResolutionFeedback, Notification)

random.seed(20261029)
SEED_DATE = date(2026, 10, 29)
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
# Keep synthetic examples specific to the selected problem. These are demo descriptions,
# not copied from real residents or reports.
DETAIL_BY_PROBLEM = {
    "Electrical": "An electrical fault has been reported and needs a safe inspection.",
    "Plumbing": "A plumbing fixture is leaking or not working correctly and needs repair.",
    "Lift malfunction": "The lift is not operating normally and needs a maintenance inspection.",
    "Door/lock": "The door or lock is damaged and needs repair.",
    "Furniture damage": "The furniture is damaged and may not be safe to use.",
    "Water dispenser": "The water dispenser is not working correctly and needs maintenance.",
    "Washing machine": "The washing machine is not operating correctly and needs maintenance.",
    "Drainage": "The drain is blocked or draining slowly and needs maintenance.",
    "Power socket": "The power socket is not working and needs an electrical inspection.",
    "Fan repair": "The fan is not working correctly and needs repair.",
    "Light fixture": "The light does not turn on or flickers and needs an electrical inspection.",
    "Switch repair": "The switch is not working correctly and needs an electrical inspection.",
    "Leakage": "Water leakage has been noticed and needs inspection.",
    "Cleaning": "Dust and dirt are visible and the area needs cleaning.",
    "Waste disposal": "Waste needs to be collected and disposed of correctly.",
    "Water area hygiene": "The drinking-water area needs cleaning and a hygiene inspection.",
    "Toilet cleaning": "The toilet area is unclean and needs cleaning and sanitation.",
    "Bathroom cleaning": "The bathroom needs cleaning and sanitation.",
    "Corridor cleaning": "The corridor needs sweeping and mopping.",
    "Dustbin overflow": "The bin is full and waste needs to be collected.",
    "Wet floor": "The floor is wet and needs attention to reduce slip risk.",
    "Bad odour": "An unpleasant odour has been noticed and the area needs inspection and cleaning.",
    "Cloth drying area cleaning": "The cloth-drying area needs cleaning.",
    "Washing machine area cleaning": "The washing-machine area needs cleaning; this is a housekeeping request, not a machine repair.",
    "Drinking water area cleaning": "The drinking-water area needs cleaning; the dispenser itself is not being reported as faulty.",
    "Unclean lift lobby": "The lift lobby needs cleaning; this is a housekeeping request, not a lift repair.",
    "Pest issue": "A pest has been noticed and the area needs inspection and appropriate pest control.",
    "Other": "Please inspect the reported issue and determine the appropriate action.",
}

# Keep synthetic examples semantically aligned with their category, problem type and location.
AREA_BY_PROBLEM = {
    "Electrical": ["room", "corridor"], "Plumbing": ["toilet", "bathroom", "room"],
    "Lift malfunction": ["lift_lobby"], "Door/lock": ["room", "corridor"],
    "Furniture damage": ["room"], "Water dispenser": ["drinking_water_area"],
    "Washing machine": ["washing_machine_area"], "Drainage": ["toilet", "bathroom"],
    "Ceiling damage": ["room", "corridor"], "Window damage": ["room"],
    "Bed repair": ["room"], "Desk repair": ["room"], "Chair repair": ["room"],
    "Power socket": ["room", "corridor"], "Fan repair": ["room"],
    "Light fixture": ["room", "corridor", "lift_lobby"], "Switch repair": ["room", "corridor"],
    "Internet point": ["room"], "Leakage": ["toilet", "bathroom", "room"],
    "Cleaning": ["room", "corridor", "bathroom", "toilet"], "Waste disposal": ["corridor", "cloth_drying_area"],
    "Water area hygiene": ["drinking_water_area"], "Pest issue": ["room", "corridor", "toilet", "bathroom"],
    "Toilet cleaning": ["toilet"], "Bathroom cleaning": ["bathroom"],
    "Corridor cleaning": ["corridor"], "Dustbin overflow": ["corridor", "cloth_drying_area"],
    "Wet floor": ["bathroom", "toilet", "corridor"], "Bad odour": ["toilet", "bathroom", "drinking_water_area"],
    "Cloth drying area cleaning": ["cloth_drying_area"], "Washing machine area cleaning": ["washing_machine_area"],
    "Drinking water area cleaning": ["drinking_water_area"], "Spillage": ["corridor", "bathroom", "drinking_water_area"],
    "Cobwebs": ["room", "corridor", "lift_lobby"], "Stain removal": ["room", "corridor", "bathroom"],
    "Disinfection": ["toilet", "bathroom", "room"], "Common area cleaning": ["corridor", "lift_lobby", "cloth_drying_area"],
    "Unclean lift lobby": ["lift_lobby"], "Other": AREAS,
}

def title_for(problem_name, area):
    titles = {
        "Electrical": "Electrical fault", "Plumbing": "Plumbing leak", "Lift malfunction": "Lift not working",
        "Door/lock": "Door lock needs repair", "Furniture damage": "Damaged furniture",
        "Water dispenser": "Water dispenser not working", "Washing machine": "Washing machine repair required",
        "Drainage": "Drain blockage", "Ceiling damage": "Ceiling damage reported", "Window damage": "Window needs repair",
        "Bed repair": "Bed frame needs repair", "Desk repair": "Desk needs repair", "Chair repair": "Chair needs repair",
        "Power socket": "Power socket not working", "Fan repair": "Fan not working", "Light fixture": "Light fixture not working",
        "Switch repair": "Switch not working", "Internet point": "Internet point not working", "Leakage": "Water leakage reported",
        "Cleaning": "Cleaning required", "Waste disposal": "Waste disposal required", "Water area hygiene": "Drinking water area hygiene",
        "Pest issue": "Pest issue reported", "Toilet cleaning": "Toilet cleaning required", "Bathroom cleaning": "Bathroom cleaning required",
        "Corridor cleaning": "Corridor cleaning required", "Dustbin overflow": "Dustbin needs emptying", "Wet floor": "Wet floor needs attention",
        "Bad odour": "Unpleasant odour reported", "Cloth drying area cleaning": "Cloth drying area cleaning required",
        "Washing machine area cleaning": "Washing machine area cleaning required", "Drinking water area cleaning": "Drinking water area cleaning required",
        "Spillage": "Spillage needs cleaning", "Cobwebs": "Cobweb removal required", "Stain removal": "Stain removal required",
        "Disinfection": "Disinfection required", "Common area cleaning": "Common area cleaning required",
        "Unclean lift lobby": "Lift lobby cleaning required", "Other": "Other hostel issue",
    }
    return titles.get(problem_name, f"{problem_name} issue")

def seed(reset_issues=False):
    db = SessionLocal()
    try:
        if db.scalar(select(Hostel.id).limit(1)):
            if not reset_issues:
                for u in db.query(User).all():
                    if u.email.endswith("@example.test"):
                        u.email = u.email.replace("@example.test", "@iitdh.ac.in")
                    u.is_verified = True
                    if u.role == "student":
                        # Student accounts must use Google Sign-In only.
                        u.password_hash = None
                fixed_accounts = [ADMIN_CREDENTIALS, *STAFF_CREDENTIALS]
                for account in fixed_accounts:
                    user = db.query(User).filter(User.email == account["email"], User.deleted_at.is_(None)).first()
                    if user:
                        user.password_hash = account["password_hash"]
                        user.is_verified = True
                db.commit()
                print("Seed data already exists; ensured demo accounts are verified.")
                return
            # This is a demo-only reset: rebuild all deterministic synthetic data cleanly.
            for model in (Notification, IssueResolutionFeedback, IssueConfirmation, IssueUpdate, Issue,
                          AssetLocation, Asset, Location, Wing, Floor, Hostel, User, ProblemType, Category):
                db.query(model).delete(synchronize_session=False)
            db.commit()
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
        categories = [Category(name=name, description=f"{name} complaint category", resolution_target_hours=72 if name == "Housekeeping" else 120) for name in PROBLEMS]
        db.add_all(categories); db.flush()
        ptypes = []
        for category in categories:
            for name in PROBLEMS[category.name]:
                ptypes.append(ProblemType(category_id=category.id, name=name, requires_description=(name == "Other")))
        db.add_all(ptypes)
        users = []
        # Students authenticate only with Google. Their passwords are intentionally NULL.
        for i in range(1, 41):
            users.append(User(name=f"Demo Student {i:02d}", email=f"student{i:02d}@iitdh.ac.in", role="student", password_hash=None, is_verified=True))

        category_by_name = {category.name: category for category in categories}
        for account in STAFF_CREDENTIALS:
            category = category_by_name[account["category"]]
            users.append(User(
                name=account["name"],
                email=account["email"],
                role="staff",
                category_id=category.id,
                password_hash=account["password_hash"],
                is_verified=True,
            ))

        users.append(User(
            name=ADMIN_CREDENTIALS["name"],
            email=ADMIN_CREDENTIALS["email"],
            role="administrator",
            password_hash=ADMIN_CREDENTIALS["password_hash"],
            is_verified=True,
        ))
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
            problem = random.choice(ptypes)
            category = problem.category
            compatible_areas = AREA_BY_PROBLEM.get(problem.name, AREAS)
            eligible_locations = [loc for loc in location_rows if loc.area_type in compatible_areas]
            loc = random.choice(eligible_locations or location_rows)
            reporter = random.choice(students)
            status = random.choice(status_options)
            issue_title = f"{title_for(problem.name, loc.area_type)} #{i+1:03d}"
            area_name = loc.area_type.replace("_", " ")
            detail = DETAIL_BY_PROBLEM.get(
                problem.name,
                f"{problem.name} has been reported and needs appropriate attention.",
            )
            description = f"{detail} Location: {area_name}."
            issue = Issue(title=issue_title, description=description,
                          location_id=loc.id, problem_type_id=problem.id, reporter_id=reporter.id,
                          status=status, is_public=(i % 7 != 0),
                          room_label=(f"Room {100 + i % 30}" if loc.area_type == "room" else None),
                          service_date=(SEED_DATE - timedelta(days=i % 14) if category.name == "Housekeeping" else None),
                          due_date=(SEED_DATE+timedelta(days=random.randint(-5,14))))
            db.add(issue); db.flush(); issues.append(issue)
            db.add(IssueUpdate(issue_id=issue.id, actor_id=reporter.id, actor_role=reporter.role, old_status=None, new_status="submitted", comment="Synthetic initial report"))
            if status != "submitted":
                actor = next((staff_user for staff_user in staff if staff_user.category_id == category.id), staff[0])
                db.add(IssueUpdate(issue_id=issue.id, actor_id=actor.id, actor_role=actor.role, old_status="submitted", new_status=status, comment="Synthetic status history"))
            if i % 4 == 0:
                other_students = [student for student in students if student.id != reporter.id]
                if other_students:
                    db.add(IssueConfirmation(issue_id=issue.id, user_id=random.choice(other_students).id))
            if status in ("resolved", "closed") and i % 3 == 0:
                db.add(IssueResolutionFeedback(issue_id=issue.id, user_id=reporter.id, outcome="resolved", comment="Synthetic feedback"))
            db.add(Notification(user_id=reporter.id, issue_id=issue.id, title="Issue update", message=f"Demo issue #{i+1:03d} is currently {status}.", is_read=(i % 2 == 0)))
        db.commit()
        print(f"Seeded {len(hostels)} hostels, 16 floors, 80 wings, {len(location_rows)} locations, {len(assets)} lifts, {len(users)} users and {len(issues)} issues.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed synthetic HostelFix demo data")
    parser.add_argument("--reset-demo-issues", action="store_true", help="rebuild all synthetic demo data, including the 200 sample issues")
    args = parser.parse_args()
    seed(reset_issues=args.reset_demo_issues)
