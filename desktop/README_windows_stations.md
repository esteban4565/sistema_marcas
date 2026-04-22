# Estaciones Windows para Marcacion

Este documento describe como ejecutar las estaciones de marcacion como aplicacion de Windows, mientras la parte administrativa sigue en Django Web.

## Arquitectura

- Django Web se mantiene para administracion: usuarios, roles, personal, estudiantes, reportes.
- La marcacion de estaciones se hace por una app de escritorio: desktop/station_app.py.
- La app se comunica con Django por API protegida con clave por estacion.

## Endpoints API

- POST /attendance/station-api/personal/mark/
- GET /attendance/station-api/personal/recent/
- POST /attendance/station-api/estudiante/mark/
- GET /attendance/station-api/estudiante/recent/

Se requiere encabezado HTTP: X-Station-Key

## Configurar claves en Django

Defina variables de entorno antes de iniciar el servidor:

PowerShell:

$env:STATION_KEY_PERSONAL="cambie-esta-clave-personal"
$env:STATION_KEY_ESTUDIANTE="cambie-esta-clave-estudiante"

Luego ejecute el servidor:

python manage.py runserver 0.0.0.0:8000

## Ejecutar app en cada estacion

Instale dependencias (requests ya esta en requirements.txt):

pip install -r requirements.txt

Estacion Direccion (personal):

python desktop/station_app.py --server http://IP_DEL_SERVIDOR:8000 --station personal --key cambie-esta-clave-personal

Estacion Porton (estudiantes):

python desktop/station_app.py --server http://IP_DEL_SERVIDOR:8000 --station estudiante --key cambie-esta-clave-estudiante

## Generar dos .exe con parametros fijos

1. Edite `desktop/station_config.py` con URL y claves reales.
2. Ejecute en PowerShell:

`powershell -ExecutionPolicy Bypass -File desktop/build_stations.ps1`

Se generan:

- `dist/StationPersonal.exe`
- `dist/StationEstudiantes.exe`

Cada .exe queda configurado con parametros fijos desde `station_config.py`.

## Ejecucion directa (sin .exe)

- Personal: `python desktop/station_personal.py`
- Estudiantes: `python desktop/station_estudiantes.py`

## Recomendacion de red

- Use una IP fija para el servidor Django en la red local.
- Si usa SQLite, evite muchas escrituras concurrentes desde demasiados equipos.
- Para mayor escala, migre a PostgreSQL.
