from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app import main  # noqa: E402


REPORT_DOC = REPO_ROOT / "docs" / "phase-8-75-uat-report.md"


@dataclass
class LiveCheck:
    case_id: str
    scenario_id: str
    category: str
    status: str
    detail: str = ""


def ready_brief(
    *,
    text: str,
    stack: list[str],
    language: str,
) -> main.SearchBrief:
    return main.SearchBrief(
        source_text=text,
        brief_status="ready_for_planning",
        role_family="Backend Developer",
        technology="Java",
        stack=stack,
        location="Ukraine",
        seniority=None,
        must_have=["Java"],
        nice_to_have=stack,
        exclusions=[],
        search_depth="standard",
        profile_sources=["linkedin_public"],
        assumptions=[],
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
        "search_brief_fingerprint": main.search_brief_fingerprint(
            main.search_brief_validation_response(
                main.SearchBrief(**{
                    "source_text": "live-uat",
                    "brief_status": "ready_for_planning",
                    "role_family": tool_input["role_family"],
                    "technology": tool_input["technology"],
                    "stack": tool_input["stack"],
                    "location": tool_input["location"],
                    "search_depth": tool_input["search_depth"],
                    "profile_sources": ["linkedin_public"],
                })
            )["normalized_brief"]
        ),
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


def runtime_request(
    *,
    tool_name: str,
    tool_input: dict[str, Any],
    turn_mode: str,
    runtime_approval: dict[str, Any] | None = None,
    language: str,
) -> main.AgentRuntimeTurnRequest:
    return main.AgentRuntimeTurnRequest(
        turn_mode=turn_mode,
        tool_name=tool_name,
        tool_input=tool_input,
        runtime_context=build_runtime_context(tool_name, tool_input),
        runtime_approval=runtime_approval,
        agent_language=language,
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


def check(checks: list[LiveCheck], case_id: str, scenario_id: str, category: str, condition: bool, detail: str = "") -> None:
    status = "pass" if condition else "fail"
    checks.append(LiveCheck(case_id, scenario_id, category, status, detail if not condition else ""))
    if not condition:
        raise AssertionError(f"{case_id} failed: {detail}")


def compact_agent_response_matches(message: str, report: dict[str, Any], agent_response: dict[str, Any]) -> bool:
    if not isinstance(message, str) or not message.strip():
        return False
    if "\n" in message or len(message) > 260:
        return False
    lowered = message.lower()
    if "search completed" not in lowered and "поиск заверш" not in lowered:
        return False
    summary_facts = agent_response.get("summary_facts") or {}
    quality = summary_facts.get("quality_distribution") or {}
    expected_numbers = [
        summary_facts.get("candidate_count", report.get("unique_profiles", 0)),
        quality.get("strong", 0),
        quality.get("review", 0),
        quality.get("weak", 0),
    ]
    if any(str(int(value or 0)) not in message for value in expected_numbers):
        return False
    forbidden_terms = [
        "raw result",
        "queries executed",
        "next iteration",
        "limitations",
        "огранич",
        "следующ",
    ]
    return not any(term in lowered for term in forbidden_terms)


LIVE_SCENARIOS = [
    {
        "scenario_id": "LIVE-EN-SINGLE-001",
        "language": "en",
        "brief": ready_brief(
            text="Find backend developers in Ukraine with Java, Spring and Kafka.",
            stack=["Spring", "Kafka"],
            language="en",
        ),
        "tool_name": "run_single_wave_search",
        "tool_input": {
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring", "Kafka"],
            "location": "Ukraine",
            "search_depth": "standard",
            "linkedin_profiles_only": True,
            "location_filter_enabled": True,
        },
    },
    {
        "scenario_id": "LIVE-RU-MULTI-001",
        "language": "ru",
        "brief": ready_brief(
            text="Найди backend разработчиков в Украине, основной стек Java, Spring и Kafka.",
            stack=["Spring", "Kafka"],
            language="ru",
        ),
        "tool_name": "run_multi_wave_search",
        "tool_input": {
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring", "Kafka"],
            "location": "Ukraine",
            "search_depth": "standard",
            "linkedin_profiles_only": True,
            "location_filter_enabled": True,
            "max_waves": 2,
            "min_new_unique_per_wave": 2,
            "patience": 1,
        },
    },
]


async def run_live_scenario(scenario: dict[str, Any], checks: list[LiveCheck]) -> dict[str, Any]:
    scenario_id = scenario["scenario_id"]
    language = scenario["language"]
    brief = scenario["brief"]
    tool_name = scenario["tool_name"]
    tool_input = scenario["tool_input"]

    agent_plan = main.build_agent_plan_response(
        main.AgentPlanRequest(search_brief=brief, language=language)
    )
    check(checks, f"{scenario_id}-PLAN-OK", scenario_id, "live_plan", agent_plan["ok"] is True, "Agent Plan failed")
    check(
        checks,
        f"{scenario_id}-PLAN-SUPPORTED",
        scenario_id,
        "live_plan",
        agent_plan["agent_plan_status"] == "supported",
        f"Unexpected agent plan status: {agent_plan['agent_plan_status']}",
    )

    query_plan = await main.create_agent_query_plan(
        main.AgentQueryPlanRequest(
            planner_mode="rule_based",
            search_brief=brief,
            agent_plan_brief_fingerprint=agent_plan["agent_plan"]["brief_fingerprint"],
            agent_plan_action=agent_plan["agent_plan"]["proposed_action"],
        )
    )
    check(checks, f"{scenario_id}-QUERY-OK", scenario_id, "live_query_plan", query_plan["ok"] is True, "QueryPlan failed")
    check(
        checks,
        f"{scenario_id}-QUERY-COUNT",
        scenario_id,
        "live_query_plan",
        len(query_plan["query_plan"]["queries"]) == 10,
        "Expected 10 query slots",
    )
    check(
        checks,
        f"{scenario_id}-QUERY-NOT-EXECUTABLE",
        scenario_id,
        "live_query_plan",
        query_plan["execution_allowed"] is False and query_plan["execution_approval_required"] is True,
        "QueryPlan must require execution approval",
    )

    prepare = await main.create_agent_runtime_turn(
        runtime_request(
            tool_name=tool_name,
            tool_input=tool_input,
            turn_mode="prepare",
            language=language,
        )
    )
    check(checks, f"{scenario_id}-PREPARE-OK", scenario_id, "live_runtime", prepare["ok"] is True, "Runtime prepare failed")
    check(
        checks,
        f"{scenario_id}-PREPARE-PENDING",
        scenario_id,
        "live_runtime",
        prepare["runtime_state"] == "approval_pending",
        f"Unexpected runtime state: {prepare['runtime_state']}",
    )
    check(
        checks,
        f"{scenario_id}-PREPARE-APPROVAL",
        scenario_id,
        "live_runtime",
        bool(prepare["pending_approvals"]),
        "Expected pending approval",
    )

    approval = approval_from_prepare(prepare)
    observed = await main.create_agent_runtime_turn(
        runtime_request(
            tool_name=tool_name,
            tool_input=tool_input,
            turn_mode="execute_approved",
            runtime_approval=approval,
            language=language,
        )
    )
    check(checks, f"{scenario_id}-EXEC-OK", scenario_id, "live_runtime", observed["ok"] is True, "Runtime execute failed")
    check(
        checks,
        f"{scenario_id}-EXEC-OBSERVED",
        scenario_id,
        "live_runtime",
        observed["runtime_state"] == "observed",
        f"Unexpected runtime state: {observed['runtime_state']}",
    )

    result = observed["tool_results"][0]["result"]
    report = result["report"]
    deduped = result.get("deduped_results", [])
    agent_response = result.get("agent_response") or {}
    message = agent_response.get("message", "")

    check(checks, f"{scenario_id}-REPORT-SUCCESS", scenario_id, "live_results", report.get("queries_succeeded", 0) > 0, "No successful queries")
    check(checks, f"{scenario_id}-REPORT-UNIQUE", scenario_id, "live_results", report.get("unique_profiles", 0) > 0, "No unique profiles")
    check(checks, f"{scenario_id}-RESULTS-PRESENT", scenario_id, "live_results", len(deduped) > 0, "No deduped candidates")
    check(
        checks,
        f"{scenario_id}-AGENT-RESPONSE-COMPACT",
        scenario_id,
        "live_results",
        compact_agent_response_matches(message, report, agent_response),
        f"Unexpected agent response message: {message}",
    )
    check(
        checks,
        f"{scenario_id}-NO-AUTO-PROFILE",
        scenario_id,
        "live_boundaries",
        not any("opened_profile" in json.dumps(item).lower() for item in observed.get("tool_results", [])),
        "Runtime must not open profiles",
    )

    return {
        "scenario_id": scenario_id,
        "tool_name": tool_name,
        "queries_succeeded": report.get("queries_succeeded", 0),
        "queries_total": report.get("queries_total", 0),
        "unique_profiles": report.get("unique_profiles", 0),
        "displayed": report.get("displayed", 0),
        "raw_total": report.get("raw_total", 0),
        "mode": report.get("mode") or ("multi_wave" if tool_name == "run_multi_wave_search" else "single_wave"),
        "waves_run": report.get("waves_run"),
        "stop_reason": report.get("stop_reason"),
    }


async def run_live() -> dict[str, Any]:
    if not os.getenv("TAVILY_API_KEY"):
        raise RuntimeError("TAVILY_API_KEY is required for Phase 8.75 live UAT.")

    checks: list[LiveCheck] = []
    scenario_summaries: list[dict[str, Any]] = []
    for scenario in LIVE_SCENARIOS:
        scenario_summaries.append(await run_live_scenario(scenario, checks))

    counts = Counter(check.status for check in checks)
    failed = [check for check in checks if check.status != "pass"]
    return {
        "status": "green" if not failed else "red",
        "total": len(checks),
        "passed": counts.get("pass", 0),
        "failed": counts.get("fail", 0),
        "scenarios": scenario_summaries,
        "failed_checks": [check.__dict__ for check in failed],
    }


def write_live_report(summary: dict[str, Any], output_path: Path) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    scenario_rows = "\n".join(
        "| {scenario_id} | {mode} | {queries_succeeded}/{queries_total} | {unique_profiles} | {displayed} | {waves_run} | {stop_reason} |".format(
            scenario_id=item["scenario_id"],
            mode=item["mode"],
            queries_succeeded=item["queries_succeeded"],
            queries_total=item["queries_total"],
            unique_profiles=item["unique_profiles"],
            displayed=item["displayed"],
            waves_run=item.get("waves_run") or "n/a",
            stop_reason=item.get("stop_reason") or "n/a",
        )
        for item in summary["scenarios"]
    )

    existing = output_path.read_text(encoding="utf-8") if output_path.exists() else "# Phase 8.75 UAT Report\n"
    live_section = f"""## Live Acceptance Run

Generated: {now}

Status: `{summary['status']}`

| Metric | Count |
| --- | ---: |
| live checks | {summary['total']} |
| passed | {summary['passed']} |
| failed | {summary['failed']} |
| approved backend runtime executions | {len(summary['scenarios'])} |

| Scenario | Mode | Queries succeeded | Unique profiles | Displayed | Waves | Stop reason |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{scenario_rows}

Live UAT used only the existing backend Agent Runtime prepare -> explicit approval -> execute_approved path. It did not call Tavily directly, did not open LinkedIn profiles, did not log in, did not scrape, did not message candidates, and did not commit raw result payloads or candidate URLs.
"""

    if "## Live Acceptance Run" in existing:
        prefix = existing.split("## Live Acceptance Run", 1)[0]
        suffix = ""
        if "## Failures" in existing:
            suffix = "\n## Failures" + existing.split("## Failures", 1)[1]
        output_path.write_text(prefix + live_section + ("\n" + suffix if suffix else ""), encoding="utf-8")
    else:
        output_path.write_text(existing.rstrip() + "\n\n" + live_section, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 8.75 limited live Tavily UAT through backend runtime.")
    parser.add_argument(
        "--write-report",
        type=Path,
        default=None,
        help="Optional Markdown report path to update.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    return parser.parse_args()


def main_entry() -> None:
    args = parse_args()
    summary = asyncio.run(run_live())
    if summary["failed"]:
        raise AssertionError(summary["failed_checks"])
    if args.write_report:
        write_live_report(summary, args.write_report)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "Phase 8.75 live UAT passed: "
            f"{summary['passed']}/{summary['total']} checks across {len(summary['scenarios'])} approved executions"
        )


if __name__ == "__main__":
    main_entry()
