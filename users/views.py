from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Role, Personal, Estudiante

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
    fields = ['identificacion', 'nombre', 'apellido', 'email', 'telefono', 'puesto', 'fecha_nacimiento', 'departamento', 'titulo', 'horario', 'estado']
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
        Profile.objects.create(user=user, role=role)
        form.instance.user = user
        return super().form_valid(form)

class PersonalUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Personal
    template_name = 'users/personal_form.html'
    fields = ['identificacion', 'nombre', 'apellido', 'email', 'telefono', 'puesto', 'fecha_nacimiento', 'departamento', 'titulo', 'horario', 'estado']
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
    fields = ['user', 'nombre', 'apellido1', 'apellido2', 'fecha_nacimiento', 'nivel', 'grupo', 'subgrupo', 'horario', 'estado']
    success_url = reverse_lazy('estudiante_list')

class EstudianteUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Estudiante
    template_name = 'users/estudiante_form.html'
    fields = ['user', 'nombre', 'apellido1', 'apellido2', 'fecha_nacimiento', 'nivel', 'grupo', 'subgrupo', 'horario', 'estado']
    success_url = reverse_lazy('estudiante_list')

class EstudianteDeleteView(LoginRequiredMixin, AdminOnlyMixin, DeleteView):
    model = Estudiante
    template_name = 'users/estudiante_confirm_delete.html'
    success_url = reverse_lazy('estudiante_list')
