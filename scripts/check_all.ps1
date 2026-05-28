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

Invoke-Check "P8 Candidate Primary Surface smoke" {
    & $python scripts/smoke_p8_candidate_primary_surface.py
}

Invoke-Check "P8.9 UI Polish smoke" {
    & $python scripts/smoke_p89_ui_polish.py
}

Invoke-Check "P8 Query Contribution Hidden smoke" {
    & $python scripts/smoke_p8_query_contribution_hidden.py
}

Invoke-Check "P8 Chat Quality smoke" {
    & $python scripts/smoke_p8_chat_quality.py
}

Invoke-Check "P8 Conversational Search Confirmation smoke" {
    & $python scripts/smoke_p8_conversational_search_confirmation.py
}

Invoke-Check "P8.8 Conversation Hardening smoke" {
    & $python scripts/smoke_p88_conversation_hardening.py
}

Invoke-Check "P8 Multi-wave Default smoke" {
    & $python scripts/smoke_p8_multi_wave_default.py
}

Invoke-Check "P8 Candidate Explanation Wording smoke" {
    & $python scripts/smoke_p8_candidate_explanation_wording.py
}

Invoke-Check "P8.5 Agentic Candidate Review Contract smoke" {
    & $python scripts/smoke_p85_agentic_candidate_review_contract.py
}

Invoke-Check "P8.5 Top Candidate Recommendation smoke" {
    & $python scripts/smoke_p85_top_candidate_recommendation.py
}

Invoke-Check "P8.5 Selected Candidate Comparison smoke" {
    & $python scripts/smoke_p85_selected_candidate_comparison.py
}

Invoke-Check "P8.5 Selected Candidate Fit/Gap smoke" {
    & $python scripts/smoke_p85_selected_candidate_fit_gap.py
}

Invoke-Check "P8.5 Workspace Refinement Suggestions smoke" {
    & $python scripts/smoke_p85_workspace_refinement_suggestions.py
}

Invoke-Check "P9 Multi-Provider Search smoke" {
    & $python scripts/smoke_p9_multi_provider_search.py
}

Invoke-Check "P9.5 Final POC Hardening smoke" {
    & $python scripts/smoke_p95_final_poc.py
}

Invoke-Check "P9.6 Post-Deploy Polish smoke" {
    & $python scripts/smoke_p96_post_deploy_polish.py
}

Invoke-Check "P9.7 Semantic Interpreter smoke" {
    & $python scripts/smoke_p97_semantic_interpreter.py
}

Invoke-Check "P9.8 Role Anchoring smoke" {
    & $python scripts/smoke_p98_role_anchoring.py
}

Invoke-Check "P9.9 Search Brief Extractor smoke" {
    & $python scripts/smoke_p99_search_brief_extractor.py
}

Invoke-Check "Phase 9.9 Semantic Search Brief UAT" {
    & $python scripts/uat_phase_9_9_semantic_search_brief.py
}

Invoke-Check "P9.9 Search Brief Refinement smoke" {
    & $python scripts/smoke_p99_search_brief_refinement.py
}

Invoke-Check "P9.10 LocationGuard smoke" {
    & $python scripts/smoke_p910_location_guard.py
}

Invoke-Check "Phase 8.75 No-Live UAT" {
    & $python scripts/uat_phase_8_75_no_live.py
}

Write-Host ""
Write-Host "All local regression checks passed."
