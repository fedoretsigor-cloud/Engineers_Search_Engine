import json
import os

import httpx


SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION = "search_brief_extractor_v2"
SEARCH_BRIEF_EXTRACTOR_MAX_COMPLETION_TOKENS = 900
SEARCH_BRIEF_EXTRACTOR_TIMEOUT_SECONDS = 30
DEFAULT_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def search_brief_extractor_system_prompt() -> str:
    return (
        "You extract a recruiter's initial candidate-search request into a bounded "
        "Search Brief draft. Return strict JSON only. You may extract meaning, but "
        "you must not validate, generate search queries, browse, call providers, "
        "access LinkedIn, scrape, automate profiles, message candidates, approve "
        "searches, perform account actions, or persist data."
    )


def search_brief_extractor_user_prompt(
    *,
    latest_message: str,
    language: str,
    previous_brief: dict | None = None,
) -> str:
    return json.dumps(
        {
            "task": (
                "Extract a raw SearchBriefExtractor v2 draft from the latest "
                "clean-state recruiter message."
            ),
            "required_output": {
                "schema_version": SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
                "draft_brief": {
                    "source_text": "original recruiter request text",
                    "role_family": "explicit IT/software/data/product/security/design/operations role or null",
                    "role_ambiguity": {
                        "is_ambiguous": "boolean",
                        "label": "ambiguous role label or null",
                        "options": ["safe role options when obvious"],
                        "clarification_question": "one targeted role question or null",
                    },
                    "technology": "main technical skill/platform/language/tool or null",
                    "stack": ["1-3 explicitly requested technical stack signals"],
                    "location": "target country/city/region/remote value or null",
                    "seniority": "optional seniority or null",
                    "must_have": ["required non-stack requirements"],
                    "nice_to_have": ["optional requirements"],
                    "domain_experience": ["business/domain context such as banking or fintech"],
                    "exclusions": [],
                    "search_depth": "standard or deep",
                    "profile_sources": ["linkedin_public"],
                    "notes": "safe non-instructional note or null",
                },
                "confidence": "high | medium | low",
                "reason_codes": ["short_snake_case"],
            },
            "latest_message": latest_message,
            "language": language,
            "previous_brief": previous_brief or {},
            "semantic_rules": [
                "Keep the requested candidate role in role_family.",
                "Do not convert a technology into the target role.",
                "Separate domain/business context from technical skills.",
                "Examples of domain/business context: banking, fintech, healthcare, ecommerce, telecom.",
                "Examples of technical skills: SQL, Java, Selenium, AWS, Terraform, Power BI.",
                "If a role label such as Analyst is ambiguous, set role_ambiguity.is_ambiguous to true.",
                "Do not invent missing role, technology, stack, or location values.",
                "Use English field values only.",
            ],
            "hard_boundaries": [
                "No query generation.",
                "No Tavily, Serper, SerpApi, or provider calls.",
                "No direct web-search bypass.",
                "No LinkedIn login.",
                "No LinkedIn scraping, profile automation, or restriction bypass.",
                "No candidate messaging or outreach.",
                "No user or third-party account actions.",
                "No search approval.",
                "No persistence.",
            ],
            "prompt_version": SEARCH_BRIEF_EXTRACTOR_PROMPT_VERSION,
        },
        ensure_ascii=False,
        indent=2,
    )


def search_brief_extractor_openai_payload(
    *,
    model: str,
    latest_message: str,
    language: str = "en",
    previous_brief: dict | None = None,
) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": search_brief_extractor_system_prompt()},
            {
                "role": "user",
                "content": search_brief_extractor_user_prompt(
                    latest_message=latest_message,
                    language=language,
                    previous_brief=previous_brief,
                ),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": SEARCH_BRIEF_EXTRACTOR_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }


async def run_openai_json_search_brief_extractor(
    *,
    latest_message: str,
    language: str = "en",
    previous_brief: dict | None = None,
    chat_completions_url: str | None = None,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, "openai_not_configured"

    payload = search_brief_extractor_openai_payload(
        model=model,
        latest_message=latest_message,
        language=language,
        previous_brief=previous_brief,
    )

    try:
        async with httpx.AsyncClient(timeout=SEARCH_BRIEF_EXTRACTOR_TIMEOUT_SECONDS) as client:
            response = await client.post(
                os.getenv(
                    "OPENAI_CHAT_COMPLETIONS_URL",
                    chat_completions_url or DEFAULT_OPENAI_CHAT_COMPLETIONS_URL,
                ),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return None, "openai_search_brief_extractor_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_search_brief_extractor_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_search_brief_extractor_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_search_brief_extractor_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_search_brief_extractor_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_search_brief_extractor_wrong_shape"

    return parsed_content, None
