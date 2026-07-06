# Lokales TotalSegmentator-Tool

Lokale Windows-Weboberfläche für TotalSegmentator.

Dieses Repository zeigt, wie Codex einen wissenschaftlich geprägten Workflow in eine lokal lauffähige Windows-Anwendung überführen kann: aus einer klaren Idee wird ein direkt nutzbares Tool mit Installation, Vorverarbeitung, lokaler Ausführung, Browser-Oberfläche und nachvollziehbarem Ergebnis.

Repository auf GitHub: https://github.com/maxrusse/totalseg-demo

Erstellt mit Codex CLI auf GPT-5.5 (`xhigh`).

## So nutzt du Codex

Wenn Codex das hier für dich lokal nachbauen oder an deinen Rechner anpassen soll, verwende entweder deine eigene Eingabe oder verweise direkt auf das GitHub-Repository.

- Beispiel: `https://github.com/maxrusse/totalseg-demo`
- Bitte Codex, die Lösung an deinen PC anzupassen, also lokale Pfade, GPU oder CPU, und vorhandene Datenordner zu verwenden.
- Bitte Codex, alle benötigten Abhängigkeiten in einem repo-lokalen `env` oder `venv` zu installieren.
- Nutze `/goal`, wenn der Auftrag als durchgaengige Aufgabe mit klarem Ziel verfolgt werden soll.
- Ergebnisse können je nach Codex-Version, GPT-Modell, Reasoning-Einstellung, Hardware und Workspace-Zustand variieren.

Beispiel-Eingabe:

```text
Nimm dieses Repo als Ausgangspunkt: https://github.com/maxrusse/totalseg-demo
Baue oder passe die App lokal für meinen PC an, installiere alle benötigten Abhängigkeiten in einem repo-lokalen env/venv und halte dich an /goal für die gesamte Umsetzung.
```

## Enthaltene Funktionen

- DICOM-Ordner auswählen und Serien lokal scannen
- Eine CT-Serie für den Lauf gezielt auswählen
- DICOM-Daten vorverarbeiten und in ein Lauf-Format überführen
- TotalSegmentator lokal starten, ohne externe Cloud-Abhängigkeit während des Laufs
- Verfügbare Tasks und Algorithmus-Optionen im Browser wählen
- Fortschritt und Status je Job im Webfrontend verfolgen
- CT-Slices und Segmentierungen nebeneinander anzeigen
- Masken farblich darstellen und pro Struktur durchsehen
- Volumina berechnen und als `volumes.json` sowie `volumes.txt` exportieren
- Pro Lauf ein eigenes Job-Verzeichnis mit Protokoll und Ergebnissen schreiben
- Installation, Start und Schnelltest mit PowerShell-Skripten reproduzierbar machen

## Typischer Ablauf

Das Projekt läuft lokal unter Windows und braucht für den normalen Ablauf nur zwei Schritte:

1. `install.ps1`
2. `start.ps1`

Optional kann man vorab die Modellgewichte laden, damit der erste Lauf nicht warten muss:

3. `install.ps1 -DownloadWeights`

oder

3. `download_weights.ps1`

## Voraussetzungen Für Manuelle Einrichtung

Wer das Projekt nicht über die Skripte, sondern manuell aufsetzen will, braucht mindestens:

- Windows 10 oder 11
- PowerShell
- eine lokale Python-Umgebung im Repo, zum Beispiel `env` oder `venv`
- Zugriff auf die DICOM-Testdaten oder eigene CT-Daten
- ausreichend Speicherplatz für Laufdaten und Modellgewichte
- optional eine NVIDIA-GPU für schnellere Segmentierung

Manuelle Einrichtung heisst hier:

- Abhängigkeiten aus `requirements.txt` in die lokale Umgebung installieren
- TotalSegmentator und seine Laufzeitdateien lokal verfügbar machen
- die Modellgewichte lokal laden, falls nicht nur ein Schnelltest geplant ist
- `install.ps1` und `start.ps1` nur als Referenz nutzen, wenn du den Ablauf selbst nachbaust

## Hinweis Zu Den Tokenkosten

Der erste Build-Schritt in der lokalen Codex-Historie für die Session `019eee1a-ef90-7663-9e1d-dc37068fe6dd` endete vor der ersten Folgeeingabe und nutzte `7,642,415` Eingabe-Tokens, `7,200,128` zwischengespeicherte Eingabe-Tokens, `48,851` Ausgabe-Tokens und `7,691,266` Tokens insgesamt. Die Session-Metadaten zeigen `gpt-5.5` mit `xhigh`-Aufwand.

Wenn man das mit GPT-5.5 im Standard-Kurzkontext berechnet, liegen die API-äquivalenten Kosten bei etwa `$7.28`:

- nicht zwischengespeicherte Eingabe-Tokens: `442,287`
- zwischengespeicherte Eingabe-Tokens: `7,200,128`
- Ausgabe-Tokens: `48,851`

Zwischengespeicherte Tokens sind Treffer im Eingabe-Präfix-Cache innerhalb der OpenAI-API-Infrastruktur, nicht Erinnerung aus einer früheren Codex-Instanz oder einem anderen Account. OpenAI sagt, dass diese Caches automatisch sind, nicht zwischen Organisationen geteilt werden und als `cached_tokens` im Nutzungsobjekt erscheinen. Siehe [Eingabecaching](https://developers.openai.com/api/docs/guides/prompt-caching) und [Preisübersicht](https://developers.openai.com/api/docs/pricing).

## Installation

PowerShell als normaler Benutzer öffnen:

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

Optional können die Modellgewichte vorab geladen werden:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -DownloadWeights -WeightsTask lung_nodules
```

Das gleiche lässt sich auch mit `download_weights.ps1` machen. TotalSegmentator speichert die Gewichte lokal unter `runtime\totalsegmentator_home`.

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
3. Eine CT-Serie mit der Schaltfläche `Use` auswählen.
4. Task wählen, z.B. `lung_nodules` oder `total`.
5. `Start` klicken.

CPU-Läufe können lange dauern. `Fast` ist standardmäßig aktiv.

## Schnelltest Ohne Segmentierung

```powershell
powershell -ExecutionPolicy Bypass -File .\smoke_test.ps1
```

Der Test sucht die erste CT-Serie in LIDC-IDRI und prüft die DICOM-zu-NIfTI-Vorverarbeitung.

## Ergebnisse

Jeder Lauf bekommt einen Ordner unter `data\jobs\<job-id>`:

- `input.nii.gz`: vorverarbeitetes CT
- `segmentations\`: TotalSegmentator-Masken
- `volumes.json`: berechnete Volumina
- `volumes.txt`: Text-Export
- `log.txt`: Laufprotokoll

Der Viewer zeigt links CT-Slices und rechts die ausgewählte Maske. Volumina lassen sich über `Volumina` als Textdatei exportieren.

## Hinweise

TotalSegmentator ist kein Medizinprodukt für klinische Nutzung. Die App ist ein lokales Forschungs-/Testwerkzeug.

Offizielle TotalSegmentator-Dokumentation: https://github.com/wasserth/TotalSegmentator
