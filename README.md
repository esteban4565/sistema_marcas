# Sistema de Marcas de Asistencia

Aplicación web en Django para marcar asistencias de docentes, administrativos y estudiantes.

## Instalación

1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar migraciones: `python manage.py migrate`
3. Crear superusuario: `python manage.py createsuperuser`
4. Ejecutar servidor: `python manage.py runserver`

## Uso

- Acceder a /admin/ para administrar usuarios y perfiles.
- Los usuarios pueden marcar asistencia en /attendance/mark/
- Ver lista en /attendance/list/

## Notas

- Base de datos: SQLite (por defecto).
- Autenticación requerida para marcar asistencia.

## Modo Hibrido: Web Admin + Estaciones Windows

- La administracion continua en interfaz web (Django): `/users/roles/`, `/users/`, `/attendance/`, etc.
- Las estaciones de marcacion pueden ejecutarse como app Windows:
	- `desktop/station_app.py`
	- Guía completa: `desktop/README_windows_stations.md`