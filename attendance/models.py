from django.db import models

class Marca(models.Model):
    identificacion = models.CharField(max_length=20, help_text="Identificación de la persona (Docente, Administrativo o Estudiante)")
    fecha_hora = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora exacta de la marca")
    tipo_persona = models.CharField(
        max_length=10,
        choices=[('personal', 'Personal'), ('estudiante', 'Estudiante')],
        blank=True,
        help_text="Tipo de persona (se determina automáticamente al registrar)"
    )

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.identificacion} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M:%S')}"

    def save(self, *args, **kwargs):
        # Determinar automáticamente el tipo de persona si no está establecido
        if not self.tipo_persona:
            from users.models import Personal, Estudiante
            if Personal.objects.filter(identificacion=self.identificacion).exists():
                self.tipo_persona = 'personal'
            elif Estudiante.objects.filter(identificacion=self.identificacion).exists():
                self.tipo_persona = 'estudiante'
        super().save(*args, **kwargs)
