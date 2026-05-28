import asyncio
import json
import os
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import search_brief_extractor as extractor
from app import main as app_main
from app.schemas import RecruiterChatMessage, RecruiterChatTurnRequest


def assert_prompt_contract() -> None:
    system_prompt = extractor.search_brief_extractor_system_prompt()
    user_prompt = extractor.search_brief_extractor_user_prompt(
        latest_message="I need Analyst in Canada with banking domain experience and SQL skills.",
        language="en",
    )
    payload = json.loads(user_prompt)

    assert extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION in user_prompt, user_prompt
    assert "No query generation." in user_prompt, user_prompt
    assert "No Tavily, Serper, SerpApi, or provider calls." in user_prompt, user_prompt
    assert "No LinkedIn login." in user_prompt, user_prompt
    assert "No persistence." in user_prompt, user_prompt
    assert "must not validate" in system_prompt, system_prompt
    assert payload["required_output"]["draft_brief"]["role_family"], payload
    assert payload["required_output"]["draft_brief"]["role_ambiguity"], payload
    assert payload["required_output"]["draft_brief"]["domain_experience"], payload
    assert payload["required_output"]["draft_brief"]["technology"], payload
    assert "Separate domain/business context from technical skills." in payload["semantic_rules"], payload


def assert_openai_payload_contract() -> None:
    payload = extractor.search_brief_extractor_openai_payload(
        model="test-model",
        latest_message="Find QA Automation in Spain with Java and Selenium.",
        language="en",
    )
    assert payload["model"] == "test-model", payload
    assert payload["temperature"] == 0, payload
    assert payload["response_format"] == {"type": "json_object"}, payload
    assert payload["max_completion_tokens"] == extractor.SEARCH_BRIEF_EXTRACTOR_MAX_COMPLETION_TOKENS, payload
    assert payload["messages"][0]["role"] == "system", payload
    assert payload["messages"][1]["role"] == "user", payload


def valid_raw_extractor_output() -> dict:
    return {
        "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        "draft_brief": {
            "source_text": "I need Analyst in Canada with banking domain experience and SQL skills.",
            "role_family": "Analyst",
            "role_ambiguity": {
                "is_ambiguous": True,
                "label": "Analyst",
                "options": ["Data Analyst", "Business Analyst", "Systems Analyst"],
                "clarification_question": "Which Analyst role should the search target?",
            },
            "technology": "SQL",
            "stack": ["SQL"],
            "location": "Canada",
            "seniority": None,
            "must_have": [],
            "nice_to_have": [],
            "domain_experience": ["banking domain experience"],
            "exclusions": [],
            "search_depth": "standard",
            "profile_sources": ["linkedin_public"],
            "notes": None,
        },
        "confidence": "high",
        "reason_codes": ["extracted_multi_signal_request"],
    }


def assert_validator_accepts_and_separates_domain_context() -> None:
    validated, errors = extractor.validate_search_brief_extractor_output(
        valid_raw_extractor_output()
    )
    assert errors == [], errors
    assert validated is not None, validated
    normalized_brief = validated["normalized_brief"]
    assert validated["validator_version"] == "search_brief_extractor_validator_v1", validated
    assert normalized_brief["role_family"] == "Analyst", normalized_brief
    assert normalized_brief["technology"] == "SQL", normalized_brief
    assert normalized_brief["stack"] == ["SQL"], normalized_brief
    assert normalized_brief["location"] == "Canada", normalized_brief
    assert "banking domain experience" in normalized_brief["must_have"], normalized_brief
    assert "banking domain experience" in validated["domain_experience"], validated
    assert validated["role_ambiguity"]["is_ambiguous"] is True, validated
    assert "role_family" in validated["clarification_targets"], validated
    assert normalized_brief["brief_status"] == "needs_clarification", normalized_brief


def assert_validator_rejects_domain_as_technology() -> None:
    raw = valid_raw_extractor_output()
    raw["draft_brief"]["technology"] = "Banking domain"
    raw["draft_brief"]["domain_experience"] = []
    validated, errors = extractor.validate_search_brief_extractor_output(raw)
    assert validated is None, validated
    assert any(error["field"] == "technology" for error in errors), errors


def assert_validator_rejects_unsafe_values() -> None:
    raw = valid_raw_extractor_output()
    raw["draft_brief"]["location"] = "https://example.com"
    validated, errors = extractor.validate_search_brief_extractor_output(raw)
    assert validated is None, validated
    assert any(error["field"] == "location" for error in errors), errors


def assert_validator_rejects_low_confidence_and_unknown_fields() -> None:
    raw = valid_raw_extractor_output()
    raw["confidence"] = "low"
    raw["extra"] = "not allowed"
    raw["draft_brief"]["extra"] = "not allowed"
    validated, errors = extractor.validate_search_brief_extractor_output(raw)
    assert validated is None, validated
    assert any(error["field"] == "confidence" for error in errors), errors
    assert any(error["field"] == "extractor_output" for error in errors), errors
    assert any(error["field"] == "draft_brief" for error in errors), errors


def assert_validator_rejects_too_many_stack_items() -> None:
    raw = valid_raw_extractor_output()
    raw["draft_brief"]["stack"] = ["SQL", "AWS", "Terraform", "Power BI"]
    validated, errors = extractor.validate_search_brief_extractor_output(raw)
    assert validated is None, validated
    assert any(error["field"] == "stack" for error in errors), errors


async def assert_missing_openai_config() -> None:
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    old_model = os.environ.pop("OPENAI_MODEL", None)
    try:
        parsed, error = await extractor.run_openai_json_search_brief_extractor(
            latest_message="Find QA Automation in Spain with Java.",
            language="en",
        )
        assert parsed is None, parsed
        assert error == "openai_not_configured", error
    finally:
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key
        if old_model is not None:
            os.environ["OPENAI_MODEL"] = old_model


class FakeResponse:
    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


class FakeAsyncClient:
    last_request: dict | None = None
    next_content = "{}"

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, headers: dict, json: dict) -> FakeResponse:
        FakeAsyncClient.last_request = {
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": self.timeout,
        }
        return FakeResponse(FakeAsyncClient.next_content)


async def assert_openai_wrapper_parses_json() -> None:
    old_key = os.environ.get("OPENAI_API_KEY")
    old_model = os.environ.get("OPENAI_MODEL")
    old_client = extractor.httpx.AsyncClient
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["OPENAI_MODEL"] = "test-model"
    FakeAsyncClient.next_content = json.dumps(
        {
            "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
            "draft_brief": {
                "role_family": "QA Automation",
                "technology": "Java",
                "stack": ["Selenium"],
                "location": "Spain",
                "domain_experience": [],
            },
            "confidence": "high",
            "reason_codes": ["extracted"],
        }
    )
    extractor.httpx.AsyncClient = FakeAsyncClient
    try:
        parsed, error = await extractor.run_openai_json_search_brief_extractor(
            latest_message="Find QA Automation in Spain with Java and Selenium.",
            language="en",
            chat_completions_url="https://example.test/chat",
        )
        assert error is None, error
        assert parsed is not None, parsed
        assert parsed["draft_brief"]["role_family"] == "QA Automation", parsed
        assert FakeAsyncClient.last_request is not None
        assert FakeAsyncClient.last_request["url"] == "https://example.test/chat"
        assert FakeAsyncClient.last_request["json"]["response_format"] == {"type": "json_object"}
        assert "Bearer test-key" == FakeAsyncClient.last_request["headers"]["Authorization"]
    finally:
        extractor.httpx.AsyncClient = old_client
        if old_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = old_key
        if old_model is None:
            os.environ.pop("OPENAI_MODEL", None)
        else:
            os.environ["OPENAI_MODEL"] = old_model


async def assert_openai_wrapper_rejects_invalid_json() -> None:
    old_key = os.environ.get("OPENAI_API_KEY")
    old_model = os.environ.get("OPENAI_MODEL")
    old_client = extractor.httpx.AsyncClient
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["OPENAI_MODEL"] = "test-model"
    FakeAsyncClient.next_content = "not json"
    extractor.httpx.AsyncClient = FakeAsyncClient
    try:
        parsed, error = await extractor.run_openai_json_search_brief_extractor(
            latest_message="Find QA Automation in Spain with Java.",
            language="en",
        )
        assert parsed is None, parsed
        assert error == "openai_search_brief_extractor_invalid_json", error
    finally:
        extractor.httpx.AsyncClient = old_client
        if old_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = old_key
        if old_model is None:
            os.environ.pop("OPENAI_MODEL", None)
        else:
            os.environ["OPENAI_MODEL"] = old_model


def recruiter_chat_request(message: str) -> RecruiterChatTurnRequest:
    return RecruiterChatTurnRequest(
        messages=[RecruiterChatMessage(role="user", content=message)],
        language="en",
    )


async def assert_clean_state_chat_uses_validated_extractor_for_qa_role() -> None:
    old_extractor = app_main.run_openai_json_search_brief_extractor
    old_legacy_chat = app_main.run_openai_json_recruiter_chat

    async def fake_extractor(**kwargs):
        assert kwargs["latest_message"] == "I need QA Automation in Spain with Java skills"
        return {
            "schema_version": extractor.SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
            "draft_brief": {
                "source_text": kwargs["latest_message"],
                "role_family": "QA Automation",
                "role_ambiguity": {
                    "is_ambiguous": False,
                    "label": None,
                    "options": [],
                    "clarification_question": None,
                },
                "technology": "Java",
                "stack": ["Java"],
                "location": "Spain",
                "seniority": None,
                "must_have": [],
                "nice_to_have": [],
                "domain_experience": [],
                "exclusions": [],
                "search_depth": "standard",
                "profile_sources": ["linkedin_public"],
                "notes": None,
            },
            "confidence": "high",
            "reason_codes": ["clean_state_extraction"],
        }, None

    async def fail_legacy_chat(*args, **kwargs):
        raise AssertionError("legacy recruiter chat parser should not run for clean state")

    app_main.run_openai_json_search_brief_extractor = fake_extractor
    app_main.run_openai_json_recruiter_chat = fail_legacy_chat
    try:
        response = await app_main.recruiter_chat_turn_response(
            recruiter_chat_request("I need QA Automation in Spain with Java skills")
        )
        normalized_brief = response["normalized_brief"]
        assert response["ok"] is True, response
        assert response["state"] == "ready_for_planning", response
        assert normalized_brief["role_family"] == "QA Automation", normalized_brief
        assert normalized_brief["technology"] == "Java", normalized_brief
        assert normalized_brief["stack"] == ["Java"], normalized_brief
        assert normalized_brief["location"] == "Spain", normalized_brief
    finally:
        app_main.run_openai_json_search_brief_extractor = old_extractor
        app_main.run_openai_json_recruiter_chat = old_legacy_chat


async def assert_clean_state_chat_preserves_domain_and_role_ambiguity() -> None:
    old_extractor = app_main.run_openai_json_search_brief_extractor
    old_legacy_chat = app_main.run_openai_json_recruiter_chat

    async def fake_extractor(**kwargs):
        return valid_raw_extractor_output(), None

    async def fail_legacy_chat(*args, **kwargs):
        raise AssertionError("legacy recruiter chat parser should not run for clean state")

    app_main.run_openai_json_search_brief_extractor = fake_extractor
    app_main.run_openai_json_recruiter_chat = fail_legacy_chat
    try:
        response = await app_main.recruiter_chat_turn_response(
            recruiter_chat_request(
                "I need Analyst in Canada with banking domain experience and SQL skills."
            )
        )
        normalized_brief = response["normalized_brief"]
        assert response["ok"] is True, response
        assert response["state"] == "needs_clarification", response
        assert normalized_brief["role_family"] == "Analyst", normalized_brief
        assert normalized_brief["technology"] == "SQL", normalized_brief
        assert normalized_brief["stack"] == ["SQL"], normalized_brief
        assert normalized_brief["location"] == "Canada", normalized_brief
        assert "banking domain experience" in normalized_brief["must_have"], normalized_brief
        assert response["next_question"], response
    finally:
        app_main.run_openai_json_search_brief_extractor = old_extractor
        app_main.run_openai_json_recruiter_chat = old_legacy_chat


async def assert_clean_state_chat_rejects_invalid_extractor_without_legacy_fallback() -> None:
    old_extractor = app_main.run_openai_json_search_brief_extractor
    old_legacy_chat = app_main.run_openai_json_recruiter_chat

    async def fake_extractor(**kwargs):
        raw = valid_raw_extractor_output()
        raw["draft_brief"]["technology"] = "Banking domain"
        raw["draft_brief"]["domain_experience"] = []
        return raw, None

    async def fail_legacy_chat(*args, **kwargs):
        raise AssertionError("legacy recruiter chat parser should not run after validator rejection")

    app_main.run_openai_json_search_brief_extractor = fake_extractor
    app_main.run_openai_json_recruiter_chat = fail_legacy_chat
    try:
        response = await app_main.recruiter_chat_turn_response(
            recruiter_chat_request(
                "I need Analyst in Canada with banking domain experience and SQL skills."
            )
        )
        assert response["ok"] is False, response
        assert response["state"] == "needs_clarification", response
        assert any(
            error["field"] == "technology"
            for error in response["validation_errors"]
        ), response
    finally:
        app_main.run_openai_json_search_brief_extractor = old_extractor
        app_main.run_openai_json_recruiter_chat = old_legacy_chat


async def assert_clean_state_intent_role_label_does_not_bypass_extractor() -> None:
    old_extractor = app_main.run_openai_json_search_brief_extractor
    old_legacy_chat = app_main.run_openai_json_recruiter_chat
    old_intent_classifier = app_main.classify_recruiter_chat_intent_response

    async def fake_intent_classifier(*args, **kwargs):
        return {
            "intent": "candidate_search",
            "role_domain": "it_software",
            "role_support_status": "supported",
            "role_label": "Legacy Backend Developer",
            "pending_action_intent": "unclear",
            "field_intent": "unclear",
            "unsupported_role_label": None,
            "confidence": "high",
            "response_language": "en",
        }

    async def fake_extractor(**kwargs):
        return valid_raw_extractor_output(), None

    async def fail_legacy_chat(*args, **kwargs):
        raise AssertionError("legacy recruiter chat parser should not run for clean state")

    app_main.classify_recruiter_chat_intent_response = fake_intent_classifier
    app_main.run_openai_json_search_brief_extractor = fake_extractor
    app_main.run_openai_json_recruiter_chat = fail_legacy_chat
    try:
        response = await app_main.recruiter_chat_turn_response(
            recruiter_chat_request(
                "I told you role Analyst in Canada with banking domain experience and SQL skills."
            )
        )
        normalized_brief = response["normalized_brief"]
        assert response["ok"] is True, response
        assert normalized_brief["role_family"] == "Analyst", normalized_brief
        assert normalized_brief["role_family"] != "Legacy Backend Developer", normalized_brief
        assert normalized_brief["technology"] == "SQL", normalized_brief
        assert normalized_brief["location"] == "Canada", normalized_brief
    finally:
        app_main.classify_recruiter_chat_intent_response = old_intent_classifier
        app_main.run_openai_json_search_brief_extractor = old_extractor
        app_main.run_openai_json_recruiter_chat = old_legacy_chat


async def main() -> None:
    assert_prompt_contract()
    assert_openai_payload_contract()
    assert_validator_accepts_and_separates_domain_context()
    assert_validator_rejects_domain_as_technology()
    assert_validator_rejects_unsafe_values()
    assert_validator_rejects_low_confidence_and_unknown_fields()
    assert_validator_rejects_too_many_stack_items()
    await assert_missing_openai_config()
    await assert_openai_wrapper_parses_json()
    await assert_openai_wrapper_rejects_invalid_json()
    await assert_clean_state_chat_uses_validated_extractor_for_qa_role()
    await assert_clean_state_chat_preserves_domain_and_role_ambiguity()
    await assert_clean_state_chat_rejects_invalid_extractor_without_legacy_fallback()
    await assert_clean_state_intent_role_label_does_not_bypass_extractor()


if __name__ == "__main__":
    asyncio.run(main())
