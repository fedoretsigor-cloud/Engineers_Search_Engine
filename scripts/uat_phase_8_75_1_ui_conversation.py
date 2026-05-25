from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import sys
from typing import Any, Callable

import uvicorn


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main  # noqa: E402


REPORT_DOC = PROJECT_DIR / "docs" / "phase-8-75-1-conversation-ux-report.md"


@dataclass
class UiStep:
    text: str
    expect: str = "assistant"


@dataclass
class UiScenario:
    case_id: str
    category: str
    language: str
    steps: list[UiStep]
    expected: str
    expected_terms: list[str] = field(default_factory=list)
    expected_stack: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    case_id: str
    category: str
    status: str
    detail: str = ""


CHAT_FIXTURES: dict[str, dict[str, Any]] = {}


def brief_payload(
    text: str,
    *,
    role_family: str | None = "Backend Developer",
    technology: str | None = "Java",
    stack: list[str] | None = None,
    location: str | None = "Ukraine",
    seniority: str | None = None,
    status: str = "ready_for_planning",
) -> dict[str, Any]:
    selected_stack = stack if stack is not None else ["Spring", "Kafka"]
    return {
        "source_text": text,
        "brief_status": status,
        "role_family": role_family,
        "technology": technology,
        "stack": selected_stack,
        "location": location,
        "seniority": seniority,
        "must_have": [technology] if technology else [],
        "nice_to_have": selected_stack,
        "exclusions": [],
        "search_depth": "standard",
        "profile_sources": ["linkedin_public"],
        "assumptions": [],
    }


def register_fixture(text: str, **kwargs: Any) -> None:
    CHAT_FIXTURES[text] = brief_payload(text, **kwargs)


def empty_brief_payload(text: str) -> dict[str, Any]:
    return brief_payload(
        text,
        role_family=None,
        technology=None,
        stack=[],
        location=None,
        status="needs_clarification",
    )


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    text = main.latest_recruiter_chat_user_text(request.messages)
    return {"draft_brief": CHAT_FIXTURES.get(text, empty_brief_payload(text))}, []


async def fake_wording_llm(payload: dict[str, Any]) -> tuple[None, str]:
    return None, "ui_uat_wording_disabled"


def fake_search_response(query_plan: dict[str, Any], execution_approval: dict[str, Any], *, mode: str) -> dict[str, Any]:
    return {
        "ok": True,
        "query_plan": query_plan,
        "execution_approval": execution_approval,
        "query_results": [],
        "deduped_results": [
            {
                "normalized_url": "https://example.invalid/ui-uat-anna",
                "current_location_status": "target_location",
                "stack_fit": "selected_stack_found",
                "result": {
                    "name": "Anna UI",
                    "title": "Senior Java Backend Developer",
                    "url": "https://example.invalid/ui-uat-anna",
                    "quality_score": 94,
                    "role_display": "Backend Developer",
                    "technology_display": "Java",
                    "current_location_line": "Kyiv, Ukraine",
                    "selected_stack_terms_found": ["Spring", "Kafka"],
                },
            },
            {
                "normalized_url": "https://example.invalid/ui-uat-bohdan",
                "current_location_status": "target_location",
                "stack_fit": "selected_stack_found",
                "result": {
                    "name": "Bohdan UI",
                    "title": "Java Software Engineer",
                    "url": "https://example.invalid/ui-uat-bohdan",
                    "quality_score": 82,
                    "role_display": "Java Software Engineer",
                    "technology_display": "Java",
                    "current_location_line": "Ukraine",
                    "selected_stack_terms_found": ["Spring"],
                },
            },
            {
                "normalized_url": "https://example.invalid/ui-uat-christina",
                "current_location_status": "target_location",
                "stack_fit": "stack_query_source_only",
                "result": {
                    "name": "Christina UI",
                    "title": "Backend Engineer",
                    "url": "https://example.invalid/ui-uat-christina",
                    "quality_score": 69,
                    "role_display": "Backend Engineer",
                    "technology_display": "Java",
                    "current_location_line": "Lviv, Ukraine",
                    "selected_stack_terms_found": [],
                    "missing_selected_stack_terms": ["Kafka"],
                },
            },
        ],
        "report": {
            "queries_total": len(query_plan.get("queries", [])),
            "queries_succeeded": len(query_plan.get("queries", [])),
            "queries_failed": 0,
            "raw_total": 30,
            "normalized_total": 30,
            "displayed": 3,
            "unique_profiles": 3,
            "duplicates_removed": 0,
            "hidden_by_profile_filter": 0,
            "hidden_by_location_filter": 0,
            "rescued_by_header_location": 0,
            "hidden_by_foreign_current_location": 0,
            "weak_location_history_only": 0,
            "unknown_non_country_domain_location": 0,
            "mode": mode,
            "waves_run": 2 if mode == "multi_wave" else None,
            "queries_executed": 2 * len(query_plan.get("queries", [])) if mode == "multi_wave" else len(query_plan.get("queries", [])),
            "stop_reason": "low_incremental_gain" if mode == "multi_wave" else None,
            "new_unique_profiles_per_wave": [3, 0] if mode == "multi_wave" else [],
        },
        "agent_response": {
            "language": "en",
            "message": "Search completed: 3 unique candidates identified: 2 strong, 1 in review, and 0 weak candidates.",
        },
    }


class FakeExecution:
    def __init__(self) -> None:
        self.original_single = main.execute_single_wave_structured_search_response
        self.original_multi = main.execute_multi_wave_structured_search_response
        self.calls = 0

    async def single(self, request: Any, query_plan: dict[str, Any], execution_approval: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        return fake_search_response(query_plan, execution_approval, mode="single_wave")

    async def multi(
        self,
        request: Any,
        query_plan: dict[str, Any],
        settings: dict[str, Any],
        execution_approval: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls += 1
        return fake_search_response(query_plan, execution_approval, mode="multi_wave")

    def install(self) -> None:
        main.execute_single_wave_structured_search_response = self.single
        main.execute_multi_wave_structured_search_response = self.multi

    def restore(self) -> None:
        main.execute_single_wave_structured_search_response = self.original_single
        main.execute_multi_wave_structured_search_response = self.original_multi


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def has_cyrillic(value: str) -> bool:
    return any("\u0400" <= char <= "\u04ff" for char in value)


def normalized(value: str) -> str:
    return " ".join((value or "").lower().split())


COMMON_FORBIDDEN_VISIBLE_TERMS = [
    "queryplan",
    "backend planner",
    "fingerprint",
    "runtime",
    "tavily",
    "build plan",
    "frontend ready",
    "product safety boundaries",
    "agent runtime",
]

RU_FORBIDDEN_VISIBLE_TERMS = [
    "search summary",
    "initial search summary",
    "stack item",
    "java stack",
]

HARSH_HARMLESS_TERMS = [
    "this does not look like candidate search",
    "request refused",
    "product safety",
]


def assert_no_forbidden_terms(value: str, *, language: str, allow_approval: bool = False) -> None:
    text = normalized(value)
    forbidden = list(COMMON_FORBIDDEN_VISIBLE_TERMS)
    if not allow_approval:
        forbidden.append("approval")
    for term in forbidden:
        if term in text:
            raise AssertionError(f"visible internal term leaked: {term}")
    if language == "ru":
        for term in RU_FORBIDDEN_VISIBLE_TERMS:
            if term in text:
                raise AssertionError(f"mixed RU wording leaked: {term}")


def assert_polite_harmless(value: str) -> None:
    text = normalized(value)
    for term in HARSH_HARMLESS_TERMS:
        if term in text:
            raise AssertionError(f"harsh harmless-input wording: {term}")


def build_ready_cases() -> list[UiScenario]:
    role_variants = [
        ("Find backend developers in Ukraine with Java, {stack}.", "en"),
        ("Need Java backend engineers in Ukraine, {stack}.", "en"),
        ("Looking for Backend Developer profiles in Ukraine, Java, {stack}.", "en"),
        ("Search Java Software Engineer profiles in Ukraine with {stack}.", "en"),
        ("Найди backend разработчиков в Украине, Java, {stack}.", "ru"),
        ("Ищем Java backend инженеров в Украине, {stack}.", "ru"),
        ("Нужен Backend Developer Java Украина, {stack}.", "ru"),
        ("Java backend dev Ukraine, {stack}.", "en"),
    ]
    stack_sets = [
        ["Spring", "Kafka"],
        ["Spring Boot", "AWS"],
        ["Kafka", "Docker"],
        ["Hibernate", "PostgreSQL"],
        ["REST", "Microservices"],
        ["Kubernetes", "Docker"],
    ]
    cases: list[UiScenario] = []
    index = 1
    for stack in stack_sets:
        for template, language in role_variants:
            stack_text = " and ".join(stack) if language == "en" else " и ".join(stack)
            text = template.format(stack=stack_text)
            register_fixture(text, stack=stack)
            cases.append(
                UiScenario(
                    case_id=f"P8751-READY-{index:03d}",
                    category="positive_ready",
                    language=language,
                    steps=[UiStep(text, "ready")],
                    expected="ready",
                    expected_terms=["confirm" if language == "en" else "подтверди"],
                    expected_stack=stack,
                )
            )
            index += 1
    return cases


def build_missing_cases() -> list[UiScenario]:
    specs = [
        ("Need Java developers in Ukraine.", "en", {"role_family": "Backend Developer", "technology": "Java", "stack": [], "location": "Ukraine", "status": "needs_clarification"}, "stack"),
        ("Find backend with Spring and Kafka.", "en", {"role_family": "Backend Developer", "technology": "Java", "stack": ["Spring", "Kafka"], "location": None, "status": "needs_clarification"}, "location"),
        ("Java Ukraine Spring.", "en", {"role_family": None, "technology": "Java", "stack": ["Spring"], "location": "Ukraine", "status": "needs_clarification"}, "role"),
        ("Нужен Java разработчик в Украине.", "ru", {"role_family": "Backend Developer", "technology": "Java", "stack": [], "location": "Ukraine", "status": "needs_clarification"}, "стек"),
        ("Ищем backend Spring Kafka.", "ru", {"role_family": "Backend Developer", "technology": "Java", "stack": ["Spring", "Kafka"], "location": None, "status": "needs_clarification"}, "локац"),
        ("Java Украина Spring.", "ru", {"role_family": None, "technology": "Java", "stack": ["Spring"], "location": "Ukraine", "status": "needs_clarification"}, "роль"),
    ]
    cases: list[UiScenario] = []
    for repeat in range(3):
        for index, (text, language, fixture_kwargs, expected_term) in enumerate(specs, start=1):
            case_text = text if repeat == 0 else f"{text} #{repeat + 1}"
            register_fixture(case_text, **fixture_kwargs)
            cases.append(
                UiScenario(
                    case_id=f"P8751-MISSING-{repeat * len(specs) + index:03d}",
                    category="missing_clarification",
                    language=language,
                    steps=[UiStep(case_text, "clarification")],
                    expected="clarification",
                    expected_terms=[expected_term],
                )
            )
    return cases


def build_simple_cases() -> list[UiScenario]:
    small_talk = [
        ("hello", "en"),
        ("hi there", "en"),
        ("how are you?", "en"),
        ("thanks", "en"),
        ("are you there?", "en"),
        ("good morning", "en"),
        ("привет", "ru"),
        ("как дела?", "ru"),
        ("спасибо", "ru"),
        ("ты на связи?", "ru"),
        ("добрый день", "ru"),
        ("здравствуй", "ru"),
    ]
    noise = [
        ("xsdfszdzsz", "en"),
        ("qweqweqwe", "en"),
        ("....", "en"),
        ("долрлрлрлрл", "ru"),
        ("ываыва", "ru"),
        ("сантихника", "ru"),
        ("asdf 123 ???", "en"),
        ("блаблабла", "ru"),
    ]
    off_topic = [
        ("what is the weather?", "en"),
        ("what is the dollar rate?", "en"),
        ("tell me a joke", "en"),
        ("какая погода?", "ru"),
        ("какой курс доллара?", "ru"),
        ("расскажи анекдот", "ru"),
        ("can you order lunch?", "en"),
        ("можешь заказать обед?", "ru"),
    ]
    prohibited = [
        ("Open LinkedIn profiles and read them.", "en"),
        ("Log into LinkedIn and scrape candidates.", "en"),
        ("Message all candidates automatically.", "en"),
        ("Search Google directly outside backend.", "en"),
        ("Collect candidate emails and phones.", "en"),
        ("Зайди в LinkedIn и напиши кандидатам.", "ru"),
        ("Собери телефоны кандидатов.", "ru"),
        ("Автоматически отправь сообщения кандидатам.", "ru"),
        ("Обойди backend и поищи в Google напрямую.", "ru"),
        ("Войди в мой аккаунт LinkedIn.", "ru"),
    ]

    cases: list[UiScenario] = []
    for index, (text, language) in enumerate(small_talk, start=1):
        cases.append(UiScenario(f"P8751-SMALL-{index:03d}", "small_talk", language, [UiStep(text)], "small_talk"))
    for index, (text, language) in enumerate(noise, start=1):
        cases.append(UiScenario(f"P8751-NOISE-{index:03d}", "noise_unclear", language, [UiStep(text)], "noise"))
    for index, (text, language) in enumerate(off_topic, start=1):
        cases.append(UiScenario(f"P8751-OFFTOPIC-{index:03d}", "off_topic", language, [UiStep(text)], "off_topic"))
    for index, (text, language) in enumerate(prohibited, start=1):
        cases.append(UiScenario(f"P8751-SAFETY-{index:03d}", "prohibited", language, [UiStep(text)], "prohibited"))
    return cases


def build_multiturn_cases() -> list[UiScenario]:
    base_en = "Find backend developers in Ukraine with Java, Spring and Kafka."
    base_ru = "Найди backend разработчиков в Украине, Java, Spring и Kafka."
    register_fixture(base_en, stack=["Spring", "Kafka"])
    register_fixture(base_ru, stack=["Spring", "Kafka"])

    missing_stack_en = "Find Java backend developers in Ukraine."
    missing_stack_ru = "Нужен Java backend разработчик в Украине."
    register_fixture(
        missing_stack_en,
        role_family="Backend Developer",
        technology="Java",
        stack=[],
        location="Ukraine",
        status="needs_clarification",
    )
    register_fixture(
        missing_stack_ru,
        role_family="Backend Developer",
        technology="Java",
        stack=[],
        location="Ukraine",
        status="needs_clarification",
    )

    cases = [
        UiScenario("P8751-PENDING-001", "pending_answer", "en", [UiStep(missing_stack_en), UiStep("Spring", "ready")], "ready", expected_stack=["Spring"]),
        UiScenario("P8751-PENDING-002", "pending_answer", "en", [UiStep(missing_stack_en), UiStep("Kafka", "ready")], "ready", expected_stack=["Kafka"]),
        UiScenario("P8751-PENDING-003", "pending_answer", "ru", [UiStep(missing_stack_ru), UiStep("Спринг", "ready")], "ready", expected_stack=["Spring"]),
        UiScenario("P8751-PENDING-004", "pending_answer", "ru", [UiStep(missing_stack_ru), UiStep("кафка", "ready")], "ready", expected_stack=["Kafka"]),
        UiScenario("P8751-REFINE-001", "refinement", "en", [UiStep(base_en, "ready"), UiStep("add Docker", "ready")], "ready", expected_stack=["Spring", "Kafka", "Docker"]),
        UiScenario("P8751-REFINE-002", "refinement", "en", [UiStep(base_en, "ready"), UiStep("remove Kafka and add AWS", "ready")], "ready", expected_stack=["Spring", "AWS"]),
        UiScenario("P8751-REFINE-003", "refinement", "ru", [UiStep(base_ru, "ready"), UiStep("добавь Docker", "ready")], "ready", expected_stack=["Spring", "Kafka", "Docker"]),
        UiScenario("P8751-REFINE-004", "refinement", "ru", [UiStep(base_ru, "ready"), UiStep("убери Kafka и добавь AWS", "ready")], "ready", expected_stack=["Spring", "AWS"]),
        UiScenario("P8751-CONFIRM-001", "chat_confirmation", "en", [UiStep(base_en, "ready"), UiStep("yes please start", "results")], "results"),
        UiScenario("P8751-CONFIRM-002", "chat_confirmation", "en", [UiStep(base_en, "ready"), UiStep("go ahead", "results")], "results"),
        UiScenario("P8751-CONFIRM-003", "chat_confirmation", "ru", [UiStep(base_ru, "ready"), UiStep("да, запускай", "results")], "results"),
        UiScenario("P8751-CONFIRM-004", "chat_confirmation", "ru", [UiStep(base_ru, "ready"), UiStep("окей вперед", "results")], "results"),
    ]
    return cases


def build_scenarios() -> list[UiScenario]:
    return [
        *build_ready_cases(),
        *build_missing_cases(),
        *build_simple_cases(),
        *build_multiturn_cases(),
    ]


async def wait_for_server(port: int) -> None:
    deadline = asyncio.get_running_loop().time() + 15
    while True:
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            if asyncio.get_running_loop().time() > deadline:
                raise TimeoutError("Timed out waiting for UAT server")
            await asyncio.sleep(0.1)


async def chat_texts(page: Any) -> list[str]:
    return await page.locator("#chat-messages .chat-message p").all_text_contents()


async def last_assistant_message(page: Any) -> str:
    texts = await page.locator("#chat-messages .assistant-message p").all_text_contents()
    return texts[-1].strip() if texts else ""


async def visible_text(page: Any) -> str:
    return await page.locator("body").inner_text(timeout=5000)


async def reset_ui(page: Any) -> None:
    await page.locator("#reset-chat").click()
    await page.wait_for_function(
        "() => document.querySelector('#chat-input') && !document.querySelector('#chat-input').disabled",
        timeout=10000,
    )


async def send_message(page: Any, text: str, expect: str) -> None:
    before = len(await chat_texts(page))
    await page.locator("#chat-input").fill(text)
    await page.locator("#chat-input").press("Enter")
    if expect == "ready":
        await page.wait_for_function(
            """(before) => {
                if (document.querySelectorAll('#chat-messages .chat-message p').length <= before) {
                    return false;
                }
                const messages = [...document.querySelectorAll('#chat-messages .assistant-message p')].map((node) => node.innerText.toLowerCase());
                const status = (document.querySelector('#chat-status')?.innerText || '').toLowerCase();
                return status.includes('confirm in chat') ||
                    messages.slice(before).some((text) => text.includes('confirm') || text.includes('подтверди'));
            }""",
            arg=before,
            timeout=15000,
        )
    elif expect == "results":
        await page.wait_for_function(
            """() => {
                const report = (document.querySelector('#report-status')?.innerText || '').toLowerCase();
                const results = (document.querySelector('#results-status')?.innerText || '').toLowerCase();
                const messages = [...document.querySelectorAll('#chat-messages .assistant-message p')].map((node) => node.innerText.toLowerCase());
                return report.includes('unique') && results.includes('showing') &&
                    messages.some((text) => text.includes('search completed') || text.includes('поиск заверш'));
            }""",
            timeout=20000,
        )
    else:
        await page.wait_for_function(
            """(before) => document.querySelectorAll('#chat-messages .chat-message p').length > before""",
            arg=before,
            timeout=10000,
        )
        await page.wait_for_function(
            "() => !document.querySelector('#chat-input')?.disabled",
            timeout=10000,
        )


async def assert_ready(page: Any, scenario: UiScenario) -> None:
    reply = await last_assistant_message(page)
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    assert_no_forbidden_terms(reply, language=scenario.language)
    if scenario.language == "ru" and not has_cyrillic(reply):
        raise AssertionError("RU ready reply is not localized")
    lowered = normalized(reply)
    if "confirm" not in lowered and "подтверди" not in lowered:
        raise AssertionError(f"ready reply does not ask for confirmation: {reply}")
    brief_text = (await page.locator("#brief-summary-panel").text_content(timeout=5000)) or ""
    searchable_text = f"{reply}\n{brief_text}"
    for term in ["Backend Developer", "Java", "Ukraine", *scenario.expected_stack]:
        if term and term not in searchable_text:
            raise AssertionError(f"ready UI missing {term!r}")


async def assert_clarification(page: Any, scenario: UiScenario) -> None:
    reply = await last_assistant_message(page)
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    assert_no_forbidden_terms(reply, language=scenario.language)
    assert_polite_harmless(reply)
    if "?" not in reply:
        raise AssertionError(f"clarification reply should ask one question: {reply}")
    for term in scenario.expected_terms:
        if term.lower() not in reply.lower():
            raise AssertionError(f"clarification reply missing {term!r}: {reply}")


async def assert_small_talk(page: Any, scenario: UiScenario) -> None:
    reply = await last_assistant_message(page)
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    assert_no_forbidden_terms(reply, language=scenario.language)
    assert_polite_harmless(reply)
    lowered = normalized(reply)
    if scenario.language == "ru":
        if not has_cyrillic(reply) or not any(term in lowered for term in ["пом", "на связи", "ищем"]):
            raise AssertionError(f"RU small-talk reply is not helpful/polite: {reply}")
    elif not any(term in lowered for term in ["help", "ready", "tell me", "good to"]):
        raise AssertionError(f"EN small-talk reply is not helpful/polite: {reply}")


async def assert_noise(page: Any, scenario: UiScenario) -> None:
    reply = await last_assistant_message(page)
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    assert_no_forbidden_terms(reply, language=scenario.language)
    assert_polite_harmless(reply)
    lowered = normalized(reply)
    if scenario.language == "ru":
        if "не понял" not in lowered and "не распознал" not in lowered:
            raise AssertionError(f"RU unclear reply should say it did not understand: {reply}")
    elif "did not understand" not in lowered and "please tell me" not in lowered:
        raise AssertionError(f"EN unclear reply should say it did not understand: {reply}")


async def assert_off_topic(page: Any, scenario: UiScenario) -> None:
    reply = await last_assistant_message(page)
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    assert_no_forbidden_terms(reply, language=scenario.language)
    assert_polite_harmless(reply)
    lowered = normalized(reply)
    if scenario.language == "ru":
        if not has_cyrillic(reply) or "поиск" not in lowered:
            raise AssertionError(f"RU off-topic reply should redirect to candidate search: {reply}")
    elif "candidate search" not in lowered and "sourcing" not in lowered:
        raise AssertionError(f"EN off-topic reply should redirect to candidate search: {reply}")


async def assert_prohibited(page: Any, scenario: UiScenario) -> None:
    reply = await last_assistant_message(page)
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    assert_no_forbidden_terms(reply, language=scenario.language)
    lowered = normalized(reply)
    if scenario.language == "ru":
        if "не могу" not in lowered:
            raise AssertionError(f"RU prohibited reply should refuse safely: {reply}")
    elif "can't" not in lowered and "cannot" not in lowered:
        raise AssertionError(f"EN prohibited reply should refuse safely: {reply}")
    if await page.locator("#approve-search").is_enabled():
        raise AssertionError("prohibited request left executable run control enabled")


async def assert_results(page: Any, scenario: UiScenario) -> None:
    text = await visible_text(page)
    assert_no_forbidden_terms(text, language="en")
    report = await page.locator("#report-status").inner_text(timeout=5000)
    results = await page.locator("#results-status").inner_text(timeout=5000)
    reply = await last_assistant_message(page)
    if "3 unique" not in report:
        raise AssertionError(f"report summary missing unique count: {report}")
    if "Showing" not in results:
        raise AssertionError(f"candidate table is not primary/visible: {results}")
    lowered = normalized(reply)
    if "search completed" not in lowered and "поиск заверш" not in lowered:
        raise AssertionError(f"post-search reply is not compact completion: {reply}")
    if "next iteration" in lowered or "suggest" in lowered:
        raise AssertionError(f"post-search reply is too verbose: {reply}")


async def assert_scenario(page: Any, scenario: UiScenario) -> None:
    if scenario.expected == "ready":
        await assert_ready(page, scenario)
    elif scenario.expected == "clarification":
        await assert_clarification(page, scenario)
    elif scenario.expected == "small_talk":
        await assert_small_talk(page, scenario)
    elif scenario.expected == "noise":
        await assert_noise(page, scenario)
    elif scenario.expected == "off_topic":
        await assert_off_topic(page, scenario)
    elif scenario.expected == "prohibited":
        await assert_prohibited(page, scenario)
    elif scenario.expected == "results":
        await assert_results(page, scenario)
    else:
        raise AssertionError(f"Unknown expected scenario type: {scenario.expected}")


async def run_ui_scenario(page: Any, scenario: UiScenario) -> None:
    await reset_ui(page)
    helper = await last_assistant_message(page)
    if "Feel free to start the chat" not in helper:
        raise AssertionError(f"initial helper is not warm/current: {helper}")
    for step in scenario.steps:
        await send_message(page, step.text, step.expect)
    await assert_scenario(page, scenario)


async def run_browser_cases(base_url: str, scenarios: list[UiScenario], headed: bool) -> list[CaseResult]:
    from playwright.async_api import async_playwright

    results: list[CaseResult] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headed)
        page = await browser.new_page(viewport={"width": 1366, "height": 900})
        await page.goto(base_url, wait_until="networkidle")
        for scenario in scenarios:
            try:
                await run_ui_scenario(page, scenario)
                results.append(CaseResult(scenario.case_id, scenario.category, "pass"))
            except Exception as exc:
                results.append(CaseResult(scenario.case_id, scenario.category, "fail", str(exc)))
        await browser.close()
    return results


def write_report(results: list[CaseResult], output_path: Path) -> None:
    total = len(results)
    failures = [result for result in results if result.status != "pass"]
    categories = Counter(result.category for result in results)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    category_rows = "\n".join(f"| {category} | {count} |" for category, count in sorted(categories.items()))
    failure_text = "None." if not failures else "\n".join(
        f"- `{failure.case_id}` ({failure.category}): {failure.detail}" for failure in failures[:40]
    )
    status = "green" if not failures else "red"
    output_path.write_text(
        f"""# Phase 8.75.1 Conversation UX UAT Report

Generated: {now}

Status: `{status}`

| Metric | Count |
| --- | ---: |
| UI scenarios | {total} |
| passed | {total - len(failures)} |
| failed | {len(failures)} |

## Category Coverage

| Category | Scenarios |
| --- | ---: |
{category_rows}

## Failures

{failure_text}

## Fixes Applied During Gate

- Softened harmless off-topic replies so the assistant redirects to candidate search without a harsh rejection.
- Added conservative off-topic coverage for joke/lunch/Russian lunch requests.
- Added conservative unclear-input handling for single unsupported/noisy words before Search Brief extraction.
- Kept prohibited requests non-executable by clearing stale executable state and checking disabled run controls.
- Localized Russian safety, stack, ambiguity, and refinement wording to avoid visible internal English terms.
- Extended chat confirmation detection for natural English/Russian approval phrases while preserving state-bound runtime execution.
- Updated UI progress copy to avoid exposing Tavily/query-plan implementation terms.
- Hardened the UI UAT runner to wait for the current Agent Plan/summary state after refinements.

## Analysis

This UAT drives the real frontend chat UI with simulated recruiter messages. It covers positive ready searches, missing-field clarification, small talk, unclear/noisy input, off-topic input, prohibited requests, refinement, confirmation, and post-search visible results. The test server uses the current FastAPI app and frontend while replacing OpenAI/Tavily execution with deterministic local doubles.

Decision: {'Phase 8.75.1 is green; Phase 9 can proceed through reviewed persistence/privacy/session-boundary tasks.' if not failures else 'Phase 8.75.1 is not green yet; fix the failed UX cases and rerun.'}
""",
        encoding="utf-8",
    )


async def run_all(write_report_path: Path | None, headed: bool) -> dict[str, Any]:
    scenarios = build_scenarios()
    if len(scenarios) < 100:
        raise AssertionError(f"Expected at least 100 UI scenarios, got {len(scenarios)}")

    original_chat_llm = main.run_openai_json_recruiter_chat
    original_wording_llm = main.run_openai_json_agent_wording
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY"),
    }
    fake_execution = FakeExecution()
    port = find_free_port()
    config = uvicorn.Config(main.app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server_task: asyncio.Task | None = None

    try:
        main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm
        main.run_openai_json_agent_wording = fake_wording_llm
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_MODEL", None)
        os.environ["TAVILY_API_KEY"] = "fake-ui-uat-tavily-key"
        fake_execution.install()

        server_task = asyncio.create_task(server.serve())
        await wait_for_server(port)
        results = await run_browser_cases(f"http://127.0.0.1:{port}", scenarios, headed)
    finally:
        server.should_exit = True
        if server_task:
            await server_task
        fake_execution.restore()
        main.run_openai_json_recruiter_chat = original_chat_llm
        main.run_openai_json_agent_wording = original_wording_llm
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    if write_report_path:
        write_report(results, write_report_path)

    failures = [result for result in results if result.status != "pass"]
    summary = {
        "status": "green" if not failures else "red",
        "total": len(results),
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "categories": dict(sorted(Counter(result.category for result in results).items())),
        "failed_cases": [failure.__dict__ for failure in failures],
    }
    if failures:
        raise AssertionError(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 8.75.1 UI conversation UX UAT.")
    parser.add_argument("--write-report", type=Path, default=None)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main_entry() -> None:
    args = parse_args()
    summary = asyncio.run(run_all(args.write_report, args.headed))
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Phase 8.75.1 UI conversation UX UAT passed: {summary['passed']}/{summary['total']} scenarios")


if __name__ == "__main__":
    main_entry()
