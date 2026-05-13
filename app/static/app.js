const statusElement = document.querySelector("#app-status");
const searchForm = document.querySelector("#search-form");
const mainAnchorInput = document.querySelector("#main-anchor");
const additionalAnchorsInput = document.querySelector("#additional-anchors");
const stackInput = document.querySelector("#stack");
const locationInput = document.querySelector("#location");
const booleanQueryInput = document.querySelector("#boolean-query");
const rebuildQueryButton = document.querySelector("#rebuild-query");
const resultsStatus = document.querySelector("#results-status");
const resultsList = document.querySelector("#results-list");
const searchButton = searchForm.querySelector(".primary-button");

function parseCommaList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function quoteTerm(term) {
  return `"${term.replaceAll('"', '\\"')}"`;
}

function orGroup(terms) {
  if (!terms.length) {
    return "";
  }
  if (terms.length === 1) {
    return quoteTerm(terms[0]);
  }
  return `(${terms.map(quoteTerm).join(" OR ")})`;
}

function andGroup(terms) {
  if (!terms.length) {
    return "";
  }
  return terms.map(quoteTerm).join(" AND ");
}

function buildBooleanQuery() {
  const mainAnchor = mainAnchorInput.value.trim();
  const additionalAnchors = parseCommaList(additionalAnchorsInput.value);
  const stack = parseCommaList(stackInput.value);
  const location = locationInput.value.trim();

  return [
    "site:linkedin.com/in",
    mainAnchor ? quoteTerm(mainAnchor) : "",
    orGroup(additionalAnchors),
    orGroup(stack),
    location ? quoteTerm(location) : "",
  ]
    .filter(Boolean)
    .join(" AND ");
}

function rebuildBooleanQuery() {
  booleanQueryInput.value = buildBooleanQuery();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderResults(results, counts) {
  if (!results.length) {
    resultsList.innerHTML = "";
    const rawCount = counts?.raw ?? 0;
    resultsStatus.textContent = rawCount
      ? `${rawCount} raw result${rawCount === 1 ? "" : "s"} returned, but none passed required filters.`
      : "No Tavily results returned.";
    return;
  }

  const rawCount = counts?.raw ?? results.length;
  resultsStatus.textContent = `Showing ${results.length} relevant result${
    results.length === 1 ? "" : "s"
  } from ${rawCount} raw Tavily result${rawCount === 1 ? "" : "s"}.`;
  resultsList.innerHTML = results
    .map((result) => {
      const title = result.title || "Untitled result";
      const url = result.url || "";
      const content = result.snippet || result.content || "No snippet returned.";
      const score = result.score ?? "n/a";
      const name = result.name || "unknown";
      const reason = result.relevance_reason || "No relevance reason returned.";

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
          <p class="result-snippet">${escapeHtml(reason)}</p>
        </article>
      `;
    })
    .join("");
}

if (statusElement) {
  statusElement.textContent = "Frontend ready";
}

rebuildBooleanQuery();

[mainAnchorInput, additionalAnchorsInput, stackInput, locationInput].forEach((input) => {
  input.addEventListener("input", rebuildBooleanQuery);
});

rebuildQueryButton.addEventListener("click", rebuildBooleanQuery);

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = booleanQueryInput.value.trim();

  if (!query) {
    resultsStatus.textContent = "Enter a Boolean query before searching.";
    resultsList.innerHTML = "";
    return;
  }

  searchButton.disabled = true;
  resultsStatus.textContent = "Searching Tavily...";
  resultsList.innerHTML = "";

  fetch("/api/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      max_results: 20,
      main_anchor: mainAnchorInput.value.trim(),
      additional_anchors: parseCommaList(additionalAnchorsInput.value),
      stack: parseCommaList(stackInput.value),
      location: locationInput.value.trim(),
    }),
  })
    .then(async (response) => {
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Search request failed.");
      }
      renderResults(data.relevant_results || [], data.counts);
    })
    .catch((error) => {
      resultsStatus.textContent = error.message;
      resultsList.innerHTML = "";
    })
    .finally(() => {
      searchButton.disabled = false;
    });
});
