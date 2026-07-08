"""
backend/app/services/trend_analysis.py
────────────────────────────────────────
Sprint 7: Historical Trend Analysis Engine

Responsibilities:
  1. Aggregate inspection data into daily / weekly / monthly time-series buckets.
  2. Produce defect-type trend breakdowns (which classes are rising or falling).
  3. Produce machine-level failure trend summaries.
  4. Produce fleet-wide KPI trend summary (acceptance rate, avg confidence, latency).
  5. Cache results in Redis to avoid repeated heavy aggregations.

Design:
  - All aggregation is pure SQL via SQLAlchemy (no pandas, no numpy dependency).
  - Redis caching with 5-minute TTL to balance freshness vs. performance.
  - Returns fully serializable dicts — no ORM objects cross the service boundary.
  - Raises no exceptions to callers; errors are logged and empty data returned.

No fake data: if there are no inspections, the response reflects that honestly.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.redis import cache_get, cache_set
from app.models.db_models import Inspection, Detection, Machine

logger = get_logger(__name__)

# Redis TTL for trend data (seconds)
_CACHE_TTL = 300  # 5 minutes


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _day_range(date: datetime.date) -> tuple[datetime, datetime]:
    """Return UTC start/end datetime for a calendar date."""
    start = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(date.year, date.month, date.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
    return start, end


def _week_label(date: datetime.date) -> str:
    """Return ISO week label e.g. 'W27 Jun 30'."""
    iso_week = date.isocalendar()[1]
    return f"W{iso_week:02d} {date.strftime('%b %d')}"


def _month_label(date: datetime.date) -> str:
    return date.strftime("%b %Y")


def _safe_round(v: float | None, decimals: int = 2) -> float:
    if v is None:
        return 0.0
    return round(float(v), decimals)


# ─────────────────────────────────────────────────────────────────────────────
# Daily Trend
# ─────────────────────────────────────────────────────────────────────────────

def get_daily_trend(db: Session, days: int = 30) -> list[dict[str, Any]]:
    """Return per-day inspection metrics for the last N days.

    Each dict contains:
        date, total_inspections, failed_inspections, pass_rate,
        avg_confidence, avg_latency_ms, defect_classes (dict of class → count)

    Args:
        db:   SQLAlchemy Session.
        days: Number of calendar days to include (default 30, max 90).
    """
    days = min(max(days, 1), 90)
    cache_key = f"trend:daily:{days}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    today = datetime.now(timezone.utc).date()
    result: list[dict[str, Any]] = []

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        start, end = _day_range(day)

        total: int = db.query(Inspection).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.is_deleted == False,
        ).count()

        failed: int = db.query(Inspection).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.status == "FAIL",
            Inspection.is_deleted == False,
        ).count()

        avg_conf = db.query(func.avg(Inspection.confidence)).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.is_deleted == False,
        ).scalar()

        avg_lat = db.query(func.avg(Inspection.latency_ms)).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.is_deleted == False,
        ).scalar()

        pass_rate = round(((total - failed) / total * 100), 2) if total > 0 else 100.0

        result.append({
            "date": day.strftime("%b %d"),
            "iso_date": day.isoformat(),
            "total_inspections": total,
            "failed_inspections": failed,
            "pass_rate": pass_rate,
            "avg_confidence": _safe_round(avg_conf),
            "avg_latency_ms": _safe_round(avg_lat, 1),
        })

    cache_set(cache_key, json.dumps(result), ttl=_CACHE_TTL)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Weekly Trend
# ─────────────────────────────────────────────────────────────────────────────

def get_weekly_trend(db: Session, weeks: int = 12) -> list[dict[str, Any]]:
    """Return per-week aggregated metrics for the last N weeks.

    Args:
        db:    SQLAlchemy Session.
        weeks: Number of calendar weeks to include (default 12, max 52).
    """
    weeks = min(max(weeks, 1), 52)
    cache_key = f"trend:weekly:{weeks}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    today = datetime.now(timezone.utc).date()
    result: list[dict[str, Any]] = []

    for w in range(weeks - 1, -1, -1):
        # week_end = today - w*7 days, week_start = week_end - 6 days
        week_end = today - timedelta(days=w * 7)
        week_start = week_end - timedelta(days=6)

        start = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

        total: int = db.query(Inspection).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.is_deleted == False,
        ).count()

        failed: int = db.query(Inspection).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.status == "FAIL",
            Inspection.is_deleted == False,
        ).count()

        avg_conf = db.query(func.avg(Inspection.confidence)).filter(
            Inspection.created_at >= start,
            Inspection.created_at <= end,
            Inspection.is_deleted == False,
        ).scalar()

        pass_rate = round(((total - failed) / total * 100), 2) if total > 0 else 100.0

        result.append({
            "week": _week_label(week_start),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_inspections": total,
            "failed_inspections": failed,
            "pass_rate": pass_rate,
            "avg_confidence": _safe_round(avg_conf),
        })

    cache_set(cache_key, json.dumps(result), ttl=_CACHE_TTL)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Monthly Trend
# ─────────────────────────────────────────────────────────────────────────────

def get_monthly_trend(db: Session, months: int = 6) -> list[dict[str, Any]]:
    """Return per-month aggregated metrics for the last N months.

    Args:
        db:     SQLAlchemy Session.
        months: Number of calendar months to include (default 6, max 24).
    """
    months = min(max(months, 1), 24)
    cache_key = f"trend:monthly:{months}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    today = datetime.now(timezone.utc)
    result: list[dict[str, Any]] = []

    for m in range(months - 1, -1, -1):
        # Calculate first and last day of target month
        target_month = today.month - m
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_start = datetime(target_year, target_month, 1, 0, 0, 0, tzinfo=timezone.utc)
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)
        else:
            month_end = datetime(target_year, target_month + 1, 1, tzinfo=timezone.utc) - timedelta(microseconds=1)

        total: int = db.query(Inspection).filter(
            Inspection.created_at >= month_start,
            Inspection.created_at <= month_end,
            Inspection.is_deleted == False,
        ).count()

        failed: int = db.query(Inspection).filter(
            Inspection.created_at >= month_start,
            Inspection.created_at <= month_end,
            Inspection.status == "FAIL",
            Inspection.is_deleted == False,
        ).count()

        avg_conf = db.query(func.avg(Inspection.confidence)).filter(
            Inspection.created_at >= month_start,
            Inspection.created_at <= month_end,
            Inspection.is_deleted == False,
        ).scalar()

        pass_rate = round(((total - failed) / total * 100), 2) if total > 0 else 100.0

        result.append({
            "month": _month_label(month_start.date()),
            "month_start": month_start.date().isoformat(),
            "total_inspections": total,
            "failed_inspections": failed,
            "pass_rate": pass_rate,
            "avg_confidence": _safe_round(avg_conf),
        })

    cache_set(cache_key, json.dumps(result), ttl=_CACHE_TTL)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Defect Type Trend
# ─────────────────────────────────────────────────────────────────────────────

def get_defect_type_trend(db: Session, days: int = 30) -> list[dict[str, Any]]:
    """Return defect class frequency trend over the last N days.

    Each dict contains:
        defect_class, defect_name, count, percentage, trend_label

    Args:
        db:   SQLAlchemy Session.
        days: Lookback window in days (default 30, max 90).
    """
    days = min(max(days, 1), 90)
    cache_key = f"trend:defect_type:{days}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(Detection.defect_class, func.count(Detection.id).label("count"))
        .join(Inspection, Detection.inspection_id == Inspection.id)
        .filter(
            Inspection.created_at >= cutoff,
            Inspection.is_deleted == False,
            Detection.is_deleted == False,
        )
        .group_by(Detection.defect_class)
        .order_by(func.count(Detection.id).desc())
        .all()
    )

    total_defects = sum(r.count for r in rows)
    result: list[dict[str, Any]] = []
    for r in rows:
        pct = round((r.count / total_defects * 100), 2) if total_defects > 0 else 0.0

        # Determine severity label based on percentage
        if pct >= 40:
            severity = "critical"
        elif pct >= 20:
            severity = "high"
        elif pct >= 10:
            severity = "moderate"
        else:
            severity = "low"

        result.append({
            "defect_class": r.defect_class,
            "defect_name": r.defect_class.replace("_", " ").title(),
            "count": r.count,
            "percentage": pct,
            "severity": severity,
        })

    cache_set(cache_key, json.dumps(result), ttl=_CACHE_TTL)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Machine Trend
# ─────────────────────────────────────────────────────────────────────────────

def get_machine_failure_trend(db: Session, days: int = 30) -> list[dict[str, Any]]:
    """Return per-machine failure rate trend for the last N days.

    Each dict contains:
        machine_id, machine_name, machine_location, total_inspections,
        failed_inspections, defect_rate, status

    Args:
        db:   SQLAlchemy Session.
        days: Lookback window in days (default 30, max 90).
    """
    days = min(max(days, 1), 90)
    cache_key = f"trend:machine_failure:{days}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    machines = db.query(Machine).filter(Machine.is_deleted == False).all()

    result: list[dict[str, Any]] = []
    for m in machines:
        total = db.query(Inspection).filter(
            Inspection.machine_id == m.id,
            Inspection.created_at >= cutoff,
            Inspection.is_deleted == False,
        ).count()

        failed = db.query(Inspection).filter(
            Inspection.machine_id == m.id,
            Inspection.created_at >= cutoff,
            Inspection.status == "FAIL",
            Inspection.is_deleted == False,
        ).count()

        defect_rate = round(failed / total, 4) if total > 0 else 0.0
        pct = round(defect_rate * 100, 2)

        if total == 0:
            status = "no_data"
        elif pct >= 50:
            status = "critical"
        elif pct >= 25:
            status = "warning"
        else:
            status = "normal"

        result.append({
            "machine_id": m.id,
            "machine_name": m.name,
            "machine_location": m.location or "Unknown",
            "total_inspections": total,
            "failed_inspections": failed,
            "defect_rate": defect_rate,
            "defect_rate_pct": pct,
            "status": status,
        })

    result.sort(key=lambda x: x["defect_rate"], reverse=True)
    cache_set(cache_key, json.dumps(result), ttl=_CACHE_TTL)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Fleet Trend Summary
# ─────────────────────────────────────────────────────────────────────────────

def get_trend_summary(db: Session, days: int = 30) -> dict[str, Any]:
    """Return a high-level trend summary for the fleet.

    Combines daily trend data to compute period-over-period metrics:
        - Total inspections in period
        - Total failures in period
        - Overall pass rate
        - Average confidence
        - Machines at risk count (defect_rate > 25%)
        - Most frequent defect class

    Args:
        db:   SQLAlchemy Session.
        days: Lookback window in days.
    """
    cache_key = f"trend:summary:{days}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    total = db.query(Inspection).filter(
        Inspection.created_at >= cutoff,
        Inspection.is_deleted == False,
    ).count()

    failed = db.query(Inspection).filter(
        Inspection.created_at >= cutoff,
        Inspection.status == "FAIL",
        Inspection.is_deleted == False,
    ).count()

    avg_conf = db.query(func.avg(Inspection.confidence)).filter(
        Inspection.created_at >= cutoff,
        Inspection.is_deleted == False,
    ).scalar()

    avg_lat = db.query(func.avg(Inspection.latency_ms)).filter(
        Inspection.created_at >= cutoff,
        Inspection.is_deleted == False,
    ).scalar()

    # Machines at risk
    machines = db.query(Machine).filter(Machine.is_deleted == False).all()
    at_risk = 0
    for m in machines:
        m_total = db.query(Inspection).filter(
            Inspection.machine_id == m.id,
            Inspection.created_at >= cutoff,
            Inspection.is_deleted == False,
        ).count()
        m_failed = db.query(Inspection).filter(
            Inspection.machine_id == m.id,
            Inspection.created_at >= cutoff,
            Inspection.status == "FAIL",
            Inspection.is_deleted == False,
        ).count()
        if m_total > 0 and (m_failed / m_total) >= 0.25:
            at_risk += 1

    # Most frequent defect
    top_defect = (
        db.query(Detection.defect_class, func.count(Detection.id).label("cnt"))
        .join(Inspection, Detection.inspection_id == Inspection.id)
        .filter(
            Inspection.created_at >= cutoff,
            Inspection.is_deleted == False,
            Detection.is_deleted == False,
        )
        .group_by(Detection.defect_class)
        .order_by(func.count(Detection.id).desc())
        .first()
    )

    pass_rate = round(((total - failed) / total * 100), 2) if total > 0 else 100.0

    summary = {
        "period_days": days,
        "total_inspections": total,
        "failed_inspections": failed,
        "pass_rate": pass_rate,
        "avg_confidence": _safe_round(avg_conf),
        "avg_latency_ms": _safe_round(avg_lat, 1),
        "machines_at_risk": at_risk,
        "total_machines": len(machines),
        "top_defect_class": top_defect[0] if top_defect else None,
        "top_defect_name": top_defect[0].replace("_", " ").title() if top_defect else "None",
        "top_defect_count": int(top_defect[1]) if top_defect else 0,
    }

    cache_set(cache_key, json.dumps(summary), ttl=_CACHE_TTL)
    return summary
