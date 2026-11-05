"""Semantic problem-to-location constraints shared by issue create and update flows."""
from fastapi import HTTPException

# Explicitly location-bound problem types. Other general problems remain reportable
# in any area because the same fault (e.g. electrical or plumbing) can occur widely.
PROBLEM_AREA_RULES = {
    "Washing machine": {"washing_machine_area"},
    "Washing machine area cleaning": {"washing_machine_area"},
    "Lift malfunction": {"lift_lobby"},
    "Unclean lift lobby": {"lift_lobby"},
    "Water dispenser": {"drinking_water_area"},
    "Water area hygiene": {"drinking_water_area"},
    "Drinking water area cleaning": {"drinking_water_area"},
    "Toilet cleaning": {"toilet"},
    "Bathroom cleaning": {"bathroom"},
    "Corridor cleaning": {"corridor"},
    "Cloth drying area cleaning": {"cloth_drying_area"},
}

def validate_problem_location(problem_type, location):
    allowed = PROBLEM_AREA_RULES.get(problem_type.name)
    if allowed and location.area_type not in allowed:
        readable = ", ".join(area.replace("_", " ") for area in sorted(allowed))
        raise HTTPException(
            status_code=422,
            detail=f"'{problem_type.name}' must be reported in: {readable}.",
        )
