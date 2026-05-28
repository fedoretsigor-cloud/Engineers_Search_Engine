import asyncio
import json
import os
from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from app import search_brief_extractor as extractor


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


async def main() -> None:
    assert_prompt_contract()
    assert_openai_payload_contract()
    await assert_missing_openai_config()
    await assert_openai_wrapper_parses_json()
    await assert_openai_wrapper_rejects_invalid_json()


if __name__ == "__main__":
    asyncio.run(main())
