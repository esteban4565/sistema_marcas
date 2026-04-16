from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse
from .models import Role, Personal, Estudiante
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from urllib.parse import quote_plus

class IndexView(TemplateView):
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_time'] = datetime.now()
        
        # Obtener las últimas 10 marcas con información de las personas
        from attendance.models import Marca
        from .models import Personal, Estudiante
        
        ultimas_marcas = Marca.objects.select_related().order_by('-fecha_hora')[:10]
        marcas_con_info = []
        
        for marca in ultimas_marcas:
            persona_info = {
                'identificacion': marca.identificacion,
                'fecha_hora': marca.fecha_hora,
                'tipo_persona': marca.tipo_persona,
                'nombre_completo': marca.identificacion  # fallback
            }
            
            # Buscar información de la persona
            if marca.tipo_persona == 'personal':
                try:
                    persona = Personal.objects.get(identificacion=marca.identificacion)
                    persona_info['nombre_completo'] = f"{persona.nombre} {persona.apellido1} {persona.apellido2 or ''}".strip()
                except Personal.DoesNotExist:
                    pass
            elif marca.tipo_persona == 'estudiante':
                try:
                    persona = Estudiante.objects.get(identificacion=marca.identificacion)
                    persona_info['nombre_completo'] = f"{persona.nombre} {persona.apellido1} {persona.apellido2 or ''}".strip()
                except Estudiante.DoesNotExist:
                    pass
            
            marcas_con_info.append(persona_info)
        
        context['ultimas_marcas'] = marcas_con_info
        return context
    
    def post(self, request, *args, **kwargs):
        identificacion = request.POST.get('identification', '').strip()
        if identificacion:
            from attendance.models import Marca
            # Crear la marca
            marca = Marca.objects.create(identificacion=identificacion)
            # Verificar si existe la persona
            from .models import Personal, Estudiante
            persona = None
            if Personal.objects.filter(identificacion=identificacion).exists():
                persona = Personal.objects.get(identificacion=identificacion)
                marca.tipo_persona = 'personal'
                marca.save()
            elif Estudiante.objects.filter(identificacion=identificacion).exists():
                persona = Estudiante.objects.get(identificacion=identificacion)
                marca.tipo_persona = 'estudiante'
                marca.save()
            
            # Mensaje de éxito
            messages.success(request, f"Marca registrada exitosamente para {persona.nombre if persona else identificacion}")
        else:
            messages.error(request, "Por favor ingrese una identificación válida")
        
        return redirect('home')

class AdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.profile.role.name == 'admin'
    
    def handle_no_permission(self):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/dashboard/')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'users/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.request.user.profile.role.name
        return context

class RoleListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = Role
    template_name = 'users/role_list.html'
    context_object_name = 'roles'

class RoleCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = Role
    template_name = 'users/role_form.html'
    fields = ['name']
    success_url = reverse_lazy('role_list')

class RoleUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Role
    template_name = 'users/role_form.html'
    fields = ['name']
    success_url = reverse_lazy('role_list')

class RoleDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):
    model = Role
    template_name = 'users/role_confirm_delete.html'
    success_url = reverse_lazy('role_list')

class UserListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return User.objects.all()

class UserCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Asignar role default
        default_role = Role.objects.get(name='estudiante')
        from .models import Profile
        Profile.objects.create(user=self.object, role=default_role)
        return response

class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')

    def get_queryset(self):
        if self.request.user.profile.role.name == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class UserDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

class PersonalListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = Personal
    template_name = 'users/personal_list.html'
    context_object_name = 'personales'

class PersonalCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = Personal
    template_name = 'users/personal_form.html'
    fields = ['identificacion', 'nombre', 'apellido1', 'apellido2', 'email', 'telefono', 'puesto', 'fecha_nacimiento', 'departamento', 'titulo', 'horario', 'estado']
    success_url = reverse_lazy('personal_list')

    def form_valid(self, form):
        identificacion = form.cleaned_data['identificacion']
        if User.objects.filter(username=identificacion).exists():
            from django.contrib import messages
            messages.error(self.request, f"La identificación {identificacion} ya existe.")
            return self.form_invalid(form)
        puesto = form.cleaned_data['puesto']
        password = ('D' if puesto == 'Docente' else 'A') + identificacion + '*'
        user = User.objects.create_user(username=identificacion, password=password)
        role_name = 'docente' if puesto == 'Docente' else 'administrativo'
        role = Role.objects.get(name=role_name)
        from .models import Profile
        Profile.objects.filter(user=user).delete()
        Profile.objects.create(user=user, role=role)
        form.instance.user = user
        return super().form_valid(form)

class PersonalUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Personal
    template_name = 'users/personal_form.html'
    fields = ['identificacion', 'nombre', 'apellido1', 'apellido2', 'email', 'telefono', 'puesto', 'fecha_nacimiento', 'departamento', 'titulo', 'horario', 'estado']
    success_url = reverse_lazy('personal_list')

class PersonalDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):
    model = Personal
    template_name = 'users/personal_confirm_delete.html'
    success_url = reverse_lazy('personal_list')

class EstudianteListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = Estudiante
    template_name = 'users/estudiante_list.html'
    context_object_name = 'estudiantes'

class EstudianteCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = Estudiante
    template_name = 'users/estudiante_form.html'
    fields = ['identificacion', 'nombre', 'apellido1', 'apellido2', 'fecha_nacimiento', 'nivel', 'grupo', 'subgrupo', 'horario', 'estado']
    success_url = reverse_lazy('estudiante_list')

    def form_valid(self, form):
        identificacion = form.cleaned_data['identificacion']
        if User.objects.filter(username=identificacion).exists():
            from django.contrib import messages
            messages.error(self.request, f"La identificación {identificacion} ya existe.")
            return self.form_invalid(form)
        password = 'E' + identificacion + '*'
        user = User.objects.create_user(username=identificacion, password=password)
        role = Role.objects.get(name='estudiante')
        from .models import Profile
        Profile.objects.filter(user=user).delete()
        Profile.objects.create(user=user, role=role)
        form.instance.user = user
        return super().form_valid(form)

class EstudianteUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Estudiante
    template_name = 'users/estudiante_form.html'
    fields = ['identificacion', 'nombre', 'apellido1', 'apellido2', 'fecha_nacimiento', 'nivel', 'grupo', 'subgrupo', 'horario', 'estado']
    success_url = reverse_lazy('estudiante_list')

class EstudianteDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):
    model = Estudiante
    template_name = 'users/estudiante_confirm_delete.html'
    success_url = reverse_lazy('estudiante_list')

class PersonalCarnetView(LoginRequiredMixin, AdminOnlyMixin, TemplateView):
    template_name = 'users/personal_carnet.html'

    @staticmethod
    def _format_identificacion(identificacion: str) -> str:
        digits = ''.join(ch for ch in identificacion if ch.isdigit())
        if len(digits) == 9:
            return f"{digits[0]}-{digits[1:5]}-{digits[5:]}"
        return identificacion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        personal = get_object_or_404(Personal, pk=self.kwargs['pk'])
        context['personal'] = personal
        context['full_name'] = f"{personal.nombre} {personal.apellido1} {personal.apellido2 or ''}".strip()
        context['formatted_identificacion'] = self._format_identificacion(personal.identificacion)
        context['photo_filename'] = f"img_personal/{personal.identificacion}.jpg"
        context['qr_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote_plus(personal.identificacion)}"
        return context


class EstudianteCarnetView(LoginRequiredMixin, AdminOnlyMixin, TemplateView):
    template_name = 'users/estudiante_carnet.html'

    @staticmethod
    def _format_identificacion(identificacion: str) -> str:
        digits = ''.join(ch for ch in identificacion if ch.isdigit())
        if len(digits) == 9:
            return f"{digits[0]}-{digits[1:5]}-{digits[5:]}"
        return identificacion

    @staticmethod
    def _ciclo_por_nivel(nivel: int) -> str:
        if 7 <= nivel <= 9:
            return 'Tercer Ciclo'
        if 10 <= nivel <= 12:
            return 'Educación diversificada'
        return ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estudiante = get_object_or_404(Estudiante, pk=self.kwargs['pk'])

        full_name = f"{estudiante.nombre} {estudiante.apellido1} {estudiante.apellido2 or ''}".strip()
        ciclo = self._ciclo_por_nivel(estudiante.nivel)
        nivel_grupo = f"{estudiante.nivel}-{estudiante.grupo} ({estudiante.subgrupo}) - {ciclo}" if ciclo else f"{estudiante.nivel}-{estudiante.grupo} ({estudiante.subgrupo})"

        context['estudiante'] = estudiante
        context['full_name'] = full_name
        context['formatted_identificacion'] = self._format_identificacion(estudiante.identificacion)
        context['nivel_grupo_ciclo'] = nivel_grupo
        context['photo_filename'] = f"img_estudiantes/{estudiante.identificacion}.jpg"
        context['qr_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote_plus(estudiante.identificacion)}"
        return context

def buscar_tse(request):
    """Vista para buscar datos en el TSE de Costa Rica"""
    if request.method == 'POST':
        identificacion = request.POST.get('identificacion', '')
        
        if not identificacion:
            return JsonResponse({'error': 'Identificación requerida'}, status=400)
        
        try:
            # URL de la página de búsqueda del TSE
            url_busqueda = 'https://servicioselectorales.tse.go.cr/chc/consulta_cedula.aspx'
            
            # Crear sesión para mantener cookies
            session = requests.Session()
            
            # Obtener la página inicial para conseguir los tokens necesarios
            response_inicial = session.get(url_busqueda)
            soup_inicial = BeautifulSoup(response_inicial.text, 'html.parser')
            
            # Buscar los tokens de ViewState y EventValidation
            viewstate = soup_inicial.find('input', {'name': '__VIEWSTATE'})
            eventvalidation = soup_inicial.find('input', {'name': '__EVENTVALIDATION'})
            viewstategenerator = soup_inicial.find('input', {'name': '__VIEWSTATEGENERATOR'})
            
            if not viewstate or not eventvalidation:
                return JsonResponse({'error': 'No se pudo obtener los datos de la página del TSE'}, status=400)
            
            # Preparar los datos para el POST
            data = {
                '__VIEWSTATE': viewstate.get('value', ''),
                '__EVENTVALIDATION': eventvalidation.get('value', ''),
                '__VIEWSTATEGENERATOR': viewstategenerator.get('value', '') if viewstategenerator else '',
                'txtcedula': identificacion,
                'btnConsultaCedula': 'Consultar',
            }
            
            # Hacer la búsqueda
            response_busqueda = session.post(url_busqueda, data=data)
            soup_resultado = BeautifulSoup(response_busqueda.text, 'html.parser')
            
            # Buscar los labels con los datos
            nombre_label = soup_resultado.find('span', {'id': 'lblnombrecompleto'})
            fecha_label = soup_resultado.find('span', {'id': 'lblfechaNacimiento'})
            
            if not nombre_label or not fecha_label:
                return JsonResponse({'error': 'No se encontraron datos para esa identificación'}, status=404)
            
            nombre_completo = nombre_label.text.strip() if nombre_label else ''
            fecha_nacimiento = fecha_label.text.strip() if fecha_label else ''
            
            # Procesar el nombre completo (dividir en apellido1, apellido2, nombre)
            partes = nombre_completo.split()
            apellido1 = partes[-2] if len(partes) >= 2 else ''
            apellido2 = partes[-1] if len(partes) >= 1 else ''
            nombre = ' '.join(partes[:-2]) if len(partes) > 2 else ''
            
            # Procesar la fecha (convertir formato si es necesario)
            # Esperamos formato DD/MM/YYYY
            try:
                # Si viene en formato DD/MM/YYYY, convertir a YYYY-MM-DD
                if '/' in fecha_nacimiento:
                    partes_fecha = fecha_nacimiento.split('/')
                    if len(partes_fecha) == 3:
                        fecha_cocina = f"{partes_fecha[2]}-{partes_fecha[1]}-{partes_fecha[0]}"
                    else:
                        fecha_cocina = fecha_nacimiento
                else:
                    fecha_cocina = fecha_nacimiento
            except:
                fecha_cocina = fecha_nacimiento
            
            return JsonResponse({
                'success': True,
                'nombre': nombre,
                'apellido1': apellido1,
                'apellido2': apellido2,
                'fecha_nacimiento': fecha_cocina,
            })
        
        except Exception as e:
            return JsonResponse({'error': f'Error al buscar en TSE: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
