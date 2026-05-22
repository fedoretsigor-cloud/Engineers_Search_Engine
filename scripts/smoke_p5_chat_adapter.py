import asyncio
import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


LLM_CALLS: list[str] = []


def chat_request(
    text: str,
    language: str | None = None,
    draft_brief: main.SearchBrief | None = None,
) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language=language,
        draft_brief=draft_brief,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


def ready_java_ukraine_brief(stack: list[str] | None = None) -> main.SearchBrief:
    selected_stack = stack or ["Spring", "Kafka"]
    return main.SearchBrief(
        source_text="Find backend developers in Ukraine with Java stack.",
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=selected_stack,
        location="Ukraine",
        seniority=None,
        must_have=["Java"],
        nice_to_have=selected_stack,
        exclusions=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        assumptions=[],
    )


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
    LLM_CALLS.append(request.messages[-1].content)
    text = " ".join(message.content.lower() for message in request.messages)

    if "find backend" in text:
        return {
            "draft_brief": {
                "source_text": request.messages[-1].content,
                "brief_status": "ready_for_planning",
                "role_family": "Backend Developer",
                "technology": "Java",
                "stack": ["Spring", "Kafka"],
                "location": "Ukraine",
                "seniority": None,
                "must_have": ["Java"],
                "nice_to_have": ["Spring", "Kafka"],
                "exclusions": [],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "assumptions": [],
            }
        }, []

    if "backend" in text:
        return {
            "draft_brief": {
                "source_text": request.messages[-1].content,
                "brief_status": "ready_for_planning",
                "role_family": "Backend Developer",
                "technology": "Java",
                "stack": ["Spring", "Kafka"],
                "location": "Ukraine",
                "must_have": ["Java"],
                "nice_to_have": ["Spring", "Kafka"],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "assumptions": [],
            }
        }, []

    return {
        "draft_brief": {
            "source_text": request.messages[-1].content,
            "brief_status": "needs_clarification",
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": [],
            "location": None,
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "assumptions": [],
        }
    }, []


async def run_smoke() -> None:
    original_env = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "OPENAI_MODEL": os.environ.get("OPENAI_MODEL"),
    }
    original_llm = main.run_openai_json_recruiter_chat
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)

    try:
        assert any(
            route.path == "/api/recruiter-chat/turn"
            for route in main.app.routes
        )
        assert main.normalize_location_value("Украина") == "Ukraine"

        before_greeting = len(LLM_CALLS)
        ru_greeting = await main.recruiter_chat_turn_response(
            chat_request("привет", language="ru")
        )
        assert len(LLM_CALLS) == before_greeting
        assert ru_greeting["ok"] is True
        assert ru_greeting["state"] == "needs_clarification"
        assert ru_greeting["normalized_brief"] is None
        assert ru_greeting["can_build_plan"] is False
        assert "роль" in ru_greeting["assistant_message"].lower()

        en_greeting = await main.recruiter_chat_turn_response(
            chat_request("hello", language="en")
        )
        assert len(LLM_CALLS) == before_greeting
        assert en_greeting["ok"] is True
        assert en_greeting["state"] == "needs_clarification"
        assert en_greeting["normalized_brief"] is None
        assert en_greeting["can_build_plan"] is False
        assert "role" in en_greeting["assistant_message"].lower()

        near_empty = await main.recruiter_chat_turn_response(
            chat_request("...", language="en")
        )
        assert len(LLM_CALLS) == before_greeting
        assert near_empty["ok"] is True
        assert near_empty["state"] == "needs_clarification"
        assert near_empty["normalized_brief"] is None
        assert near_empty["can_build_plan"] is False

        draft_preserved = await main.recruiter_chat_turn_response(
            chat_request(
                "hello",
                language="en",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert len(LLM_CALLS) == before_greeting
        assert draft_preserved["state"] == "ready_for_planning"
        assert draft_preserved["normalized_brief"]["role_family"] == "Backend Developer"
        assert draft_preserved["normalized_brief"]["technology"] == "Java"
        assert draft_preserved["normalized_brief"]["stack"] == ["Spring", "Kafka"]
        assert draft_preserved["normalized_brief"]["location"] == "Ukraine"
        assert draft_preserved["can_build_plan"] is True

        before_refinement = len(LLM_CALLS)
        add_stack = await main.recruiter_chat_turn_response(
            chat_request(
                "добавь Docker",
                language="ru",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert len(LLM_CALLS) == before_refinement
        assert add_stack["state"] == "ready_for_planning"
        assert add_stack["normalized_brief"]["stack"] == ["Spring", "Kafka", "Docker"]
        assert add_stack["brief_changed"] is True
        assert add_stack["stale_state_should_clear"] is True
        assert add_stack["brief_patch"]["operations"][0]["operation"] == "add_stack"

        remove_and_add = await main.recruiter_chat_turn_response(
            chat_request(
                "remove Kafka and add Docker",
                language="en",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert len(LLM_CALLS) == before_refinement
        assert remove_and_add["normalized_brief"]["stack"] == ["Spring", "Docker"]
        assert remove_and_add["brief_changed"] is True
        assert remove_and_add["stale_state_should_clear"] is True
        assert [
            operation["operation"]
            for operation in remove_and_add["brief_patch"]["operations"]
        ] == ["remove_stack", "add_stack"]

        replace_stack = await main.recruiter_chat_turn_response(
            chat_request(
                "only Spring",
                language="en",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert replace_stack["normalized_brief"]["stack"] == ["Spring"]
        assert replace_stack["brief_changed"] is True
        assert replace_stack["stale_state_should_clear"] is True

        set_seniority = await main.recruiter_chat_turn_response(
            chat_request(
                "senior",
                language="en",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert set_seniority["normalized_brief"]["seniority"] == "Senior"
        assert set_seniority["brief_changed"] is True
        assert set_seniority["stale_state_should_clear"] is True

        deep_search = await main.recruiter_chat_turn_response(
            chat_request(
                "deep search",
                language="en",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert deep_search["normalized_brief"]["search_depth"] == "deep"
        assert deep_search["brief_changed"] is True
        assert deep_search["stale_state_should_clear"] is True

        unsupported_patch = await main.recruiter_chat_turn_response(
            chat_request(
                "remove Kafka and add React",
                language="en",
                draft_brief=ready_java_ukraine_brief(),
            )
        )
        assert unsupported_patch["normalized_brief"]["stack"] == ["Spring", "Kafka"]
        assert unsupported_patch["brief_changed"] is False
        assert unsupported_patch["stale_state_should_clear"] is False
        assert any(
            operation["operation"] == "unsupported"
            for operation in unsupported_patch["brief_patch"]["operations"]
        )

        before_clean_initial = len(LLM_CALLS)
        clean_initial_without_draft = await main.recruiter_chat_turn_response(
            chat_request("add Docker", language="en")
        )
        assert len(LLM_CALLS) == before_clean_initial + 1
        assert clean_initial_without_draft["state"] == "needs_clarification"
        assert clean_initial_without_draft["normalized_brief"]["role_family"] == "Backend Developer"
        assert clean_initial_without_draft["normalized_brief"]["technology"] == "Java"
        assert clean_initial_without_draft["normalized_brief"]["location"] is None
        assert clean_initial_without_draft["brief_patch"] is None

        duplicate_add = await main.recruiter_chat_turn_response(
            chat_request(
                "add Spring",
                language="en",
                draft_brief=ready_java_ukraine_brief(["Spring"]),
            )
        )
        assert duplicate_add["normalized_brief"]["stack"] == ["Spring"]
        assert duplicate_add["brief_changed"] is False
        assert duplicate_add["stale_state_should_clear"] is False

        missing_remove = await main.recruiter_chat_turn_response(
            chat_request(
                "remove Kafka",
                language="en",
                draft_brief=ready_java_ukraine_brief(["Spring"]),
            )
        )
        assert missing_remove["normalized_brief"]["stack"] == ["Spring"]
        assert missing_remove["brief_changed"] is False
        assert missing_remove["stale_state_should_clear"] is False

        last_stack_remove = await main.recruiter_chat_turn_response(
            chat_request(
                "remove Spring",
                language="en",
                draft_brief=ready_java_ukraine_brief(["Spring"]),
            )
        )
        assert last_stack_remove["normalized_brief"]["stack"] == ["Spring"]
        assert last_stack_remove["brief_changed"] is False
        assert last_stack_remove["stale_state_should_clear"] is False
        assert last_stack_remove["brief_patch"]["requires_clarification"] is True

        before_complete = len(LLM_CALLS)
        ru_complete = await main.recruiter_chat_turn_response(
            chat_request(
                "Найди backend разработчиков в Украине, основной стек Java, "
                "желательно Spring и Kafka.",
                language="ru",
            )
        )
        assert len(LLM_CALLS) == before_complete + 1
        assert ru_complete["ok"] is True
        assert ru_complete["state"] == "ready_for_planning"
        assert ru_complete["normalized_brief"]["role_family"] == "Backend Developer"
        assert ru_complete["normalized_brief"]["technology"] == "Java"
        assert ru_complete["normalized_brief"]["location"] == "Ukraine"
        assert ru_complete["normalized_brief"]["stack"] == ["Spring", "Kafka"]
        assert ru_complete["recommended_planner_mode"] == "rule_based"
        assert ru_complete["can_build_plan"] is True
        assert ru_complete["build_plan_action"]["endpoint"] == "/api/agent/query-plan"
        assert ru_complete["build_plan_action"]["planner_mode"] == "rule_based"

        en_complete = await main.recruiter_chat_turn_response(
            chat_request(
                "Find backend developers in Ukraine with Java as main skill, "
                "ideally Spring and Kafka.",
                language="en",
            )
        )
        assert en_complete["ok"] is True
        assert en_complete["state"] == "ready_for_planning"
        assert en_complete["recommended_planner_mode"] == "rule_based"

        incomplete = await main.recruiter_chat_turn_response(
            chat_request("Найди Java разработчиков.", language="ru")
        )
        assert incomplete["ok"] is True
        assert incomplete["state"] == "needs_clarification"
        assert incomplete["next_question"]
        assert "\n" not in incomplete["next_question"]
        assert incomplete["can_build_plan"] is False

        refused = await main.recruiter_chat_turn_response(
            chat_request(
                "Зайди в LinkedIn, залогинься и напиши кандидатам.",
                language="ru",
            )
        )
        assert refused["ok"] is False
        assert refused["state"] == "refused"
        assert refused["validation_errors"]
        assert refused["can_build_plan"] is False

    finally:
        main.run_openai_json_recruiter_chat = original_llm
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P5 chat adapter smoke passed")
