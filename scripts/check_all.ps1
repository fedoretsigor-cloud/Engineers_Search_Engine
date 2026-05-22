$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

$codexNode = Join-Path $HOME ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if ($env:NODE_EXE) {
    $node = $env:NODE_EXE
} elseif (Test-Path $codexNode) {
    $node = $codexNode
} else {
    $node = "node"
}

function Invoke-Check {
    param(
        [string] $Name,
        [scriptblock] $Command
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Command
    Write-Host "OK: $Name"
}

Invoke-Check "Python compileall" {
    & $python -m compileall app scripts
}

Invoke-Check "Frontend JavaScript syntax" {
    & $node --check app/static/candidate_workspace.js
    & $node --check app/static/app.js
}

Invoke-Check "P5 chat adapter smoke" {
    & $python scripts/smoke_p5_chat_adapter.py
}

Invoke-Check "P5 Agent Plan smoke" {
    & $python scripts/smoke_p5_agent_plan.py
}

Invoke-Check "P5 Agent Response smoke" {
    & $python scripts/smoke_p5_agent_response.py
}

Invoke-Check "P5 LLM Wording smoke" {
    & $python scripts/smoke_p5_llm_wording.py
}

Invoke-Check "P5.5 routes smoke" {
    & $python scripts/smoke_p55_routes.py
}

Invoke-Check "P6 Agent Runtime smoke" {
    & $python scripts/smoke_p6_agent_runtime.py
}

Invoke-Check "P6 Runtime Guardrails smoke" {
    & $python scripts/smoke_p6_runtime_guardrails.py
}

Invoke-Check "P6 Unmocked Runtime Execution smoke" {
    & $python scripts/smoke_p6_runtime_unmocked_execution.py
}

Invoke-Check "P7 Agent Messages smoke" {
    & $python scripts/smoke_p7_agent_messages.py
}

Invoke-Check "P7 Wording Validation smoke" {
    & $python scripts/smoke_p7_wording_validation.py
}

Invoke-Check "P7 Golden Conversations smoke" {
    & $python scripts/smoke_p7_golden_conversations.py
}

Invoke-Check "P7.5 Current Flow Regressions smoke" {
    & $python scripts/smoke_p75_current_flow_regressions.py
}

Invoke-Check "P8 Candidate Workspace helper smoke" {
    & $node scripts/smoke_p8_candidate_workspace_helpers.js
}

Invoke-Check "P8 Export UI Wiring smoke" {
    & $python scripts/smoke_p8_export_ui_wiring.py
}

Invoke-Check "P8 Candidate Explanation Wording smoke" {
    & $python scripts/smoke_p8_candidate_explanation_wording.py
}

Write-Host ""
Write-Host "All local regression checks passed."
