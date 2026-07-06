# Codex Windows Demo

GitHub: https://github.com/maxrusse/totalseg-demo

This is a self-contained Windows web app that runs locally on Windows.

It generates a synthetic 3D demo scene locally, so there is:

- no DICOM input
- no model weights
- no external segmentation runtime

The app uses FastAPI + a small browser UI and writes demo jobs into `data\jobs`.

## Prompt History

### TotalSeg build prompt

> Build a local Windows web frontend for TotalSegmentator with install/start/stop scripts, a browser UI, job tracking, a viewer, and volume export. Keep it fully local and self-contained.

### GitHub upload prompt

> Upload that as a full working example without DICOM or weights to GitHub as a public example for a Codex one-shot Windows application. Add small info on how to run it in the README with manual PowerShell one-liners, and ignore the backup.

## Run manually

```powershell
cd C:\Users\Max\code\work\Totalseg
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

One-liner:

```powershell
powershell -ExecutionPolicy Bypass -Command "Set-Location C:\Users\Max\code\work\Totalseg; .\install.ps1; .\start.ps1"
```

The app opens at:

`http://127.0.0.1:7865`

## Stop

```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

## Smoke test

```powershell
powershell -ExecutionPolicy Bypass -File .\smoke_test.ps1
```

## What you get

- a generated demo volume
- a few local masks
- slice and mask viewers
- job history and volume reports

The public example is intentionally small and reproducible so it is easy to hand to a teammate.
