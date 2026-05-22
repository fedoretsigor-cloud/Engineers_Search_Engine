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

const indexHtml = fs.readFileSync(indexPath, "utf8");
assert.ok(
  indexHtml.indexOf("/static/candidate_workspace.js") > -1 &&
    indexHtml.indexOf("/static/candidate_workspace.js") < indexHtml.indexOf("/static/app.js"),
  "candidate_workspace.js should load before app.js"
);

console.log("P8 candidate workspace helper smoke passed.");
