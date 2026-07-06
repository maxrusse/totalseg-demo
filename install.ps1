param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $Root "runtime\venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"

New-Item -ItemType Directory -Force -Path (Join-Path $Root "runtime") | Out-Null

if (-not (Test-Path $Python)) {
    & $PythonExe -m venv $VenvDir
}

& $Python -m pip install --upgrade pip setuptools wheel

& $Python -m pip install -r (Join-Path $Root "requirements.txt")

Write-Host ""
Write-Host "Installation fertig."
Write-Host "Start: powershell -ExecutionPolicy Bypass -File `"$Root\start.ps1`""
