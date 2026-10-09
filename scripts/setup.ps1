$ErrorActionPreference = "Stop"

$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python 3.11 or 3.12 is required. Install it and reopen PowerShell."
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $python.Source -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
& ".\.venv\Scripts\python.exe" -m pytest -q
Write-Host "Backend environment is ready. Run .\scripts\sync-upstream-data.ps1 to fetch the data."