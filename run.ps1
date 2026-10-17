$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (Test-Path -LiteralPath '.venv/Scripts/python.exe') {
    & '.venv/Scripts/python.exe' -m uvicorn app:app --host 127.0.0.1 --port 8010
} elseif (Test-Path -LiteralPath '.deps/falkordb') {
    $env:PYTHONPATH = Join-Path $PSScriptRoot '.deps'
    python -m uvicorn app:app --host 127.0.0.1 --port 8010
} else {
    Write-Error 'Install requirements in .venv first; see README.md.'
}
