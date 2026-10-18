param(
    [string]$PythonVersion = "3.12",
    [switch]$Dev
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    py "-$PythonVersion" -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }
}

& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip." }

$Target = "."
if ($Dev) { $Target = ".[dev,pdf]" } else { $Target = ".[pdf]" }
& $Python -m pip install -e $Target
if ($LASTEXITCODE -ne 0) { throw "Failed to install the unified package." }

Write-Host "Environment ready: $Python"
Write-Host "Run: .\run.ps1 --help"
