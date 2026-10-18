[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$MainArgs,
    [string]$PythonVersion = "3.12",
    [switch]$Recreate,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$BootstrapScript = Join-Path $ProjectRoot "bootstrap.ps1"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$MainScript = Join-Path $ProjectRoot "main.py"

$needsBootstrap = $true
if (-not $Recreate -and (Test-Path -LiteralPath $VenvPython)) {
    $version = (& $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
    if ($version -eq $PythonVersion) {
        & $VenvPython -c "import importlib.util as u, sys; mods=['numpy','scipy','matplotlib','sympy','openai','pymupdf']; missing=[m for m in mods if u.find_spec(m) is None]; sys.exit(1 if missing else 0)" *> $null
        $needsBootstrap = ($LASTEXITCODE -ne 0)
    }
}

if ($CheckOnly) {
    & $BootstrapScript -PythonVersion $PythonVersion -CheckOnly
    exit $LASTEXITCODE
}

if ($needsBootstrap) {
    if ($Recreate) {
        & $BootstrapScript -PythonVersion $PythonVersion -Recreate
    }
    else {
        & $BootstrapScript -PythonVersion $PythonVersion
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Python environment is not ready. Run .\bootstrap.ps1 first."
}

& $VenvPython $MainScript @MainArgs
exit $LASTEXITCODE
