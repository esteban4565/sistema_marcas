$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv-2\Scripts\python.exe'

if (-not (Test-Path $pythonExe)) {
    throw "No se encontro Python en $pythonExe"
}

Set-Location $projectRoot

& $pythonExe -m pip install pyinstaller

# Limpiar compilaciones anteriores
Remove-Item -Recurse -Force "$projectRoot\build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$projectRoot\dist" -ErrorAction SilentlyContinue
Remove-Item -Force "$projectRoot\StationPersonal.spec" -ErrorAction SilentlyContinue
Remove-Item -Force "$projectRoot\StationEstudiantes.spec" -ErrorAction SilentlyContinue

# Compilar ejecutable de estacion personal
& $pythonExe -m PyInstaller --noconfirm --onefile --windowed --name StationPersonal desktop\station_personal.py

# Compilar ejecutable de estacion estudiantes
& $pythonExe -m PyInstaller --noconfirm --onefile --windowed --name StationEstudiantes desktop\station_estudiantes.py

Write-Host "Compilacion finalizada"
Write-Host "Ejecutables generados en: $projectRoot\dist"
