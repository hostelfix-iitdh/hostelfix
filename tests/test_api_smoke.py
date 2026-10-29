from app.db.session import get_db
from app.models import Hostel, Floor, Wing, Location, Category, ProblemType, User

def seed_minimal(client):
    # Get the same test DB session through the dependency override.
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    h = Hostel(name="Test Hostel"); db.add(h); db.flush()
    f = Floor(hostel_id=h.id, floor_number=1); db.add(f); db.flush()
    w = Wing(floor_id=f.id, wing_name="A"); db.add(w); db.flush()
    loc = Location(wing_id=w.id, area_type="toilet"); db.add(loc)
    cat = Category(name="Maintenance"); db.add(cat); db.flush()
    pt = ProblemType(category_id=cat.id, name="Plumbing"); db.add(pt)
    user = User(name="Test Student", email="student@example.test", role="student"); db.add(user)
    db.commit()
    ids = (loc.id, pt.id, user.id)
    try: next(generator)
    except StopIteration: pass
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
    response = client.post("/api/v1/issues", headers={"X-User-Id": str(user_id)}, json={
        "title": "Leaking sink", "description": "The sink is leaking continuously.",
        "location_id": location_id, "problem_type_id": problem_type_id, "is_public": True
    })
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
