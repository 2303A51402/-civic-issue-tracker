import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/reports", tags=["Reports"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-photo")
def upload_photo(file: UploadFile = File(...), user: models.User = Depends(get_current_user)):
    """Upload a report photo, returns a URL to reference in ReportCreate.photo_url.
    For production, swap this for a cloud storage upload (e.g. Cloudinary/S3) and
    return the hosted URL instead of a local path.
    """
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"photo_url": f"/{filepath}"}


@router.post("", response_model=schemas.ReportOut, status_code=201)
def create_report(
    payload: schemas.ReportCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    report = models.Report(
        user_id=user.id,
        category=payload.category,
        description=payload.description,
        photo_url=payload.photo_url,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=models.ReportStatus.reported,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    history = models.StatusHistory(
        report_id=report.id,
        old_status=None,
        new_status=models.ReportStatus.reported,
        changed_by=user.id,
    )
    db.add(history)
    db.commit()

    return report


@router.get("", response_model=List[schemas.ReportOut])
def list_reports(
    category: Optional[models.ReportCategory] = None,
    status: Optional[models.ReportStatus] = None,
    db: Session = Depends(get_db),
):
    """Public endpoint — powers the map view. Anyone can see reports and their status,
    which is the whole point of transparency in a civic tracker."""
    query = db.query(models.Report)
    if category:
        query = query.filter(models.Report.category == category)
    if status:
        query = query.filter(models.Report.status == status)
    return query.order_by(models.Report.created_at.desc()).all()


@router.get("/mine", response_model=List[schemas.ReportOut])
def my_reports(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Report).filter(models.Report.user_id == user.id).order_by(
        models.Report.created_at.desc()
    ).all()


@router.get("/{report_id}", response_model=schemas.ReportDetailOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}/status", response_model=schemas.ReportOut)
def update_status(
    report_id: str,
    payload: schemas.ReportStatusUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Admin-only. Updates status and logs it to StatusHistory so the BI dashboard
    can later compute accurate resolution-time analytics."""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    old_status = report.status
    report.status = payload.status
    if payload.status == models.ReportStatus.resolved:
        from datetime import datetime
        report.resolved_at = datetime.utcnow()

    history = models.StatusHistory(
        report_id=report.id,
        old_status=old_status,
        new_status=payload.status,
        changed_by=admin.id,
    )
    db.add(history)
    db.commit()
    db.refresh(report)
    return report


@router.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    """Admin-only summary stats — useful as a quick API-level analytics endpoint
    even before you plug the data into Power BI/Tableau."""
    from sqlalchemy import func

    by_category = (
        db.query(models.Report.category, func.count(models.Report.id))
        .group_by(models.Report.category)
        .all()
    )
    by_status = (
        db.query(models.Report.status, func.count(models.Report.id))
        .group_by(models.Report.status)
        .all()
    )
    total = db.query(models.Report).count()

    return {
        "total_reports": total,
        "by_category": {c.value: count for c, count in by_category},
        "by_status": {s.value: count for s, count in by_status},
    }
