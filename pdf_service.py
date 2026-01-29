# pdf_service.py
# ---------------------------------------------------------
# PDF GENERATION SERVICE (ASYNC)
# Uses ReportLab to create the "Legendary" design.
# Now runs in a separate thread to avoid UI blocking.
# ---------------------------------------------------------

import datetime
import os
import threading
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class PDFReportGenerator:

    def generate_async(self, subjects, total_avg, classification, filename, callback):
        """
        Generates PDF asynchronously in a separate thread.
        :param subjects: list of SubjectData objects
        :param total_avg: float
        :param classification: str
        :param filename: str
        :param callback: function to call with result (success, msg)
        """

        def task():
            result = self.generate(subjects, total_avg, classification, filename)
            if callback:
                callback(result)

        threading.Thread(target=task, daemon=True).start()

    def generate(self, subjects, total_avg, classification, filename):
        """
        Synchronous PDF generation (internal)
        """
        try:
            # --- Intelligent path selection ---
            android_path = "/storage/emulated/0/Download"
            desktop_path = os.path.join(os.path.expanduser("~"), "Downloads")

            if os.path.exists(android_path):
                save_dir = android_path
            else:
                save_dir = desktop_path
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

            full_path = os.path.join(save_dir, filename)
        except Exception as e:
            return False, f"Path Error: {str(e)}"

        # --- Design Palette ---
        C_PRIMARY = colors.HexColor("#2e004f")
        C_SECONDARY = colors.HexColor("#6c5ce7")

        def draw_background(c, doc):
            c.saveState()
            w, h = A4

            # Header Background
            c.setFillColor(C_PRIMARY)
            path = c.beginPath()
            path.moveTo(0, h)
            path.lineTo(w, h)
            path.lineTo(w, h - 140)
            path.lineTo(0, h - 100)
            path.close()
            c.drawPath(path, fill=1, stroke=0)

            # Header Text
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 24)
            c.drawRightString(w - 40, h - 50, "ACADEMIC REPORT")
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.HexColor("#dcdde1"))
            c.drawRightString(w - 40, h - 65, datetime.datetime.now().strftime("%d %B, %Y"))

            # Footer
            c.setStrokeColor(C_SECONDARY)
            c.setLineWidth(2)
            c.line(50, 50, w - 50, 50)
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.gray)
            c.drawString(50, 35, "ACADEMIC ANALYTICS SUITE")
            c.drawRightString(w - 50, 35, "Powered by Karim Dev")

            # Grade Badge
            cx, cy = w / 2, h - 160
            c.setStrokeColor(C_SECONDARY)
            c.setLineWidth(3)
            c.setFillColor(colors.white)
            c.circle(cx, cy, 60, fill=1, stroke=1)
            c.setFillColor(C_PRIMARY)
            c.circle(cx, cy, 52, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 26)
            c.drawCentredString(cx, cy + 6, f"{total_avg:.2f}")
            c.setFont("Helvetica", 10)
            c.drawCentredString(cx, cy - 15, "/ 20")
            c.setFillColor(C_SECONDARY)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(cx, cy - 85, f"PERFORMANCE: {classification.upper()}")
            c.restoreState()

        try:
            doc = SimpleDocTemplate(full_path, pagesize=A4, rightMargin=40, leftMargin=40,
                                    topMargin=280, bottomMargin=60)
            elements = []
            styles = getSampleStyleSheet()

            # Table
            style_h = ParagraphStyle('Header', parent=styles['Normal'], fontName='Helvetica-Bold',
                                     fontSize=10, textColor=C_PRIMARY, alignment=TA_CENTER)
            style_hl = ParagraphStyle('HeaderL', parent=style_h, alignment=TA_LEFT)

            headers = [Paragraph("SUBJECT", style_hl), Paragraph("AVG", style_h),
                       Paragraph("COEFF", style_h), Paragraph("WEIGHTED", style_h)]
            data = [headers]

            total_c = 0
            total_w = 0

            for sub in subjects:
                row = [
                    Paragraph(f"<b>{sub.name}</b>", styles['Normal']),
                    f"{sub.average:.2f}",
                    str(sub.coeff),
                    f"{sub.weighted_score:.2f}"
                ]
                data.append(row)
                total_c += sub.coeff
                total_w += sub.weighted_score

            data.append(["", "TOTALS", str(total_c), f"{total_w:.2f}"])

            t = Table(data, colWidths=[230, 100, 80, 100])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('LINEBELOW', (0, 0), (-1, 0), 2, C_PRIMARY),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor("#fdfbff")]),
                ('LINEABOVE', (1, -1), (-1, -1), 1, C_SECONDARY),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, -1), (-1, -1), C_PRIMARY),
            ]))
            elements.append(t)

            doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
            return True, f"Saved to: {full_path}"
        except Exception as e:
            return False, str(e)
