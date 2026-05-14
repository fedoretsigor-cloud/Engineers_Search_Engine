const statusElement = document.querySelector("#app-status");
const searchForm = document.querySelector("#search-form");
const roleFamilySelect = document.querySelector("#role-family");
const technologySelect = document.querySelector("#technology");
const locationInput = document.querySelector("#location");
const profilesOnlyInput = document.querySelector("#profiles-only");
const locationFilterInput = document.querySelector("#location-filter-enabled");
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

function validationMessage(errors) {
  return errors.map((error) => `${error.field}: ${error.message}`).join(" ");
}

function renderPlanErrors(errors) {
  planStatus.textContent = validationMessage(errors);
  queryList.innerHTML = "";
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

function renderQueryPlan(queryPlan) {
  const queries = queryPlan.queries || [];
  planStatus.textContent = `${queryPlan.planner_version} generated ${queries.length} ${pluralize(
    queries.length,
    "query",
    "queries"
  )}.`;

  queryList.innerHTML = queries
    .map((querySlot) => {
      const stack = querySlot.uses_stack?.length
        ? querySlot.uses_stack.join(", ")
        : "none";

      return `
        <article class="query-item">
          <div class="query-heading">
            <strong>${escapeHtml(querySlot.id)}</strong>
            <span>${escapeHtml(querySlot.category)}</span>
          </div>
          <p>${escapeHtml(querySlot.purpose)}</p>
          <code>${escapeHtml(querySlot.query)}</code>
          <p class="query-stack">Stack: ${escapeHtml(stack)}</p>
        </article>
      `;
    })
    .join("");
}

async function refreshQueryPlan() {
  updateLocationFilterToggle();
  updateStackState();
  planStatus.textContent = "Building plan...";
  queryList.innerHTML = "";

  try {
    const response = await fetch("/api/query-plan", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildStructuredRequest()),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Query plan request failed.");
    }

    if (!data.ok) {
      renderPlanErrors(data.errors || []);
      return;
    }

    renderQueryPlan(data.query_plan);
  } catch (error) {
    planStatus.textContent = error.message;
    queryList.innerHTML = "";
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

  reportStatus.textContent = `${report.queries_succeeded} of ${report.queries_total} ${pluralize(
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
    ["Negative location", report.hidden_by_negative_header_location],
    ["Weak location", report.weak_location_history_only],
    ["Unknown location", report.unknown_non_country_domain_location],
    ["Failed queries", report.queries_failed],
  ];

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
      const score = result.score ?? "n/a";
      const name = result.name || "unknown";
      const sources = item.query_sources || [];
      const sourceBadges = sources
        .map((source) => `<span>${escapeHtml(source.id)}</span>`)
        .join("");

      return `
        <article class="result-item">
          <h3>${escapeHtml(title)}</h3>
          <p class="result-meta">
            <span>Name: ${escapeHtml(name)}</span>
            <span>Score: ${escapeHtml(score)}</span>
            <span>Source: ${escapeHtml(result.source || "unknown")}</span>
          </p>
          ${
            url
              ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(url)}</a>`
              : ""
          }
          <p class="result-snippet">${escapeHtml(content)}</p>
          <div class="source-badges" aria-label="Query sources">${sourceBadges}</div>
          <details>
            <summary>Query sources</summary>
            ${(sources || [])
              .map(
                (source) => `
                  <p class="result-snippet">
                    ${escapeHtml(source.id)}: ${escapeHtml(source.query)}
                  </p>
                `
              )
              .join("")}
          </details>
        </article>
      `;
    })
    .join("");
}

async function runStructuredSearch() {
  if (!updateStackState()) {
    resultsStatus.textContent = "Select at least one stack item before searching.";
    resultsList.innerHTML = "";
    return;
  }

  searchButton.disabled = true;
  refreshPlanButton.disabled = true;
  resultsStatus.textContent = "Searching Tavily...";
  reportStatus.textContent = "Running query plan...";
  resultsList.innerHTML = "";
  reportGrid.innerHTML = "";
  contributionList.innerHTML = "";

  try {
    const response = await fetch("/api/structured-search", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildStructuredRequest()),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Structured search request failed.");
    }

    if (data.errors?.length) {
      renderSearchErrors(data.errors);
      return;
    }

    renderQueryPlan(data.query_plan);
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

[roleFamilySelect, technologySelect, locationInput, profilesOnlyInput].forEach((input) => {
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
