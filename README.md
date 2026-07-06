# Codex Windows Demo

This is a self-contained Windows web app that Codex can open, run, and inspect in one shot.

It generates a synthetic 3D demo scene locally, so there is:

- no DICOM input
- no model weights
- no external segmentation runtime

The app uses FastAPI + a small browser UI and writes demo jobs into `data\jobs`.

## Run with Codex

Open this GitHub repo in Codex and ask it to run the Windows demo. The one-liner it should use is:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1; powershell -ExecutionPolicy Bypass -File .\start.ps1
```

## Run manually

```powershell
cd C:\Users\Max\code\work\Totalseg
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
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

The public example is intentionally small and reproducible so it is easy to hand to Codex or a teammate.
