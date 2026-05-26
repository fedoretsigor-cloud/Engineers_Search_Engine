from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from app import main
from app.search_execution import (
    PHASE9_SERPAPI_PAGE_LIMIT,
    SEARCH_PROVIDER_SERPER,
    SEARCH_PROVIDER_SERPAPI_BING,
    SEARCH_PROVIDER_SERPAPI_GOOGLE,
    SEARCH_PROVIDER_TAVILY,
    _serpapi_params,
    provider_result,
)


QUERY_SLOT = {
    "id": "Q01",
    "category": "role_based",
    "role_phrase": "Java Backend Developer",
    "uses_stack": ["Spring"],
    "query": 'site:linkedin.com/in ("Java Backend Developer") Ukraine Spring',
    "max_results": 10,
}


def query_plan() -> dict:
    return {
        "version": "smoke",
        "input_snapshot": {
            "role_family": "Backend Developer",
            "technology": "Java",
            "stack": ["Spring"],
            "location": "Ukraine",
        },
        "filters": {
            "linkedin_profiles_only": True,
            "location_filter_enabled": False,
        },
        "queries": [QUERY_SLOT],
    }


def query_result(provider: str, url: str, title: str, snippet: str) -> dict:
    return {
        "query_id": QUERY_SLOT["id"],
        "provider_query_id": f"{provider}:Q01",
        "provider": provider,
        "provider_page": 1 if provider != SEARCH_PROVIDER_TAVILY else None,
        "category": QUERY_SLOT["category"],
        "role_phrase": QUERY_SLOT["role_phrase"],
        "uses_stack": QUERY_SLOT["uses_stack"],
        "query": QUERY_SLOT["query"],
        "ok": True,
        "raw_results": [
            provider_result(
                provider=provider,
                query_slot=QUERY_SLOT,
                title=title,
                url=url,
                snippet=snippet,
                rank=1,
                page=1,
            )
        ],
        "raw_count": 1,
        "response_time": 0.1,
        "usage": None,
        "request_id": None,
        "error": None,
    }


def main_smoke() -> None:
    plan = query_plan()
    query_results = [
        query_result(
            SEARCH_PROVIDER_TAVILY,
            "https://ua.linkedin.com/in/shared-java",
            "Shared Java Backend Developer - LinkedIn",
            "Kyiv, Ukraine - Java Spring",
        ),
        query_result(
            SEARCH_PROVIDER_SERPER,
            "https://ua.linkedin.com/in/shared-java",
            "Shared Java Backend Developer",
            "Ukraine - Java Spring",
        ),
        query_result(
            SEARCH_PROVIDER_SERPAPI_GOOGLE,
            "https://ua.linkedin.com/in/google-java",
            "Google Java Backend Developer",
            "Ukraine - Java Spring",
        ),
        query_result(
            SEARCH_PROVIDER_SERPAPI_BING,
            "https://ua.linkedin.com/in/bing-java",
            "Bing Java Backend Developer",
            "Ukraine - Java Spring",
        ),
    ]

    deduped_results, report = main.build_deduped_results_and_report(
        plan,
        query_results,
    )
    report = main.mark_multi_provider_report(
        plan,
        report,
        query_results,
        base_mode="single_wave",
    )

    assert len(deduped_results) == 3
    shared = next(
        item
        for item in deduped_results
        if item["normalized_url"] == "ua.linkedin.com/in/shared-java"
    )
    shared_providers = {
        source["provider"] for source in shared.get("provider_sources", [])
    }
    assert shared_providers == {SEARCH_PROVIDER_TAVILY, SEARCH_PROVIDER_SERPER}
    assert report["provider_mode"] == "multi_provider"
    assert report["query_attempts"] == 4
    assert report["providers"] == [
        SEARCH_PROVIDER_TAVILY,
        SEARCH_PROVIDER_SERPER,
        SEARCH_PROVIDER_SERPAPI_GOOGLE,
        SEARCH_PROVIDER_SERPAPI_BING,
    ]
    assert report["provider_breakdown"][SEARCH_PROVIDER_SERPER]["raw_total"] == 1
    assert report["provider_breakdown"][SEARCH_PROVIDER_SERPER]["duplicates"] == 1
    assert report["provider_limits"]["serpapi_google_pages"] == 5
    assert PHASE9_SERPAPI_PAGE_LIMIT == 5

    google_page_5 = _serpapi_params(
        QUERY_SLOT,
        SEARCH_PROVIDER_SERPAPI_GOOGLE,
        5,
        "secret",
    )
    bing_page_5 = _serpapi_params(
        QUERY_SLOT,
        SEARCH_PROVIDER_SERPAPI_BING,
        5,
        "secret",
    )
    assert google_page_5["engine"] == "google"
    assert google_page_5["start"] == 40
    assert bing_page_5["engine"] == "bing"
    assert bing_page_5["first"] == 41
    assert "secret" not in str(report)


if __name__ == "__main__":
    main_smoke()
    print("P9 multi-provider search smoke passed")
