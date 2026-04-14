from django.db import models
from django.contrib.auth.models import User

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    type = models.CharField(max_length=10, choices=[('in', 'Entrada'), ('out', 'Salida')])

    def __str__(self):
        return f"{self.user.username} - {self.date} {self.time} {self.get_type_display()}"
