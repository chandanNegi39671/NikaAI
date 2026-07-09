"""
backend/app/api/endpoints/analytics.py
──────────────────────────────────────
Endpoints for business intelligence dashboards and report downloading.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.auth import PermissionChecker
from app.core.database import get_db
from app.services.analytics import get_dashboard_analytics
from app.services.report import generate_csv_export, generate_inspection_pdf

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics & Reports"],
    dependencies=[Depends(PermissionChecker("analytics:read"))],
)


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    """Retrieve standard system telemetry, quality stats, and trend chart segments."""
    return get_dashboard_analytics(db)


@router.get("/report/pdf/{inspection_id}")
def download_pdf_report(inspection_id: str, db: Session = Depends(get_db)):
    """Generate and stream a professional PDF visual quality report."""
    try:
        pdf_bytes = generate_inspection_pdf(db, inspection_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=inspection_report_{inspection_id}.pdf"
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        )


@router.get("/report/csv")
def download_csv_report(
    ids: list[str] = Query(..., description="List of inspection IDs to export"),
    db: Session = Depends(get_db),
):
    """Compile selected inspections into a structured CSV file."""
    try:
        csv_str = generate_csv_export(db, ids)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=inspections_export.csv"
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CSV generation failed: {exc}",
        )
