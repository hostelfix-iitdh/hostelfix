import asyncio
import re
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import client_key, rate_limiter
from app.db.session import get_db
from app.models import Asset, Category, Floor, Hostel, Location, ProblemType, User, Wing
from app.routers.deps import get_actor
<<<<<<< HEAD
from app.services.ai import provider, SmartReportResult
from app.core.rate_limit import rate_limiter, client_key
=======
from app.services.ai import SmartReportResult, provider
>>>>>>> 674014b3680ed9758c12e5cb16302fa9b00d513d

router = APIRouter(prefix="/issues", tags=["SmartReport AI"])
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
    "image/avif",
}


def _options(db: Session) -> dict:
    hostels = db.query(Hostel).order_by(Hostel.id).all()
    floors = db.query(Floor).order_by(Floor.hostel_id, Floor.floor_number).all()
    wings = db.query(Wing).order_by(Wing.floor_id, Wing.wing_name).all()
    locations = db.query(Location).order_by(Location.id).all()
    assets = db.query(Asset).order_by(Asset.hostel_id, Asset.name).all()
    categories = db.query(Category).order_by(Category.name).all()
    problems = db.query(ProblemType).order_by(ProblemType.category_id, ProblemType.name).all()
    return {
        "hostels": [{"id": x.id, "name": x.name} for x in hostels],
        "floors": [
            {"id": x.id, "hostel_id": x.hostel_id, "floor_number": x.floor_number} for x in floors
        ],
        "wings": [{"id": x.id, "floor_id": x.floor_id, "wing_name": x.wing_name} for x in wings],
        "areas": [{"id": x.id, "wing_id": x.wing_id, "area_type": x.area_type} for x in locations],
        "assets": [
            {"id": x.id, "hostel_id": x.hostel_id, "name": x.name, "asset_type": x.asset_type}
            for x in assets
        ],
        "categories": [{"id": x.id, "name": x.name} for x in categories],
        "problem_types": [
            {"id": x.id, "category_id": x.category_id, "name": x.name} for x in problems
        ],
    }


def _norm(v: str | None) -> str:
    return " ".join(str(v or "").lower().replace("_", " ").split())


def _evidence(value: str | None, span: str | None, text: str) -> bool:
    if not value or not span:
        return False
    return _norm(span) in _norm(text) or _norm(value) in _norm(text)


def _set_suggestion(result: dict, field: str, value: str, span: str, confidence: float = 0.99):
    result[field] = {"value": value, "span": span, "confidence": confidence}


def _extract_from_text(text: str, options: dict, out: dict) -> None:
    """Deterministically recover location facts so obvious phrases reliably fill the form."""
    low = text.lower()
    # Hostel
    for h in options["hostels"]:
        aliases = [h["name"].lower(), h["name"].lower().replace("hostel ", "h")]
        m = next(
            (
                re.search(rf"\b{re.escape(alias)}\b", low)
                for alias in aliases
                if re.search(rf"\b{re.escape(alias)}\b", low)
            ),
            None,
        )
        if m:
            _set_suggestion(out, "hostel", h["name"], text[m.start() : m.end()])
            break
    # Floor: ordinal, word ordinal, or explicit numeric floor.
    nums = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
    }
    floor_re = re.compile(
        r"\b(?:(\d{1,2})(?:st|nd|rd|th)?|("
        + "|".join(nums)
        + r"))\s*(?:floor|fl)\b|\bfloor\s*(\d{1,2})\b",
        re.IGNORECASE,
    )
    m = floor_re.search(text)
    if m:
        value = int(m.group(1) or nums.get((m.group(2) or "").lower()) or m.group(3))
        if any(int(x["floor_number"]) == value for x in options["floors"]):
            _set_suggestion(out, "floor", str(value), m.group(0))
    # Wing
    m = re.search(r"\b(?:wing\s*)?([A-E])\s*(?:wing)?\b", text, re.IGNORECASE)
    if m and re.search(r"\bwing\b", m.group(0), re.IGNORECASE):
        _set_suggestion(out, "wing", m.group(1).upper(), m.group(0))
    # Area aliases. Longest aliases first.
    area_aliases = {
        "washing_machine_area": ["washing machine area", "washing-machine area", "washer area"],
        "cloth_drying_area": ["cloth drying area", "clothes drying area", "drying area"],
        "drinking_water_area": ["drinking water area", "water dispenser area", "drinking water"],
        "lift_lobby": ["lift lobby", "elevator lobby", "lift area", "elevator area"],
        "corridor": ["corridor", "hallway", "hall"],
        "bathroom": ["bathroom", "washroom"],
        "toilet": ["toilet"],
        "room": ["room"],
    }
    for area, aliases in area_aliases.items():
        found = next((a for a in aliases if re.search(rf"\b{re.escape(a)}\b", low)), None)
        if found:
            _set_suggestion(out, "area", area, found)
            break
    # Room label such as room 412.
    m = re.search(r"\b(?:room|rm)\s*(?:no\.?\s*)?([A-Za-z0-9-]{2,10})\b", text, re.IGNORECASE)
    if m:
        _set_suggestion(out, "room_label", m.group(1), m.group(0))
    # Text asset references. Exact DB assets are preferred.
    for asset in options["assets"]:
        m = re.search(rf"\b{re.escape(asset['name'].lower())}\b", low)
        if m:
            _set_suggestion(out, "asset", asset["name"], text[m.start() : m.end()])
            break


def _postprocess(result: SmartReportResult, options: dict, text: str) -> dict:
    out = result.model_dump()
    for field, items, key in [
        ("hostel", options["hostels"], "name"),
        ("floor", options["floors"], "floor_number"),
        ("wing", options["wings"], "wing_name"),
        ("area", options["areas"], "area_type"),
        ("asset", options["assets"], "name"),
    ]:
        suggestion = out[field]
        if not suggestion.get("value") or (
            field in {"hostel", "floor", "wing", "area", "asset"}
            and not _evidence(suggestion.get("value"), suggestion.get("span"), text)
        ):
            suggestion["value"] = None
            suggestion["span"] = None
            suggestion["confidence"] = 0
        else:
            if field == "floor":
                try:
                    suggestion["value"] = str(
                        next(
                            x for x in items if str(x["floor_number"]) == str(suggestion["value"])
                        )["floor_number"]
                    )
                except StopIteration:
                    suggestion["value"] = None
            elif field == "wing":
                suggestion["value"] = str(suggestion["value"]).upper().replace("WING ", "")
    _extract_from_text(text, options, out)

    observation = _norm(result.image_observation)
    if "washing machine" in observation and any(
        w in observation for w in ("broken", "damaged", "not working", "fault", "leak")
    ):
        out["category"] = {
            "value": "Maintenance",
            "span": result.image_observation,
            "confidence": 0.95,
        }
        out["problem_type"] = {
            "value": "Washing machine",
            "span": result.image_observation,
            "confidence": 0.95,
        }
        out["title"] = out["title"] or "Washing machine needs repair"
    if ("lift" in observation or "elevator" in observation) and any(
        w in observation for w in ("stuck", "broken", "not working", "fault")
    ):
        out["category"] = {
            "value": "Maintenance",
            "span": result.image_observation,
            "confidence": 0.95,
        }
        out["problem_type"] = {
            "value": "Lift malfunction",
            "span": result.image_observation,
            "confidence": 0.95,
        }
        out["title"] = out["title"] or "Lift malfunction"

    if not out.get("title"):
        out["title"] = "Hostel issue reported"
    if not out.get("description"):
        out["description"] = text.strip()
    missing = []
    for field in ("hostel", "floor", "wing", "area"):
        if not out.get(field, {}).get("value"):
            missing.append(field)
    if not out.get("category", {}).get("value"):
        missing.append("category")
    if not out.get("problem_type", {}).get("value"):
        missing.append("problem_type")
    out["missing_fields"] = missing
    out["needs_clarification"] = bool(missing)
    return out


def _local_fallback(text: str, options: dict) -> SmartReportResult:
    out = SmartReportResult(description=text.strip(), title="Hostel issue reported")
    data = out.model_dump()
    _extract_from_text(text, options, data)
    low = text.lower()
    rules = [
        (
            r"washing machine|washer",
            r"not working|broken|damaged|leak|repair|out of order",
            "Maintenance",
            "Washing machine",
            "Washing machine needs repair",
        ),
        (
            r"lift|elevator",
            r"stuck|not working|broken|malfunction|fault",
            "Maintenance",
            "Lift malfunction",
            "Lift malfunction",
        ),
        (
            r"corridor|hallway",
            r"dirty|unclean|cleaning|dusty",
            "Housekeeping",
            "Corridor cleaning",
            "Corridor cleaning required",
        ),
        (
            r"washing machine area|washer area",
            r"dirty|unclean|cleaning",
            "Housekeeping",
            "Washing machine area cleaning",
            "Washing machine area cleaning required",
        ),
        (
            r"lift lobby|elevator lobby",
            r"dirty|unclean|cleaning",
            "Housekeeping",
            "Unclean lift lobby",
            "Lift lobby cleaning required",
        ),
        (
            r"toilet|washroom",
            r"dirty|unclean|cleaning",
            "Housekeeping",
            "Toilet cleaning",
            "Toilet cleaning required",
        ),
        (
            r"bathroom|shower",
            r"dirty|unclean|cleaning",
            "Housekeeping",
            "Bathroom cleaning",
            "Bathroom cleaning required",
        ),
        (
            r"tap|faucet|pipe|shower|leak",
            r"leak|leaking|dripping|broken",
            "Maintenance",
            "Plumbing",
            "Plumbing leak",
        ),
    ]
    for obj, fault, category, problem, title in rules:
        if re.search(obj, low) and re.search(fault, low):
            data["category"] = {"value": category, "span": text, "confidence": 0.9}
            data["problem_type"] = {"value": problem, "span": text, "confidence": 0.9}
            data["title"] = title
            break
    return SmartReportResult.model_validate(data)


@router.post("/draft")
async def smart_draft(
    request: Request,
    text: str = Form(default=""),
    image: UploadFile | None = File(default=None),
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
):
    rate_limiter.check(
        client_key(request, "smartreport"),
        30,
        3600,
        "Too many SmartReport requests from this address. Try again later.",
    )
    if actor.role != "student":
        raise HTTPException(403, "SmartReport is available to students only")
    if not text.strip() and not image:
        raise HTTPException(422, "Provide a description or an image")
    if len(text) > settings.ai_max_chars:
        raise HTTPException(422, f"Description is limited to {settings.ai_max_chars} characters")
    data = None
    if image:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(415, "Unsupported image type")
        data = await image.read()
        if len(data) > settings.ai_max_image_bytes:
            raise HTTPException(413, "Image is too large; maximum is 5 MB")
    # SmartReport is intentionally limited to one use per student per calendar day.
    # The usage marker is stored in MySQL, so the limit survives API/container restarts.
    today = date.today()
    locked_actor = db.query(User).filter(User.id == actor.id).with_for_update().one()
    if locked_actor.smart_report_last_used_on == today:
        raise HTTPException(
            429, "Daily SmartReport limit reached. You can use SmartReport again tomorrow."
        )
    locked_actor.smart_report_last_used_on = today
    db.commit()
    options = _options(db)
    try:
        result = await asyncio.wait_for(
            provider.draft(text.strip(), options, data, image.content_type if image else None),
            timeout=settings.ai_timeout_seconds,
        )
        message = "SmartReport draft ready. Review the location and all suggested fields before submitting."
    except Exception as exc:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("SmartReport Gemini request failed: %s", exc)
        # The location extraction and classification fallback keeps the core form usable
        # when Gemini is temporarily unavailable. It never claims to have classified an image.
        result = _local_fallback(text.strip(), options)
        if image:
            result.image_observation = "The image could not be classified by Gemini right now. Please review the image-based asset/problem fields manually."
        message = "SmartReport used local text extraction because Gemini is temporarily unavailable. Review every field before submitting."
    return {"draft": _postprocess(result, options, text), "message": message}
