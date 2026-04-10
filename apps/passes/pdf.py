from io import BytesIO

from django.db.models import QuerySet
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AccessPass

HEADER_COLOR = colors.HexColor("#1a1a2e")
ROW_ALT_COLOR = colors.HexColor("#f2f2f2")


def build_passes_pdf(queryset: QuerySet[AccessPass], park_name: str) -> BytesIO:
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

    elements.append(Paragraph(f"Reporte de Pases — {park_name}", styles["Title"]))
    elements.append(Paragraph(f"Generado: {timezone.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    headers = ["ID", "Visitante", "Placa", "Destino", "Tipo", "Válido desde", "Válido hasta", "Estado", "Creado por"]
    rows = [headers]

    single_count = 0
    day_count = 0
    active_count = 0
    inactive_count = 0

    now = timezone.now()

    for pass_obj in queryset.iterator():
        created_by_name = ""
        if pass_obj.created_by:
            created_by_name = (
                f"{pass_obj.created_by.first_name} {pass_obj.created_by.last_name}".strip()
                or pass_obj.created_by.email
            )

        if pass_obj.is_active and pass_obj.valid_from <= now <= pass_obj.valid_to:
            status_label = "Activo"
        elif pass_obj.is_active and pass_obj.valid_from > now:
            status_label = "Próximo"
        elif pass_obj.valid_to < now:
            status_label = "Expirado"
        else:
            status_label = "Desactivado"

        rows.append([
            str(pass_obj.id),
            pass_obj.visitor_name,
            pass_obj.plate or "—",
            pass_obj.destination.name,
            pass_obj.get_pass_type_display(),
            pass_obj.valid_from.strftime("%d/%m/%Y %H:%M"),
            pass_obj.valid_to.strftime("%d/%m/%Y %H:%M"),
            status_label,
            created_by_name or "—",
        ])

        if pass_obj.pass_type == AccessPass.PassType.SINGLE:
            single_count += 1
        else:
            day_count += 1

        if pass_obj.is_active:
            active_count += 1
        else:
            inactive_count += 1

    col_widths = [1.2 * cm, 4 * cm, 2.5 * cm, 4 * cm, 2 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm, 4 * cm]

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

    total = single_count + day_count
    summary_data = [
        ["Total pases", "Single Use", "Day Pass", "Activos", "Inactivos"],
        [str(total), str(single_count), str(day_count), str(active_count), str(inactive_count)],
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
