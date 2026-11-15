import json
from pathlib import Path
from app.services.ai import SmartReportResult
from app.routers.ai import _postprocess
from app.db.session import get_db


def test_evaluation_set_has_at_least_20_cases():
    data = json.loads(Path(__file__).with_name("ai_evaluation_set.json").read_text())
    assert len(data) >= 40


def test_image_washing_machine_classification_is_normalized():
    result = SmartReportResult(
        hostel={"value": None, "span": None}, floor={"value": None, "span": None},
        wing={"value": None, "span": None}, area={"value": None, "span": None},
        asset={"value": None, "span": None}, category={"value": "Housekeeping", "span": None},
        problem_type={"value": "Washing machine area cleaning", "span": None},
        title="", description="", image_observation="A damaged washing machine with a broken panel.")
    options={"hostels":[],"floors":[],"wings":[],"areas":[],"assets":[],
             "categories":[{"name":"Maintenance"},{"name":"Housekeeping"}],
             "problem_types":[{"name":"Washing machine"},{"name":"Washing machine area cleaning"}]}
    out=_postprocess(result, options, "")
    assert out["category"]["value"] == "Maintenance"
    assert out["problem_type"]["value"] == "Washing machine"


def test_register_accepts_five_character_password(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.send_mail", lambda *args, **kwargs: None)
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "testuser@iitdh.ac.in",
        "password": "Test1",
        "consent": True,
    })
    assert response.status_code == 201


def test_register_rejects_non_iitdh_email(client):
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "testuser@gmail.com",
        "password": "Test1",
        "consent": True,
    })
    assert response.status_code == 422

def test_fixed_role_credentials_are_argon2_hashes():
    from app.core.role_credentials import ADMIN_CREDENTIALS, STAFF_CREDENTIALS
    assert ADMIN_CREDENTIALS["password_hash"].startswith("$argon2")
    assert all(item["password_hash"].startswith("$argon2") for item in STAFF_CREDENTIALS)


def test_admin_can_create_and_delete_staff_with_hashed_password(client):
    from app.models import Category, User
    from app.services.security import verify_password
    db = next(client.app.dependency_overrides[get_db]())
    category = Category(name="Maintenance New", resolution_target_hours=168)
    admin = User(name="Admin", email="admin-new@iitdh.ac.in", role="administrator", is_verified=True)
    db.add_all([category, admin]); db.commit(); db.refresh(category); db.refresh(admin)
    h = {"X-User-Id": str(admin.id)}
    created = client.post("/api/v1/admin/staff", headers=h, json={"name":"Tech", "email":"tech@iitdh.ac.in", "category_id":category.id, "password":"secret1"})
    assert created.status_code == 201
    staff = db.query(User).filter(User.email == "tech@iitdh.ac.in").one()
    assert staff.password_hash and staff.password_hash != "secret1"
    assert verify_password("secret1", staff.password_hash)
    assert client.delete(f"/api/v1/admin/staff/{staff.id}", headers=h).status_code == 204
    db.refresh(staff)
    assert staff.deleted_at is not None and staff.password_hash is None
    db.close()


def test_smart_report_falls_back_to_pattern_mode_after_daily_limit(client):
    from datetime import date
    from app.models import User
    db = next(client.app.dependency_overrides[get_db]())
    student = User(name="Student", email="student@iitdh.ac.in", role="student", is_verified=True, smart_report_last_used_on=date.today())
    db.add(student); db.commit(); db.refresh(student)
    response = client.post("/api/v1/issues/draft", headers={"X-User-Id": str(student.id)}, data={"text":"Hostel 1 fourth floor wing B corridor is dirty"})
    assert response.status_code == 200
    assert response.json()["mode"] == "pattern"
    assert response.json()["daily_limit_reached"] is True
    image = client.post("/api/v1/issues/draft", headers={"X-User-Id": str(student.id)}, data={"text":"Hostel 1 corridor"}, files={"image":("x.png", b"not-an-image", "image/png")})
    assert image.status_code == 403
    db.close()
