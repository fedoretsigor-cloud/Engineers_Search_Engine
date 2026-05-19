import os

import httpx
from fastapi import HTTPException

from app.agent_messages import runtime_tool_unavailable_source_message


TAVILY_SEARCH_URL = "https://api.tavily.com/search"


async def run_tavily_query(query: str, max_results: int) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=runtime_tool_unavailable_source_message(),
        )

    payload = {
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
        "include_favicon": False,
        "include_domains": ["linkedin.com"],
        "include_usage": True,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Tavily search request failed.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tavily search is unavailable.") from exc

    return response.json()


async def run_query_slot(query_slot: dict) -> dict:
    try:
        tavily_data = await run_tavily_query(
            query_slot["query"],
            query_slot["max_results"],
        )
    except HTTPException as exc:
        return {
            "query_id": query_slot["id"],
            "category": query_slot["category"],
            "role_phrase": query_slot.get("role_phrase"),
            "uses_stack": query_slot.get("uses_stack", []),
            "query": query_slot["query"],
            "ok": False,
            "raw_results": [],
            "raw_count": 0,
            "response_time": None,
            "usage": None,
            "request_id": None,
            "error": exc.detail,
        }

    raw_results = tavily_data.get("results", [])
    return {
        "query_id": query_slot["id"],
        "category": query_slot["category"],
        "role_phrase": query_slot.get("role_phrase"),
        "uses_stack": query_slot.get("uses_stack", []),
        "query": query_slot["query"],
        "ok": True,
        "raw_results": raw_results,
        "raw_count": len(raw_results),
        "response_time": tavily_data.get("response_time"),
        "usage": tavily_data.get("usage"),
        "request_id": tavily_data.get("request_id"),
        "error": None,
    }


async def run_query_plan_wave(
    query_plan: dict,
    wave_id: int | None = None,
) -> list[dict]:
    query_results = []

    for query_slot in query_plan["queries"]:
        query_result = await run_query_slot(query_slot)
        if wave_id is not None:
            query_result["wave_id"] = wave_id
        query_results.append(query_result)

    return query_results


async def run_multi_wave_query_plan_core(
    query_plan: dict,
    settings: dict,
    run_wave,
    build_report,
) -> tuple[list[dict], dict, list[dict]]:
    all_query_results: list[dict] = []
    wave_reports: list[dict] = []
    cumulative_unique_urls: set[str] = set()
    low_gain_streak = 0
    stop_reason = "max_waves_reached"

    for wave_id in range(1, settings["max_waves"] + 1):
        wave_query_results = await run_wave(query_plan, wave_id)
        all_query_results.extend(wave_query_results)

        wave_deduped_results, wave_report = build_report(
            query_plan,
            wave_query_results,
            include_wave_sources=True,
        )
        wave_unique_urls = {
            result["normalized_url"] for result in wave_deduped_results
        }
        new_unique_urls = wave_unique_urls - cumulative_unique_urls
        duplicates_across_waves = len(wave_unique_urls & cumulative_unique_urls)
        cumulative_unique_urls.update(wave_unique_urls)

        new_unique_count = len(new_unique_urls)
        if new_unique_count < settings["min_new_unique_per_wave"]:
            low_gain_streak += 1
        else:
            low_gain_streak = 0

        wave_reports.append(
            {
                "wave_id": wave_id,
                "queries_succeeded": wave_report["queries_succeeded"],
                "queries_failed": wave_report["queries_failed"],
                "raw_total": wave_report["raw_total"],
                "displayed": wave_report["displayed"],
                "unique_profiles": wave_report["unique_profiles"],
                "new_unique_profiles": new_unique_count,
                "cumulative_unique_profiles": len(cumulative_unique_urls),
                "duplicates_across_waves": duplicates_across_waves,
                "hidden_by_profile_filter": wave_report[
                    "hidden_by_profile_filter"
                ],
                "hidden_by_location_filter": wave_report[
                    "hidden_by_location_filter"
                ],
                "hidden_by_foreign_current_location": wave_report[
                    "hidden_by_foreign_current_location"
                ],
            }
        )

        if low_gain_streak >= settings["patience"]:
            stop_reason = "low_incremental_gain"
            break

    deduped_results, report = build_report(
        query_plan,
        all_query_results,
        include_wave_sources=True,
    )
    report["queries_total"] = len(all_query_results)
    report.update(
        {
            "experimental": True,
            "mode": "multi_wave",
            "multi_wave_settings": settings,
            "waves_run": len(wave_reports),
            "planned_max_waves": settings["max_waves"],
            "stop_reason": stop_reason,
            "queries_executed": len(all_query_results),
            "unique_profiles_per_wave": [
                wave["unique_profiles"] for wave in wave_reports
            ],
            "new_unique_profiles_per_wave": [
                wave["new_unique_profiles"] for wave in wave_reports
            ],
            "cumulative_unique_profiles": [
                wave["cumulative_unique_profiles"] for wave in wave_reports
            ],
            "duplicates_across_waves": sum(
                wave["duplicates_across_waves"] for wave in wave_reports
            ),
            "wave_reports": wave_reports,
        }
    )

    return deduped_results, report, all_query_results
