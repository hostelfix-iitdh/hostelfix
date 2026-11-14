from app.db.session import get_db
from app.models import Asset, AssetLocation, Category, Floor, Hostel, Location, Notification, ProblemType, User, Wing
from app.routers.ai import _extract_from_text, _local_fallback, _norm, _postprocess, _options
from app.services.ai import FieldSuggestion, SmartReportResult


def db_for(client):
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    return db, generator


def close_db(generator):
    try:
        next(generator)
    except StopIteration:
        pass


def admin_user(client):
    db, generator = db_for(client)
    category = Category(name="Maintenance")
    db.add(category)
    db.flush()
    user = User(name="Admin", email="admin@iitdh.ac.in", role="administrator", is_verified=True)
    db.add(user)
    db.commit()
    ids = user.id, category.id
    close_db(generator)
    return ids


def test_admin_configuration_crud_and_duplicates(client):
    admin_id, category_id = admin_user(client)
    h = {"X-User-Id": str(admin_id)}

    hostel = client.post("/api/v1/admin/hostels", headers=h, json={"name": "Hostel New"})
    assert hostel.status_code == 201
    hostel_id = hostel.json()["id"]
    assert client.post("/api/v1/admin/hostels", headers=h, json={"name": "hostel new"}).status_code == 409

    floor = client.post("/api/v1/admin/floors", headers=h, json={"hostel_id": hostel_id, "floor_number": 2})
    assert floor.status_code == 201
    floor_id = floor.json()["id"]
    assert client.post("/api/v1/admin/floors", headers=h, json={"hostel_id": hostel_id, "floor_number": 2}).status_code == 409
    assert client.post("/api/v1/admin/floors", headers=h, json={"hostel_id": 999, "floor_number": 1}).status_code == 404

    wing = client.post("/api/v1/admin/wings", headers=h, json={"floor_id": floor_id, "wing_name": " b "})
    assert wing.status_code == 201
    wing_id = wing.json()["id"]
    assert wing.json()["wing_name"] == "B"
    assert client.post("/api/v1/admin/wings", headers=h, json={"floor_id": floor_id, "wing_name": "b"}).status_code == 409
    assert client.post("/api/v1/admin/wings", headers=h, json={"floor_id": 999, "wing_name": "C"}).status_code == 404

    location = client.post(
        "/api/v1/admin/locations",
        headers=h,
        json={"wing_id": wing_id, "area_type": " corridor ", "description": "Main corridor"},
    )
    assert location.status_code == 201
    location_id = location.json()["id"]
    assert location.json()["area_type"] == "corridor"
    assert client.post("/api/v1/admin/locations", headers=h, json={"wing_id": wing_id, "area_type": "corridor"}).status_code == 409
    assert client.patch("/api/v1/admin/locations/999", headers=h, json={"area_type": "hall"}).status_code == 404
    patched = client.patch(
        f"/api/v1/admin/locations/{location_id}",
        headers=h,
        json={"area_type": "hall", "description": "Updated"},
    )
    assert patched.status_code == 200
    assert patched.json()["area_type"] == "hall"

    category = client.post(
        "/api/v1/admin/categories",
        headers=h,
        json={"name": "Housekeeping", "description": "Cleaning", "resolution_target_hours": 24},
    )
    assert category.status_code == 201
    new_category_id = category.json()["id"]
    assert client.post("/api/v1/admin/categories", headers=h, json={"name": "housekeeping"}).status_code == 409
    assert client.patch("/api/v1/admin/categories/999", headers=h, json={"description": "x"}).status_code == 404
    assert client.patch(
        f"/api/v1/admin/categories/{new_category_id}", headers=h, json={"resolution_target_hours": 48}
    ).status_code == 200

    problem = client.post(
        "/api/v1/admin/problem-types",
        headers=h,
        json={"category_id": new_category_id, "name": "Corridor cleaning", "requires_description": True},
    )
    assert problem.status_code == 201
    problem_id = problem.json()["id"]
    assert client.post(
        "/api/v1/admin/problem-types", headers=h,
        json={"category_id": new_category_id, "name": "Corridor cleaning"},
    ).status_code == 409
    assert client.post(
        "/api/v1/admin/problem-types", headers=h,
        json={"category_id": 999, "name": "Other"},
    ).status_code == 404
    assert client.patch("/api/v1/admin/problem-types/999", headers=h, json={"name": "Other"}).status_code == 404
    assert client.patch(
        f"/api/v1/admin/problem-types/{problem_id}", headers=h,
        json={"name": "Clean corridor", "description": "Updated"},
    ).status_code == 200

    asset = client.post(
        "/api/v1/admin/assets", headers=h,
        json={"hostel_id": hostel_id, "name": "Vacuum 1", "asset_type": "equipment", "location_ids": [location_id]},
    )
    assert asset.status_code == 201
    asset_id = asset.json()["id"]
    assert client.patch(
        f"/api/v1/admin/assets/{asset_id}", headers=h,
        json={"name": "Vacuum 2", "description": "Updated"},
    ).status_code == 200
    assert client.post(
        f"/api/v1/admin/assets/{asset_id}/locations", headers=h, json={"location_id": location_id}
    ).status_code == 409
    assert client.delete(
        f"/api/v1/admin/assets/{asset_id}/locations/{location_id}", headers=h
    ).status_code == 204
    assert client.delete(
        f"/api/v1/admin/assets/{asset_id}/locations/{location_id}", headers=h
    ).status_code == 404
    assert client.patch("/api/v1/admin/assets/999", headers=h, json={"name": "xx"}).status_code == 404
    assert client.post("/api/v1/admin/assets", headers=h, json={
        "hostel_id": 999, "name": "Bad", "asset_type": "equipment"
    }).status_code == 404
    assert client.post("/api/v1/admin/assets", headers=h, json={
        "hostel_id": hostel_id, "name": "Bad", "asset_type": "equipment", "location_ids": [999]
    }).status_code == 422


def test_admin_analytics_staff_and_role_guard(client, monkeypatch):
    admin_id, category_id = admin_user(client)
    h = {"X-User-Id": str(admin_id)}
    monkeypatch.setattr("app.routers.admin.send_mail", lambda *args, **kwargs: None)

    response = client.post(
        "/api/v1/admin/staff", headers=h,
        json={"name": "Staff One", "email": "staff1@iitdh.ac.in", "category_id": category_id},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "staff"
    assert response.json()["development_set_password_url"]
    assert client.post(
        "/api/v1/admin/staff", headers=h,
        json={"name": "Staff One", "email": "staff1@iitdh.ac.in", "category_id": category_id},
    ).status_code == 409
    assert client.post(
        "/api/v1/admin/staff", headers=h,
        json={"name": "Staff Two", "email": "staff2@iitdh.ac.in", "category_id": 999},
    ).status_code == 422

    analytics = client.get("/api/v1/admin/analytics", headers=h)
    assert analytics.status_code == 200
    assert analytics.json()["total_issues"] == 0
    assert analytics.json()["average_resolution_hours"] is None

    db, generator = db_for(client)
    student = User(name="Student", email="student@iitdh.ac.in", role="student")
    db.add(student)
    db.commit()
    student_id = student.id
    close_db(generator)
    assert client.get("/api/v1/admin/analytics", headers={"X-User-Id": str(student_id)}).status_code == 403


def test_location_endpoints_and_not_found_paths(client):
    db, generator = db_for(client)
    hostel = Hostel(name="H1")
    db.add(hostel); db.flush()
    floor = Floor(hostel_id=hostel.id, floor_number=1)
    db.add(floor); db.flush()
    wing = Wing(floor_id=floor.id, wing_name="A")
    db.add(wing); db.flush()
    loc = Location(wing_id=wing.id, area_type="corridor")
    cat = Category(name="Maintenance")
    db.add_all([loc, cat]); db.flush()
    problem = ProblemType(category_id=cat.id, name="Plumbing")
    db.add(problem)
    asset = Asset(hostel_id=hostel.id, name="Tap", asset_type="fixture")
    db.add(asset); db.flush()
    db.add(AssetLocation(asset_id=asset.id, location_id=loc.id))
    db.commit()
    ids = hostel.id, floor.id, wing.id, loc.id, cat.id
    close_db(generator)

    assert client.get("/api/v1/hostels").status_code == 200
    assert client.get(f"/api/v1/hostels/{ids[0]}/floors").status_code == 200
    assert client.get(f"/api/v1/floors/{ids[1]}/wings").status_code == 200
    assert client.get(f"/api/v1/wings/{ids[2]}/locations").status_code == 200
    assert client.get("/api/v1/categories").status_code == 200
    assert client.get(f"/api/v1/categories/{ids[4]}/problem-types").status_code == 200
    assert client.get(f"/api/v1/locations/{ids[3]}/assets").status_code == 200
    assert client.get("/api/v1/hostels/999/floors").status_code == 404
    assert client.get("/api/v1/floors/999/wings").status_code == 404
    assert client.get("/api/v1/wings/999/locations").status_code == 404
    assert client.get("/api/v1/categories/999/problem-types").status_code == 404
    assert client.get("/api/v1/locations/999/assets").status_code == 404


def test_profile_password_notifications_and_delete(client):
    from app.services.security import hash_password

    db, generator = db_for(client)
    user = User(
        name="Profile User", email="profile@iitdh.ac.in", role="staff", password_hash=hash_password("oldpass"),
        is_verified=True,
    )
    db.add(user); db.flush()
    note = Notification(user_id=user.id, title="Test", message="Hello")
    db.add(note); db.commit()
    user_id, note_id = user.id, note.id
    close_db(generator)
    h = {"X-User-Id": str(user_id)}

    profile = client.get("/api/v1/me", headers=h)
    assert profile.status_code == 200
    assert profile.json()["email"] == "profile@iitdh.ac.in"
    assert client.patch("/api/v1/me", headers=h, json={"name": "Updated User"}).status_code == 200
    assert client.post("/api/v1/me/password", headers=h, json={"current_password": "wrong", "new_password": "newpass"}).status_code == 401
    assert client.post("/api/v1/me/password", headers=h, json={"current_password": "oldpass", "new_password": "newpass"}).status_code == 200

    notes = client.get("/api/v1/notifications", headers=h)
    assert notes.status_code == 200
    assert notes.json()["total"] == 1
    assert client.patch(f"/api/v1/notifications/{note_id}", headers=h, json={"is_read": True}).status_code == 200
    assert client.patch("/api/v1/notifications/999", headers=h, json={"is_read": True}).status_code == 404

    db, generator = db_for(client)
    other = User(name="Other", email="other@iitdh.ac.in", role="staff", is_verified=True)
    db.add(other); db.commit(); other_id = other.id
    close_db(generator)
    assert client.patch(f"/api/v1/notifications/{note_id}", headers={"X-User-Id": str(other_id)}, json={"is_read": False}).status_code == 403

    assert client.delete("/api/v1/me", headers=h).status_code == 204
    assert client.get("/api/v1/me", headers=h).status_code == 401


def test_auth_config_google_login_and_password_flows(client, monkeypatch):
    assert client.get("/api/v1/auth/config").status_code == 200
    monkeypatch.setattr("app.routers.auth.send_mail", lambda *args, **kwargs: None)
    register = client.post("/api/v1/auth/register", json={
        "name": "Auth User", "email": "authuser@iitdh.ac.in", "password": "pass123", "consent": True,
    })
    assert register.status_code == 201
    token = register.json()["development_verification_url"].split("verify=", 1)[1]
    assert client.post("/api/v1/auth/verify", json={"token": token}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "authuser@iitdh.ac.in", "password": "pass123"}).status_code == 403

    db, generator = db_for(client)
    admin = User(name="Login Admin", email="loginadmin@iitdh.ac.in", role="administrator", password_hash=__import__("app.services.security", fromlist=["hash_password"]).hash_password("secret"), is_verified=True)
    db.add(admin); db.commit(); close_db(generator)
    login = client.post("/api/v1/auth/login", json={"email": "loginadmin@iitdh.ac.in", "password": "secret"})
    assert login.status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.post("/api/v1/auth/login", json={"email": "loginadmin@iitdh.ac.in", "password": "bad"}).status_code == 401

    reset = client.post("/api/v1/auth/forgot-password", json={"email": "loginadmin@iitdh.ac.in"})
    assert reset.status_code == 200
    assert client.post("/api/v1/auth/forgot-password", json={"email": "missing@iitdh.ac.in"}).status_code == 200

    monkeypatch.setattr("app.routers.auth.verify_google_id_token", lambda credential: {
        "email": "googleuser@iitdh.ac.in", "sub": "google-sub-123", "name": "Google User"
    })
    google = client.post("/api/v1/auth/google", json={"credential": "x" * 20})
    assert google.status_code == 200
    assert google.json()["role"] == "student"


def test_smartreport_helpers_cover_fallback_and_extraction(client):
    db, generator = db_for(client)
    hostel = Hostel(name="Hostel 1"); db.add(hostel); db.flush()
    floor = Floor(hostel_id=hostel.id, floor_number=6); db.add(floor); db.flush()
    wing = Wing(floor_id=floor.id, wing_name="E"); db.add(wing); db.flush()
    area = Location(wing_id=wing.id, area_type="corridor"); db.add(area)
    asset = Asset(hostel_id=hostel.id, name="Lift 1", asset_type="lift"); db.add(asset)
    cat = Category(name="Housekeeping"); db.add(cat); db.flush()
    pt = ProblemType(category_id=cat.id, name="Corridor cleaning"); db.add(pt)
    db.commit()
    options = _options(db)
    close_db(generator)

    out = {}
    _extract_from_text("Hostel 1, 6th floor, Wing E dirty corridor near room 612 and Lift 1", options, out)
    assert out["hostel"]["value"] == "Hostel 1"
    assert out["floor"]["value"] == "6"
    assert out["wing"]["value"] == "E"
    assert out["area"]["value"] == "corridor"
    assert out["room_label"]["value"] == "612"
    assert out["asset"]["value"] == "Lift 1"

    fallback = _local_fallback("Hostel 1 6th floor Wing E dirty corridor", options)
    assert fallback.category.value == "Housekeeping"
    assert fallback.problem_type.value == "Corridor cleaning"
    assert _norm("  Hello_World  ") == "hello world"

    result = SmartReportResult(
        category=FieldSuggestion(value="Housekeeping", span="dirty corridor"),
        problem_type=FieldSuggestion(value="Corridor cleaning", span="dirty corridor"),
        title="", description="", image_observation="",
    )
    processed = _postprocess(result, options, "Hostel 1 6th floor Wing E dirty corridor")
    assert processed["needs_clarification"] is False
    assert processed["title"] == "Hostel issue reported"
