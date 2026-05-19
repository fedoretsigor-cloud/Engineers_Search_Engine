param(
    [string] $Remote = "origin",
    [string] $Branch = "",
    [int] $TimeoutSeconds = 900,
    [int] $PollSeconds = 10
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

if (-not $Branch) {
    $Branch = (& git branch --show-current).Trim()
}

if (-not $Branch) {
    throw "Could not determine current branch. Pass -Branch explicitly."
}

Write-Host "Pushing $Branch to $Remote..."
& git push $Remote $Branch
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$commitSha = (& git rev-parse HEAD).Trim()
& (Join-Path $PSScriptRoot "watch_ci.ps1") `
    -CommitSha $commitSha `
    -TimeoutSeconds $TimeoutSeconds `
    -PollSeconds $PollSeconds
exit $LASTEXITCODE
