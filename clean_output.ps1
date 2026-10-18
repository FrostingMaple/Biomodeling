[CmdletBinding()]
param(
    [switch]$Execute,
    [switch]$DryRun,
    [int]$KeepLatest = 0,
    [switch]$IncludeReports,
    [switch]$IncludeSessions,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ($Execute -and $DryRun) {
    throw "-Execute and -DryRun cannot be used together."
}
if (-not $Execute -and -not $DryRun) {
    $DryRun = $true
}
if ($KeepLatest -lt 0) {
    throw "-KeepLatest must be greater than or equal to 0."
}

$projectRoot = [IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path)).TrimEnd([IO.Path]::DirectorySeparatorChar)
$outputDir = [IO.Path]::GetFullPath((Join-Path $projectRoot "output"))
$rootPrefix = $projectRoot + [IO.Path]::DirectorySeparatorChar
$outputPrefix = $outputDir.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

if (-not (Test-Path -LiteralPath $outputDir -PathType Container)) {
    Write-Host "Output directory does not exist: $outputDir"
    exit 0
}
if (-not $outputDir.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to operate outside the project root: $outputDir"
}

$files = @(
    Get-ChildItem -LiteralPath $outputDir -File |
        Where-Object { $_.Extension -in @(".json", ".png") }
)

if ($IncludeReports) {
    $reportsDir = Join-Path $outputDir "reports"
    if (Test-Path -LiteralPath $reportsDir -PathType Container) {
        $files += Get-ChildItem -LiteralPath $reportsDir -File -Filter "*.md"
    }
}
if ($IncludeSessions) {
    $sessionsDir = Join-Path $outputDir "sessions"
    if (Test-Path -LiteralPath $sessionsDir -PathType Container) {
        $files += Get-ChildItem -LiteralPath $sessionsDir -File -Filter "*.json"
    }
}

$files = @($files | Sort-Object LastWriteTime -Descending)
$candidates = if ($KeepLatest -gt 0) {
    @($files | Select-Object -Skip $KeepLatest)
} else {
    @($files)
}

if ($candidates.Count -eq 0) {
    Write-Host "No matching runtime files found."
    exit 0
}

foreach ($file in $candidates) {
    $fullPath = [IO.Path]::GetFullPath($file.FullName)
    if (-not $fullPath.StartsWith($outputPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside output/: $fullPath"
    }
}

Write-Host "Runtime files selected: $($candidates.Count)"
Write-Host "Keep latest: $KeepLatest"
Write-Host "Mode: $(if ($DryRun) { 'DRY RUN (no files will be deleted)' } else { 'EXECUTE' })"
$candidates | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize

if ($DryRun) {
    Write-Host "Preview only. Add -Execute to delete the listed files."
    exit 0
}

if (-not $Force) {
    $answer = Read-Host "Permanently delete the listed files? Type YES to continue"
    if ($answer -ne "YES") {
        Write-Host "Cancelled."
        exit 1
    }
}

foreach ($file in $candidates) {
    Remove-Item -LiteralPath $file.FullName -Force
}

Write-Host "Deleted $($candidates.Count) runtime files."
