from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import main  # noqa: E402


WORKSPACE_JS_UAT = REPO_ROOT / "scripts" / "uat_phase_8_75_workspace_cases.js"
PLAN_DOC = REPO_ROOT / "docs" / "phase-8-75-uat-acceptance-gate.md"
REPORT_DOC = REPO_ROOT / "docs" / "phase-8-75-uat-report.md"


@dataclass
class CaseResult:
    case_id: str
    category: str
    status: str
    detail: str = ""


class UatRunner:
    def __init__(self) -> None:
        self.results: list[CaseResult] = []

    def check(self, case_id: str, category: str, assertion: Callable[[], None]) -> None:
        try:
            assertion()
        except Exception as exc:
            self.results.append(CaseResult(case_id, category, "fail", str(exc)))
            raise
        self.results.append(CaseResult(case_id, category, "pass"))

    def add_external_summary(self, prefix: str, category: str, summary: dict[str, Any]) -> None:
        total = int(summary.get("total") or 0)
        failed = int(summary.get("failed") or 0)
        for index in range(1, total + 1):
            status = "fail" if failed and index <= failed else "pass"
            self.results.append(CaseResult(f"{prefix}-{index:03d}", category, status))

    def summary(self) -> dict[str, Any]:
        counter = Counter(result.status for result in self.results)
        categories = Counter(result.category for result in self.results)
        failures = [result for result in self.results if result.status != "pass"]
        return {
            "total": len(self.results),
            "passed": counter.get("pass", 0),
            "failed": counter.get("fail", 0),
            "categories": dict(sorted(categories.items())),
            "failed_cases": [failure.__dict__ for failure in failures],
        }


def node_executable() -> str:
    configured = os.environ.get("NODE_EXE")
    if configured:
        return configured
    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / "node.exe"
    )
    if bundled.exists():
        return str(bundled)
    return "node"


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def ready_brief(
    *,
    source_text: str = "Find Backend Developer Java in Ukraine with Spring and Kafka.",
    stack: list[str] | None = None,
    location: str = "Ukraine",
    technology: str = "Java",
    role_family: str = "Backend Developer",
    seniority: str | None = None,
    search_depth: str = "standard",
) -> main.SearchBrief:
    selected_stack = stack if stack is not None else ["Spring", "Kafka"]
    return main.SearchBrief(
        source_text=source_text,
        brief_status="ready_for_planning",
        role_family=role_family,
        technology=technology,
        stack=selected_stack,
        location=location,
        seniority=seniority,
        must_have=[technology] if technology else [],
        nice_to_have=selected_stack,
        exclusions=[],
        search_depth=search_depth,
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


def brief_dict(
    text: str,
    *,
    stack: list[str],
    location: str = "Ukraine",
    technology: str = "Java",
    role_family: str = "Backend Developer",
    seniority: str | None = None,
    status: str = "ready_for_planning",
) -> dict[str, Any]:
    return {
        "source_text": text,
        "brief_status": status,
        "role_family": role_family,
        "technology": technology,
        "stack": stack,
        "location": location,
        "seniority": seniority,
        "must_have": [technology] if technology else [],
        "nice_to_have": stack,
        "exclusions": [],
        "search_depth": "standard",
        "profile_sources": ["linkedin_public"],
        "assumptions": [],
    }


CHAT_FIXTURES: dict[str, dict[str, Any]] = {}


def register_chat_fixture(text: str, **kwargs: Any) -> None:
    CHAT_FIXTURES[text] = brief_dict(text, **kwargs)


READY_CHAT_CASES = [
    ("CHAT-READY-001", "Find backend developers in Ukraine with Java, Spring and Kafka.", "en", ["Spring", "Kafka"], None),
    ("CHAT-READY-002", "Find Java backend engineers in Ukraine with Spring Boot and AWS.", "en", ["Spring Boot", "AWS"], None),
    ("CHAT-READY-003", "Need Senior Java Backend Developer in Ukraine, Spring and Docker.", "en", ["Spring", "Docker"], "Senior"),
    ("CHAT-READY-004", "Need Middle Java backend in Ukraine, Hibernate and PostgreSQL.", "en", ["Hibernate", "PostgreSQL"], "Middle"),
    ("CHAT-READY-005", "Java backend Ukraine Kafka AWS Docker.", "en", ["Kafka", "AWS", "Docker"], None),
    ("CHAT-READY-006", "Backend Developer with main skill Java in Ukraine, REST and Microservices.", "en", ["REST", "Microservices"], None),
    ("CHAT-READY-007", "Search Java Software Engineer profiles in Ukraine with Kubernetes and Docker.", "en", ["Kubernetes", "Docker"], None),
    ("CHAT-READY-008", "Find Backend Engineer Java Ukraine with Spring Boot and Kafka.", "en", ["Spring Boot", "Kafka"], None),
    ("CHAT-READY-009", "Найди backend разработчиков в Украине, основной стек Java, Spring и Kafka.", "ru", ["Spring", "Kafka"], None),
    ("CHAT-READY-010", "Ищем Senior Java Backend Developer, Украина, Spring Boot и AWS.", "ru", ["Spring Boot", "AWS"], "Senior"),
    ("CHAT-READY-011", "Нужен Java программист в Киеве, Spring и Docker.", "ru", ["Spring", "Docker"], None),
    ("CHAT-READY-012", "Java backend Украина, Kafka, AWS, Docker.", "ru", ["Kafka", "AWS", "Docker"], None),
    ("CHAT-READY-013", "Найди Java Software Engineer в Украине, Hibernate и PostgreSQL.", "ru", ["Hibernate", "PostgreSQL"], None),
    ("CHAT-READY-014", "Нужен backend разработчик Java, Украина, REST и микросервисы.", "ru", ["REST", "Microservices"], None),
    ("CHAT-READY-015", "Java backend dev Ukraine, спринг и кафка.", "en", ["Spring", "Kafka"], None),
    ("CHAT-READY-016", "Найди Backend Developer Java Ukraine, Kubernetes и Docker.", "ru", ["Kubernetes", "Docker"], None),
]

for _, text, _, stack, seniority in READY_CHAT_CASES:
    register_chat_fixture(text, stack=stack, seniority=seniority)

MISSING_CHAT_CASES = [
    ("CHAT-MISS-001", "Need Java developers in Ukraine.", "en", ["stack"]),
    ("CHAT-MISS-002", "Find backend with Spring and Kafka.", "en", ["location"]),
    ("CHAT-MISS-003", "Java Ukraine.", "en", ["role_family", "stack"]),
    ("CHAT-MISS-004", "Нужен Java разработчик в Украине.", "ru", ["stack"]),
    ("CHAT-MISS-005", "Ищем backend Spring Kafka.", "ru", ["location"]),
    ("CHAT-MISS-006", "Java Украина.", "ru", ["role_family", "stack"]),
]

for _, text, _, missing_fields in MISSING_CHAT_CASES:
    fixture = brief_dict(text, stack=[], status="needs_clarification")
    for field in missing_fields:
        if field == "location":
            fixture["location"] = None
        if field == "role_family":
            fixture["role_family"] = None
    CHAT_FIXTURES[text] = fixture


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    text = request.messages[-1].content
    fixture = CHAT_FIXTURES.get(text)
    if fixture is None:
        return {
            "draft_brief": brief_dict(
                text,
                stack=[],
                location=None,
                status="needs_clarification",
            )
        }, []
    return {"draft_brief": fixture}, []


def chat_request(
    text: str,
    *,
    language: str | None = None,
    draft_brief: main.SearchBrief | None = None,
) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        messages=[main.RecruiterChatMessage(role="user", content=text)],
        language=language,
        draft_brief=draft_brief,
        planner_mode="rule_based",
    )


def build_runtime_context(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "run_multi_wave_search":
        normalized_request, settings, errors = main.normalize_multi_wave_search_request(
            main.MultiWaveStructuredSearchRequest(**tool_input)
        )
    else:
        normalized_request, errors = main.normalize_structured_search_request(
            main.StructuredSearchRequest(**tool_input)
        )
        settings = None
    assert not errors, errors
    query_plan = main.RuleBasedQueryPlannerV1().build(normalized_request)
    context = {
        "planner_mode": "rule_based",
        "tool_name": tool_name,
        "execution_mode": "multi_wave" if tool_name == "run_multi_wave_search" else "single_wave",
        "plan_fingerprint": main.query_plan_fingerprint(query_plan),
        "query_count": len(query_plan["queries"]),
        "search_brief_fingerprint": "uat-brief-fingerprint",
        "multi_wave_enabled": tool_name == "run_multi_wave_search",
    }
    if settings:
        context.update(
            {
                "max_waves": settings["max_waves"],
                "min_new_unique_per_wave": settings["min_new_unique_per_wave"],
                "patience": settings["patience"],
            }
        )
    return context


def runtime_payload(
    *,
    tool_name: str = "run_single_wave_search",
    tool_input: dict[str, Any] | None = None,
    turn_mode: str = "prepare",
    runtime_approval: dict[str, Any] | None = None,
    runtime_context: dict[str, Any] | None = None,
) -> main.AgentRuntimeTurnRequest:
    payload = tool_input or {
        "role_family": "Backend Developer",
        "technology": "Java",
        "stack": ["Spring", "Kafka"],
        "location": "Ukraine",
        "search_depth": "standard",
        "linkedin_profiles_only": True,
        "location_filter_enabled": True,
    }
    return main.AgentRuntimeTurnRequest(
        turn_mode=turn_mode,
        tool_name=tool_name,
        tool_input=payload,
        runtime_context=runtime_context or build_runtime_context(tool_name, payload),
        runtime_approval=runtime_approval,
        agent_language="en",
    )


def approval_from_prepare(prepare_response: dict[str, Any]) -> dict[str, Any]:
    approval = prepare_response["pending_approvals"][0]
    return {
        "approval_status": "approved",
        "tool_call_id": approval["tool_call_id"],
        "tool_name": approval["tool_name"],
        "tool_input_fingerprint": approval["tool_input_fingerprint"],
        "context_fingerprint": approval["context_fingerprint"],
        "idempotency_key": approval["idempotency_key"],
    }


class FakeExecution:
    def __init__(self) -> None:
        self.single_calls = 0
        self.multi_calls = 0
        self.original_single = main.execute_single_wave_structured_search_response
        self.original_multi = main.execute_multi_wave_structured_search_response

    async def single(self, request: Any, query_plan: dict[str, Any], execution_approval: dict[str, Any]) -> dict[str, Any]:
        self.single_calls += 1
        return fake_search_response(query_plan, execution_approval, mode="single_wave")

    async def multi(
        self,
        request: Any,
        query_plan: dict[str, Any],
        settings: dict[str, Any],
        execution_approval: dict[str, Any],
    ) -> dict[str, Any]:
        self.multi_calls += 1
        response = fake_search_response(query_plan, execution_approval, mode="multi_wave")
        response["report"]["waves_run"] = settings["max_waves"]
        response["report"]["queries_executed"] = settings["max_waves"] * len(query_plan["queries"])
        return response

    @property
    def total_calls(self) -> int:
        return self.single_calls + self.multi_calls

    def __enter__(self) -> "FakeExecution":
        main.execute_single_wave_structured_search_response = self.single
        main.execute_multi_wave_structured_search_response = self.multi
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        main.execute_single_wave_structured_search_response = self.original_single
        main.execute_multi_wave_structured_search_response = self.original_multi


def fake_search_response(
    query_plan: dict[str, Any],
    execution_approval: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    return {
        "ok": True,
        "query_plan": query_plan,
        "execution_approval": execution_approval,
        "query_results": [],
        "deduped_results": [
            {
                "normalized_url": "https://ua.linkedin.com/in/mock-java",
                "current_location_status": "target_location",
                "stack_fit": "selected_stack_found",
                "result": {
                    "name": "Mock Java",
                    "title": "Java Backend Developer",
                    "quality_score": 91,
                    "role_display": "Backend Developer",
                    "technology_display": "Java",
                    "current_location_line": "Kyiv, Ukraine",
                    "selected_stack_terms_found": ["Spring", "Kafka"],
                },
            }
        ],
        "report": {
            "queries_total": len(query_plan["queries"]),
            "queries_succeeded": len(query_plan["queries"]),
            "queries_failed": 0,
            "raw_total": 12,
            "normalized_total": 12,
            "unique_profiles": 1,
            "displayed": 1,
            "duplicates_removed": 0,
            "hidden_by_profile_filter": 0,
            "hidden_by_location_filter": 0,
            "hidden_by_foreign_current_location": 0,
            "mode": mode,
        },
        "agent_response": {"message": "Search completed: 1 unique candidate identified: 1 strong, 0 in review, and 0 weak candidates."},
    }


async def run_chat_cases(runner: UatRunner) -> None:
    for case_id, text, language, expected_stack, expected_seniority in READY_CHAT_CASES:
        response = await main.recruiter_chat_turn_response(chat_request(text, language=language))
        if language == "ru" or main.contains_cyrillic_text(text):
            runner.check(f"{case_id}-OK", "chat_english_only", lambda response=response: assert_equal(response["ok"], False))
            runner.check(f"{case_id}-STATE", "chat_english_only", lambda response=response: assert_equal(response["state"], "needs_clarification"))
            runner.check(f"{case_id}-NO-BUILD", "chat_english_only", lambda response=response: assert_equal(response["can_build_plan"], False))
            runner.check(f"{case_id}-NO-BRIEF", "chat_english_only", lambda response=response: assert_equal(response["normalized_brief"], None))
            runner.check(f"{case_id}-MESSAGE", "chat_english_only", lambda response=response: assert_contains((response.get("assistant_message") or "").lower(), "english input only"))
            continue
        runner.check(f"{case_id}-STATE", "chat_ready", lambda response=response: assert_equal(response["state"], "ready_for_planning"))
        runner.check(f"{case_id}-BUILD", "chat_ready", lambda response=response: assert_equal(response["can_build_plan"], True))
        runner.check(f"{case_id}-ROLE", "chat_ready", lambda response=response: assert_equal(response["normalized_brief"]["role_family"], "Backend Developer"))
        runner.check(f"{case_id}-TECH", "chat_ready", lambda response=response: assert_equal(response["normalized_brief"]["technology"], "Java"))
        runner.check(f"{case_id}-LOC", "chat_ready", lambda response=response: assert_equal(response["normalized_brief"]["location"], "Ukraine"))
        runner.check(f"{case_id}-STACK", "chat_ready", lambda response=response, expected_stack=expected_stack: assert_equal(response["normalized_brief"]["stack"], expected_stack))
        runner.check(f"{case_id}-SENIORITY", "chat_ready", lambda response=response, expected_seniority=expected_seniority: assert_equal(response["normalized_brief"].get("seniority"), expected_seniority))

    for case_id, text, language, _missing_fields in MISSING_CHAT_CASES:
        response = await main.recruiter_chat_turn_response(chat_request(text, language=language))
        if language == "ru" or main.contains_cyrillic_text(text):
            runner.check(f"{case_id}-OK", "chat_english_only", lambda response=response: assert_equal(response["ok"], False))
            runner.check(f"{case_id}-STATE", "chat_english_only", lambda response=response: assert_equal(response["state"], "needs_clarification"))
            runner.check(f"{case_id}-NO-BUILD", "chat_english_only", lambda response=response: assert_equal(response["can_build_plan"], False))
            runner.check(f"{case_id}-NO-BRIEF", "chat_english_only", lambda response=response: assert_equal(response["normalized_brief"], None))
            runner.check(f"{case_id}-MESSAGE", "chat_english_only", lambda response=response: assert_contains((response.get("assistant_message") or "").lower(), "english input only"))
            continue
        runner.check(f"{case_id}-STATE", "chat_clarification", lambda response=response: assert_equal(response["state"], "needs_clarification"))
        runner.check(f"{case_id}-NO-BUILD", "chat_clarification", lambda response=response: assert_equal(response["can_build_plan"], False))
        runner.check(f"{case_id}-QUESTION", "chat_clarification", lambda response=response: assert_truthy(response.get("next_question") or response.get("assistant_message")))

    behavior_cases = [
        ("CHAT-GUARD-001", "hello", "en", "needs_clarification", True),
        ("CHAT-GUARD-002", "привет", "ru", "needs_clarification", True),
        ("CHAT-GUARD-003", "what is the weather?", "en", "needs_clarification", True),
        ("CHAT-GUARD-004", "какая погода?", "ru", "needs_clarification", True),
        ("CHAT-GUARD-005", "xsdfszdzsz", "en", "needs_clarification", True),
        ("CHAT-GUARD-006", "сантихника", "ru", "needs_clarification", True),
        ("CHAT-GUARD-007", "Open LinkedIn profiles and read them.", "en", "refused", False),
        ("CHAT-GUARD-008", "Зайди в LinkedIn и напиши кандидатам.", "ru", "refused", False),
        ("CHAT-GUARD-009", "Search Google directly outside backend.", "en", "refused", False),
        ("CHAT-GUARD-010", "Собери email и телефоны кандидатов.", "ru", "refused", False),
    ]
    for case_id, text, language, expected_state, expected_ok in behavior_cases:
        response = await main.recruiter_chat_turn_response(chat_request(text, language=language))
        if language == "ru" or main.contains_cyrillic_text(text):
            expected_ok = False
            expected_state = "needs_clarification"
        runner.check(f"{case_id}-OK", "chat_guardrails", lambda response=response, expected_ok=expected_ok: assert_equal(response["ok"], expected_ok))
        runner.check(f"{case_id}-STATE", "chat_guardrails", lambda response=response, expected_state=expected_state: assert_equal(response["state"], expected_state))
        runner.check(f"{case_id}-NO-BUILD", "chat_guardrails", lambda response=response: assert_equal(response["can_build_plan"], False))

    refinement_cases = [
        ("CHAT-REF-001", "add Docker", "en", ["Spring", "Kafka", "Docker"], True),
        ("CHAT-REF-002", "remove Kafka and add Docker", "en", ["Spring", "Docker"], True),
        ("CHAT-REF-003", "only Spring", "en", ["Spring"], True),
        ("CHAT-REF-004", "senior", "en", ["Spring", "Kafka"], True),
        ("CHAT-REF-005", "добавь Докер", "ru", ["Spring", "Kafka", "Docker"], True),
        ("CHAT-REF-006", "убери Kafka и добавь AWS", "ru", ["Spring", "AWS"], True),
        ("CHAT-REF-007", "remove Spring", "en", ["Kafka"], True),
    ]
    for case_id, text, language, expected_stack, expect_patch in refinement_cases:
        response = await main.recruiter_chat_turn_response(
            chat_request(text, language=language, draft_brief=ready_brief())
        )
        if language == "ru" or main.contains_cyrillic_text(text):
            runner.check(f"{case_id}-OK", "chat_english_only", lambda response=response: assert_equal(response["ok"], False))
            runner.check(f"{case_id}-STATE", "chat_english_only", lambda response=response: assert_equal(response["state"], "needs_clarification"))
            runner.check(f"{case_id}-NO-BUILD", "chat_english_only", lambda response=response: assert_equal(response["can_build_plan"], False))
            runner.check(f"{case_id}-NO-BRIEF", "chat_english_only", lambda response=response: assert_equal(response["normalized_brief"], None))
            continue
        runner.check(f"{case_id}-STATE", "chat_refinement", lambda response=response: assert_equal(response["state"], "ready_for_planning"))
        runner.check(f"{case_id}-STACK", "chat_refinement", lambda response=response, expected_stack=expected_stack: assert_equal(response["normalized_brief"]["stack"], expected_stack))
        runner.check(f"{case_id}-PATCH", "chat_refinement", lambda response=response, expect_patch=expect_patch: assert_equal(bool(response.get("brief_patch")), expect_patch))


def assert_equal(actual: Any, expected: Any) -> None:
    assert actual == expected, f"expected {expected!r}, got {actual!r}"


def assert_truthy(value: Any) -> None:
    assert value, "expected truthy value"


def assert_contains(text: str, needle: str) -> None:
    assert needle in text, f"missing {needle!r}"


def assert_not_contains(text: str, needle: str) -> None:
    assert needle not in text, f"unexpected {needle!r}"


def run_brief_and_plan_cases(runner: UatRunner) -> None:
    stack_sets = [
        ["Spring"],
        ["Kafka"],
        ["Spring", "Kafka"],
        ["Spring Boot", "AWS"],
        ["Hibernate", "PostgreSQL"],
        ["Docker", "Kubernetes"],
        ["REST", "Microservices"],
        ["Kafka", "AWS", "Docker"],
    ]
    for index, stack in enumerate(stack_sets, start=1):
        brief = ready_brief(stack=stack)
        validation = main.search_brief_validation_response(brief)
        runner.check(f"BRIEF-{index:03d}-OK", "brief_validation", lambda validation=validation: assert_equal(validation["errors"], []))
        runner.check(f"BRIEF-{index:03d}-STATUS", "brief_validation", lambda validation=validation: assert_equal(validation["normalized_brief"]["brief_status"], "ready_for_planning"))
        runner.check(f"BRIEF-{index:03d}-REQUEST", "brief_validation", lambda validation=validation: assert_equal(validation["adapted_structured_request"]["stack"], stack))
        plan = main.build_agent_plan_response(main.AgentPlanRequest(search_brief=brief, language="en"))
        runner.check(f"PLAN-{index:03d}-SUPPORTED", "agent_plan", lambda plan=plan: assert_equal(plan["agent_plan_status"], "supported"))
        runner.check(f"PLAN-{index:03d}-ACTION", "agent_plan", lambda plan=plan: assert_equal(plan["agent_plan"]["proposed_action"]["endpoint"], "/api/agent/query-plan"))

    missing_stack = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(stack=[]), language="en")
    )
    runner.check("PLAN-MISSING-STACK-001", "agent_plan", lambda: assert_equal(missing_stack["agent_plan_status"], "needs_clarification"))
    runner.check("PLAN-MISSING-STACK-002", "agent_plan", lambda: assert_equal(missing_stack["agent_plan"], None))

    unsupported_depth = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(search_depth="deep"), language="en")
    )
    runner.check("PLAN-UNSUPPORTED-DEPTH-001", "agent_plan", lambda: assert_equal(unsupported_depth["agent_plan_status"], "unsupported"))

    generic_location = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(location="Poland"), language="en")
    )
    runner.check("PLAN-GENERIC-LOCATION-001", "agent_plan", lambda: assert_equal(generic_location["agent_plan_status"], "supported"))
    runner.check("PLAN-GENERIC-LOCATION-002", "agent_plan", lambda: assert_truthy(generic_location["agent_plan"]))
    runner.check("PLAN-GENERIC-LOCATION-003", "agent_plan", lambda: assert_equal(generic_location["validation_errors"], []))

    generic_technology = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(technology="JavaScript"), language="en")
    )
    runner.check("PLAN-GENERIC-TECH-001", "agent_plan", lambda: assert_equal(generic_technology["agent_plan_status"], "supported"))
    runner.check("PLAN-GENERIC-TECH-002", "agent_plan", lambda: assert_truthy(generic_technology["agent_plan"]))
    runner.check("PLAN-GENERIC-TECH-003", "agent_plan", lambda: assert_equal(generic_technology["validation_errors"], []))


async def run_query_plan_cases(runner: UatRunner) -> None:
    brief = ready_brief(stack=["Spring", "Kafka"])
    agent_plan = main.build_agent_plan_response(main.AgentPlanRequest(search_brief=brief, language="en"))
    action = agent_plan["agent_plan"]["proposed_action"]
    fingerprint = agent_plan["agent_plan"]["brief_fingerprint"]

    query_plan = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=brief,
            agent_plan_brief_fingerprint=fingerprint,
            agent_plan_action=action,
        )
    )
    runner.check("QUERY-PLAN-001", "query_plan", lambda: assert_equal(query_plan["ok"], True))
    runner.check("QUERY-PLAN-002", "query_plan", lambda: assert_equal(query_plan["plan_status"], "validated_not_executable"))
    runner.check("QUERY-PLAN-003", "query_plan", lambda: assert_equal(len(query_plan["query_plan"]["queries"]), 10))
    runner.check("QUERY-PLAN-004", "query_plan", lambda: assert_equal(query_plan["execution_approval_required"], True))
    runner.check("QUERY-PLAN-005", "query_plan", lambda: assert_equal(query_plan["execution_allowed"], False))

    stale = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=brief,
            agent_plan_brief_fingerprint="stale",
            agent_plan_action=action,
        )
    )
    runner.check("QUERY-PLAN-STALE-001", "query_plan", lambda: assert_equal(stale["ok"], False))
    runner.check(
        "QUERY-PLAN-STALE-002",
        "query_plan",
        lambda: assert_truthy(any(error.get("code") == "stale_or_mismatched_agent_plan_fingerprint" for error in stale["errors"])),
    )

    missing_context = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(planner_mode="rule_based", search_brief=brief)
    )
    runner.check("QUERY-PLAN-MISSING-001", "query_plan", lambda: assert_equal(missing_context["ok"], False))
    runner.check("QUERY-PLAN-MISSING-002", "query_plan", lambda: assert_truthy(missing_context["errors"]))


async def run_runtime_cases(runner: UatRunner) -> None:
    previous_tavily = os.environ.get("TAVILY_API_KEY")
    os.environ["TAVILY_API_KEY"] = "fake-uat-tavily-key"
    try:
        with FakeExecution() as execution:
            prepare = await main.create_agent_runtime_turn(runtime_payload())
            runner.check("RUNTIME-PREPARE-001", "runtime", lambda: assert_equal(prepare["ok"], True))
            runner.check("RUNTIME-PREPARE-002", "runtime", lambda: assert_equal(prepare["runtime_state"], "approval_pending"))
            runner.check("RUNTIME-PREPARE-003", "runtime", lambda: assert_equal(execution.total_calls, 0))

            approval = approval_from_prepare(prepare)
            observed = await main.create_agent_runtime_turn(
                runtime_payload(turn_mode="execute_approved", runtime_approval=approval)
            )
            runner.check("RUNTIME-EXEC-001", "runtime", lambda: assert_equal(observed["ok"], True))
            runner.check("RUNTIME-EXEC-002", "runtime", lambda: assert_equal(observed["runtime_state"], "observed"))
            runner.check("RUNTIME-EXEC-003", "runtime", lambda: assert_equal(execution.single_calls, 1))

            stale_approval = dict(approval)
            stale_approval["tool_input_fingerprint"] = "stale"
            blocked = await main.create_agent_runtime_turn(
                runtime_payload(turn_mode="execute_approved", runtime_approval=stale_approval)
            )
            runner.check("RUNTIME-BLOCK-001", "runtime", lambda: assert_equal(blocked["ok"], False))
            runner.check("RUNTIME-BLOCK-002", "runtime", lambda: assert_equal(blocked["runtime_state"], "blocked"))

            multi_input = {
                "role_family": "Backend Developer",
                "technology": "Java",
                "stack": ["Spring", "Kafka"],
                "location": "Ukraine",
                "search_depth": "standard",
                "linkedin_profiles_only": True,
                "location_filter_enabled": True,
                "max_waves": 2,
                "min_new_unique_per_wave": 1,
                "patience": 1,
            }
            multi_prepare = await main.create_agent_runtime_turn(
                runtime_payload(tool_name="run_multi_wave_search", tool_input=multi_input)
            )
            multi_approval = approval_from_prepare(multi_prepare)
            multi_observed = await main.create_agent_runtime_turn(
                runtime_payload(
                    tool_name="run_multi_wave_search",
                    tool_input=multi_input,
                    turn_mode="execute_approved",
                    runtime_approval=multi_approval,
                )
            )
            runner.check("RUNTIME-MULTI-001", "runtime", lambda: assert_equal(multi_prepare["runtime_state"], "approval_pending"))
            runner.check("RUNTIME-MULTI-002", "runtime", lambda: assert_equal(multi_observed["runtime_state"], "observed"))
            runner.check("RUNTIME-MULTI-003", "runtime", lambda: assert_equal(execution.multi_calls, 1))
    finally:
        if previous_tavily is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = previous_tavily


def run_static_contract_cases(runner: UatRunner) -> None:
    docs = {
        "tasks": read("Tasks.md"),
        "project": read("ProjectStatus.md"),
        "roadmap": read("Roadmap.md"),
        "readme": read("README.md"),
        "agents": read("AGENTS.md"),
        "p85": read("docs/phase-8-5-agentic-candidate-review-contract.md"),
        "app": read("app/static/app.js"),
        "workspace": read("app/static/candidate_workspace.js"),
        "check_all": read("scripts/check_all.ps1"),
    }
    checks = [
        ("STATIC-001", "tasks", "Phase 8.75"),
        ("STATIC-002", "tasks", "P8.75-001"),
        ("STATIC-003", "project", "Phase 8.75"),
        ("STATIC-004", "roadmap", "Phase 8.75"),
        ("STATIC-005", "readme", "Phase 8.75"),
        ("STATIC-006", "agents", "Phase 8.75"),
        ("STATIC-007", "p85", "must not execute searches"),
        ("STATIC-008", "p85", "Recruiter notes remain local/private"),
        ("STATIC-009", "app", "const DEFAULT_MULTI_WAVE_ENABLED = true;"),
        ("STATIC-010", "app", "handlePendingSearchRunChatAction"),
        ("STATIC-011", "app", "renderWorkspaceRefinementSuggestions"),
        ("STATIC-012", "workspace", "buildWorkspaceRefinementSuggestions"),
        ("STATIC-013", "workspace", "source: \"deterministic_workspace_facts\""),
        ("STATIC-014", "check_all", "scripts/uat_phase_8_75_no_live.py"),
    ]
    for case_id, key, needle in checks:
        runner.check(case_id, "static_contracts", lambda key=key, needle=needle: assert_contains(docs[key], needle))

    forbidden_static_pairs = [
        ("STATIC-FORBID-001", "app", "window.open(candidate"),
        ("STATIC-FORBID-002", "workspace", "localStorage"),
        ("STATIC-FORBID-003", "workspace", "sessionStorage"),
        ("STATIC-FORBID-004", "workspace", "indexedDB"),
    ]
    for case_id, key, needle in forbidden_static_pairs:
        runner.check(case_id, "static_contracts", lambda key=key, needle=needle: assert_not_contains(docs[key], needle))


def run_workspace_js_cases(runner: UatRunner) -> None:
    completed = subprocess.run(
        [node_executable(), str(WORKSPACE_JS_UAT), "--json"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(completed.stdout)
    if summary.get("failed"):
        raise AssertionError(f"Workspace JS UAT failed: {summary}")
    runner.add_external_summary("P875-WSJS", "workspace_js", summary)


def write_report(summary: dict[str, Any], output_path: Path) -> None:
    categories = "\n".join(
        f"| {category} | {count} |"
        for category, count in summary["categories"].items()
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    failed_cases = summary["failed_cases"]
    failure_text = "None." if not failed_cases else "\n".join(
        f"- `{case['case_id']}` ({case['category']}): {case['detail']}"
        for case in failed_cases
    )
    output_path.write_text(
        f"""# Phase 8.75 UAT Report

Generated: {now}

## No-Live Acceptance Run

Status: `green`

| Metric | Count |
| --- | ---: |
| total no-live checks | {summary['total']} |
| passed | {summary['passed']} |
| failed | {summary['failed']} |

## No-Live Category Coverage

| Category | Checks |
| --- | ---: |
{categories}

## Live Acceptance Run

Status: `pending`

The live Tavily run is recorded by `scripts/uat_phase_8_75_live.py` after the no-live gate is green. The live run must use the existing backend runtime approval path and must not commit raw candidate data, profile URLs, Tavily payloads, or secrets.

## Failures

{failure_text}

## Analysis

The no-live gate covers recruiter chat behavior, Search Brief validation, Agent Plan and QueryPlan boundaries, runtime approval guardrails, Candidate Workspace mapping/view/review/export helpers, Phase 8.5 agentic review helpers, and static product boundaries. It is deterministic and safe to run in CI.
""",
        encoding="utf-8",
    )


async def run_all(write_report_path: Path | None) -> dict[str, Any]:
    runner = UatRunner()
    original_chat_llm = main.run_openai_json_recruiter_chat
    original_wording_llm = main.run_openai_json_agent_wording
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }

    async def no_live_wording(*_args: Any, **_kwargs: Any) -> tuple[dict | None, list[dict[str, str]]]:
        return None, [{"field": "openai", "message": "No-live UAT disables OpenAI wording."}]

    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm
    main.run_openai_json_agent_wording = no_live_wording
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    try:
        run_static_contract_cases(runner)
        await run_chat_cases(runner)
        run_brief_and_plan_cases(runner)
        await run_query_plan_cases(runner)
        await run_runtime_cases(runner)
        run_workspace_js_cases(runner)
    finally:
        main.run_openai_json_recruiter_chat = original_chat_llm
        main.run_openai_json_agent_wording = original_wording_llm
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    summary = runner.summary()
    if summary["failed"]:
        raise AssertionError(f"Phase 8.75 no-live UAT failed: {summary['failed_cases']}")
    if summary["total"] < 100:
        raise AssertionError(f"Expected at least 100 no-live checks, got {summary['total']}")
    if write_report_path:
        write_report(summary, write_report_path)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 8.75 no-live UAT acceptance checks.")
    parser.add_argument(
        "--write-report",
        type=Path,
        default=None,
        help="Optional Markdown report path to write.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    return parser.parse_args()


def main_entry() -> None:
    args = parse_args()
    summary = asyncio.run(run_all(args.write_report))
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "Phase 8.75 no-live UAT passed: "
            f"{summary['passed']}/{summary['total']} checks"
        )


if __name__ == "__main__":
    main_entry()
