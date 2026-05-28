from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app.main import build_deduped_results_and_report
from app.planning import RuleBasedQueryPlannerV1
from app.schemas import StructuredSearchRequest
from app.search_validation import normalize_structured_search_request


def normalized_request(location: str) -> dict:
    request, errors = normalize_structured_search_request(
        StructuredSearchRequest(
            role_family="Business Analyst",
            technology="SQL",
            stack=["SQL"],
            location=location,
        )
    )
    assert errors == [], errors
    assert request is not None
    return request


def raw_result(title: str, url: str, content: str) -> dict:
    return {
        "title": title,
        "url": url,
        "content": content,
        "score": 0.95,
    }


def query_results_for(raw_results: list[dict]) -> list[dict]:
    return [
        {
            "query_id": "Q01",
            "provider_query_id": "tavily:Q01",
            "provider": "tavily",
            "provider_page": None,
            "category": "role_based",
            "role_phrase": "Business Analyst",
            "uses_stack": [],
            "query": 'site:linkedin.com/in AND "Business Analyst" AND "SQL" AND "Poland"',
            "ok": True,
            "raw_results": raw_results,
            "raw_count": len(raw_results),
            "response_time": 0.1,
            "usage": None,
            "request_id": None,
            "error": None,
        }
    ]


def assert_poland_location_guard() -> None:
    request = normalized_request("Poland")
    assert request["location_filter_enabled"] is True, request
    plan = RuleBasedQueryPlannerV1().build(request)
    assert plan["filters"]["location_filter_enabled"] is True, plan

    deduped, report = build_deduped_results_and_report(
        plan,
        query_results_for(
            [
                raw_result(
                    "Kostia Sydorenko - Business Analyst",
                    "https://pl.linkedin.com/in/kostia",
                    "Kostia Sydorenko\nBusiness Analyst\n500 connections",
                ),
                raw_result(
                    "Anna Kowalska - Business Analyst",
                    "https://www.linkedin.com/in/anna-kowalska",
                    "Anna Kowalska\nBusiness Analyst\nWarsaw, Poland\n500 connections",
                ),
                raw_result(
                    "Tim Kane - Business Analyst",
                    "https://www.linkedin.com/in/tim-kane",
                    "Tim Kane\nBusiness Analyst\nNew York, United States\n500 connections",
                ),
                raw_result(
                    "Bob Market - Business Analyst",
                    "https://www.linkedin.com/in/bob-market",
                    "Bob Market Business Analyst SQL for Poland market history",
                ),
                raw_result(
                    "Unknown Location - Business Analyst",
                    "https://www.linkedin.com/in/unknown-location",
                    "Unknown Location\nBusiness Analyst\nSQL reporting\n500 connections",
                ),
            ]
        ),
    )

    statuses = {item["location_signal_status"] for item in deduped}
    assert report["unique_profiles"] == 2, report
    assert statuses == {"country_domain", "target_location"}, statuses
    assert report["hidden_by_location_filter"] == 3, report
    assert report["hidden_by_foreign_current_location"] == 1, report
    assert report["weak_location_history_only"] == 1, report
    assert report["unknown_non_country_domain_location"] == 1, report
    assert report["location_filter_report"]["config_location"] == "Poland", report


def assert_fallback_location_guard_for_unseeded_location() -> None:
    request = normalized_request("Portugal")
    assert request["location_filter_enabled"] is True, request
    plan = RuleBasedQueryPlannerV1().build(request)

    deduped, report = build_deduped_results_and_report(
        plan,
        query_results_for(
            [
                raw_result(
                    "Ana Silva - Business Analyst",
                    "https://www.linkedin.com/in/ana-silva",
                    "Ana Silva\nBusiness Analyst\nLisbon, Portugal\n500 connections",
                ),
                raw_result(
                    "Foreign Candidate - Business Analyst",
                    "https://www.linkedin.com/in/foreign-candidate",
                    "Foreign Candidate\nBusiness Analyst\nMadrid, Spain\n500 connections",
                ),
            ]
        ),
    )

    assert report["location_filter_report"]["config_location"] == "Portugal", report
    assert report["unique_profiles"] == 1, report
    assert deduped[0]["location_signal_status"] == "target_location", deduped
    assert report["hidden_by_foreign_current_location"] == 1, report


def assert_known_country_aliases() -> None:
    for location, expected_label in [
        ("Spain", "Spain"),
        ("Canada", "Canada"),
        ("UK", "United Kingdom"),
        ("United States", "United States"),
        ("Remote", "Remote"),
    ]:
        request = normalized_request(location)
        assert request["location_filter_enabled"] is True, (location, request)
        plan = RuleBasedQueryPlannerV1().build(request)
        assert plan["filters"]["location_filter_enabled"] is True, plan
        assert plan["input_snapshot"]["location"] == location, plan


def main() -> None:
    assert_poland_location_guard()
    assert_fallback_location_guard_for_unseeded_location()
    assert_known_country_aliases()
    print("P9.10 LocationGuard smoke passed")


if __name__ == "__main__":
    main()
