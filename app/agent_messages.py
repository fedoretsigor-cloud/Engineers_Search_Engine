import re

from app.domain_config import SEARCH_BRIEF_STATUS_READY_FOR_PLANNING
from app.text_utils import normalize_text_value


AGENT_MESSAGE_COVERAGE = {
    "recruiter_chat_onboarding_source_message": {
        "helper": "recruiter_chat_onboarding_source_message",
        "message_type": "onboarding",
        "surface": "chat",
        "source_owner": "Search Brief backend validation",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "recruiter_chat_near_empty_source_message": {
        "helper": "recruiter_chat_near_empty_source_message",
        "message_type": "onboarding",
        "surface": "chat",
        "source_owner": "Search Brief backend validation",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "recruiter_chat_draft_preserved_source_message": {
        "helper": "recruiter_chat_draft_preserved_source_message",
        "message_type": "onboarding, clarification_question, brief_summary",
        "surface": "chat",
        "source_owner": "Search Brief backend validation",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "localized_clarifying_question_source_message": {
        "helper": "localized_clarifying_question_source_message",
        "message_type": "clarification_question",
        "surface": "chat",
        "source_owner": "Search Brief backend validation",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "next_question",
    },
    "ready_for_planning_source_message": {
        "helper": "ready_for_planning_source_message",
        "message_type": "brief_summary",
        "surface": "chat, brief_panel",
        "source_owner": "Search Brief backend validation",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "validation_error_source_message": {
        "helper": "validation_error_source_message",
        "message_type": "validation_feedback",
        "surface": "chat, status_panel",
        "source_owner": "structured error envelope",
        "source_object": "backend validation response",
        "public_response_field": "assistant_message",
    },
    "recruiter_chat_refusal_source_message": {
        "helper": "recruiter_chat_refusal_source_message",
        "message_type": "safety_refusal",
        "surface": "chat, status_panel",
        "source_owner": "Search Brief backend validation; product safety guard",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "brief_refinement_source_message": {
        "helper": "brief_refinement_source_message",
        "message_type": "brief_refinement_applied",
        "surface": "chat, brief_panel, status_panel",
        "source_owner": "deterministic brief patch/refinement backend",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "refinement_requires_initial_brief_source_message": {
        "helper": "refinement_requires_initial_brief_source_message",
        "message_type": "brief_refinement_rejected",
        "surface": "chat, brief_panel, status_panel",
        "source_owner": "deterministic brief patch/refinement backend",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "unsupported_patch_source_message": {
        "helper": "unsupported_patch_source_message",
        "message_type": "brief_refinement_rejected",
        "surface": "chat, brief_panel, status_panel",
        "source_owner": "deterministic brief patch/refinement backend",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "last_stack_item_source_message": {
        "helper": "last_stack_item_source_message",
        "message_type": "brief_refinement_rejected",
        "surface": "chat, brief_panel, status_panel",
        "source_owner": "deterministic brief patch/refinement backend",
        "source_object": "/api/recruiter-chat/turn",
        "public_response_field": "assistant_message",
    },
    "agent_plan_supported_source_message": {
        "helper": "agent_plan_supported_source_message",
        "message_type": "agent_plan",
        "surface": "chat, action_queue",
        "source_owner": "Agent Plan backend response",
        "source_object": "/api/agent/plan",
        "public_response_field": "agent_plan.message",
    },
    "agent_plan_needs_clarification_source_message": {
        "helper": "agent_plan_needs_clarification_source_message",
        "message_type": "planning_needs_clarification",
        "surface": "chat, plan_panel, status_panel",
        "source_owner": "Agent Plan backend response",
        "source_object": "/api/agent/plan",
        "public_response_field": "message",
    },
    "agent_plan_unsupported_source_message": {
        "helper": "agent_plan_unsupported_source_message",
        "message_type": "agent_plan_unsupported",
        "surface": "chat, action_queue, status_panel",
        "source_owner": "Agent Plan backend response",
        "source_object": "/api/agent/plan",
        "public_response_field": "message",
    },
    "agent_plan_action_error_source_message": {
        "helper": "agent_plan_action_error_source_message",
        "message_type": "runtime_action_rejected",
        "surface": "action_queue, status_panel",
        "source_owner": "Agent Plan backend validation",
        "source_object": "/api/agent/query-plan",
        "public_response_field": "validation_errors[].message",
    },
    "query_plan_ready_approval_notice": {
        "helper": "query_plan_ready_approval_notice",
        "message_type": "query_plan_ready",
        "surface": "plan_panel, action_queue, status_panel",
        "source_owner": "QueryPlan/planner backend",
        "source_object": "/api/agent/query-plan",
        "public_response_field": "approval_notice",
    },
    "query_plan_fallback_approval_notice": {
        "helper": "query_plan_fallback_approval_notice",
        "message_type": "query_plan_ready",
        "surface": "plan_panel, action_queue, status_panel",
        "source_owner": "QueryPlan/planner backend",
        "source_object": "/api/agent/query-plan",
        "public_response_field": "approval_notice",
    },
    "query_plan_preview_approval_notice": {
        "helper": "query_plan_preview_approval_notice",
        "message_type": "query_plan_preview",
        "surface": "plan_panel, status_panel",
        "source_owner": "QueryPlan/planner backend",
        "source_object": "/api/agent/query-plan; /api/ai-query-plan/validate",
        "public_response_field": "approval_notice",
    },
    "query_plan_ai_validated_approval_notice": {
        "helper": "query_plan_ai_validated_approval_notice",
        "message_type": "query_plan_preview",
        "surface": "plan_panel, status_panel",
        "source_owner": "QueryPlan/planner backend",
        "source_object": "/api/agent/query-plan",
        "public_response_field": "approval_notice",
    },
    "query_plan_rejected_approval_notice": {
        "helper": "query_plan_rejected_approval_notice",
        "message_type": "query_plan_rejected",
        "surface": "plan_panel, status_panel",
        "source_owner": "QueryPlan/planner backend",
        "source_object": "/api/agent/query-plan",
        "public_response_field": "approval_notice",
    },
    "search_brief_not_ready_for_query_plan_source_message": {
        "helper": "search_brief_not_ready_for_query_plan_source_message",
        "message_type": "planning_needs_clarification",
        "surface": "plan_panel, status_panel",
        "source_owner": "Search Brief backend validation",
        "source_object": "/api/ai-query-plan/validate",
        "public_response_field": "errors[].message",
    },
    "runtime_tool_unavailable_source_message": {
        "helper": "runtime_tool_unavailable_source_message",
        "message_type": "tool_unavailable",
        "surface": "chat, plan_panel, status_panel, results_panel",
        "source_owner": "backend service/config availability check",
        "source_object": "backend service/config availability checks",
        "public_response_field": "errors[].message",
    },
    "runtime_execution_failed_source_message": {
        "helper": "runtime_execution_failed_source_message",
        "message_type": "execution_failed",
        "surface": "status_panel, results_panel",
        "source_owner": "Agent Runtime backend",
        "source_object": "/api/agent/runtime/turn",
        "public_response_field": "tool_results[].errors[].message",
    },
    "agent_response_summary_source_message": {
        "helper": "agent_response_summary_source_message",
        "message_type": "agent_response",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "approved search response agent_response",
        "public_response_field": "agent_response.message",
    },
    "agent_response_quality_notes_source_messages": {
        "helper": "agent_response_quality_notes_source_messages",
        "message_type": "agent_response",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "approved search response agent_response",
        "public_response_field": "agent_response.quality_notes",
    },
    "agent_response_limitations_source_messages": {
        "helper": "agent_response_limitations_source_messages",
        "message_type": "agent_response",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "approved search response agent_response",
        "public_response_field": "agent_response.limitations",
    },
    "agent_response_suggested_next_actions_source_messages": {
        "helper": "agent_response_suggested_next_actions_source_messages",
        "message_type": "agent_response",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "approved search response agent_response",
        "public_response_field": "agent_response.suggested_next_actions",
    },
    "next_iteration_review_high_quality_candidates_source_copy": {
        "helper": "next_iteration_review_high_quality_candidates_source_copy",
        "message_type": "next_iteration_options",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "agent_response.next_iteration_options",
        "public_response_field": "agent_response.next_iteration_options[].label/reason",
    },
    "next_iteration_narrow_visible_stack_source_copy": {
        "helper": "next_iteration_narrow_visible_stack_source_copy",
        "message_type": "next_iteration_options",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "agent_response.next_iteration_options",
        "public_response_field": "agent_response.next_iteration_options[].label/reason",
    },
    "next_iteration_broaden_observed_stack_source_copy": {
        "helper": "next_iteration_broaden_observed_stack_source_copy",
        "message_type": "next_iteration_options",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "agent_response.next_iteration_options",
        "public_response_field": "agent_response.next_iteration_options[].label/reason",
    },
    "next_iteration_clarify_stack_source_copy": {
        "helper": "next_iteration_clarify_stack_source_copy",
        "message_type": "next_iteration_options",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "agent_response.next_iteration_options",
        "public_response_field": "agent_response.next_iteration_options[].label/reason",
    },
    "next_iteration_deep_search_source_copy": {
        "helper": "next_iteration_deep_search_source_copy",
        "message_type": "next_iteration_options",
        "surface": "chat, results_panel",
        "source_owner": "deterministic Agent Response backend",
        "source_object": "agent_response.next_iteration_options",
        "public_response_field": "agent_response.next_iteration_options[].label/reason",
    },
}

AGENT_PLAN_ERROR_MISSING_FINGERPRINT = "missing_agent_plan_fingerprint"
AGENT_PLAN_ERROR_STALE_FINGERPRINT = "stale_or_mismatched_agent_plan_fingerprint"
AGENT_PLAN_ERROR_MISSING_ACTION = "missing_agent_plan_action"
AGENT_PLAN_ERROR_UNSUPPORTED_ACTION = "unsupported_agent_plan_action"
AGENT_PLAN_ERROR_MISMATCHED_PLANNER_MODE = "mismatched_agent_plan_planner_mode"
AGENT_PLAN_ERROR_UNSUPPORTED_BASELINE = "unsupported_agent_v0_baseline"

NEXT_ITERATION_REVIEW_HIGH_QUALITY = "review_high_quality_candidates"
NEXT_ITERATION_NARROW_VISIBLE_STACK = "narrow_to_visible_selected_stack"
NEXT_ITERATION_BROADEN_OBSERVED_STACK = "broaden_with_observed_stack"
NEXT_ITERATION_CLARIFY_STACK = "clarify_stack_preference"
NEXT_ITERATION_DEEP_SEARCH = "try_deep_search_depth"


def agent_message_language(
    language: str | None,
    normalized_brief: dict | None = None,
) -> str:
    normalized_language = (normalize_text_value(language) or "").lower()
    if normalized_language.startswith(("ru", "\u0440\u0443\u0441")):
        return "ru"
    if normalized_language.startswith(("en", "\u0430\u043d\u0433\u043b")):
        return "en"

    source_text = (normalized_brief or {}).get("source_text") or ""
    if re.search(r"[\u0400-\u04ff]", source_text):
        return "ru"

    return "en"


def recruiter_chat_refusal_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u042f \u043d\u0435 \u043c\u043e\u0433\u0443 "
            "\u0432\u044b\u043f\u043e\u043b\u043d\u044f\u0442\u044c LinkedIn login, "
            "scraping, \u043e\u0431\u0445\u043e\u0434 "
            "\u043e\u0433\u0440\u0430\u043d\u0438\u0447\u0435\u043d\u0438\u0439, "
            "\u0430\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 "
            "\u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f "
            "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0430\u043c, "
            "\u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f \u0441 "
            "\u0430\u043a\u043a\u0430\u0443\u043d\u0442\u0430\u043c\u0438 "
            "\u0438\u043b\u0438 \u043f\u0440\u044f\u043c\u043e\u0439 "
            "web-search \u0432 \u043e\u0431\u0445\u043e\u0434 backend. "
            "\u041c\u043e\u0433\u0443 \u043f\u043e\u043c\u043e\u0447\u044c "
            "\u0441\u0444\u043e\u0440\u043c\u0438\u0440\u043e\u0432\u0430\u0442\u044c "
            "search summary \u0434\u043b\u044f safe public-profile search."
        )

    return (
        "I cannot perform LinkedIn login, scraping, restriction bypass, automatic "
        "candidate messaging, account actions, or direct web-search outside the "
        "approved search flow. I can help turn the request into a safe search summary."
    )


def localized_clarifying_question_source_message(field: str, language: str) -> str:
    if language == "ru":
        questions = {
            "role_family": "\u041a\u0430\u043a\u0443\u044e \u0440\u043e\u043b\u044c \u0438\u0449\u0435\u043c?",
            "technology": (
                "\u041a\u0430\u043a\u0430\u044f \u043e\u0441\u043d\u043e\u0432\u043d\u0430\u044f "
                "\u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f "
                "\u0434\u043e\u043b\u0436\u043d\u0430 \u0431\u044b\u0442\u044c "
                "\u0443 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u0430?"
            ),
            "stack": (
                "\u041a\u0430\u043a\u0438\u0435 Java stack "
                "\u0441\u0438\u0433\u043d\u0430\u043b\u044b \u0432\u0430\u0436\u043d\u044b: "
                "Spring, Kafka, AWS, Hibernate \u0438\u043b\u0438 "
                "\u0447\u0442\u043e-\u0442\u043e \u0434\u0440\u0443\u0433\u043e\u0435?"
            ),
            "location": (
                "\u0412 \u043a\u0430\u043a\u043e\u0439 "
                "\u043b\u043e\u043a\u0430\u0446\u0438\u0438 \u0438\u0449\u0435\u043c "
                "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432?"
            ),
            "search_depth": "\u0414\u0435\u043b\u0430\u0435\u043c standard \u0438\u043b\u0438 deep search?",
            "profile_sources": (
                "\u041a\u0430\u043a\u0438\u0435 "
                "\u043f\u0443\u0431\u043b\u0438\u0447\u043d\u044b\u0435 "
                "\u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u0438 "
                "\u043f\u0440\u043e\u0444\u0438\u043b\u0435\u0439 "
                "\u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u044c?"
            ),
        }
        return questions.get(
            field,
            (
                "\u0423\u0442\u043e\u0447\u043d\u0438, "
                "\u043f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, "
                f"\u043f\u043e\u043b\u0435 {field}."
            ),
        )

    questions = {
        "role_family": "What role family should the search target?",
        "technology": "What main technology should the candidate have?",
        "stack": (
            "Which Java stack signals are important for this search: "
            "Spring, Kafka, AWS, Hibernate, or something else?"
        ),
        "location": "What target location should the search use?",
        "search_depth": "Should this be a standard or deep search?",
        "profile_sources": "Which public profile source should be used?",
    }
    return questions.get(field, f"Please clarify {field}.")


def ready_for_planning_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u042f \u043f\u043e\u043d\u044f\u043b \u043f\u043e\u0438\u0441\u043a. "
            "\u041f\u0440\u043e\u0432\u0435\u0440\u044c summary. "
            "\u041f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u044c search?"
        )

    return "I understood the search. Review the summary. Prepare search now?"


def validation_error_source_message(
    errors: list[dict[str, str]],
    language: str,
) -> str:
    if not errors:
        return ""

    message = errors[0].get("message", "Validation error.")
    if language == "ru":
        return f"\u041d\u0443\u0436\u043d\u043e \u0443\u0442\u043e\u0447\u043d\u0438\u0442\u044c brief: {message}"

    return f"The brief needs clarification: {message}"


def recruiter_chat_onboarding_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u041f\u0440\u0438\u0432\u0435\u0442. "
            "\u0420\u0430\u0441\u0441\u043a\u0430\u0436\u0438, "
            "\u043f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, "
            "\u043a\u043e\u0433\u043e \u0438\u0449\u0435\u043c: "
            "\u0440\u043e\u043b\u044c, \u043e\u0441\u043d\u043e\u0432\u043d\u0430\u044f "
            "\u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f, "
            "\u043b\u043e\u043a\u0430\u0446\u0438\u044f \u0438 1-3 "
            "\u0441\u0438\u0433\u043d\u0430\u043b\u0430 \u0441\u0442\u0435\u043a\u0430."
        )

    return (
        "Hello. Tell me who we should find: role, main technology, location, "
        "and 1-3 stack signals."
    )


def recruiter_chat_near_empty_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u041d\u0430\u043f\u0438\u0448\u0438, "
            "\u043f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, "
            "\u043a\u043e\u0433\u043e \u0438\u0449\u0435\u043c: "
            "\u0440\u043e\u043b\u044c, \u043e\u0441\u043d\u043e\u0432\u043d\u0430\u044f "
            "\u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f, "
            "\u043b\u043e\u043a\u0430\u0446\u0438\u044f \u0438 1-3 "
            "\u0441\u0438\u0433\u043d\u0430\u043b\u0430 \u0441\u0442\u0435\u043a\u0430."
        )

    return (
        "Please tell me who we should find: role, main technology, location, "
        "and 1-3 stack signals."
    )


def recruiter_chat_draft_preserved_source_message(
    normalized_brief: dict,
    language: str,
    fallback_message: str,
    next_question: str | None,
) -> str:
    if normalized_brief.get("brief_status") == SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        if language == "ru":
            return (
                "\u0422\u0435\u043a\u0443\u0449\u0430\u044f search summary "
                "\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d \u0438 "
                "\u0433\u043e\u0442\u043e\u0432\u0430."
            )
        return "Hello. The current search summary is still saved and ready."

    if next_question:
        if language == "ru":
            return (
                "\u0422\u0435\u043a\u0443\u0449\u0430\u044f search summary "
                f"\u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d. {next_question}"
            )
        return f"The current search summary is still saved. {next_question}"

    return fallback_message


def refinement_requires_initial_brief_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 "
            "\u0441\u043e\u0431\u0435\u0440\u0435\u043c initial search summary: "
            "\u0440\u043e\u043b\u044c, \u043e\u0441\u043d\u043e\u0432\u043d\u0430\u044f "
            "\u0442\u0435\u0445\u043d\u043e\u043b\u043e\u0433\u0438\u044f, "
            "\u043b\u043e\u043a\u0430\u0446\u0438\u044f \u0438 1-3 stack "
            "\u0441\u0438\u0433\u043d\u0430\u043b\u0430."
        )
    return (
        "Let's collect the initial search summary first: role, main technology, "
        "location, and 1-3 stack signals."
    )


def unsupported_patch_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u042d\u0442\u043e \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435 "
            "\u0432\u043d\u0435 \u0442\u0435\u043a\u0443\u0449\u0435\u0433\u043e "
            "Java/Ukraine flow. \u0423\u0442\u043e\u0447\u043d\u0438 "
            "\u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435 \u0432 "
            "\u0440\u0430\u043c\u043a\u0430\u0445 Backend Developer, Java, "
            "Ukraine \u0438 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0430\u043d\u043d\u043e\u0433\u043e "
            "Java stack."
        )
    return (
        "That change is outside the current Java/Ukraine flow. Please refine it "
        "within Backend Developer, Java, Ukraine, and the supported Java stack."
    )


def last_stack_item_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u041d\u0435\u043b\u044c\u0437\u044f "
            "\u0443\u0431\u0440\u0430\u0442\u044c "
            "\u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0439 stack item "
            "\u0431\u0435\u0437 \u0437\u0430\u043c\u0435\u043d\u044b. "
            "\u0412\u044b\u0431\u0435\u0440\u0438 replacement \u0438\u0437 "
            "\u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0430\u043d\u043d\u043e\u0433\u043e "
            "Java stack."
        )
    return (
        "I cannot remove the last stack item without a replacement. Choose a "
        "replacement from the supported Java stack."
    )


def brief_refinement_source_message(
    language: str,
    changed: bool,
    action_summary: str,
) -> str:
    if not changed:
        if language == "ru":
            return (
                "Search summary \u043d\u0435 "
                "\u0438\u0437\u043c\u0435\u043d\u0438\u043b\u0441\u044f. "
                "\u0422\u0435\u043a\u0443\u0449\u0438\u0439 \u043f\u043b\u0430\u043d "
                "\u043c\u043e\u0436\u043d\u043e \u043e\u0441\u0442\u0430\u0432\u0438\u0442\u044c."
            )
        return "Search summary did not change. The current prepared search can stay as is."

    if language == "ru":
        return (
            f"\u041e\u0431\u043d\u043e\u0432\u0438\u043b search summary ({action_summary}). "
            "\u041d\u0443\u0436\u043d\u043e \u0437\u0430\u043d\u043e\u0432\u043e "
            "\u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u044c search."
        )
    return f"Updated the search summary ({action_summary}). Prepare search again before running."


def agent_plan_supported_source_message(
    language: str,
    normalized_request: dict,
) -> str:
    stack_text = ", ".join(normalized_request.get("stack") or []) or "n/a"
    if language == "ru":
        return (
            "\u042f \u043f\u043e\u043d\u044f\u043b \u0437\u0430\u0434\u0430\u0447\u0443: "
            "\u0438\u0449\u0435\u043c Backend Developer \u0441 Java \u0432 "
            f"\u0423\u043a\u0440\u0430\u0438\u043d\u0435, stack: {stack_text}. "
            "\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 "
            "\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 "
            "\u0448\u0430\u0433 - \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u044c search details. \u041f\u043e\u0438\u0441\u043a "
            "\u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0441\u044f "
            "\u0431\u0435\u0437 \u0442\u0432\u043e\u0435\u0433\u043e Run search."
        )

    return (
        "I understood the task: find Backend Developer profiles with Java in "
        f"Ukraine, stack: {stack_text}. The next step is to prepare search details. "
        "Search will not run until you confirm Run search."
    )


def agent_plan_needs_clarification_source_message(language: str) -> str:
    if language == "ru":
        return (
            "\u041c\u043d\u0435 \u043d\u0443\u0436\u0435\u043d stack, "
            "\u0447\u0442\u043e\u0431\u044b \u0441\u043e\u0437\u0434\u0430\u0442\u044c "
            "search \u0434\u043b\u044f Java/Ukraine baseline."
        )

    return "I need the missing stack before I can prepare the search."


def agent_plan_unsupported_source_message(language: str) -> str:
    if language == "ru":
        return (
            "Agent v0 \u043f\u043e\u043a\u0430 "
            "\u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442 "
            "\u0442\u043e\u043b\u044c\u043a\u043e Backend Developer with Java in Ukraine."
        )

    return "Agent v0 currently supports only Backend Developer with Java in Ukraine."


def agent_plan_action_error_source_message(error_code: str) -> str:
    messages = {
        AGENT_PLAN_ERROR_MISSING_FINGERPRINT: (
            "Prepare search requires the current search summary."
        ),
        AGENT_PLAN_ERROR_STALE_FINGERPRINT: (
            "Prepared search does not match the current search summary."
        ),
        AGENT_PLAN_ERROR_MISSING_ACTION: (
            "Prepare search requires a supported current action."
        ),
        AGENT_PLAN_ERROR_UNSUPPORTED_ACTION: "Prepare search action is not supported.",
        AGENT_PLAN_ERROR_MISMATCHED_PLANNER_MODE: (
            "Prepared search mode does not match the current request."
        ),
        AGENT_PLAN_ERROR_UNSUPPORTED_BASELINE: (
            "Agent v0 currently supports only Backend Developer with Java in Ukraine."
        ),
    }
    return messages.get(error_code, "Prepare search action is not supported.")


def query_plan_ready_approval_notice() -> str:
    return "Search is ready to run. Review the details before running search."


def query_plan_fallback_approval_notice() -> str:
    return "Fallback search is ready. Review the details before running search."


def query_plan_rejected_approval_notice() -> str:
    return "A fallback search is available. Confirm Run search before execution."


def query_plan_ai_validated_approval_notice() -> str:
    return "This AI preview is validated. Confirm Run search before execution."


def query_plan_preview_approval_notice() -> str:
    return "This preview has not run. Confirm Run search before execution."


def runtime_tool_unavailable_source_message() -> str:
    return "TAVILY_API_KEY is not configured."


def runtime_execution_failed_source_message() -> str:
    return "Search execution failed."


def search_brief_not_ready_for_query_plan_source_message() -> str:
    return "Search summary must be ready before preparing search."


def agent_response_summary_source_message(language: str, summary_facts: dict) -> str:
    candidate_count = summary_facts["candidate_count"]

    if language == "ru":
        return (
            f"\u041f\u043e\u0438\u0441\u043a \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d: {candidate_count} "
            f"\u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 "
            "\u043d\u0430\u0439\u0434\u0435\u043d\u043e. \u041e\u0442\u043a\u0440\u043e\u0439 candidate workspace "
            "\u0438 \u043d\u0430\u0447\u043d\u0438 \u0441 \u0441\u0430\u043c\u044b\u0445 "
            "\u0441\u0438\u043b\u044c\u043d\u044b\u0445 \u0441\u043e\u0432\u043f\u0430\u0434\u0435\u043d\u0438\u0439."
        )

    return (
        f"Search completed: {candidate_count} unique candidates found. Review them "
        "in the candidate workspace, starting with the strongest matches."
    )


def agent_response_quality_notes_source_messages(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    quality = summary_facts["quality_distribution"]
    signals = summary_facts["strong_signal_counts"]

    quality_note = {
        "kind": "quality_distribution",
        "message": (
            f"Quality buckets: {quality['strong']} strong, "
            f"{quality['review']} review, {quality['weak']} weak."
        ),
        "facts": quality,
    }
    if language == "ru":
        return [
            quality_note,
            {
                "kind": "signals",
                "message": (
                    "Java \u0438 \u0440\u043e\u043b\u044c \u0441\u0447\u0438\u0442\u0430\u044e\u0442\u0441\u044f "
                    "\u0441\u0438\u043b\u044c\u043d\u044b\u043c\u0438 \u0442\u043e\u043b\u044c\u043a\u043e "
                    "\u043a\u043e\u0433\u0434\u0430 \u043e\u043d\u0438 \u0432\u0438\u0434\u043d\u044b "
                    "\u0432 public profile text."
                ),
                "facts": signals,
            },
        ]

    return [
        quality_note,
        {
            "kind": "signals",
            "message": (
                "Java and role signals count as strong only when visible in "
                "public profile text."
            ),
            "facts": signals,
        },
    ]


def agent_response_limitations_source_messages(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    signals = summary_facts["strong_signal_counts"]
    if language == "ru":
        return [
            {
                "kind": "public_snippets",
                "message": (
                    "\u041e\u0442\u0432\u0435\u0442 \u043e\u0441\u043d\u043e\u0432\u0430\u043d "
                    "\u0442\u043e\u043b\u044c\u043a\u043e \u043d\u0430 public snippets "
                    "\u0438 \u0434\u0430\u043d\u043d\u044b\u0445, \u0443\u0436\u0435 "
                    "\u0432\u0435\u0440\u043d\u0443\u0442\u044b\u0445 backend."
                ),
            },
            {
                "kind": "stack_visibility",
                "message": (
                    "Selected stack \u043d\u0435 \u0432\u0438\u0434\u0435\u043d "
                    f"\u0432 public snippets \u0443 {signals['selected_stack_not_visible']} "
                    "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432; "
                    "\u044d\u0442\u043e \u043d\u0435 \u0434\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0435\u0442, "
                    "\u0447\u0442\u043e \u0443 \u043d\u0438\u0445 \u043d\u0435\u0442 "
                    "\u044d\u0442\u043e\u0433\u043e stack."
                ),
            },
            {
                "kind": "seniority_visibility",
                "message": (
                    "Seniority \u043d\u0435 \u0432\u0438\u0434\u0435\u043d "
                    f"\u0443 {signals['seniority_not_visible']} "
                    "\u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432."
                ),
            },
        ]

    return [
        {
            "kind": "public_snippets",
            "message": (
                "This response is based only on public snippets and data already "
                "returned by the backend."
            ),
        },
        {
            "kind": "stack_visibility",
            "message": (
                "Selected stack is not visible in public snippets for "
                f"{signals['selected_stack_not_visible']} candidates; this does "
                "not prove they lack that stack."
            ),
        },
        {
            "kind": "seniority_visibility",
            "message": (
                f"Seniority is not visible for {signals['seniority_not_visible']} "
                "candidates."
            ),
        },
    ]


def agent_response_suggested_next_actions_source_messages(
    language: str,
    summary_facts: dict,
) -> list[dict[str, object]]:
    if language == "ru":
        return [
            {
                "label": "\u041f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c top candidates",
                "description": (
                    "\u041d\u0430\u0447\u0430\u0442\u044c \u0441 strong bucket "
                    "\u0438 \u043f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c "
                    "\u043f\u0440\u043e\u0444\u0438\u043b\u0438 \u0432\u0440\u0443\u0447\u043d\u0443\u044e."
                ),
                "executable": False,
            },
            {
                "label": "\u0423\u0442\u043e\u0447\u043d\u0438\u0442\u044c stack",
                "description": (
                    "\u0415\u0441\u043b\u0438 stack \u0432 snippets "
                    "\u0432\u0438\u0434\u0435\u043d \u0441\u043b\u0430\u0431\u043e, "
                    "\u043c\u043e\u0436\u043d\u043e \u0438\u0437\u043c\u0435\u043d\u0438\u0442\u044c "
                    "\u0438\u043b\u0438 \u0441\u0443\u0437\u0438\u0442\u044c stack."
                ),
                "executable": False,
            },
        ]

    return [
        {
            "label": "Review top candidates",
            "description": "Start with the strong bucket and manually inspect profiles.",
            "executable": False,
        },
        {
            "label": "Adjust stack",
            "description": (
                "If stack visibility is weak in snippets, consider narrowing or "
                "changing selected stack terms."
            ),
            "executable": False,
        },
    ]


def next_iteration_review_high_quality_candidates_source_copy(
    strong_count: int,
    language: str = "en",
) -> tuple[str, str]:
    if language == "ru":
        return (
            "\u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c strong candidates",
            (
                f"{strong_count} \u043a\u0430\u043d\u0434\u0438\u0434\u0430\u0442\u043e\u0432 \u0432 strong quality bucket. "
                "\u042d\u0442\u043e \u0442\u043e\u043b\u044c\u043a\u043e review-focus \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u0438\u0435; "
                "\u043e\u043d\u043e \u043d\u0435 \u043c\u0435\u043d\u044f\u0435\u0442 search summary."
            ),
        )
    return (
        "Review high-quality candidates first",
        (
            f"{strong_count} candidates are in the strong quality bucket. "
            "This is a review-focus suggestion only and does not change the search."
        ),
    )


def next_iteration_narrow_visible_stack_source_copy(
    visible_selected_stack: list[str],
    missing_selected_stack: list[str],
    language: str = "en",
) -> tuple[str, str]:
    if language == "ru":
        return (
            "\u0421\u0443\u0437\u0438\u0442\u044c stack \u0434\u043e \u0432\u0438\u0434\u0438\u043c\u044b\u0445 selected terms",
            (
                "\u0412 \u0442\u0435\u043a\u0443\u0449\u0438\u0445 \u0440\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u0430\u0445 \u043f\u0440\u044f\u043c\u043e \u0432\u0438\u0434\u043d\u044b "
                f"{', '.join(visible_selected_stack)}, \u0430 "
                f"{', '.join(missing_selected_stack)} \u043d\u0435 \u0432\u0438\u0434\u043d\u044b \u0432 returned snippets."
            ),
        )
    return (
        "Narrow stack to visible selected terms",
        (
            "Current results directly show "
            f"{', '.join(visible_selected_stack)}, while "
            f"{', '.join(missing_selected_stack)} is not visible in returned snippets."
        ),
    )


def next_iteration_broaden_observed_stack_source_copy(
    term: str,
    count: int,
    language: str = "en",
) -> tuple[str, str]:
    if language == "ru":
        return (
            f"\u0420\u0430\u0441\u0448\u0438\u0440\u0438\u0442\u044c stack \u0447\u0435\u0440\u0435\u0437 {term}",
            (
                f"{term} \u0432\u0438\u0434\u0435\u043d \u0443 {count} returned candidates, "
                "\u043d\u043e \u0435\u0433\u043e \u043d\u0435\u0442 \u0432 selected stack."
            ),
        )
    return (
        f"Broaden stack with {term}",
        (
            f"{term} is visible in {count} returned candidates but is not "
            "part of the selected stack."
        ),
    )


def next_iteration_clarify_stack_source_copy(language: str = "en") -> tuple[str, str]:
    if language == "ru":
        return (
            "\u0423\u0442\u043e\u0447\u043d\u0438\u0442\u044c stack preference",
            (
                "Selected stack \u043d\u0435 \u0432\u0438\u0434\u0435\u043d \u0432 returned public snippets. "
                "\u0421\u0430\u043c\u044b\u0439 \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 next step - \u0443\u0442\u043e\u0447\u043d\u0438\u0442\u044c, "
                "\u043e\u0441\u0442\u0430\u0432\u0438\u0442\u044c \u0438\u043b\u0438 \u0437\u0430\u043c\u0435\u043d\u0438\u0442\u044c \u044d\u0442\u043e\u0442 stack."
            ),
        )
    return (
        "Clarify stack preference",
        (
            "Selected stack is not directly visible in the returned public snippets. "
            "The safest next step is to ask whether to keep or replace it."
        ),
    )


def next_iteration_deep_search_source_copy(language: str = "en") -> tuple[str, str]:
    if language == "ru":
        return (
            "\u041f\u043e\u043f\u0440\u043e\u0431\u043e\u0432\u0430\u0442\u044c deep search depth",
            (
                "\u0422\u0435\u043a\u0443\u0449\u0438\u0439 search summary \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0435\u0442 standard depth. "
                "Deep depth - \u044d\u0442\u043e search-level change, \u043a\u043e\u0442\u043e\u0440\u044b\u0439 "
                "\u043d\u0443\u0436\u043d\u043e \u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u043f\u043e\u0434\u0433\u043e\u0442\u043e\u0432\u0438\u0442\u044c."
            ),
        )
    return (
        "Try deep search depth",
        (
            "The current search uses standard depth. Deep depth is a search-level "
            "change that must be prepared before running."
        ),
    )
