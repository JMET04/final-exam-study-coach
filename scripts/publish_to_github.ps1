param(
  [Parameter(Mandatory = $true)]
  [string]$RemoteUrl,

  [string]$Branch = "main",
  [string]$Tag = "v0.1.0"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath ".git")) {
  throw "Run this script from the repository root: github_release"
}

$currentBranch = git branch --show-current
if ($currentBranch -ne $Branch) {
  git checkout $Branch
}

$existingRemote = git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
  git remote add origin $RemoteUrl
} elseif ($existingRemote -ne $RemoteUrl) {
  git remote set-url origin $RemoteUrl
}

git push -u origin $Branch
git push origin $Tag

Write-Host "Published $Branch and $Tag to $RemoteUrl"
