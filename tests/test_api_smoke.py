from datetime import UTC

from app.db.session import get_db
from app.models import Category, Floor, Hostel, Location, ProblemType, User, Wing


def seed_minimal(client):
    # Get the same test DB session through the dependency override.
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    h = Hostel(name="Test Hostel")
    db.add(h)
    db.flush()
    f = Floor(hostel_id=h.id, floor_number=1)
    db.add(f)
    db.flush()
    w = Wing(floor_id=f.id, wing_name="A")
    db.add(w)
    db.flush()
    loc = Location(wing_id=w.id, area_type="toilet")
    db.add(loc)
    cat = Category(name="Maintenance")
    db.add(cat)
    db.flush()
    pt = ProblemType(category_id=cat.id, name="Plumbing")
    db.add(pt)
    user = User(name="Test Student", email="student@example.test", role="student")
    db.add(user)
    db.commit()
    ids = (loc.id, pt.id, user.id)
    try:
        next(generator)
    except StopIteration:
        pass
    return ids


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_hostels_empty(client):
    response = client.get("/api/v1/hostels")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_create_and_list_issue(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    response = client.post(
        "/api/v1/issues",
        headers={"X-User-Id": str(user_id)},
        json={
            "title": "Leaking sink",
            "description": "The sink is leaking continuously.",
            "location_id": location_id,
            "problem_type_id": problem_type_id,
            "is_public": True,
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "submitted"
    listed = client.get("/api/v1/issues")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["page"] == 1
    assert listed.json()["size"] == 20
    public_issue = listed.json()["items"][0]
    assert "priority" not in public_issue
    assert "reporter_id" not in public_issue
    assert "room_label" not in public_issue


def test_catalogs_and_profile(client):
    _location_id, _problem_type_id, user_id = seed_minimal(client)
    locations = client.get("/api/v1/locations/catalog")
    assert locations.status_code == 200
    assert locations.json()["items"][0]["hostel_name"] == "Test Hostel"
    problems = client.get("/api/v1/problem-types/catalog")
    assert problems.status_code == 200
    assert problems.json()["items"][0]["category_name"] == "Maintenance"
    profile = client.get("/api/v1/me", headers={"X-User-Id": str(user_id)})
    assert profile.status_code == 200
    assert profile.json()["role"] == "student"


def test_my_issues_and_confirmation_summary(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    headers = {"X-User-Id": str(user_id)}
    created = client.post(
        "/api/v1/issues",
        headers=headers,
        json={
            "title": "Leaking shower",
            "description": "The shower is leaking continuously.",
            "location_id": location_id,
            "problem_type_id": problem_type_id,
            "is_public": True,
        },
    )
    assert created.status_code == 201
    issue_id = created.json()["id"]
    mine = client.get("/api/v1/my/issues", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["total"] == 1
    summary = client.get(f"/api/v1/issues/{issue_id}/confirmations", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["count"] == 0
    assert summary.json()["is_reporter"] is True
    own_confirmation = client.post(f"/api/v1/issues/{issue_id}/confirmations", headers=headers)
    assert own_confirmation.status_code == 403
    assert "own report" in own_confirmation.json()["error"]["message"]

    other_user = User(name="Another Student", email="another@example.test", role="student")
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    db.add(other_user)
    db.commit()
    other_id = other_user.id
    try:
        next(generator)
    except StopIteration:
        pass
    other_headers = {"X-User-Id": str(other_id)}
    other_summary = client.get(f"/api/v1/issues/{issue_id}/confirmations", headers=other_headers)
    assert other_summary.status_code == 200
    assert other_summary.json()["is_reporter"] is False
    confirmed = client.post(f"/api/v1/issues/{issue_id}/confirmations", headers=other_headers)
    assert confirmed.status_code == 201
    summary = client.get(f"/api/v1/issues/{issue_id}/confirmations", headers=other_headers)
    assert summary.json()["confirmed"] is True


def test_admin_can_create_staff_account(client):
    _location_id, _problem_type_id, _student_id = seed_minimal(client)
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    from app.models import Category, User

    category = db.query(Category).first()
    admin = User(name="Test Admin", email="admin@example.test", role="administrator")
    db.add(admin)
    db.commit()
    admin_id = admin.id
    try:
        next(generator)
    except StopIteration:
        pass
<<<<<<< HEAD
    response = client.post("/api/v1/admin/staff", headers={"X-User-Id": str(admin_id)}, json={
        "name": "Maintenance Staff", "email": "maintenance@iitdh.ac.in", "category_id": category.id
    })
=======
    response = client.post(
        "/api/v1/admin/staff",
        headers={"X-User-Id": str(admin_id)},
        json={
            "name": "Maintenance Staff",
            "email": "maintenance@iitdh.ac.in",
            "category_id": category.id,
        },
    )
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "staff"


def test_problem_type_location_mismatch_is_rejected(client):
    location_id, _, user_id = seed_minimal(client)
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    from app.models import Category, ProblemType

    maintenance = db.query(Category).filter_by(name="Maintenance").first()
    washing_machine = ProblemType(category_id=maintenance.id, name="Washing machine")
    db.add(washing_machine)
    db.commit()
    problem_id = washing_machine.id
    try:
        next(generator)
    except StopIteration:
        pass
    response = client.post(
        "/api/v1/issues",
        headers={"X-User-Id": str(user_id)},
        json={
            "title": "Washing machine repair required",
            "description": "The washing machine is not working and needs repair.",
            "location_id": location_id,
            "problem_type_id": problem_id,
            "is_public": True,
        },
    )
    assert response.status_code == 422
    assert "washing machine area" in response.json()["error"]["message"].lower()


def create_test_issue(client, *, user_id, location_id, problem_type_id, title="Leaking sink"):
    """Create a valid issue for lifecycle tests and return its response."""
    return client.post(
        "/api/v1/issues",
        headers={"X-User-Id": str(user_id)},
        json={
            "title": title,
            "description": "The sink is leaking continuously and needs repair.",
            "location_id": location_id,
            "problem_type_id": problem_type_id,
            "is_public": True,
        },
    )


def test_reporter_can_edit_submitted_issue(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    created = create_test_issue(
        client,
        user_id=user_id,
        location_id=location_id,
        problem_type_id=problem_type_id,
    )
    assert created.status_code == 201, created.text

    issue_id = created.json()["id"]
    edited = client.patch(
        f"/api/v1/issues/{issue_id}",
        headers={"X-User-Id": str(user_id)},
        json={
            "title": "Bathroom sink leaking",
            "description": "The bathroom sink has been leaking since this morning.",
        },
    )

    assert edited.status_code == 200, edited.text
    assert edited.json()["title"] == "Bathroom sink leaking"
    assert edited.json()["description"].startswith("The bathroom sink")


def test_reporter_can_delete_submitted_issue(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    created = create_test_issue(
        client,
        user_id=user_id,
        location_id=location_id,
        problem_type_id=problem_type_id,
    )
    issue_id = created.json()["id"]

    deleted = client.delete(f"/api/v1/issues/{issue_id}", headers={"X-User-Id": str(user_id)})

    assert deleted.status_code == 204
    assert client.get(f"/api/v1/issues/{issue_id}").status_code == 404


def test_complaint_cannot_be_edited_or_deleted_after_acknowledgement(client):
    location_id, problem_type_id, student_id = seed_minimal(client)
    created = create_test_issue(
        client,
        user_id=student_id,
        location_id=location_id,
        problem_type_id=problem_type_id,
    )
    issue_id = created.json()["id"]

    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    category = db.query(Category).filter_by(name="Maintenance").first()
    staff_user = User(
        name="Maintenance Staff",
        email="staff@example.test",
        role="staff",
        category_id=category.id,
    )
    db.add(staff_user)
    db.commit()
    staff_id = staff_user.id
    try:
        next(generator)
    except StopIteration:
        pass

    acknowledged = client.patch(
        f"/api/v1/staff/issues/{issue_id}/status",
        headers={"X-User-Id": str(staff_id)},
        json={"status": "acknowledged", "comment": "Assigned for review"},
    )
    assert acknowledged.status_code == 200, acknowledged.text

    student_headers = {"X-User-Id": str(student_id)}
    edited = client.patch(
        f"/api/v1/issues/{issue_id}",
        headers=student_headers,
        json={"title": "Changed complaint title"},
    )
    deleted = client.delete(f"/api/v1/issues/{issue_id}", headers=student_headers)

    assert edited.status_code == 409
    assert deleted.status_code == 409


def test_another_user_cannot_edit_or_delete_report(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    created = create_test_issue(
        client,
        user_id=user_id,
        location_id=location_id,
        problem_type_id=problem_type_id,
    )
    issue_id = created.json()["id"]

    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    other_user = User(name="Other Student", email="other@example.test", role="student")
    db.add(other_user)
    db.commit()
    other_id = other_user.id
    try:
        next(generator)
    except StopIteration:
        pass

    headers = {"X-User-Id": str(other_id)}
    edited = client.patch(
        f"/api/v1/issues/{issue_id}",
        headers=headers,
        json={"title": "Not my complaint"},
    )
    deleted = client.delete(f"/api/v1/issues/{issue_id}", headers=headers)

    assert edited.status_code == 403
    assert deleted.status_code == 403

<<<<<<< HEAD
def test_similar_open_complaints_endpoint_and_room_exclusion(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    created = create_test_issue(client, user_id=user_id, location_id=location_id, problem_type_id=problem_type_id)
    assert created.status_code == 201
    other = User(name="Other Student", email="other2@example.test", role="student")
    generator = client.app.dependency_overrides[get_db](); db = next(generator)
    db.add(other); db.commit(); other_id = other.id
    try: next(generator)
    except StopIteration: pass
    response = client.get(f"/api/v1/issues/similar?location_id={location_id}&problem_type_id={problem_type_id}", headers={"X-User-Id": str(other_id)})
=======

def test_similar_open_complaints_endpoint_and_room_exclusion(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
    created = create_test_issue(
        client, user_id=user_id, location_id=location_id, problem_type_id=problem_type_id
    )
    assert created.status_code == 201
    other = User(name="Other Student", email="other2@example.test", role="student")
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    db.add(other)
    db.commit()
    other_id = other.id
    try:
        next(generator)
    except StopIteration:
        pass
    response = client.get(
        f"/api/v1/issues/similar?location_id={location_id}&problem_type_id={problem_type_id}",
        headers={"X-User-Id": str(other_id)},
    )
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == created.json()["id"]


def test_status_transitions_and_resolution_feedback(client):
    location_id, problem_type_id, student_id = seed_minimal(client)
<<<<<<< HEAD
    created = create_test_issue(client, user_id=student_id, location_id=location_id, problem_type_id=problem_type_id)
    issue_id = created.json()["id"]
    generator = client.app.dependency_overrides[get_db](); db = next(generator)
    category = db.query(Category).filter_by(name="Maintenance").first()
    staff = User(name="Staff", email="staff2@example.test", role="staff", category_id=category.id, is_verified=True)
    db.add(staff); db.commit(); staff_id = staff.id
    try: next(generator)
    except StopIteration: pass
    h={"X-User-Id":str(staff_id)}
    assert client.patch(f"/api/v1/staff/issues/{issue_id}/status",headers=h,json={"status":"resolved"}).status_code==409
    for status in ("acknowledged","in_progress","resolved"):
        r=client.patch(f"/api/v1/staff/issues/{issue_id}/status",headers=h,json={"status":status,"comment":"Progress"})
        assert r.status_code==200, r.text
    confirmed=client.post(f"/api/v1/issues/{issue_id}/resolution-feedback",headers={"X-User-Id":str(student_id)},json={"outcome":"resolved","comment":"Fixed"})
    assert confirmed.status_code==201
    assert confirmed.json()["status"]=="closed"
    reopened=client.post(f"/api/v1/issues/{issue_id}/resolution-feedback",headers={"X-User-Id":str(student_id)},json={"outcome":"reopen_requested","comment":"Still broken"})
    assert reopened.status_code==409
=======
    created = create_test_issue(
        client, user_id=student_id, location_id=location_id, problem_type_id=problem_type_id
    )
    issue_id = created.json()["id"]
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    category = db.query(Category).filter_by(name="Maintenance").first()
    staff = User(
        name="Staff",
        email="staff2@example.test",
        role="staff",
        category_id=category.id,
        is_verified=True,
    )
    db.add(staff)
    db.commit()
    staff_id = staff.id
    try:
        next(generator)
    except StopIteration:
        pass
    h = {"X-User-Id": str(staff_id)}
    assert (
        client.patch(
            f"/api/v1/staff/issues/{issue_id}/status", headers=h, json={"status": "resolved"}
        ).status_code
        == 409
    )
    for status in ("acknowledged", "in_progress", "resolved"):
        r = client.patch(
            f"/api/v1/staff/issues/{issue_id}/status",
            headers=h,
            json={"status": status, "comment": "Progress"},
        )
        assert r.status_code == 200, r.text
    confirmed = client.post(
        f"/api/v1/issues/{issue_id}/resolution-feedback",
        headers={"X-User-Id": str(student_id)},
        json={"outcome": "resolved", "comment": "Fixed"},
    )
    assert confirmed.status_code == 201
    assert confirmed.json()["status"] == "closed"
    reopened = client.post(
        f"/api/v1/issues/{issue_id}/resolution-feedback",
        headers={"X-User-Id": str(student_id)},
        json={"outcome": "reopen_requested", "comment": "Still broken"},
    )
    assert reopened.status_code == 409
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d


def test_asset_must_serve_selected_location(client):
    location_id, problem_type_id, user_id = seed_minimal(client)
<<<<<<< HEAD
    generator = client.app.dependency_overrides[get_db](); db = next(generator)
    from app.models import Hostel, Asset
    hostel=db.query(Hostel).first(); asset=Asset(hostel_id=hostel.id,name="Lift 1",asset_type="lift"); db.add(asset); db.commit(); asset_id=asset.id
    try: next(generator)
    except StopIteration: pass
    r=client.post("/api/v1/issues",headers={"X-User-Id":str(user_id)},json={"title":"Lift issue","description":"The lift is not working and needs inspection.","location_id":location_id,"problem_type_id":problem_type_id,"asset_id":asset_id,"is_public":True})
    assert r.status_code==422

def test_auto_close_after_seven_days(client):
    from datetime import datetime, timedelta, timezone
    from app.services.lifecycle import auto_close_resolved_issues
    location_id, problem_type_id, student_id = seed_minimal(client)
    created=create_test_issue(client,user_id=student_id,location_id=location_id,problem_type_id=problem_type_id)
    issue_id=created.json()["id"]
    generator=client.app.dependency_overrides[get_db](); db=next(generator)
    category=db.query(Category).filter_by(name="Maintenance").first()
    staff=User(name="Staff",email="staff3@iitdh.ac.in",role="staff",category_id=category.id,is_verified=True); admin=User(name="Admin",email="admin3@iitdh.ac.in",role="administrator",is_verified=True); db.add_all([staff,admin]); db.commit() 
    issue=db.get(__import__('app.models',fromlist=['Issue']).Issue,issue_id); issue.status="resolved"; issue.resolved_at=datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(days=8); db.commit()
    count=auto_close_resolved_issues(db, datetime.now(timezone.utc).replace(tzinfo=None))
    assert count==1
    db.refresh(issue); assert issue.status=="closed"
    update=issue.updates[-1]; assert update.comment=="auto-closed: no response"
    try: next(generator)
    except StopIteration: pass
=======
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    from app.models import Asset, Hostel

    hostel = db.query(Hostel).first()
    asset = Asset(hostel_id=hostel.id, name="Lift 1", asset_type="lift")
    db.add(asset)
    db.commit()
    asset_id = asset.id
    try:
        next(generator)
    except StopIteration:
        pass
    r = client.post(
        "/api/v1/issues",
        headers={"X-User-Id": str(user_id)},
        json={
            "title": "Lift issue",
            "description": "The lift is not working and needs inspection.",
            "location_id": location_id,
            "problem_type_id": problem_type_id,
            "asset_id": asset_id,
            "is_public": True,
        },
    )
    assert r.status_code == 422


def test_auto_close_after_seven_days(client):
    from datetime import datetime, timedelta

    from app.services.lifecycle import auto_close_resolved_issues

    location_id, problem_type_id, student_id = seed_minimal(client)
    created = create_test_issue(
        client, user_id=student_id, location_id=location_id, problem_type_id=problem_type_id
    )
    issue_id = created.json()["id"]
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    category = db.query(Category).filter_by(name="Maintenance").first()
    staff = User(
        name="Staff",
        email="staff3@iitdh.ac.in",
        role="staff",
        category_id=category.id,
        is_verified=True,
    )
    admin = User(name="Admin", email="admin3@iitdh.ac.in", role="administrator", is_verified=True)
    db.add_all([staff, admin])
    db.commit()
    issue = db.get(__import__("app.models", fromlist=["Issue"]).Issue, issue_id)
    issue.status = "resolved"
    issue.resolved_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=8)
    db.commit()
    count = auto_close_resolved_issues(db, datetime.now(UTC).replace(tzinfo=None))
    assert count == 1
    db.refresh(issue)
    assert issue.status == "closed"
    update = issue.updates[-1]
    assert update.comment == "auto-closed: no response"
    try:
        next(generator)
    except StopIteration:
        pass
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
