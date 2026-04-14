from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Role(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class Personal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal')
    identificacion = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    PUESTO_CHOICES = [
        ('Docente', 'Docente'),
        ('Administrativo', 'Administrativo'),
    ]
    puesto = models.CharField(max_length=100, choices=PUESTO_CHOICES)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True)
    titulo = models.CharField(max_length=10, blank=True)
    HORARIO_CHOICES = [
        ('Diurno', 'Diurno'),
        ('Nocturno', 'Nocturno'),
        ('Diurno_Nocturno', 'Diurno_Nocturno'),
    ]
    horario = models.CharField(max_length=20, choices=HORARIO_CHOICES, blank=True)
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('desactivo', 'Desactivo'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.puesto}"

class Estudiante(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='estudiante')
    nombre = models.CharField(max_length=100)
    apellido1 = models.CharField(max_length=100)
    apellido2 = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    nivel = models.IntegerField()
    grupo = models.IntegerField()
    subgrupo = models.CharField(max_length=10)
    HORARIO_CHOICES = [
        ('Diurno', 'Diurno'),
        ('Nocturno', 'Nocturno'),
        ('Diurno_Nocturno', 'Diurno_Nocturno'),
    ]
    horario = models.CharField(max_length=20, choices=HORARIO_CHOICES)
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('desactivo', 'Desactivo'),
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activo')

    def __str__(self):
        return f"{self.nombre} {self.apellido1} - Nivel {self.nivel} Grupo {self.grupo}{self.subgrupo}"

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        default_role = Role.objects.get(name='estudiante')
        Profile.objects.create(user=instance, role=default_role)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
