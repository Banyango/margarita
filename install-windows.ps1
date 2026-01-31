# install-windows.ps1
# Usage: .\install-windows.ps1 [-Repository "owner/repo"]
param(
  [string]$Repository = $env:GITHUB_REPOSITORY
)

function Get-Repo {
  param($repo)
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
  Write-Error "Could not determine GitHub repository. Pass -Repository or set GITHUB_REPOSITORY (owner/repo)."
  exit 1
}
Write-Host "Using repository: $repo"

$temp = New-TemporaryFile
Invoke-WebRequest -UseBasicParsing -Uri "https://api.github.com/repos/$repo/releases/latest" -OutFile $temp

$json = Get-Content $temp -Raw | ConvertFrom-Json
$asset = $json.assets | Where-Object { $_.name -like 'margarita-windows-*' } | Select-Object -First 1
if (-not $asset) {
  Write-Error "No Windows asset found in latest release for pattern 'margarita-windows-*'."
  exit 1
}

$downloadUrl = $asset.browser_download_url
$assetName = $asset.name

Write-Host "Found asset: $assetName"

$outPath = Join-Path $PWD $assetName
Write-Host "Downloading $downloadUrl to $outPath..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $outPath

# Decide install directory: prefer Program Files\Margarita, then $env:LOCALAPPDATA\Programs\Margarita, else user's bin
$installDir = "$env:ProgramFiles\Margarita"
if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Force -Path $installDir | Out-Null }

$dest = Join-Path $installDir $assetName
Move-Item -Path $outPath -Destination $dest -Force

# Optionally add installDir to PATH for current user
$profilePath = [Environment]::GetFolderPath('UserProfile')
$envPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($envPath -notlike "*$installDir*") {
  Write-Host "Adding $installDir to user PATH"
  $newPath = "$envPath;$installDir"
  [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
}

# Create a stable 'margarita' launcher script in installDir
$launcher = Join-Path $installDir 'margarita.cmd'
$exePath = Join-Path $installDir $assetName
Set-Content -Path $launcher -Value "@echo off`n\"%~dp0\\$assetName\" %*" -Force -Encoding ASCII

Write-Host "Installed $assetName -> $dest"
Write-Host "Created launcher: $launcher"
Write-Host "Done. You may need to open a new terminal for PATH changes to take effect."

