from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Marca
from django.utils import timezone
from datetime import datetime
from django.urls import reverse

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
    
    # Si se envió el formulario con identificación
    if request.method == 'POST':
        identificacion = request.POST.get('identificacion', '').strip()
        if identificacion:
            return redirect('select_month', person_type=person_type, identificacion=identificacion)
        else:
            messages.error(request, "Por favor ingrese una identificación válida.")
    
    return render(request, 'attendance/select_identification.html', {
        'person_type': person_type,
        'person_type_display': 'Personal' if person_type == 'personal' else 'Estudiante'
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
