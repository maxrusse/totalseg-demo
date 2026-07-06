$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root "runtime\conda-env\python.exe"

if (-not (Test-Path $Python)) {
    throw "Runtime fehlt. Bitte zuerst install.ps1 ausfuehren."
}

Push-Location $Root
try {
    & $Python scripts\smoke_check.py --dicom-root "C:\Users\Max\code\work\TCIA_LIDC-IDRI\lidc_idri"
}
finally {
    Pop-Location
}
