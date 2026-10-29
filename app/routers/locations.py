from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Hostel, Floor, Wing, Location, Category, ProblemType, Asset, AssetLocation

router = APIRouter(tags=["Locations and Categories"])
@router.get("/hostels")
def hostels(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    query = db.query(Hostel); total = query.count()
    return {"items": query.order_by(Hostel.id).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
@router.get("/hostels/{hostel_id}/floors")
def floors(hostel_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    if not db.get(Hostel, hostel_id): raise HTTPException(404, "Hostel not found")
    query = db.query(Floor).filter_by(hostel_id=hostel_id); total = query.count()
    return {"items": query.order_by(Floor.floor_number).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
@router.get("/floors/{floor_id}/wings")
def wings(floor_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    if not db.get(Floor, floor_id): raise HTTPException(404, "Floor not found")
    query = db.query(Wing).filter_by(floor_id=floor_id); total = query.count()
    return {"items": query.order_by(Wing.wing_name).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
@router.get("/wings/{wing_id}/locations")
def locations(wing_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    if not db.get(Wing, wing_id): raise HTTPException(404, "Wing not found")
    query = db.query(Location).filter_by(wing_id=wing_id); total = query.count()
    return {"items": query.order_by(Location.area_type).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
@router.get("/categories")
def categories(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    query = db.query(Category); total = query.count()
    return {"items": query.order_by(Category.name).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
@router.get("/categories/{category_id}/problem-types")
def problem_types(category_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    if not db.get(Category, category_id): raise HTTPException(404, "Category not found")
    query = db.query(ProblemType).filter_by(category_id=category_id); total = query.count()
    return {"items": query.order_by(ProblemType.name).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
@router.get("/locations/{location_id}/assets")
def assets(location_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    if not db.get(Location, location_id): raise HTTPException(404, "Location not found")
    query = db.query(Asset).join(AssetLocation).filter(AssetLocation.location_id == location_id); total = query.count()
    return {"items": query.order_by(Asset.name).offset((page-1)*size).limit(size).all(), "page": page, "size": size, "total": total}
