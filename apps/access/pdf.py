from io import BytesIO

from django.db.models import QuerySet
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AccessLog

HEADER_COLOR = colors.HexColor("#1a1a2e")
ROW_ALT_COLOR = colors.HexColor("#f2f2f2")


def build_access_logs_pdf(queryset: QuerySet[AccessLog], park_name: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # Título
    elements.append(Paragraph(f"Reporte de Accesos — {park_name}", styles["Title"]))
    elements.append(Paragraph(f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Encabezados de tabla
    headers = ["ID", "Visitante", "Placa", "Destino", "Tipo", "Guardia", "Entrada", "Salida", "Estado"]
    rows = [headers]

    qr_count = 0
    manual_count = 0
    open_count = 0
    closed_count = 0

    for log in queryset.iterator():
        guard_name = ""
        if log.guard:
            guard_name = f"{log.guard.first_name} {log.guard.last_name}".strip() or log.guard.email

        rows.append([
            str(log.id),
            log.visitor_name,
            log.plate or "—",
            log.destination.name,
            log.get_access_type_display(),
            guard_name or "—",
            log.entry_time.strftime("%d/%m/%Y %H:%M"),
            log.exit_time.strftime("%d/%m/%Y %H:%M") if log.exit_time else "—",
            log.get_status_display(),
        ])

        if log.access_type == AccessLog.AccessType.QR:
            qr_count += 1
        else:
            manual_count += 1

        if log.status == AccessLog.Status.OPEN:
            open_count += 1
        else:
            closed_count += 1

    col_widths = [1.2 * cm, 4 * cm, 2.5 * cm, 4 * cm, 2 * cm, 4 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT_COLOR]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.8 * cm))

    # Resumen
    total = qr_count + manual_count
    summary_data = [
        ["Total registros", "QR", "Manual", "Abiertos", "Cerrados"],
        [str(total), str(qr_count), str(manual_count), str(open_count), str(closed_count)],
    ]
    summary_table = Table(summary_data, colWidths=[4 * cm] * 5)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
