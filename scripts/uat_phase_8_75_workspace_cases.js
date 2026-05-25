const assert = require("assert");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { TextEncoder } = require("util");

const repoRoot = path.resolve(__dirname, "..");
const helperPath = path.join(repoRoot, "app", "static", "candidate_workspace.js");

const context = {
  console,
  Date,
  TextEncoder,
  URL,
  crypto: crypto.webcrypto,
  require,
  window: {
    TextEncoder,
    crypto: crypto.webcrypto,
    require,
  },
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync(helperPath, "utf8"), context, { filename: helperPath });

const workspace = context.window.CandidateWorkspace;
const results = [];

function check(id, category, fn) {
  try {
    fn();
    results.push({ id, category, status: "pass" });
  } catch (error) {
    results.push({
      id,
      category,
      status: "fail",
      detail: error && error.message ? error.message : String(error),
    });
    throw error;
  }
}

function containsForbiddenPayload(value) {
  const serialized = JSON.stringify(value).toLowerCase();
  return [
    "candidate_id",
    "normalized_url",
    "linkedin.com/in",
    "https://",
    "raw_content",
    "private recruiter note",
    "brief_patch",
    "proposed_action",
    "approval",
    "endpoint",
  ].some((term) => serialized.includes(term));
}

function sampleRawResults() {
  return [
    {
      normalized_url: "https://ua.linkedin.com/in/anna-java",
      current_location_status: "target_location",
      stack_fit: "selected_stack_found",
      result: {
        name: "Anna Java",
        title: "Senior Java Backend Developer - LinkedIn",
        url: "https://ua.linkedin.com/in/anna-java",
        quality_score: 94,
        role_display: "Backend Developer",
        role_fit: "target_or_close_role",
        technology_display: "Java",
        technology_fit: "exact",
        stack_evidence: [
          { term: "Spring", source: "candidate_text", evidence_type: "direct_text" },
          { term: "Kafka", source: "candidate_text", evidence_type: "direct_text" },
        ],
        selected_stack_terms_found: ["Spring", "Kafka"],
        current_location_line: "Kyiv, Ukraine",
        location_signal_terms: ["Kyiv", "Ukraine"],
        quality_score_breakdown: [
          { component: "role", points: 25, max_points: 25, fit: "target_or_close_role" },
          { component: "stack", points: 20, max_points: 20, fit: "selected_stack_found" },
          { component: "location", points: 25, max_points: 25, fit: "target_location" },
        ],
        seniority_display: "Senior",
        review_flag_details: [],
      },
      query_sources: [{ id: "Q01", category: "role_based", query: "raw query should not leak" }],
    },
    {
      normalized_url: "https://ua.linkedin.com/in/bohdan-backend",
      current_location_status: "target_location",
      stack_fit: "stack_query_source_only",
      result: {
        name: "Bohdan Backend",
        title: "Java Software Engineer",
        url: "https://ua.linkedin.com/in/bohdan-backend",
        quality_score: 72,
        role_display: "Java Software Engineer",
        role_fit: "target_or_close_role",
        technology_display: "Java",
        technology_fit: "exact",
        stack_evidence: [{ term: "Kafka", source: "query_source", evidence_type: "stack_query_group" }],
        selected_stack_terms_found: [],
        missing_selected_stack_terms: ["Spring"],
        current_location_line: "Ukraine",
        review_flag_details: [{ code: "stack_query_source_only", label: "Stack query source only", severity: "medium" }],
      },
    },
    {
      normalized_url: "https://ua.linkedin.com/in/christina-java",
      current_location_status: "unknown_current_location",
      stack_fit: "missing_selected_stack",
      result: {
        name: "Christina Java",
        title: "Java Engineer",
        url: "https://ua.linkedin.com/in/christina-java",
        quality_score: 58,
        role_display: "Java Engineer",
        role_fit: "target_or_close_role",
        technology_display: "Java",
        technology_fit: "exact",
        selected_stack_terms_found: [],
        missing_selected_stack_terms: ["Spring", "Kafka"],
        current_location_line: "",
        review_flag_details: [{ code: "missing_selected_stack", label: "Stack not visible", severity: "warning" }],
      },
    },
    {
      normalized_url: "https://cz.linkedin.com/in/dana-java",
      current_location_status: "foreign_current_location",
      stack_fit: "selected_stack_found",
      result: {
        name: "Dana JVM",
        title: "Java Developer",
        url: "https://cz.linkedin.com/in/dana-java",
        quality_score: 48,
        role_display: "Java Developer",
        role_fit: "target_or_close_role",
        technology_display: "Java",
        technology_fit: "exact",
        selected_stack_terms_found: ["Spring"],
        current_location_line: "Prague, Czechia",
        review_flag_details: [{ code: "foreign_current_location", label: "Foreign location", severity: "risk" }],
      },
    },
    {
      normalized_url: "https://ua.linkedin.com/in/erik-platform",
      current_location_status: "target_location",
      stack_fit: "selected_stack_found",
      result: {
        name: "Erik Platform",
        title: "Backend Platform Engineer",
        url: "https://ua.linkedin.com/in/erik-platform",
        quality_score: 88,
        role_display: "Backend Engineer",
        role_fit: "target_or_close_role",
        technology_display: "Java",
        technology_fit: "exact",
        selected_stack_terms_found: ["Spring", "AWS"],
        current_location_line: "Lviv, Ukraine",
        review_flag_details: [],
      },
    },
    {
      normalized_url: "https://linkedin.com.evil/in/not-safe",
      current_location_status: "target_location",
      stack_fit: "missing_selected_stack",
      result: {
        name: "Unsafe Host",
        url: "javascript:alert(1)",
        quality_score: "bad",
      },
    },
  ];
}

check("P875-WS-001", "workspace_exports", () => assert.ok(workspace));
check("P875-WS-002", "workspace_exports", () => assert.strictEqual(workspace.REVIEW_STATUSES.SHORTLISTED, "shortlisted"));
check("P875-WS-003", "workspace_exports", () => assert.strictEqual(typeof workspace.buildCandidateExplanation, "function"));
check("P875-WS-004", "workspace_exports", () => assert.strictEqual(typeof workspace.buildTopCandidateRecommendation, "function"));
check("P875-WS-005", "workspace_exports", () => assert.strictEqual(typeof workspace.buildSelectedCandidateComparison, "function"));
check("P875-WS-006", "workspace_exports", () => assert.strictEqual(typeof workspace.buildSelectedCandidateFitGapExplanation, "function"));
check("P875-WS-007", "workspace_exports", () => assert.strictEqual(typeof workspace.buildWorkspaceRefinementSuggestions, "function"));
check("P875-WS-008", "workspace_exports", () => assert.strictEqual(typeof workspace.buildWorkspaceExportModel, "function"));

const candidates = workspace.mapDedupedResultsToWorkspaceCandidates(sampleRawResults());
const reviewState = workspace.createReviewStateForCandidates(candidates);
reviewState[candidates[0].candidate_id] = {
  ...reviewState[candidates[0].candidate_id],
  status: workspace.REVIEW_STATUSES.SHORTLISTED,
  note: "private recruiter note",
};
reviewState[candidates[1].candidate_id] = {
  ...reviewState[candidates[1].candidate_id],
  status: workspace.REVIEW_STATUSES.SHORTLISTED,
};
reviewState[candidates[3].candidate_id] = {
  ...reviewState[candidates[3].candidate_id],
  status: workspace.REVIEW_STATUSES.NOT_A_FIT,
};

check("P875-WS-009", "mapping", () => assert.strictEqual(candidates.length, 6));
check("P875-WS-010", "mapping", () => assert.strictEqual(candidates[0].profile_href, "https://ua.linkedin.com/in/anna-java"));
check("P875-WS-011", "mapping", () => assert.strictEqual(candidates[5].profile_href, ""));
check("P875-WS-012", "mapping", () => assert.strictEqual(candidates[0].quality_bucket, "high"));
check("P875-WS-013", "mapping", () => assert.strictEqual(candidates[2].quality_bucket, "medium"));
check("P875-WS-014", "mapping", () => assert.strictEqual(candidates[3].location_group, "foreign"));
check("P875-WS-015", "mapping", () => assert.ok(candidates[2].review_flags.length > 0));

const highFirst = workspace.applyWorkspaceView(
  candidates,
  { sort: "quality_desc", quality_filter: "all", location_filter: "all", review_status_filter: "all", shortlist_filter: "all" },
  reviewState
);
const targetOnly = workspace.applyWorkspaceView(
  candidates,
  { sort: "quality_desc", quality_filter: "all", location_filter: "target", review_status_filter: "all", shortlist_filter: "all" },
  reviewState
);
const shortlistedOnly = workspace.applyWorkspaceView(
  candidates,
  { sort: "quality_desc", quality_filter: "all", location_filter: "all", review_status_filter: "all", shortlist_filter: "shortlisted" },
  reviewState
);

check("P875-WS-016", "workspace_view", () => assert.strictEqual(highFirst[0].display_name, "Anna Java"));
check("P875-WS-017", "workspace_view", () => assert.ok(targetOnly.every((candidate) => candidate.location_group === "target")));
check("P875-WS-018", "workspace_view", () => assert.strictEqual(shortlistedOnly.length, 2));
check("P875-WS-019", "workspace_view", () => assert.ok(shortlistedOnly.every((candidate) => reviewState[candidate.candidate_id].status === "shortlisted")));

const strongExplanation = workspace.buildCandidateExplanation(candidates[0]);
const queryOnlyExplanation = workspace.buildCandidateExplanation(candidates[1]);
const foreignExplanation = workspace.buildCandidateExplanation(candidates[3]);

check("P875-WS-020", "candidate_explanation", () => assert.strictEqual(strongExplanation.source, "deterministic_workspace_facts"));
check("P875-WS-021", "candidate_explanation", () => assert.ok(strongExplanation.positive_signals.some((item) => item.code === "quality_score_high")));
check("P875-WS-022", "candidate_explanation", () => assert.ok(strongExplanation.positive_signals.some((item) => item.code === "target_location")));
check("P875-WS-023", "candidate_explanation", () => assert.ok(strongExplanation.positive_signals.some((item) => item.code === "stack_confirmed")));
check("P875-WS-024", "candidate_explanation", () => assert.ok(queryOnlyExplanation.cautions.some((item) => item.code === "stack_query_source_only")));
check("P875-WS-025", "candidate_explanation", () => assert.ok(foreignExplanation.cautions.some((item) => item.code === "location_foreign_or_mismatch")));
check("P875-WS-026", "candidate_explanation", () => assert.ok(!JSON.stringify(strongExplanation).includes("private recruiter note")));

const top = workspace.buildTopCandidateRecommendation(candidates, reviewState, { limit: 3, scope: "visible_candidates" });
check("P875-WS-027", "top_candidate", () => assert.strictEqual(top.source, "deterministic_workspace_facts"));
check("P875-WS-028", "top_candidate", () => assert.strictEqual(top.scope, "visible_candidates"));
check("P875-WS-029", "top_candidate", () => assert.ok(top.recommendations.length > 0));
check("P875-WS-030", "top_candidate", () => assert.ok(!top.recommendations.some((item) => item.display_name === "Dana JVM")));
check("P875-WS-031", "top_candidate", () => assert.strictEqual(containsForbiddenPayload(top), false));

const comparison = workspace.buildSelectedCandidateComparison(candidates, reviewState, { limit: 4 });
check("P875-WS-032", "selected_comparison", () => assert.strictEqual(comparison.source, "deterministic_workspace_facts"));
check("P875-WS-033", "selected_comparison", () => assert.strictEqual(comparison.selected_count, 2));
check("P875-WS-034", "selected_comparison", () => assert.ok(comparison.candidates.length >= 2));
check("P875-WS-035", "selected_comparison", () => assert.strictEqual(containsForbiddenPayload(comparison), false));

const fitGap = workspace.buildSelectedCandidateFitGapExplanation(candidates, reviewState, { limit: 4 });
check("P875-WS-036", "fit_gap", () => assert.strictEqual(fitGap.source, "deterministic_workspace_facts"));
check("P875-WS-037", "fit_gap", () => assert.strictEqual(fitGap.selected_count, 2));
check("P875-WS-038", "fit_gap", () => assert.ok(fitGap.candidate_fit_gaps.length >= 2));
check("P875-WS-039", "fit_gap", () =>
  assert.ok(
    fitGap.summary.toLowerCase().includes("manual review") ||
      fitGap.candidate_fit_gaps.some((item) => item.gap_labels.length > 0)
  )
);
check("P875-WS-040", "fit_gap", () => assert.strictEqual(containsForbiddenPayload(fitGap), false));

const guidance = workspace.buildWorkspaceRefinementSuggestions(candidates, reviewState, {
  limit: 5,
  scope: "all_candidates",
});
const guidanceTypes = new Set(guidance.suggestions.map((item) => item.suggestion_type));
check("P875-WS-041", "refinement_guidance", () => assert.strictEqual(guidance.source, "deterministic_workspace_facts"));
check("P875-WS-042", "refinement_guidance", () => assert.strictEqual(guidance.scope, "visible_candidates"));
check("P875-WS-043", "refinement_guidance", () => assert.strictEqual(guidance.stats.shortlisted, 2));
check("P875-WS-044", "refinement_guidance", () => assert.ok(guidanceTypes.has("review_selected")));
check("P875-WS-045", "refinement_guidance", () => assert.ok(guidanceTypes.has("review_strong_candidates")));
check("P875-WS-046", "refinement_guidance", () => assert.strictEqual(containsForbiddenPayload(guidance), false));

const exportModel = workspace.buildWorkspaceExportModel({
  allCandidates: candidates,
  visibleCandidates: highFirst,
  reviewStateByCandidateId: reviewState,
  scope: "shortlisted",
  format: "csv",
  workspaceRun: {
    workspace_run_id: "workspace:test",
    execution_mode: "multi_wave",
    unique_candidates: candidates.length,
  },
  exportedAt: "2026-05-25T12:00:00.000Z",
});
const csv = workspace.serializeWorkspaceExportCsv(exportModel);
const markdown = workspace.serializeWorkspaceExportMarkdown({
  ...exportModel,
  metadata: { ...exportModel.metadata, format: "markdown" },
});

check("P875-WS-047", "export", () => assert.strictEqual(exportModel.candidates.length, 2));
check("P875-WS-048", "export", () => assert.ok(csv.includes("candidate_name")));
check("P875-WS-049", "export", () => assert.ok(markdown.includes("Candidate Workspace Export")));
check("P875-WS-050", "export", () => assert.ok(!csv.includes("raw query should not leak")));
check("P875-WS-051", "export", () => assert.ok(!markdown.includes("raw query should not leak")));
check("P875-WS-052", "export", () => assert.ok(!csv.includes("<script")));
check("P875-WS-053", "export", () => assert.ok(workspace.buildWorkspaceExportFilename("2026-05-25T12:00:00.000Z", "shortlisted", "csv").endsWith(".csv")));
check("P875-WS-054", "export", () => assert.strictEqual(workspace.workspaceExportMimeType("markdown"), "text/markdown;charset=utf-8"));

const noVisible = workspace.buildWorkspaceRefinementSuggestions([], {}, { scope: "all_candidates" });
check("P875-WS-055", "empty_state", () => assert.strictEqual(noVisible.stats.visible_candidates, 0));
check("P875-WS-056", "empty_state", () => assert.strictEqual(noVisible.scope, "visible_candidates"));
check("P875-WS-057", "empty_state", () => assert.ok(noVisible.suggestions.some((item) => item.suggestion_type === "adjust_view")));
check("P875-WS-058", "empty_state", () => assert.strictEqual(containsForbiddenPayload(noVisible), false));

const failed = results.filter((result) => result.status !== "pass");
const summary = {
  total: results.length,
  passed: results.length - failed.length,
  failed: failed.length,
  categories: results.reduce((acc, result) => {
    acc[result.category] = (acc[result.category] || 0) + 1;
    return acc;
  }, {}),
  failed_cases: failed,
};

if (process.argv.includes("--json")) {
  console.log(JSON.stringify(summary));
} else {
  console.log(`Phase 8.75 workspace UAT passed: ${summary.passed}/${summary.total} cases`);
}
