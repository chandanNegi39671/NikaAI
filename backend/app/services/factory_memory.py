"""
backend/app/services/factory_memory.py
──────────────────────────────────────
Factory Memory Knowledge Base Service for Nika AI.
"""

from __future__ import annotations
import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.db_models import FactoryMemory, Inspection, Detection, Machine
from app.core.redis import cache_get, cache_set

def get_factory_memories(db: Session, query: str | None = None) -> list[dict]:
    """Retrieve historical defect classes, recommended actions, and occurrence metrics.

    Provides basic text search across classes and patterns. Results are cached.
    """
    cache_key = f"factory_memory:query:{query or 'ALL'}"
    cached = cache_get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except Exception:
            pass

    q = db.query(FactoryMemory)
    if query:
        search = f"%{query}%"
        q = q.filter(
            (FactoryMemory.defect_class.like(search)) |
            (FactoryMemory.description.like(search)) |
            (FactoryMemory.recurring_defect_pattern.like(search))
        )
    
    results = q.all()
    
    response = []
    for fm in results:
        # Calculate occurrences dynamically
        total_occurrences = db.query(Detection).filter(
            Detection.defect_class == fm.defect_class,
            Detection.is_deleted == False
        ).count()
        
        # Resolve top risk machine dynamically
        risk_machine = "None"
        top_machine = db.query(
            Inspection.machine_id, func.count(Inspection.id).label("count")
        ).join(Detection, Detection.inspection_id == Inspection.id).filter(
            Detection.defect_class == fm.defect_class,
            Inspection.is_deleted == False
        ).group_by(Inspection.machine_id).order_by(
            func.count(Inspection.id).desc()
        ).first()
        
        if top_machine and top_machine[0]:
            mach = db.query(Machine).filter(Machine.id == top_machine[0]).first()
            if mach:
                risk_machine = mach.name

        response.append({
            "id": fm.id,
            "defectClass": fm.defect_class,
            "defectName": fm.defect_class.replace("_", " ").title(),
            "description": fm.description,
            "recurringPattern": fm.recurring_defect_pattern,
            "recommendedAction": fm.recommended_action,
            "totalOccurrences": total_occurrences,
            "topRiskMachine": risk_machine
        })
        
    cache_set(cache_key, json.dumps(response), ttl=300)
    return response
