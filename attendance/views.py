from io import BytesIO
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.urls import reverse

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak

from .models import Marca

WEEKDAY_NAMES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
MONTHS = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
]

@login_required
def attendance_list(request):
    """Página principal con botones para seleccionar tipo de persona"""
    if request.user.profile.role.name != 'admin':
        # Para usuarios no admin, mostrar sus propias marcas
        identificacion = getattr(request.user, 'personal', None)
        if identificacion:
            identificacion = identificacion.identificacion
        else:
            identificacion = getattr(request.user, 'estudiante', None)
            if identificacion:
                identificacion = identificacion.identificacion
        if identificacion:
            marcas = Marca.objects.filter(identificacion=identificacion).order_by('-fecha_hora')[:10]  # Últimas 10
            return render(request, 'attendance/user_marks.html', {'marcas': marcas})
        else:
            messages.error(request, "No se encontró su información de identificación.")
            return redirect('home')
    
    # Para admin, mostrar página con botones
    return render(request, 'attendance/select_type.html')

@login_required
def select_person_type(request, person_type):
    """Página para seleccionar identificación según tipo de persona"""
    if request.user.profile.role.name != 'admin':
        return redirect('attendance_list')
    
    if person_type not in ['personal', 'estudiante']:
        messages.error(request, "Tipo de persona inválido.")
        return redirect('attendance_list')
    
    selected_month = request.GET.get('month', '')
    
    # Si se envió el formulario con identificación
    if request.method == 'POST':
        identificacion = request.POST.get('identificacion', '').strip()
        if identificacion:
            return redirect('select_month', person_type=person_type, identificacion=identificacion)
        else:
            messages.error(request, "Por favor ingrese una identificación válida.")
    
    return render(request, 'attendance/select_identification.html', {
        'person_type': person_type,
        'person_type_display': 'Personal' if person_type == 'personal' else 'Estudiante',
        'months': MONTHS,
        'selected_month': selected_month,
    })

@login_required
def select_month(request, person_type, identificacion):
    """Página para seleccionar mes y mostrar marcas"""
    if request.user.profile.role.name != 'admin':
        return redirect('attendance_list')
    
    if person_type not in ['personal', 'estudiante']:
        messages.error(request, "Tipo de persona inválido.")
        return redirect('attendance_list')
    
    # Verificar que la identificación existe
    from users.models import Personal, Estudiante
    persona = None
    if person_type == 'personal':
        persona = Personal.objects.filter(identificacion=identificacion).first()
    else:
        persona = Estudiante.objects.filter(identificacion=identificacion).first()
    
    if not persona:
        messages.error(request, f"No se encontró {'personal' if person_type == 'personal' else 'estudiante'} con identificación {identificacion}.")
        return redirect('select_person_type', person_type=person_type)
    
    # Si se seleccionó un mes, filtrar las marcas
    selected_month = request.GET.get('month')
    marcas = Marca.objects.filter(identificacion=identificacion).order_by('-fecha_hora')
    
    if selected_month:
        try:
            month_num = int(selected_month)
            if 1 <= month_num <= 12:
                # Filtrar por mes y año actual
                current_year = timezone.now().year
                marcas = marcas.filter(
                    fecha_hora__year=current_year,
                    fecha_hora__month=month_num
                )
        except ValueError:
            pass
    
    # Meses disponibles
    months = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    return render(request, 'attendance/monthly_report.html', {
        'persona': persona,
        'person_type': person_type,
        'person_type_display': 'Personal' if person_type == 'personal' else 'Estudiante',
        'identificacion': identificacion,
        'marcas': marcas,
        'months': months,
        'selected_month': selected_month,
        'current_year': timezone.now().year
    })


def _get_general_personal_rows(personal, selected_month):
    from users.models import Personal

    identificacion = personal.identificacion
    marcas = Marca.objects.filter(identificacion=identificacion).order_by('fecha_hora')
    if selected_month:
        try:
            month_num = int(selected_month)
            if 1 <= month_num <= 12:
                current_year = timezone.now().year
                marcas = marcas.filter(
                    fecha_hora__year=current_year,
                    fecha_hora__month=month_num
                )
        except ValueError:
            pass

    date_rows = []
    for marca in marcas:
        date_rows.append([
            marca.fecha_hora.strftime('%d/%m/%Y'),
            WEEKDAY_NAMES[marca.fecha_hora.weekday()],
            marca.fecha_hora.strftime('%I:%M %p'),
        ])

    return date_rows


def _generate_general_personal_pdf_buffer(personal_list, selected_month):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=10,
        leading=12,
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=6,
    )
    person_title_style = ParagraphStyle(
        'PersonTitle',
        parent=styles['Heading3'],
        alignment=TA_LEFT,
        fontSize=11,
        leading=14,
        spaceAfter=4,
    )

    generated_text = timezone.now().strftime('%d/%m/%Y %I:%M %p')
    periodo_text = 'Todas las marcas'
    if selected_month:
        month_num = int(selected_month) if selected_month.isdigit() else None
        if month_num and 1 <= month_num <= 12:
            periodo_text = f'Mes de {MONTHS[month_num - 1][1]} {timezone.now().year}'

    elements.append(Paragraph('Dirección Regional de Educación Alajuela', title_style))
    elements.append(Paragraph('Supervisión Educativa Circuito 01', subtitle_style))
    elements.append(Paragraph('Colegio Técnico Profesional de Carrizal', subtitle_style))
    elements.append(Paragraph('Informe General de Asistencia Institucional - Personal', subtitle_style))
    elements.append(Paragraph(f'Generado: {generated_text}', normal_style))
    elements.append(Paragraph(periodo_text, normal_style))
    elements.append(Spacer(1, 12))

    for index, personal in enumerate(personal_list):
        person_name = f'{personal.apellido1} {personal.apellido2 or ""}, {personal.nombre}'
        elements.append(Paragraph(person_name, person_title_style))
        elements.append(Paragraph(f'Identificación: {personal.identificacion or "-"}', normal_style))

        marcas = Marca.objects.filter(identificacion=personal.identificacion).order_by('fecha_hora')
        if selected_month:
            try:
                month_num = int(selected_month)
                if 1 <= month_num <= 12:
                    marcas = marcas.filter(
                        fecha_hora__year=timezone.now().year,
                        fecha_hora__month=month_num,
                    )
            except ValueError:
                pass

        rows = _build_pdf_rows(marcas)
        table_data = [[
            'Fecha', 'Día', 'Entrada', 'Marca 2', 'Marca 3', 'Marca 4', 'Marca 5', 'Salida'
        ]]

        if rows:
            table_data.extend(rows)
        else:
            table_data.append(['No hay marcas registradas', '', '', '', '', '', '', ''])

        report_table = Table(table_data, colWidths=[65, 65, 60, 60, 60, 60, 60, 60])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('LINEBEFORE', (0, 0), (-1, -1), 0.25, colors.gray),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        elements.append(report_table)

        if index < len(personal_list) - 1:
            elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer


def download_general_personal_pdf(request):
    if request.user.profile.role.name != 'admin':
        return redirect('attendance_list')

    selected_month = request.GET.get('month', '')
    from users.models import Personal
    personal_list = Personal.objects.order_by('apellido1', 'apellido2', 'nombre')
    buffer = _generate_general_personal_pdf_buffer(personal_list, selected_month)

    filename = 'reporte_general_personal'
    if selected_month:
        filename += f'_mes_{selected_month}'
    filename += '.pdf'

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _get_person_by_type(person_type, identificacion):
    from users.models import Personal, Estudiante
    if person_type == 'personal':
        return Personal.objects.filter(identificacion=identificacion).first()
    return Estudiante.objects.filter(identificacion=identificacion).first()


def _get_filtered_marcas(identificacion, selected_month):
    marcas = Marca.objects.filter(identificacion=identificacion).order_by('fecha_hora')

    if selected_month:
        try:
            month_num = int(selected_month)
            if 1 <= month_num <= 12:
                current_year = timezone.now().year
                marcas = marcas.filter(
                    fecha_hora__year=current_year,
                    fecha_hora__month=month_num
                )
        except ValueError:
            pass

    return marcas


def _build_pdf_rows(marcas):
    rows = []
    fechas = {}

    for marca in marcas:
        fecha = marca.fecha_hora.date()
        fechas.setdefault(fecha, []).append(marca.fecha_hora.time())

    for fecha, times in sorted(fechas.items()):
        times = sorted(times)
        day_name = WEEKDAY_NAMES[fecha.weekday()]

        first_time = times[0].strftime('%I:%M %p') if times else ''
        last_time = times[-1].strftime('%I:%M %p') if len(times) > 1 else ''
        mid_times = [t.strftime('%I:%M %p') for t in times[1:-1]]

        while len(mid_times) < 4:
            mid_times.append('')

        rows.append([
            fecha.strftime('%d/%m/%Y'),
            day_name,
            first_time,
            mid_times[0],
            mid_times[1],
            mid_times[2],
            mid_times[3],
            last_time,
        ])

    return rows


def _generate_pdf_buffer(persona, person_type_display, identificacion, marcas, selected_month):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=10,
        leading=12,
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
    )

    elements.append(Paragraph('Dirección Regional de Educación Alajuela', title_style))
    elements.append(Paragraph('Supervisión Educativa Circuito 01', subtitle_style))
    elements.append(Paragraph('Colegio Técnico Profesional de Carrizal', subtitle_style))
    elements.append(Paragraph('Informe de Asistencia Mensual Institucional', subtitle_style))
    elements.append(Spacer(1, 12))

    periodo_text = 'Todas las marcas'
    if selected_month:
        months = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        month_num = int(selected_month) if selected_month.isdigit() else None
        if month_num and 1 <= month_num <= 12:
            periodo_text = f'Mes de {months[month_num]} {timezone.now().year}'

    header_data = [
        ['Funcionario:', f'{persona.nombre} {persona.apellido1} {persona.apellido2 or ""}'],
        ['Identificación:', identificacion],
        ['Periodo:', periodo_text],
    ]

    header_table = Table(header_data, colWidths=[100, 340])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    table_data = [
        ['Fecha', 'Día', 'Entrada', 'Marca 2', 'Marca 3', 'Marca 4', 'Marca 5', 'Salida']
    ]
    table_data.extend(_build_pdf_rows(marcas))

    if len(table_data) == 1:
        table_data.append(['No hay marcas registradas en el periodo seleccionado.', '', '', '', '', '', '', ''])

    report_table = Table(table_data, colWidths=[65, 65, 60, 60, 60, 60, 60, 60])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('LINEBEFORE', (0, 0), (-1, -1), 0.25, colors.gray),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(report_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def download_report_pdf(request, person_type, identificacion):
    if request.user.profile.role.name != 'admin':
        return redirect('attendance_list')

    persona = _get_person_by_type(person_type, identificacion)
    if not persona:
        messages.error(request, f"No se encontró {'personal' if person_type == 'personal' else 'estudiante'} con identificación {identificacion}.")
        return redirect('select_person_type', person_type=person_type)

    selected_month = request.GET.get('month')
    marcas = _get_filtered_marcas(identificacion, selected_month)
    buffer = _generate_pdf_buffer(persona, 'Personal' if person_type == 'personal' else 'Estudiante', identificacion, marcas, selected_month)

    filename = f"reporte_marcas_{identificacion}"
    if selected_month:
        filename += f"_mes_{selected_month}"
    filename += ".pdf"

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
