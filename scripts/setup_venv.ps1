$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    py -3.13 -m venv .venv
} else {
    python -m venv .venv
}

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    throw 'Could not create .venv. Install Python 3.13 and ensure the Python launcher is available.'
}

.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "`nEnvironment created. Activate it with: .\.venv\Scripts\Activate.ps1"
Write-Host 'Then copy .env.example to .env and configure DATABASE_URL for your local MySQL instance.'
