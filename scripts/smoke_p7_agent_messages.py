import asyncio
import inspect
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import agent_messages, main


def ready_brief(
    *,
    stack: list[str] | None = None,
    language: str = "en",
    search_depth: str = "standard",
) -> main.SearchBrief:
    source_text = "Find Backend Developer Java in Ukraine with Spring and Kafka."
    if language == "ru":
        source_text = "Ищем Backend Developer Java в Украине, Spring и Kafka."

    return main.SearchBrief(
        source_text=source_text,
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=["Spring", "Kafka"] if stack is None else stack,
        location="Ukraine",
        seniority=None,
        must_have=["Java"],
        nice_to_have=["Spring", "Kafka"],
        exclusions=[],
        search_depth=search_depth,
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


def sample_summary_facts() -> dict:
    return {
        "mode": "single_wave",
        "candidate_count": 3,
        "raw_total": 10,
        "displayed": 3,
        "queries_succeeded": 9,
        "queries_total": 10,
        "quality_distribution": {"strong": 1, "review": 1, "weak": 1},
        "strong_signal_counts": {
            "target_or_close_role": 2,
            "exact_technology": 3,
            "selected_stack_visible": 1,
            "selected_stack_not_visible": 2,
            "seniority_not_visible": 1,
            "role_missing": 0,
            "technology_missing": 0,
            "target_location": 3,
            "weak_location": 0,
            "unknown_location": 0,
        },
        "top_review_flags": [],
        "input_snapshot": {
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring", "Kafka"],
            "location": "Ukraine",
            "search_depth": "standard",
        },
    }


def assert_coverage_matrix() -> None:
    required_fields = {
        "helper",
        "message_type",
        "surface",
        "source_owner",
        "source_object",
        "public_response_field",
    }
    assert agent_messages.AGENT_MESSAGE_COVERAGE
    for key, entry in agent_messages.AGENT_MESSAGE_COVERAGE.items():
        assert required_fields.issubset(entry.keys()), key
        assert entry["helper"] == key, key
        assert hasattr(agent_messages, entry["helper"]), key
        for field in required_fields:
            assert entry[field], f"{key}.{field}"


def assert_helper_module_boundary() -> None:
    source = inspect.getsource(agent_messages)
    forbidden_imports = [
        "from app.main",
        "import app.main",
        "from app.routes",
        "import app.routes",
        "from app.agent_wording",
        "import app.agent_wording",
        "from app.search_execution",
        "import app.search_execution",
        "from app.agent_plan",
        "import app.agent_plan",
        "from app.agent_response",
        "import app.agent_response",
    ]
    for forbidden in forbidden_imports:
        assert forbidden not in source


def assert_language_and_chat_messages() -> None:
    assert agent_messages.agent_message_language("ru", None) == "ru"
    assert agent_messages.agent_message_language("en", None) == "en"
    assert (
        agent_messages.agent_message_language(
            None,
            {"source_text": "Ищем Java Backend Developer в Украине"},
        )
        == "ru"
    )

    assert main.recruiter_chat_onboarding_message(
        "en"
    ) == agent_messages.recruiter_chat_onboarding_source_message("en")
    assert main.recruiter_chat_onboarding_message(
        "ru"
    ) == agent_messages.recruiter_chat_onboarding_source_message("ru")
    assert main.localized_clarifying_question_for_missing_field(
        "stack",
        "en",
    ) == agent_messages.localized_clarifying_question_source_message("stack", "en")
    assert main.localized_clarifying_question_for_missing_field(
        "stack",
        "ru",
    ) == agent_messages.localized_clarifying_question_source_message("stack", "ru")
    assert main.ready_for_planning_message(
        "en"
    ) == agent_messages.ready_for_planning_source_message("en")
    assert main.ready_for_planning_message(
        "ru"
    ) == agent_messages.ready_for_planning_source_message("ru")

    refusal = main.recruiter_chat_refusal_message("en")
    assert "I cannot perform LinkedIn login" in refusal
    assert "approved backend pipeline" in refusal


def assert_agent_plan_and_query_messages() -> None:
    normalized_request = {
        "role_family": "Backend Developer",
        "technology": "Java",
        "location": "Ukraine",
        "stack": ["Spring", "Kafka"],
    }
    assert main.agent_plan_supported_message(
        "en",
        normalized_request,
    ) == agent_messages.agent_plan_supported_source_message("en", normalized_request)
    assert main.agent_plan_supported_message(
        "ru",
        normalized_request,
    ) == agent_messages.agent_plan_supported_source_message("ru", normalized_request)

    assert (
        agent_messages.query_plan_ready_approval_notice()
        == "Search plan is ready. Review the queries before running search."
    )
    assert (
        agent_messages.query_plan_preview_approval_notice()
        == "This plan is not executed yet. Search execution requires approval."
    )
    assert (
        agent_messages.runtime_tool_unavailable_source_message()
        == "TAVILY_API_KEY is not configured."
    )


def assert_agent_response_messages() -> None:
    summary_facts = sample_summary_facts()
    assert main.agent_response_message_en(
        summary_facts
    ) == agent_messages.agent_response_summary_source_message("en", summary_facts)
    assert main.agent_response_message_ru(
        summary_facts
    ) == agent_messages.agent_response_summary_source_message("ru", summary_facts)
    assert main.agent_response_limitations(
        "en",
        summary_facts,
    ) == agent_messages.agent_response_limitations_source_messages("en", summary_facts)
    assert main.agent_response_suggested_next_actions(
        "ru",
        summary_facts,
    ) == agent_messages.agent_response_suggested_next_actions_source_messages(
        "ru",
        summary_facts,
    )

    query_plan = {
        "queries": [],
        "input_snapshot": summary_facts["input_snapshot"],
    }
    agent_response = main.build_agent_response(
        query_plan,
        {
            "mode": "single_wave",
            "unique_profiles": 0,
            "raw_total": 0,
            "displayed": 0,
            "queries_succeeded": 0,
            "queries_total": 0,
        },
        [],
        "en",
    )
    options = agent_response["next_iteration_options"]
    assert options
    assert all(option["is_executable_now"] is False for option in options)
    assert all(option["requires_approval_before_execution"] is True for option in options)


def assert_no_unsafe_positive_claims() -> None:
    texts = [
        main.recruiter_chat_onboarding_message("en"),
        main.ready_for_planning_message("en"),
        main.agent_plan_supported_message(
            "en",
            {"stack": ["Spring"], "location": "Ukraine"},
        ),
        agent_messages.query_plan_ready_approval_notice(),
        agent_messages.query_plan_preview_approval_notice(),
        agent_messages.runtime_execution_failed_source_message(),
        main.agent_response_message_en(sample_summary_facts()),
    ]
    unsafe_positive_phrases = [
        "I will log in to LinkedIn",
        "I will scrape LinkedIn",
        "I will message candidates",
        "I will use your account",
        "Search will run without approval",
        "guaranteed candidates",
        "perfect candidates",
    ]
    for text in texts:
        for phrase in unsafe_positive_phrases:
            assert phrase not in text


async def assert_backend_response_fields() -> None:
    supported = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    assert supported["agent_plan"]["message"] == supported["message"]
    assert supported["agent_plan_status"] == "supported"
    assert supported["agent_plan"]["proposed_action"]["requires_approval"] is False

    missing_stack = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(stack=[]), language="en")
    )
    assert missing_stack["agent_plan_status"] == "needs_clarification"
    assert missing_stack["agent_plan"] is None

    unsupported = main.build_agent_plan_response(
        main.AgentPlanRequest(
            search_brief=ready_brief(search_depth="deep"),
            language="en",
        )
    )
    assert unsupported["agent_plan_status"] == "unsupported"
    assert unsupported["agent_plan"] is None

    executable_plan = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
            agent_plan_brief_fingerprint=supported["agent_plan"]["brief_fingerprint"],
            agent_plan_action=supported["agent_plan"]["proposed_action"],
        )
    )
    assert executable_plan["approval_notice"] == agent_messages.query_plan_ready_approval_notice()
    assert executable_plan["execution_approval_required"] is True


async def run_smoke() -> None:
    assert_coverage_matrix()
    assert_helper_module_boundary()
    assert_language_and_chat_messages()
    assert_agent_plan_and_query_messages()
    assert_agent_response_messages()
    assert_no_unsafe_positive_claims()
    await assert_backend_response_fields()


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P7 Agent Messages smoke passed")
