import asyncio
import os
from pathlib import Path
import sys
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main, search_brief_extractor as extractor


class SemanticCaseError(AssertionError):
    pass


EXTRACTOR_CALLS: list[str] = []


def chat_request(message: str) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        messages=[main.RecruiterChatMessage(role="user", content=message)],
        language="en",
    )


def raw_extractor_output(
    *,
    text: str,
    role_family: str | None,
    technology: str | None,
    stack: list[str] | None,
    location: str | None,
    domain_experience: list[str] | None = None,
    role_ambiguous: bool = False,
    role_options: list[str] | None = None,
    confidence: str = "high",
) -> dict[str, Any]:
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": text,
            "role_family": role_family,
            "role_ambiguity": {
                "is_ambiguous": role_ambiguous,
                "label": role_family if role_ambiguous else None,
                "options": role_options or [],
                "clarification_question": (
                    f"Which {role_family} role should the search target?"
                    if role_ambiguous and role_family
                    else None
                ),
            },
            "technology": technology,
            "stack": stack or [],
            "location": location,
            "seniority": None,
            "must_have": [],
            "nice_to_have": [],
            "domain_experience": domain_experience or [],
            "exclusions": [],
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "notes": None,
        },
        "confidence": confidence,
        "reason_codes": ["semantic_uat_fixture"],
    }


SEMANTIC_CASES = [
    {
        "case_id": "P99-UAT-001",
        "text": "I need QA Automation in Spain with Java and Selenium.",
        "raw": raw_extractor_output(
            text="I need QA Automation in Spain with Java and Selenium.",
            role_family="QA Automation",
            technology="Java",
            stack=["Selenium"],
            location="Spain",
        ),
        "expected": {
            "state": "ready_for_planning",
            "role_family": "QA Automation",
            "technology": "Java",
            "stack": ["Selenium"],
            "location": "Spain",
        },
    },
    {
        "case_id": "P99-UAT-002",
        "text": "I need Analyst in Canada with banking domain experience and SQL skills.",
        "raw": raw_extractor_output(
            text="I need Analyst in Canada with banking domain experience and SQL skills.",
            role_family="Analyst",
            technology="SQL",
            stack=["SQL"],
            location="Canada",
            domain_experience=["banking domain experience"],
            role_ambiguous=True,
            role_options=["Data Analyst", "Business Analyst", "Systems Analyst"],
        ),
        "expected": {
            "state": "needs_clarification",
            "role_family": "Analyst",
            "technology": "SQL",
            "stack": ["SQL"],
            "location": "Canada",
            "must_have_contains": "banking domain experience",
            "next_question_contains": "role",
        },
    },
    {
        "case_id": "P99-UAT-003",
        "text": "Find Data Analyst in Germany with SQL and Power BI.",
        "raw": raw_extractor_output(
            text="Find Data Analyst in Germany with SQL and Power BI.",
            role_family="Data Analyst",
            technology="SQL",
            stack=["Power BI"],
            location="Germany",
        ),
        "expected": {
            "state": "ready_for_planning",
            "role_family": "Data Analyst",
            "technology": "SQL",
            "stack": ["Power BI"],
            "location": "Germany",
        },
    },
    {
        "case_id": "P99-UAT-004",
        "text": "Find DevOps Engineer in Canada with AWS and Terraform.",
        "raw": raw_extractor_output(
            text="Find DevOps Engineer in Canada with AWS and Terraform.",
            role_family="DevOps Engineer",
            technology="AWS",
            stack=["Terraform"],
            location="Canada",
        ),
        "expected": {
            "state": "ready_for_planning",
            "role_family": "DevOps Engineer",
            "technology": "AWS",
            "stack": ["Terraform"],
            "location": "Canada",
        },
    },
    {
        "case_id": "P99-UAT-005",
        "text": "Find Product Manager in Poland with fintech domain and AI experience.",
        "raw": raw_extractor_output(
            text="Find Product Manager in Poland with fintech domain and AI experience.",
            role_family="Product Manager",
            technology="AI",
            stack=["AI"],
            location="Poland",
            domain_experience=["fintech domain"],
        ),
        "expected": {
            "state": "ready_for_planning",
            "role_family": "Product Manager",
            "technology": "AI",
            "stack": ["AI"],
            "location": "Poland",
            "must_have_contains": "fintech domain",
        },
    },
    {
        "case_id": "P99-UAT-006",
        "text": "Find Business Analyst in UK with Salesforce and banking experience.",
        "raw": raw_extractor_output(
            text="Find Business Analyst in UK with Salesforce and banking experience.",
            role_family="Business Analyst",
            technology="Salesforce",
            stack=["Salesforce"],
            location="UK",
            domain_experience=["banking experience"],
        ),
        "expected": {
            "state": "ready_for_planning",
            "role_family": "Business Analyst",
            "technology": "Salesforce",
            "stack": ["Salesforce"],
            "location": "UK",
            "must_have_contains": "banking experience",
        },
    },
    {
        "case_id": "P99-UAT-007",
        "text": "Find Cybersecurity Analyst remote with SIEM and SOC.",
        "raw": raw_extractor_output(
            text="Find Cybersecurity Analyst remote with SIEM and SOC.",
            role_family="Cybersecurity Analyst",
            technology="SIEM",
            stack=["SOC"],
            location="Remote",
        ),
        "expected": {
            "state": "ready_for_planning",
            "role_family": "Cybersecurity Analyst",
            "technology": "SIEM",
            "stack": ["SOC"],
            "location": "Remote",
        },
    },
    {
        "case_id": "P99-UAT-008",
        "text": "Analyst",
        "raw": raw_extractor_output(
            text="Analyst",
            role_family="Analyst",
            technology=None,
            stack=[],
            location=None,
            role_ambiguous=True,
            role_options=["Data Analyst", "Business Analyst", "Systems Analyst"],
        ),
        "expected": {
            "state": "needs_clarification",
            "role_family": "Analyst",
            "technology": None,
            "stack": [],
            "location": None,
            "next_question_contains": "role",
        },
    },
]


NEGATIVE_CASES = [
    {
        "case_id": "P99-UAT-009",
        "text": "What is the weather?",
        "extractor_should_run": False,
        "expected_state": "needs_clarification",
        "expected_normalized_brief": None,
    },
    {
        "case_id": "P99-UAT-010",
        "text": "\u041d\u0430\u0439\u0434\u0438 QA Automation \u0432 Spain with Java.",
        "extractor_should_run": False,
        "expected_state": "needs_clarification",
        "expected_normalized_brief": None,
    },
    {
        "case_id": "P99-UAT-011",
        "text": "I need Analyst in Canada with banking domain experience.",
        "extractor_should_run": True,
        "raw": raw_extractor_output(
            text="I need Analyst in Canada with banking domain experience.",
            role_family="Analyst",
            technology="Banking domain",
            stack=[],
            location="Canada",
            domain_experience=[],
        ),
        "expected_state": "needs_clarification",
        "expected_error_field": "technology",
    },
]


def assert_equal(actual: Any, expected: Any, case_id: str, field: str) -> None:
    if actual != expected:
        raise SemanticCaseError(
            f"{case_id}: expected {field}={expected!r}, got {actual!r}"
        )


async def forbidden_legacy_chat(*args: Any, **kwargs: Any):
    raise SemanticCaseError("Legacy recruiter-chat parser must not run in Phase 9.9 semantic UAT.")


async def no_live_wording(*args: Any, **kwargs: Any):
    return None, "semantic_uat_wording_disabled"


async def run_semantic_case(case: dict[str, Any]) -> None:
    async def fake_extractor(**kwargs: Any):
        EXTRACTOR_CALLS.append(kwargs["latest_message"])
        return case["raw"], None

    main.run_openai_json_search_brief_extractor = fake_extractor
    response = await main.recruiter_chat_turn_response(chat_request(case["text"]))
    expected = case["expected"]
    normalized_brief = response["normalized_brief"]

    assert_equal(response["state"], expected["state"], case["case_id"], "state")
    if not isinstance(normalized_brief, dict):
        raise SemanticCaseError(f"{case['case_id']}: expected normalized brief.")
    for field in ("role_family", "technology", "stack", "location"):
        assert_equal(
            normalized_brief.get(field),
            expected[field],
            case["case_id"],
            field,
        )
    if expected.get("must_have_contains"):
        if expected["must_have_contains"] not in (normalized_brief.get("must_have") or []):
            raise SemanticCaseError(
                f"{case['case_id']}: expected domain in must_have."
            )
    if expected.get("next_question_contains"):
        next_question = (response.get("next_question") or "").lower()
        if expected["next_question_contains"] not in next_question:
            raise SemanticCaseError(
                f"{case['case_id']}: expected targeted next question, got {next_question!r}."
            )


async def run_negative_case(case: dict[str, Any]) -> None:
    before_calls = len(EXTRACTOR_CALLS)

    async def fake_extractor(**kwargs: Any):
        EXTRACTOR_CALLS.append(kwargs["latest_message"])
        if "raw" not in case:
            raise SemanticCaseError(f"{case['case_id']}: extractor should not run.")
        return case["raw"], None

    main.run_openai_json_search_brief_extractor = fake_extractor
    response = await main.recruiter_chat_turn_response(chat_request(case["text"]))
    assert_equal(
        response["state"],
        case["expected_state"],
        case["case_id"],
        "state",
    )
    if case.get("extractor_should_run"):
        assert_equal(len(EXTRACTOR_CALLS), before_calls + 1, case["case_id"], "extractor_calls")
    else:
        assert_equal(len(EXTRACTOR_CALLS), before_calls, case["case_id"], "extractor_calls")
    if "expected_normalized_brief" in case:
        assert_equal(
            response["normalized_brief"],
            case["expected_normalized_brief"],
            case["case_id"],
            "normalized_brief",
        )
    if case.get("expected_error_field"):
        if not any(
            error.get("field") == case["expected_error_field"]
            for error in response.get("validation_errors") or []
        ):
            raise SemanticCaseError(
                f"{case['case_id']}: expected validation error field {case['expected_error_field']!r}."
            )


async def run_uat() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_extractor = main.run_openai_json_search_brief_extractor
    original_legacy_chat = main.run_openai_json_recruiter_chat
    original_wording = main.run_openai_json_agent_wording
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    main.run_openai_json_recruiter_chat = forbidden_legacy_chat
    main.run_openai_json_agent_wording = no_live_wording
    try:
        for case in SEMANTIC_CASES:
            await run_semantic_case(case)
        for case in NEGATIVE_CASES:
            await run_negative_case(case)
    finally:
        main.run_openai_json_search_brief_extractor = original_extractor
        main.run_openai_json_recruiter_chat = original_legacy_chat
        main.run_openai_json_agent_wording = original_wording
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    total = len(SEMANTIC_CASES) + len(NEGATIVE_CASES)
    print(f"Phase 9.9 semantic Search Brief UAT passed: {total}/{total} cases")


if __name__ == "__main__":
    asyncio.run(run_uat())
