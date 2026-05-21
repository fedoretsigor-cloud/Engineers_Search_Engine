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

const PRIMARY_BUILD_PLAN_MODE = "rule_based";
const AGENT_PLAN_ENDPOINT = "/api/agent/plan";
const AGENT_QUERY_PLAN_ENDPOINT = "/api/agent/query-plan";
const AGENT_RUNTIME_TURN_ENDPOINT = "/api/agent/runtime/turn";
const AGENT_ACTION_BUILD_QUERY_PLAN = "build_query_plan";
const AGENT_ACTION_RUN_SINGLE_WAVE = "run_single_wave_search";
const AGENT_ACTION_RUN_MULTI_WAVE = "run_multi_wave_search";
const AGENT_QUEUE_ACTION_BUILD_PLAN = "build_plan";
const AGENT_QUEUE_ACTION_RUN_SEARCH = "run_search";
const AGENT_RUNTIME_TURN_MODE_PREPARE = "prepare";
const AGENT_RUNTIME_TURN_MODE_EXECUTE_APPROVED = "execute_approved";
const AGENT_RUNTIME_EXECUTION_MODE_SINGLE_WAVE = "single_wave";
const AGENT_RUNTIME_EXECUTION_MODE_MULTI_WAVE = "multi_wave";

const AGENT_ACTION_STATUS_LABELS = {
  blocked: "Blocked",
  ready: "Ready",
  ready_for_approval: "Ready for approval",
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
    label: "Search Brief",
    className: "typed-brief-summary",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.BRIEF_REFINEMENT_APPLIED]: {
    label: "Brief refinement",
    className: "typed-brief-refinement",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.BRIEF_REFINEMENT_REJECTED]: {
    label: "Brief refinement blocked",
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
    label: "Tool unavailable",
    className: "typed-tool-unavailable",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.AGENT_PLAN]: {
    label: "Agent Plan",
    className: "typed-agent-plan",
    speaker: "AI Agent",
  },
  [AGENT_MESSAGE_TYPES.AGENT_PLAN_UNSUPPORTED]: {
    label: "Unsupported brief",
    className: "typed-agent-plan-unsupported",
    speaker: "AI Agent",
  },
  [AGENT_MESSAGE_TYPES.PLANNING_NEEDS_CLARIFICATION]: {
    label: "Planning needs input",
    className: "typed-planning-needs-clarification",
    speaker: "AI Agent",
  },
  [AGENT_MESSAGE_TYPES.SYSTEM_ERROR]: {
    label: "System error",
    className: "typed-system-error",
    speaker: "AI",
  },
  [AGENT_MESSAGE_TYPES.AGENT_RESPONSE]: {
    label: "Agent Response",
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
let adaptedStructuredRequest = null;
let latestPlannerData = null;
let latestQueryPlan = null;
let latestPlanFingerprint = null;
let latestExecutablePlan = false;
let latestAgentResponse = null;
let currentRuntimePendingApproval = null;
let currentRuntimeToolCall = null;
let runtimeApprovalVersion = 0;
let chatRequestInFlight = false;
let agentPlanRequestInFlight = false;
let planRequestInFlight = false;
let runtimePrepareRequestInFlight = false;
let searchRequestInFlight = false;
let interactionVersion = 0;
let agentActionDisplayState = {
  [AGENT_QUEUE_ACTION_BUILD_PLAN]: null,
  [AGENT_QUEUE_ACTION_RUN_SEARCH]: null,
};

const MULTI_WAVE_DEFAULTS = {
  max_waves: 5,
  min_new_unique_per_wave: 3,
  patience: 2,
};

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
    rule_based: "Search Plan",
    ai: "AI preview",
    ai_with_fallback: "AI-assisted preview",
    draft_query_plan: "Draft QueryPlan",
    validated_not_executable: "Validated preview",
    rejected: "Rejected",
    rule_based_fallback: "Fallback Search Plan",
    needs_clarification: "Needs clarification",
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

function readyBriefChatStatus(options = {}) {
  const includePending = options.includePending !== false;
  if (includePending && agentPlanRequestInFlight) {
    return "Search Brief ready. Preparing Agent Plan...";
  }

  if (hasSupportedAgentAction()) {
    return "Agent Plan ready. Build Plan is available.";
  }

  if (currentAgentPlanData?.agent_plan_status === "unsupported") {
    return "Agent v0 does not support this brief yet.";
  }

  if (currentAgentPlanData) {
    return "Agent Plan needs clarification before Build Plan.";
  }

  return "Search Brief ready. Preparing Agent Plan...";
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
    return "Ready for approval";
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
        ? "Search Plan is visible and ready for approval."
        : "A non-executable plan preview is visible."
    );
  }
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  syncExecutionControlsFromPlan();
  updateActionState();
}

function clearPlannerData() {
  latestPlannerData = null;
  latestQueryPlan = null;
  latestPlanFingerprint = null;
  adaptedStructuredRequest = null;
  latestExecutablePlan = false;
  clearRuntimeApproval();
  updateActionState();
}

function clearAgentPlanData() {
  currentAgentPlanData = null;
  currentAgentPlan = null;
  currentAgentAction = null;
  messages = messages.filter((message) => message.kind !== "agent_plan");
}

function clearSearchResultsData() {
  latestAgentResponse = null;
  messages = messages.filter((message) => message.kind !== "agent_response");
  reportStatus.textContent = "Run a search to see counts.";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
  resultsStatus.textContent = "Run a search to see deduped candidates.";
  resultsList.innerHTML = "";
}

function clearDownstreamStateAfterBriefChange() {
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  clearSearchResultsData();
  planStatus.textContent = "Build a plan from the updated chat brief.";
  queryList.innerHTML = "";
}

function clearExecutableStateAfterRefusal() {
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  clearSearchResultsData();
  planStatus.textContent = "Build a plan from the current Search Brief.";
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
    throw new Error("Build Plan before approving search.");
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
    throw new Error("Current QueryPlan is missing approval fingerprint.");
  }
  if (!currentAgentPlan?.brief_fingerprint) {
    throw new Error("Current Agent Plan is missing Search Brief fingerprint.");
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
    throw new Error("Runtime approval is not prepared for the current Search Plan.");
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
    return "AI Agent";
  }

  return message.role === "user" ? "You" : "AI";
}

function chatRoleClass(message = {}) {
  return message.role === "user" ? "user-message" : "assistant-message";
}

function renderPlainChatMessage(message = {}) {
  return `
    <article class="chat-message ${chatRoleClass(message)}">
      <span>${escapeHtml(plainChatSpeaker(message))}</span>
      <p>${escapeHtml(message.content)}</p>
    </article>
  `;
}

function renderNextIterationOptions(options = []) {
  const visibleOptions = arrayValue(options);
  if (!visibleOptions.length) {
    return "";
  }

  return `
    <div class="next-iteration-options" aria-label="Next iteration options">
      <strong>Next iteration options</strong>
      <p>Not executable. Write a follow-up in chat if you want to change the Search Brief.</p>
      <ol>
        ${visibleOptions
          .map((option, index) => {
            const safeOption = option || {};
            const label = safeOption.label || safeOption.id || `Option ${index + 1}`;
            const reason = safeOption.reason || "Grounded in the returned search data.";
            return `
              <li>
                <strong>${escapeHtml(label)}</strong>
                <p>${escapeHtml(reason)}</p>
              </li>
            `;
          })
          .join("")}
      </ol>
    </div>
  `;
}

function renderTypedChatMessage(message = {}) {
  const meta = AGENT_MESSAGE_TYPE_META[message.messageType];
  if (!meta) {
    return renderPlainChatMessage(message);
  }

  const optionsMarkup =
    message.messageType === AGENT_MESSAGE_TYPES.AGENT_RESPONSE
      ? renderNextIterationOptions(message.payload?.next_iteration_options)
      : "";

  return `
    <article class="chat-message ${chatRoleClass(message)} typed-message ${meta.className}">
      <span>${escapeHtml(meta.speaker)} - ${escapeHtml(meta.label)}</span>
      <p>${escapeHtml(message.content)}</p>
      ${optionsMarkup}
    </article>
  `;
}

function renderChatMessages() {
  if (!messages.length) {
    chatMessagesElement.innerHTML = `
      <article class="chat-message assistant-message">
        <p>Describe the search in natural language. I will collect a Search Brief before planning.</p>
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
    <div class="planner-section">
      <div class="brief-heading">
        <h3>Search Brief</h3>
        <span>${escapeHtml(plannerLabel(state))}</span>
      </div>
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
  let detail = "Complete a supported Search Brief before building a plan.";

  if (planRequestInFlight) {
    status = "running";
    detail = "Building the visible QueryPlan.";
  } else if (displayState?.status === "failed" && !latestQueryPlan) {
    status = "failed";
    detail = displayState.detail || "Build Plan failed.";
  } else if (latestQueryPlan?.queries?.length) {
    status = "completed";
    detail = latestExecutablePlan
      ? "Search Plan is visible and ready for approval."
      : "A non-executable plan preview is visible.";
  } else if (hasSupportedAgentAction()) {
    status = "ready";
    detail = "Supported Agent Plan action is ready.";
  } else if (agentPlanRequestInFlight) {
    detail = "Waiting for Agent Plan.";
  } else if (currentAgentPlanData?.agent_plan_status === "unsupported") {
    detail = "Agent v0 does not support this brief.";
  } else if (chatState === "ready_for_planning" && normalizedBrief) {
    detail = "Waiting for a supported Agent Plan action.";
  }

  return {
    id: AGENT_QUEUE_ACTION_BUILD_PLAN,
    title: "Build Search Plan",
    action: AGENT_ACTION_BUILD_QUERY_PLAN,
    requiresApproval: false,
    status,
    detail,
    context: [
      ["Source", "Agent Plan"],
      [
        "Brief",
        currentAgentPlan?.brief_fingerprint
          ? `fingerprint ${shortFingerprint(currentAgentPlan.brief_fingerprint)}`
          : "not bound",
      ],
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
  let detail = "Build an executable Search Plan before approval.";

  if (searchRequestInFlight) {
    status = "running";
    detail = `Running ${currentRunSearchModeLabel()} search.`;
  } else if (runtimePrepareRequestInFlight) {
    status = "running";
    detail = "Preparing runtime approval for the visible Search Plan.";
  } else if (displayState?.status === "failed") {
    status = "failed";
    detail = displayState.detail || "Search failed.";
  } else if (displayState?.status === "completed" && latestExecutablePlan) {
    status = "completed";
    detail = "Search completed and results are visible.";
  } else if (latestExecutablePlan && latestPlanFingerprint && currentRuntimePendingApproval) {
    status = "ready_for_approval";
    detail = "Runtime approval is prepared for the visible Search Plan.";
  } else if (latestExecutablePlan && latestPlanFingerprint) {
    detail = "Waiting for runtime approval preparation.";
  } else if (hasVisiblePlan) {
    detail = "Visible plan is not executable.";
  }

  return {
    id: AGENT_QUEUE_ACTION_RUN_SEARCH,
    title: "Run Search",
    action: currentRunSearchAction(),
    requiresApproval: true,
    status,
    detail,
    context: [
      ["Source", "Visible QueryPlan"],
      ["Mode", currentRunSearchModeLabel()],
      [
        "QueryPlan",
        latestPlanFingerprint
          ? `fingerprint ${shortFingerprint(latestPlanFingerprint)}`
          : "not bound",
      ],
      ["Queries", queryCountForCurrentPlan() || "not ready"],
      [
        "Runtime",
        currentRuntimePendingApproval
          ? `approval ${shortFingerprint(currentRuntimePendingApproval.tool_call_id)}`
          : "not prepared",
      ],
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
    <div class="agent-action-header">
      <h3>Agent Actions</h3>
      <span>${escapeHtml(items.length ? `${items.length} active` : "idle")}</span>
    </div>
  `;

  if (!items.length) {
    agentActionQueueElement.innerHTML = `
      ${header}
      <p class="agent-action-empty">No agent action is ready yet.</p>
    `;
    return;
  }

  agentActionQueueElement.innerHTML = `
    ${header}
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
                  <span>Tool</span>
                  <strong>${escapeHtml(item.action)}</strong>
                </div>
                <div>
                  <span>Approval</span>
                  <strong>${item.requiresApproval ? "Required" : "Not required"}</strong>
                </div>
                ${renderAgentActionContext(item.context)}
              </div>
            </article>
          `;
        })
        .join("")}
    </div>
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
              <h3>Planner explanation</h3>
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
              data.approval_notice || "This plan is not executed yet. Search execution requires approval."
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
    validationMessage(errors) || "Build Plan failed."
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
      error.message || "Runtime approval preparation failed."
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
    "Preparing runtime approval for the visible Search Plan."
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
      throw new Error(data.detail || "Runtime approval preparation failed.");
    }

    if (data.errors?.length) {
      renderSearchErrors(data.errors);
      return null;
    }

    const pendingApproval = data.pending_approvals?.[0] || null;
    const toolCall = data.tool_calls?.[0] || null;
    if (!pendingApproval || !toolCall) {
      throw new Error("Runtime approval response did not include a pending tool call.");
    }

    currentRuntimePendingApproval = pendingApproval;
    currentRuntimeToolCall = toolCall;
    setAgentActionDisplayState(
      AGENT_QUEUE_ACTION_RUN_SEARCH,
      "ready_for_approval",
      "Runtime approval is prepared for the visible Search Plan."
    );
    resultsStatus.textContent = "Search plan is ready for explicit approval.";
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
      error.message || "Runtime approval preparation failed."
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
    planStatus.textContent = `Search plan is ready: ${queryPlan.planner_version} generated ${queryCountText}.`;
  } else {
    const modeText = plannerData?.planner_mode
      ? `${plannerLabel(plannerData.planner_mode)}: `
      : "";
    planStatus.textContent = `${modeText}${queryPlan.planner_version} generated ${queryCountText}.`;
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
    resultsStatus.textContent = "Build a valid plan before approving search.";
    return;
  }

  renderQueryPlan(queryPlan, data);

  if (latestExecutablePlan) {
    resultsStatus.textContent =
      "Search plan is ready. Review the queries before running search.";
    return;
  }

  resultsStatus.textContent =
    "Plan preview is not executable yet. Use a rule-based or rule-based fallback plan to search.";
}

function rememberAgentPlanData(data = {}) {
  currentAgentPlanData = data;
  currentAgentPlan = data.agent_plan || null;
  currentAgentAction = currentAgentPlan?.proposed_action || null;
}

function appendAgentPlanMessage(data = {}) {
  const content =
    data.agent_plan?.message ||
    data.message ||
    "Agent Plan is not available for this Search Brief.";

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

function visibleNextIterationOptions(agentResponse = {}) {
  return arrayValue(agentResponse.next_iteration_options).map((option, index) => {
    const safeOption = option || {};
    return {
      id: safeOption.id || `option_${index + 1}`,
      label: safeOption.label || safeOption.id || `Option ${index + 1}`,
      reason: safeOption.reason || "Grounded in the returned search data.",
    };
  });
}

function appendAgentResponseMessage(agentResponse = null) {
  const response = agentResponse || {};
  const content = response.message || "";
  const nextIterationOptions = visibleNextIterationOptions(response);
  if (!content && !nextIterationOptions.length) {
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
          next_iteration_options: nextIterationOptions,
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
  chatStatusElement.textContent = "Preparing Agent Plan...";

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
      throw new Error(data.detail || "Agent Plan request failed.");
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
    throw new Error("Build Plan requires a supported Agent Plan action.");
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
    throw new Error(data.detail || "Query plan request failed.");
  }

  return data;
}

async function buildPlanFromChat() {
  if (!normalizedBrief || chatState !== "ready_for_planning") {
    planStatus.textContent = "Complete the Search Brief in chat before building a plan.";
    return null;
  }

  const requestVersion = interactionVersion;
  planRequestInFlight = true;
  setAgentActionDisplayState(
    AGENT_QUEUE_ACTION_BUILD_PLAN,
    "running",
    "Building the visible QueryPlan."
  );
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  updateActionState();
  planStatus.textContent = "Building plan...";
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
      error.message || "Build Plan failed."
    );
    clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
    planStatus.textContent = error.message;
    queryList.innerHTML = "";
    return null;
  } finally {
    if (requestVersion === interactionVersion) {
      planRequestInFlight = false;
      updateActionState();
      if (latestExecutablePlan) {
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
    searchRequestInFlight;
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

  if (data.assistant_message) {
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
    chatStatusElement.textContent = "Request refused by product safety boundaries.";
  } else {
    chatStatusElement.textContent = "Answer the clarification to complete the Search Brief.";
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
  const options = visibleNextIterationOptions(latestAgentResponse);
  const optionText = options.length
    ? ` Current options: ${options
        .slice(0, 3)
        .map((option) => option.label)
        .join("; ")}.`
    : "";
  messages.push({ role: "user", content: userText, localOnly: true });
  messages.push(
    typedChatMessage(
      {
        role: "assistant",
        content:
          `Based on the visible results, improve the next iteration by reviewing the strongest candidates first and then choosing a refined follow-up search.${optionText} I will not rerun search without explicit approval.`,
        kind: "agent_response",
        localOnly: true,
      },
      {
        messageType: AGENT_MESSAGE_TYPES.AGENT_RESPONSE,
        surface: "chat",
        payload: {
          next_iteration_options: options,
        },
      }
    )
  );
  chatStatusElement.textContent = "Results are visible. Follow-up suggestions are grounded in the current results.";
  renderChatMessages();
  updateActionState();
}

async function sendChatTurn(userText) {
  if (isPostResultsFollowUpMessage(userText)) {
    handlePostResultsFollowUp(userText);
    chatInput.focus();
    return;
  }

  const requestVersion = interactionVersion;
  messages.push({ role: "user", content: userText });
  renderChatMessages();
  chatRequestInFlight = true;
  chatStatusElement.textContent = "Updating Search Brief...";
  updateActionState();

  try {
    const response = await fetch("/api/recruiter-chat/turn", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: chatMessagesForBackend(),
        draft_brief: draftBrief,
      }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Recruiter chat request failed.");
    }

    if (requestVersion !== interactionVersion) {
      return;
    }

    updateChatStateFromResponse(data);
  } catch (error) {
    if (requestVersion !== interactionVersion) {
      return;
    }

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
  clearAgentActionDisplayState();
  clearPlannerData();
  clearAgentPlanData();
  chatInput.value = "";
  chatStatusElement.textContent = "Describe the search in Russian or English.";
  planStatus.textContent = "Build a plan from the chat brief.";
  queryList.innerHTML = "";
  reportStatus.textContent = "Run a search to see counts.";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
  resultsStatus.textContent = "Run a search to see deduped candidates.";
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
  reportStatus.textContent = `${reportMode}: ${report.queries_succeeded} of ${report.queries_total} ${pluralize(
    report.queries_total,
    "query",
    "queries"
  )} succeeded.`;

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

  reportGrid.innerHTML = fields
    .map(
      ([label, value]) => `
        <div class="report-metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value ?? 0)}</strong>
        </div>
      `
    )
    .join("");

  contributionList.innerHTML = (report.query_contribution || [])
    .map(
      (item) => `
        <article class="contribution-item ${item.ok ? "" : "is-failed"}">
          <div>
            <strong>${escapeHtml(item.id)}</strong>
            <span>${escapeHtml(item.category)}</span>
          </div>
          <p>
            raw ${escapeHtml(item.raw)}, filtered ${escapeHtml(item.filtered)},
            new ${escapeHtml(item.new_unique_profiles)}, duplicates ${escapeHtml(item.duplicates)}
          </p>
          ${item.error ? `<p class="error-text">${escapeHtml(item.error)}</p>` : ""}
        </article>
      `
    )
    .join("");
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
          class="flag-badge severity-${escapeHtml(flag.severity || "info")}"
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

function renderResults(dedupedResults, report) {
  if (!dedupedResults.length) {
    resultsList.innerHTML = "";
    resultsStatus.textContent = report?.raw_total
      ? `${report.raw_total} raw ${pluralize(
          report.raw_total,
          "result",
          "results"
        )} returned, no unique candidates after filters and dedupe.`
      : "No candidates returned.";
    return;
  }

  resultsStatus.textContent = `Showing ${dedupedResults.length} unique ${pluralize(
    dedupedResults.length,
    "candidate",
    "candidates"
  )}.`;

  resultsList.innerHTML = dedupedResults
    .map((item) => {
      const result = item.result || {};
      const title = result.title || "Untitled result";
      const url = result.url || item.normalized_url || "";
      const content = result.snippet || result.content || "No snippet returned.";
      const name = result.name || "unknown";
      const headline = result.headline || title;
      const qualityScore = result.quality_score ?? "n/a";
      const locationDisplay =
        result.current_location_line ||
        item.current_location_line ||
        result.location_signal_status ||
        item.location_signal_status ||
        "n/a";
      const flagDetails = result.review_flag_details || [];
      const sources = item.query_sources || [];
      const sourceBadges = sources
        .map((source) => `<span title="${escapeHtml(source.role_phrase || source.query)}">${escapeHtml(source.id)}</span>`)
        .join("");

      return `
        <article class="result-item candidate-card">
          <div class="candidate-header">
            <div class="candidate-identity">
              <h3>${escapeHtml(name)}</h3>
              <p>${escapeHtml(headline)}</p>
            </div>
            <div class="candidate-score" aria-label="Quality score">
              <span>Quality</span>
              <strong>${escapeHtml(qualityScore)}</strong>
            </div>
          </div>
          ${
            url
              ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(url)}</a>`
              : ""
          }
          <div class="quality-grid">
            ${renderQualityField("Location", locationDisplay)}
            ${renderQualityField("Role", result.role_display)}
            ${renderQualityField("Tech", result.technology_display)}
            ${renderQualityField("Stack", stackDisplayValue(result))}
            ${renderQualityField("Seniority", result.seniority_display)}
            ${renderQualityField("Source", result.source || "unknown")}
          </div>
          <div class="flag-badges" aria-label="Review flags">
            ${renderFlagBadges(flagDetails)}
          </div>
          <div class="source-badges" aria-label="Query sources">
            ${sourceBadges}
          </div>
          <details>
            <summary>Quality details</summary>
            ${renderScoreBreakdown(result)}
            <p class="result-snippet">${escapeHtml(content)}</p>
          </details>
          <details>
            <summary>Query sources</summary>
            ${renderQuerySourceDetails(sources)}
          </details>
        </article>
      `;
    })
    .join("");
}

async function runStructuredSearch() {
  if (!latestExecutablePlan) {
    resultsStatus.textContent =
      "Build an executable rule-based or fallback plan before approving search.";
    return;
  }
  if (!currentRuntimePendingApproval) {
    resultsStatus.textContent =
      "Wait for runtime approval preparation before approving search.";
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
  resultsStatus.textContent = "Preparing approval for the visible QueryPlan...";
  reportStatus.textContent = "Validating current plan before Tavily execution...";
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";

  try {
    if (!latestPlanFingerprint || !latestQueryPlan?.queries?.length) {
      throw new Error("Current QueryPlan is missing approval fingerprint.");
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
      ? "Searching Tavily with multi-wave..."
      : "Searching Tavily...";
    reportStatus.textContent = multiWaveInput.checked
      ? "Running multi-wave query plan..."
      : "Running query plan...";

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

    renderQueryPlan(searchData.query_plan, {
      planner_mode: "rule_based",
      normalized_brief: normalizedBrief,
    });
    renderReport(searchData.report);
    renderResults(searchData.deduped_results || [], searchData.report);
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

if (statusElement) {
  statusElement.textContent = "Frontend ready";
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

resetChatButton.addEventListener("click", resetChat);
buildPlanButton.addEventListener("click", buildPlanFromChat);
searchButton.addEventListener("click", runStructuredSearch);
multiWaveInput.addEventListener("change", () => {
  clearRuntimeApproval();
  clearAgentActionDisplayState([AGENT_QUEUE_ACTION_RUN_SEARCH]);
  updateActionState();
  if (latestExecutablePlan) {
    void prepareRuntimeSearchAction();
  }
});

resetChat();
