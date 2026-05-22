(function (root) {
  "use strict";

  const SORT_MODES = {
    ORIGINAL: "original",
    QUALITY_DESC: "quality_desc",
    QUALITY_ASC: "quality_asc",
    NAME_ASC: "name_asc",
  };

  const QUALITY_FILTERS = {
    ALL: "all",
    SCORE_80_PLUS: "80_plus",
    SCORE_70_PLUS: "70_plus",
    SCORE_60_PLUS: "60_plus",
  };

  const STACK_FILTERS = {
    ALL: "all",
    CONFIRMED: "confirmed",
    QUERY_SOURCE_ONLY: "query_source_only",
    NOT_VISIBLE: "not_visible",
  };

  const REVIEW_FLAG_FILTERS = {
    ALL: "all",
    HAS_FLAGS: "has_flags",
    NO_FLAGS: "no_flags",
    HIGH_MEDIUM: "high_medium",
  };

  const LOCATION_FILTERS = {
    ALL: "all",
    TARGET: "target",
    UNKNOWN_WEAK: "unknown_weak",
  };

  const REVIEW_STATUSES = {
    NEW: "new",
    REVIEWING: "reviewing",
    SHORTLISTED: "shortlisted",
    NOT_A_FIT: "not_a_fit",
  };

  const SHORTLIST_FILTERS = {
    ALL: "all",
    SHORTLISTED: "shortlisted",
    NOT_SHORTLISTED: "not_shortlisted",
  };

  const NOTE_MAX_LENGTH = 1000;
  const SAFE_SEVERITIES = new Set(["info", "warning", "risk", "positive", "high", "medium", "low"]);
  const SAFE_REVIEW_STATUSES = new Set(Object.values(REVIEW_STATUSES));

  function arrayValue(value) {
    return Array.isArray(value) ? value : [];
  }

  function stringValue(value) {
    return typeof value === "string" ? value.trim() : "";
  }

  function lowerValue(value) {
    return stringValue(value).toLowerCase();
  }

  function isUsefulText(value) {
    const text = stringValue(value);
    return Boolean(text) && text.toLowerCase() !== "unknown" && text.toLowerCase() !== "n/a";
  }

  function firstUsefulText(values) {
    for (const value of values) {
      if (isUsefulText(value)) {
        return stringValue(value);
      }
    }
    return "";
  }

  function finiteNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function hasFiniteNumber(value) {
    return Number.isFinite(Number(value));
  }

  function normalizeUrlCandidate(value) {
    const raw = stringValue(value);
    if (!raw) {
      return "";
    }
    if (/^https?:\/\//i.test(raw)) {
      return raw;
    }
    if (/^[a-z0-9.-]*linkedin\.com\/in\//i.test(raw)) {
      return `https://${raw}`;
    }
    return raw;
  }

  function safeLinkedInProfileHrefFromValue(value) {
    const candidate = normalizeUrlCandidate(value);
    if (!candidate) {
      return "";
    }

    try {
      const parsed = new URL(candidate);
      const hostname = parsed.hostname.toLowerCase();
      const isLinkedInHost = hostname === "linkedin.com" || hostname.endsWith(".linkedin.com");
      const isHttp = parsed.protocol === "https:" || parsed.protocol === "http:";
      if (!isHttp || !isLinkedInHost || !parsed.pathname.toLowerCase().startsWith("/in/")) {
        return "";
      }
      return parsed.toString();
    } catch (error) {
      return "";
    }
  }

  function buildSafeLinkedInProfileHref(item) {
    const normalizedHref = safeLinkedInProfileHrefFromValue(item && item.normalized_url);
    if (normalizedHref) {
      return normalizedHref;
    }
    const resultHref = safeLinkedInProfileHrefFromValue(item && item.result && item.result.url);
    return resultHref || "";
  }

  function candidateStableId(item, index) {
    const normalizedUrl = stringValue(item && item.normalized_url);
    return normalizedUrl || `workspace-row-${index + 1}`;
  }

  function displayNameForCandidate(item, index) {
    const result = (item && item.result) || {};
    return (
      firstUsefulText([
        result.name,
        item && item.name,
        result.headline,
        item && item.headline,
        result.title,
        item && item.title,
        item && item.normalized_url,
      ]) || `Candidate ${index + 1}`
    );
  }

  function normalizeLocationStatus(item) {
    const result = (item && item.result) || {};
    const raw = lowerValue(
      item &&
        (item.current_location_status ||
          item.location_status ||
          item.location_decision ||
          item.location_match_type ||
          result.current_location_status ||
          result.location_signal_status ||
          result.location_status)
    );
    if (!raw) {
      return "unknown_current_location";
    }
    return raw;
  }

  function locationGroup(item) {
    const status = normalizeLocationStatus(item);
    if (
      status === "target_location" ||
      status === "country_domain" ||
      status === "rescued_header_location" ||
      status === "target_current_location"
    ) {
      return "target";
    }
    if (status === "foreign_current_location" || status === "excluded_foreign_current_location") {
      return "foreign";
    }
    return "unknown_weak";
  }

  function normalizeStackFit(item) {
    const result = (item && item.result) || {};
    const raw = lowerValue(item && (item.stack_fit || item.stack_match_type || result.stack_fit));
    if (raw === "selected_stack_found" || raw === "confirmed" || raw === "direct_stack_evidence") {
      return "confirmed";
    }
    if (raw === "stack_query_source_only" || raw === "query_source_only") {
      return "query_source_only";
    }
    if (raw === "missing_selected_stack" || raw === "not_visible") {
      return "not_visible";
    }
    return raw || "unknown";
  }

  function normalizeSeniorityLevel(item) {
    const result = (item && item.result) || {};
    const raw = lowerValue(
      item && (item.seniority_level || item.seniority || result.seniority_level || result.seniority_display)
    );
    if (raw.includes("lead") || raw.includes("principal") || raw.includes("staff")) {
      return 4;
    }
    if (raw.includes("senior") || raw === "sr") {
      return 3;
    }
    if (raw.includes("middle") || raw.includes("mid")) {
      return 2;
    }
    if (raw.includes("junior") || raw.includes("entry")) {
      return 1;
    }
    return 0;
  }

  function normalizeReviewFlagDetails(item) {
    const result = (item && item.result) || {};
    const details = arrayValue((item && item.review_flag_details) || result.review_flag_details);
    if (details.length) {
      return details.map((flag) => ({
        code: stringValue(flag && flag.code),
        label: stringValue(flag && flag.label) || stringValue(flag && flag.code) || "Review flag",
        severity: normalizeSeverity(flag && flag.severity),
      }));
    }
    return arrayValue((item && item.review_flags) || result.review_flags).map((flag) => ({
      code: stringValue(flag),
      label: stringValue(flag) || "Review flag",
      severity: "info",
    }));
  }

  function mapDedupedResultToWorkspaceCandidate(item, index) {
    const result = (item && item.result) || {};
    const candidateId = candidateStableId(item, index);
    const rawQualityScore =
      (item && item.quality_score) ?? result.quality_score ?? result.score;
    const hasQualityScore = hasFiniteNumber(rawQualityScore);
    const qualityScore = hasQualityScore ? finiteNumber(rawQualityScore, 0) : 0;
    const safeProfileHref = buildSafeLinkedInProfileHref(item || {});
    const normalizedUrl = stringValue(item && item.normalized_url);
    const displayUrl = normalizedUrl || stringValue(result.url);
    const reviewFlags = normalizeReviewFlagDetails(item || {});
    const querySources = arrayValue(item && item.query_sources);

    return {
      candidate_id: candidateId,
      order_index: index,
      source_index: index,
      display_index: index + 1,
      display_name: displayNameForCandidate(item || {}, index),
      headline: firstUsefulText([result.headline, item && item.headline, result.title, item && item.title]),
      profile_url: displayUrl,
      profile_href: safeProfileHref,
      normalized_url: normalizedUrl,
      source: stringValue(item && item.source) || stringValue(result.source) || "linkedin",
      quality_score: qualityScore,
      has_quality_score: hasQualityScore,
      quality_bucket: qualityBucket(qualityScore),
      stack_fit: normalizeStackFit(item || {}),
      location_status: normalizeLocationStatus(item || {}),
      location_group: locationGroup(item || {}),
      seniority_level:
        stringValue(
          item &&
            (item.seniority_level ||
              item.seniority ||
              result.seniority_level ||
              result.seniority_display)
        ) || "unknown",
      seniority_rank: normalizeSeniorityLevel(item || {}),
      review_flags: reviewFlags,
      matched_signals: arrayValue(item && item.matched_signals),
      matched_terms: arrayValue(item && item.matched_terms),
      selected_stack_terms_found: arrayValue(
        (item && item.selected_stack_terms_found) || result.selected_stack_terms_found
      ),
      missing_selected_stack_terms: arrayValue(
        (item && item.missing_selected_stack_terms) || result.missing_selected_stack_terms
      ),
      query_sources: querySources,
      snippet: stringValue(result.content) || stringValue(result.snippet) || stringValue(item && item.content),
      raw_title: stringValue(result.title) || stringValue(item && item.title),
      identity: {
        is_stable_identity: Boolean(normalizedUrl),
        primary_value: normalizedUrl || candidateId,
        safe_profile_href: safeProfileHref,
      },
      raw: item,
    };
  }

  function qualityBucket(score) {
    const value = finiteNumber(score, 0);
    if (value >= 70) {
      return "high";
    }
    if (value >= 40) {
      return "medium";
    }
    return "low";
  }

  function mapDedupedResultsToWorkspaceCandidates(results) {
    return arrayValue(results).map((item, index) => mapDedupedResultToWorkspaceCandidate(item, index));
  }

  function createWorkspaceRunId(context) {
    const parts = [
      context && context.idempotency_key,
      context && context.tool_call_id,
      context && context.plan_fingerprint,
      context && context.run_counter,
    ]
      .map((part) => String(part ?? "").trim())
      .filter(Boolean);
    return parts.length ? `workspace:${parts.join(":")}` : `workspace:local:${Date.now()}`;
  }

  function normalizeSortMode(value) {
    return Object.values(SORT_MODES).includes(value) ? value : SORT_MODES.ORIGINAL;
  }

  function normalizeFilter(value, allowed, fallback) {
    return allowed.includes(value) ? value : fallback;
  }

  function defaultWorkspaceViewState() {
    return {
      sort_mode: SORT_MODES.ORIGINAL,
      quality_filter: QUALITY_FILTERS.ALL,
      stack_filter: STACK_FILTERS.ALL,
      review_flag_filter: REVIEW_FLAG_FILTERS.ALL,
      location_filter: LOCATION_FILTERS.ALL,
      review_status_filter: "all",
      shortlist_filter: SHORTLIST_FILTERS.ALL,
    };
  }

  function normalizeWorkspaceViewState(viewState) {
    const state = viewState || {};
    return {
      sort_mode: normalizeSortMode(state.sort_mode),
      quality_filter: normalizeFilter(
        state.quality_filter,
        Object.values(QUALITY_FILTERS),
        QUALITY_FILTERS.ALL
      ),
      stack_filter: normalizeFilter(state.stack_filter, Object.values(STACK_FILTERS), STACK_FILTERS.ALL),
      review_flag_filter: normalizeFilter(
        state.review_flag_filter,
        Object.values(REVIEW_FLAG_FILTERS),
        REVIEW_FLAG_FILTERS.ALL
      ),
      location_filter: normalizeFilter(
        state.location_filter,
        Object.values(LOCATION_FILTERS),
        LOCATION_FILTERS.ALL
      ),
      review_status_filter: normalizeFilter(
        state.review_status_filter,
        ["all"].concat(Object.values(REVIEW_STATUSES)),
        "all"
      ),
      shortlist_filter: normalizeFilter(
        state.shortlist_filter,
        Object.values(SHORTLIST_FILTERS),
        SHORTLIST_FILTERS.ALL
      ),
    };
  }

  function candidateReviewState(reviewStateByCandidateId, candidateId) {
    return (
      (reviewStateByCandidateId && reviewStateByCandidateId[candidateId]) || {
        status: REVIEW_STATUSES.NEW,
        shortlisted: false,
        note: "",
      }
    );
  }

  function applyQualityFilter(candidate, filter) {
    if (filter === QUALITY_FILTERS.ALL) {
      return true;
    }
    if (!candidate.has_quality_score) {
      return false;
    }
    const thresholds = {
      [QUALITY_FILTERS.SCORE_80_PLUS]: 80,
      [QUALITY_FILTERS.SCORE_70_PLUS]: 70,
      [QUALITY_FILTERS.SCORE_60_PLUS]: 60,
    };
    return candidate.quality_score >= thresholds[filter];
  }

  function applyStackFilter(candidate, filter) {
    if (filter === STACK_FILTERS.ALL) {
      return true;
    }
    return candidate.stack_fit === filter;
  }

  function applyReviewFlagFilter(candidate, filter) {
    if (filter === REVIEW_FLAG_FILTERS.ALL) {
      return true;
    }
    const hasFlags = candidate.review_flags.length > 0;
    if (filter === REVIEW_FLAG_FILTERS.HAS_FLAGS) {
      return hasFlags;
    }
    if (filter === REVIEW_FLAG_FILTERS.NO_FLAGS) {
      return !hasFlags;
    }
    return candidate.review_flags.some((flag) => flag.severity === "high" || flag.severity === "medium");
  }

  function applyLocationFilter(candidate, filter) {
    if (filter === LOCATION_FILTERS.ALL) {
      return true;
    }
    return candidate.location_group === filter;
  }

  function applyReviewStatusFilter(reviewState, filter) {
    if (filter === "all") {
      return true;
    }
    return reviewState.status === filter;
  }

  function applyShortlistFilter(reviewState, filter) {
    if (filter === SHORTLIST_FILTERS.ALL) {
      return true;
    }
    const shortlisted = isWorkspaceCandidateShortlisted(reviewState);
    return filter === SHORTLIST_FILTERS.SHORTLISTED ? shortlisted : !shortlisted;
  }

  function sortWorkspaceCandidates(candidates, sortMode) {
    const sorted = candidates.slice();
    if (sortMode === SORT_MODES.QUALITY_DESC) {
      sorted.sort((left, right) => {
        if (left.has_quality_score !== right.has_quality_score) {
          return left.has_quality_score ? -1 : 1;
        }
        return right.quality_score - left.quality_score || left.order_index - right.order_index;
      });
      return sorted;
    }
    if (sortMode === SORT_MODES.QUALITY_ASC) {
      sorted.sort((left, right) => {
        if (left.has_quality_score !== right.has_quality_score) {
          return left.has_quality_score ? -1 : 1;
        }
        return left.quality_score - right.quality_score || left.order_index - right.order_index;
      });
      return sorted;
    }
    if (sortMode === SORT_MODES.NAME_ASC) {
      sorted.sort((left, right) => {
        const byName = left.display_name.localeCompare(right.display_name, undefined, { sensitivity: "base" });
        return byName || left.order_index - right.order_index;
      });
      return sorted;
    }
    sorted.sort((left, right) => left.order_index - right.order_index);
    return sorted;
  }

  function applyWorkspaceView(candidates, viewState, reviewStateByCandidateId) {
    const state = normalizeWorkspaceViewState(viewState);
    const filtered = arrayValue(candidates).filter((candidate) => {
      const reviewState = candidateReviewState(reviewStateByCandidateId, candidate.candidate_id);
      return (
        applyQualityFilter(candidate, state.quality_filter) &&
        applyStackFilter(candidate, state.stack_filter) &&
        applyReviewFlagFilter(candidate, state.review_flag_filter) &&
        applyLocationFilter(candidate, state.location_filter) &&
        applyReviewStatusFilter(reviewState, state.review_status_filter) &&
        applyShortlistFilter(reviewState, state.shortlist_filter)
      );
    });
    return sortWorkspaceCandidates(filtered, state.sort_mode);
  }

  function normalizeReviewStatusForInit(value) {
    return SAFE_REVIEW_STATUSES.has(value) ? value : REVIEW_STATUSES.NEW;
  }

  function normalizeReviewStatusForUpdate(value, previousStatus) {
    return SAFE_REVIEW_STATUSES.has(value) ? value : normalizeReviewStatusForInit(previousStatus);
  }

  function normalizeNote(value) {
    return stringValue(value).slice(0, NOTE_MAX_LENGTH);
  }

  function createInitialReviewState(previous) {
    const existing = previous || {};
    return {
      status: normalizeReviewStatusForInit(existing.status),
      note: normalizeNote(existing.note),
    };
  }

  function createReviewStateForCandidates(candidates, previousStateByCandidateId) {
    const previous = previousStateByCandidateId || {};
    return arrayValue(candidates).reduce((state, candidate) => {
      state[candidate.candidate_id] = createInitialReviewState(previous[candidate.candidate_id]);
      return state;
    }, {});
  }

  function setWorkspaceReviewStatus(reviewStateByCandidateId, candidateId, status) {
    const state = Object.assign({}, reviewStateByCandidateId || {});
    const previous = createInitialReviewState(state[candidateId]);
    const nextStatus = normalizeReviewStatusForUpdate(status, previous.status);
    state[candidateId] = Object.assign({}, previous, {
      status: nextStatus,
    });
    return state;
  }

  function toggleWorkspaceShortlist(reviewStateByCandidateId, candidateId, enabled) {
    const state = Object.assign({}, reviewStateByCandidateId || {});
    const previous = createInitialReviewState(state[candidateId]);
    state[candidateId] = Object.assign({}, previous, {
      status: Boolean(enabled) ? REVIEW_STATUSES.SHORTLISTED : REVIEW_STATUSES.REVIEWING,
    });
    return state;
  }

  function setWorkspaceCandidateNote(reviewStateByCandidateId, candidateId, note) {
    const state = Object.assign({}, reviewStateByCandidateId || {});
    const previous = createInitialReviewState(state[candidateId]);
    state[candidateId] = Object.assign({}, previous, { note: normalizeNote(note) });
    return state;
  }

  function isWorkspaceCandidateShortlisted(reviewState) {
    return normalizeReviewStatusForInit(reviewState && reviewState.status) === REVIEW_STATUSES.SHORTLISTED;
  }

  function reviewStatusLabel(status) {
    const labels = {
      new: "New",
      reviewing: "Reviewing",
      shortlisted: "Shortlisted",
      not_a_fit: "Not a fit",
    };
    return labels[normalizeReviewStatusForInit(status)];
  }

  function reviewStatusClassName(status) {
    return `review-status-${normalizeReviewStatusForInit(status).replace(/_/g, "-")}`;
  }

  function normalizeSeverity(severity) {
    const normalized = lowerValue(severity);
    return SAFE_SEVERITIES.has(normalized) ? normalized : "info";
  }

  function severityClassName(severity) {
    return `severity-${normalizeSeverity(severity)}`;
  }

  root.CandidateWorkspace = {
    SORT_MODES,
    QUALITY_FILTERS,
    STACK_FILTERS,
    REVIEW_FLAG_FILTERS,
    LOCATION_FILTERS,
    REVIEW_STATUSES,
    SHORTLIST_FILTERS,
    NOTE_MAX_LENGTH,
    buildSafeLinkedInProfileHref,
    createWorkspaceRunId,
    defaultWorkspaceViewState,
    normalizeWorkspaceViewState,
    mapDedupedResultToWorkspaceCandidate,
    mapDedupedResultsToWorkspaceCandidates,
    applyWorkspaceView,
    createReviewStateForCandidates,
    setWorkspaceReviewStatus,
    toggleWorkspaceShortlist,
    setWorkspaceCandidateNote,
    isWorkspaceCandidateShortlisted,
    reviewStatusLabel,
    reviewStatusClassName,
    severityClassName,
  };
})(typeof window !== "undefined" ? window : globalThis);
