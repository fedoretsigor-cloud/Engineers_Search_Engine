const statusElement = document.querySelector("#app-status");
const chatForm = document.querySelector("#recruiter-chat-form");
const chatInput = document.querySelector("#chat-input");
const chatMessagesElement = document.querySelector("#chat-messages");
const chatStatusElement = document.querySelector("#chat-status");
const resetChatButton = document.querySelector("#reset-chat");
const sendChatButton = document.querySelector("#send-chat");
const buildPlanButton = document.querySelector("#build-plan");
const searchButton = document.querySelector("#approve-search");
const briefSummaryPanel = document.querySelector("#brief-summary-panel");
const agentActionQueueElement = document.querySelector("#agent-action-queue");
const profilesOnlyInput = document.querySelector("#profiles-only");
const locationFilterInput = document.querySelector("#location-filter-enabled");
const multiWaveInput = document.querySelector("#multi-wave-enabled");
const planStatus = document.querySelector("#plan-status");
const queryList = document.querySelector("#query-list");
const reportStatus = document.querySelector("#report-status");
const reportGrid = document.querySelector("#report-grid");
const contributionList = document.querySelector("#contribution-list");
const resultsStatus = document.querySelector("#results-status");
const resultsList = document.querySelector("#results-list");
const candidateWorkspace = window.CandidateWorkspace;

const PRIMARY_BUILD_PLAN_MODE = "rule_based";
const AGENT_PLAN_ENDPOINT = "/api/agent/plan";
const AGENT_QUERY_PLAN_ENDPOINT = "/api/agent/query-plan";
const RECRUITER_CHAT_INTENT_ENDPOINT = "/api/recruiter-chat/intent";
const AGENT_RUNTIME_TURN_ENDPOINT = "/api/agent/runtime/turn";
const CANDIDATE_EXPLANATION_WORDING_ENDPOINT = "/api/candidate-workspace/explanation-wording";
const AGENT_ACTION_BUILD_QUERY_PLAN = "build_query_plan";
const AGENT_ACTION_RUN_SINGLE_WAVE = "run_single_wave_search";
const AGENT_ACTION_RUN_MULTI_WAVE = "run_multi_wave_search";
const AGENT_QUEUE_ACTION_BUILD_PLAN = "build_plan";
const AGENT_QUEUE_ACTION_RUN_SEARCH = "run_search";
const AGENT_RUNTIME_TURN_MODE_PREPARE = "prepare";
const AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED = "execute_approved";
const AGENT_RUNTIME_EXECUTION_MODE_SINGLE_WAVE = "single_wave";
const AGENT_RUNTIME_EXECUTION_MODE_MULTI_WAVE = "multi_wave";
const ASSISTANT_SPEAKER_LABEL = "AI Assistant";

const AGENT_ACTION_STATUS_LABELS = {
  blocked: "Blocked",
  ready: "Ready",
  ready_for_approval: "Ready to run",
  running: "Running",
  completed: "Completed",
  stale: "Stale",
  failed: "Failed",
};

const AGENT_MESSAGE_TYPES = {
  ONBOARDING: "onboarding",
  CLARIFICATION_QUESTION: "clarification_question",
  BRIEF_SUMMARY: "brief_summary",
  BRIEF_REFINEMENT_APPLIED: "brief_refinement_applied",
  BRIEF_REFINEMENT_REJECTED: "brief_refinement_rejected",
  VALIDATION_FEEDBACK: "validation_feedback",
  SAFETY_REFUSAL: "safety_refusal",
  TOOL_UNAVAILABLE: "tool_unavailable",
  AGENT_PLAN: "agent_plan",
  AGENT_PLAN_UNSUPPORTED: "agent_plan_unsupported",
  PLANNING_NEEDS_CLARIFICATION: "planning_needs_clarification",
  SYSTEM_ERROR: "system_error",
  AGENT_RESPONSE: "agent_response",
};

const AGENT_MESSAGE_TYPE_META = {
  [AGENT_MESSAGE_TYPES.ONBOARDING]: {
    label: "Onboarding",
    className: "typed-onboarding",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.CLARIFICATION_QUESTION]: {
    label: "Clarification",
    className: "typed-clarification",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.BRIEF_SUMMARY]: {
    label: "Search summary",
    className: "typed-brief-summary",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.BRIEF_REFINEMENT_APPLIED]: {
    label: "Search updated",
    className: "typed-brief-refinement",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.BRIEF_REFINEMENT_REJECTED]: {
    label: "Search update blocked",
    className: "typed-brief-refinement-rejected",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK]: {
    label: "Validation",
    className: "typed-validation",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.SAFETY_REFUSAL]: {
    label: "Safety boundary",
    className: "typed-safety",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.TOOL_UNAVAILABLE]: {
    label: "Configuration issue",
    className: "typed-tool-unavailable",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.AGENT_PLAN]: {
    label: "Search ready",
    className: "typed-agent-plan",
    speaker: "AI Agent",
  },
  [AGENT_MESSAGE_TYPES.AGENT_PLAN_UNSUPPORTED]: {
    label: "Unsupported brief",
    className: "typed-agent-plan-unsupported",
    speaker: "AI Agent",
  },
  [AGENT_MESSAGE_TYPES.PLANNING_NEEDS_CLARIFICATION]: {
    label: "Search needs input",
    className: "typed-planning-needs-clarification",
    speaker: "AI Agent",
  },
  [AGENT_MESSAGE_TYPES.SYSTEM_ERROR]: {
    label: "System error",
    className: "typed-system-error",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.AGENT_RESPONSE]: {
    label: "Search completed",
    className: "typed-agent-response",
    speaker: "AI Agent",
  },
};

const RECRUITER_CHAT_TOOL_UNAVAILABLE_FIELDS = new Set([
  "openai_api_key",
  "openai_model",
  "openai",
]);

let messages = [];
let draftBrief = null;
let normalizedBrief = null;
let chatState = "drafting";
let recommendedPlannerMode = PRIMARY_BUILD_PLAN_MODE;
let currentChatLanguage = "en";
let currentAgentPlanData = null;
let currentAgentPlan = null;
let currentAgentAction = null;
let pendingChatAction = null;
let adaptedStructuredRequest = null;
let latestPlannerData = null;
let latestQueryPlan = null;
let latestPlanFingerprint = null;
let latestExecutablePlan = false;
let latestAgentResponse = null;
let currentRuntimePendingApproval = null;
let currentRuntimeToolCall = null;
let runtimeApprovalVersion = 0;
let workspaceRunCounter = 0;
let latestWorkspaceRun = null;
let workspaceCandidates = [];
let visibleWorkspaceCandidates = [];
let workspaceViewState = candidateWorkspace.defaultWorkspaceViewState();
let workspaceReviewStateByCandidateId = {};
let workspaceExplanationWordingByKey = {};
let workspaceExportState = defaultWorkspaceExportState();
let workspacePaginationState = defaultWorkspacePaginationState();
let chatRequestInFlight = false;
let agentPlanRequestInFlight = false;
let planRequestInFlight = false;
let runtimePrepareRequestInFlight = false;
let searchRequestInFlight = false;
let searchConfirmationInFlight = false;
let interactionVersion = 0;
let chatTransientMessageCounter = 0;
let agentActionDisplayState = {
  [AGENT_QUEUE_ACTION_BUILD_PLAN]: null,
  [AGENT_QUEUE_ACTION_RUN_SEARCH]: null,
};

const MULTI_WAVE_DEFAULTS = {
  max_waves: 5,
  min_new_unique_per_wave: 3,
  patience: 2,
};
const DEFAULT_MULTI_WAVE_ENABLED = true;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pluralize(count, singular, plural) {
  return count === 1 ? singular : plural;
}

function displayValue(value, fallback = "n/a") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return value;
}

function displayList(values = [], fallback = "none") {
  return values.length ? values.join(", ") : fallback;
}

function arrayValue(value) {
  return Array.isArray(value) ? value : [];
}

function shortFingerprint(value) {
  if (!value) {
    return "not bound";
  }

  const text = String(value);
  return text.length > 12 ? `${text.slice(0, 10)}...` : text;
}

function currentRunSearchAction() {
  return multiWaveInput.checked
    ? AGENT_ACTION_RUN_MULTI_WAVE
    : AGENT_ACTION_RUN_SINGLE_WAVE;
}

function currentRunSearchModeLabel() {
  return multiWaveInput.checked ? "Multi-wave" : "Single-wave";
}

function currentRunSearchExecutionMode() {
  return multiWaveInput.checked
    ? AGENT_RUNTIME_EXECUTION_MODE_MULTI_WAVE
    : AGENT_RUNTIME_EXECUTION_MODE_SINGLE_WAVE;
}

function clearRuntimeApproval() {
  runtimeApprovalVersion += 1;
  currentRuntimePendingApproval = null;
  currentRuntimeToolCall = null;
  runtimePrepareRequestInFlight = false;
}

function defaultWorkspaceExportState() {
  return {
    scope: candidateWorkspace.normalizeExportScope("visible"),
    format: candidateWorkspace.normalizeExportFormat("csv"),
    status: "",
  };
}

function defaultWorkspacePaginationState() {
  return {
    currentPage: 1,
    pageSize: 8,
  };
}

function clampWorkspacePage(page, totalPages) {
  const safeTotalPages = Math.max(Number(totalPages) || 1, 1);
  const safePage = Math.max(Number(page) || 1, 1);
  return Math.min(safePage, safeTotalPages);
}

function workspacePaginationModel(candidates = visibleWorkspaceCandidates) {
  const pageSize = Math.max(Number(workspacePaginationState.pageSize) || 8, 1);
  const totalItems = candidates.length;
  const totalPages = Math.max(Math.ceil(totalItems / pageSize), 1);
  const currentPage = clampWorkspacePage(workspacePaginationState.currentPage, totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;

  workspacePaginationState = {
    ...workspacePaginationState,
    currentPage,
    pageSize,
  };

  return {
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    startIndex,
    endIndex,
    pageCandidates: candidates.slice(startIndex, endIndex),
  };
}

function renderWorkspacePaginationControls(pagination) {
  if (!pagination || pagination.totalPages <= 1) {
    return "";
  }

  return `
    <nav class="candidate-workspace-pagination" aria-label="Candidate results pages">
      <span>
        Page ${escapeHtml(pagination.currentPage)} of ${escapeHtml(pagination.totalPages)}
      </span>
      <div class="candidate-workspace-pagination-controls">
        <button
          type="button"
          class="secondary-button"
          data-workspace-page-action="previous"
          ${pagination.currentPage <= 1 ? "disabled" : ""}
        >
          Previous
        </button>
        <button
          type="button"
          class="secondary-button"
          data-workspace-page-action="next"
          ${pagination.currentPage >= pagination.totalPages ? "disabled" : ""}
        >
          Next
        </button>
      </div>
    </nav>
  `;
}

function updateWorkspaceExportStatusTarget() {
  const statusTarget = resultsList.querySelector("[data-workspace-export-status]");
  if (statusTarget) {
    statusTarget.textContent = workspaceExportState.status || "";
  }
}

function setWorkspaceExportStatus(status, render = false) {
  workspaceExportState = {
    ...workspaceExportState,
    status: String(status || ""),
  };
  if (render && latestWorkspaceRun) {
    renderWorkspaceResults(latestWorkspaceRun.report);
  } else {
    updateWorkspaceExportStatusTarget();
  }
}

function clearWorkspaceExportStatus(render = false) {
  if (!workspaceExportState.status) {
    return;
  }
  setWorkspaceExportStatus("", render);
}

function clearWorkspaceState() {
  latestWorkspaceRun = null;
  workspaceCandidates = [];
  visibleWorkspaceCandidates = [];
  workspaceViewState = candidateWorkspace.defaultWorkspaceViewState();
  workspaceReviewStateByCandidateId = {};
  workspaceExplanationWordingByKey = {};
  workspaceExportState = defaultWorkspaceExportState();
  workspacePaginationState = defaultWorkspacePaginationState();
}

function captureWorkspaceRunContext(searchData = {}) {
  workspaceRunCounter += 1;
  return {
    run_counter: workspaceRunCounter,
    idempotency_key: currentRuntimePendingApproval?.idempotency_key,
    tool_call_id:
      currentRuntimePendingApproval?.tool_call_id ||
      currentRuntimeToolCall?.id ||
      currentRuntimeToolCall?.tool_call_id,
    tool_name: currentRunSearchAction(),
    execution_mode: currentRunSearchExecutionMode(),
    context_fingerprint: currentRuntimePendingApproval?.context_fingerprint,
    tool_input_fingerprint: currentRuntimePendingApproval?.tool_input_fingerprint,
    plan_fingerprint:
      latestPlanFingerprint ||
      searchData.query_plan?.plan_fingerprint ||
      latestQueryPlan?.plan_fingerprint,
    query_count:
      searchData.query_plan?.queries?.length ||
      latestQueryPlan?.queries?.length ||
      0,
    created_at: new Date().toISOString(),
  };
}

function replaceWorkspaceRun(dedupedResults = [], report = null, runContext = {}) {
  const mappedCandidates = candidateWorkspace.mapDedupedResultsToWorkspaceCandidates(
    dedupedResults
  );
  const workspaceRunId = candidateWorkspace.createWorkspaceRunId(runContext);
  const candidates = mappedCandidates.map((candidate, index) => ({
    ...candidate,
    wording_target_key: candidateWorkspace.createWordingTargetKey(
      runContext.run_counter || workspaceRunCounter || 1,
      index
    ),
  }));

  latestWorkspaceRun = {
    workspace_run_id: workspaceRunId,
    created_at: runContext.created_at || new Date().toISOString(),
    run_context: runContext,
    report,
    total_candidates: candidates.length,
  };
  workspaceCandidates = candidates;
  visibleWorkspaceCandidates = candidates;
  workspaceViewState = candidateWorkspace.defaultWorkspaceViewState();
  workspaceReviewStateByCandidateId =
    candidateWorkspace.createReviewStateForCandidates(candidates);
  workspaceExplanationWordingByKey = {};
  workspaceExportState = defaultWorkspaceExportState();
  workspacePaginationState = defaultWorkspacePaginationState();
}

function renderWorkspaceOption(value, label, currentValue) {
  return `<option value="${escapeHtml(value)}" ${
    currentValue === value ? "selected" : ""
  }>${escapeHtml(label)}</option>`;
}

function renderWorkspaceExportBlock() {
  const exportState = {
    scope: candidateWorkspace.normalizeExportScope(workspaceExportState.scope),
    format: candidateWorkspace.normalizeExportFormat(workspaceExportState.format),
    status: workspaceExportState.status || "",
  };

  return `
    <div class="candidate-workspace-export" aria-label="Candidate export controls">
      <div class="candidate-workspace-export-controls">
        <label>
          Export scope
          <select data-workspace-export-control="scope">
            ${renderWorkspaceOption("visible", "Visible", exportState.scope)}
            ${renderWorkspaceOption("shortlisted", "Shortlisted", exportState.scope)}
            ${renderWorkspaceOption("all", "All", exportState.scope)}
          </select>
        </label>
        <label>
          Format
          <select data-workspace-export-control="format">
            ${renderWorkspaceOption("csv", "CSV", exportState.format)}
            ${renderWorkspaceOption("markdown", "Markdown", exportState.format)}
          </select>
        </label>
        <button type="button" class="secondary-button workspace-export-button" data-workspace-export-action="download">
          Export
        </button>
      </div>
      <span class="candidate-workspace-export-status" role="status" aria-live="polite" data-workspace-export-status>
        ${escapeHtml(exportState.status)}
      </span>
    </div>
  `;
}

function renderWorkspaceToolbar() {
  if (!latestWorkspaceRun) {
    return "";
  }

  const runLabel = latestWorkspaceRun.run_context?.execution_mode || "search";
  const queryCount = latestWorkspaceRun.run_context?.query_count || 0;
  const candidateCount = latestWorkspaceRun.total_candidates || workspaceCandidates.length || 0;

  return `
    <section class="candidate-workspace-toolbar candidate-workspace-summary" aria-label="Candidate results summary">
      <div class="candidate-workspace-meta">
        <div>
          <span>Candidate Results</span>
          <strong>${escapeHtml(candidateCount)} unique ${escapeHtml(
            pluralize(candidateCount, "candidate", "candidates")
          )}</strong>
        </div>
        <p>${escapeHtml(displayValue(runLabel))}, ${escapeHtml(queryCount)} ${escapeHtml(
          pluralize(queryCount, "query", "queries")
        )}</p>
      </div>
    </section>
  `;
}

function renderWorkspaceProfileLink(candidate = {}) {
  if (!candidate.profile_href) {
    return candidate.profile_url
      ? `<p class="workspace-profile-url">${escapeHtml(candidate.profile_url)}</p>`
      : "";
  }

  return `
    <a href="${escapeHtml(candidate.profile_href)}" target="_blank" rel="noreferrer">
      ${escapeHtml(candidate.profile_url || candidate.profile_href)}
    </a>
  `;
}

function renderWorkspaceRowField(label, value) {
  return `
    <div class="candidate-row-field">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(displayValue(value, "N/A"))}</strong>
    </div>
  `;
}

function renderWorkspaceReviewStatusOptions(currentStatus) {
  return [
    ["new", "New"],
    ["reviewing", "Reviewing"],
    ["shortlisted", "Shortlisted"],
    ["not_a_fit", "Not a fit"],
  ]
    .map(([value, label]) => renderWorkspaceOption(value, label, currentStatus))
    .join("");
}

function renderExplanationReasonList(items = [], emptyText = "", overlayReasonsByKey = {}) {
  if (!items.length) {
    return emptyText ? `<p>${escapeHtml(emptyText)}</p>` : "";
  }

  return `
    <ul>
      ${items
        .map((item) => {
          const overlayReason = overlayReasonsByKey[item.reason_key] || null;
          return `<li>${escapeHtml(overlayReason?.label || item.label || item.code)}</li>`;
        })
        .join("")}
    </ul>
  `;
}

function workspaceWordingStateKey(workspaceRunId, wordingTargetKey) {
  return `${workspaceRunId || "no-run"}::${wordingTargetKey || "no-target"}`;
}

function workspaceWordingStateForCandidate(candidate = {}) {
  if (!latestWorkspaceRun || !candidate.wording_target_key) {
    return null;
  }
  return (
    workspaceExplanationWordingByKey[
      workspaceWordingStateKey(latestWorkspaceRun.workspace_run_id, candidate.wording_target_key)
    ] || null
  );
}

function overlayReasonsByKey(overlay = null) {
  return arrayValue(overlay?.reasons).reduce((items, reason) => {
    if (reason?.reason_key) {
      items[reason.reason_key] = reason;
    }
    return items;
  }, {});
}

function wordingStatusText(state = null) {
  if (!state) {
    return "";
  }
  if (state.status === "pending") {
    return "Improving wording...";
  }
  if (state.status === "applied") {
    return "AI wording applied. Deterministic facts unchanged.";
  }
  if (state.status === "fallback") {
    if (state.reason === "openai_not_configured") {
      return "Wording helper unavailable. Deterministic wording kept.";
    }
    if (state.reason === "unsupported_language") {
      return "Candidate explanation wording supports English only. Deterministic wording kept.";
    }
    return "Could not improve wording. Deterministic wording kept.";
  }
  return "";
}

function renderCandidateExplanationWordingStatus(state = null) {
  const text = wordingStatusText(state);
  return text ? `<span class="candidate-explanation-wording-status">${escapeHtml(text)}</span>` : "";
}

function renderCandidateExplanation(candidate) {
  if (!candidateWorkspace.buildCandidateExplanation) {
    return "";
  }

  const explanation = candidateWorkspace.buildCandidateExplanation(candidate);
  if (!explanation || explanation.source !== "deterministic_workspace_facts") {
    return "";
  }
  const renderableReasons = candidateWorkspace.buildCandidateExplanationRenderableReasons(explanation);
  const wordingState = workspaceWordingStateForCandidate(candidate);
  const activeOverlay = wordingState?.status === "applied" ? wordingState.overlay : null;
  const activeOverlayReasons = overlayReasonsByKey(activeOverlay);
  const summary = activeOverlay?.summary || explanation.summary || "Review returned candidate details manually.";
  const wordingPending = wordingState?.status === "pending";

  return `
    <section class="candidate-explanation" aria-label="Candidate explanation">
      <h4>Candidate explanation</h4>
      <p>${escapeHtml(summary)}</p>
      <div class="candidate-explanation-grid">
        <div>
          <span>Positive signals</span>
          ${renderExplanationReasonList(
            renderableReasons.positive_signals,
            "No strong positive signal selected.",
            activeOverlayReasons
          )}
        </div>
        <div>
          <span>Cautions</span>
          ${renderExplanationReasonList(
            renderableReasons.cautions,
            "No caution selected.",
            activeOverlayReasons
          )}
        </div>
        <div>
          <span>Evidence</span>
          ${renderExplanationReasonList(
            renderableReasons.evidence_items,
            "No extra evidence returned.",
            activeOverlayReasons
          )}
        </div>
      </div>
      <div class="candidate-explanation-wording-actions">
        <button
          type="button"
          class="secondary-button"
          data-workspace-action="improve-wording"
          ${wordingPending ? "disabled" : ""}
        >
          ${wordingPending ? "Improving..." : "Improve wording"}
        </button>
        ${renderCandidateExplanationWordingStatus(wordingState)}
      </div>
    </section>
  `;
}

function renderRecommendationList(items = [], emptyText = "") {
  if (!items.length) {
    return emptyText ? `<p>${escapeHtml(emptyText)}</p>` : "";
  }
  return `
    <ul>
      ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderTopCandidateRecommendation() {
  if (!candidateWorkspace.buildTopCandidateRecommendation || !visibleWorkspaceCandidates.length) {
    return "";
  }

  const recommendation = candidateWorkspace.buildTopCandidateRecommendation(
    visibleWorkspaceCandidates,
    workspaceReviewStateByCandidateId,
    {
      limit: 3,
      scope: "visible_candidates",
    }
  );

  if (
    !recommendation ||
    recommendation.source !== "deterministic_workspace_facts" ||
    !recommendation.recommendations.length
  ) {
    return "";
  }

  return `
    <section class="workspace-agent-review" aria-label="Agent candidate review">
      <div class="workspace-agent-review-header">
        <div>
          <span>Agent review</span>
          <strong>Suggested first review</strong>
        </div>
        <p>Based on current visible candidates.</p>
      </div>
      <ol class="workspace-agent-review-list">
        ${recommendation.recommendations
          .map((item, index) => {
            const quality = item.quality_score === null ? "n/a" : item.quality_score;
            return `
              <li class="${index === 0 ? "primary" : ""}">
                <div class="workspace-agent-review-candidate">
                  <span>#${escapeHtml(item.display_index)}</span>
                  <div>
                    <strong>${escapeHtml(item.display_name)}</strong>
                    <p>${escapeHtml(item.headline)}</p>
                  </div>
                  <small>${escapeHtml(quality)} ${escapeHtml(item.quality_bucket || "")}</small>
                </div>
                <p>${escapeHtml(item.summary)}</p>
                <div class="workspace-agent-review-reasons">
                  <div>
                    <span>Why</span>
                    ${renderRecommendationList(item.reasons, "Returned fit signals are limited.")}
                  </div>
                  <div>
                    <span>Check</span>
                    ${renderRecommendationList(item.cautions, "No major caution selected.")}
                  </div>
                </div>
              </li>
            `;
          })
          .join("")}
      </ol>
    </section>
  `;
}

function renderSelectedCandidateComparison() {
  if (!candidateWorkspace.buildSelectedCandidateComparison || !visibleWorkspaceCandidates.length) {
    return "";
  }

  const comparison = candidateWorkspace.buildSelectedCandidateComparison(
    visibleWorkspaceCandidates,
    workspaceReviewStateByCandidateId,
    {
      limit: 4,
      scope: "visible_shortlisted_candidates",
    }
  );

  if (
    !comparison ||
    comparison.source !== "deterministic_workspace_facts" ||
    !comparison.selected_count
  ) {
    return "";
  }

  if (!comparison.ready) {
    return `
      <section class="workspace-agent-review workspace-selected-comparison" aria-label="Selected candidate comparison">
        <div class="workspace-agent-review-header">
          <div>
            <span>Agent review</span>
            <strong>Selected comparison</strong>
          </div>
          <p>Based on visible shortlisted candidates.</p>
        </div>
        <p class="workspace-agent-review-empty">Shortlist one more visible candidate to compare them.</p>
      </section>
    `;
  }

  return `
    <section class="workspace-agent-review workspace-selected-comparison" aria-label="Selected candidate comparison">
      <div class="workspace-agent-review-header">
        <div>
          <span>Agent review</span>
          <strong>Selected comparison</strong>
        </div>
        <p>Based on ${escapeHtml(comparison.selected_count)} visible shortlisted ${escapeHtml(
          pluralize(comparison.selected_count, "candidate", "candidates")
        )}.</p>
      </div>
      <div class="workspace-selected-comparison-grid">
        ${comparison.candidates
          .map((candidate) => {
            const quality = candidate.quality_score === null ? "n/a" : candidate.quality_score;
            return `
              <article class="workspace-comparison-card">
                <div class="workspace-agent-review-candidate">
                  <span>#${escapeHtml(candidate.display_index)}</span>
                  <div>
                    <strong>${escapeHtml(candidate.display_name)}</strong>
                    <p>${escapeHtml(candidate.headline)}</p>
                  </div>
                  <small>${escapeHtml(quality)} ${escapeHtml(candidate.quality_bucket || "")}</small>
                </div>
                <dl class="workspace-comparison-facts">
                  <div><dt>Role</dt><dd>${escapeHtml(candidate.role)}</dd></div>
                  <div><dt>Tech</dt><dd>${escapeHtml(candidate.technology)}</dd></div>
                  <div><dt>Location</dt><dd>${escapeHtml(candidate.location_status)}</dd></div>
                  <div><dt>Stack</dt><dd>${escapeHtml(candidate.stack_terms.length ? candidate.stack_terms.join(", ") : candidate.stack_fit)}</dd></div>
                  <div><dt>Seniority</dt><dd>${escapeHtml(candidate.seniority)}</dd></div>
                </dl>
                <div class="workspace-agent-review-reasons workspace-comparison-lists">
                  <div>
                    <span>Signals</span>
                    ${renderRecommendationList(candidate.positive_signals, "Returned fit signals are limited.")}
                  </div>
                  <div>
                    <span>Check</span>
                    ${renderRecommendationList(
                      candidate.cautions.concat(candidate.review_flags),
                      "No major caution selected."
                    )}
                  </div>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
      <div class="workspace-comparison-summary">
        <div>
          <span>Shared signals</span>
          ${renderRecommendationList(comparison.shared_signals, "No shared signal across all selected candidates.")}
        </div>
        <div>
          <span>Differences</span>
          ${renderRecommendationList(comparison.differences, "Returned comparison facts are similar.")}
        </div>
      </div>
    </section>
  `;
}

function renderSelectedCandidateFitGapExplanation() {
  if (!candidateWorkspace.buildSelectedCandidateFitGapExplanation || !visibleWorkspaceCandidates.length) {
    return "";
  }

  const fitGap = candidateWorkspace.buildSelectedCandidateFitGapExplanation(
    visibleWorkspaceCandidates,
    workspaceReviewStateByCandidateId,
    {
      limit: 4,
      scope: "visible_shortlisted_candidates",
    }
  );

  if (
    !fitGap ||
    fitGap.source !== "deterministic_workspace_facts" ||
    !fitGap.ready ||
    !fitGap.candidate_fit_gaps.length
  ) {
    return "";
  }

  return `
    <section class="workspace-agent-review workspace-fit-gap-review" aria-label="Selected candidate fit and gap explanation">
      <div class="workspace-agent-review-header">
        <div>
          <span>Agent review</span>
          <strong>Fit and gaps</strong>
        </div>
        <p>Based on visible shortlisted candidates.</p>
      </div>
      <p class="workspace-fit-gap-summary">${escapeHtml(fitGap.summary)}</p>
      <div class="workspace-comparison-summary">
        <div>
          <span>Shared fit</span>
          ${renderRecommendationList(fitGap.shared_fits, "No fit signal is shared by all selected candidates.")}
        </div>
        <div>
          <span>Shared gaps</span>
          ${renderRecommendationList(fitGap.shared_gaps, "No common manual-review gap across all selected candidates.")}
        </div>
      </div>
      <div class="workspace-selected-comparison-grid">
        ${fitGap.candidate_fit_gaps
          .map((candidate) => {
            const quality = candidate.quality_score === null ? "n/a" : candidate.quality_score;
            return `
              <article class="workspace-comparison-card workspace-fit-gap-card">
                <div class="workspace-agent-review-candidate">
                  <span>#${escapeHtml(candidate.display_index)}</span>
                  <div>
                    <strong>${escapeHtml(candidate.display_name)}</strong>
                    <p>${escapeHtml(candidate.headline)}</p>
                  </div>
                  <small>${escapeHtml(quality)} ${escapeHtml(candidate.quality_bucket || "")}</small>
                </div>
                <div class="workspace-agent-review-reasons workspace-comparison-lists">
                  <div>
                    <span>Fit</span>
                    ${renderRecommendationList(candidate.fit_labels, "Returned fit signals are limited.")}
                  </div>
                  <div>
                    <span>Gaps</span>
                    ${renderRecommendationList(candidate.gap_labels, "No major gap selected.")}
                  </div>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderWorkspaceRefinementSuggestions() {
  if (!candidateWorkspace.buildWorkspaceRefinementSuggestions || !latestWorkspaceRun) {
    return "";
  }

  const guidance = candidateWorkspace.buildWorkspaceRefinementSuggestions(
    visibleWorkspaceCandidates,
    workspaceReviewStateByCandidateId,
    {
      limit: 3,
      scope: "visible_candidates",
    }
  );

  if (
    !guidance ||
    guidance.source !== "deterministic_workspace_facts" ||
    !guidance.suggestions.length
  ) {
    return "";
  }

  return `
    <section class="workspace-agent-review workspace-refinement-guidance" aria-label="Workspace review guidance">
      <div class="workspace-agent-review-header">
        <div>
          <span>Agent review</span>
          <strong>Review guidance</strong>
        </div>
        <p>Based on current visible candidates.</p>
      </div>
      <div class="workspace-refinement-grid">
        ${guidance.suggestions
          .map(
            (suggestion) => `
              <article class="workspace-refinement-card">
                <span>${escapeHtml(suggestion.suggestion_type.replace(/_/g, " "))}</span>
                <strong>${escapeHtml(suggestion.title)}</strong>
                <p>${escapeHtml(suggestion.reason)}</p>
                <p>${escapeHtml(suggestion.guidance)}</p>
              </article>
            `
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderWorkspaceCandidate(candidate) {
  const selectedStack = candidate.selected_stack_terms_found.length
    ? candidate.selected_stack_terms_found.join(", ")
    : displayValue(candidate.stack_fit);
  const qualityDisplay = candidate.has_quality_score ? candidate.quality_score : "n/a";
  const roleDisplay = candidate.raw?.result?.role_display || candidate.headline || candidate.raw_title;
  const sourceDisplay = candidate.source || "linkedin";

  return `
    <article class="result-item candidate-card candidate-result-row workspace-candidate-row" data-candidate-id="${escapeHtml(
      candidate.candidate_id
    )}">
      <div class="candidate-row-main">
        <div class="candidate-score candidate-score-pill" aria-label="Quality score">
          <span>Score</span>
          <strong>${escapeHtml(qualityDisplay)}</strong>
        </div>
        <div class="candidate-identity candidate-row-identity">
          <h3>${escapeHtml(candidate.display_name)}</h3>
          <p>${escapeHtml(candidate.headline || candidate.raw_title || "No headline returned.")}</p>
          <div class="candidate-row-link">
            ${renderWorkspaceProfileLink(candidate)}
          </div>
        </div>
        ${renderWorkspaceRowField("Role", roleDisplay)}
        ${renderWorkspaceRowField("Location", candidate.location_status)}
        ${renderWorkspaceRowField("Stack", selectedStack)}
        ${renderWorkspaceRowField("Source", sourceDisplay)}
      </div>
    </article>
  `;
}

function renderWorkspaceResults(report = null) {
  if (!latestWorkspaceRun) {
    resultsList.innerHTML = "";
    resultsStatus.textContent = "Run a search to see candidates.";
    return;
  }

  visibleWorkspaceCandidates = recomputeVisibleWorkspaceCandidates();
  const pagination = workspacePaginationModel(visibleWorkspaceCandidates);

  if (!workspaceCandidates.length) {
    resultsStatus.textContent = report?.raw_total
      ? `${report.raw_total} raw ${pluralize(
          report.raw_total,
          "result",
          "results"
        )} returned, no unique candidates after filters and dedupe.`
      : "No candidates returned.";
    resultsList.innerHTML = renderWorkspaceToolbar();
    return;
  }

  resultsStatus.textContent = `${workspaceCandidates.length} unique ${pluralize(
    workspaceCandidates.length,
    "candidate",
    "candidates"
  )} found.`;

  resultsList.innerHTML = `
    ${renderWorkspaceToolbar()}
    ${renderSelectedCandidateComparison()}
    ${renderSelectedCandidateFitGapExplanation()}
    ${
      visibleWorkspaceCandidates.length
        ? `<section class="candidate-workspace-list candidate-workspace-page">${pagination.pageCandidates
            .map(renderWorkspaceCandidate)
            .join("")}</section>
          ${renderWorkspacePaginationControls(pagination)}`
        : `<div class="workspace-empty-state">No candidates match current view filters. Reset filters to show all candidates.</div>`
    }
  `;
}

function clearAgentActionDisplayState(actionIds = null) {
  const ids = actionIds || [
    AGENT_QUEUE_ACTION_BUILD_PLAN,
    AGENT_QUEUE_ACTION_RUN_SEARCH,
  ];
  ids.forEach((actionId) => {
    agentActionDisplayState[actionId] = null;
  });
}

function setAgentActionDisplayState(actionId, status, detail = "") {
  agentActionDisplayState[actionId] = status ? { status, detail } : null;
}

function actionStatusLabel(status) {
  return AGENT_ACTION_STATUS_LABELS[status] || displayValue(status);
}

function plannerLabel(value) {
  const labels = {
    rule_based: "Search details",
    ai: "AI preview",
    ai_with_fallback: "AI-assisted preview",
    draft_query_plan: "Draft search details",
    validated_not_executable: "Validated preview",
    rejected: "Rejected",
    rule_based_fallback: "Fallback search details",
    needs_clarification: "Needs clarification",
    ready_for_planning: "Ready",
  };

  return labels[value] || displayValue(value);
}

function validationMessage(errors = []) {
  return errors.map((error) => `${error.field}: ${error.message}`).join(" ");
}

function plannerModeForBuildPlan() {
  return currentAgentAction?.planner_mode || PRIMARY_BUILD_PLAN_MODE;
}

function hasSupportedAgentAction() {
  return Boolean(
    currentAgentPlan?.brief_fingerprint &&
      currentAgentAction?.action === AGENT_ACTION_BUILD_QUERY_PLAN &&
      currentAgentAction?.endpoint === AGENT_QUERY_PLAN_ENDPOINT &&
      currentAgentAction?.planner_mode === PRIMARY_BUILD_PLAN_MODE &&
      currentAgentAction?.requires_approval === false
  );
}

function clearPendingChatAction() {
  pendingChatAction = null;
}

function currentBuildPlanActionIdentity() {
  if (!hasSupportedAgentAction()) {
    return null;
  }

  return {
    type: "build_search_plan",
    briefFingerprint: currentAgentPlan.brief_fingerprint,
    endpoint: currentAgentAction.endpoint,
    plannerMode: currentAgentAction.planner_mode,
    action: currentAgentAction.action,
  };
}

function currentSearchRunConfirmationIdentity() {
  const actionIdentity = currentBuildPlanActionIdentity();
  if (!actionIdentity) {
    return null;
  }

  return {
    ...actionIdentity,
    type: "start_search",
    runAction: currentRunSearchAction(),
    executionMode: currentRunSearchExecutionMode(),
    multiWaveEnabled: multiWaveInput.checked,
  };
}

function setPendingSearchRunChatAction() {
  const actionIdentity = currentSearchRunConfirmationIdentity();
  pendingChatAction = actionIdentity
    ? {
        ...actionIdentity,
        createdAt: Date.now(),
      }
    : null;
}

function pendingSearchRunConfirmationIsCurrent() {
  const actionIdentity = currentSearchRunConfirmationIdentity();
  return Boolean(
    pendingChatAction?.type === "start_search" &&
      actionIdentity &&
      pendingChatAction.briefFingerprint === actionIdentity.briefFingerprint &&
      pendingChatAction.endpoint === actionIdentity.endpoint &&
      pendingChatAction.plannerMode === actionIdentity.plannerMode &&
      pendingChatAction.action === actionIdentity.action &&
      pendingChatAction.runAction === actionIdentity.runAction &&
      pendingChatAction.executionMode === actionIdentity.executionMode &&
      pendingChatAction.multiWaveEnabled === actionIdentity.multiWaveEnabled
  );
}

function currentSearchSummaryUpdateIdentity(field = null) {
  const actionIdentity = currentBuildPlanActionIdentity();
  const briefIdentity =
    currentAgentPlan?.brief_fingerprint ||
    (normalizedBrief
      ? JSON.stringify({
          role_family: normalizedBrief.role_family || null,
          technology: normalizedBrief.technology || null,
          stack: normalizedBrief.stack || [],
          location: normalizedBrief.location || null,
          seniority: normalizedBrief.seniority || null,
          search_depth: normalizedBrief.search_depth || null,
        })
      : null);

  if (!briefIdentity) {
    return null;
  }

  return {
    ...(actionIdentity || {}),
    type: field ? "update_search_summary_field" : "update_search_summary",
    briefFingerprint: briefIdentity,
    field,
  };
}

function setPendingSearchSummaryUpdateAction() {
  const actionIdentity = currentSearchSummaryUpdateIdentity();
  pendingChatAction = actionIdentity
    ? {
        ...actionIdentity,
        createdAt: Date.now(),
      }
    : null;
}

function setPendingSearchSummaryUpdateFieldAction(field) {
  const actionIdentity = currentSearchSummaryUpdateIdentity(field);
  pendingChatAction = actionIdentity
    ? {
        ...actionIdentity,
        createdAt: Date.now(),
      }
    : null;
}

function pendingSearchSummaryUpdateIsCurrent() {
  if (
    !pendingChatAction ||
    !["update_search_summary", "update_search_summary_field"].includes(
      pendingChatAction.type
    )
  ) {
    return false;
  }

  const actionIdentity = currentSearchSummaryUpdateIdentity(pendingChatAction.field || null);
  return Boolean(
    actionIdentity &&
      pendingChatAction.briefFingerprint === actionIdentity.briefFingerprint &&
      pendingChatAction.field === actionIdentity.field
  );
}

function normalizeChatCommandText(text) {
  return String(text || "")
    .trim()
    .toLowerCase()
    .replace(/[!"'`.,;:!?()[\]{}<>]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function isBuildPlanConfirmation(text) {
  const normalizedText = normalizeChatCommandText(text);
  return [
    "yes",
    "yep",
    "yeah",
    "build it",
    "build plan",
    "build search plan",
    "prepare it",
    "prepare search",
    "prepare the search",
    "go ahead",
    "да",
    "давай",
    "построй",
    "строим",
    "построить",
  ].includes(normalizedText);
}

function isBuildPlanDismissal(text) {
  const normalizedText = normalizeChatCommandText(text);
  return ["no", "not now", "нет", "пока нет", "не сейчас"].includes(normalizedText);
}

const SEARCH_RUN_CONFIRMATIONS = new Set([
  "yes",
  "y",
  "yep",
  "yeah",
  "ok",
  "okay",
  "go ahead",
  "proceed",
  "run it",
  "run search",
  "start",
  "start search",
  "\u0434\u0430",
  "\u043e\u043a",
  "\u043e\u043a\u0435\u0439",
  "\u0434\u0430\u0432\u0430\u0439",
  "\u0432\u043f\u0435\u0440\u0435\u0434",
  "\u0437\u0430\u043f\u0443\u0441\u043a\u0430\u0439",
  "\u0441\u0442\u0430\u0440\u0442",
  "\u043d\u0430\u0447\u0438\u043d\u0430\u0439",
]);

const SEARCH_RUN_REFINEMENTS = new Set([
  "no",
  "not yet",
  "change",
  "refine",
  "edit",
  "not now",
  "\u043d\u0435\u0442",
  "\u043d\u0435 \u0441\u0435\u0439\u0447\u0430\u0441",
  "\u043f\u043e\u043a\u0430 \u043d\u0435\u0442",
  "\u0443\u0442\u043e\u0447\u043d\u0438\u0442\u044c",
  "\u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c",
  "\u043f\u043e\u043c\u0435\u043d\u044f\u0442\u044c",
]);

const SEARCH_RUN_AMBIGUOUS_REPLIES = new Set([
  "maybe",
  "later",
  "not sure",
  "\u043d\u0435 \u0437\u043d\u0430\u044e",
  "\u043f\u043e\u0437\u0436\u0435",
  "\u043c\u043e\u0436\u0435\u0442",
]);

function isSearchRunConfirmation(text) {
  const normalizedText = normalizeChatCommandText(text);
  if (SEARCH_RUN_CONFIRMATIONS.has(normalizedText)) {
    return true;
  }

  const hasEnglishConfirmIntent =
    /\b(yes|yep|yeah|ok|okay|sure|go ahead|proceed)\b/.test(normalizedText) &&
    /\b(start|run|search|go ahead|proceed)\b/.test(normalizedText);
  const hasRussianConfirmIntent =
    /(да|ок|окей|давай|вперед|запускай|старт|начинай)/.test(normalizedText) &&
    /(запускай|вперед|старт|начинай|поиск|давай)/.test(normalizedText);
  return hasEnglishConfirmIntent || hasRussianConfirmIntent;
}

function isSearchRunRefinementRequest(text) {
  return SEARCH_RUN_REFINEMENTS.has(normalizeChatCommandText(text));
}

function isGenericSearchRunRefinementRequest(text) {
  const normalizedText = normalizeChatCommandText(text);
  return (
    /\b(update|change|edit|modify|adjust)\b/.test(normalizedText) &&
    !/\b(spring|kafka|aws|hibernate|java|ukraine|backend)\b/.test(normalizedText)
  );
}

function isRestartSearchSetupRequest(text) {
  const normalizedText = normalizeChatCommandText(text);
  if (
    [
      "start over",
      "start again",
      "restart",
      "reset",
      "new search",
      "start new search",
      "clear brief",
      "\u043d\u0430\u0447\u0430\u0442\u044c \u0437\u0430\u043d\u043e\u0432\u043e",
      "\u0441\u0431\u0440\u043e\u0441",
      "\u043d\u043e\u0432\u044b\u0439 \u043f\u043e\u0438\u0441\u043a",
    ].includes(normalizedText)
  ) {
    return true;
  }

  return /\b(start|begin|try|do)\s+(again|over|from scratch)\b/.test(normalizedText);
}

function isSearchRunAmbiguousReply(text) {
  return SEARCH_RUN_AMBIGUOUS_REPLIES.has(normalizeChatCommandText(text));
}

function chatMessageResponseLanguage(text) {
  if (/[\u0400-\u04FF]/.test(text || "")) {
    return "ru";
  }
  if (/[A-Za-z]/.test(text || "")) {
    return "en";
  }
  return currentChatLanguage;
}

const SEARCH_SUMMARY_UPDATE_FIELD_LABELS = {
  role_family: "role",
  technology: "technology",
  stack: "stack",
  location: "location",
  seniority: "seniority",
  search_depth: "search depth",
  profile_sources: "profile sources",
};

function pendingUpdateFieldQuestion(field, language = currentChatLanguage) {
  if (field === "location") {
    return language === "ru"
      ? "\u041a\u0430\u043a\u0443\u044e \u043b\u043e\u043a\u0430\u0446\u0438\u044e \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c?"
      : "What location should I use?";
  }
  if (field === "stack") {
    return language === "ru"
      ? "\u041a\u0430\u043a\u0438\u0435 1-3 stack signals \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c?"
      : "Which 1-3 stack signals should I use?";
  }
  if (field === "technology") {
    return language === "ru"
      ? "\u041a\u0430\u043a\u0443\u044e \u043e\u0441\u043d\u043e\u0432\u043d\u0443\u044e \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044e \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c? \u0412 \u0442\u0435\u043a\u0443\u0449\u0435\u043c flow \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044f Java."
      : "What main technology should I use? The current flow supports Java.";
  }
  if (field === "role_family") {
    return language === "ru"
      ? "\u041a\u0430\u043a\u0443\u044e \u0446\u0435\u043b\u0435\u0432\u0443\u044e \u0440\u043e\u043b\u044c \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c?"
      : "What target role should I use?";
  }
  return language === "ru"
    ? "\u041a\u0430\u043a\u043e\u0435 \u043f\u043e\u043b\u0435 \u0432 search summary \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c?"
    : "Which search summary field should I update?";
}

function fallbackPendingSearchSummaryUpdateIntent(text) {
  const normalizedText = normalizeChatCommandText(text);
  const responseLanguage = chatMessageResponseLanguage(text);
  if (isRestartSearchSetupRequest(text)) {
    return { intent: "restart", field: null, responseLanguage };
  }
  if (["cancel", "stop", "nevermind", "never mind", "\u043e\u0442\u043c\u0435\u043d\u0430", "\u0441\u0442\u043e\u043f"].includes(normalizedText)) {
    return { intent: "cancel", field: null, responseLanguage };
  }

  const fieldPatterns = [
    ["role_family", /\b(role|role family|position)\b/],
    ["technology", /\b(technology|main technology|language)\b/],
    ["stack", /\b(stack|spring|kafka|aws|hibernate|docker|kubernetes)\b/],
    ["location", /\b(location|country|city|place)\b/],
    ["seniority", /\b(seniority|level|senior|middle|junior|lead)\b/],
    ["search_depth", /\b(depth|search depth|deep|standard)\b/],
  ];
  for (const [field, pattern] of fieldPatterns) {
    if (pattern.test(normalizedText)) {
      return { intent: "select_field", field, responseLanguage };
    }
  }

  if (pendingChatAction?.type === "update_search_summary_field") {
    return {
      intent: "provide_value",
      field: pendingChatAction.field,
      responseLanguage,
    };
  }

  return { intent: "unclear", field: null, responseLanguage };
}

async function classifyPendingSearchSummaryUpdateIntent(userText) {
  if (!pendingSearchSummaryUpdateIsCurrent()) {
    return {
      intent: "unclear",
      field: null,
      responseLanguage: chatMessageResponseLanguage(userText),
    };
  }

  const isFieldValue = pendingChatAction.type === "update_search_summary_field";
  try {
    const response = await fetch(RECRUITER_CHAT_INTENT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        latest_message: userText,
        language: currentChatLanguage,
        context_type: isFieldValue ? "pending_update_value" : "pending_update",
        pending_update_field: isFieldValue ? pendingChatAction.field : null,
        current_brief_status: chatState,
        current_brief: normalizedBrief,
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      return fallbackPendingSearchSummaryUpdateIntent(userText);
    }

    const dataIntent = String(data.intent || "unclear");
    const intent =
      dataIntent === "restart"
        ? "restart"
        : String(data.pending_update_intent || "unclear");
    if (["select_field", "provide_value", "cancel", "restart", "unclear"].includes(intent)) {
      return {
        intent,
        field: data.field || data.answered_field || pendingChatAction.field || null,
        responseLanguage: ["en", "ru"].includes(data.response_language)
          ? data.response_language
          : chatMessageResponseLanguage(userText),
      };
    }
  } catch (_error) {
    return fallbackPendingSearchSummaryUpdateIntent(userText);
  }

  return fallbackPendingSearchSummaryUpdateIntent(userText);
}

function fallbackPendingSearchRunIntent(text) {
  const responseLanguage = chatMessageResponseLanguage(text);
  if (isRestartSearchSetupRequest(text)) {
    return { intent: "restart", reasonCode: "restart_current_search_setup", responseLanguage };
  }
  if (isSearchRunConfirmation(text)) {
    return { intent: "confirm", reasonCode: "deterministic_confirm", responseLanguage };
  }
  if (isSearchRunRefinementRequest(text)) {
    return { intent: "refine", reasonCode: "deterministic_refine", responseLanguage };
  }
  if (isGenericSearchRunRefinementRequest(text)) {
    return {
      intent: "refine",
      reasonCode: "generic_update_before_search",
      responseLanguage,
    };
  }
  if (isSearchRunAmbiguousReply(text)) {
    return { intent: "unclear", reasonCode: "deterministic_ambiguous", responseLanguage };
  }
  return { intent: "unclear", reasonCode: "deterministic_unclear", responseLanguage };
}

async function classifyPendingSearchRunIntent(userText) {
  if (!pendingChatAction || pendingChatAction.type !== "start_search") {
    return {
      intent: "unclear",
      reasonCode: "no_pending_action",
      responseLanguage: chatMessageResponseLanguage(userText),
    };
  }

  try {
    const response = await fetch(RECRUITER_CHAT_INTENT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        latest_message: userText,
        language: currentChatLanguage,
        context_type: "pending_action",
        pending_action_type: "start_search",
        current_brief_status: chatState,
      }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      return fallbackPendingSearchRunIntent(userText);
    }

    const fallback = fallbackPendingSearchRunIntent(userText);
    const dataIntent = String(data.intent || "unclear");
    const intent =
      dataIntent === "restart" ? "restart" : String(data.pending_action_intent || "unclear");
    if (intent === "unclear" && fallback.intent !== "unclear") {
      return fallback;
    }
    if (["confirm", "refine", "reject", "restart", "unclear"].includes(intent)) {
      return {
        intent,
        reasonCode: String(data.pending_action_reason_code || ""),
        responseLanguage: ["en", "ru"].includes(data.response_language)
          ? data.response_language
          : chatMessageResponseLanguage(userText),
      };
    }
  } catch (_error) {
    return fallbackPendingSearchRunIntent(userText);
  }

  return fallbackPendingSearchRunIntent(userText);
}

function readyBriefChatStatus(options = {}) {
  const includePending = options.includePending !== false;
  if (includePending && agentPlanRequestInFlight) {
    return "Search summary is ready. Preparing the next step...";
  }

  if (hasSupportedAgentAction()) {
    return "Search is understood. Confirm in chat to start it, or tell me what to change.";
  }

  if (currentAgentPlanData?.agent_plan_status === "unsupported") {
    return "This search is outside the supported Java/Ukraine flow.";
  }

  if (currentAgentPlanData) {
    return "Search needs one more clarification before it can be prepared.";
  }

  return "Search summary is ready. Preparing the next step...";
}

function isBackendSearchPlan(data = {}) {
  return (
    data.planner_mode === "rule_based" ||
    data.planner_mode === "rule_based_fallback" ||
    data.plan_status === "rule_based_fallback"
  );
}

function plannerStatusLabel(status, mode) {
  if (
    status === "validated_not_executable" &&
    isBackendSearchPlan({ planner_mode: mode, plan_status: status })
  ) {
    return "Ready to run";
  }

  if (status === "validated_not_executable" && mode === "ai") {
    return "Preview only";
  }

  return plannerLabel(status);
}

function queryPlanFromPlannerData(data = {}) {
  return data.query_plan || data.fallback_query_plan || data.draft_query_plan || null;
}

function planFingerprintFromPlannerData(data = {}, queryPlan = null) {
  return (
    data.plan_fingerprint ||
    data.fallback_plan_fingerprint ||
    queryPlan?.plan_fingerprint ||
    null
  );
}

function isExecutablePlannerData(data = {}) {
  const queryPlan = queryPlanFromPlannerData(data);
  const fingerprint = planFingerprintFromPlannerData(data, queryPlan);
  const mode = data.planner_mode;
  const status = data.plan_status;

  return Boolean(
    data.ok &&
      data.adapted_structured_request &&
      queryPlan?.queries?.length &&
      fingerprint &&
      (mode === "rule_based" ||
        mode === "rule_based_fallback" ||
        status === "rule_based_fallback")
  );
}

function rememberPlannerData(data = {}) {
  clearPendingChatAction();
  latestPlannerData = data;
  latestQueryPlan = queryPlanFromPlannerData(data);
  latestPlanFingerprint = planFingerprintFromPlannerData(data, latestQueryPlan);
  adaptedStructuredRequest = data.adapted_structured_request || null;
  latestExecutablePlan = isExecutablePlannerData(data);
  clearRuntimeApproval();
  if (latestQueryPlan?.queries?.length) {
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_BUILD_PLAN,
      "completed",
      latestExecutablePlan
        ? "Search is ready to run."
        : "Search preview is visible."
    );
  }
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  syncExecutionControlsFromPlan();
  updateActionState();
}

function clearPlannerData() {
  clearPendingChatAction();
  latestPlannerData = null;
  latestQueryPlan = null;
  latestPlanFingerprint = null;
  adaptedStructuredRequest = null;
  latestExecutablePlan = false;
  clearRuntimeApproval();
  updateActionState();
}

function clearAgentPlanData() {
  clearPendingChatAction();
  currentAgentPlanData = null;
  currentAgentPlan = null;
  currentAgentAction = null;
  messages = messages.filter((message) => message.kind !== "agent_plan");
}

function clearSearchResultsData() {
  clearPendingChatAction();
  latestAgentResponse = null;
  messages = messages.filter((message) => message.kind !== "agent_response");
  clearWorkspaceState();
  reportStatus.textContent = "Run a search to see the summary.";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
  resultsStatus.textContent = "Run a search to see candidates.";
  resultsList.innerHTML = "";
}

function clearDownstreamStateAfterBriefChange() {
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  clearSearchResultsData();
  planStatus.textContent = "Prepare search from the updated chat summary.";
  queryList.innerHTML = "";
}

function clearSearchSetupStateAfterRestart() {
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  clearRuntimeApproval();
  planStatus.textContent = "Prepare search from the chat summary.";
  queryList.innerHTML = "";
}

function clearExecutableStateAfterRefusal() {
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  clearSearchResultsData();
  planStatus.textContent = "Prepare search from the current summary.";
  queryList.innerHTML = "";
}

function chatMessagesForBackend() {
  return messages
    .filter((message) => !message.localOnly)
    .map((message) => ({
      role: message.role,
      content: message.content,
    }));
}

function appendOutgoingUserMessage(userText, options = {}) {
  const message = {
    role: "user",
    content: userText,
  };
  if (options.localOnly) {
    message.localOnly = true;
  }
  messages.push(message);
  renderChatMessages();
  return message;
}

function markChatMessageForBackend(message) {
  if (message) {
    delete message.localOnly;
  }
}

function appendAssistantThinkingMessage(language = currentChatLanguage) {
  chatTransientMessageCounter += 1;
  const transientId = `thinking-${chatTransientMessageCounter}`;
  messages.push({
    role: "assistant",
    content: language === "ru" ? "Думаю..." : "Thinking...",
    localOnly: true,
    transient: true,
    transientId,
  });
  renderChatMessages();
  return transientId;
}

function clearAssistantThinkingMessage(transientId = null) {
  const previousLength = messages.length;
  messages = messages.filter(
    (message) =>
      !message.transient ||
      (transientId && message.transientId !== transientId)
  );
  if (messages.length !== previousLength) {
    renderChatMessages();
  }
}

function pendingChatActionUsesLocalOnlyHistory() {
  return Boolean(
    pendingChatAction &&
      ["start_search", "update_search_summary", "update_search_summary_field"].includes(
        pendingChatAction.type
      )
  );
}

function typedChatMessage(baseMessage, metadata = {}) {
  const message = {
    ...baseMessage,
  };

  if (metadata.messageType && AGENT_MESSAGE_TYPE_META[metadata.messageType]) {
    message.messageType = metadata.messageType;
  }

  if (metadata.surface) {
    message.surface = metadata.surface;
  }

  if (metadata.payload) {
    message.payload = metadata.payload;
  }

  return message;
}

function agentPlanMessageType(agentPlanStatus) {
  if (agentPlanStatus === "supported") {
    return AGENT_MESSAGE_TYPES.AGENT_PLAN;
  }

  if (agentPlanStatus === "unsupported") {
    return AGENT_MESSAGE_TYPES.AGENT_PLAN_UNSUPPORTED;
  }

  return AGENT_MESSAGE_TYPES.PLANNING_NEEDS_CLARIFICATION;
}

function recruiterChatErrors(data = {}) {
  return arrayValue(data.validation_errors);
}

function hasToolUnavailableError(errors = []) {
  return errors.some((error) => {
    const safeError = error || {};
    const field = String(safeError.field || "").toLowerCase();
    if (RECRUITER_CHAT_TOOL_UNAVAILABLE_FIELDS.has(field)) {
      return true;
    }

    return [
      safeError.code,
      safeError.classification,
      safeError.type,
      safeError.category,
    ].some((value) => String(value || "").toLowerCase() === AGENT_MESSAGE_TYPES.TOOL_UNAVAILABLE);
  });
}

function recruiterChatMessageType(data = {}) {
  const errors = recruiterChatErrors(data);
  const hasBriefPatch = Boolean(data.brief_patch);

  if (data.state === "refused") {
    return AGENT_MESSAGE_TYPES.SAFETY_REFUSAL;
  }

  if (hasToolUnavailableError(errors)) {
    return AGENT_MESSAGE_TYPES.TOOL_UNAVAILABLE;
  }

  if (hasBriefPatch && (data.brief_patch?.requires_clarification || errors.length > 0)) {
    return AGENT_MESSAGE_TYPES.BRIEF_REFINEMENT_REJECTED;
  }

  if (hasBriefPatch) {
    return AGENT_MESSAGE_TYPES.BRIEF_REFINEMENT_APPLIED;
  }

  if (
    data.state === "needs_clarification" &&
    data.next_question &&
    arrayValue(data.missing_fields).length > 0 &&
    !errors.length
  ) {
    return AGENT_MESSAGE_TYPES.CLARIFICATION_QUESTION;
  }

  if (errors.length > 0) {
    return AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK;
  }

  if (data.state === "ready_for_planning") {
    return AGENT_MESSAGE_TYPES.BRIEF_SUMMARY;
  }

  if (data.state === "needs_clarification") {
    return AGENT_MESSAGE_TYPES.ONBOARDING;
  }

  return null;
}

function syncExecutionControlsFromPlan() {
  if (!adaptedStructuredRequest) {
    profilesOnlyInput.checked = true;
    locationFilterInput.checked = true;
    profilesOnlyInput.disabled = true;
    locationFilterInput.disabled = true;
    return;
  }

  profilesOnlyInput.checked = Boolean(adaptedStructuredRequest.linkedin_profiles_only);
  locationFilterInput.checked = Boolean(adaptedStructuredRequest.location_filter_enabled);
  profilesOnlyInput.disabled = true;
  locationFilterInput.disabled = true;
}

function buildRuntimeToolInput() {
  if (!adaptedStructuredRequest) {
    throw new Error("Prepare the search before running it.");
  }

  const toolInput = {
    role_family: adaptedStructuredRequest.role_family,
    technology: adaptedStructuredRequest.technology,
    stack: adaptedStructuredRequest.stack || [],
    location: adaptedStructuredRequest.location,
    search_depth: adaptedStructuredRequest.search_depth,
    linkedin_profiles_only: adaptedStructuredRequest.linkedin_profiles_only,
    location_filter_enabled: adaptedStructuredRequest.location_filter_enabled,
  };

  if (!multiWaveInput.checked) {
    return toolInput;
  }

  return {
    ...toolInput,
    ...MULTI_WAVE_DEFAULTS,
  };
}

function buildRuntimeContext() {
  if (!latestPlanFingerprint || !latestQueryPlan?.queries?.length) {
    throw new Error("Current search details are missing.");
  }
  if (!currentAgentPlan?.brief_fingerprint) {
    throw new Error("Current search summary is missing.");
  }

  const context = {
    planner_mode: PRIMARY_BUILD_PLAN_MODE,
    tool_name: currentRunSearchAction(),
    execution_mode: currentRunSearchExecutionMode(),
    plan_fingerprint: latestPlanFingerprint,
    query_count: latestQueryPlan.queries.length,
    search_brief_fingerprint: currentAgentPlan.brief_fingerprint,
    multi_wave_enabled: multiWaveInput.checked,
  };

  if (!multiWaveInput.checked) {
    return context;
  }

  return {
    ...context,
    ...MULTI_WAVE_DEFAULTS,
  };
}

function buildApprovedRuntimeApproval() {
  if (!currentRuntimePendingApproval) {
    throw new Error("Search is not ready to run yet.");
  }

  return {
    approval_status: "approved",
    tool_call_id: currentRuntimePendingApproval.tool_call_id,
    tool_name: currentRuntimePendingApproval.tool_name,
    tool_input_fingerprint: currentRuntimePendingApproval.tool_input_fingerprint,
    context_fingerprint: currentRuntimePendingApproval.context_fingerprint,
    idempotency_key: currentRuntimePendingApproval.idempotency_key,
  };
}

function plainChatSpeaker(message = {}) {
  if (message.kind?.startsWith("agent_")) {
    return ASSISTANT_SPEAKER_LABEL;
  }

  return message.role === "user" ? "You" : ASSISTANT_SPEAKER_LABEL;
}

function chatRoleClass(message = {}) {
  const roleClass = message.role === "user" ? "user-message" : "assistant-message";
  return message.transient ? `${roleClass} assistant-thinking-message` : roleClass;
}

function renderPlainChatMessage(message = {}) {
  return `
    <article class="chat-message ${chatRoleClass(message)}">
      <span>${escapeHtml(plainChatSpeaker(message))}</span>
      <p>${escapeHtml(message.content)}</p>
    </article>
  `;
}

function renderTypedChatMessage(message = {}) {
  const meta = AGENT_MESSAGE_TYPE_META[message.messageType];
  if (!meta) {
    return renderPlainChatMessage(message);
  }

  return `
    <article
      class="chat-message ${chatRoleClass(message)} typed-message ${meta.className}"
      data-message-type="${escapeHtml(message.messageType || "")}"
      data-message-type-label="${escapeHtml(meta.label)}"
    >
      <span aria-label="${escapeHtml(`${ASSISTANT_SPEAKER_LABEL}: ${meta.label}`)}">${escapeHtml(ASSISTANT_SPEAKER_LABEL)}</span>
      <p>${escapeHtml(message.content)}</p>
    </article>
  `;
}

function renderChatMessages() {
  if (!messages.length) {
    chatMessagesElement.innerHTML = `
      <article class="chat-message assistant-message chat-empty-message">
        <p>Feel free to start the chat and describe who you are looking for. I will do my best to help you.</p>
      </article>
    `;
    return;
  }

  chatMessagesElement.innerHTML = messages
    .map((message) =>
      message.messageType ? renderTypedChatMessage(message) : renderPlainChatMessage(message)
    )
    .join("");
  chatMessagesElement.scrollTop = chatMessagesElement.scrollHeight;
}

function renderBriefSummaryCard(brief = normalizedBrief, state = chatState) {
  if (!brief || !Object.keys(brief).length) {
    briefSummaryPanel.hidden = true;
    briefSummaryPanel.innerHTML = "";
    return "";
  }

  const fields = [
    ["Role", brief.role_family],
    ["Technology", brief.technology],
    ["Stack", displayList(brief.stack || [])],
    ["Location", brief.location],
    ["Depth", brief.search_depth],
    ["Seniority", brief.seniority || "n/a"],
  ];

  const markup = `
    <details class="planner-section collapsible-section brief-collapsible">
      <summary class="collapsible-summary brief-heading">
        <h3>Search summary</h3>
        <span>${escapeHtml(plannerLabel(state))}</span>
        <span class="collapse-indicator" aria-hidden="true"></span>
      </summary>
      <div class="collapsible-content">
        <div class="brief-grid">
          ${fields
            .map(
              ([label, value]) => `
                <div>
                  <span>${escapeHtml(label)}</span>
                  <strong>${escapeHtml(displayValue(value))}</strong>
                </div>
              `
            )
            .join("")}
        </div>
        ${
          brief.assumptions?.length
            ? `<p class="planner-note">Assumptions: ${escapeHtml(brief.assumptions.join(", "))}</p>`
            : ""
        }
        ${
          brief.missing_fields?.length
            ? `<p class="planner-note">Missing: ${escapeHtml(brief.missing_fields.join(", "))}</p>`
            : ""
        }
      </div>
    </details>
  `;

  briefSummaryPanel.hidden = false;
  briefSummaryPanel.innerHTML = markup;
  return markup;
}

function renderBriefSummary(brief = {}) {
  return renderBriefSummaryCard(brief, brief.brief_status || chatState);
}

function queryCountForCurrentPlan() {
  return latestQueryPlan?.queries?.length || 0;
}

function buildSearchPlanQueueItem() {
  const hasRelevantState = Boolean(
    normalizedBrief ||
      currentAgentPlanData ||
      currentAgentPlan ||
      agentPlanRequestInFlight ||
      planRequestInFlight ||
      latestQueryPlan
  );
  if (!hasRelevantState) {
    return null;
  }

  const displayState = agentActionDisplayState[AGENT_QUEUE_ACTION_BUILD_PLAN];
  let status = "blocked";
  let detail = "Complete a supported search summary before preparing search.";

  if (planRequestInFlight) {
    status = "running";
    detail = "Preparing search details.";
  } else if (displayState?.status === "failed" && !latestQueryPlan) {
    status = "failed";
    detail = displayState.detail || "Prepare search failed.";
  } else if (latestQueryPlan?.queries?.length) {
    status = "completed";
    detail = latestExecutablePlan
      ? "Search is ready to run."
      : "Search preview is visible.";
  } else if (hasSupportedAgentAction()) {
    status = "ready";
    detail = "Search summary is ready.";
  } else if (agentPlanRequestInFlight) {
    detail = "Preparing search summary.";
  } else if (currentAgentPlanData?.agent_plan_status === "unsupported") {
    detail = "This search is outside the supported Java/Ukraine flow.";
  } else if (chatState === "ready_for_planning" && normalizedBrief) {
    detail = "Waiting until the search can be prepared.";
  }

  return {
    id: AGENT_QUEUE_ACTION_BUILD_PLAN,
    title: "Prepare search",
    action: "Prepare search",
    requiresApproval: false,
    status,
    detail,
    context: [
      ["Source", "Current search summary"],
      ["Status", currentAgentPlan?.brief_fingerprint ? "Current" : "Not ready"],
    ],
  };
}

function runSearchQueueItem() {
  const hasVisiblePlan = Boolean(latestQueryPlan?.queries?.length);
  const displayState = agentActionDisplayState[AGENT_QUEUE_ACTION_RUN_SEARCH];
  if (!hasVisiblePlan && !searchRequestInFlight && !displayState) {
    return null;
  }

  let status = "blocked";
  let detail = "Prepare a runnable search before continuing.";

  if (searchRequestInFlight) {
    status = "running";
    detail = `Running ${currentRunSearchModeLabel()} search.`;
  } else if (runtimePrepareRequestInFlight) {
    status = "running";
    detail = "Checking that the search is ready to run.";
  } else if (displayState?.status === "failed") {
    status = "failed";
    detail = displayState.detail || "Search failed.";
  } else if (displayState?.status === "completed" && latestExecutablePlan) {
    status = "completed";
    detail = "Search completed and results are visible.";
  } else if (latestExecutablePlan && latestPlanFingerprint && currentRuntimePendingApproval) {
    status = "ready_for_approval";
    detail = "Search is ready to run.";
  } else if (latestExecutablePlan && latestPlanFingerprint) {
    detail = "Checking that the search is ready to run.";
  } else if (hasVisiblePlan) {
    detail = "This search preview cannot run yet.";
  }

  return {
    id: AGENT_QUEUE_ACTION_RUN_SEARCH,
    title: "Run search",
    action: "Run search",
    requiresApproval: true,
    status,
    detail,
    context: [
      ["Source", "Prepared search"],
      ["Mode", currentRunSearchModeLabel()],
      ["Queries", queryCountForCurrentPlan() || "not ready"],
      ["Status", currentRuntimePendingApproval ? "Ready" : "Not ready"],
    ],
  };
}

function agentActionQueueItems() {
  return [buildSearchPlanQueueItem(), runSearchQueueItem()].filter(Boolean);
}

function renderAgentActionContext(context = []) {
  return context
    .map(
      ([label, value]) => `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(displayValue(value))}</strong>
        </div>
      `
    )
    .join("");
}

function renderAgentActionQueue() {
  if (!agentActionQueueElement) {
    return;
  }

  const items = agentActionQueueItems();
  const header = `
    <summary class="collapsible-summary agent-action-header">
      <h3>Search steps</h3>
      <span>${escapeHtml(items.length ? `${items.length} active` : "idle")}</span>
      <span class="collapse-indicator" aria-hidden="true"></span>
    </summary>
  `;

  if (!items.length) {
    agentActionQueueElement.innerHTML = `
      <details class="collapsible-section agent-action-collapsible">
        ${header}
        <div class="collapsible-content">
          <p class="agent-action-empty">No search step is ready yet.</p>
        </div>
      </details>
    `;
    return;
  }

  agentActionQueueElement.innerHTML = `
    <details class="collapsible-section agent-action-collapsible">
      ${header}
      <div class="collapsible-content">
        <div class="agent-action-list">
          ${items
            .map((item) => {
              const statusClass = `status-${item.status.replaceAll("_", "-")}`;
              return `
                <article class="agent-action-item">
                  <div class="agent-action-title">
                    <strong>${escapeHtml(item.title)}</strong>
                    <span class="agent-action-status ${escapeHtml(statusClass)}">${escapeHtml(
                      actionStatusLabel(item.status)
                    )}</span>
                  </div>
                  <p class="agent-action-detail">${escapeHtml(item.detail)}</p>
                  <div class="agent-action-context">
                    <div>
                      <span>Step</span>
                      <strong>${escapeHtml(item.action)}</strong>
                    </div>
                    <div>
                      <span>Confirmation</span>
                      <strong>${item.requiresApproval ? "Required" : "Not required"}</strong>
                    </div>
                    ${renderAgentActionContext(item.context)}
                  </div>
                </article>
              `;
            })
            .join("")}
        </div>
      </div>
    </details>
  `;
}

function renderValidationErrors(errors = []) {
  if (!errors.length) {
    return "";
  }

  return `
    <div class="planner-section planner-errors">
      <h3>Validation</h3>
      ${errors
        .map(
          (error) => `
            <p>
              <strong>${escapeHtml(error.code || error.field || "error")}</strong>
              ${escapeHtml(error.field ? `${error.field}: ` : "")}${escapeHtml(error.message || "")}
            </p>
          `
        )
        .join("")}
    </div>
  `;
}

function renderPlannerDetails(data = {}) {
  const warnings = data.warnings || [];
  const assumptions = data.assumptions || [];
  const mode = data.planner_mode || recommendedPlannerMode;
  const status = data.plan_status || "draft_query_plan";

  return `
    <div class="planner-meta">
      <div class="planner-badges">
        <span>${escapeHtml(plannerLabel(mode))}</span>
        <span>${escapeHtml(plannerStatusLabel(status, mode))}</span>
      </div>
      ${renderBriefSummary(data.normalized_brief)}
      ${
        data.explanation || data.fallback_reason || warnings.length || assumptions.length
          ? `
            <div class="planner-section">
              <h3>Search detail notes</h3>
              ${data.explanation ? `<p>${escapeHtml(data.explanation)}</p>` : ""}
              ${data.fallback_reason ? `<p>${escapeHtml(data.fallback_reason)}</p>` : ""}
              ${warnings.length ? `<p>Warnings: ${escapeHtml(warnings.join(", "))}</p>` : ""}
              ${assumptions.length ? `<p>Assumptions: ${escapeHtml(assumptions.join(", "))}</p>` : ""}
            </div>
          `
          : ""
      }
      ${renderValidationErrors(data.validation_errors || data.errors || [])}
      ${
        data.approval_notice || data.approval_required
          ? `<p class="planner-notice">${escapeHtml(
              data.approval_notice || "Search is not running yet. Use Run search when you are ready."
            )}</p>`
          : ""
      }
    </div>
  `;
}

function renderPlanErrors(errors = []) {
  clearPlannerData();
  setAgentActionDisplayState(
    AGENT_QUEUE_ACTION_BUILD_PLAN,
    "failed",
    validationMessage(errors) || "Prepare search failed."
  );
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  planStatus.textContent = validationMessage(errors);
  queryList.innerHTML = renderValidationErrors(errors);
  updateActionState();
}

function renderSearchErrors(errors = []) {
  const message = validationMessage(errors);
  clearRuntimeApproval();
  setAgentActionDisplayState(
    AGENT_QUEUE_ACTION_RUN_SEARCH,
    "failed",
    message || "Search failed."
  );
  resultsStatus.textContent = message;
  reportStatus.textContent = message;
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
  updateActionState();
}

async function prepareRuntimeSearchAction() {
  if (!latestExecutablePlan || !adaptedStructuredRequest) {
    clearRuntimeApproval();
    updateActionState();
    return null;
  }
  if (
    chatRequestInFlight ||
    agentPlanRequestInFlight ||
    planRequestInFlight ||
    searchRequestInFlight
  ) {
    return null;
  }

  const requestVersion = interactionVersion;
  let payload;
  try {
    payload = {
      turn_mode: AGENT_RUNTIME_TURN_MODE_PREPARE,
      tool_name: currentRunSearchAction(),
      tool_input: buildRuntimeToolInput(),
      runtime_context: buildRuntimeContext(),
      runtime_approval: null,
      agent_language: currentChatLanguage,
    };
  } catch (error) {
    clearRuntimeApproval();
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_RUN_SEARCH,
      "failed",
      error.message || "Search readiness check failed."
    );
    updateActionState();
    return null;
  }

  clearRuntimeApproval();
  const runtimeRequestVersion = runtimeApprovalVersion;
  runtimePrepareRequestInFlight = true;
  setAgentActionDisplayState(
    AGENT_QUEUE_ACTION_RUN_SEARCH,
    "running",
    "Checking that the search is ready to run."
  );
  updateActionState();

  try {
    const response = await fetch(AGENT_RUNTIME_TURN_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (
      requestVersion !== interactionVersion ||
      runtimeRequestVersion !== runtimeApprovalVersion
    ) {
      return null;
    }

    if (!response.ok) {
      throw new Error(data.detail || "Search readiness check failed.");
    }

    if (data.errors?.length) {
      renderSearchErrors(data.errors);
      return null;
    }

    const pendingApproval = data.pending_approvals?.[0] || null;
    const toolCall = data.tool_calls?.[0] || null;
    if (!pendingApproval || !toolCall) {
      throw new Error("Search readiness response did not include a runnable action.");
    }

    currentRuntimePendingApproval = pendingApproval;
    currentRuntimeToolCall = toolCall;
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_RUN_SEARCH,
      "ready_for_approval",
      "Search is ready to run."
    );
    resultsStatus.textContent = "Search is ready to run.";
    return data;
  } catch (error) {
    if (
      requestVersion !== interactionVersion ||
      runtimeRequestVersion !== runtimeApprovalVersion
    ) {
      return null;
    }

    clearRuntimeApproval();
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_RUN_SEARCH,
      "failed",
      error.message || "Search readiness check failed."
    );
    resultsStatus.textContent = error.message;
    return null;
  } finally {
    if (
      requestVersion === interactionVersion &&
      runtimeRequestVersion === runtimeApprovalVersion
    ) {
      runtimePrepareRequestInFlight = false;
      updateActionState();
    }
  }
}

function renderQueryPlan(queryPlan, plannerData = null) {
  const queries = queryPlan.queries || [];
  const queryCountText = `${queries.length} ${pluralize(queries.length, "query", "queries")}`;

  if (plannerData && isBackendSearchPlan(plannerData)) {
    planStatus.textContent = `Search details are ready: ${queryCountText} prepared.`;
  } else {
    const modeText = plannerData?.planner_mode
      ? `${plannerLabel(plannerData.planner_mode)}: `
      : "";
    planStatus.textContent = `${modeText}${queryCountText} prepared.`;
  }

  const queryMarkup = queries
    .map((querySlot) => {
      const stack = querySlot.uses_stack?.length
        ? querySlot.uses_stack.join(", ")
        : "none";
      const rolePhrase = querySlot.role_phrase
        ? `<p class="query-stack">Role phrase: ${escapeHtml(querySlot.role_phrase)}</p>`
        : "";

      return `
        <article class="query-item">
          <div class="query-heading">
            <strong>${escapeHtml(querySlot.id)}</strong>
            <span>${escapeHtml(querySlot.category)}</span>
          </div>
          <p>${escapeHtml(querySlot.purpose)}</p>
          <code>${escapeHtml(querySlot.query)}</code>
          ${rolePhrase}
          <p class="query-stack">Stack: ${escapeHtml(stack)}</p>
        </article>
      `;
    })
    .join("");

  queryList.innerHTML = `${plannerData ? renderPlannerDetails(plannerData) : ""}${queryMarkup}`;
}

function renderAgentQueryPlan(data) {
  rememberPlannerData(data);
  const queryPlan = queryPlanFromPlannerData(data);

  if (!queryPlan) {
    planStatus.textContent = plannerLabel(data.plan_status || "rejected");
    queryList.innerHTML = renderPlannerDetails(data);
    resultsStatus.textContent = "Prepare a valid search before running it.";
    return;
  }

  renderQueryPlan(queryPlan, data);

  if (latestExecutablePlan) {
    resultsStatus.textContent =
      "Search is ready to run. Review the details first.";
    return;
  }

  resultsStatus.textContent =
    "Search preview cannot run yet. Prepare a runnable search first.";
}

function rememberAgentPlanData(data = {}) {
  currentAgentPlanData = data;
  currentAgentPlan = data.agent_plan || null;
  currentAgentAction = currentAgentPlan?.proposed_action || null;
  if (hasSupportedAgentAction()) {
    setPendingSearchRunChatAction();
  } else {
    clearPendingChatAction();
  }
}

function appendAgentPlanMessage(data = {}) {
  const content =
    data.agent_plan?.message ||
    data.message ||
    "Search is not ready for this summary.";

  messages = messages.filter((message) => message.kind !== "agent_plan");
  messages.push(
    typedChatMessage(
      {
        role: "assistant",
        content,
        kind: "agent_plan",
        localOnly: true,
      },
      {
        messageType: agentPlanMessageType(data.agent_plan_status),
        surface: "chat",
      }
    )
  );
}

function appendAgentResponseMessage(agentResponse = null) {
  const response = agentResponse || {};
  const content = response.message || "";
  if (!content) {
    return;
  }

  latestAgentResponse = response;
  messages.push(
    typedChatMessage(
      {
        role: "assistant",
        content,
        kind: "agent_response",
        localOnly: true,
      },
      {
        messageType: AGENT_MESSAGE_TYPES.AGENT_RESPONSE,
        surface: "chat",
        payload: {
          language: response.language || currentChatLanguage,
        },
      }
    )
  );
  renderChatMessages();
}

async function fetchAgentPlanForCurrentBrief() {
  if (!normalizedBrief || chatState !== "ready_for_planning") {
    return null;
  }

  const requestVersion = interactionVersion;
  agentPlanRequestInFlight = true;
  updateActionState();
  chatStatusElement.textContent = "Preparing search summary...";

  try {
    const response = await fetch(AGENT_PLAN_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        search_brief: normalizedBrief,
        language: currentChatLanguage,
      }),
    });
    const data = await response.json();

    if (requestVersion !== interactionVersion) {
      return null;
    }

    if (!response.ok) {
      throw new Error(data.detail || "Search summary request failed.");
    }

    rememberAgentPlanData(data);
    appendAgentPlanMessage(data);
    renderChatMessages();

    chatStatusElement.textContent = readyBriefChatStatus({ includePending: false });

    return data;
  } catch (error) {
    if (requestVersion !== interactionVersion) {
      return null;
    }

    clearAgentPlanData();
    messages.push(
      typedChatMessage(
        {
          role: "assistant",
          content: error.message,
          kind: "agent_plan",
          localOnly: true,
        },
        {
          messageType: AGENT_MESSAGE_TYPES.SYSTEM_ERROR,
          surface: "chat",
        }
      )
    );
    renderChatMessages();
    chatStatusElement.textContent = error.message;
    return null;
  } finally {
    if (requestVersion === interactionVersion) {
      agentPlanRequestInFlight = false;
      updateActionState();
    }
  }
}

async function fetchAgentQueryPlan() {
  if (!hasSupportedAgentAction()) {
    throw new Error("Prepare search requires a supported current action.");
  }

  const response = await fetch(currentAgentAction.endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      planner_mode: plannerModeForBuildPlan(),
      search_brief: normalizedBrief,
      agent_plan_brief_fingerprint: currentAgentPlan.brief_fingerprint,
      agent_plan_action: currentAgentAction,
    }),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Prepare search request failed.");
  }

  return data;
}

async function buildPlanFromChat(options = {}) {
  const autoPrepareRuntime = options?.autoPrepareRuntime !== false;
  if (!normalizedBrief || chatState !== "ready_for_planning") {
    planStatus.textContent = "Complete the search summary in chat before preparing search.";
    return null;
  }

  const requestVersion = interactionVersion;
  planRequestInFlight = true;
  setAgentActionDisplayState(
    AGENT_QUEUE_ACTION_BUILD_PLAN,
    "running",
    "Preparing search details."
  );
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  updateActionState();
  planStatus.textContent = "Preparing search...";
  queryList.innerHTML = "";
  clearPlannerData();

  try {
    const data = await fetchAgentQueryPlan();
    if (requestVersion !== interactionVersion) {
      return null;
    }

    if (!data.ok) {
      renderPlanErrors(data.errors || data.validation_errors || []);
      return null;
    }

    renderAgentQueryPlan(data);
    return data;
  } catch (error) {
    if (requestVersion !== interactionVersion) {
      return null;
    }

    clearPlannerData();
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_BUILD_PLAN,
      "failed",
      error.message || "Prepare search failed."
    );
    clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
    planStatus.textContent = error.message;
    queryList.innerHTML = "";
    return null;
  } finally {
    if (requestVersion === interactionVersion) {
      planRequestInFlight = false;
      updateActionState();
      if (latestExecutablePlan && autoPrepareRuntime) {
        void prepareRuntimeSearchAction();
      }
    }
  }
}

function updateActionState() {
  const isBusy =
    chatRequestInFlight ||
    agentPlanRequestInFlight ||
    planRequestInFlight ||
    runtimePrepareRequestInFlight ||
    searchRequestInFlight ||
    searchConfirmationInFlight;
  const canBuildPlan =
    chatState === "ready_for_planning" &&
    Boolean(normalizedBrief) &&
    hasSupportedAgentAction() &&
    !isBusy;
  buildPlanButton.disabled = !canBuildPlan;
  searchButton.disabled = !latestExecutablePlan || !currentRuntimePendingApproval || isBusy;
  sendChatButton.disabled = isBusy;
  chatInput.disabled = isBusy;
  multiWaveInput.disabled = isBusy;
  renderAgentActionQueue();
}

function updateChatStateFromResponse(data = {}) {
  chatState = data.state || "needs_clarification";
  currentChatLanguage = data.language || currentChatLanguage;
  recommendedPlannerMode = data.recommended_planner_mode || PRIMARY_BUILD_PLAN_MODE;
  const responseBrief = data.normalized_brief || null;

  if (data.clear_brief) {
    draftBrief = null;
    normalizedBrief = null;
    clearSearchSetupStateAfterRestart();
  } else if (responseBrief) {
    draftBrief = responseBrief;
    normalizedBrief = responseBrief;
  } else if (chatState !== "refused") {
    normalizedBrief = null;
  }

  if (chatState === "refused") {
    clearExecutableStateAfterRefusal();
  } else if (data.stale_state_should_clear) {
    clearDownstreamStateAfterBriefChange();
  }

  const suppressRedundantUpdateBubble = Boolean(
    data.assistant_message &&
      data.brief_changed &&
      data.brief_patch &&
      chatState === "ready_for_planning"
  );

  if (data.assistant_message && !suppressRedundantUpdateBubble) {
    const messageType = recruiterChatMessageType(data);
    messages.push(
      typedChatMessage(
        {
          role: "assistant",
          content: data.assistant_message,
        },
        {
          messageType,
          surface: messageType ? "chat" : null,
        }
      )
    );
  }

  if (chatState === "ready_for_planning") {
    chatStatusElement.textContent = readyBriefChatStatus();
  } else if (chatState === "refused") {
    chatStatusElement.textContent = "I cannot help with that request, but I can help with candidate search.";
  } else {
    chatStatusElement.textContent = "Answer the clarification to complete the search summary.";
  }

  renderChatMessages();
  renderBriefSummaryCard(normalizedBrief, chatState);
  updateActionState();

  if (chatState === "ready_for_planning" && (!currentAgentPlan || data.stale_state_should_clear)) {
    fetchAgentPlanForCurrentBrief();
  }
}

function isPostResultsFollowUpMessage(text) {
  const normalizedText = String(text || "").toLowerCase();
  return Boolean(
    latestAgentResponse &&
      /what should we improve next|what.+improve next|next iteration|what next|improve the next/i.test(
        normalizedText
      )
  );
}

function handlePostResultsFollowUp(userText) {
  messages.push(
    typedChatMessage(
      {
        role: "assistant",
        content:
          "Based on the visible results, start with the strongest matches. Tell me what you want to refine before I prepare another search.",
        kind: "agent_response",
        localOnly: true,
      },
      {
        messageType: AGENT_MESSAGE_TYPES.AGENT_RESPONSE,
        surface: "chat",
        payload: {
          language: latestAgentResponse?.language || currentChatLanguage,
        },
      }
    )
  );
  chatStatusElement.textContent = "Results are visible. You can refine the search in chat.";
  renderChatMessages();
  updateActionState();
}

function appendSearchConfirmationReply(content, messageType = AGENT_MESSAGE_TYPES.BRIEF_SUMMARY) {
  messages.push(
    typedChatMessage(
      {
        role: "assistant",
        content,
        localOnly: true,
      },
      {
        messageType,
        surface: "chat",
      }
    )
  );
}

async function ensureSearchReadyForConfirmedRun() {
  if (!latestExecutablePlan) {
    await buildPlanFromChat({ autoPrepareRuntime: false });
  }

  if (!latestExecutablePlan) {
    return false;
  }

  if (!currentRuntimePendingApproval) {
    await prepareRuntimeSearchAction();
  }

  return Boolean(currentRuntimePendingApproval);
}

async function handlePendingSearchRunChatAction(userText) {
  if (!pendingChatAction || pendingChatAction.type !== "start_search") {
    return false;
  }

  const pendingIntentDecision = await classifyPendingSearchRunIntent(userText);
  const pendingIntent = pendingIntentDecision.intent || "unclear";
  const pendingReasonCode = pendingIntentDecision.reasonCode || "";
  const pendingResponseLanguage =
    pendingIntentDecision.responseLanguage || chatMessageResponseLanguage(userText);
  const cleanConfirmation = pendingIntent === "confirm";
  if (!pendingSearchRunConfirmationIsCurrent()) {
    if (cleanConfirmation && pendingChatAction?.type === "start_search") {
      clearPendingChatAction();
      appendSearchConfirmationReply(
        pendingResponseLanguage === "ru"
          ? "\u041f\u043e\u0438\u0441\u043a\u043e\u0432\u0430\u044f \u0441\u0432\u043e\u0434\u043a\u0430 \u0438\u0437\u043c\u0435\u043d\u0438\u043b\u0430\u0441\u044c. \u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438 \u0442\u0435\u043a\u0443\u0449\u0438\u0439 \u043f\u043e\u0438\u0441\u043a \u0435\u0449\u0435 \u0440\u0430\u0437."
          : "The search summary changed. Confirm the current search again before I start it.",
        AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
      );
      renderChatMessages();
      updateActionState();
      chatInput.focus();
      return true;
    }
    clearPendingChatAction();
    return false;
  }

  if (pendingIntent === "restart") {
    clearPendingChatAction();
    draftBrief = null;
    normalizedBrief = null;
    chatState = "drafting";
    clearSearchSetupStateAfterRestart();
    appendSearchConfirmationReply(
      pendingResponseLanguage === "ru"
        ? "\u041e\u043a, \u043d\u0430\u0447\u0438\u043d\u0430\u0435\u043c \u0437\u0430\u043d\u043e\u0432\u043e. \u041d\u0430\u043f\u0438\u0448\u0438, \u043a\u043e\u0433\u043e \u0438\u0449\u0435\u043c: \u0440\u043e\u043b\u044c, \u043e\u0441\u043d\u043e\u0432\u043d\u0443\u044e \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044e, \u043b\u043e\u043a\u0430\u0446\u0438\u044e \u0438 1-3 \u0441\u0438\u0433\u043d\u0430\u043b\u0430 \u0441\u0442\u0435\u043a\u0430."
        : "Ok, let's start again. Tell me who we should find: role, main technology, location, and 1-3 stack signals.",
      AGENT_MESSAGE_TYPES.ONBOARDING
    );
    chatStatusElement.textContent = "";
    renderBriefSummaryCard(null);
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (pendingIntent === "refine") {
    if (
      pendingReasonCode === "wants_to_update_before_search" ||
      pendingReasonCode === "generic_update_before_search" ||
      isGenericSearchRunRefinementRequest(userText)
    ) {
      clearPendingChatAction();
      clearRuntimeApproval();
      setPendingSearchSummaryUpdateAction();
      appendSearchConfirmationReply(
        pendingResponseLanguage === "ru"
          ? "\u041a\u043e\u043d\u0435\u0447\u043d\u043e. \u0427\u0442\u043e \u043d\u0443\u0436\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u0432 search summary?"
          : "Sure. What would you like to update in the search summary?",
        AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
      );
      renderChatMessages();
      updateActionState();
      chatInput.focus();
      return true;
    }
    clearPendingChatAction();
    clearRuntimeApproval();
    updateActionState();
    return false;
  }

  if (pendingIntent === "reject") {
    clearPendingChatAction();
    clearRuntimeApproval();
    appendSearchConfirmationReply(
      pendingResponseLanguage === "ru"
        ? "\u041e\u043a, \u043f\u043e\u0438\u0441\u043a \u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u043a\u0430\u044e. \u0421\u0432\u043e\u0434\u043a\u0430 \u043e\u0441\u0442\u0430\u0435\u0442\u0441\u044f \u0433\u043e\u0442\u043e\u0432\u043e\u0439."
        : "Ok, I will not start the search. The current summary stays ready."
    );
    chatStatusElement.textContent = readyBriefChatStatus({ includePending: false });
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (pendingIntent === "unclear") {
    appendSearchConfirmationReply(
      pendingResponseLanguage === "ru"
        ? "\u0425\u043e\u0447\u0435\u0448\u044c, \u0447\u0442\u043e\u0431\u044b \u044f \u043d\u0430\u0447\u0430\u043b \u044d\u0442\u043e\u0442 \u043f\u043e\u0438\u0441\u043a, \u0438\u043b\u0438 \u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u043d\u0443\u0436\u043d\u043e \u0447\u0442\u043e-\u0442\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c?"
        : "Do you want me to start this search, or should we change something first?",
      AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
    );
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (!cleanConfirmation) {
    return false;
  }

  clearPendingChatAction();
  appendSearchConfirmationReply(
    pendingResponseLanguage === "ru"
      ? "\u041f\u043e\u043d\u044f\u043b. \u041d\u0430\u0447\u0438\u043d\u0430\u044e \u043f\u043e\u0438\u0441\u043a \u043f\u043e \u0442\u0435\u043a\u0443\u0449\u0435\u0439 \u0441\u0432\u043e\u0434\u043a\u0435."
      : "Confirmed. Starting the search from the current summary."
  );
  renderChatMessages();
  chatStatusElement.textContent = "Starting search...";
  searchConfirmationInFlight = true;
  updateActionState();

  try {
    const readyToRun = await ensureSearchReadyForConfirmedRun();
    if (!readyToRun) {
      appendSearchConfirmationReply(
        pendingResponseLanguage === "ru"
          ? "\u041d\u0435 \u0441\u043c\u043e\u0433 \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u044c \u043f\u043e\u0438\u0441\u043a. \u041f\u0440\u043e\u0432\u0435\u0440\u044c \u0441\u0432\u043e\u0434\u043a\u0443 \u0438 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438 \u0441\u043d\u043e\u0432\u0430."
          : "I could not safely prepare this search. Review the summary and confirm again.",
        AGENT_MESSAGE_TYPES.SYSTEM_ERROR
      );
      renderChatMessages();
      return true;
    }

    await runStructuredSearch();
    return true;
  } finally {
    searchConfirmationInFlight = false;
    updateActionState();
    chatInput.focus();
  }
}

async function handlePendingSearchSummaryUpdateAction(userText) {
  if (
    !pendingChatAction ||
    !["update_search_summary", "update_search_summary_field"].includes(
      pendingChatAction.type
    )
  ) {
    return false;
  }

  if (!pendingSearchSummaryUpdateIsCurrent()) {
    clearPendingChatAction();
    appendSearchConfirmationReply(
      chatMessageResponseLanguage(userText) === "ru"
        ? "\u0422\u0435\u043a\u0443\u0449\u0430\u044f search summary \u0438\u0437\u043c\u0435\u043d\u0438\u043b\u0430\u0441\u044c. \u041d\u0430\u043f\u0438\u0448\u0438, \u0447\u0442\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c, \u0435\u0449\u0435 \u0440\u0430\u0437."
        : "The current search summary changed. Tell me what to update again.",
      AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
    );
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  const updateDecision = await classifyPendingSearchSummaryUpdateIntent(userText);
  const updateIntent = updateDecision.intent || "unclear";
  const responseLanguage =
    updateDecision.responseLanguage || chatMessageResponseLanguage(userText);

  if (updateIntent === "restart") {
    clearPendingChatAction();
    draftBrief = null;
    normalizedBrief = null;
    chatState = "drafting";
    clearSearchSetupStateAfterRestart();
    appendSearchConfirmationReply(
      responseLanguage === "ru"
        ? "\u041e\u043a, \u043d\u0430\u0447\u0438\u043d\u0430\u0435\u043c \u0437\u0430\u043d\u043e\u0432\u043e. \u041d\u0430\u043f\u0438\u0448\u0438, \u043a\u043e\u0433\u043e \u0438\u0449\u0435\u043c: \u0440\u043e\u043b\u044c, \u043e\u0441\u043d\u043e\u0432\u043d\u0443\u044e \u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044e, \u043b\u043e\u043a\u0430\u0446\u0438\u044e \u0438 1-3 \u0441\u0438\u0433\u043d\u0430\u043b\u0430 \u0441\u0442\u0435\u043a\u0430."
        : "Ok, let's start again. Tell me who we should find: role, main technology, location, and 1-3 stack signals.",
      AGENT_MESSAGE_TYPES.ONBOARDING
    );
    chatStatusElement.textContent = "";
    renderBriefSummaryCard(null);
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (updateIntent === "cancel") {
    clearPendingChatAction();
    appendSearchConfirmationReply(
      responseLanguage === "ru"
        ? "\u041e\u043a, \u043e\u0441\u0442\u0430\u0432\u043b\u044f\u044e \u0442\u0435\u043a\u0443\u0449\u0443\u044e search summary \u0431\u0435\u0437 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439."
        : "Ok, I will keep the current search summary unchanged.",
      AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
    );
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (
    pendingChatAction.type === "update_search_summary" &&
    updateIntent === "select_field" &&
    updateDecision.field
  ) {
    const selectedField = String(updateDecision.field);
    setPendingSearchSummaryUpdateFieldAction(selectedField);
    appendSearchConfirmationReply(
      pendingUpdateFieldQuestion(selectedField, responseLanguage),
      AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
    );
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (pendingChatAction.type === "update_search_summary") {
    appendSearchConfirmationReply(
      responseLanguage === "ru"
        ? "\u0427\u0442\u043e \u0438\u043c\u0435\u043d\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c: role, technology, stack, location, seniority \u0438\u043b\u0438 depth?"
        : "Which field should I update: role, technology, stack, location, seniority, or depth?",
      AGENT_MESSAGE_TYPES.VALIDATION_FEEDBACK
    );
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  return false;
}

async function handlePendingBuildPlanChatAction(userText) {
  if (!pendingBuildPlanActionIsCurrent()) {
    clearPendingChatAction();
    return false;
  }

  if (isBuildPlanDismissal(userText)) {
    messages.push({ role: "user", content: userText, localOnly: true });
    clearPendingChatAction();
    messages.push(
      typedChatMessage(
        {
          role: "assistant",
          content:
            currentChatLanguage === "ru"
              ? "Ок, поиск сейчас не готовлю. Текущая сводка остается готовой."
              : "Ok, I will not prepare the search now. The current search summary stays ready.",
          localOnly: true,
        },
        {
          messageType: AGENT_MESSAGE_TYPES.BRIEF_SUMMARY,
          surface: "chat",
        }
      )
    );
    chatStatusElement.textContent = readyBriefChatStatus({ includePending: false });
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return true;
  }

  if (!isBuildPlanConfirmation(userText)) {
    return false;
  }

  messages.push({ role: "user", content: userText, localOnly: true });
  clearPendingChatAction();
  messages.push(
    typedChatMessage(
      {
        role: "assistant",
        content:
          currentChatLanguage === "ru"
            ? "Готовлю поиск по текущей сводке. Поиск не запустится без Run search."
            : "Preparing the search from the current summary. Search will still require Run search.",
        localOnly: true,
      },
      {
        messageType: AGENT_MESSAGE_TYPES.BRIEF_SUMMARY,
        surface: "chat",
      }
    )
  );
  renderChatMessages();
  chatStatusElement.textContent = "Preparing search...";
  updateActionState();
  await buildPlanFromChat();
  chatInput.focus();
  return true;
}

async function sendChatTurn(userText) {
  const requestVersion = interactionVersion;
  const optimisticUserMessage = appendOutgoingUserMessage(userText, {
    localOnly:
      pendingChatActionUsesLocalOnlyHistory() || isPostResultsFollowUpMessage(userText),
  });
  const thinkingMessageId = appendAssistantThinkingMessage(
    chatMessageResponseLanguage(userText)
  );

  try {
    if (await handlePendingSearchRunChatAction(userText)) {
      clearAssistantThinkingMessage(thinkingMessageId);
      return;
    }

    if (await handlePendingSearchSummaryUpdateAction(userText)) {
      clearAssistantThinkingMessage(thinkingMessageId);
      return;
    }

    if (isPostResultsFollowUpMessage(userText)) {
      handlePostResultsFollowUp(userText);
      clearAssistantThinkingMessage(thinkingMessageId);
      chatInput.focus();
      return;
    }

    markChatMessageForBackend(optimisticUserMessage);
    chatRequestInFlight = true;
    chatStatusElement.textContent = "";
    updateActionState();
  } catch (error) {
    clearAssistantThinkingMessage(thinkingMessageId);
    messages.push(
      typedChatMessage(
        {
          role: "assistant",
          content: error.message,
          localOnly: true,
        },
        {
          messageType: AGENT_MESSAGE_TYPES.SYSTEM_ERROR,
          surface: "chat",
        }
      )
    );
    chatStatusElement.textContent = error.message;
    renderChatMessages();
    updateActionState();
    chatInput.focus();
    return;
  }

  const pendingUpdateFieldForRequest =
    pendingChatAction?.type === "update_search_summary_field"
      ? pendingChatAction.field
      : null;

  try {
    const response = await fetch("/api/recruiter-chat/turn", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: chatMessagesForBackend(),
        draft_brief: draftBrief,
        language: currentChatLanguage,
        pending_update_field: pendingUpdateFieldForRequest,
      }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Recruiter chat request failed.");
    }

    if (requestVersion !== interactionVersion) {
      return;
    }

    clearAssistantThinkingMessage(thinkingMessageId);
    updateChatStateFromResponse(data);
    if (
      pendingUpdateFieldForRequest &&
      (data.brief_changed ||
        (data.brief_patch && data.brief_patch.requires_clarification !== true))
    ) {
      clearPendingChatAction();
    }
  } catch (error) {
    if (requestVersion !== interactionVersion) {
      return;
    }

    clearAssistantThinkingMessage(thinkingMessageId);
    messages.push(
      typedChatMessage(
        {
          role: "assistant",
          content: error.message,
          localOnly: true,
        },
        {
          messageType: AGENT_MESSAGE_TYPES.SYSTEM_ERROR,
          surface: "chat",
        }
      )
    );
    chatStatusElement.textContent = error.message;
    renderChatMessages();
    updateActionState();
  } finally {
    if (requestVersion === interactionVersion) {
      clearAssistantThinkingMessage(thinkingMessageId);
      chatRequestInFlight = false;
      updateActionState();
      chatInput.focus();
    }
  }
}

function resetChat() {
  interactionVersion += 1;
  messages = [];
  draftBrief = null;
  normalizedBrief = null;
  chatState = "drafting";
  recommendedPlannerMode = PRIMARY_BUILD_PLAN_MODE;
  currentChatLanguage = "en";
  chatRequestInFlight = false;
  agentPlanRequestInFlight = false;
  planRequestInFlight = false;
  searchRequestInFlight = false;
  searchConfirmationInFlight = false;
  chatTransientMessageCounter = 0;
  multiWaveInput.checked = DEFAULT_MULTI_WAVE_ENABLED;
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  clearWorkspaceState();
  chatInput.value = "";
  chatStatusElement.textContent = "";
  planStatus.textContent = "Prepare search from the chat summary.";
  queryList.innerHTML = "";
  reportStatus.textContent = "Run a search to see the summary.";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
  resultsStatus.textContent = "Run a search to see candidates.";
  resultsList.innerHTML = "";
  renderChatMessages();
  renderBriefSummaryCard(null);
  syncExecutionControlsFromPlan();
  updateActionState();
}

function renderReport(report) {
  if (!report) {
    reportStatus.textContent = "No report returned.";
    reportGrid.innerHTML = "";
    contributionList.innerHTML = "";
    return;
  }

  const reportMode = report.mode === "multi_wave" ? "Multi-wave" : "Single-wave";
  const uniqueCount = report.unique_profiles ?? report.displayed ?? 0;
  reportStatus.textContent = `${uniqueCount} unique ${pluralize(
    uniqueCount,
    "candidate",
    "candidates"
  )} found. ${reportMode} search completed.`;

  const fields = [
    ["Raw", report.raw_total],
    ["Normalized", report.normalized_total],
    ["Displayed", report.displayed],
    ["Unique", report.unique_profiles],
    ["Duplicates", report.duplicates_removed],
    ["Profile filter", report.hidden_by_profile_filter],
    ["Location filter", report.hidden_by_location_filter],
    ["Rescued", report.rescued_by_header_location],
    ["Foreign location", report.hidden_by_foreign_current_location],
    ["Weak location", report.weak_location_history_only],
    ["Unknown location", report.unknown_non_country_domain_location],
    ["Failed queries", report.queries_failed],
  ];
  if (report.mode === "multi_wave" || report.experimental) {
    fields.push(
      ["Waves", report.waves_run],
      ["Executed queries", report.queries_executed],
      ["Stop reason", report.stop_reason],
      ["New per wave", (report.new_unique_profiles_per_wave || []).join(", ")]
    );
  }

  const metricMarkup = fields
    .map(
      ([label, value]) => `
        <div class="report-metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value ?? 0)}</strong>
        </div>
      `
    )
    .join("");
  reportGrid.innerHTML = `
    <details class="collapsible-section report-details">
      <summary class="collapsible-summary">
        <span>Detailed metrics</span>
        <span class="collapse-indicator" aria-hidden="true"></span>
      </summary>
      <div class="report-grid-inner">${metricMarkup}</div>
    </details>
  `;

  contributionList.innerHTML = "";
}

function renderQualityField(label, value, modifier = "") {
  return `
    <div class="quality-field ${modifier}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(displayValue(value))}</strong>
    </div>
  `;
}

function stackDisplayValue(result = {}) {
  if (result.stack_fit === "missing_selected_stack") {
    return "Not visible";
  }

  if (result.stack_fit === "stack_query_source_only") {
    return "Not confirmed";
  }

  if (result.stack_fit === "missing") {
    return "N/A";
  }

  return displayValue(result.stack_display, "N/A");
}

function renderFlagBadges(flagDetails = []) {
  if (!flagDetails.length) {
    return `<span class="flag-badge severity-info">No review flags</span>`;
  }

  return flagDetails
    .map(
      (flag) => `
        <span
          class="flag-badge ${escapeHtml(candidateWorkspace.severityClassName(flag.severity))}"
          title="${escapeHtml(flag.description || flag.code)}"
        >
          ${escapeHtml(flag.label || flag.code)}
        </span>
      `
    )
    .join("");
}

function renderScoreBreakdown(result) {
  const breakdown = result.quality_score_breakdown || [];
  const penalties = result.quality_score_penalties || [];

  if (!breakdown.length && !penalties.length) {
    return `<p class="result-snippet">No quality score details returned.</p>`;
  }

  return `
    <div class="score-details">
      ${breakdown
        .map(
          (item) => `
            <div class="score-line">
              <span>${escapeHtml(item.component)}</span>
              <strong>${escapeHtml(item.points)} / ${escapeHtml(item.max_points)}</strong>
              <p>${escapeHtml(item.reason)}</p>
            </div>
          `
        )
        .join("")}
      ${penalties
        .map(
          (item) => `
            <div class="score-line is-penalty">
              <span>${escapeHtml(item.flag)}</span>
              <strong>${escapeHtml(item.points)}</strong>
              <p>${escapeHtml(item.reason)}</p>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderQuerySourceDetails(sources = []) {
  if (!sources.length) {
    return `<p class="result-snippet">No query source metadata returned.</p>`;
  }

  return sources
    .map(
      (source) => `
        <p class="result-snippet">
          <strong>${escapeHtml(source.id)}</strong>
          ${escapeHtml(source.role_phrase || source.category || "")}: ${escapeHtml(source.query)}
        </p>
      `
    )
    .join("");
}

function renderResults(dedupedResults, report, options = {}) {
  replaceWorkspaceRun(dedupedResults, report, options.runContext || {});
  renderWorkspaceResults(report);
}

async function runStructuredSearch() {
  if (!latestExecutablePlan) {
    resultsStatus.textContent =
      "Prepare a runnable search before continuing.";
    return;
  }
  if (!currentRuntimePendingApproval) {
    resultsStatus.textContent =
      "Wait until the search is ready to run.";
    return;
  }

  const requestVersion = interactionVersion;
  const runtimeRequestVersion = runtimeApprovalVersion;
  searchRequestInFlight = true;
  setAgentActionDisplayState(
    AGENT_QUEUE_ACTION_RUN_SEARCH,
    "running",
    `Running ${currentRunSearchModeLabel()} search.`
  );
  updateActionState();
  resultsStatus.textContent = "Checking that the search is ready to run...";
  reportStatus.textContent = "Starting search...";
  clearWorkspaceState();
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";

  try {
    if (!latestPlanFingerprint || !latestQueryPlan?.queries?.length) {
      throw new Error("Current search details are missing.");
    }

    const payload = {
      turn_mode: AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED,
      tool_name: currentRunSearchAction(),
      tool_input: buildRuntimeToolInput(),
      runtime_context: buildRuntimeContext(),
      runtime_approval: buildApprovedRuntimeApproval(),
      agent_language: currentChatLanguage,
    };

    resultsStatus.textContent = multiWaveInput.checked
      ? "Searching with multi-wave..."
      : "Searching...";
    reportStatus.textContent = multiWaveInput.checked
      ? "Running multi-wave search..."
      : "Running search...";

    const response = await fetch(AGENT_RUNTIME_TURN_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (
      requestVersion !== interactionVersion ||
      runtimeRequestVersion !== runtimeApprovalVersion
    ) {
      return;
    }

    if (!response.ok) {
      throw new Error(data.detail || "Agent runtime request failed.");
    }

    if (data.errors?.length) {
      renderSearchErrors(data.errors);
      return;
    }

    const toolResult = data.tool_results?.[0] || null;
    if (!toolResult) {
      throw new Error("Agent runtime did not return a tool result.");
    }
    if (toolResult.errors?.length) {
      renderSearchErrors(toolResult.errors);
      return;
    }

    const searchData = toolResult.result || {};
    if (!searchData.query_plan || !searchData.report) {
      throw new Error("Agent runtime returned an incomplete search result.");
    }
    const workspaceRunContext = captureWorkspaceRunContext(searchData);

    renderQueryPlan(searchData.query_plan, {
      planner_mode: "rule_based",
      normalized_brief: normalizedBrief,
    });
    renderReport(searchData.report);
    renderResults(searchData.deduped_results || [], searchData.report, {
      runContext: workspaceRunContext,
    });
    clearRuntimeApproval();
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_RUN_SEARCH,
      "completed",
      "Search completed and results are visible."
    );
    appendAgentResponseMessage(searchData.agent_response);
  } catch (error) {
    if (
      requestVersion !== interactionVersion ||
      runtimeRequestVersion !== runtimeApprovalVersion
    ) {
      return;
    }

    clearRuntimeApproval();
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_RUN_SEARCH,
      "failed",
      error.message || "Search failed."
    );
    resultsStatus.textContent = error.message;
    reportStatus.textContent = error.message;
    clearWorkspaceState();
    resultsList.innerHTML = "";
    reportGrid.innerHTML = "";
    contributionList.innerHTML = "";
  } finally {
    if (requestVersion === interactionVersion) {
      searchRequestInFlight = false;
      updateActionState();
    }
  }
}

function candidateIdFromWorkspaceEvent(event) {
  const row = event.target.closest("[data-candidate-id]");
  return row ? row.getAttribute("data-candidate-id") : "";
}

function workspaceCandidateById(candidateId) {
  return workspaceCandidates.find((candidate) => candidate.candidate_id === candidateId) || null;
}

function currentWordingStateKeyForCandidate(candidate = {}) {
  if (!latestWorkspaceRun || !candidate.wording_target_key) {
    return "";
  }
  return workspaceWordingStateKey(latestWorkspaceRun.workspace_run_id, candidate.wording_target_key);
}

function setCandidateWordingState(candidate, state) {
  const stateKey = currentWordingStateKeyForCandidate(candidate);
  if (!stateKey) {
    return;
  }
  workspaceExplanationWordingByKey = {
    ...workspaceExplanationWordingByKey,
    [stateKey]: state,
  };
}

function wordingResponseMatchesCurrentState(data = {}, requestPayload = {}, pendingKey = "") {
  if (!latestWorkspaceRun) {
    return false;
  }
  const stateKey = workspaceWordingStateKey(
    latestWorkspaceRun.workspace_run_id,
    requestPayload.wording_target_key
  );
  const currentState = workspaceExplanationWordingByKey[stateKey];
  return Boolean(
    data.workspace_run_id === latestWorkspaceRun.workspace_run_id &&
      data.wording_target_key === requestPayload.wording_target_key &&
      data.request_explanation_fingerprint === requestPayload.request_explanation_fingerprint &&
      data.language === requestPayload.target_language &&
      currentState?.pending_key === pendingKey
  );
}

async function requestCandidateExplanationWording(candidateId) {
  if (!latestWorkspaceRun) {
    return;
  }
  const candidate = workspaceCandidateById(candidateId);
  if (!candidate || !candidate.wording_target_key) {
    return;
  }
  const explanation = candidateWorkspace.buildCandidateExplanation(candidate);
  if (!explanation || explanation.source !== "deterministic_workspace_facts") {
    return;
  }

  let requestPayload;
  try {
    requestPayload = await candidateWorkspace.buildCandidateExplanationWordingRequest({
      workspaceRunId: latestWorkspaceRun.workspace_run_id,
      wordingTargetKey: candidate.wording_target_key,
      explanation,
      targetLanguage: candidateWorkspace.CANDIDATE_EXPLANATION_WORDING_TARGET_LANGUAGE,
    });
  } catch (error) {
    setCandidateWordingState(candidate, {
      status: "fallback",
      reason: "request_build_failed",
    });
    renderWorkspaceResults(latestWorkspaceRun.report);
    return;
  }

  const pendingKey = [
    requestPayload.workspace_run_id,
    requestPayload.wording_target_key,
    requestPayload.request_explanation_fingerprint,
    requestPayload.target_language,
  ].join("|");
  const existingState = workspaceWordingStateForCandidate(candidate);
  if (
    existingState?.status === "applied" &&
    existingState.request_explanation_fingerprint === requestPayload.request_explanation_fingerprint &&
    existingState.language === requestPayload.target_language
  ) {
    renderWorkspaceResults(latestWorkspaceRun.report);
    return;
  }
  if (existingState?.status === "pending" && existingState.pending_key === pendingKey) {
    return;
  }

  setCandidateWordingState(candidate, {
    status: "pending",
    pending_key: pendingKey,
    request_explanation_fingerprint: requestPayload.request_explanation_fingerprint,
    language: requestPayload.target_language,
  });
  renderWorkspaceResults(latestWorkspaceRun.report);

  try {
    const response = await fetch(CANDIDATE_EXPLANATION_WORDING_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestPayload),
    });
    const data = await response.json();
    if (!wordingResponseMatchesCurrentState(data, requestPayload, pendingKey)) {
      return;
    }

    if (
      response.ok &&
      data.ok &&
      data.wording_mode === "llm_assisted" &&
      data.wording_overlay
    ) {
      setCandidateWordingState(candidate, {
        status: "applied",
        overlay: data.wording_overlay,
        backend_wording_cache_key: data.backend_wording_cache_key,
        request_explanation_fingerprint: requestPayload.request_explanation_fingerprint,
        language: requestPayload.target_language,
      });
    } else {
      setCandidateWordingState(candidate, {
        status: "fallback",
        reason: data.fallback_reason || "wording_not_applied",
        request_explanation_fingerprint: requestPayload.request_explanation_fingerprint,
        language: requestPayload.target_language,
      });
    }
  } catch (error) {
    setCandidateWordingState(candidate, {
      status: "fallback",
      reason: "wording_request_failed",
      request_explanation_fingerprint: requestPayload.request_explanation_fingerprint,
      language: requestPayload.target_language,
    });
  } finally {
    if (latestWorkspaceRun) {
      renderWorkspaceResults(latestWorkspaceRun.report);
    }
  }
}

function recomputeVisibleWorkspaceCandidates() {
  return candidateWorkspace.applyWorkspaceView(
    workspaceCandidates,
    workspaceViewState,
    workspaceReviewStateByCandidateId
  );
}

function exportFormatLabel(format) {
  return candidateWorkspace.normalizeExportFormat(format) === "markdown" ? "Markdown" : "CSV";
}

function buildCurrentWorkspaceExportModel(exportedAt) {
  return candidateWorkspace.buildWorkspaceExportModel({
    workspaceRun: latestWorkspaceRun,
    allCandidates: workspaceCandidates,
    visibleCandidates: recomputeVisibleWorkspaceCandidates(),
    reviewStateByCandidateId: workspaceReviewStateByCandidateId,
    scope: workspaceExportState.scope,
    format: workspaceExportState.format,
    exportedAt,
  });
}

function serializeWorkspaceExportModel(model, format) {
  if (candidateWorkspace.normalizeExportFormat(format) === "markdown") {
    return candidateWorkspace.serializeWorkspaceExportMarkdown(model);
  }
  return candidateWorkspace.serializeWorkspaceExportCsv(model);
}

function triggerWorkspaceExportDownload() {
  if (!latestWorkspaceRun) {
    return;
  }

  const scope = candidateWorkspace.normalizeExportScope(workspaceExportState.scope);
  const format = candidateWorkspace.normalizeExportFormat(workspaceExportState.format);
  const exportedAt = new Date();
  let objectUrl = "";
  let temporaryAnchor = null;

  try {
    const exportModel = buildCurrentWorkspaceExportModel(exportedAt);
    if (!exportModel.metadata.candidate_count) {
      setWorkspaceExportStatus("No candidates to export for selected scope.");
      return;
    }

    const serialized = serializeWorkspaceExportModel(exportModel, format);
    const blob = new Blob([serialized], {
      type: candidateWorkspace.workspaceExportMimeType(format),
    });
    objectUrl = URL.createObjectURL(blob);
    temporaryAnchor = document.createElement("a");
    temporaryAnchor.href = objectUrl;
    temporaryAnchor.download = candidateWorkspace.buildWorkspaceExportFilename(exportedAt, scope, format);
    temporaryAnchor.rel = "noopener";
    temporaryAnchor.style.display = "none";
    document.body.appendChild(temporaryAnchor);
    temporaryAnchor.click();
    temporaryAnchor.remove();
    temporaryAnchor = null;

    const urlToRevoke = objectUrl;
    objectUrl = "";
    setTimeout(() => URL.revokeObjectURL(urlToRevoke), 0);
    setWorkspaceExportStatus(
      `Exported ${exportModel.metadata.candidate_count} ${pluralize(
        exportModel.metadata.candidate_count,
        "candidate",
        "candidates"
      )} as ${exportFormatLabel(format)}`
    );
  } catch (error) {
    setWorkspaceExportStatus("Export failed. Try again.");
  } finally {
    if (temporaryAnchor && temporaryAnchor.parentNode) {
      temporaryAnchor.remove();
    }
    if (objectUrl) {
      const urlToRevoke = objectUrl;
      setTimeout(() => URL.revokeObjectURL(urlToRevoke), 0);
    }
  }
}

function handleWorkspaceChange(event) {
  if (!latestWorkspaceRun) {
    return;
  }

  const exportControl = event.target.closest("[data-workspace-export-control]");
  if (exportControl) {
    const controlName = exportControl.dataset.workspaceExportControl;
    if (controlName === "scope") {
      workspaceExportState = {
        ...workspaceExportState,
        scope: candidateWorkspace.normalizeExportScope(exportControl.value),
        status: "",
      };
      renderWorkspaceResults(latestWorkspaceRun.report);
      return;
    }
    if (controlName === "format") {
      workspaceExportState = {
        ...workspaceExportState,
        format: candidateWorkspace.normalizeExportFormat(exportControl.value),
        status: "",
      };
      renderWorkspaceResults(latestWorkspaceRun.report);
      return;
    }
  }

  const controlName = event.target.dataset.workspaceControl;
  if (controlName) {
    workspaceViewState = candidateWorkspace.normalizeWorkspaceViewState({
      ...workspaceViewState,
      [controlName]: event.target.value,
    });
    workspacePaginationState = {
      ...workspacePaginationState,
      currentPage: 1,
    };
    clearWorkspaceExportStatus(false);
    renderWorkspaceResults(latestWorkspaceRun.report);
    return;
  }

  const action = event.target.dataset.workspaceAction;
  const candidateId = candidateIdFromWorkspaceEvent(event);
  if (!candidateId) {
    return;
  }

  if (action === "status") {
    workspaceReviewStateByCandidateId = candidateWorkspace.setWorkspaceReviewStatus(
      workspaceReviewStateByCandidateId,
      candidateId,
      event.target.value
    );
    clearWorkspaceExportStatus(false);
    renderWorkspaceResults(latestWorkspaceRun.report);
    return;
  }

  if (action === "shortlist") {
    workspaceReviewStateByCandidateId = candidateWorkspace.toggleWorkspaceShortlist(
      workspaceReviewStateByCandidateId,
      candidateId,
      event.target.checked
    );
    clearWorkspaceExportStatus(false);
    renderWorkspaceResults(latestWorkspaceRun.report);
  }
}

function handleWorkspaceInput(event) {
  if (!latestWorkspaceRun || event.target.dataset.workspaceAction !== "note") {
    return;
  }

  const candidateId = candidateIdFromWorkspaceEvent(event);
  if (!candidateId) {
    return;
  }

  workspaceReviewStateByCandidateId = candidateWorkspace.setWorkspaceCandidateNote(
    workspaceReviewStateByCandidateId,
    candidateId,
    event.target.value
  );
  const currentState = workspaceReviewStateByCandidateId[candidateId];
  const countElement = event.target
    .closest(".workspace-note")
    ?.querySelector("[data-workspace-note-count]");
  if (countElement) {
    countElement.textContent = `${currentState.note.length} / ${candidateWorkspace.NOTE_MAX_LENGTH}`;
  }
  clearWorkspaceExportStatus(false);
}

function handleWorkspaceClick(event) {
  if (!latestWorkspaceRun) {
    return;
  }

  const pageAction = event.target.closest("[data-workspace-page-action]");
  if (pageAction) {
    event.preventDefault();
    const direction = pageAction.dataset.workspacePageAction;
    const visibleCandidates = recomputeVisibleWorkspaceCandidates();
    const pagination = workspacePaginationModel(visibleCandidates);
    workspacePaginationState = {
      ...workspacePaginationState,
      currentPage:
        direction === "previous"
          ? pagination.currentPage - 1
          : pagination.currentPage + 1,
    };
    renderWorkspaceResults(latestWorkspaceRun.report);
    return;
  }

  const exportAction = event.target.closest("[data-workspace-export-action]");
  if (exportAction) {
    event.preventDefault();
    if (exportAction.dataset.workspaceExportAction === "download") {
      triggerWorkspaceExportDownload();
    }
    return;
  }

  const action = event.target.dataset.workspaceAction;
  if (action === "improve-wording") {
    event.preventDefault();
    const candidateId = candidateIdFromWorkspaceEvent(event);
    if (candidateId) {
      void requestCandidateExplanationWording(candidateId);
    }
    return;
  }

  if (action !== "reset-filters") {
    return;
  }

  event.preventDefault();
  workspaceViewState = candidateWorkspace.defaultWorkspaceViewState();
  workspacePaginationState = defaultWorkspacePaginationState();
  clearWorkspaceExportStatus(false);
  renderWorkspaceResults(latestWorkspaceRun.report);
}

if (statusElement) {
  statusElement.textContent = "Workspace ready";
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const userText = chatInput.value.trim();
  if (!userText) {
    return;
  }
  chatInput.value = "";
  sendChatTurn(userText);
});

chatInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) {
    return;
  }
  if (event.isComposing || chatInput.disabled || sendChatButton.disabled) {
    return;
  }
  if (!chatInput.value.trim()) {
    return;
  }

  event.preventDefault();
  if (typeof chatForm.requestSubmit === "function") {
    chatForm.requestSubmit();
    return;
  }
  sendChatButton.click();
});

resetChatButton.addEventListener("click", resetChat);
buildPlanButton.addEventListener("click", buildPlanFromChat);
searchButton.addEventListener("click", runStructuredSearch);
resultsList.addEventListener("change", handleWorkspaceChange);
resultsList.addEventListener("input", handleWorkspaceInput);
resultsList.addEventListener("click", handleWorkspaceClick);
multiWaveInput.addEventListener("change", () => {
  clearPendingChatAction();
  clearRuntimeApproval();
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  updateActionState();
  if (latestExecutablePlan) {
    void prepareRuntimeSearchAction();
  }
});

resetChat();
