const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const repoRoot = path.resolve(__dirname, "..");
const helperPath = path.join(repoRoot, "app", "static", "candidate_workspace.js");
const indexPath = path.join(repoRoot, "app", "static", "index.html");

const context = {
  console,
  Date,
  URL,
  window: {},
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync(helperPath, "utf8"), context, {
  filename: helperPath,
});

const workspace = context.window.CandidateWorkspace;
assert.ok(workspace, "CandidateWorkspace helper should be exported on window");

const inputResults = [
  {
    normalized_url: "ua.linkedin.com/in/anna-java",
    current_location_status: "target_location",
    stack_fit: "selected_stack_found",
    result: {
      name: "Anna Java",
      title: "Senior Java Developer - LinkedIn",
      url: "https://example.com/not-used",
      quality_score: 86,
      role_display: "Backend Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      stack_evidence: [{ term: "Spring", source: "candidate_text", evidence_type: "direct_text" }],
      selected_stack_terms_found: ["Spring"],
      current_location_line: "Kyiv, Ukraine",
      location_signal_terms: ["Kyiv", "Ukraine"],
      quality_score_breakdown: [
        { component: "role", points: 25, max_points: 25, fit: "target_or_close_role" },
        { component: "stack", points: 20, max_points: 20, fit: "selected_stack_found" },
        { component: "location", points: 25, max_points: 25, fit: "target_location" },
        { component: "identity", points: 5, max_points: 5, fit: "complete" },
      ],
      seniority_display: "Senior",
      review_flag_details: [],
    },
    query_sources: [{ id: "Q01", category: "role_based", query: "site:linkedin.com/in Java Ukraine" }],
  },
  {
    normalized_url: "https://www.linkedin.com/in/bohdan-backend",
    current_location_status: "unknown_current_location",
    stack_fit: "stack_query_source_only",
    result: {
      name: "Bohdan Backend",
      title: "Java Engineer",
      quality_score: 51,
      role_display: "Backend Engineer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      stack_evidence: [{ term: "Kafka", source: "query_source", evidence_type: "stack_query_group" }],
      quality_score_breakdown: [{ component: "stack", points: 6, max_points: 20, fit: "stack_query_source_only" }],
      seniority_display: "Middle",
      review_flag_details: [{ code: "missing_selected_stack", label: "Stack not visible", severity: "critical" }],
    },
  },
  {
    normalized_url: "https://cz.linkedin.com/in/carla-java",
    current_location_status: "foreign_current_location",
    stack_fit: "missing_selected_stack",
    result: {
      name: "Carla JVM",
      title: "Java Developer",
      quality_score: 28,
      role_display: "Java Developer",
      role_fit: "target_or_close_role",
      technology_display: "Java",
      technology_fit: "exact",
      seniority_display: "Junior",
      review_flag_details: [{ code: "medium_confidence", label: "Medium confidence", severity: "medium" }],
    },
  },
  {
    result: {
      name: "Fallback URL",
      url: "https://linkedin.com/in/fallback-profile",
      quality_score: 72,
    },
  },
  {
    normalized_url: "https://linkedin.com.evil/in/not-safe",
    result: {
      name: "Unsafe Host",
      url: "javascript:alert(1)",
      quality_score: "not numeric",
    },
  },
];

const candidates = workspace.mapDedupedResultsToWorkspaceCandidates(inputResults);
assert.strictEqual(candidates.length, 5);
assert.strictEqual(candidates[0].candidate_id, "ua.linkedin.com/in/anna-java");
assert.strictEqual(candidates[0].profile_href, "https://ua.linkedin.com/in/anna-java");
assert.strictEqual(candidates[3].profile_href, "https://linkedin.com/in/fallback-profile");
assert.strictEqual(candidates[3].identity.is_stable_identity, false);
assert.strictEqual(candidates[4].profile_href, "");
assert.strictEqual(candidates[0].quality_bucket, "high");
assert.strictEqual(candidates[1].quality_bucket, "medium");
assert.strictEqual(candidates[2].quality_bucket, "low");
assert.strictEqual(candidates[1].review_flags[0].severity, "info", "unknown severities should be normalized");
assert.strictEqual(workspace.CANDIDATE_EXPLANATION_VERSION, "candidate_explanation_v1");
assert.ok(workspace.buildCandidateExplanation, "Candidate explanation helper should be exported");
assert.ok(workspace.buildWorkspaceExportModel, "Workspace export model helper should be exported");
assert.ok(workspace.serializeWorkspaceExportCsv, "Workspace CSV export serializer should be exported");
assert.ok(workspace.serializeWorkspaceExportMarkdown, "Workspace Markdown export serializer should be exported");

function explanationCodes(explanation, field) {
  return explanation[field].map((item) => item.code);
}

function allExplanationReasons(explanation) {
  return [
    ...explanation.positive_signals,
    ...explanation.cautions,
    ...explanation.evidence_items,
  ];
}

const explanationAllowlist = new Set(Object.values(workspace.EXPLANATION_REASON_CODES));
const strongBefore = JSON.stringify(candidates[0]);
const strongExplanation = workspace.buildCandidateExplanation(candidates[0]);
assert.strictEqual(strongExplanation.version, "candidate_explanation_v1");
assert.strictEqual(strongExplanation.source, "deterministic_workspace_facts");
assert.ok(strongExplanation.summary.includes("strong returned fit signals"));
assert.ok(explanationCodes(strongExplanation, "positive_signals").includes("quality_score_high"));
assert.ok(explanationCodes(strongExplanation, "positive_signals").includes("target_location"));
assert.ok(explanationCodes(strongExplanation, "positive_signals").includes("stack_confirmed"));
assert.ok(explanationCodes(strongExplanation, "evidence_items").includes("query_source"));
assert.ok(explanationCodes(strongExplanation, "evidence_items").includes("quality_component"));
assert.ok(strongExplanation.positive_signals.length <= 3);
assert.ok(strongExplanation.cautions.length <= 3);
assert.ok(strongExplanation.evidence_items.length <= 4);
assert.strictEqual(JSON.stringify(candidates[0]), strongBefore, "explanation helper should not mutate candidate facts");
allExplanationReasons(strongExplanation).forEach((reason) => {
  assert.ok(explanationAllowlist.has(reason.code), `unexpected explanation reason code ${reason.code}`);
  assert.strictEqual(typeof reason.label, "string");
  assert.ok(!/[<>]/.test(reason.label), "explanation labels should be plain text, not HTML");
});

const queryOnlyExplanation = workspace.buildCandidateExplanation(candidates[1]);
assert.ok(explanationCodes(queryOnlyExplanation, "cautions").includes("stack_query_source_only"));
assert.ok(!explanationCodes(queryOnlyExplanation, "positive_signals").includes("stack_confirmed"));
assert.ok(explanationCodes(queryOnlyExplanation, "positive_signals").includes("role_or_technology_visible"));
assert.ok(queryOnlyExplanation.summary.includes("not confirmed"));

const foreignExplanation = workspace.buildCandidateExplanation(candidates[2]);
assert.ok(explanationCodes(foreignExplanation, "cautions").includes("location_foreign_or_mismatch"));
assert.ok(!explanationCodes(foreignExplanation, "cautions").includes("location_unknown_or_weak"));
assert.ok(explanationCodes(foreignExplanation, "cautions").includes("review_flags_present"));
assert.ok(!explanationCodes(foreignExplanation, "cautions").includes("quality_score_missing"));

const unsafeExplanation = workspace.buildCandidateExplanation(candidates[4]);
assert.ok(explanationCodes(unsafeExplanation, "cautions").includes("quality_score_missing"));
assert.ok(explanationCodes(unsafeExplanation, "cautions").includes("profile_href_missing_or_unsafe"));

const nonJavaSample = workspace.mapDedupedResultToWorkspaceCandidate(
  {
    normalized_url: "pl.linkedin.com/in/frontend-person",
    current_location_status: "unknown_current_location",
    stack_fit: "missing_selected_stack",
    result: {
      name: "Frontend Person",
      title: "React Engineer",
      quality_score: 45,
      role_fit: "missing_role",
      technology_fit: "related_only",
      selected_stack_terms_found: [],
      missing_selected_stack_terms: ["GraphQL"],
    },
  },
  8
);
const nonJavaExplanation = workspace.buildCandidateExplanation(nonJavaSample);
assert.ok(explanationCodes(nonJavaExplanation, "cautions").includes("stack_not_visible"));
assert.ok(!explanationCodes(nonJavaExplanation, "positive_signals").includes("role_or_technology_visible"));
assert.ok(!JSON.stringify(nonJavaExplanation).includes("Java"));
assert.ok(!JSON.stringify(nonJavaExplanation).includes("Ukraine"));

const sparseExplanation = workspace.buildCandidateExplanation({});
assert.strictEqual(sparseExplanation.source, "deterministic_workspace_facts");
assert.ok(explanationCodes(sparseExplanation, "cautions").includes("quality_score_missing"));

const explanationWithReviewState = workspace.buildCandidateExplanation(
  Object.assign({}, candidates[0], {
    review_status: "not_a_fit",
    shortlisted: true,
    note: "<script>alert(1)</script>",
  })
);
assert.deepStrictEqual(explanationWithReviewState, strongExplanation);

const runIdA = workspace.createWorkspaceRunId({
  idempotency_key: "idem",
  tool_call_id: "tool",
  plan_fingerprint: "plan",
  run_counter: 1,
});
const runIdB = workspace.createWorkspaceRunId({
  idempotency_key: "idem",
  tool_call_id: "tool",
  plan_fingerprint: "plan",
  run_counter: 2,
});
assert.notStrictEqual(runIdA, runIdB);

let reviewState = workspace.createReviewStateForCandidates(candidates, {
  [candidates[0].candidate_id]: { status: "bad-status", shortlisted: true, note: "keep" },
});
assert.strictEqual(reviewState[candidates[0].candidate_id].status, "new");
assert.strictEqual(workspace.isWorkspaceCandidateShortlisted(reviewState[candidates[0].candidate_id]), false);
reviewState = workspace.setWorkspaceReviewStatus(reviewState, candidates[0].candidate_id, "reviewing");
assert.strictEqual(reviewState[candidates[0].candidate_id].status, "reviewing");
reviewState = workspace.setWorkspaceReviewStatus(reviewState, candidates[0].candidate_id, "invalid");
assert.strictEqual(reviewState[candidates[0].candidate_id].status, "reviewing");
reviewState = workspace.toggleWorkspaceShortlist(reviewState, candidates[1].candidate_id, true);
assert.strictEqual(reviewState[candidates[1].candidate_id].status, "shortlisted");
assert.strictEqual(workspace.isWorkspaceCandidateShortlisted(reviewState[candidates[1].candidate_id]), true);
reviewState = workspace.toggleWorkspaceShortlist(reviewState, candidates[1].candidate_id, false);
assert.strictEqual(reviewState[candidates[1].candidate_id].status, "reviewing");
assert.strictEqual(workspace.isWorkspaceCandidateShortlisted(reviewState[candidates[1].candidate_id]), false);
reviewState = workspace.setWorkspaceCandidateNote(
  reviewState,
  candidates[0].candidate_id,
  "x".repeat(workspace.NOTE_MAX_LENGTH + 25)
);
assert.strictEqual(reviewState[candidates[0].candidate_id].note.length, workspace.NOTE_MAX_LENGTH);
reviewState = workspace.setWorkspaceReviewStatus(reviewState, candidates[2].candidate_id, "shortlisted");
assert.strictEqual(workspace.reviewStatusClassName("unsafe value"), "review-status-new");
assert.strictEqual(workspace.reviewStatusLabel("shortlisted"), "Shortlisted");

const beforeView = JSON.stringify(candidates);
assert.deepStrictEqual(
  workspace.applyWorkspaceView(candidates, { stack_filter: "confirmed" }, reviewState).map((item) => item.display_name),
  ["Anna Java"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { quality_filter: "80_plus" }, reviewState)
    .map((item) => item.display_name),
  ["Anna Java"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { quality_filter: "70_plus" }, reviewState)
    .map((item) => item.display_name),
  ["Anna Java", "Fallback URL"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { quality_filter: "not-real", stack_filter: "confirmed" }, reviewState)
    .map((item) => item.display_name),
  ["Anna Java"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { review_flag_filter: "has_flags" }, reviewState)
    .map((item) => item.display_name),
  ["Bohdan Backend", "Carla JVM"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { review_flag_filter: "high_medium" }, reviewState)
    .map((item) => item.display_name),
  ["Carla JVM"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { location_filter: "target" }, reviewState)
    .map((item) => item.display_name),
  ["Anna Java"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { sort_mode: "quality_desc" }, reviewState)
    .map((item) => item.display_name)
    .slice(0, 3),
  ["Anna Java", "Fallback URL", "Bohdan Backend"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { sort_mode: "quality_asc" }, reviewState)
    .map((item) => item.display_name)
    .slice(0, 4),
  ["Carla JVM", "Bohdan Backend", "Fallback URL", "Anna Java"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { review_status_filter: "shortlisted" }, reviewState)
    .map((item) => item.display_name),
  ["Carla JVM"]
);
assert.deepStrictEqual(
  workspace
    .applyWorkspaceView(candidates, { shortlist_filter: "shortlisted" }, reviewState)
    .map((item) => item.display_name),
  ["Carla JVM"]
);
assert.strictEqual(JSON.stringify(candidates), beforeView, "workspace view helpers should not mutate candidates");

assert.strictEqual(workspace.normalizeExportScope("unknown"), "visible");
assert.strictEqual(workspace.normalizeExportScope("shortlisted"), "shortlisted");
assert.strictEqual(workspace.normalizeExportFormat("unknown"), "csv");
assert.strictEqual(workspace.normalizeExportFormat("markdown"), "markdown");
assert.strictEqual(workspace.workspaceExportMimeType("csv"), "text/csv;charset=utf-8");
assert.strictEqual(workspace.workspaceExportMimeType("markdown"), "text/markdown;charset=utf-8");

function cloneCandidate(candidate) {
  return JSON.parse(JSON.stringify(candidate));
}

const fixedExportDate = new Date(2026, 4, 22, 13, 4, 5);
const exportCandidateA = Object.assign(cloneCandidate(candidates[0]), {
  candidate_id: "candidate-a",
  order_index: 2,
  display_name: '=Anna, "Java"',
  headline:
    "Senior Java Developer anna@example.com +380 (67) 123-45-67 https://evil.example\nSecond line",
  profile_href: "https://www.linkedin.com/in/foo/details/experience",
  identity: {
    is_stable_identity: true,
    safe_profile_href: "https://www.linkedin.com/in/foo/details/experience",
  },
  review_flags: [{ code: "needs_review", label: "Check https://flag.example" }],
  query_sources: [
    { id: "Q01", category: "role_based", query: "raw query should not export" },
    { category: "fallback_category", query: "raw category query should not export" },
    { id: "Q01", category: "duplicate" },
    { query: "missing id should not export" },
    { id: "unknown" },
  ],
  snippet:
    "Contact anna@example.com or +380 (67) 123-45-67. Java 17 Spring 6 Node.js 20 .NET 6 C# 2024 Q01 5+ years 10 years +5 quality points C++ https://snippet.example www.example.com",
});
const exportCandidateB = Object.assign(cloneCandidate(candidates[1]), {
  candidate_id: "candidate-b",
  order_index: 1,
  profile_href: "http://ua.linkedin.com/in/foo/",
  identity: { is_stable_identity: true, safe_profile_href: "http://ua.linkedin.com/in/foo/" },
  has_quality_score: false,
  quality_score: 999,
});
const exportCandidateC = Object.assign(cloneCandidate(candidates[4]), {
  candidate_id: { unsafe: "candidate-c" },
  order_index: 1,
  display_name: "Unsafe <script>alert(1)</script> [x](https://bad.example)",
  headline: "# Heading | table https://bad.example",
  profile_url: "https://linkedin.com/in/display-only-should-not-export",
  profile_href: "https://linkedin.com.evil/in/foo",
  identity: { is_stable_identity: true, safe_profile_href: "https://linkedin.com.evil/in/foo" },
  query_sources: [{ query: "raw only" }, null, { id: "" }],
  review_flags: [{ code: "unsafe", label: { nested: "skip" } }, { label: "Label only" }, { raw: true }],
  snippet: "<b>HTML</b>\nlinkedin.com/in/not-trusted",
});
const exportCandidates = [exportCandidateA, exportCandidateB, exportCandidateC];
const exportVisibleCandidates = [exportCandidateC, exportCandidateA];
const exportReviewState = {
  "candidate-a": {
    status: "reviewing",
    note: "\t=cmd\nhttps://note.example and linkedin.com/in/not-profile note.user@example.com",
  },
  "candidate-b": { status: "shortlisted", note: "Shortlisted note" },
};
const exportWorkspaceRun = {
  workspace_run_id: "workspace:secret:plan-fingerprint",
  run_context: {
    execution_mode: "single_wave",
    query_count: 10,
    plan_fingerprint: "hidden-plan-fingerprint",
  },
};
const exportBefore = JSON.stringify({
  exportCandidates,
  exportVisibleCandidates,
  exportReviewState,
});

const visibleExportModel = workspace.buildWorkspaceExportModel({
  workspaceRun: exportWorkspaceRun,
  allCandidates: exportCandidates,
  visibleCandidates: exportVisibleCandidates,
  reviewStateByCandidateId: exportReviewState,
  scope: "visible",
  format: "markdown",
  exportedAt: fixedExportDate,
});
assert.deepStrictEqual(
  visibleExportModel.candidates.map((item) => item.candidate_name),
  [exportCandidateC.display_name, exportCandidateA.display_name]
);
assert.deepStrictEqual(
  visibleExportModel.candidates.map((item) => item.display_index),
  [1, 2]
);
assert.strictEqual(visibleExportModel.metadata.workspace_run_id, "workspace:secret:plan-fingerprint");
assert.strictEqual(visibleExportModel.metadata.exported_at, fixedExportDate.toISOString());
assert.strictEqual(visibleExportModel.metadata.scope, "visible");
assert.strictEqual(visibleExportModel.metadata.format, "markdown");
assert.strictEqual(visibleExportModel.metadata.candidate_count, 2);
assert.strictEqual(visibleExportModel.metadata.execution_mode, "single_wave");
assert.strictEqual(visibleExportModel.metadata.query_count, 10);
assert.strictEqual(visibleExportModel.candidates[0].profile_url, "");
assert.strictEqual(visibleExportModel.candidates[0].identity_stable, "no");
assert.strictEqual(visibleExportModel.candidates[0].review_status, "new");
assert.strictEqual(visibleExportModel.candidates[0].shortlisted, "no");
assert.strictEqual(visibleExportModel.candidates[0].notes, "");
assert.strictEqual(visibleExportModel.candidates[1].profile_url, "https://www.linkedin.com/in/foo");
assert.strictEqual(visibleExportModel.candidates[1].identity_stable, "yes");
assert.strictEqual(visibleExportModel.candidates[1].review_status, "reviewing");
assert.strictEqual(visibleExportModel.candidates[1].shortlisted, "no");
assert.strictEqual(visibleExportModel.candidates[1].quality_score, "86");
assert.strictEqual(visibleExportModel.candidates[1].quality_bucket, "high");
assert.strictEqual(visibleExportModel.candidates[1].query_source_ids, "Q01; fallback_category");
assert.ok(visibleExportModel.candidates[1].explanation_summary);
assert.ok(visibleExportModel.candidates[1].explanation_codes.includes("quality_score_high"));
visibleExportModel.candidates.forEach((row) => {
  assert.ok(!Object.prototype.hasOwnProperty.call(row, "candidate_id"));
  assert.ok(!Object.prototype.hasOwnProperty.call(row, "raw"));
  assert.ok(!Object.prototype.hasOwnProperty.call(row, "explanation_version"));
  Object.values(row).forEach((value) => {
    assert.ok(
      typeof value === "string" || typeof value === "number",
      "export rows should contain only scalar serialization values"
    );
  });
});
assert.doesNotThrow(() => JSON.stringify(visibleExportModel));

const allExportModel = workspace.buildWorkspaceExportModel({
  workspaceRun: { run_context: { execution_mode: "unsafe", query_count: -1 } },
  allCandidates: exportCandidates,
  visibleCandidates: exportVisibleCandidates,
  reviewStateByCandidateId: exportReviewState,
  scope: "all",
  format: "csv",
  exportedAt: fixedExportDate,
});
assert.deepStrictEqual(
  allExportModel.candidates.map((item) => item.candidate_name),
  [exportCandidateB.display_name, exportCandidateC.display_name, exportCandidateA.display_name]
);
assert.strictEqual(allExportModel.metadata.execution_mode, "search");
assert.strictEqual(allExportModel.metadata.query_count, 0);
assert.strictEqual(allExportModel.candidates[0].quality_score, "");
assert.strictEqual(allExportModel.candidates[0].quality_bucket, "");
assert.strictEqual(allExportModel.candidates[0].profile_url, "https://ua.linkedin.com/in/foo");
assert.strictEqual(allExportModel.candidates[0].review_status, "shortlisted");
assert.strictEqual(allExportModel.candidates[0].shortlisted, "yes");

const shortlistedExportModel = workspace.buildWorkspaceExportModel({
  allCandidates: exportCandidates,
  visibleCandidates: [],
  reviewStateByCandidateId: exportReviewState,
  scope: "shortlisted",
  format: "csv",
  exportedAt: fixedExportDate,
});
assert.deepStrictEqual(shortlistedExportModel.candidates.map((item) => item.candidate_name), [
  exportCandidateB.display_name,
]);

function exportProfileRowFor(href) {
  const candidate = Object.assign(cloneCandidate(exportCandidateA), {
    candidate_id: "profile-test",
    profile_href: href,
    identity: { is_stable_identity: true, safe_profile_href: href },
  });
  return workspace.buildWorkspaceExportModel({
    allCandidates: [candidate],
    visibleCandidates: [candidate],
    reviewStateByCandidateId: {},
    scope: "visible",
    format: "csv",
    exportedAt: fixedExportDate,
  }).candidates[0];
}

assert.strictEqual(
  exportProfileRowFor("https://www.linkedin.com/in/foo/details/experience").profile_url,
  "https://www.linkedin.com/in/foo"
);
assert.strictEqual(
  exportProfileRowFor("https://linkedin.com/in/foo?trk=x#about").profile_url,
  "https://linkedin.com/in/foo"
);
assert.strictEqual(exportProfileRowFor("http://ua.linkedin.com/in/foo/").profile_url, "https://ua.linkedin.com/in/foo");
assert.strictEqual(
  exportProfileRowFor("https://linkedin.com/IN/FooCase/details").profile_url,
  "https://linkedin.com/in/FooCase"
);
assert.strictEqual(exportProfileRowFor("https://linkedin.com/in/").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://linkedin.com.evil/in/foo").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://user:pass@linkedin.com/in/foo").profile_url, "");
assert.strictEqual(exportProfileRowFor("javascript:alert(1)").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://linkedin.com/in/foo%2Fbar").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://linkedin.com/in/foo%5Cbar").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://linkedin.com/in/.").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://linkedin.com/in/..").profile_url, "");
assert.strictEqual(exportProfileRowFor("https://linkedin.com.evil/in/foo").identity_stable, "no");
assert.strictEqual(
  workspace.buildSafeLinkedInProfileHref({ normalized_url: "https://linkedin.com/in/foo?trk=x#about" }),
  "https://linkedin.com/in/foo?trk=x#about"
);

const visibleCsv = workspace.serializeWorkspaceExportCsv(visibleExportModel);
assert.ok(visibleCsv.startsWith("\ufeffsep=,\r\n"));
assert.ok(visibleCsv.endsWith("\r\n"));
const visibleCsvRows = visibleCsv.split("\r\n");
assert.strictEqual(visibleCsvRows[1], workspace.EXPORT_CSV_COLUMNS.join(","));
assert.strictEqual(visibleCsvRows.length, visibleExportModel.metadata.candidate_count + 3);
assert.ok(!/[\r\n]/.test(visibleCsv.replace(/\r\n/g, "")), "CSV data cells should not contain embedded CR/LF");
assert.ok(visibleCsv.includes('"https://www.linkedin.com/in/foo"'));
assert.ok(!visibleCsv.includes("https://evil.example"));
assert.ok(visibleCsv.includes("https: //evil.example"));
assert.ok(visibleCsv.includes("https: //note.example"));
assert.ok(visibleCsv.includes("linkedin .com/in/not-profile"));
assert.ok(visibleCsv.includes("www .example.com"));
assert.ok(visibleCsv.includes("[contact omitted]"));
assert.ok(visibleCsv.includes("note.user@example.com"), "recruiter notes should not be contact-masked");
assert.ok(visibleCsv.includes("Java 17"));
assert.ok(visibleCsv.includes("Spring 6"));
assert.ok(visibleCsv.includes("Node.js 20"));
assert.ok(visibleCsv.includes(".NET 6"));
assert.ok(visibleCsv.includes("C#"));
assert.ok(visibleCsv.includes("2024"));
assert.ok(visibleCsv.includes("Q01"));
assert.ok(visibleCsv.includes("5+ years"));
assert.ok(visibleCsv.includes("10 years"));
assert.ok(visibleCsv.includes("+5 quality points"));
assert.ok(visibleCsv.includes("C++"));
assert.ok(!visibleCsv.includes("raw query should not export"));
assert.ok(!visibleCsv.includes("candidate-a"));
assert.ok(!visibleCsv.includes("workspace:secret"));
assert.ok(!visibleCsv.includes("hidden-plan-fingerprint"));
assert.ok(!visibleCsv.includes("explanation_version"));
assert.ok(!visibleCsv.includes("[object Object]"));
assert.ok(!visibleCsv.includes('{"'));
assert.ok(visibleCsv.includes("\"'=Anna, \"\"Java\"\"\""));
assert.ok(visibleCsv.includes("\"'=cmd https: //note.example and linkedin .com/in/not-profile note.user@example.com\""));
assert.strictEqual(
  workspace.serializeWorkspaceExportCsv({ metadata: {}, candidates: [] }),
  `\ufeffsep=,\r\n${workspace.EXPORT_CSV_COLUMNS.join(",")}\r\n`
);
assert.strictEqual(workspace.sanitizeCsvCell("\tSafe", { neutralizeUrlLike: true }), "\"'Safe\"");
assert.strictEqual(workspace.sanitizeCsvCell("  -cmd", { neutralizeUrlLike: true }), "\"'-cmd\"");

const visibleMarkdown = workspace.serializeWorkspaceExportMarkdown(visibleExportModel);
assert.ok(visibleMarkdown.startsWith("# Candidate Workspace Export\n\n"));
assert.ok(visibleMarkdown.endsWith("\n"));
assert.ok(!visibleMarkdown.includes("\r"));
assert.ok(visibleMarkdown.includes("Format: markdown"));
assert.ok(visibleMarkdown.includes("Candidates: 2"));
assert.ok(visibleMarkdown.includes("- Profile: https://www.linkedin.com/in/foo"));
assert.ok(visibleMarkdown.includes("https: //bad.example"));
assert.ok(visibleMarkdown.includes("linkedin .com/in/not-trusted"));
assert.ok(visibleMarkdown.includes("&lt;script&gt;alert\\(1\\)&lt;/script&gt;"));
assert.ok(!visibleMarkdown.includes("<script>"));
assert.ok(!visibleMarkdown.includes("](https://"));
assert.ok(!visibleMarkdown.includes("workspace:secret"));
assert.ok(!visibleMarkdown.includes("candidate-a"));
assert.ok(!visibleMarkdown.includes("raw query should not export"));
assert.ok(!visibleMarkdown.includes("explanation_version"));
assert.ok(!visibleMarkdown.includes("[object Object]"));

assert.strictEqual(
  workspace.buildWorkspaceExportFilename(fixedExportDate, "shortlisted", "markdown"),
  "engineers-search-candidates-shortlisted-20260522-130405.md"
);
assert.strictEqual(
  workspace.buildWorkspaceExportFilename(fixedExportDate, "bad-scope", "bad-format"),
  "engineers-search-candidates-visible-20260522-130405.csv"
);
assert.strictEqual(
  JSON.stringify({ exportCandidates, exportVisibleCandidates, exportReviewState }),
  exportBefore,
  "export helpers should not mutate candidates, review state, or visible arrays"
);

const indexHtml = fs.readFileSync(indexPath, "utf8");
assert.ok(
  indexHtml.indexOf("/static/candidate_workspace.js") > -1 &&
    indexHtml.indexOf("/static/candidate_workspace.js") < indexHtml.indexOf("/static/app.js"),
  "candidate_workspace.js should load before app.js"
);

console.log("P8 candidate workspace helper smoke passed.");
