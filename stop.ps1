param(
    [int]$Port = 7865
)

$ErrorActionPreference = "Stop"
$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

if (-not $listeners) {
    Write-Host "Kein Server auf Port $Port gefunden."
    exit 0
}

$processIds = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($processId in $processIds) {
    Write-Host "Stoppe Prozess $processId auf Port $Port"
    Stop-Process -Id $processId -Force
}

