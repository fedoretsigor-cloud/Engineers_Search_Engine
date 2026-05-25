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
  const CANDIDATE_EXPLANATION_VERSION = "candidate_explanation_v1";
  const TOP_CANDIDATE_RECOMMENDATION_VERSION = "top_candidate_recommendation_v1";
  const TOP_CANDIDATE_RECOMMENDATION_DEFAULT_LIMIT = 3;
  const SELECTED_CANDIDATE_COMPARISON_VERSION = "selected_candidate_comparison_v1";
  const SELECTED_CANDIDATE_COMPARISON_DEFAULT_LIMIT = 4;
  const SELECTED_CANDIDATE_FIT_GAP_VERSION = "selected_candidate_fit_gap_v1";
  const SELECTED_CANDIDATE_FIT_GAP_DEFAULT_LIMIT = 4;
  const WORKSPACE_REFINEMENT_SUGGESTIONS_VERSION = "workspace_refinement_suggestions_v1";
  const WORKSPACE_REFINEMENT_SUGGESTIONS_DEFAULT_LIMIT = 3;
  const CANDIDATE_EXPLANATION_WORDING_USE_CASE = "candidate_explanation";
  const CANDIDATE_EXPLANATION_WORDING_REQUEST_VERSION = "candidate_explanation_wording_request_v1";
  const CANDIDATE_EXPLANATION_WORDING_TARGET_LANGUAGE = "en";
  const EXPLANATION_REASON_CODES = Object.freeze({
    QUALITY_SCORE_HIGH: "quality_score_high",
    QUALITY_SCORE_MEDIUM: "quality_score_medium",
    QUALITY_SCORE_MISSING: "quality_score_missing",
    TARGET_LOCATION: "target_location",
    LOCATION_UNKNOWN_OR_WEAK: "location_unknown_or_weak",
    LOCATION_FOREIGN_OR_MISMATCH: "location_foreign_or_mismatch",
    STACK_CONFIRMED: "stack_confirmed",
    STACK_QUERY_SOURCE_ONLY: "stack_query_source_only",
    STACK_NOT_VISIBLE: "stack_not_visible",
    ROLE_OR_TECHNOLOGY_VISIBLE: "role_or_technology_visible",
    SENIORITY_UNKNOWN: "seniority_unknown",
    STABLE_PROFILE_IDENTITY: "stable_profile_identity",
    PROFILE_HREF_MISSING_OR_UNSAFE: "profile_href_missing_or_unsafe",
    REVIEW_FLAGS_PRESENT: "review_flags_present",
    QUERY_SOURCE: "query_source",
    QUALITY_COMPONENT: "quality_component",
    QUALITY_PENALTY: "quality_penalty",
  });
  const CANDIDATE_EXPLANATION_LIMITS = Object.freeze({
    positive_signals: 3,
    cautions: 3,
    evidence_items: 4,
    fact_terms: 4,
    fact_items: 3,
  });
  const SAFE_SEVERITIES = new Set(["info", "warning", "risk", "positive", "high", "medium", "low"]);
  const SAFE_REVIEW_STATUSES = new Set(Object.values(REVIEW_STATUSES));
  const SAFE_EXPLANATION_REASON_CODES = new Set(Object.values(EXPLANATION_REASON_CODES));
  const WORDING_SAFE_FACT_KEYS = Object.freeze({
    quality_score_high: Object.freeze({ score: "number", bucket: "string" }),
    quality_score_medium: Object.freeze({ score: "number", bucket: "string" }),
    quality_score_missing: Object.freeze({}),
    target_location: Object.freeze({ status: "string", group: "string", terms: "string_list" }),
    location_unknown_or_weak: Object.freeze({ status: "string", group: "string", terms: "string_list" }),
    location_foreign_or_mismatch: Object.freeze({ status: "string", group: "string", terms: "string_list" }),
    stack_confirmed: Object.freeze({ terms: "string_list", source: "string" }),
    stack_query_source_only: Object.freeze({}),
    stack_not_visible: Object.freeze({ missing_terms: "string_list" }),
    role_or_technology_visible: Object.freeze({
      role_fit: "string",
      technology: "string",
      technology_fit: "string",
    }),
    seniority_unknown: Object.freeze({}),
    stable_profile_identity: Object.freeze({ profile_href_present: "boolean" }),
    profile_href_missing_or_unsafe: Object.freeze({}),
    review_flags_present: Object.freeze({ codes: "string_list" }),
    query_source: Object.freeze({ ids: "string_list", categories: "string_list" }),
    quality_component: Object.freeze({ components: "quality_components" }),
    quality_penalty: Object.freeze({ penalties: "quality_penalties" }),
  });
  const EXPORT_SCOPES = Object.freeze({
    VISIBLE: "visible",
    SHORTLISTED: "shortlisted",
    ALL: "all",
  });
  const EXPORT_FORMATS = Object.freeze({
    CSV: "csv",
    MARKDOWN: "markdown",
  });
  const EXPORT_CSV_COLUMNS = Object.freeze([
    "display_index",
    "candidate_name",
    "headline",
    "profile_url",
    "identity_stable",
    "quality_score",
    "quality_bucket",
    "role",
    "role_fit",
    "technology",
    "technology_fit",
    "seniority",
    "location",
    "location_status",
    "source",
    "stack_fit",
    "selected_stack_terms",
    "missing_stack_terms",
    "review_flags",
    "review_status",
    "shortlisted",
    "notes",
    "explanation_summary",
    "explanation_codes",
    "query_source_ids",
    "snippet",
  ]);
  const EXPORT_TEXT_LIMITS = Object.freeze({
    candidate_name: 160,
    headline: 240,
    compact: 160,
    joined: 600,
    notes: NOTE_MAX_LENGTH,
    explanation_summary: 400,
    snippet: 600,
  });
  const SAFE_EXPORT_EXECUTION_MODES = new Set(["single_wave", "multi_wave", "search"]);

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

  function uniqueStrings(values, limit = CANDIDATE_EXPLANATION_LIMITS.fact_terms) {
    const seen = new Set();
    const output = [];
    for (const value of arrayValue(values)) {
      const text = stringValue(value);
      const key = text.toLowerCase();
      if (!text || seen.has(key)) {
        continue;
      }
      seen.add(key);
      output.push(text);
      if (output.length >= limit) {
        break;
      }
    }
    return output;
  }

  function boundedText(value, maxLength = 120) {
    const text = stringValue(value);
    if (text.length <= maxLength) {
      return text;
    }
    return `${text.slice(0, maxLength - 3)}...`;
  }

  function boundedNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : undefined;
  }

  function cleanFacts(facts) {
    const cleaned = {};
    Object.entries(facts || {}).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }
      if (Array.isArray(value)) {
        const items = value
          .slice(0, CANDIDATE_EXPLANATION_LIMITS.fact_items)
          .map((item) => {
            if (typeof item === "string") {
              return boundedText(item, 80);
            }
            if (item && typeof item === "object") {
              return cleanFacts(item);
            }
            return item;
          })
          .filter((item) => item !== undefined && item !== null && item !== "");
        if (items.length) {
          cleaned[key] = items;
        }
        return;
      }
      if (typeof value === "object") {
        const item = cleanFacts(value);
        if (Object.keys(item).length) {
          cleaned[key] = item;
        }
        return;
      }
      if (typeof value === "number") {
        const number = boundedNumber(value);
        if (number !== undefined) {
          cleaned[key] = number;
        }
        return;
      }
      if (typeof value === "boolean") {
        cleaned[key] = value;
        return;
      }
      const text = boundedText(value, 120);
      if (text) {
        cleaned[key] = text;
      }
    });
    return cleaned;
  }

  function makeReason(code, label, facts) {
    if (!SAFE_EXPLANATION_REASON_CODES.has(code)) {
      return null;
    }
    const text = stringValue(label);
    if (!text) {
      return null;
    }
    const reason = {
      code,
      label: boundedText(text, 180),
    };
    const cleanedFacts = cleanFacts(facts);
    if (Object.keys(cleanedFacts).length) {
      reason.facts = cleanedFacts;
    }
    return reason;
  }

  function addReason(reasons, reason) {
    if (!reason || reasons.some((item) => item.code === reason.code)) {
      return;
    }
    reasons.push(reason);
  }

  function limitReasons(reasons, limit) {
    return arrayValue(reasons).slice(0, limit);
  }

  function resultForCandidate(candidate) {
    return (candidate && candidate.raw && candidate.raw.result) || {};
  }

  function directStackEvidence(candidate) {
    const result = resultForCandidate(candidate);
    return arrayValue(result.stack_evidence).filter((item) => {
      const source = lowerValue(item && item.source);
      const evidenceType = lowerValue(item && item.evidence_type);
      return source !== "query_source" && evidenceType !== "stack_query_group";
    });
  }

  function directStackTerms(candidate) {
    const evidenceTerms = directStackEvidence(candidate).flatMap((item) => [
      item && item.term,
      ...(Array.isArray(item && item.terms) ? item.terms : []),
    ]);
    return uniqueStrings([...arrayValue(candidate && candidate.selected_stack_terms_found), ...evidenceTerms]);
  }

  function locationEvidenceFacts(candidate) {
    const raw = (candidate && candidate.raw) || {};
    const result = resultForCandidate(candidate);
    const currentLines = uniqueStrings(raw.current_location_lines || result.current_location_lines);
    const currentLine = firstUsefulText([
      raw.current_location_line,
      result.current_location_line,
      currentLines[0],
    ]);
    const terms = uniqueStrings(raw.location_signal_terms || result.location_signal_terms);
    return {
      status: candidate.location_status,
      group: candidate.location_group,
      current_location_line: currentLine,
      terms,
    };
  }

  function hasPositiveRoleOrTechnologyEvidence(candidate) {
    const result = resultForCandidate(candidate);
    const roleFit = lowerValue(result.role_fit);
    const technologyFit = lowerValue(result.technology_fit);
    const roleVisible =
      Boolean(roleFit) &&
      roleFit !== "missing_role" &&
      roleFit !== "missing" &&
      roleFit !== "ambiguous" &&
      roleFit !== "related_only";
    const technologyVisible = technologyFit === "exact";
    return roleVisible || technologyVisible;
  }

  function roleTechnologyFacts(candidate) {
    const result = resultForCandidate(candidate);
    return {
      role: firstUsefulText([result.role_display, candidate.headline, candidate.raw_title]),
      role_fit: result.role_fit,
      technology: result.technology_display,
      technology_fit: result.technology_fit,
    };
  }

  function qualityComponentFacts(candidate) {
    return arrayValue(resultForCandidate(candidate).quality_score_breakdown)
      .filter((item) => stringValue(item && item.component))
      .slice(0, CANDIDATE_EXPLANATION_LIMITS.fact_items)
      .map((item) => ({
        component: item.component,
        points: boundedNumber(item.points),
        max_points: boundedNumber(item.max_points),
        fit: item.status || item.fit,
      }));
  }

  function qualityPenaltyFacts(candidate) {
    return arrayValue(resultForCandidate(candidate).quality_score_penalties)
      .filter((item) => stringValue(item && item.reason) || boundedNumber(item && item.points) !== undefined)
      .slice(0, CANDIDATE_EXPLANATION_LIMITS.fact_items)
      .map((item) => ({
        points: boundedNumber(item.points),
        reason: item.reason,
      }));
  }

  function querySourceFacts(candidate) {
    const sources = arrayValue(candidate && candidate.query_sources);
    const ids = uniqueStrings(sources.map((source) => source && (source.id || source.category || "query")));
    const categories = uniqueStrings(sources.map((source) => source && source.category));
    return { ids, categories };
  }

  function reviewFlagFacts(candidate) {
    const flags = arrayValue(candidate && candidate.review_flags);
    return {
      codes: uniqueStrings(flags.map((flag) => flag && (flag.code || flag.label))),
      labels: uniqueStrings(flags.map((flag) => flag && flag.label)),
    };
  }

  function buildExplanationSummary(positiveSignals, cautions) {
    const positiveCodes = new Set(positiveSignals.map((reason) => reason.code));
    const cautionCodes = new Set(cautions.map((reason) => reason.code));

    if (cautionCodes.has(EXPLANATION_REASON_CODES.LOCATION_FOREIGN_OR_MISMATCH)) {
      return "Candidate may not match the target location. Review location evidence before keeping them.";
    }
    if (
      cautionCodes.has(EXPLANATION_REASON_CODES.STACK_QUERY_SOURCE_ONLY) ||
      cautionCodes.has(EXPLANATION_REASON_CODES.STACK_NOT_VISIBLE)
    ) {
      return "Relevant candidate, but selected stack is not confirmed in the returned public data.";
    }
    if (
      positiveCodes.has(EXPLANATION_REASON_CODES.QUALITY_SCORE_HIGH) &&
      positiveCodes.has(EXPLANATION_REASON_CODES.TARGET_LOCATION) &&
      positiveCodes.has(EXPLANATION_REASON_CODES.STACK_CONFIRMED)
    ) {
      return "Candidate has strong returned fit signals.";
    }
    if (positiveSignals.length && cautions.length) {
      return "Candidate has useful returned signals, with cautions to review.";
    }
    if (positiveSignals.length) {
      return "Candidate has returned evidence that may support relevance.";
    }
    if (cautions.length) {
      return "Candidate needs manual review because returned evidence is limited or uncertain.";
    }
    return "Returned data is limited. Review candidate details manually.";
  }

  function buildCandidateExplanation(candidate) {
    const positiveSignals = [];
    const cautions = [];
    const evidenceItems = [];
    const stackTerms = directStackTerms(candidate || {});
    const locationFacts = locationEvidenceFacts(candidate || {});
    const queryFacts = querySourceFacts(candidate || {});
    const penalties = qualityPenaltyFacts(candidate || {});
    const qualityComponents = qualityComponentFacts(candidate || {});

    if (candidate && candidate.has_quality_score) {
      const bucket = qualityBucket(candidate.quality_score);
      if (bucket === "high") {
        addReason(
          positiveSignals,
          makeReason(EXPLANATION_REASON_CODES.QUALITY_SCORE_HIGH, "Quality score is high", {
            score: candidate.quality_score,
            bucket,
          })
        );
      } else if (bucket === "medium") {
        addReason(
          positiveSignals,
          makeReason(EXPLANATION_REASON_CODES.QUALITY_SCORE_MEDIUM, "Quality score is medium", {
            score: candidate.quality_score,
            bucket,
          })
        );
      }
    } else {
      addReason(cautions, makeReason(EXPLANATION_REASON_CODES.QUALITY_SCORE_MISSING, "Quality score is missing"));
    }

    if (candidate && candidate.location_group === "target") {
      addReason(
        positiveSignals,
        makeReason(EXPLANATION_REASON_CODES.TARGET_LOCATION, "Target location signal is present", locationFacts)
      );
    } else if (candidate && candidate.location_group === "foreign") {
      addReason(
        cautions,
        makeReason(EXPLANATION_REASON_CODES.LOCATION_FOREIGN_OR_MISMATCH, "Current location appears outside the target location", locationFacts)
      );
    } else {
      addReason(
        cautions,
        makeReason(EXPLANATION_REASON_CODES.LOCATION_UNKNOWN_OR_WEAK, "Location needs manual review", locationFacts)
      );
    }

    if (stackTerms.length) {
      addReason(
        positiveSignals,
        makeReason(EXPLANATION_REASON_CODES.STACK_CONFIRMED, `Visible stack terms: ${stackTerms.join(", ")}`, {
          terms: stackTerms,
          source: "candidate_text",
        })
      );
    } else if (candidate && candidate.stack_fit === "query_source_only") {
      addReason(
        cautions,
        makeReason(
          EXPLANATION_REASON_CODES.STACK_QUERY_SOURCE_ONLY,
          "Selected stack is query-source only and is not confirmed in returned candidate text"
        )
      );
    } else if (candidate && candidate.stack_fit === "not_visible") {
      addReason(
        cautions,
        makeReason(EXPLANATION_REASON_CODES.STACK_NOT_VISIBLE, "Selected stack is not visible in returned public data", {
          missing_terms: candidate.missing_selected_stack_terms || [],
        })
      );
    }

    if (hasPositiveRoleOrTechnologyEvidence(candidate || {})) {
      addReason(
        positiveSignals,
        makeReason(EXPLANATION_REASON_CODES.ROLE_OR_TECHNOLOGY_VISIBLE, "Role or technology evidence is visible", roleTechnologyFacts(candidate || {}))
      );
    }

    if (
      candidate &&
      candidate.identity &&
      candidate.identity.is_stable_identity &&
      candidate.identity.safe_profile_href
    ) {
      addReason(
        positiveSignals,
        makeReason(EXPLANATION_REASON_CODES.STABLE_PROFILE_IDENTITY, "Stable LinkedIn profile identity is available", {
          profile_href_present: Boolean(candidate.identity.safe_profile_href),
        })
      );
    } else {
      addReason(
        cautions,
        makeReason(EXPLANATION_REASON_CODES.PROFILE_HREF_MISSING_OR_UNSAFE, "Safe profile link is missing or not validated")
      );
    }

    if (!isUsefulText(candidate && candidate.seniority_level)) {
      addReason(cautions, makeReason(EXPLANATION_REASON_CODES.SENIORITY_UNKNOWN, "Seniority is unknown"));
    }

    if (arrayValue(candidate && candidate.review_flags).length) {
      addReason(
        cautions,
        makeReason(EXPLANATION_REASON_CODES.REVIEW_FLAGS_PRESENT, "Review flags need attention", reviewFlagFacts(candidate || {}))
      );
    }

    if (penalties.length) {
      addReason(
        cautions,
        makeReason(EXPLANATION_REASON_CODES.QUALITY_PENALTY, "Quality penalties are present", {
          penalties,
        })
      );
    }

    if (queryFacts.ids.length) {
      addReason(
        evidenceItems,
        makeReason(EXPLANATION_REASON_CODES.QUERY_SOURCE, `Matched query sources: ${queryFacts.ids.join(", ")}`, queryFacts)
      );
    }
    if (qualityComponents.length) {
      addReason(
        evidenceItems,
        makeReason(EXPLANATION_REASON_CODES.QUALITY_COMPONENT, "Quality breakdown components are available", {
          components: qualityComponents,
        })
      );
    }

    const limitedPositiveSignals = limitReasons(
      positiveSignals,
      CANDIDATE_EXPLANATION_LIMITS.positive_signals
    );
    const limitedCautions = limitReasons(cautions, CANDIDATE_EXPLANATION_LIMITS.cautions);
    const limitedEvidenceItems = limitReasons(
      evidenceItems,
      CANDIDATE_EXPLANATION_LIMITS.evidence_items
    );

    return {
      version: CANDIDATE_EXPLANATION_VERSION,
      summary: buildExplanationSummary(limitedPositiveSignals, limitedCautions),
      positive_signals: limitedPositiveSignals,
      cautions: limitedCautions,
      evidence_items: limitedEvidenceItems,
      source: "deterministic_workspace_facts",
    };
  }

  function explanationCodes(explanation, section) {
    return new Set(arrayValue(explanation && explanation[section]).map((reason) => reason && reason.code));
  }

  function reviewFlagSeverityCounts(candidate) {
    return arrayValue(candidate && candidate.review_flags).reduce(
      (counts, flag) => {
        const severity = normalizeSeverity(flag && flag.severity);
        if (severity === "high") {
          counts.high += 1;
        } else if (severity === "medium") {
          counts.medium += 1;
        } else if (severity === "risk" || severity === "warning") {
          counts.warning += 1;
        }
        return counts;
      },
      { high: 0, medium: 0, warning: 0 }
    );
  }

  function recommendationSafeText(value, fallback, maxLength = 160) {
    const text = boundedText(value, maxLength).replace(/\s+/g, " ").trim();
    if (!text || /(https?:\/\/|www\.|linkedin\.com|\/in\/|mailto:)/i.test(text)) {
      return fallback;
    }
    return text;
  }

  function topCandidateRank(candidate, explanation, index) {
    const positiveCodes = explanationCodes(explanation, "positive_signals");
    const cautionCodes = explanationCodes(explanation, "cautions");
    const flagCounts = reviewFlagSeverityCounts(candidate);
    return {
      has_quality_score: candidate && candidate.has_quality_score ? 1 : 0,
      quality_score: candidate && candidate.has_quality_score ? finiteNumber(candidate.quality_score, 0) : -1,
      target_location: positiveCodes.has(EXPLANATION_REASON_CODES.TARGET_LOCATION) ? 1 : 0,
      stack_confirmed: positiveCodes.has(EXPLANATION_REASON_CODES.STACK_CONFIRMED) ? 1 : 0,
      role_or_technology_visible: positiveCodes.has(EXPLANATION_REASON_CODES.ROLE_OR_TECHNOLOGY_VISIBLE) ? 1 : 0,
      stable_identity: positiveCodes.has(EXPLANATION_REASON_CODES.STABLE_PROFILE_IDENTITY) ? 1 : 0,
      high_flags: flagCounts.high,
      medium_flags: flagCounts.medium,
      warning_flags: flagCounts.warning,
      caution_count: arrayValue(explanation && explanation.cautions).length,
      order_index: Number.isFinite(Number(candidate && candidate.order_index))
        ? Number(candidate.order_index)
        : index,
    };
  }

  function compareTopCandidateRecommendation(left, right) {
    const leftRank = left._rank;
    const rightRank = right._rank;
    return (
      rightRank.has_quality_score - leftRank.has_quality_score ||
      rightRank.quality_score - leftRank.quality_score ||
      rightRank.target_location - leftRank.target_location ||
      rightRank.stack_confirmed - leftRank.stack_confirmed ||
      rightRank.role_or_technology_visible - leftRank.role_or_technology_visible ||
      rightRank.stable_identity - leftRank.stable_identity ||
      leftRank.high_flags - rightRank.high_flags ||
      leftRank.medium_flags - rightRank.medium_flags ||
      leftRank.warning_flags - rightRank.warning_flags ||
      leftRank.caution_count - rightRank.caution_count ||
      leftRank.order_index - rightRank.order_index
    );
  }

  function topCandidateReasonLabels(candidate, explanation) {
    const positiveCodes = explanationCodes(explanation, "positive_signals");
    const reasons = [];
    if (candidate && candidate.has_quality_score) {
      reasons.push(`Quality score ${candidate.quality_score} (${candidate.quality_bucket || qualityBucket(candidate.quality_score)})`);
    }
    if (positiveCodes.has(EXPLANATION_REASON_CODES.TARGET_LOCATION)) {
      reasons.push("Target location signal is present");
    }
    if (positiveCodes.has(EXPLANATION_REASON_CODES.STACK_CONFIRMED)) {
      const terms = directStackTerms(candidate).slice(0, 3);
      reasons.push(terms.length ? `Selected stack is visible: ${terms.join(", ")}` : "Selected stack is visible");
    }
    if (positiveCodes.has(EXPLANATION_REASON_CODES.ROLE_OR_TECHNOLOGY_VISIBLE)) {
      reasons.push("Role or technology evidence is visible");
    }
    if (positiveCodes.has(EXPLANATION_REASON_CODES.STABLE_PROFILE_IDENTITY)) {
      reasons.push("Stable profile identity is available");
    }
    return reasons.slice(0, 4);
  }

  function topCandidateCautionLabels(candidate, explanation) {
    const cautionCodes = explanationCodes(explanation, "cautions");
    const flagCounts = reviewFlagSeverityCounts(candidate);
    const cautions = [];
    if (cautionCodes.has(EXPLANATION_REASON_CODES.LOCATION_UNKNOWN_OR_WEAK)) {
      cautions.push("Location needs manual review");
    }
    if (cautionCodes.has(EXPLANATION_REASON_CODES.STACK_QUERY_SOURCE_ONLY)) {
      cautions.push("Selected stack is query-source only");
    }
    if (cautionCodes.has(EXPLANATION_REASON_CODES.STACK_NOT_VISIBLE)) {
      cautions.push("Selected stack is not visible");
    }
    if (flagCounts.high || flagCounts.medium || flagCounts.warning) {
      cautions.push("Review flags need attention");
    }
    if (cautionCodes.has(EXPLANATION_REASON_CODES.SENIORITY_UNKNOWN)) {
      cautions.push("Seniority is unknown");
    }
    if (cautionCodes.has(EXPLANATION_REASON_CODES.PROFILE_HREF_MISSING_OR_UNSAFE)) {
      cautions.push("Safe profile link is missing or not validated");
    }
    return cautions.slice(0, 3);
  }

  function topCandidateSummary(displayName, reasons, cautions) {
    if (reasons.length >= 3 && !cautions.length) {
      return `Start with ${displayName}: returned workspace facts show several strong fit signals.`;
    }
    if (reasons.length >= 2 && cautions.length) {
      return `Start with ${displayName}: returned fit signals are strong, with cautions to review.`;
    }
    if (reasons.length) {
      return `Start with ${displayName}: returned facts make this candidate a useful first review.`;
    }
    return `Start with ${displayName}: returned facts are limited, so review details manually.`;
  }

  function buildTopCandidateRecommendation(candidates, reviewStateByCandidateId = {}, options = {}) {
    const inputCandidates = arrayValue(candidates);
    const limit = Math.max(
      1,
      Math.min(
        5,
        Number.isFinite(Number(options.limit))
          ? Number(options.limit)
          : TOP_CANDIDATE_RECOMMENDATION_DEFAULT_LIMIT
      )
    );
    const scope = stringValue(options.scope) || "visible_candidates";
    const ranked = [];

    inputCandidates.forEach((candidate, index) => {
      if (!candidate || candidate.location_group === "foreign") {
        return;
      }
      const reviewState = candidateReviewState(reviewStateByCandidateId, candidate.candidate_id);
      if (reviewState.status === REVIEW_STATUSES.NOT_A_FIT) {
        return;
      }
      const explanation = buildCandidateExplanation(candidate);
      if (!explanation || explanation.source !== "deterministic_workspace_facts") {
        return;
      }
      const displayIndex = Number.isFinite(Number(candidate.display_index))
        ? Number(candidate.display_index)
        : index + 1;
      const displayName = recommendationSafeText(
        candidate.display_name,
        `Candidate ${displayIndex}`,
        EXPORT_TEXT_LIMITS.candidate_name
      );
      const headline = recommendationSafeText(
        candidate.headline || candidate.raw_title,
        "No headline returned.",
        EXPORT_TEXT_LIMITS.headline
      );
      const reasons = topCandidateReasonLabels(candidate, explanation);
      const cautions = topCandidateCautionLabels(candidate, explanation);
      ranked.push({
        _rank: topCandidateRank(candidate, explanation, index),
        display_index: displayIndex,
        display_name: displayName,
        headline,
        quality_score: candidate.has_quality_score ? candidate.quality_score : null,
        quality_bucket: candidate.has_quality_score ? candidate.quality_bucket || qualityBucket(candidate.quality_score) : "",
        location_status: recommendationSafeText(candidate.location_status, "unknown_current_location", 80),
        stack_fit: recommendationSafeText(candidate.stack_fit, "unknown", 80),
        summary: topCandidateSummary(displayName, reasons, cautions),
        reasons,
        cautions,
      });
    });

    ranked.sort(compareTopCandidateRecommendation);

    return {
      version: TOP_CANDIDATE_RECOMMENDATION_VERSION,
      source: "deterministic_workspace_facts",
      scope,
      candidates_analyzed: inputCandidates.length,
      candidates_considered: ranked.length,
      recommendations: ranked.slice(0, limit).map(({ _rank, ...item }) => item),
    };
  }

  function comparisonSafeText(value, fallback, maxLength = 160) {
    return recommendationSafeText(value, fallback, maxLength);
  }

  function comparisonReasonLabels(reasons, fallback) {
    const labels = arrayValue(reasons)
      .map((reason) => comparisonSafeText(reason && reason.label, "", 180))
      .filter(Boolean);
    return labels.length ? labels.slice(0, 3) : fallback ? [fallback] : [];
  }

  function comparisonReviewFlagLabels(candidate) {
    return arrayValue(candidate && candidate.review_flags)
      .map((flag) =>
        comparisonSafeText(flag && (flag.label || flag.code), "", EXPORT_TEXT_LIMITS.compact)
      )
      .filter(Boolean)
      .slice(0, 3);
  }

  function comparisonSelectedStackTerms(candidate) {
    return directStackTerms(candidate).map((term) => comparisonSafeText(term, "", 80)).filter(Boolean);
  }

  function selectedComparisonRow(candidate, explanation, index) {
    const roleTech = roleTechnologyFacts(candidate || {});
    const positiveCodes = explanationCodes(explanation, "positive_signals");
    const cautionCodes = explanationCodes(explanation, "cautions");
    const displayIndex = Number.isFinite(Number(candidate && candidate.display_index))
      ? Number(candidate.display_index)
      : index + 1;
    const displayName = comparisonSafeText(
      candidate && candidate.display_name,
      `Candidate ${displayIndex}`,
      EXPORT_TEXT_LIMITS.candidate_name
    );
    const headline = comparisonSafeText(
      (candidate && (candidate.headline || candidate.raw_title)) || "",
      "No headline returned.",
      EXPORT_TEXT_LIMITS.headline
    );
    const cautions = comparisonReasonLabels(explanation && explanation.cautions, "");
    if (candidate && candidate.location_group === "foreign" && !cautions.some((item) => /location/i.test(item))) {
      cautions.unshift("Current location appears outside the target location");
    }

    return {
      _positive_codes: positiveCodes,
      _caution_codes: cautionCodes,
      display_index: displayIndex,
      display_name: displayName,
      headline,
      quality_score: candidate && candidate.has_quality_score ? candidate.quality_score : null,
      quality_bucket: candidate && candidate.has_quality_score ? candidate.quality_bucket || qualityBucket(candidate.quality_score) : "",
      role: comparisonSafeText(roleTech.role, "n/a", EXPORT_TEXT_LIMITS.compact),
      technology: comparisonSafeText(roleTech.technology, "n/a", 80),
      location_status: comparisonSafeText(candidate && candidate.location_status, "unknown_current_location", 80),
      location_group: comparisonSafeText(candidate && candidate.location_group, "unknown_weak", 80),
      stack_fit: comparisonSafeText(candidate && candidate.stack_fit, "unknown", 80),
      stack_terms: comparisonSelectedStackTerms(candidate || {}).slice(0, 3),
      seniority: comparisonSafeText(candidate && candidate.seniority_level, "unknown", 80),
      positive_signals: comparisonReasonLabels(explanation && explanation.positive_signals, ""),
      cautions: cautions.slice(0, 4),
      review_flags: comparisonReviewFlagLabels(candidate),
    };
  }

  function uniqueComparisonValues(rows, field) {
    return uniqueStrings(rows.map((row) => row && row[field]), 6);
  }

  function buildComparisonSharedSignals(rows) {
    if (rows.length < 2) {
      return [];
    }
    const signals = [];
    if (rows.every((row) => row._positive_codes.has(EXPLANATION_REASON_CODES.TARGET_LOCATION))) {
      signals.push("All selected candidates have target-location signals in returned data");
    }
    if (rows.every((row) => row._positive_codes.has(EXPLANATION_REASON_CODES.STACK_CONFIRMED))) {
      signals.push("Selected stack is visible for all selected candidates");
    }
    if (rows.every((row) => row._positive_codes.has(EXPLANATION_REASON_CODES.ROLE_OR_TECHNOLOGY_VISIBLE))) {
      signals.push("Role or technology evidence is visible for all selected candidates");
    }
    const qualityBuckets = uniqueComparisonValues(rows.filter((row) => row.quality_score !== null), "quality_bucket");
    if (qualityBuckets.length === 1 && rows.every((row) => row.quality_score !== null)) {
      signals.push(`All selected candidates are in the ${qualityBuckets[0]} quality bucket`);
    }
    return signals.slice(0, 4);
  }

  function buildComparisonDifferences(rows, selectedCount) {
    if (rows.length < 2) {
      return [];
    }
    const differences = [];
    if (selectedCount > rows.length) {
      differences.push(`Showing first ${rows.length} of ${selectedCount} visible shortlisted candidates`);
    }

    const scored = rows.filter((row) => row.quality_score !== null);
    if (scored.length >= 2) {
      const orderedScores = scored.slice().sort((left, right) => left.quality_score - right.quality_score);
      const low = orderedScores[0];
      const high = orderedScores[orderedScores.length - 1];
      if (low.quality_score !== high.quality_score) {
        differences.push(`Quality scores range from ${low.quality_score} to ${high.quality_score}`);
      }
    }

    const stackFits = uniqueComparisonValues(rows, "stack_fit");
    if (stackFits.length > 1) {
      differences.push(`Stack visibility differs: ${stackFits.join(", ")}`);
    }
    const locationGroups = uniqueComparisonValues(rows, "location_group");
    if (locationGroups.length > 1) {
      differences.push(`Location confidence differs: ${locationGroups.join(", ")}`);
    }
    const visibleSeniorityCount = rows.filter((row) => isUsefulText(row.seniority)).length;
    if (visibleSeniorityCount > 0 && visibleSeniorityCount < rows.length) {
      differences.push(`Seniority is visible for ${visibleSeniorityCount} of ${rows.length} selected candidates`);
    }
    const flaggedCount = rows.filter((row) => row.review_flags.length > 0).length;
    if (flaggedCount) {
      differences.push(`Review flags appear for ${flaggedCount} selected candidates`);
    }
    const foreignLocationCount = rows.filter((row) => row.location_group === "foreign").length;
    if (foreignLocationCount) {
      differences.push(`${foreignLocationCount} selected candidates have foreign or mismatched location caution`);
    }
    return differences.slice(0, 5);
  }

  function buildSelectedCandidateComparison(candidates, reviewStateByCandidateId = {}, options = {}) {
    const inputCandidates = arrayValue(candidates);
    const maxCompared = Math.max(
      2,
      Math.min(
        6,
        Number.isFinite(Number(options.limit))
          ? Number(options.limit)
          : SELECTED_CANDIDATE_COMPARISON_DEFAULT_LIMIT
      )
    );
    const scope = stringValue(options.scope) || "visible_shortlisted_candidates";
    const selected = [];

    inputCandidates.forEach((candidate, index) => {
      if (!candidate) {
        return;
      }
      const reviewState = candidateReviewState(reviewStateByCandidateId, candidate.candidate_id);
      if (reviewState.status === REVIEW_STATUSES.NOT_A_FIT || !isWorkspaceCandidateShortlisted(reviewState)) {
        return;
      }
      const explanation = buildCandidateExplanation(candidate);
      if (!explanation || explanation.source !== "deterministic_workspace_facts") {
        return;
      }
      selected.push({
        candidate,
        explanation,
        index,
      });
    });

    const rows = selected
      .slice(0, maxCompared)
      .map((item) => selectedComparisonRow(item.candidate, item.explanation, item.index));
    const candidatesForOutput = rows.map(({ _positive_codes, _caution_codes, ...row }) => row);

    return {
      version: SELECTED_CANDIDATE_COMPARISON_VERSION,
      source: "deterministic_workspace_facts",
      scope,
      candidates_analyzed: inputCandidates.length,
      selected_count: selected.length,
      compared_count: rows.length,
      ready: selected.length >= 2,
      min_required: 2,
      max_compared: maxCompared,
      candidates: candidatesForOutput,
      shared_signals: buildComparisonSharedSignals(rows),
      differences: buildComparisonDifferences(rows, selected.length),
    };
  }

  function fitGapLabels(reasons) {
    return comparisonReasonLabels(reasons, "").slice(0, 4);
  }

  function addUniqueFitGapLabel(labels, label) {
    const safeLabel = comparisonSafeText(label, "", 180);
    if (safeLabel && !labels.includes(safeLabel)) {
      labels.push(safeLabel);
    }
  }

  function selectedFitGapRow(candidate, explanation, index) {
    const positiveCodes = explanationCodes(explanation, "positive_signals");
    const cautionCodes = explanationCodes(explanation, "cautions");
    const stackTerms = directStackTerms(candidate || {});
    const quality = candidate && candidate.has_quality_score ? qualityBucket(candidate.quality_score) : "";
    const fitLabels = fitGapLabels(explanation && explanation.positive_signals);
    if (candidate && candidate.has_quality_score && (quality === "high" || quality === "medium")) {
      addUniqueFitGapLabel(fitLabels, `Quality score is ${quality}`);
    }
    if (candidate && candidate.location_group === "target") {
      addUniqueFitGapLabel(fitLabels, "Target location signal is present");
    }
    if (stackTerms.length) {
      addUniqueFitGapLabel(fitLabels, `Visible stack terms: ${uniqueStrings(stackTerms, 3).join(", ")}`);
    }
    if (hasPositiveRoleOrTechnologyEvidence(candidate || {})) {
      addUniqueFitGapLabel(fitLabels, "Role or technology evidence is visible");
    }
    const displayIndex = Number.isFinite(Number(candidate && candidate.display_index))
      ? Number(candidate.display_index)
      : index + 1;
    const displayName = comparisonSafeText(
      candidate && candidate.display_name,
      `Candidate ${displayIndex}`,
      EXPORT_TEXT_LIMITS.candidate_name
    );
    const headline = comparisonSafeText(
      (candidate && (candidate.headline || candidate.raw_title)) || "",
      "No headline returned.",
      EXPORT_TEXT_LIMITS.headline
    );
    const gapLabels = fitGapLabels(explanation && explanation.cautions);
    if (candidate && candidate.location_group === "foreign" && !gapLabels.some((item) => /location/i.test(item))) {
      gapLabels.unshift("Current location appears outside the target location");
    }
    comparisonReviewFlagLabels(candidate).forEach((label) => {
      if (!gapLabels.includes(label)) {
        gapLabels.push(label);
      }
    });

    return {
      _positive_codes: positiveCodes,
      _caution_codes: cautionCodes,
      _fit_markers: {
        target_location: Boolean(candidate && candidate.location_group === "target"),
        stack_confirmed: stackTerms.length > 0,
        role_or_technology_visible: hasPositiveRoleOrTechnologyEvidence(candidate || {}),
        quality_useful: quality === "high" || quality === "medium",
      },
      display_index: displayIndex,
      display_name: displayName,
      headline,
      quality_score: candidate && candidate.has_quality_score ? candidate.quality_score : null,
      quality_bucket: candidate && candidate.has_quality_score ? candidate.quality_bucket || qualityBucket(candidate.quality_score) : "",
      fit_labels: fitLabels.slice(0, 5),
      gap_labels: gapLabels.slice(0, 5),
    };
  }

  function buildFitGapSharedFits(rows) {
    if (rows.length < 2) {
      return [];
    }
    const fits = [];
    if (rows.every((row) => row._fit_markers.target_location)) {
      fits.push("Target-location signal is present for all selected candidates");
    }
    if (rows.every((row) => row._fit_markers.stack_confirmed)) {
      fits.push("Selected stack is visible for all selected candidates");
    }
    if (rows.every((row) => row._fit_markers.role_or_technology_visible)) {
      fits.push("Role or technology evidence is visible for all selected candidates");
    }
    if (rows.every((row) => row._fit_markers.quality_useful)) {
      fits.push("All selected candidates have high or medium returned quality signals");
    }
    return fits.slice(0, 4);
  }

  function buildFitGapSharedGaps(rows) {
    if (rows.length < 2) {
      return [];
    }
    const gaps = [];
    if (rows.every((row) => row._caution_codes.has(EXPLANATION_REASON_CODES.SENIORITY_UNKNOWN))) {
      gaps.push("Seniority is not visible for all selected candidates");
    }
    if (
      rows.every(
        (row) =>
          row._caution_codes.has(EXPLANATION_REASON_CODES.STACK_QUERY_SOURCE_ONLY) ||
          row._caution_codes.has(EXPLANATION_REASON_CODES.STACK_NOT_VISIBLE)
      )
    ) {
      gaps.push("Selected stack is not confirmed in returned data for all selected candidates");
    }
    if (rows.every((row) => row._caution_codes.has(EXPLANATION_REASON_CODES.LOCATION_UNKNOWN_OR_WEAK))) {
      gaps.push("Location needs manual review for all selected candidates");
    }
    if (rows.every((row) => row._caution_codes.has(EXPLANATION_REASON_CODES.LOCATION_FOREIGN_OR_MISMATCH))) {
      gaps.push("Returned current-location data appears outside the target for all selected candidates");
    }
    if (rows.every((row) => row._caution_codes.has(EXPLANATION_REASON_CODES.PROFILE_HREF_MISSING_OR_UNSAFE))) {
      gaps.push("Safe profile link is missing or not validated for all selected candidates");
    }
    if (rows.every((row) => row._caution_codes.has(EXPLANATION_REASON_CODES.REVIEW_FLAGS_PRESENT))) {
      gaps.push("Review flags need attention for all selected candidates");
    }
    return gaps.slice(0, 4);
  }

  function buildFitGapSummary(rows, sharedFits, sharedGaps) {
    if (rows.length < 2) {
      return "Shortlist at least two visible candidates to explain fit and gaps.";
    }
    if (sharedFits.length && sharedGaps.length) {
      return "Selected candidates share useful returned fit signals, with gaps that need manual review.";
    }
    if (sharedFits.length) {
      return "Selected candidates share returned fit signals; compare individual gaps before narrowing the review.";
    }
    if (sharedGaps.length) {
      return "Selected candidates share manual-review gaps; returned fit evidence is limited across the selected set.";
    }
    return "Selected candidates have mixed returned evidence; compare individual fit and gap labels before narrowing the review.";
  }

  function buildSelectedCandidateFitGapExplanation(candidates, reviewStateByCandidateId = {}, options = {}) {
    const inputCandidates = arrayValue(candidates);
    const maxCompared = Math.max(
      2,
      Math.min(
        6,
        Number.isFinite(Number(options.limit))
          ? Number(options.limit)
          : SELECTED_CANDIDATE_FIT_GAP_DEFAULT_LIMIT
      )
    );
    const scope = stringValue(options.scope) || "visible_shortlisted_candidates";
    const selected = [];

    inputCandidates.forEach((candidate, index) => {
      if (!candidate) {
        return;
      }
      const reviewState = candidateReviewState(reviewStateByCandidateId, candidate.candidate_id);
      if (reviewState.status === REVIEW_STATUSES.NOT_A_FIT || !isWorkspaceCandidateShortlisted(reviewState)) {
        return;
      }
      const explanation = buildCandidateExplanation(candidate);
      if (!explanation || explanation.source !== "deterministic_workspace_facts") {
        return;
      }
      selected.push({
        candidate,
        explanation,
        index,
      });
    });

    const rows = selected
      .slice(0, maxCompared)
      .map((item) => selectedFitGapRow(item.candidate, item.explanation, item.index));
    const sharedFits = buildFitGapSharedFits(rows);
    const sharedGaps = buildFitGapSharedGaps(rows);
    const candidateFitGaps = rows.map(({ _positive_codes, _caution_codes, _fit_markers, ...row }) => row);

    return {
      version: SELECTED_CANDIDATE_FIT_GAP_VERSION,
      source: "deterministic_workspace_facts",
      scope,
      candidates_analyzed: inputCandidates.length,
      selected_count: selected.length,
      compared_count: rows.length,
      ready: selected.length >= 2,
      min_required: 2,
      max_compared: maxCompared,
      summary: buildFitGapSummary(rows, sharedFits, sharedGaps),
      shared_fits: sharedFits,
      shared_gaps: sharedGaps,
      candidate_fit_gaps: candidateFitGaps,
    };
  }

  function emptyRefinementStats() {
    return {
      visible_candidates: 0,
      shortlisted: 0,
      not_a_fit: 0,
      high_quality: 0,
      medium_quality: 0,
      low_quality: 0,
      missing_quality: 0,
      stack_confirmed: 0,
      stack_needs_review: 0,
      target_location: 0,
      location_needs_review: 0,
      review_flagged: 0,
    };
  }

  function workspaceRefinementStats(candidates, reviewStateByCandidateId) {
    const stats = emptyRefinementStats();
    arrayValue(candidates).forEach((candidate) => {
      if (!candidate) {
        return;
      }
      stats.visible_candidates += 1;
      const reviewState = candidateReviewState(reviewStateByCandidateId, candidate.candidate_id);
      if (isWorkspaceCandidateShortlisted(reviewState)) {
        stats.shortlisted += 1;
      }
      if (reviewState.status === REVIEW_STATUSES.NOT_A_FIT) {
        stats.not_a_fit += 1;
      }
      if (candidate.has_quality_score) {
        const bucket = candidate.quality_bucket || qualityBucket(candidate.quality_score);
        if (bucket === "high") {
          stats.high_quality += 1;
        } else if (bucket === "medium") {
          stats.medium_quality += 1;
        } else {
          stats.low_quality += 1;
        }
      } else {
        stats.missing_quality += 1;
      }
      if (candidate.stack_fit === "confirmed") {
        stats.stack_confirmed += 1;
      } else if (candidate.stack_fit === "query_source_only" || candidate.stack_fit === "not_visible") {
        stats.stack_needs_review += 1;
      }
      if (candidate.location_group === "target") {
        stats.target_location += 1;
      } else if (candidate.location_group === "unknown_weak" || candidate.location_group === "foreign") {
        stats.location_needs_review += 1;
      }
      if (arrayValue(candidate.review_flags).length) {
        stats.review_flagged += 1;
      }
    });
    return stats;
  }

  function boundedSuggestion(type, title, reason, guidance) {
    const suggestion = {
      suggestion_type: comparisonSafeText(type, "review_guidance", 60),
      title: comparisonSafeText(title, "Review current candidates", 120),
      reason: comparisonSafeText(reason, "Based on current visible workspace facts.", 220),
      guidance: comparisonSafeText(guidance, "Use the current workspace before changing the search.", 260),
    };
    return suggestion.title && suggestion.reason && suggestion.guidance ? suggestion : null;
  }

  function addWorkspaceSuggestion(suggestions, type, title, reason, guidance) {
    const suggestion = boundedSuggestion(type, title, reason, guidance);
    if (!suggestion) {
      return;
    }
    if (suggestions.some((item) => item.suggestion_type === suggestion.suggestion_type)) {
      return;
    }
    suggestions.push(suggestion);
  }

  function buildWorkspaceRefinementSuggestions(candidates, reviewStateByCandidateId = {}, options = {}) {
    const inputCandidates = arrayValue(candidates);
    const limit = Math.max(
      1,
      Math.min(
        5,
        Number.isFinite(Number(options.limit))
          ? Number(options.limit)
          : WORKSPACE_REFINEMENT_SUGGESTIONS_DEFAULT_LIMIT
      )
    );
    const scope = "visible_candidates";
    const stats = workspaceRefinementStats(inputCandidates, reviewStateByCandidateId);
    const suggestions = [];
    const total = stats.visible_candidates;

    if (!total) {
      addWorkspaceSuggestion(
        suggestions,
        "adjust_view",
        "No visible candidates to review",
        "Current workspace filters show no visible candidates.",
        "Reset or adjust the workspace filters before changing the Search Brief."
      );
    } else {
      if (stats.shortlisted >= 2) {
        addWorkspaceSuggestion(
          suggestions,
          "review_selected",
          "Use selected comparison next",
          `${stats.shortlisted} visible candidates are shortlisted.`,
          "Review the selected comparison and fit/gap sections before changing the search."
        );
      } else if (total >= 2) {
        addWorkspaceSuggestion(
          suggestions,
          "shortlist_for_comparison",
          "Shortlist candidates for comparison",
          "At least two visible candidates are available for comparison.",
          "Shortlist two to four candidates that look relevant, then compare their fit and gaps."
        );
      }

      if (stats.high_quality > 0) {
        addWorkspaceSuggestion(
          suggestions,
          "review_strong_candidates",
          "Review strong candidates first",
          `${stats.high_quality} visible candidates are in the high quality bucket.`,
          "Start with the strongest visible candidates before refining the Search Brief."
        );
      }

      if (stats.stack_needs_review >= Math.max(2, Math.ceil(total * 0.5))) {
        addWorkspaceSuggestion(
          suggestions,
          "review_stack_visibility",
          "Check stack visibility",
          `${stats.stack_needs_review} visible candidates do not show confirmed selected stack evidence.`,
          "If stack is mandatory, write the exact stack requirement in chat before running a new search."
        );
      }

      if (stats.location_needs_review >= Math.max(2, Math.ceil(total * 0.3))) {
        addWorkspaceSuggestion(
          suggestions,
          "review_location_confidence",
          "Check location confidence",
          `${stats.location_needs_review} visible candidates have weak, unknown, or mismatched location signals.`,
          "Review workspace location signals; refine location wording in chat only if the current results are too uncertain."
        );
      }

      if (stats.review_flagged > 0) {
        addWorkspaceSuggestion(
          suggestions,
          "review_flags",
          "Review flagged candidates",
          `${stats.review_flagged} visible candidates have review flags.`,
          "Inspect flagged candidates in the workspace before shortlisting or changing the Search Brief."
        );
      }
    }

    if (!suggestions.length) {
      addWorkspaceSuggestion(
        suggestions,
        "continue_review",
        "Continue current review",
        "Current visible candidates have enough returned evidence for manual review.",
        "Review visible candidates first; refine the Search Brief in chat only after the current set is not useful."
      );
    }

    return {
      version: WORKSPACE_REFINEMENT_SUGGESTIONS_VERSION,
      source: "deterministic_workspace_facts",
      scope,
      candidates_analyzed: inputCandidates.length,
      stats,
      suggestions: suggestions.slice(0, limit),
    };
  }

  function normalizeWordingText(value, maxLength = 160) {
    const text = stringValue(value).replace(/\s+/g, " ").trim();
    if (!text || text.length > maxLength || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(text)) {
      return "";
    }
    if (/(https?:\/\/|www\.|linkedin\.com|\/in\/|javascript:|mailto:|<|>|\[[^\]]+\]\([^)]+\))/i.test(text)) {
      return "";
    }
    return text;
  }

  function normalizeWordingStringList(value) {
    const terms = [];
    const seen = new Set();
    for (const item of arrayValue(value).slice(0, 8)) {
      const text = normalizeWordingText(item, 80);
      if (!text) {
        return null;
      }
      const key = text.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        terms.push(text);
      }
    }
    return terms;
  }

  function normalizeWordingNumber(value) {
    if (typeof value !== "number" || !Number.isFinite(value) || value < -10000 || value > 10000) {
      return null;
    }
    return Number.isInteger(value) ? value : Number(value.toFixed(4));
  }

  function normalizeWordingQualityComponents(value) {
    return arrayValue(value)
      .slice(0, 5)
      .map((item) => {
        const source = item || {};
        const component = {};
        if (Object.prototype.hasOwnProperty.call(source, "component")) {
          component.component = normalizeWordingText(source.component, 80);
        }
        if (Object.prototype.hasOwnProperty.call(source, "fit")) {
          component.fit = normalizeWordingText(source.fit, 80);
        }
        if (Object.prototype.hasOwnProperty.call(source, "points")) {
          component.points = normalizeWordingNumber(source.points);
        }
        if (Object.prototype.hasOwnProperty.call(source, "max_points")) {
          component.max_points = normalizeWordingNumber(source.max_points);
        }
        Object.keys(component).forEach((key) => {
          if (component[key] === "" || component[key] === null) {
            delete component[key];
          }
        });
        return component;
      })
      .filter((item) => Object.keys(item).length);
  }

  function normalizeWordingQualityPenalties(value) {
    return arrayValue(value)
      .slice(0, 5)
      .map((item) => {
        const source = item || {};
        const penalty = {};
        if (Object.prototype.hasOwnProperty.call(source, "points")) {
          penalty.points = normalizeWordingNumber(source.points);
        }
        if (Object.prototype.hasOwnProperty.call(source, "reason")) {
          penalty.reason = normalizeWordingText(source.reason, 80);
        }
        Object.keys(penalty).forEach((key) => {
          if (penalty[key] === "" || penalty[key] === null) {
            delete penalty[key];
          }
        });
        return penalty;
      })
      .filter((item) => Object.keys(item).length);
  }

  function wordingSafeFactsForReason(code, facts) {
    const contract = WORDING_SAFE_FACT_KEYS[code] || {};
    const source = facts && typeof facts === "object" && !Array.isArray(facts) ? facts : {};
    const sanitized = {};
    Object.entries(contract).forEach(([key, kind]) => {
      if (!Object.prototype.hasOwnProperty.call(source, key)) {
        return;
      }
      let value = null;
      if (kind === "string") {
        value = normalizeWordingText(source[key], 80);
      } else if (kind === "string_list") {
        value = normalizeWordingStringList(source[key]);
      } else if (kind === "number") {
        value = normalizeWordingNumber(source[key]);
      } else if (kind === "boolean") {
        value = typeof source[key] === "boolean" ? source[key] : null;
      } else if (kind === "quality_components") {
        value = normalizeWordingQualityComponents(source[key]);
      } else if (kind === "quality_penalties") {
        value = normalizeWordingQualityPenalties(source[key]);
      }
      if (value !== "" && value !== null) {
        sanitized[key] = value;
      }
    });
    return sanitized;
  }

  function explanationReasonKey(section, index, code) {
    return `${section}[${index}]:${code}`;
  }

  function renderableExplanationReasonsForSection(explanation, section) {
    return arrayValue(explanation && explanation[section])
      .filter((reason) => reason && SAFE_EXPLANATION_REASON_CODES.has(reason.code))
      .map((reason, index) => {
        const label = normalizeWordingText(reason.label || reason.code, 160);
        return {
          reason_key: explanationReasonKey(section, index, reason.code),
          section,
          code: reason.code,
          label: label || reason.code,
          facts: wordingSafeFactsForReason(reason.code, reason.facts || {}),
        };
      });
  }

  function buildCandidateExplanationRenderableReasons(explanation) {
    return {
      positive_signals: renderableExplanationReasonsForSection(explanation, "positive_signals"),
      cautions: renderableExplanationReasonsForSection(explanation, "cautions"),
      evidence_items: renderableExplanationReasonsForSection(explanation, "evidence_items"),
    };
  }

  function candidateExplanationFingerprintPayload(request) {
    return {
      wording_use_case: request.wording_use_case,
      target_language: request.target_language,
      request_payload_contract_version: request.request_payload_contract_version,
      explanation_version: request.explanation_version,
      source: request.source,
      summary: request.summary,
      positive_signals: request.positive_signals,
      cautions: request.cautions,
      evidence_items: request.evidence_items,
    };
  }

  function canonicalJson(value) {
    if (value === null || typeof value !== "object") {
      return JSON.stringify(value);
    }
    if (Array.isArray(value)) {
      return `[${value.map((item) => canonicalJson(item)).join(",")}]`;
    }
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
      .join(",")}}`;
  }

  async function sha256Hex(text) {
    const encoder = (root.TextEncoder || globalThis.TextEncoder) && new (root.TextEncoder || globalThis.TextEncoder)();
    const cryptoSource = root.crypto || globalThis.crypto;
    if (cryptoSource && cryptoSource.subtle && encoder) {
      const digest = await cryptoSource.subtle.digest("SHA-256", encoder.encode(text));
      return Array.from(new Uint8Array(digest))
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");
    }
    const requireFn = root.require || globalThis.require;
    if (typeof requireFn === "function") {
      return requireFn("crypto").createHash("sha256").update(text, "utf8").digest("hex");
    }
    throw new Error("SHA-256 support is not available.");
  }

  async function candidateExplanationRequestFingerprint(request) {
    return `sha256:${await sha256Hex(canonicalJson(candidateExplanationFingerprintPayload(request)))}`;
  }

  function createWordingTargetKey(runCounter, index) {
    const safeRunCounter = Math.max(1, Math.floor(finiteNumber(runCounter, 1)));
    const safeIndex = Math.max(0, Math.floor(finiteNumber(index, 0)));
    return `wtk-${safeRunCounter}-${safeIndex + 1}`;
  }

  async function buildCandidateExplanationWordingRequest(config = {}) {
    const explanation = config.explanation || {};
    const renderableReasons = buildCandidateExplanationRenderableReasons(explanation);
    const request = {
      wording_use_case: CANDIDATE_EXPLANATION_WORDING_USE_CASE,
      request_payload_contract_version: CANDIDATE_EXPLANATION_WORDING_REQUEST_VERSION,
      target_language: config.targetLanguage || CANDIDATE_EXPLANATION_WORDING_TARGET_LANGUAGE,
      workspace_run_id: stringValue(config.workspaceRunId),
      wording_target_key: stringValue(config.wordingTargetKey),
      request_explanation_fingerprint: "",
      explanation_version: CANDIDATE_EXPLANATION_VERSION,
      source: "deterministic_workspace_facts",
      summary: normalizeWordingText(explanation.summary || "Review returned candidate details manually.", 320),
      positive_signals: renderableReasons.positive_signals,
      cautions: renderableReasons.cautions,
      evidence_items: renderableReasons.evidence_items,
    };
    request.request_explanation_fingerprint = await candidateExplanationRequestFingerprint(request);
    return request;
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

  function rawExportText(value) {
    if (value === undefined || value === null) {
      return "";
    }
    if (typeof value === "string") {
      return value;
    }
    if (typeof value === "number") {
      return Number.isFinite(value) ? String(value) : "";
    }
    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
    return "";
  }

  function normalizeExportScope(value) {
    const normalized = stringValue(value).toLowerCase();
    return Object.values(EXPORT_SCOPES).includes(normalized) ? normalized : EXPORT_SCOPES.VISIBLE;
  }

  function normalizeExportFormat(value) {
    const normalized = stringValue(value).toLowerCase();
    return Object.values(EXPORT_FORMATS).includes(normalized) ? normalized : EXPORT_FORMATS.CSV;
  }

  function normalizeExportDate(value) {
    const candidate =
      value && typeof value.getTime === "function" ? value : new Date(value);
    if (candidate && Number.isFinite(candidate.getTime())) {
      return candidate;
    }
    return new Date();
  }

  function normalizeExportInteger(value) {
    const number = Number(value);
    return Number.isFinite(number) && number >= 0 ? Math.floor(number) : 0;
  }

  function normalizeExportExecutionMode(value) {
    const normalized = stringValue(value).toLowerCase();
    return SAFE_EXPORT_EXECUTION_MODES.has(normalized) ? normalized : "search";
  }

  function normalizeExportSingleLine(value) {
    return rawExportText(value)
      .replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, " ")
      .replace(/[\r\n\t]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function capExportText(value, maxLength) {
    const text = rawExportText(value);
    const limit = Number(maxLength);
    if (!Number.isFinite(limit) || limit < 0) {
      return text;
    }
    return text.slice(0, limit);
  }

  function isObviousPhoneLikeText(value) {
    const text = stringValue(value);
    const digits = (text.match(/\d/g) || []).length;
    if (digits < 7) {
      return false;
    }
    const hasLeadingPlus = text.startsWith("+");
    const hasParentheses = /[()]/.test(text);
    const separatorCount = (text.match(/[\s.-]/g) || []).length;
    return hasLeadingPlus || hasParentheses || separatorCount >= 2;
  }

  function maskContactLikeText(value) {
    return rawExportText(value)
      .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, "[contact omitted]")
      .replace(/(?:\+?\d[\d\s().-]{6,}\d)/g, (match) =>
        isObviousPhoneLikeText(match) ? "[contact omitted]" : match
      );
  }

  function neutralizeExportUrlLikeText(value) {
    return rawExportText(value)
      .replace(/https:\/\//gi, "https: //")
      .replace(/http:\/\//gi, "http: //")
      .replace(/\bwww\./gi, "www .")
      .replace(/\b((?:[a-z0-9-]+\.)*linkedin)\.com\/in\//gi, "$1 .com/in/");
  }

  function normalizeExportText(value, options) {
    const config = options || {};
    let text = normalizeExportSingleLine(value);
    if (config.contactMask) {
      text = maskContactLikeText(text);
    }
    text = capExportText(text, config.maxLength);
    if (config.neutralizeUrlLike) {
      text = neutralizeExportUrlLikeText(text);
    }
    return text;
  }

  function exportProfileUrlFromValue(value) {
    const candidate = normalizeUrlCandidate(value);
    if (!candidate) {
      return "";
    }

    try {
      const parsed = new URL(candidate);
      const hostname = parsed.hostname.toLowerCase();
      const isLinkedInHost = hostname === "linkedin.com" || hostname.endsWith(".linkedin.com");
      const isHttp = parsed.protocol === "https:" || parsed.protocol === "http:";
      if (!isHttp || !isLinkedInHost || parsed.username || parsed.password) {
        return "";
      }
      const segments = parsed.pathname.split("/").filter(Boolean);
      const slug = segments[1] || "";
      if (
        segments.length < 2 ||
        segments[0].toLowerCase() !== "in" ||
        !slug ||
        slug === "." ||
        slug === ".." ||
        /%(?:2f|5c)/i.test(slug)
      ) {
        return "";
      }
      return `https://${hostname}/in/${slug}`;
    } catch (error) {
      return "";
    }
  }

  function exportScalarItemText(value) {
    if (typeof value === "string") {
      return stringValue(value);
    }
    if (typeof value === "number" && Number.isFinite(value)) {
      return String(value);
    }
    return "";
  }

  function joinExportScalarItems(values) {
    return arrayValue(values)
      .map(exportScalarItemText)
      .filter(Boolean)
      .join("; ");
  }

  function joinExportReviewFlags(flags) {
    return arrayValue(flags)
      .map((flag) => {
        if (typeof flag === "string") {
          return stringValue(flag);
        }
        if (!flag || typeof flag !== "object" || Array.isArray(flag)) {
          return "";
        }
        const code = stringValue(flag.code);
        const label = stringValue(flag.label);
        if (code && label && code !== label) {
          return `${code}: ${label}`;
        }
        return code || label;
      })
      .filter(Boolean)
      .join("; ");
  }

  function joinExportQuerySourceIds(sources) {
    const seen = new Set();
    const output = [];
    arrayValue(sources).forEach((source) => {
      if (!source || typeof source !== "object" || Array.isArray(source)) {
        return;
      }
      const text = stringValue(source.id) || stringValue(source.category);
      const key = text.toLowerCase();
      if (!text || key === "unknown" || seen.has(key)) {
        return;
      }
      seen.add(key);
      output.push(text);
    });
    return output.join("; ");
  }

  function buildExportExplanation(candidate) {
    try {
      const explanation = buildCandidateExplanation(candidate);
      if (
        !explanation ||
        explanation.source !== "deterministic_workspace_facts" ||
        explanation.version !== CANDIDATE_EXPLANATION_VERSION
      ) {
        return { summary: "", codes: "" };
      }
      const codes = [
        ...arrayValue(explanation.positive_signals),
        ...arrayValue(explanation.cautions),
        ...arrayValue(explanation.evidence_items),
      ]
        .map((reason) => stringValue(reason && reason.code))
        .filter(Boolean);
      return {
        summary: rawExportText(explanation.summary),
        codes: codes.join("; "),
      };
    } catch (error) {
      return { summary: "", codes: "" };
    }
  }

  function firstExportText(values, usefulOnly = false) {
    for (const value of values) {
      const text = rawExportText(value);
      const normalized = stringValue(text);
      if (!normalized) {
        continue;
      }
      if (usefulOnly && !isUsefulText(normalized)) {
        continue;
      }
      return normalized;
    }
    return "";
  }

  function candidateReviewStateForExport(reviewStateByCandidateId, candidate) {
    const candidateId = typeof (candidate && candidate.candidate_id) === "string"
      ? candidate.candidate_id.trim()
      : "";
    if (!candidateId) {
      return createInitialReviewState();
    }
    return createInitialReviewState(candidateReviewState(reviewStateByCandidateId, candidateId));
  }

  function orderedExportCandidates(candidates) {
    return arrayValue(candidates)
      .map((candidate, index) => {
        const order = Number(candidate && candidate.order_index);
        return {
          candidate,
          index,
          order: Number.isFinite(order) ? order : index,
        };
      })
      .sort((left, right) => left.order - right.order || left.index - right.index)
      .map((item) => item.candidate);
  }

  function selectExportCandidates(allCandidates, visibleCandidates, reviewStateByCandidateId, scope) {
    if (scope === EXPORT_SCOPES.VISIBLE) {
      return arrayValue(visibleCandidates).slice();
    }
    const ordered = orderedExportCandidates(allCandidates);
    if (scope === EXPORT_SCOPES.SHORTLISTED) {
      return ordered.filter((candidate) =>
        isWorkspaceCandidateShortlisted(candidateReviewStateForExport(reviewStateByCandidateId, candidate))
      );
    }
    return ordered;
  }

  function exportWorkspaceRunMetadata(workspaceRun, scope, format, exportedAt, candidateCount) {
    const run = workspaceRun && typeof workspaceRun === "object" ? workspaceRun : {};
    const context = run.run_context && typeof run.run_context === "object" ? run.run_context : {};
    return {
      workspace_run_id: rawExportText(run.workspace_run_id),
      exported_at: normalizeExportDate(exportedAt).toISOString(),
      scope,
      format,
      candidate_count: normalizeExportInteger(candidateCount),
      execution_mode: normalizeExportExecutionMode(context.execution_mode || run.execution_mode),
      query_count: normalizeExportInteger(context.query_count ?? run.query_count),
    };
  }

  function buildWorkspaceExportCandidateRow(candidate, reviewStateByCandidateId, displayIndex) {
    const item = candidate && typeof candidate === "object" ? candidate : {};
    const raw = item.raw && typeof item.raw === "object" ? item.raw : {};
    const result = raw.result && typeof raw.result === "object" ? raw.result : {};
    const reviewState = candidateReviewStateForExport(reviewStateByCandidateId, item);
    const profileUrl = exportProfileUrlFromValue(item.profile_href);
    const hasQualityScore = Boolean(item.has_quality_score) && hasFiniteNumber(item.quality_score);
    const qualityScore = hasQualityScore ? Number(item.quality_score) : null;
    const explanation = buildExportExplanation(item);

    return {
      display_index: normalizeExportInteger(displayIndex),
      candidate_name: rawExportText(item.display_name),
      headline: firstExportText([item.headline, item.raw_title]),
      profile_url: profileUrl,
      identity_stable: item.identity && item.identity.is_stable_identity && profileUrl ? "yes" : "no",
      quality_score: hasQualityScore ? String(qualityScore) : "",
      quality_bucket: hasQualityScore ? qualityBucket(qualityScore) : "",
      role: rawExportText(result.role_display),
      role_fit: rawExportText(result.role_fit),
      technology: rawExportText(result.technology_display),
      technology_fit: rawExportText(result.technology_fit),
      seniority: firstExportText([item.seniority_level, result.seniority_display, result.seniority_level]),
      location: firstExportText(
        [
          raw.current_location_line,
          result.current_location_line,
          ...arrayValue(raw.current_location_lines),
          ...arrayValue(result.current_location_lines),
        ],
        true
      ),
      location_status: rawExportText(item.location_status),
      source: rawExportText(item.source),
      stack_fit: rawExportText(item.stack_fit),
      selected_stack_terms: joinExportScalarItems(item.selected_stack_terms_found),
      missing_stack_terms: joinExportScalarItems(item.missing_selected_stack_terms),
      review_flags: joinExportReviewFlags(item.review_flags),
      review_status: normalizeReviewStatusForInit(reviewState.status),
      shortlisted: isWorkspaceCandidateShortlisted(reviewState) ? "yes" : "no",
      notes: capExportText(rawExportText(reviewState.note), NOTE_MAX_LENGTH),
      explanation_summary: explanation.summary,
      explanation_codes: explanation.codes,
      query_source_ids: joinExportQuerySourceIds(item.query_sources),
      snippet: rawExportText(item.snippet),
    };
  }

  function buildWorkspaceExportModel(options) {
    const config = options || {};
    const scope = normalizeExportScope(config.scope);
    const format = normalizeExportFormat(config.format);
    const exportedAt = normalizeExportDate(config.exportedAt);
    const selectedCandidates = selectExportCandidates(
      config.allCandidates,
      config.visibleCandidates,
      config.reviewStateByCandidateId,
      scope
    );
    const rows = selectedCandidates.map((candidate, index) =>
      buildWorkspaceExportCandidateRow(candidate, config.reviewStateByCandidateId, index + 1)
    );

    return {
      metadata: exportWorkspaceRunMetadata(config.workspaceRun, scope, format, exportedAt, rows.length),
      candidates: rows,
    };
  }

  function exportFieldOptions(field) {
    const compactFields = new Set([
      "role",
      "role_fit",
      "technology",
      "technology_fit",
      "seniority",
      "location",
      "location_status",
      "source",
      "stack_fit",
      "review_status",
      "shortlisted",
      "identity_stable",
      "quality_bucket",
    ]);
    const joinedFields = new Set([
      "selected_stack_terms",
      "missing_stack_terms",
      "review_flags",
      "explanation_codes",
      "query_source_ids",
    ]);
    const returnedCandidateTextFields = new Set([
      "candidate_name",
      "headline",
      "role",
      "role_fit",
      "technology",
      "technology_fit",
      "seniority",
      "location",
      "location_status",
      "source",
      "stack_fit",
      "selected_stack_terms",
      "missing_stack_terms",
      "review_flags",
      "explanation_summary",
      "explanation_codes",
      "query_source_ids",
      "snippet",
    ]);
    let maxLength = EXPORT_TEXT_LIMITS.compact;
    if (field === "candidate_name") {
      maxLength = EXPORT_TEXT_LIMITS.candidate_name;
    } else if (field === "headline") {
      maxLength = EXPORT_TEXT_LIMITS.headline;
    } else if (joinedFields.has(field)) {
      maxLength = EXPORT_TEXT_LIMITS.joined;
    } else if (field === "notes") {
      maxLength = EXPORT_TEXT_LIMITS.notes;
    } else if (field === "explanation_summary") {
      maxLength = EXPORT_TEXT_LIMITS.explanation_summary;
    } else if (field === "snippet") {
      maxLength = EXPORT_TEXT_LIMITS.snippet;
    } else if (field === "display_index" || field === "quality_score") {
      maxLength = 40;
    } else if (!compactFields.has(field)) {
      maxLength = EXPORT_TEXT_LIMITS.compact;
    }
    return {
      maxLength,
      contactMask: returnedCandidateTextFields.has(field),
      neutralizeUrlLike: field !== "profile_url",
      allowPlainUrl: field === "profile_url",
    };
  }

  function sanitizeCsvCell(value, options) {
    const config = options || {};
    const rawText = rawExportText(value);
    let text = normalizeExportText(rawText, {
      maxLength: config.maxLength,
      contactMask: config.contactMask,
      neutralizeUrlLike: !config.allowPlainUrl && config.neutralizeUrlLike !== false,
    });
    const startsWithFormulaControl = /^[\t\r\n]/.test(rawText);
    const firstNonWhitespace = text.match(/\S/);
    const startsWithFormulaChar =
      firstNonWhitespace && /^[=+\-@]$/.test(firstNonWhitespace[0]);
    if (startsWithFormulaControl || startsWithFormulaChar) {
      text = `'${text}`;
    }
    return `"${text.replace(/"/g, '""')}"`;
  }

  function serializeWorkspaceExportCsv(model) {
    const candidates = arrayValue(model && model.candidates);
    const rows = [
      "\ufeffsep=,",
      EXPORT_CSV_COLUMNS.join(","),
      ...candidates.map((candidate) =>
        EXPORT_CSV_COLUMNS.map((field) =>
          sanitizeCsvCell(
            field === "profile_url" ? exportProfileUrlFromValue(candidate && candidate[field]) : candidate && candidate[field],
            exportFieldOptions(field)
          )
        ).join(",")
      ),
    ];
    return `${rows.join("\r\n")}\r\n`;
  }

  function escapeMarkdownText(value, options) {
    const config = options || {};
    const text = normalizeExportText(value, {
      maxLength: config.maxLength,
      contactMask: config.contactMask,
      neutralizeUrlLike: !config.allowPlainUrl && config.neutralizeUrlLike !== false,
    })
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return text.replace(/[\\[\]()#*_|`~!]/g, "\\$&");
  }

  function markdownFieldValue(row, field) {
    return escapeMarkdownText(row && row[field], exportFieldOptions(field));
  }

  function serializeWorkspaceExportMarkdown(model) {
    const metadata = (model && model.metadata) || {};
    const candidates = arrayValue(model && model.candidates);
    const scope = normalizeExportScope(metadata.scope);
    const format = EXPORT_FORMATS.MARKDOWN;
    const executionMode = normalizeExportExecutionMode(metadata.execution_mode);
    const queryCount = normalizeExportInteger(metadata.query_count);
    const candidateCount = normalizeExportInteger(metadata.candidate_count ?? candidates.length);
    const exportedAt = rawExportText(metadata.exported_at) || normalizeExportDate().toISOString();
    const lines = [
      "# Candidate Workspace Export",
      "",
      `Exported at: ${escapeMarkdownText(exportedAt, { maxLength: 80 })}`,
      `Scope: ${escapeMarkdownText(scope, { maxLength: 40 })}`,
      `Format: ${escapeMarkdownText(format, { maxLength: 40 })}`,
      `Candidates: ${candidateCount}`,
      `Execution mode: ${escapeMarkdownText(executionMode, { maxLength: 40 })}`,
      `Queries: ${queryCount}`,
      "",
    ];

    candidates.forEach((row, index) => {
      const displayIndex = normalizeExportInteger(row && row.display_index) || index + 1;
      const name =
        markdownFieldValue(row, "candidate_name") ||
        escapeMarkdownText(`Candidate ${displayIndex}`, { maxLength: EXPORT_TEXT_LIMITS.candidate_name });
      const quality = [rawExportText(row && row.quality_score), rawExportText(row && row.quality_bucket)]
        .filter(Boolean)
        .join(" ");
      lines.push(`## ${displayIndex}. ${name}`);
      lines.push("");
      lines.push(`- Headline: ${markdownFieldValue(row, "headline")}`);
      lines.push(`- Profile: ${exportProfileUrlFromValue(row && row.profile_url)}`);
      lines.push(`- Quality: ${escapeMarkdownText(quality, { maxLength: 80 })}`);
      lines.push(`- Role: ${markdownFieldValue(row, "role")}`);
      lines.push(`- Role fit: ${markdownFieldValue(row, "role_fit")}`);
      lines.push(`- Technology: ${markdownFieldValue(row, "technology")}`);
      lines.push(`- Technology fit: ${markdownFieldValue(row, "technology_fit")}`);
      lines.push(`- Seniority: ${markdownFieldValue(row, "seniority")}`);
      lines.push(`- Location: ${markdownFieldValue(row, "location")}`);
      lines.push(`- Location status: ${markdownFieldValue(row, "location_status")}`);
      lines.push(`- Source: ${markdownFieldValue(row, "source")}`);
      lines.push(`- Stack fit: ${markdownFieldValue(row, "stack_fit")}`);
      lines.push(`- Review flags: ${markdownFieldValue(row, "review_flags")}`);
      lines.push(`- Review status: ${markdownFieldValue(row, "review_status")}`);
      lines.push(`- Shortlisted: ${markdownFieldValue(row, "shortlisted")}`);
      lines.push(`- Notes: ${markdownFieldValue(row, "notes")}`);
      lines.push(`- Explanation: ${markdownFieldValue(row, "explanation_summary")}`);
      lines.push(`- Explanation codes: ${markdownFieldValue(row, "explanation_codes")}`);
      lines.push(`- Query sources: ${markdownFieldValue(row, "query_source_ids")}`);
      lines.push(`- Snippet: ${markdownFieldValue(row, "snippet")}`);
      lines.push("");
    });

    return `${lines.join("\n").replace(/\n+$/, "")}\n`;
  }

  function padExportDatePart(value) {
    return String(value).padStart(2, "0");
  }

  function buildWorkspaceExportFilename(exportedAt, scope, format) {
    const date = normalizeExportDate(exportedAt);
    const normalizedScope = normalizeExportScope(scope);
    const normalizedFormat = normalizeExportFormat(format);
    const extension = normalizedFormat === EXPORT_FORMATS.MARKDOWN ? "md" : "csv";
    const stamp = [
      date.getFullYear(),
      padExportDatePart(date.getMonth() + 1),
      padExportDatePart(date.getDate()),
      "-",
      padExportDatePart(date.getHours()),
      padExportDatePart(date.getMinutes()),
      padExportDatePart(date.getSeconds()),
    ].join("");
    return `engineers-search-candidates-${normalizedScope}-${stamp}.${extension}`;
  }

  function workspaceExportMimeType(format) {
    return normalizeExportFormat(format) === EXPORT_FORMATS.MARKDOWN
      ? "text/markdown;charset=utf-8"
      : "text/csv;charset=utf-8";
  }

  root.CandidateWorkspace = {
    SORT_MODES,
    QUALITY_FILTERS,
    STACK_FILTERS,
    REVIEW_FLAG_FILTERS,
    LOCATION_FILTERS,
    REVIEW_STATUSES,
    SHORTLIST_FILTERS,
    EXPORT_SCOPES,
    EXPORT_FORMATS,
    EXPORT_CSV_COLUMNS,
    NOTE_MAX_LENGTH,
    CANDIDATE_EXPLANATION_VERSION,
    TOP_CANDIDATE_RECOMMENDATION_VERSION,
    SELECTED_CANDIDATE_COMPARISON_VERSION,
    SELECTED_CANDIDATE_FIT_GAP_VERSION,
    WORKSPACE_REFINEMENT_SUGGESTIONS_VERSION,
    CANDIDATE_EXPLANATION_WORDING_USE_CASE,
    CANDIDATE_EXPLANATION_WORDING_REQUEST_VERSION,
    CANDIDATE_EXPLANATION_WORDING_TARGET_LANGUAGE,
    EXPLANATION_REASON_CODES,
    buildSafeLinkedInProfileHref,
    buildCandidateExplanation,
    buildTopCandidateRecommendation,
    buildSelectedCandidateComparison,
    buildSelectedCandidateFitGapExplanation,
    buildWorkspaceRefinementSuggestions,
    buildCandidateExplanationRenderableReasons,
    buildCandidateExplanationWordingRequest,
    candidateExplanationRequestFingerprint,
    createWordingTargetKey,
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
    normalizeExportScope,
    normalizeExportFormat,
    normalizeExportText,
    neutralizeExportUrlLikeText,
    sanitizeCsvCell,
    escapeMarkdownText,
    buildWorkspaceExportModel,
    serializeWorkspaceExportCsv,
    serializeWorkspaceExportMarkdown,
    buildWorkspaceExportFilename,
    workspaceExportMimeType,
  };
})(typeof window !== "undefined" ? window : globalThis);
