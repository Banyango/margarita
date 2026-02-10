# install-windows.ps1
# Simple installer for Margarita on Windows.
# Edit $VERSION at the top of this file before running to control which release is installed.
# Usage:
#   .\install-windows.ps1 -Repository "owner/repo" [-Asset "asset-name-or-url"]
# Examples:
#   .\install-windows.ps1 -Repository "Banyango/margarita"
#   .\install-windows.ps1 -Repository "Banyango/margarita" -Asset "margarita-windows-0.3.3.exe"
#   .\install-windows.ps1 -Repository "Banyango/margarita" -Asset "https://github.com/owner/repo/releases/download/v0.3.3/margarita-windows-0.3.3.exe"

# Manual version variable - update before running if you want a different release
$VERSION = '0.3.5'

param(
  [string]$Repository = Banyango/margarita,
  [string]$Asset = margarita-windows-$VERSION.exe
)

function Get-Repo($repo) {
  if ($repo) { return $repo }
  try {
    $url = git config --get remote.origin.url 2>$null
  } catch {
    $url = $null
  }
  if (-not $url) { return $null }
  if ($url -match 'git@github.com:(.+)/(.+)\.git') { return "$($Matches[1])/$($Matches[2])" }
  if ($url -match 'https://github.com/(.+)/(.+)\.git') { return "$($Matches[1])/$($Matches[2])" }
  return $null
}

$repo = Get-Repo -repo $Repository
if (-not $repo) {
  Write-Host "Usage: .\install-windows.ps1 -Repository 'owner/repo' [-Asset 'asset-or-url']"
  Write-Host "Please provide the GitHub repository (owner/repo) or set GITHUB_REPOSITORY env var."
  exit 1
}

if (-not $VERSION) {
  Write-Error "Please set `$VERSION at the top of this script before running."
  exit 1
}

# Determine download URL
if ($Asset -and ($Asset -like 'http*')) {
  $downloadUrl = $Asset
  $assetName = [System.IO.Path]::GetFileName($downloadUrl)
} else {
  if (-not $Asset) { $assetName = "margarita-windows-$VERSION.exe" } else { $assetName = $Asset }
  $downloadUrl = "https://github.com/$repo/releases/download/v$VERSION/$assetName"
}

Write-Host "Downloading: $downloadUrl"

$temp = [System.IO.Path]::GetTempFileName()
try {
  Invoke-WebRequest -Uri $downloadUrl -OutFile $temp -UseBasicParsing -ErrorAction Stop
} catch {
  Write-Error "Failed to download $downloadUrl`n$($_.Exception.Message)"
  Write-Host "If the asset name differs, pass it with -Asset or set `$VERSION in this script."
  exit 1
}

# Prefer Program Files\Margarita if writable, else use LocalAppData\Programs\Margarita, else fall back to %USERPROFILE%\bin
$installDir = Join-Path $env:ProgramFiles 'Margarita'
if (-not (Test-Path $installDir)) {
  try { New-Item -ItemType Directory -Path $installDir -Force | Out-Null } catch { $installDir = $null }
}

if (-not $installDir) {
  $installDir = Join-Path $env:LOCALAPPDATA 'Programs\Margarita'
  if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
}

if (-not $installDir) {
  $installDir = Join-Path $env:USERPROFILE 'bin'
  if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
}

$targetPath = Join-Path $installDir 'margarita.exe'

try {
  Move-Item -Path $temp -Destination $targetPath -Force
} catch {
  Write-Host "Attempting elevated move to $installDir..."
  $ps = Start-Process -FilePath powershell -ArgumentList "-NoProfile -Command Move-Item -Path '$temp' -Destination '$targetPath' -Force" -Verb RunAs -Wait -PassThru
  if ($ps.ExitCode -ne 0) { Write-Error "Failed to move file to $installDir"; exit 1 }
}

Write-Host "Installed margarita -> $targetPath"

# Add installDir to user PATH if missing
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$installDir*") {
  Write-Host "Adding $installDir to user PATH"
  $newPath = if ($userPath) { "$userPath;$installDir" } else { $installDir }
  [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
  Write-Host "Note: You may need to open a new terminal for PATH changes to take effect."
}

Write-Host "Done. Run 'margarita.exe --help' to verify."
