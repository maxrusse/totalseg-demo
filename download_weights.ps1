param(
    [string]$WeightsTask = "lung_nodules"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvDir = Join-Path $Root "runtime\conda-env"
$Python = Join-Path $EnvDir "python.exe"
$TotalsegHome = Join-Path $Root "runtime\totalsegmentator_home"

if (-not (Test-Path $Python)) {
    throw "Runtime fehlt. Bitte zuerst install.ps1 ausfuehren."
}

$env:TOTALSEG_HOME_DIR = $TotalsegHome
$Downloader = Join-Path $EnvDir "Scripts\totalseg_download_weights.exe"
if (-not (Test-Path $Downloader)) {
    throw "totalseg_download_weights wurde nicht installiert."
}

& $Downloader -t total
if ($WeightsTask -ne "total") {
    & $Downloader -t $WeightsTask
}
