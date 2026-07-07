"""
backend/app/services/gemma.py
─────────────────────────────
Rule-based defect explanation generator mimicking Gemma LLM reasoning.
"""

from __future__ import annotations
import json
from dataclasses import dataclass

@dataclass
class GemmaExplanationResult:
    explanation_text: str
    trust_score: float
    explanation_json: str

def generate_explanation(defect_class: str) -> GemmaExplanationResult:
    """Generates structured reasoning for visual defects, mimicking a fine-tuned Gemma LLM.

    Args:
        defect_class: The defect label returned by the YOLO model.

    Returns:
        GemmaExplanationResult containing text, score, and serialized JSON.
    """
    # Default fallback values
    severity = "Warning"
    causes = ["Mechanical stress", "Material handling error"]
    repairability = "Medium"
    prevention = "Perform regular calibration on production line guide rails."
    recommended_action = "Review recent inspection logs and notify line supervisor."
    trust_score = 0.92

    defect_lower = defect_class.lower()
    if "crack" in defect_lower:
        severity = "Critical"
        causes = [
            "Excessive thermal load during processing",
            "High concentration of stress points during metal forming",
            "Micro-voids in primary raw material stock"
        ]
        repairability = "Irreparable"
        prevention = "Implement pre-heating step for metal billets and monitor coolant flow rate hourly."
        recommended_action = "Stop CNC operation immediately. Discard the current part and check tool wear."
        trust_score = 0.95
    elif "scratch" in defect_lower:
        severity = "Warning"
        causes = [
            "Friction against machine guide rails",
            "Robotic grabber misaligned or exerting excessive force",
            "Abrasive particles in material transport tray"
        ]
        repairability = "Easy"
        prevention = "Install protective rubber sleeve on grippers and vacuum clean work area daily."
        recommended_action = "Wipe guide rails, re-align conveyor belts, and buff scratch out if depth is < 0.2mm."
        trust_score = 0.89
    elif "dent" in defect_lower:
        severity = "Critical"
        causes = [
            "Incorrect ejector pin pressure on mold",
            "Accidental impact during part ejection stage",
            "Incorrect clamping pressure alignment"
        ]
        repairability = "Medium"
        prevention = "Recalibrate ejector stroke limiters and check hydraulic valve seals."
        recommended_action = "Check machine pressure gauges, reset hydraulic limiters, and scrap the part if structural integrity is compromised."
        trust_score = 0.91

    explanation_dict = {
        "defect": defect_class,
        "severity": severity,
        "causes": causes,
        "repairability": repairability,
        "prevention": prevention,
        "recommended_action": recommended_action
    }

    explanation_text = (
        f"Gemma AI Quality Copilot Analysis:\n"
        f"- Severity: {severity}\n"
        f"- Causes: {', '.join(causes)}\n"
        f"- Repairability: {repairability}\n"
        f"- Prevention: {prevention}\n"
        f"- Recommended Action: {recommended_action}"
    )

    return GemmaExplanationResult(
        explanation_text=explanation_text,
        trust_score=trust_score,
        explanation_json=json.dumps(explanation_dict)
    )
