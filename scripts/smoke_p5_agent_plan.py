import asyncio
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import main


def ready_brief(
    *,
    stack: list[str] | None = None,
    search_depth: str = "standard",
) -> main.SearchBrief:
    return main.SearchBrief(
        source_text="Find Backend Developer Java in Ukraine with Spring and Kafka.",
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


async def run_smoke() -> None:
    assert any(route.path == "/api/agent/plan" for route in main.app.routes)

    supported = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(), language="en")
    )
    assert supported["ok"] is True
    assert supported["agent_plan_status"] == "supported"
    assert supported["agent_plan"]["brief_fingerprint"]
    assert supported["agent_plan"]["proposed_action"] == {
        "action": "build_query_plan",
        "endpoint": "/api/agent/query-plan",
        "planner_mode": "rule_based",
        "requires_approval": False,
    }

    missing_agent_context = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
        )
    )
    assert missing_agent_context["ok"] is False
    assert missing_agent_context["plan_status"] == "rejected"
    assert any(
        error.get("code") == "missing_agent_plan_fingerprint"
        for error in missing_agent_context["errors"]
    )
    assert any(
        error.get("code") == "missing_agent_plan_action"
        for error in missing_agent_context["errors"]
    )

    executable_plan = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
            agent_plan_brief_fingerprint=supported["agent_plan"][
                "brief_fingerprint"
            ],
            agent_plan_action=supported["agent_plan"]["proposed_action"],
        )
    )
    assert executable_plan["ok"] is True
    assert executable_plan["plan_status"] == "validated_not_executable"
    assert len(executable_plan["query_plan"]["queries"]) == 10

    stale_plan = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
            agent_plan_brief_fingerprint="stale",
            agent_plan_action=supported["agent_plan"]["proposed_action"],
        )
    )
    assert stale_plan["ok"] is False
    assert stale_plan["plan_status"] == "rejected"
    assert any(
        error.get("code") == "stale_or_mismatched_agent_plan_fingerprint"
        for error in stale_plan["errors"]
    )

    mismatched_action = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=ready_brief(),
            agent_plan_brief_fingerprint=supported["agent_plan"][
                "brief_fingerprint"
            ],
            agent_plan_action={
                **supported["agent_plan"]["proposed_action"],
                "planner_mode": "ai",
            },
        )
    )
    assert mismatched_action["ok"] is False
    assert any(
        error.get("code") == "unsupported_agent_plan_action"
        for error in mismatched_action["errors"]
    )

    missing_stack = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=ready_brief(stack=[]), language="en")
    )
    assert missing_stack["ok"] is True
    assert missing_stack["agent_plan_status"] == "needs_clarification"
    assert missing_stack["agent_plan"] is None
    assert "stack" in missing_stack["missing_fields"]

    unsupported = main.build_agent_plan_response(
        main.AgentPlanRequest(
            search_brief=ready_brief(search_depth="deep"),
            language="en",
        )
    )
    assert unsupported["ok"] is True
    assert unsupported["agent_plan_status"] == "unsupported"
    assert unsupported["agent_plan"] is None


if __name__ == "__main__":
    asyncio.run(run_smoke())
    print("P5 Agent Plan smoke passed")
