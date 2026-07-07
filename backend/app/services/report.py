"""
backend/app/services/report.py
──────────────────────────────
PDF, CSV, and JSON report generator using ReportLab and standard libraries.
"""

from __future__ import annotations
import io
import csv
from sqlalchemy.orm import Session
from app.models.db_models import Inspection

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_inspection_pdf(db: Session, inspection_id: str) -> bytes:
    """Generates a professional quality compliance report in PDF format.

    Uses HexColor palettes aligned with the design specification and embeds structured AI reasoning.
    """
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise ValueError("Inspection not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Premium deep blue & copper color palette
    primary_color = colors.HexColor("#0D47A1")
    accent_color = colors.HexColor("#E65100")
    text_color = colors.HexColor("#212121")
    light_bg = colors.HexColor("#F5F5F5")

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=primary_color,
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=accent_color,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        textColor=text_color,
        leading=13
    )

    bold_body_style = ParagraphStyle(
        "ReportBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    story = []

    story.append(Paragraph("NIKA AI QUALITY INSPECTION CERTIFICATE", title_style))
    story.append(Spacer(1, 10))

    meta_data = [
        [Paragraph("Inspection ID:", bold_body_style), Paragraph(str(inspection.id), body_style)],
        [Paragraph("Timestamp:", bold_body_style), Paragraph(inspection.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style)],
        [Paragraph("Status:", bold_body_style), Paragraph(inspection.status, ParagraphStyle("StatusTxt", parent=bold_body_style, textColor=colors.HexColor("#2E7D32") if inspection.status == "PASS" else colors.HexColor("#C62828")))],
        [Paragraph("Operator:", bold_body_style), Paragraph(inspection.worker.name if inspection.worker else "Default", body_style)],
        [Paragraph("Machine Name:", bold_body_style), Paragraph(inspection.machine.name if inspection.machine else "Default", body_style)],
        [Paragraph("Inference Duration:", bold_body_style), Paragraph(f"{inspection.inference_time_ms:.1f} ms", body_style)]
    ]
    
    t_meta = Table(meta_data, colWidths=[130, 370])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), light_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    story.append(Paragraph("AI Detections Breakdown", section_style))
    story.append(Spacer(1, 4))

    if inspection.detections:
        detection_data = [[
            Paragraph("Class", bold_body_style),
            Paragraph("Confidence", bold_body_style),
            Paragraph("Bounding Box (x1, y1, x2, y2)", bold_body_style)
        ]]
        for det in inspection.detections:
            bbox_str = f"({det.x1:.1f}, {det.y1:.1f}, {det.x2:.1f}, {det.y2:.1f})"
            detection_data.append([
                Paragraph(det.defect_class.replace("_", " ").title(), body_style),
                Paragraph(f"{det.confidence * 100:.2f}%", body_style),
                Paragraph(bbox_str, body_style)
            ])
        t_det = Table(detection_data, colWidths=[150, 100, 250])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E0E0E0")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        story.append(t_det)
    else:
        story.append(Paragraph("No defects detected. Part meets quality compliance criteria.", body_style))
    
    story.append(Spacer(1, 12))

    story.append(Paragraph("AI Quality Copilot Reasoning", section_style))
    story.append(Spacer(1, 4))

    if inspection.explanation:
        expl = inspection.explanation
        story.append(Paragraph(f"<b>Trust Score:</b> {expl.trust_score * 100:.1f}%", body_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(expl.gemma_explanation, body_style))
    else:
        story.append(Paragraph("No explanation generated.", body_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def generate_csv_export(db: Session, inspection_ids: list[str]) -> str:
    """Exports inspection historical details as raw CSV data."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Inspection ID", "Timestamp", "Status", "Inference Time (ms)", "Average Confidence", 
        "Machine Name", "Operator Name", "Defect Classes Found"
    ])
    
    inspections = db.query(Inspection).filter(Inspection.id.in_(inspection_ids)).all()
    for ins in inspections:
        defect_classes = ",".join([d.defect_class for d in ins.detections])
        writer.writerow([
            ins.id,
            ins.created_at.isoformat(),
            ins.status,
            ins.inference_time_ms,
            ins.confidence,
            ins.machine.name if ins.machine else "N/A",
            ins.worker.name if ins.worker else "N/A",
            defect_classes or "None"
        ])
        
    return output.getvalue()
