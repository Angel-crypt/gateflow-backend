from io import BytesIO

from django.db.models import QuerySet
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AccessPass

# Color palette
PRIMARY = colors.HexColor("#0F172A")
ACCENT = colors.HexColor("#2563EB")
ACCENT_LIGHT = colors.HexColor("#DBEAFE")
ROW_ALT = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")
MUTED = colors.HexColor("#94A3B8")
AMBER_LIGHT = colors.HexColor("#FEF3C7")
GREEN_LIGHT = colors.HexColor("#D1FAE5")
RED_LIGHT = colors.HexColor("#FEE2E2")
GRAY_LIGHT = colors.HexColor("#F1F5F9")
WHITE = colors.white

# Page content width: landscape A4 (29.7cm) minus margins (1.5cm x 2)
CONTENT_WIDTH = 26.7 * cm


def build_passes_pdf(queryset: QuerySet[AccessPass], park_name: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=WHITE,
        leading=19,
    )
    date_style = ParagraphStyle(
        "date",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=MUTED,
        alignment=TA_RIGHT,
        leading=13,
    )

    elements = []

    # --- Header banner ---
    header_data = [[
        Paragraph(f"{park_name}<br/><font size='9'>Reporte de Pases</font>", title_style),
        Paragraph(
            f"Generado el<br/><b><font color='#FFFFFF'>{timezone.now().strftime('%d/%m/%Y  %H:%M')}</font></b>",
            date_style,
        ),
    ]]
    header_table = Table(header_data, colWidths=[CONTENT_WIDTH * 0.72, CONTENT_WIDTH * 0.28])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (0, -1), 16),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 3, ACCENT),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5 * cm))

    # --- Data collection ---
    headers = ["ID", "Visitante", "Placa", "Destino", "Tipo", "Válido desde", "Válido hasta", "Estado", "Creado por"]
    rows = [headers]

    single_count = day_count = active_count = upcoming_count = expired_count = deactivated_count = 0

    now = timezone.now()

    for pass_obj in queryset.iterator():
        created_by_name = "N/A"
        if pass_obj.created_by:
            created_by_name = (
                f"{pass_obj.created_by.first_name} {pass_obj.created_by.last_name}".strip()
                or pass_obj.created_by.email
            )

        if pass_obj.is_active and pass_obj.valid_from <= now <= pass_obj.valid_to:
            status_label = "Activo"
            active_count += 1
        elif pass_obj.is_active and pass_obj.valid_from > now:
            status_label = "Próximo"
            upcoming_count += 1
        elif pass_obj.valid_to < now:
            status_label = "Expirado"
            expired_count += 1
        else:
            status_label = "Desactivado"
            deactivated_count += 1

        rows.append([
            str(pass_obj.id),
            pass_obj.visitor_name,
            pass_obj.plate or "N/A",
            pass_obj.destination.name,
            pass_obj.get_pass_type_display(),
            pass_obj.valid_from.strftime("%d/%m/%Y %H:%M"),
            pass_obj.valid_to.strftime("%d/%m/%Y %H:%M"),
            status_label,
            created_by_name,
        ])

        if pass_obj.pass_type == AccessPass.PassType.SINGLE:
            single_count += 1
        else:
            day_count += 1

    # --- Data table ---
    col_widths = [1.2 * cm, 4 * cm, 2.5 * cm, 4 * cm, 2 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm, 4 * cm]

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ROW_ALT]),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        # Borders
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        # Alignment
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("ALIGN", (5, 0), (6, -1), "CENTER"),
        ("ALIGN", (7, 0), (7, -1), "CENTER"),
        ("ALIGN", (1, 0), (3, -1), "LEFT"),
        ("ALIGN", (8, 0), (8, -1), "LEFT"),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("LEFTPADDING", (3, 0), (3, -1), 6),
        ("LEFTPADDING", (8, 0), (8, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.7 * cm))

    # --- Summary cards ---
    total = single_count + day_count
    summary_labels = [["Total", "Single Use", "Day Pass", "Activos", "Próximos", "Expirados", "Desactivados"]]
    summary_values = [[
        str(total),
        str(single_count),
        str(day_count),
        str(active_count),
        str(upcoming_count),
        str(expired_count),
        str(deactivated_count),
    ]]

    summary_table = Table(
        summary_labels + summary_values,
        colWidths=[2.8 * cm] * 7,
    )
    summary_table.setStyle(TableStyle([
        # Labels row
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (2, 0), WHITE),
        ("TEXTCOLOR", (3, 0), (3, 0), colors.HexColor("#065F46")),
        ("TEXTCOLOR", (4, 0), (4, 0), colors.HexColor("#92400E")),
        ("TEXTCOLOR", (5, 0), (5, 0), colors.HexColor("#991B1B")),
        ("TEXTCOLOR", (6, 0), (6, 0), colors.HexColor("#374151")),
        ("BACKGROUND", (0, 0), (2, 0), ACCENT),
        ("BACKGROUND", (3, 0), (3, 0), colors.HexColor("#10B981")),
        ("BACKGROUND", (4, 0), (4, 0), colors.HexColor("#F59E0B")),
        ("BACKGROUND", (5, 0), (5, 0), colors.HexColor("#FCA5A5")),
        ("BACKGROUND", (6, 0), (6, 0), colors.HexColor("#E2E8F0")),
        # Values row
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 14),
        ("TEXTCOLOR", (0, 1), (2, 1), ACCENT),
        ("TEXTCOLOR", (3, 1), (3, 1), colors.HexColor("#059669")),
        ("TEXTCOLOR", (4, 1), (4, 1), colors.HexColor("#D97706")),
        ("TEXTCOLOR", (5, 1), (5, 1), colors.HexColor("#DC2626")),
        ("TEXTCOLOR", (6, 1), (6, 1), colors.HexColor("#64748B")),
        ("BACKGROUND", (0, 1), (2, 1), ACCENT_LIGHT),
        ("BACKGROUND", (3, 1), (3, 1), GREEN_LIGHT),
        ("BACKGROUND", (4, 1), (4, 1), AMBER_LIGHT),
        ("BACKGROUND", (5, 1), (5, 1), RED_LIGHT),
        ("BACKGROUND", (6, 1), (6, 1), GRAY_LIGHT),
        # Shared
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEAFTER", (0, 0), (5, -1), 0.5, BORDER),
    ]))
    elements.append(summary_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
