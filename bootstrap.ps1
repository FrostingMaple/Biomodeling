[CmdletBinding()]
param(
    [string]$PythonVersion = "3.12",
    [switch]$Recreate,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$UvCacheDir = Join-Path $ProjectRoot ".uv-cache"
$IsPy314OrNewer = ([version]$PythonVersion -ge [version]"3.14")
$CompatiblePackages = if ($IsPy314OrNewer) {
    @(
        "numpy>=2.5.4",
        "scipy>=1.18.1",
        "matplotlib>=3.11",
        "sympy>=1.14.0",
        "openai>=3.8.0",
        "pymupdf>=1.24"
    )
}
else {
    @(
        "numpy==2.2.6",
        "scipy==1.15.2",
        "matplotlib==3.9.4",
        "sympy>=1.14.0",
        "openai>=3.8.0",
        "pymupdf>=1.24"
    )
}

function Remove-ProjectVenv {
    $resolvedRoot = [IO.Path]::GetFullPath($ProjectRoot).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $resolvedTarget = [IO.Path]::GetFullPath($VenvDir)
    if (-not $resolvedTarget.StartsWith($resolvedRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the project root: $resolvedTarget"
    }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}

function Get-VenvPythonVersion {
    return (& $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
}

function Test-VenvDependencies {
    & $VenvPython -c "import importlib.util as u, sys; mods=['numpy','scipy','matplotlib','sympy','openai','pymupdf']; missing=[m for m in mods if u.find_spec(m) is None]; sys.exit(1 if missing else 0)" *> $null
    return ($LASTEXITCODE -eq 0)
}

if ($Recreate -and $CheckOnly) {
    throw "-Recreate cannot be combined with -CheckOnly."
}

if ($Recreate -and (Test-Path -LiteralPath $VenvDir)) {
    Write-Host "Removing existing .venv (requested by -Recreate)..."
    Remove-ProjectVenv
}

if (Test-Path -LiteralPath $VenvPython) {
    $existingVersion = Get-VenvPythonVersion
    if ($existingVersion -ne $PythonVersion) {
        throw "Existing .venv uses Python $existingVersion, but this project expects Python $PythonVersion. Run .\bootstrap.ps1 -Recreate to rebuild it."
    }
    Write-Host "Using existing .venv with Python $existingVersion."
}
else {
    if (Test-Path -LiteralPath $VenvDir) {
        throw ".venv exists but $VenvPython was not found. Run .\bootstrap.ps1 -Recreate to rebuild the environment."
    }

    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($uv) {
        New-Item -ItemType Directory -Force -Path $UvCacheDir | Out-Null
        $env:UV_CACHE_DIR = $UvCacheDir

        Write-Host "Creating .venv with uv and Python $PythonVersion..."
        & uv python install $PythonVersion
        if ($LASTEXITCODE -ne 0) {
            throw "uv failed to prepare Python $PythonVersion."
        }

        & uv venv --python $PythonVersion $VenvDir
        if ($LASTEXITCODE -ne 0) {
            throw "uv failed to create .venv."
        }
    }
    else {
        $py = Get-Command py -ErrorAction SilentlyContinue
        if (-not $py) {
            throw "uv was not found and the Windows py launcher is unavailable. Install uv or Python $PythonVersion, then run this script again."
        }

        Write-Host "Creating .venv with py -$PythonVersion..."
        & py "-$PythonVersion" -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            throw "Python $PythonVersion is not available. Install it or install uv, then run this script again."
        }
    }
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    if ($CheckOnly) {
        throw "Environment is not ready at $VenvPython. Run .\bootstrap.ps1 to create it."
    }
    throw "Python executable was not found at $VenvPython."
}

if ($CheckOnly) {
    if (-not (Test-VenvDependencies)) {
        throw "Environment exists at $VenvPython, but one or more required dependencies are missing. Run .\bootstrap.ps1 to install them."
    }
    Write-Host "Environment is ready: $VenvPython"
    exit 0
}

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    New-Item -ItemType Directory -Force -Path $UvCacheDir | Out-Null
    $env:UV_CACHE_DIR = $UvCacheDir

    Write-Host "Installing all project dependencies..."
    & uv pip install --python $VenvPython @CompatiblePackages
}
else {
    Write-Host "Installing all project dependencies with pip..."
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip."
    }

    & $VenvPython -m pip install @CompatiblePackages
}

if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

if (-not (Test-VenvDependencies)) {
    throw "Dependency installation finished, but one or more required modules are still missing."
}

Write-Host "Environment is ready: $VenvPython"
