from collections.abc import Awaitable, Callable

from app.agent_messages import (
    AGENT_PLAN_ERROR_MISMATCHED_PLANNER_MODE,
    AGENT_PLAN_ERROR_MISSING_ACTION,
    AGENT_PLAN_ERROR_MISSING_FINGERPRINT,
    AGENT_PLAN_ERROR_STALE_FINGERPRINT,
    AGENT_PLAN_ERROR_UNSUPPORTED_ACTION,
    AGENT_PLAN_ERROR_UNSUPPORTED_BASELINE,
    agent_message_language,
    agent_plan_action_error_source_message,
    agent_plan_needs_clarification_source_message,
    agent_plan_supported_source_message,
    agent_plan_unsupported_source_message,
)
from app.agent_tools import AGENT_ACTION_BUILD_QUERY_PLAN, AGENT_QUERY_PLAN_ENDPOINT
from app.domain_config import (
    PLANNER_MODE_RULE_BASED,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
    SEARCH_DEPTH_STANDARD,
)
from app.planning import add_plan_validation_error
from app.schemas import AgentPlanRequest, AgentQueryPlanRequest
from app.search_brief import search_brief_fingerprint, search_brief_validation_response


AGENT_PLAN_STATUS_SUPPORTED = "supported"
AGENT_PLAN_STATUS_NEEDS_CLARIFICATION = "needs_clarification"
AGENT_PLAN_STATUS_UNSUPPORTED = "unsupported"

ValidationErrorFormatter = Callable[[list[dict[str, str]], str], str]
AgentPlanWordingApplier = Callable[[dict, dict, str], Awaitable[dict]]


def agent_plan_language(language: str | None, normalized_brief: dict | None = None) -> str:
    return agent_message_language(language, normalized_brief)


def agent_plan_proposed_action() -> dict:
    return {
        "action": AGENT_ACTION_BUILD_QUERY_PLAN,
        "endpoint": AGENT_QUERY_PLAN_ENDPOINT,
        "planner_mode": PLANNER_MODE_RULE_BASED,
        "requires_approval": False,
    }


def is_supported_agent_v0_baseline(
    normalized_brief: dict,
    normalized_request: dict | None,
) -> bool:
    if not normalized_request:
        return False

    return (
        normalized_request.get("role_family") == "Backend Developer"
        and normalized_request.get("technology") == "Java"
        and normalized_request.get("location") == "Ukraine"
        and bool(normalized_request.get("stack"))
        and (normalized_brief.get("search_depth") or SEARCH_DEPTH_STANDARD)
        == SEARCH_DEPTH_STANDARD
    )


def agent_plan_supported_message(language: str, normalized_request: dict) -> str:
    return agent_plan_supported_source_message(language, normalized_request)


def agent_plan_needs_clarification_message(language: str) -> str:
    return agent_plan_needs_clarification_source_message(language)


def agent_plan_unsupported_message(language: str) -> str:
    return agent_plan_unsupported_source_message(language)


def build_agent_plan_response(
    request: AgentPlanRequest,
    validation_error_formatter: ValidationErrorFormatter,
) -> dict:
    brief_response = search_brief_validation_response(request.search_brief)
    normalized_brief = brief_response["normalized_brief"]
    language = agent_plan_language(request.language, normalized_brief)

    if brief_response["errors"]:
        return {
            "ok": False,
            "agent_plan_status": AGENT_PLAN_STATUS_NEEDS_CLARIFICATION,
            "agent_plan": None,
            "message": validation_error_formatter(brief_response["errors"], language),
            "normalized_brief": normalized_brief,
            "adapted_structured_request": None,
            "missing_fields": brief_response["missing_fields"],
            "clarifying_questions": brief_response["clarifying_questions"],
            "errors": brief_response["errors"],
            "validation_errors": brief_response["errors"],
        }

    if normalized_brief["brief_status"] != SEARCH_BRIEF_STATUS_READY_FOR_PLANNING:
        return {
            "ok": True,
            "agent_plan_status": AGENT_PLAN_STATUS_NEEDS_CLARIFICATION,
            "agent_plan": None,
            "message": agent_plan_needs_clarification_message(language),
            "normalized_brief": normalized_brief,
            "adapted_structured_request": None,
            "missing_fields": normalized_brief.get("missing_fields", []),
            "clarifying_questions": normalized_brief.get("clarifying_questions", []),
            "errors": [],
            "validation_errors": [],
        }

    normalized_request = brief_response["adapted_structured_request"]
    if not is_supported_agent_v0_baseline(normalized_brief, normalized_request):
        return {
            "ok": True,
            "agent_plan_status": AGENT_PLAN_STATUS_UNSUPPORTED,
            "agent_plan": None,
            "message": agent_plan_unsupported_message(language),
            "normalized_brief": normalized_brief,
            "adapted_structured_request": normalized_request,
            "missing_fields": [],
            "clarifying_questions": [],
            "errors": [],
            "validation_errors": [],
        }

    fingerprint = search_brief_fingerprint(normalized_brief)
    message = agent_plan_supported_message(language, normalized_request)
    agent_plan = {
        "brief_fingerprint": fingerprint,
        "input_snapshot": normalized_brief,
        "message": message,
        "proposed_action": agent_plan_proposed_action(),
    }

    return {
        "ok": True,
        "agent_plan_status": AGENT_PLAN_STATUS_SUPPORTED,
        "agent_plan": agent_plan,
        "message": message,
        "normalized_brief": normalized_brief,
        "adapted_structured_request": normalized_request,
        "missing_fields": [],
        "clarifying_questions": [],
        "errors": [],
        "validation_errors": [],
    }


async def build_agent_plan_response_with_wording(
    request: AgentPlanRequest,
    validation_error_formatter: ValidationErrorFormatter,
    wording_applier: AgentPlanWordingApplier,
) -> dict:
    response = build_agent_plan_response(request, validation_error_formatter)
    agent_plan = response.get("agent_plan")
    normalized_request = response.get("adapted_structured_request")

    if (
        response.get("ok") is True
        and response.get("agent_plan_status") == AGENT_PLAN_STATUS_SUPPORTED
        and isinstance(agent_plan, dict)
        and isinstance(normalized_request, dict)
    ):
        language = agent_plan_language(request.language, response.get("normalized_brief"))
        worded_agent_plan = await wording_applier(
            agent_plan,
            normalized_request,
            language,
        )
        response["agent_plan"] = worded_agent_plan
        response["message"] = worded_agent_plan["message"]

    return response


def validate_agent_query_plan_action(
    request: AgentQueryPlanRequest,
    normalized_brief: dict,
    normalized_request: dict,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    action = request.agent_plan_action
    fingerprint = request.agent_plan_brief_fingerprint

    expected_fingerprint = search_brief_fingerprint(normalized_brief)
    if not fingerprint:
        add_plan_validation_error(
            errors,
            "agent_plan_brief_fingerprint",
            AGENT_PLAN_ERROR_MISSING_FINGERPRINT,
            agent_plan_action_error_source_message(AGENT_PLAN_ERROR_MISSING_FINGERPRINT),
        )
    elif fingerprint != expected_fingerprint:
        add_plan_validation_error(
            errors,
            "agent_plan_brief_fingerprint",
            AGENT_PLAN_ERROR_STALE_FINGERPRINT,
            agent_plan_action_error_source_message(AGENT_PLAN_ERROR_STALE_FINGERPRINT),
        )

    if not isinstance(action, dict):
        add_plan_validation_error(
            errors,
            "agent_plan_action",
            AGENT_PLAN_ERROR_MISSING_ACTION,
            agent_plan_action_error_source_message(AGENT_PLAN_ERROR_MISSING_ACTION),
        )
        return errors

    expected_action = agent_plan_proposed_action()
    for field, expected_value in expected_action.items():
        if action.get(field) != expected_value:
            add_plan_validation_error(
                errors,
                f"agent_plan_action.{field}",
                AGENT_PLAN_ERROR_UNSUPPORTED_ACTION,
                agent_plan_action_error_source_message(AGENT_PLAN_ERROR_UNSUPPORTED_ACTION),
            )

    if action.get("planner_mode") != request.planner_mode:
        add_plan_validation_error(
            errors,
            "agent_plan_action.planner_mode",
            AGENT_PLAN_ERROR_MISMATCHED_PLANNER_MODE,
            agent_plan_action_error_source_message(
                AGENT_PLAN_ERROR_MISMATCHED_PLANNER_MODE
            ),
        )

    if not is_supported_agent_v0_baseline(normalized_brief, normalized_request):
        add_plan_validation_error(
            errors,
            "agent_plan_action",
            AGENT_PLAN_ERROR_UNSUPPORTED_BASELINE,
            agent_plan_action_error_source_message(AGENT_PLAN_ERROR_UNSUPPORTED_BASELINE),
        )

    return errors
