import csv
import io
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.services.adherence_service import AdherenceService
from app.services.medication_service import MedicationService


class ReportService:

    def __init__(self) -> None:
        self.adherence = AdherenceService()
        self.medications = MedicationService()

    def export_csv(self, db: Session, user_id: int) -> bytes:
        report = self.adherence.report(db, user_id)
        heatmap = self.adherence.heatmap(db, user_id)
        meds = self.medications.list_for_user(db, user_id)

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["MediGuardian Adherence Report"])
        writer.writerow(["Generated", datetime.utcnow().isoformat()])
        writer.writerow(["User ID", user_id])
        writer.writerow([])
        writer.writerow(["Summary"])
        for key, value in report.items():
            writer.writerow([key, value])
        writer.writerow([])
        writer.writerow(["Medications"])
        writer.writerow(["ID", "Name", "Dosage"])
        for med in meds:
            writer.writerow([med.id, med.name, med.dosage])
        writer.writerow([])
        writer.writerow(["Daily Heatmap"])
        writer.writerow(["Date", "Taken", "Missed", "Skipped"])
        for day in heatmap:
            writer.writerow([
                day["date"],
                day.get("taken", 0),
                day.get("missed", 0),
                day.get("skipped", 0),
            ])
        return buffer.getvalue().encode("utf-8")

    def export_pdf(self, db: Session, user_id: int) -> bytes:
        report = self.adherence.report(db, user_id)
        meds = self.medications.list_for_user(db, user_id)
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("<b>MediGuardian Adherence Report</b>", styles["Title"]),
            Spacer(1, 12),
            Paragraph(f"User ID: {user_id}", styles["Normal"]),
            Paragraph(
                f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                styles["Normal"],
            ),
            Spacer(1, 16),
            Paragraph("<b>Summary</b>", styles["Heading2"]),
        ]

        summary_data = [["Metric", "Value"]] + [
            [k.replace("_", " ").title(), str(v)] for k, v in report.items()
        ]
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d9488")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 16))
        story.append(Paragraph("<b>Active Medications</b>", styles["Heading2"]))

        med_data = [["Name", "Dosage"]] + [[m.name, m.dosage] for m in meds]
        med_table = Table(med_data, colWidths=[250, 150])
        med_table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(med_table)

        doc.build(story)
        return buffer.getvalue()
