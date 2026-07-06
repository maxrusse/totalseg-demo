param(
    [string]$CondaExe = "C:\Users\Max\miniconda3\Scripts\conda.exe",
    [switch]$SkipTorch,
    [ValidateSet("auto", "cpu", "cu118", "cu126", "cu128")]
    [string]$TorchBuild = "auto",
    [switch]$DownloadWeights,
    [string]$WeightsTask = "lung_nodules"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvDir = Join-Path $Root "runtime\conda-env"
$Python = Join-Path $EnvDir "python.exe"
$TotalsegHome = Join-Path $Root "runtime\totalsegmentator_home"

New-Item -ItemType Directory -Force -Path (Join-Path $Root "runtime") | Out-Null
New-Item -ItemType Directory -Force -Path $TotalsegHome | Out-Null

if (-not (Test-Path $CondaExe)) {
    throw "Conda wurde nicht gefunden: $CondaExe"
}

if (-not (Test-Path $Python)) {
    & $CondaExe create -y -p $EnvDir python=3.11 pip
}

& $Python -m pip install --upgrade pip setuptools wheel

if (-not $SkipTorch) {
    if ($TorchBuild -eq "auto") {
        $NvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
        if ($NvidiaSmi) {
            $TorchBuild = "cu128"
        }
        else {
            $TorchBuild = "cpu"
        }
    }
    $TorchIndex = "https://download.pytorch.org/whl/$TorchBuild"
    Write-Host "Installing PyTorch build: $TorchBuild"
    & $Python -m pip install --force-reinstall torch torchvision --index-url $TorchIndex
}

& $Python -m pip install -r (Join-Path $Root "requirements.txt")

$env:TOTALSEG_HOME_DIR = $TotalsegHome
if ($DownloadWeights) {
    $Downloader = Join-Path $EnvDir "Scripts\totalseg_download_weights.exe"
    if (-not (Test-Path $Downloader)) {
        throw "totalseg_download_weights wurde nicht installiert."
    }
    & $Downloader -t total
    if ($WeightsTask -ne "total") {
        & $Downloader -t $WeightsTask
    }
}

Write-Host ""
Write-Host "Installation fertig."
Write-Host "Start: powershell -ExecutionPolicy Bypass -File `"$Root\start.ps1`""
