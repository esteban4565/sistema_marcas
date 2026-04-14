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
    DEPARTAMENTO_CHOICES = [
        ('AGENTE DE SEGURIDAD', 'AGENTE DE SEGURIDAD'),
        ('AUX. ADMINITRATIVO', 'AUX. ADMINITRATIVO'),
        ('COORDINACIONES', 'COORDINACIONES'),
        ('DEP. AUXILIARES', 'DEP. AUXILIARES'),
        ('DEP. CIENCIAS', 'DEP. CIENCIAS'),
        ('DEP. COMEDOR', 'DEP. COMEDOR'),
        ('DEP. EDUCACIÓN FÍSICA', 'DEP. EDUCACIÓN FÍSICA'),
        ('DEP. EMPREND. E INNOVACIÓN', 'DEP. EMPREND. E INNOVACIÓN'),
        ('DEP. ESPAÑOL', 'DEP. ESPAÑOL'),
        ('DEP. EST. SOCIALES', 'DEP. EST. SOCIALES'),
        ('DEP. ÉTICA Y PSICOLOGÍA', 'DEP. ÉTICA Y PSICOLOGÍA'),
        ('DEP. FÍSICA, QUÍMICA Y BIOLOGÍA', 'DEP. FÍSICA, QUÍMICA Y BIOLOGÍA'),
        ('DEP. FRANCÉS ACADÉMICO', 'DEP. FRANCÉS ACADÉMICO'),
        ('DEP. INGLÉS ACADÉMICO', 'DEP. INGLÉS ACADÉMICO'),
        ('DEP. INGLÉS ESPECIALIZADO', 'DEP. INGLÉS ESPECIALIZADO'),
        ('DEP. LIMPIEZA Y ASEO', 'DEP. LIMPIEZA Y ASEO'),
        ('DEP. MATEMÁTICAS', 'DEP. MATEMÁTICAS'),
        ('DEP. MÚSICA', 'DEP. MÚSICA'),
        ('DEP. ORIENTACIÓN', 'DEP. ORIENTACIÓN'),
        ('DEP. RECEPCIÓN', 'DEP. RECEPCIÓN'),
        ('DEP. RELIGIÓN', 'DEP. RELIGIÓN'),
        ('DEP. SEGURIDAD', 'DEP. SEGURIDAD'),
        ('DIRECCIÓN', 'DIRECCIÓN'),
        ('ESP. ADUANAS', 'ESP. ADUANAS'),
        ('ESP. BANCA Y FINANZAS', 'ESP. BANCA Y FINANZAS'),
        ('ESP. CONTABILIDAD', 'ESP. CONTABILIDAD'),
        ('ESP. INFORMÁTICA', 'ESP. INFORMÁTICA'),
        ('ESP. DIBUJO TÉCNICO', 'ESP. DIBUJO TÉCNICO'),
        ('ESP. EJECUTIVO CENTROS DE SERV.', 'ESP. EJECUTIVO CENTROS DE SERV.'),
        ('ESP. ELECTRÓNICA', 'ESP. ELECTRÓNICA'),
        ('ESP. SECRETARIADO EJECUTIVO', 'ESP. SECRETARIADO EJECUTIVO'),
        ('ESP. TURISMO', 'ESP. TURISMO'),
        ('JTA. ADMINISTRATIVA', 'JTA. ADMINISTRATIVA'),
        ('P.N. FORMACIÓN TECNOLÓGICA', 'P.N. FORMACIÓN TECNOLÓGICA'),
        ('REUBICADA', 'REUBICADA'),
        ('TALLERES EXPLORATORIOS', 'TALLERES EXPLORATORIOS'),
    ]
    departamento = models.CharField(max_length=100, choices=DEPARTAMENTO_CHOICES, blank=True)
    TITULO_CHOICES = [
        ('I', 'I'),
        ('II', 'II'),
    ]
    titulo = models.CharField(max_length=10, choices=TITULO_CHOICES, blank=True)
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
        if not Profile.objects.filter(user=instance).exists():
            default_role = Role.objects.get(name='estudiante')
            Profile.objects.create(user=instance, role=default_role)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
