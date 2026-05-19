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

Write-Host ""
Write-Host "All local regression checks passed."
