import json
from pathlib import Path
<<<<<<< HEAD
from app.services.ai import SmartReportResult
from app.routers.ai import _postprocess
=======

from app.routers.ai import _postprocess
from app.services.ai import SmartReportResult
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d


def test_evaluation_set_has_at_least_20_cases():
    data = json.loads(Path(__file__).with_name("ai_evaluation_set.json").read_text())
    assert len(data) >= 40


def test_image_washing_machine_classification_is_normalized():
    result = SmartReportResult(
<<<<<<< HEAD
        hostel={"value": None, "span": None}, floor={"value": None, "span": None},
        wing={"value": None, "span": None}, area={"value": None, "span": None},
        asset={"value": None, "span": None}, category={"value": "Housekeeping", "span": None},
        problem_type={"value": "Washing machine area cleaning", "span": None},
        title="", description="", image_observation="A damaged washing machine with a broken panel.")
    options={"hostels":[],"floors":[],"wings":[],"areas":[],"assets":[],
             "categories":[{"name":"Maintenance"},{"name":"Housekeeping"}],
             "problem_types":[{"name":"Washing machine"},{"name":"Washing machine area cleaning"}]}
    out=_postprocess(result, options, "")
=======
        hostel={"value": None, "span": None},
        floor={"value": None, "span": None},
        wing={"value": None, "span": None},
        area={"value": None, "span": None},
        asset={"value": None, "span": None},
        category={"value": "Housekeeping", "span": None},
        problem_type={"value": "Washing machine area cleaning", "span": None},
        title="",
        description="",
        image_observation="A damaged washing machine with a broken panel.",
    )
    options = {
        "hostels": [],
        "floors": [],
        "wings": [],
        "areas": [],
        "assets": [],
        "categories": [{"name": "Maintenance"}, {"name": "Housekeeping"}],
        "problem_types": [{"name": "Washing machine"}, {"name": "Washing machine area cleaning"}],
    }
    out = _postprocess(result, options, "")
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
    assert out["category"]["value"] == "Maintenance"
    assert out["problem_type"]["value"] == "Washing machine"


def test_register_accepts_five_character_password(client, monkeypatch):
    monkeypatch.setattr("app.routers.auth.send_mail", lambda *args, **kwargs: None)
<<<<<<< HEAD
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "testuser@iitdh.ac.in",
        "password": "Test1",
        "consent": True,
    })
=======
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "testuser@iitdh.ac.in",
            "password": "Test1",
            "consent": True,
        },
    )
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
    assert response.status_code == 201


def test_register_rejects_non_iitdh_email(client):
<<<<<<< HEAD
    response = client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "testuser@gmail.com",
        "password": "Test1",
        "consent": True,
    })
    assert response.status_code == 422

def test_fixed_role_credentials_are_argon2_hashes():
    from app.core.role_credentials import ADMIN_CREDENTIALS, STAFF_CREDENTIALS
=======
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": "testuser@gmail.com",
            "password": "Test1",
            "consent": True,
        },
    )
    assert response.status_code == 422


def test_fixed_role_credentials_are_argon2_hashes():
    from app.core.role_credentials import ADMIN_CREDENTIALS, STAFF_CREDENTIALS

>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d
    assert ADMIN_CREDENTIALS["password_hash"].startswith("$argon2")
    assert all(item["password_hash"].startswith("$argon2") for item in STAFF_CREDENTIALS)
