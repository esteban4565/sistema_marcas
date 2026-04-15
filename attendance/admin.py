from django.contrib import admin
from .models import Marca

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['identificacion', 'fecha_hora', 'tipo_persona']
    list_filter = ['tipo_persona', 'fecha_hora']
    search_fields = ['identificacion']
    readonly_fields = ['fecha_hora']
    ordering = ['-fecha_hora']
