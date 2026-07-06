param(
    [int]$Port = 7865,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root "runtime\venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Runtime fehlt. Bitte zuerst install.ps1 ausfuehren."
}

$Url = "http://127.0.0.1:$Port"

if (-not $NoBrowser) {
    Start-Process $Url | Out-Null
}

Push-Location $Root
try {
    & $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}
