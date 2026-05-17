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

let messages = [];
let draftBrief = null;
let normalizedBrief = null;
let chatState = "drafting";
let recommendedPlannerMode = "ai_with_fallback";
let adaptedStructuredRequest = null;
let latestPlannerData = null;
let latestQueryPlan = null;
let latestPlanFingerprint = null;
let latestExecutablePlan = false;
let chatRequestInFlight = false;
let planRequestInFlight = false;
let searchRequestInFlight = false;
let interactionVersion = 0;

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

function plannerLabel(value) {
  const labels = {
    rule_based: "Rule-based",
    ai: "AI draft",
    ai_with_fallback: "AI with fallback",
    draft_query_plan: "Draft QueryPlan",
    validated_not_executable: "Validated, not executable",
    rejected: "Rejected",
    rule_based_fallback: "Rule-based fallback",
    needs_clarification: "Needs clarification",
  };

  return labels[value] || displayValue(value);
}

function validationMessage(errors = []) {
  return errors.map((error) => `${error.field}: ${error.message}`).join(" ");
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
  syncExecutionControlsFromPlan();
  updateActionState();
}

function clearPlannerData() {
  latestPlannerData = null;
  latestQueryPlan = null;
  latestPlanFingerprint = null;
  adaptedStructuredRequest = null;
  latestExecutablePlan = false;
  updateActionState();
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

function buildExecutionApproval() {
  const queryCount = latestQueryPlan?.queries?.length || 0;

  return {
    approval_status: "approved",
    approved_action: multiWaveInput.checked
      ? "run_multi_wave_search"
      : "run_single_wave_search",
    approved_planner_mode: "rule_based",
    approved_query_count: queryCount,
    approved_plan_fingerprint: latestPlanFingerprint,
  };
}

function searchEndpoint() {
  return multiWaveInput.checked
    ? "/api/structured-search/multi-wave"
    : "/api/structured-search";
}

function buildSearchRequest(executionApproval = null) {
  if (!adaptedStructuredRequest) {
    throw new Error("Build Plan before approving search.");
  }

  const request = {
    ...adaptedStructuredRequest,
    execution_approval: executionApproval,
  };

  if (!multiWaveInput.checked) {
    return request;
  }

  return {
    ...request,
    ...MULTI_WAVE_DEFAULTS,
  };
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
    .map(
      (message) => `
        <article class="chat-message ${
          message.role === "user" ? "user-message" : "assistant-message"
        }">
          <span>${escapeHtml(message.role === "user" ? "You" : "AI")}</span>
          <p>${escapeHtml(message.content)}</p>
        </article>
      `
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
        <span>${escapeHtml(plannerLabel(status))}</span>
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
  planStatus.textContent = validationMessage(errors);
  queryList.innerHTML = renderValidationErrors(errors);
}

function renderSearchErrors(errors = []) {
  const message = validationMessage(errors);
  resultsStatus.textContent = message;
  reportStatus.textContent = message;
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
}

function renderQueryPlan(queryPlan, plannerData = null) {
  const queries = queryPlan.queries || [];
  const modeText = plannerData?.planner_mode
    ? `${plannerLabel(plannerData.planner_mode)}: `
    : "";
  planStatus.textContent = `${modeText}${queryPlan.planner_version} generated ${queries.length} ${pluralize(
    queries.length,
    "query",
    "queries"
  )}.`;

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
      "Visible rule-based plan is ready. Approve & Search will run through the backend approval gate.";
    return;
  }

  resultsStatus.textContent =
    "Plan preview is not executable yet. Use a rule-based or rule-based fallback plan to search.";
}

async function fetchAgentQueryPlan() {
  const response = await fetch("/api/agent/query-plan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      planner_mode: recommendedPlannerMode || "ai_with_fallback",
      search_brief: normalizedBrief,
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
    planStatus.textContent = error.message;
    queryList.innerHTML = "";
    return null;
  } finally {
    if (requestVersion === interactionVersion) {
      planRequestInFlight = false;
      updateActionState();
    }
  }
}

function updateActionState() {
  const isBusy = chatRequestInFlight || planRequestInFlight || searchRequestInFlight;
  const canBuildPlan =
    chatState === "ready_for_planning" && Boolean(normalizedBrief) && !isBusy;
  buildPlanButton.disabled = !canBuildPlan;
  searchButton.disabled = !latestExecutablePlan || isBusy;
  sendChatButton.disabled = isBusy;
  chatInput.disabled = isBusy;
}

function updateChatStateFromResponse(data = {}) {
  chatState = data.state || "needs_clarification";
  recommendedPlannerMode = data.recommended_planner_mode || "ai_with_fallback";
  draftBrief = data.normalized_brief || draftBrief;
  normalizedBrief = data.normalized_brief || null;
  clearPlannerData();

  if (data.assistant_message) {
    messages.push({ role: "assistant", content: data.assistant_message });
  }

  if (chatState === "ready_for_planning") {
    chatStatusElement.textContent = "Search Brief ready. Build a plan to continue.";
  } else if (chatState === "refused") {
    chatStatusElement.textContent = "Request refused by product safety boundaries.";
  } else {
    chatStatusElement.textContent = "Answer the clarification to complete the Search Brief.";
  }

  renderChatMessages();
  renderBriefSummaryCard(normalizedBrief, chatState);
  updateActionState();
}

async function sendChatTurn(userText) {
  const requestVersion = interactionVersion;
  messages.push({ role: "user", content: userText });
  renderChatMessages();
  chatRequestInFlight = true;
  clearPlannerData();
  chatStatusElement.textContent = "Updating Search Brief...";
  updateActionState();

  try {
    const response = await fetch("/api/recruiter-chat/turn", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages,
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

    messages.push({
      role: "assistant",
      content: error.message,
    });
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
  recommendedPlannerMode = "ai_with_fallback";
  chatRequestInFlight = false;
  planRequestInFlight = false;
  searchRequestInFlight = false;
  clearPlannerData();
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

  const requestVersion = interactionVersion;
  searchRequestInFlight = true;
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

    const executionApproval = buildExecutionApproval();

    resultsStatus.textContent = multiWaveInput.checked
      ? "Searching Tavily with multi-wave..."
      : "Searching Tavily...";
    reportStatus.textContent = multiWaveInput.checked
      ? "Running multi-wave query plan..."
      : "Running query plan...";

    const response = await fetch(searchEndpoint(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildSearchRequest(executionApproval)),
    });
    const data = await response.json();
    if (requestVersion !== interactionVersion) {
      return;
    }

    if (!response.ok) {
      throw new Error(data.detail || "Structured search request failed.");
    }

    if (data.errors?.length) {
      renderSearchErrors(data.errors);
      return;
    }

    renderQueryPlan(data.query_plan, {
      planner_mode: "rule_based",
      normalized_brief: normalizedBrief,
    });
    renderReport(data.report);
    renderResults(data.deduped_results || [], data.report);
  } catch (error) {
    if (requestVersion !== interactionVersion) {
      return;
    }

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
multiWaveInput.addEventListener("change", updateActionState);

resetChat();
