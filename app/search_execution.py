from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx
from fastapi import HTTPException

from app.agent_messages import runtime_tool_unavailable_source_message


TAVILY_SEARCH_URL = "https://api.tavily.com/search"
SERPER_SEARCH_URL = "https://google.serper.dev/search"
SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"

SEARCH_PROVIDER_TAVILY = "tavily"
SEARCH_PROVIDER_SERPER = "serper"
SEARCH_PROVIDER_SERPAPI_GOOGLE = "serpapi_google"
SEARCH_PROVIDER_SERPAPI_BING = "serpapi_bing"
PHASE9_EXTRA_PROVIDERS = [
    SEARCH_PROVIDER_SERPER,
    SEARCH_PROVIDER_SERPAPI_GOOGLE,
    SEARCH_PROVIDER_SERPAPI_BING,
]
PHASE9_PROVIDER_ORDER = [
    SEARCH_PROVIDER_TAVILY,
    *PHASE9_EXTRA_PROVIDERS,
]
PHASE9_SERPAPI_PAGE_LIMIT = 5
PHASE9_PROVIDER_TIMEOUT_SECONDS = 20
PHASE9_PROVIDER_MAX_CONCURRENCY = 4


def provider_result(
    *,
    provider: str,
    query_slot: dict,
    title: Any,
    url: Any,
    snippet: Any = "",
    rank: Any = None,
    page: int = 1,
) -> dict:
    return {
        "provider": provider,
        "provider_query_id": query_slot["id"],
        "query_text": query_slot["query"],
        "title": str(title or "").strip(),
        "url": str(url or "").strip(),
        "content": str(snippet or "").strip(),
        "snippet": str(snippet or "").strip(),
        "rank": rank,
        "page": page,
    }


def _bounded_provider_error(message: str) -> str:
    text = str(message or "Provider request failed.").strip()
    if len(text) > 180:
        text = f"{text[:177]}..."
    return text


def _provider_query_result(
    query_slot: dict,
    provider: str,
    *,
    ok: bool,
    raw_results: list[dict] | None = None,
    page: int | None = None,
    response_time: float | None = None,
    error: str | None = None,
) -> dict:
    provider_query_id = (
        f"{provider}:{query_slot['id']}:p{page}"
        if page is not None
        else f"{provider}:{query_slot['id']}"
    )
    return {
        "query_id": query_slot["id"],
        "provider_query_id": provider_query_id,
        "provider": provider,
        "provider_page": page,
        "category": query_slot["category"],
        "role_phrase": query_slot.get("role_phrase"),
        "uses_stack": query_slot.get("uses_stack", []),
        "query": query_slot["query"],
        "ok": ok,
        "raw_results": raw_results or [],
        "raw_count": len(raw_results or []),
        "response_time": response_time,
        "usage": None,
        "request_id": None,
        "error": error,
    }


def provider_unavailable_result(query_slot: dict, provider: str, message: str) -> dict:
    return _provider_query_result(
        query_slot,
        provider,
        ok=False,
        raw_results=[],
        error=_bounded_provider_error(message),
    )


async def _post_json(
    url: str,
    *,
    headers: dict[str, str],
    json_payload: dict[str, Any],
) -> tuple[dict, float]:
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=PHASE9_PROVIDER_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=headers, json=json_payload)
        response.raise_for_status()
    return response.json(), round(time.perf_counter() - start, 3)


async def _get_json(
    url: str,
    *,
    params: dict[str, Any],
) -> tuple[dict, float]:
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=PHASE9_PROVIDER_TIMEOUT_SECONDS) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
    return response.json(), round(time.perf_counter() - start, 3)


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
            "provider_query_id": f"{SEARCH_PROVIDER_TAVILY}:{query_slot['id']}",
            "provider": SEARCH_PROVIDER_TAVILY,
            "provider_page": None,
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
        "provider_query_id": f"{SEARCH_PROVIDER_TAVILY}:{query_slot['id']}",
        "provider": SEARCH_PROVIDER_TAVILY,
        "provider_page": None,
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


async def run_serper_query_slot(query_slot: dict) -> dict:
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return provider_unavailable_result(
            query_slot,
            SEARCH_PROVIDER_SERPER,
            "SERPER_API_KEY is not configured.",
        )

    payload = {
        "q": query_slot["query"],
        "num": query_slot["max_results"],
        "page": 1,
    }
    try:
        data, response_time = await _post_json(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json_payload=payload,
        )
    except httpx.HTTPStatusError as exc:
        return provider_unavailable_result(
            query_slot,
            SEARCH_PROVIDER_SERPER,
            f"Serper request failed with status {exc.response.status_code}.",
        )
    except httpx.HTTPError:
        return provider_unavailable_result(
            query_slot,
            SEARCH_PROVIDER_SERPER,
            "Serper search is unavailable.",
        )

    raw_organic = data.get("organic", [])
    raw_results = [
        provider_result(
            provider=SEARCH_PROVIDER_SERPER,
            query_slot=query_slot,
            title=item.get("title"),
            url=item.get("link"),
            snippet=item.get("snippet"),
            rank=item.get("position"),
            page=1,
        )
        for item in raw_organic
        if isinstance(item, dict)
    ]
    result = _provider_query_result(
        query_slot,
        SEARCH_PROVIDER_SERPER,
        ok=True,
        raw_results=raw_results,
        page=1,
        response_time=response_time,
    )
    result["usage"] = {
        "credits": data.get("credits"),
        "organic_count": len(raw_organic),
    }
    return result


def _serpapi_params(query_slot: dict, provider: str, page: int, api_key: str) -> dict:
    params: dict[str, Any] = {
        "api_key": api_key,
        "q": query_slot["query"],
        "num": query_slot["max_results"],
        "output": "json",
    }
    if provider == SEARCH_PROVIDER_SERPAPI_GOOGLE:
        params.update(
            {
                "engine": "google",
                "start": (page - 1) * query_slot["max_results"],
                "google_domain": "google.com",
                "hl": "en",
                "gl": "ua",
            }
        )
    else:
        params.update(
            {
                "engine": "bing",
                "first": (page - 1) * query_slot["max_results"] + 1,
                "cc": "UA",
            }
        )
    return params


async def run_serpapi_query_slot_page(
    query_slot: dict,
    provider: str,
    page: int,
) -> dict:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return provider_unavailable_result(
            query_slot,
            provider,
            "SERPAPI_API_KEY is not configured.",
        )

    try:
        data, response_time = await _get_json(
            SERPAPI_SEARCH_URL,
            params=_serpapi_params(query_slot, provider, page, api_key),
        )
    except httpx.HTTPStatusError as exc:
        return _provider_query_result(
            query_slot,
            provider,
            ok=False,
            page=page,
            error=_bounded_provider_error(
                f"SerpApi request failed with status {exc.response.status_code}."
            ),
        )
    except httpx.HTTPError:
        return _provider_query_result(
            query_slot,
            provider,
            ok=False,
            page=page,
            error=_bounded_provider_error("SerpApi search is unavailable."),
        )

    raw_organic = data.get("organic_results", [])
    raw_results = [
        provider_result(
            provider=provider,
            query_slot=query_slot,
            title=item.get("title"),
            url=item.get("link"),
            snippet=item.get("snippet"),
            rank=item.get("position"),
            page=page,
        )
        for item in raw_organic
        if isinstance(item, dict)
    ]
    result = _provider_query_result(
        query_slot,
        provider,
        ok=True,
        raw_results=raw_results,
        page=page,
        response_time=response_time,
    )
    result["request_id"] = data.get("search_metadata", {}).get("id")
    result["usage"] = {
        "organic_count": len(raw_organic),
        "page": page,
    }
    return result


async def run_serpapi_query_slot(query_slot: dict, provider: str) -> list[dict]:
    if not os.getenv("SERPAPI_API_KEY"):
        return [
            provider_unavailable_result(
                query_slot,
                provider,
                "SERPAPI_API_KEY is not configured.",
            )
        ]

    return [
        await run_serpapi_query_slot_page(query_slot, provider, page)
        for page in range(1, PHASE9_SERPAPI_PAGE_LIMIT + 1)
    ]


async def _run_limited(coroutines: list) -> list:
    semaphore = asyncio.Semaphore(PHASE9_PROVIDER_MAX_CONCURRENCY)

    async def run_one(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(run_one(coro) for coro in coroutines))


async def run_provider_expansion_query_plan(query_plan: dict) -> list[dict]:
    provider_runs = []
    for query_slot in query_plan["queries"]:
        provider_runs.append(run_serper_query_slot(query_slot))
        provider_runs.append(
            run_serpapi_query_slot(query_slot, SEARCH_PROVIDER_SERPAPI_GOOGLE)
        )
        provider_runs.append(
            run_serpapi_query_slot(query_slot, SEARCH_PROVIDER_SERPAPI_BING)
        )

    if not provider_runs:
        return []

    provider_results = await _run_limited(provider_runs)
    flattened: list[dict] = []
    for item in provider_results:
        if isinstance(item, list):
            flattened.extend(item)
        else:
            flattened.append(item)
    return flattened


def provider_breakdown_from_query_results(query_results: list[dict]) -> dict:
    breakdown: dict[str, dict] = {}
    for query_result in query_results:
        provider = query_result.get("provider") or SEARCH_PROVIDER_TAVILY
        provider_report = breakdown.setdefault(
            provider,
            {
                "query_attempts": 0,
                "queries_succeeded": 0,
                "queries_failed": 0,
                "raw_total": 0,
                "displayed": 0,
                "new_unique_profiles": 0,
                "duplicates": 0,
                "pages_reviewed": 0,
                "errors": [],
                "latency_seconds": 0,
            },
        )
        provider_report["query_attempts"] += 1
        provider_report["raw_total"] += int(
            query_result.get("raw_count") or query_result.get("raw") or 0
        )
        provider_report["displayed"] += int(query_result.get("filtered") or 0)
        provider_report["new_unique_profiles"] += int(
            query_result.get("new_unique_profiles") or 0
        )
        provider_report["duplicates"] += int(query_result.get("duplicates") or 0)
        if query_result.get("ok"):
            provider_report["queries_succeeded"] += 1
        else:
            provider_report["queries_failed"] += 1
            if query_result.get("error"):
                provider_report["errors"].append(
                    _bounded_provider_error(query_result["error"])
                )
        if query_result.get("provider_page"):
            provider_report["pages_reviewed"] += 1
        if query_result.get("response_time"):
            provider_report["latency_seconds"] = round(
                provider_report["latency_seconds"]
                + float(query_result.get("response_time") or 0),
                3,
            )

    return breakdown


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
