"""
backend/app/services/visualization_engine.py
─────────────────────────────────────────────
Visualization Engine for generating deterministic bounding box highlight overlays
and simulated XAI heatmaps.
"""

from sqlalchemy.orm import Session
from app.core.repository import inspection_repo
from app.models.db_models import AIExplanation, Inspection
from app.services.gemma import generate_explanation

def get_visualization_report(db: Session, inspection_id: str) -> dict:
    """Retrieve bounding box overlays, trust scoring, and mock explainability heatmaps.
    
    Generates a deterministic layout from YOLO detections to construct an SVG visual map,
    clearly labeled as 'Simulated Explainability'.
    """
    inspection = inspection_repo.get(db, inspection_id)
    if not inspection:
        return {}
        
    # Attempt to load Gemma reasoning from existing AIExplanation relation
    explanation = db.query(AIExplanation).filter(
        AIExplanation.inspection_id == inspection_id
    ).first()
    
    explanation_text = ""
    trust_score = 0.92
    structured_reasoning = {}
    
    if explanation:
        explanation_text = explanation.gemma_explanation
        trust_score = explanation.trust_score
        try:
            import json
            structured_reasoning = json.loads(explanation.explanation_json)
        except Exception:
            structured_reasoning = {}
    else:
        # Generate default rule-based explanation if missing
        defect_class = "general_anomaly"
        if inspection.detections:
            defect_class = inspection.detections[0].defect_class
        gemma_res = generate_explanation(defect_class)
        explanation_text = gemma_res.explanation_text
        trust_score = gemma_res.trust_score
        try:
            import json
            structured_reasoning = json.loads(gemma_res.explanation_json)
        except Exception:
            structured_reasoning = {}

    # Build heatmaps deterministically around defect detection zones
    heatmap_regions = []
    for index, det in enumerate(inspection.detections):
        # Scale bounding box to mock standard visual maps
        center_x = (det.x1 + det.x2) / 2.0
        center_y = (det.y1 + det.y2) / 2.0
        radius = max((det.x2 - det.x1), (det.y2 - det.y1), 0.1) * 0.7
        
        heatmap_regions.append({
            "region_id": f"heat_region_{index}",
            "x": center_x,
            "y": center_y,
            "radius": radius,
            "intensity": det.confidence,
            "label": det.defect_class
        })

    return {
        "inspection_id": inspection_id,
        "status": inspection.status,
        "overall_confidence": inspection.confidence,
        "inference_latency_ms": inspection.inference_time_ms,
        "trust_score": trust_score,
        "explanation": explanation_text,
        "structured_reasoning": structured_reasoning,
        "visualization_type": "simulated_explainability",
        "heatmap_regions": heatmap_regions,
        "model_metadata": {
            "model_architecture": "YOLOv8s Defect Detection",
            "weights_version": "production_best_v1",
            "classes": ["surface_crack", "scratch", "dent"]
        }
    }
