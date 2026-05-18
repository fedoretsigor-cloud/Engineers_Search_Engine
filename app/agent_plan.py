from collections.abc import Awaitable, Callable
import re

from app.agent_tools import AGENT_ACTION_BUILD_QUERY_PLAN, AGENT_QUERY_PLAN_ENDPOINT
from app.domain_config import (
    PLANNER_MODE_RULE_BASED,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
    SEARCH_DEPTH_STANDARD,
)
from app.planning import add_plan_validation_error
from app.schemas import AgentPlanRequest, AgentQueryPlanRequest
from app.search_brief import search_brief_fingerprint, search_brief_validation_response
from app.text_utils import normalize_text_value


AGENT_PLAN_STATUS_SUPPORTED = "supported"
AGENT_PLAN_STATUS_NEEDS_CLARIFICATION = "needs_clarification"
AGENT_PLAN_STATUS_UNSUPPORTED = "unsupported"

ValidationErrorFormatter = Callable[[list[dict[str, str]], str], str]
AgentPlanWordingApplier = Callable[[dict, dict, str], Awaitable[dict]]


def agent_plan_language(language: str | None, normalized_brief: dict | None = None) -> str:
    normalized_language = (normalize_text_value(language) or "").lower()
    if normalized_language.startswith(("ru", "\u0440\u0443\u0441")):
        return "ru"
    if normalized_language.startswith(("en", "\u0430\u043d\u0433\u043b")):
        return "en"

    source_text = (normalized_brief or {}).get("source_text") or ""
    if re.search(r"[\u0400-\u04ff]", source_text):
        return "ru"

    return "en"


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
    stack_text = ", ".join(normalized_request.get("stack") or []) or "n/a"
    if language == "ru":
        return (
            "\u042f \u043f\u043e\u043d\u044f\u043b \u0437\u0430\u0434\u0430\u0447\u0443: "
            "\u0438\u0449\u0435\u043c Backend Developer \u0441 Java \u0432 "
            f"\u0423\u043a\u0440\u0430\u0438\u043d\u0435, stack: {stack_text}. "
            "\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 "
            "\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u044b\u0439 "
            "\u0448\u0430\u0433 - Build Plan \u0447\u0435\u0440\u0435\u0437 "
            "approved backend planner. \u041f\u043e\u0438\u0441\u043a "
            "\u043d\u0435 \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0441\u044f "
            "\u0431\u0435\u0437 approval."
        )

    return (
        "I understood the task: find Backend Developer profiles with Java in "
        f"Ukraine, stack: {stack_text}. The next safe step is Build Plan through "
        "the approved backend planner. Search will not run without approval."
    )


def agent_plan_needs_clarification_message(language: str) -> str:
    if language == "ru":
        return (
            "\u041c\u043d\u0435 \u043d\u0443\u0436\u0435\u043d stack, "
            "\u0447\u0442\u043e\u0431\u044b \u0441\u043e\u0437\u0434\u0430\u0442\u044c "
            "Agent Plan \u0434\u043b\u044f Java/Ukraine baseline."
        )

    return "I need the missing stack before I can create an Agent Plan."


def agent_plan_unsupported_message(language: str) -> str:
    if language == "ru":
        return (
            "Agent v0 \u043f\u043e\u043a\u0430 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442 "
            "\u0442\u043e\u043b\u044c\u043a\u043e Backend Developer with Java in Ukraine."
        )

    return "Agent v0 currently supports only Backend Developer with Java in Ukraine."


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
            "missing_agent_plan_fingerprint",
            "Build Plan requires the current Agent Plan fingerprint.",
        )
    elif fingerprint != expected_fingerprint:
        add_plan_validation_error(
            errors,
            "agent_plan_brief_fingerprint",
            "stale_or_mismatched_agent_plan_fingerprint",
            "Agent Plan fingerprint does not match the current Search Brief.",
        )

    if not isinstance(action, dict):
        add_plan_validation_error(
            errors,
            "agent_plan_action",
            "missing_agent_plan_action",
            "Build Plan requires a supported Agent Plan proposed_action.",
        )
        return errors

    expected_action = agent_plan_proposed_action()
    for field, expected_value in expected_action.items():
        if action.get(field) != expected_value:
            add_plan_validation_error(
                errors,
                f"agent_plan_action.{field}",
                "unsupported_agent_plan_action",
                "Build Plan proposed_action is not supported.",
            )

    if action.get("planner_mode") != request.planner_mode:
        add_plan_validation_error(
            errors,
            "agent_plan_action.planner_mode",
            "mismatched_agent_plan_planner_mode",
            "Agent Plan planner_mode must match the Build Plan request.",
        )

    if not is_supported_agent_v0_baseline(normalized_brief, normalized_request):
        add_plan_validation_error(
            errors,
            "agent_plan_action",
            "unsupported_agent_v0_baseline",
            "Agent v0 currently supports only Backend Developer with Java in Ukraine.",
        )

    return errors
