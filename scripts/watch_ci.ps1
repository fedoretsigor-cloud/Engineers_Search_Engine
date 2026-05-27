param(
    [string] $CommitSha = "",
    [string] $Owner = "",
    [string] $Repo = "",
    [string] $Event = "push",
    [int] $TimeoutSeconds = 900,
    [int] $PollSeconds = 10,
    [int] $RunVisibilityTimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

if (-not $CommitSha) {
    $CommitSha = (& git rev-parse HEAD).Trim()
}

if (-not $Owner -or -not $Repo) {
    $remoteUrl = (& git remote get-url origin).Trim()
    if ($remoteUrl -notmatch "github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)(?:\.git)?$") {
        throw "Could not parse GitHub owner/repo from origin remote: $remoteUrl"
    }

    if (-not $Owner) {
        $Owner = $Matches.owner
    }
    if (-not $Repo) {
        $Repo = $Matches.repo
    }
}

$apiBase = "https://api.github.com/repos/$Owner/$Repo"
$headers = @{
    "Accept" = "application/vnd.github+json"
    "User-Agent" = "engineers-search-engine-ci-watch"
}

$token = $env:GITHUB_TOKEN
if (-not $token) {
    $token = $env:GH_TOKEN
}
if ($token) {
    $headers["Authorization"] = "Bearer $token"
}

function Invoke-GitHubApi {
    param([string] $Uri)
    return Invoke-RestMethod -Uri $Uri -Headers $headers
}

function Get-FailedJobDetails {
    param([object] $Run)

    $jobsUrl = "$apiBase/actions/runs/$($Run.id)/jobs?per_page=100"
    $jobsResponse = Invoke-GitHubApi -Uri $jobsUrl
    $failedJobs = @($jobsResponse.jobs | Where-Object {
        $_.conclusion -and $_.conclusion -ne "success" -and $_.conclusion -ne "skipped"
    })

    foreach ($job in $failedJobs) {
        Write-Host "Failed job: $($job.name) [$($job.conclusion)]"

        $failedSteps = @($job.steps | Where-Object {
            $_.conclusion -and $_.conclusion -ne "success" -and $_.conclusion -ne "skipped"
        })
        foreach ($step in $failedSteps) {
            Write-Host "  Failed step: $($step.name) [$($step.conclusion)]"
        }
    }
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$visibilityDeadline = (Get-Date).AddSeconds([Math]::Min($RunVisibilityTimeoutSeconds, $TimeoutSeconds))
$shortSha = $CommitSha.Substring(0, [Math]::Min(7, $CommitSha.Length))
$runsUrl = "$apiBase/actions/runs?head_sha=$CommitSha&event=$Event&per_page=20"

Write-Host "Waiting for GitHub Actions CI for $Owner/$Repo@$shortSha..."

while ((Get-Date) -lt $deadline) {
    $response = Invoke-GitHubApi -Uri $runsUrl
    $runs = @($response.workflow_runs | Where-Object { $_.head_sha -eq $CommitSha })

    if ($runs.Count -eq 0) {
        if ((Get-Date) -ge $visibilityDeadline) {
            Write-Host "CI run did not become visible for $shortSha after $RunVisibilityTimeoutSeconds seconds."
            Write-Host "This usually means workflow triggers do not include event '$Event' for this ref, or the GitHub API cannot access the run."
            Write-Host "Check manually: https://github.com/$Owner/$Repo/actions"
            exit 2
        }

        Write-Host "CI run not visible yet. Waiting $PollSeconds seconds..."
        Start-Sleep -Seconds $PollSeconds
        continue
    }

    $incompleteRuns = @($runs | Where-Object { $_.status -ne "completed" })
    if ($incompleteRuns.Count -gt 0) {
        $statusText = ($runs | ForEach-Object {
            "$($_.name):$($_.status)"
        }) -join ", "
        Write-Host "CI running: $statusText. Waiting $PollSeconds seconds..."
        Start-Sleep -Seconds $PollSeconds
        continue
    }

    $failedRuns = @($runs | Where-Object { $_.conclusion -ne "success" })
    if ($failedRuns.Count -eq 0) {
        Write-Host "CI passed for $shortSha."
        foreach ($run in $runs) {
            Write-Host "Run: $($run.html_url)"
        }
        exit 0
    }

    Write-Host "CI failed for $shortSha."
    foreach ($run in $failedRuns) {
        Write-Host "Workflow: $($run.name) [$($run.conclusion)]"
        Write-Host "Run: $($run.html_url)"
        Get-FailedJobDetails -Run $run
    }
    exit 1
}

Write-Host "CI status timed out for $shortSha after $TimeoutSeconds seconds."
Write-Host "Check manually: https://github.com/$Owner/$Repo/actions"
exit 2
