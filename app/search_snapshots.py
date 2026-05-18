from datetime import datetime, timezone
import json
from pathlib import Path
import re

from app.planning import add_query_plan_fingerprint, query_plan_fingerprint
from app.text_utils import compact_spaces


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
SEARCH_RUN_LOG_DIR = PROJECT_DIR / "logs" / "search-runs"


def snapshot_slug(value: object) -> str:
    compact_value = compact_spaces(str(value or "")).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", compact_value).strip("-")
    return slug or "unknown"


def structured_search_snapshot_filename(
    normalized_request: dict,
    timestamp: datetime,
    snapshot_type: str = "structured-search",
) -> str:
    timestamp_part = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")
    role_part = snapshot_slug(normalized_request.get("role_family"))
    technology_part = snapshot_slug(normalized_request.get("technology"))
    location_part = snapshot_slug(normalized_request.get("location"))

    return (
        f"{timestamp_part}_{snapshot_type}_"
        f"{role_part}-{technology_part}-{location_part}.json"
    )


def query_result_status_summary(query_result: dict) -> dict:
    summary = {
        "query_id": query_result.get("query_id"),
        "category": query_result.get("category"),
        "role_phrase": query_result.get("role_phrase"),
        "uses_stack": query_result.get("uses_stack"),
        "query": query_result.get("query"),
        "ok": query_result.get("ok"),
        "raw_count": query_result.get("raw_count"),
        "response_time": query_result.get("response_time"),
        "usage": query_result.get("usage"),
        "request_id": query_result.get("request_id"),
        "error": query_result.get("error"),
    }
    if "wave_id" in query_result:
        summary["wave_id"] = query_result["wave_id"]

    return summary


def build_structured_search_snapshot(
    query_plan: dict,
    query_results: list[dict],
    deduped_results: list[dict],
    report: dict,
    timestamp: datetime,
    snapshot_type: str = "structured-search",
    execution_approval: dict | None = None,
) -> dict:
    return {
        "snapshot_type": snapshot_type,
        "timestamp": timestamp.isoformat(),
        "normalized_request": query_plan.get("input_snapshot"),
        "query_plan": add_query_plan_fingerprint(query_plan),
        "plan_fingerprint": query_plan_fingerprint(query_plan),
        "execution_approval": execution_approval,
        "report": report,
        "location_filter_report": report.get("location_filter_report"),
        "deduped_results": deduped_results,
        "query_results_summary": [
            query_result_status_summary(query_result)
            for query_result in query_results
        ],
        "query_results": query_results,
    }


def write_structured_search_snapshot(
    query_plan: dict,
    query_results: list[dict],
    deduped_results: list[dict],
    report: dict,
    snapshot_type: str = "structured-search",
    execution_approval: dict | None = None,
) -> Path:
    timestamp = datetime.now(timezone.utc)
    snapshot = build_structured_search_snapshot(
        query_plan,
        query_results,
        deduped_results,
        report,
        timestamp,
        snapshot_type,
        execution_approval,
    )
    SEARCH_RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = SEARCH_RUN_LOG_DIR / structured_search_snapshot_filename(
        query_plan.get("input_snapshot") or {},
        timestamp,
        snapshot_type,
    )
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return snapshot_path
