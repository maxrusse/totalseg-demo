$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root "runtime\venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Runtime fehlt. Bitte zuerst install.ps1 ausfuehren."
}

Push-Location $Root
try {
    & $Python scripts\smoke_check.py
}
finally {
    Pop-Location
}
