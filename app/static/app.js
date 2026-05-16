const statusElement = document.querySelector("#app-status");
const searchForm = document.querySelector("#search-form");
const roleFamilySelect = document.querySelector("#role-family");
const technologySelect = document.querySelector("#technology");
const locationInput = document.querySelector("#location");
const plannerModeSelect = document.querySelector("#planner-mode");
const profilesOnlyInput = document.querySelector("#profiles-only");
const locationFilterInput = document.querySelector("#location-filter-enabled");
const multiWaveInput = document.querySelector("#multi-wave-enabled");
const refreshPlanButton = document.querySelector("#refresh-plan");
const stackMessage = document.querySelector("#stack-message");
const planStatus = document.querySelector("#plan-status");
const queryList = document.querySelector("#query-list");
const reportStatus = document.querySelector("#report-status");
const reportGrid = document.querySelector("#report-grid");
const contributionList = document.querySelector("#contribution-list");
const resultsStatus = document.querySelector("#results-status");
const resultsList = document.querySelector("#results-list");
const searchButton = searchForm.querySelector(".primary-button");
const stackInputs = Array.from(document.querySelectorAll('input[name="stack"]'));

let planRefreshTimer = null;
let locationFilterTouched = false;
let latestPlannerData = null;
let latestQueryPlan = null;
let latestPlanFingerprint = null;

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

function selectedStack() {
  return stackInputs.filter((input) => input.checked).map((input) => input.value);
}

function isUkraineLocation() {
  return locationInput.value.trim().toLowerCase() === "ukraine";
}

function buildStructuredRequest() {
  return {
    role_family: roleFamilySelect.value,
    technology: technologySelect.value,
    stack: selectedStack(),
    location: locationInput.value.trim(),
    linkedin_profiles_only: profilesOnlyInput.checked,
    location_filter_enabled: locationFilterInput.checked,
  };
}

function buildSearchBrief() {
  const stack = selectedStack();
  const roleFamily = roleFamilySelect.value;
  const technology = technologySelect.value;
  const location = locationInput.value.trim();
  const missingFields = [];
  const clarifyingQuestions = [];

  if (!stack.length) {
    missingFields.push("stack");
    clarifyingQuestions.push(
      "Which Java stack signals are important for this search: Spring, Kafka, AWS, Hibernate, or something else?"
    );
  }

  return {
    source_text: `${roleFamily} with ${technology} in ${location}`,
    brief_status: missingFields.length ? "needs_clarification" : "ready_for_planning",
    role_family: roleFamily,
    technology,
    stack,
    location,
    seniority: null,
    must_have: technology ? [technology] : [],
    nice_to_have: stack,
    exclusions: [],
    search_depth: multiWaveInput.checked ? "deep" : "standard",
    profile_sources: ["linkedin_public"],
    notes: null,
    missing_fields: missingFields,
    clarifying_questions: clarifyingQuestions,
    assumptions: [],
  };
}

function buildAgentQueryPlanRequest() {
  return {
    planner_mode: plannerModeSelect.value,
    search_brief: buildSearchBrief(),
  };
}

function buildSearchRequest(executionApproval = null) {
  const request = buildStructuredRequest();

  if (executionApproval) {
    request.execution_approval = executionApproval;
  }

  if (!multiWaveInput.checked) {
    return request;
  }

  return {
    ...request,
    ...MULTI_WAVE_DEFAULTS,
  };
}

function queryPlanFromPlannerData(data = {}) {
  return data.query_plan || data.fallback_query_plan || data.draft_query_plan || null;
}

function rememberPlannerData(data = {}) {
  latestPlannerData = data;
  latestQueryPlan = queryPlanFromPlannerData(data);
  latestPlanFingerprint = data.plan_fingerprint || latestQueryPlan?.plan_fingerprint || null;
}

function clearPlannerData() {
  latestPlannerData = null;
  latestQueryPlan = null;
  latestPlanFingerprint = null;
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

function validationMessage(errors) {
  return errors.map((error) => `${error.field}: ${error.message}`).join(" ");
}

function renderPlanErrors(errors) {
  planStatus.textContent = validationMessage(errors);
  queryList.innerHTML = "";
}

function displayList(values = [], fallback = "none") {
  return values.length ? values.join(", ") : fallback;
}

function plannerLabel(value) {
  const labels = {
    rule_based: "Rule-based",
    ai: "AI draft",
    ai_with_fallback: "AI with fallback",
    validated_not_executable: "Validated, not executable",
    rejected: "Rejected",
    rule_based_fallback: "Rule-based fallback",
    needs_clarification: "Needs clarification",
  };

  return labels[value] || displayValue(value);
}

function renderBriefSummary(brief = {}) {
  if (!brief || !Object.keys(brief).length) {
    return "";
  }

  const fields = [
    ["Role", brief.role_family],
    ["Technology", brief.technology],
    ["Stack", displayList(brief.stack || [])],
    ["Location", brief.location],
    ["Depth", brief.search_depth],
  ];

  return `
    <div class="planner-section">
      <h3>Search Brief</h3>
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
        brief.clarifying_questions?.length
          ? `<p class="planner-note">${escapeHtml(brief.clarifying_questions.join(" "))}</p>`
          : ""
      }
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
  const mode = data.planner_mode || plannerModeSelect.value;
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

function renderSearchErrors(errors) {
  const message = validationMessage(errors);
  resultsStatus.textContent = message;
  reportStatus.textContent = message;
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";
}

function updateLocationFilterToggle() {
  const isUkraine = isUkraineLocation();
  locationFilterInput.disabled = !isUkraine;

  if (!isUkraine) {
    locationFilterInput.checked = false;
    return;
  }

  if (!locationFilterTouched) {
    locationFilterInput.checked = true;
  }
}

function updateStackState() {
  const chosenStack = selectedStack();
  const reachedLimit = chosenStack.length >= 3;

  stackInputs.forEach((input) => {
    input.disabled = !input.checked && reachedLimit;
  });

  if (!chosenStack.length) {
    stackMessage.textContent = "Select at least one stack item.";
    searchButton.disabled = false;
    return false;
  }

  stackMessage.textContent = `${chosenStack.length} selected.`;
  return true;
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
    return;
  }

  renderQueryPlan(queryPlan, data);
}

async function fetchAgentQueryPlan() {
  const response = await fetch("/api/agent/query-plan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(buildAgentQueryPlanRequest()),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Query plan request failed.");
  }

  return data;
}

async function refreshQueryPlan() {
  updateLocationFilterToggle();
  updateStackState();
  planStatus.textContent = "Building plan...";
  queryList.innerHTML = "";

  try {
    const data = await fetchAgentQueryPlan();

    if (!data.ok) {
      clearPlannerData();
      renderPlanErrors(data.errors || []);
      return;
    }

    renderAgentQueryPlan(data);
    return data;
  } catch (error) {
    clearPlannerData();
    planStatus.textContent = error.message;
    queryList.innerHTML = "";
    return null;
  }
}

function schedulePlanRefresh() {
  window.clearTimeout(planRefreshTimer);
  planRefreshTimer = window.setTimeout(refreshQueryPlan, 180);
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
  if (plannerModeSelect.value !== "rule_based") {
    resultsStatus.textContent =
      "AI planner previews cannot be executed yet. Switch Planner mode to Rule-based to run the current search.";
    reportStatus.textContent = "Search execution still requires the future approval flow.";
    return;
  }

  if (!updateStackState()) {
    resultsStatus.textContent = "Select at least one stack item before searching.";
    resultsList.innerHTML = "";
    return;
  }

  searchButton.disabled = true;
  refreshPlanButton.disabled = true;
  resultsStatus.textContent = "Preparing approval for the visible QueryPlan...";
  reportStatus.textContent = "Validating current plan before Tavily execution...";
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";

  try {
    const planData = await fetchAgentQueryPlan();
    if (!planData.ok) {
      clearPlannerData();
      renderPlanErrors(planData.errors || []);
      resultsStatus.textContent = validationMessage(planData.errors || []);
      reportStatus.textContent = "Search was not approved.";
      return;
    }

    renderAgentQueryPlan(planData);

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

    if (!response.ok) {
      throw new Error(data.detail || "Structured search request failed.");
    }

    if (data.errors?.length) {
      renderSearchErrors(data.errors);
      return;
    }

    renderQueryPlan(data.query_plan, {
      planner_mode: "rule_based",
    });
    renderReport(data.report);
    renderResults(data.deduped_results || [], data.report);
  } catch (error) {
    resultsStatus.textContent = error.message;
    reportStatus.textContent = error.message;
    resultsList.innerHTML = "";
    reportGrid.innerHTML = "";
    contributionList.innerHTML = "";
  } finally {
    searchButton.disabled = false;
    refreshPlanButton.disabled = false;
  }
}

if (statusElement) {
  statusElement.textContent = "Frontend ready";
}

locationFilterInput.addEventListener("change", () => {
  locationFilterTouched = true;
  schedulePlanRefresh();
});

[
  roleFamilySelect,
  technologySelect,
  locationInput,
  profilesOnlyInput,
  plannerModeSelect,
  multiWaveInput,
].forEach((input) => {
  input.addEventListener("input", schedulePlanRefresh);
  input.addEventListener("change", schedulePlanRefresh);
});

stackInputs.forEach((input) => {
  input.addEventListener("change", () => {
    updateStackState();
    schedulePlanRefresh();
  });
});

refreshPlanButton.addEventListener("click", refreshQueryPlan);

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runStructuredSearch();
});

updateLocationFilterToggle();
updateStackState();
refreshQueryPlan();
