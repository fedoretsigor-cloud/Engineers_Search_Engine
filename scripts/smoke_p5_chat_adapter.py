import asyncio
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


def chat_request(text: str, language: str | None = None) -> main.RecruiterChatTurnRequest:
    return main.RecruiterChatTurnRequest(
        language=language,
        messages=[main.RecruiterChatMessage(role="user", content=text)],
    )


async def fake_recruiter_chat_llm(
    request: main.RecruiterChatTurnRequest,
) -> tuple[dict | None, list[dict[str, str]]]:
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
    original_llm = main.run_openai_json_recruiter_chat
    main.run_openai_json_recruiter_chat = fake_recruiter_chat_llm

    try:
        assert any(
            route.path == "/api/recruiter-chat/turn"
            for route in main.app.routes
        )
        assert main.normalize_location_value("Украина") == "Ukraine"

        ru_complete = await main.recruiter_chat_turn_response(
            chat_request(
                "Найди backend разработчиков в Украине, основной стек Java, "
                "желательно Spring и Kafka.",
                language="ru",
            )
        )
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


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P5 chat adapter smoke passed")
