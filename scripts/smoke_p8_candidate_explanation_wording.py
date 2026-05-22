import asyncio
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))


from app.candidate_explanation_wording import (  # noqa: E402
    CANDIDATE_EXPLANATION_WORDING_REQUEST_VERSION,
    CANDIDATE_EXPLANATION_WORDING_USE_CASE,
    EXPLANATION_REASON_CODES,
    REASON_SECTIONS,
    WORDING_SAFE_FACT_KEYS,
    build_candidate_explanation_wording_response,
    build_model_payload,
    candidate_explanation_request_fingerprint,
    flatten_renderable_reasons,
    sanitize_candidate_explanation_wording_request,
)


def sample_request() -> dict:
    request = {
        "wording_use_case": CANDIDATE_EXPLANATION_WORDING_USE_CASE,
        "request_payload_contract_version": CANDIDATE_EXPLANATION_WORDING_REQUEST_VERSION,
        "target_language": "en",
        "workspace_run_id": "workspace:test:run-1",
        "wording_target_key": "wtk-1-1",
        "request_explanation_fingerprint": "sha256:" + ("0" * 64),
        "explanation_version": "candidate_explanation_v1",
        "source": "deterministic_workspace_facts",
        "summary": "Candidate has strong returned fit signals.",
        "positive_signals": [
            {
                "reason_key": "positive_signals[0]:quality_score_high",
                "section": "positive_signals",
                "code": "quality_score_high",
                "label": "Quality score is high",
                "facts": {"score": 86, "bucket": "high"},
            },
            {
                "reason_key": "positive_signals[1]:stack_confirmed",
                "section": "positive_signals",
                "code": "stack_confirmed",
                "label": "Visible stack terms: Spring, Kafka",
                "facts": {"terms": ["Spring", "Kafka"], "source": "candidate_text"},
            },
        ],
        "cautions": [
            {
                "reason_key": "cautions[0]:seniority_unknown",
                "section": "cautions",
                "code": "seniority_unknown",
                "label": "Seniority is unknown",
                "facts": {},
            }
        ],
        "evidence_items": [
            {
                "reason_key": "evidence_items[0]:query_source",
                "section": "evidence_items",
                "code": "query_source",
                "label": "Matched query sources: Q01",
                "facts": {"ids": ["Q01"], "categories": ["role_based"]},
            }
        ],
    }
    request["request_explanation_fingerprint"] = candidate_explanation_request_fingerprint(
        request
    )
    return request


def assert_contract_snapshot() -> None:
    assert set(WORDING_SAFE_FACT_KEYS.keys()) == EXPLANATION_REASON_CODES
    assert REASON_SECTIONS == ("positive_signals", "cautions", "evidence_items")


def assert_request_validation() -> None:
    request = sample_request()
    sanitized, errors = sanitize_candidate_explanation_wording_request(request)
    assert not errors
    assert sanitized is not None
    assert sanitized["request_explanation_fingerprint"] == request[
        "request_explanation_fingerprint"
    ]
    assert "role" not in sanitized["positive_signals"][0]["facts"]

    bad_extra = dict(request)
    bad_extra["candidate_id"] = "https://www.linkedin.com/in/secret"
    sanitized, errors = sanitize_candidate_explanation_wording_request(bad_extra)
    assert sanitized is None
    assert errors[0]["code"] == "unknown_request_field"

    bad_fingerprint = dict(request)
    bad_fingerprint["summary"] = "Candidate has changed text."
    sanitized, errors = sanitize_candidate_explanation_wording_request(bad_fingerprint)
    assert sanitized is None
    assert errors[0]["code"] == "fingerprint_mismatch"

    bad_fact = sample_request()
    bad_fact["positive_signals"][0]["facts"]["profile_url"] = "https://linkedin.com/in/x"
    bad_fact["request_explanation_fingerprint"] = candidate_explanation_request_fingerprint(
        bad_fact
    )
    sanitized, errors = sanitize_candidate_explanation_wording_request(bad_fact)
    assert sanitized is None
    assert errors[0]["code"] == "unknown_fact_key"


def assert_model_payload_excludes_runtime_binding() -> None:
    request = sample_request()
    sanitized, errors = sanitize_candidate_explanation_wording_request(request)
    assert sanitized is not None and not errors
    payload = build_model_payload(sanitized)
    serialized = str(payload)
    assert "workspace_run_id" not in serialized
    assert "wording_target_key" not in serialized
    assert "request_explanation_fingerprint" not in serialized
    assert "candidate_id" not in serialized
    assert "linkedin.com" not in serialized.lower()
    assert "86" in payload["allowed_numbers"]


async def assert_response_paths() -> None:
    request = sample_request()
    called = False

    async def should_not_call(_payload: dict) -> tuple[dict | None, str | None]:
      nonlocal called
      called = True
      return None, "should_not_call"

    no_config_response = await build_candidate_explanation_wording_response(
        request,
        wording_runner=should_not_call,
        openai_configured=lambda: False,
    )
    assert no_config_response["ok"] is True
    assert no_config_response["wording_mode"] == "deterministic_fallback"
    assert no_config_response["fallback_reason"] == "openai_not_configured"
    assert no_config_response["wording_overlay"] is None
    assert called is False

    async def fake_success(model_payload: dict) -> tuple[dict | None, str | None]:
        reasons = []
        explanation = model_payload["deterministic_explanation"]
        for section in REASON_SECTIONS:
            for reason in explanation[section]:
                reasons.append(
                    {
                        "reason_key": reason["reason_key"],
                        "code": reason["code"],
                        "label": f"Reviewed signal: {reason['label']}",
                    }
                )
        return {
            "summary": "Returned evidence shows a strong candidate fit.",
            "reasons": reasons,
        }, None

    success_response = await build_candidate_explanation_wording_response(
        request,
        wording_runner=fake_success,
        openai_configured=lambda: True,
    )
    assert success_response["ok"] is True
    assert success_response["wording_mode"] == "llm_assisted"
    assert success_response["wording_overlay"]["summary"].startswith("Returned evidence")
    assert success_response["backend_wording_cache_key"].startswith("sha256:")
    assert success_response["workspace_run_id"] == request["workspace_run_id"]
    assert success_response["wording_target_key"] == request["wording_target_key"]

    async def fake_bad_number(model_payload: dict) -> tuple[dict | None, str | None]:
        reasons = [
            {
                "reason_key": reason["reason_key"],
                "code": reason["code"],
                "label": reason["label"],
            }
            for reason in flatten_renderable_reasons(
                model_payload["deterministic_explanation"]
            )
        ]
        return {"summary": "This candidate scored 99.", "reasons": reasons}, None

    fallback_response = await build_candidate_explanation_wording_response(
        request,
        wording_runner=fake_bad_number,
        openai_configured=lambda: True,
    )
    assert fallback_response["ok"] is True
    assert fallback_response["wording_mode"] == "deterministic_fallback"
    assert fallback_response["fallback_reason"] == "llm_output_disallowed_numbers"
    assert fallback_response["wording_overlay"] is None

    unsupported_language = dict(request)
    unsupported_language["target_language"] = "ru"
    unsupported_language["request_explanation_fingerprint"] = (
        candidate_explanation_request_fingerprint(unsupported_language)
    )
    response = await build_candidate_explanation_wording_response(
        unsupported_language,
        wording_runner=should_not_call,
        openai_configured=lambda: True,
    )
    assert response["fallback_reason"] == "unsupported_language"


def assert_route_no_network() -> None:
    from app import main

    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    client = TestClient(main.app)
    response = client.post(
        "/api/candidate-workspace/explanation-wording",
        json=sample_request(),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["wording_overlay"] is None
    assert payload["fallback_reason"] == "openai_not_configured"


def run_smoke() -> None:
    assert_contract_snapshot()
    assert_request_validation()
    assert_model_payload_excludes_runtime_binding()
    asyncio.run(assert_response_paths())
    assert_route_no_network()


if __name__ == "__main__":
    run_smoke()
    print("P8 candidate explanation wording smoke passed")
