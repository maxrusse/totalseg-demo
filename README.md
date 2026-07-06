# TotalSegmentator Local Tool

Lokales Windows-Webfrontend fuer TotalSegmentator.

GitHub: https://github.com/maxrusse/totalseg-demo

Das Projekt laeuft lokal unter Windows und braucht fuer den normalen Ablauf nur zwei Schritte:

1. `install.ps1`
2. `start.ps1`

Optional kann man vorab die Modellgewichte laden, damit der erste Lauf nicht warten muss:

3. `install.ps1 -DownloadWeights`

oder

3. `download_weights.ps1`

## Installation

PowerShell als normaler Benutzer oeffnen:

```powershell
cd C:\Users\Max\code\work\Totalseg
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Das Skript nutzt die vorhandene Miniconda-Installation unter `C:\Users\Max\miniconda3`, legt eine Python-3.11-Umgebung unter `runtime\conda-env` an und installiert:

- PyTorch CPU oder CUDA (`auto` nutzt bei NVIDIA-GPU den CUDA-12.8-Wheel)
- TotalSegmentator
- FastAPI/Uvicorn
- SimpleITK, pydicom, nibabel, numpy, Pillow

CPU-only Installation erzwingen:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -TorchBuild cpu
```

Optional koennen die Modellgewichte vorab geladen werden:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -DownloadWeights -WeightsTask lung_nodules
```

Das gleiche laesst sich auch mit `download_weights.ps1` machen. TotalSegmentator speichert die Gewichte lokal unter `runtime\totalsegmentator_home`.

## Start

```powershell
cd C:\Users\Max\code\work\Totalseg
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

Die App startet auf:

`http://127.0.0.1:7865`

Server stoppen:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

## Testdaten

Die App ist auf die vorhandenen LIDC-IDRI-Daten voreingestellt:

`C:\Users\Max\code\work\TCIA_LIDC-IDRI\lidc_idri`

Im Browser:

1. Patient- oder Serienordner auswaehlen.
2. `Scannen` klicken.
3. Eine CT-Serie mit `Use` auswaehlen.
4. Task waehlen, z.B. `lung_nodules` oder `total`.
5. `Start` klicken.

CPU-Laeufe koennen lange dauern. `Fast` ist standardmaessig aktiv.

## Smoke-Test ohne Segmentierung

```powershell
powershell -ExecutionPolicy Bypass -File .\smoke_test.ps1
```

Der Test sucht die erste CT-Serie in LIDC-IDRI und prueft die DICOM-zu-NIfTI-Vorverarbeitung.

## Ergebnisse

Jeder Lauf bekommt einen Ordner unter `data\jobs\<job-id>`:

- `input.nii.gz`: vorverarbeitetes CT
- `segmentations\`: TotalSegmentator-Masken
- `volumes.json`: berechnete Volumina
- `volumes.txt`: Text-Export
- `log.txt`: Laufprotokoll

Der Viewer zeigt links CT-Slices und rechts die ausgewaehlte Maske. Volumina lassen sich ueber `Volumina` als Textdatei exportieren.

## Hinweise

TotalSegmentator ist kein Medizinprodukt fuer klinische Nutzung. Die App ist ein lokales Forschungs-/Testwerkzeug.

Offizielle TotalSegmentator-Dokumentation: https://github.com/wasserth/TotalSegmentator
