import copy
import json
import os
import re

import httpx

from app.text_utils import normalize_text_value


OPENAI_AGENT_WORDING_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_AGENT_WORDING_MAX_COMPLETION_TOKENS = 800
AGENT_WORDING_MODE_LLM_ASSISTED = "llm_assisted"
AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK = "deterministic_fallback"
AGENT_WORDING_FALLBACK_NOT_CONFIGURED = "openai_not_configured"
AGENT_WORDING_TIMEOUT_SECONDS = 8.0
AGENT_WORDING_USE_CASE_AGENT_PLAN = "agent_plan"
AGENT_WORDING_USE_CASE_AGENT_RESPONSE = "agent_response"
AGENT_WORDING_USE_CASE_RECRUITER_CHAT_ONBOARDING = "recruiter_chat_onboarding"
AGENT_WORDING_TAXONOMY_VERSION = "phase_7_agent_message_taxonomy_v0"
AGENT_WORDING_FACTS_CONTRACT_VERSION = "phase_7_message_facts_contract_v0"
AGENT_WORDING_STYLE_POLICY_VERSION = "phase_7_agent_wording_style_policy_v0"
AGENT_WORDING_ROUTING_POLICY_VERSION = "phase_7_llm_routing_gating_policy_v0"
AGENT_WORDING_PAYLOAD_CONTRACT_VERSION = "phase_7_bounded_llm_payload_contract_v0"
AGENT_WORDING_PROMPT_CONTRACT_VERSION = "phase_7_bounded_llm_prompt_contract_v0"
AGENT_WORDING_PROMPT_VERSION = "phase_7_agent_wording_prompt_v0"
AGENT_WORDING_VALIDATOR_VERSION = "phase_7_wording_validator_v0"
AGENT_WORDING_DETERMINISTIC_BUILDER_VERSION = "phase_7_agent_messages_v0"


def agent_wording_hard_boundaries() -> list[str]:
    return [
        "No web search by the wording helper.",
        "No direct web-search by the agent outside the approved backend pipeline.",
        "No LinkedIn login.",
        "No LinkedIn scraping or restriction bypass.",
        "No candidate messaging or automatic outreach.",
        "No user or third-party account actions.",
        "No autonomous execution.",
        "Do not change facts, counts, actions, filters, scoring, location logic, dedupe, planner behavior, fingerprints, or approval state.",
        "Do not invent candidates or claim direct LinkedIn inspection.",
    ]


def agent_wording_system_prompt() -> str:
    return (
        "You are a bounded wording helper for a human-approved recruiting agent. "
        "Return one valid JSON object only. Your only job is to make the provided "
        "deterministic Agent Plan, Agent Response, or onboarding text clearer and more natural. "
        "You must not browse, search, call tools, access LinkedIn, log in, scrape, "
        "message candidates, act on accounts, change facts, change counts, change "
        "actions, change approval rules, or create executable next steps."
    )


def agent_wording_user_prompt(payload: dict) -> str:
    return json.dumps(
        {
            "task": "Rewrite only allowed user-facing text fields.",
            "required_output_shape": {
                "message": "string",
                "warnings": ["optional short strings"],
                "limitations": [
                    {
                        "kind": "existing limitation kind only",
                        "message": "optional rewritten limitation message",
                    }
                ],
            },
            "rules": [
                "Return JSON only.",
                "Use the requested language.",
                "Use only facts present in the payload.",
                "Do not add numbers outside allowed_numbers.",
                "Do not include query text.",
                "Do not create or change suggested_next_actions.",
                "Do not make any next step executable.",
                "Do not repeat prohibited behavior as a capability.",
            ],
            "payload": payload,
        },
        ensure_ascii=False,
        indent=2,
    )


def agent_wording_has_openai_config() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"))


async def run_openai_json_agent_wording(
    payload: dict,
    *,
    chat_completions_url: str = OPENAI_AGENT_WORDING_CHAT_COMPLETIONS_URL,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, AGENT_WORDING_FALLBACK_NOT_CONFIGURED

    request_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": agent_wording_system_prompt()},
            {"role": "user", "content": agent_wording_user_prompt(payload)},
        ],
        "temperature": 0.2,
        "max_completion_tokens": OPENAI_AGENT_WORDING_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }

    try:
        async with httpx.AsyncClient(timeout=AGENT_WORDING_TIMEOUT_SECONDS) as client:
            response = await client.post(
                os.getenv("OPENAI_CHAT_COMPLETIONS_URL", chat_completions_url),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        return None, "openai_wording_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_wording_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_wording_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_wording_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_wording_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_wording_wrong_shape"

    return parsed_content, None


def agent_wording_number_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(
            r"(?<![A-Za-z0-9_])-?\d+(?:\.\d+)?(?![A-Za-z0-9_])",
            value or "",
        )
    }


def agent_wording_allowed_numbers(value: object) -> set[str]:
    numbers: set[str] = set()
    if isinstance(value, bool) or value is None:
        return numbers
    if isinstance(value, int):
        numbers.add(str(value))
        return numbers
    if isinstance(value, float):
        numbers.add(str(value))
        if value.is_integer():
            numbers.add(str(int(value)))
        return numbers
    if isinstance(value, str):
        return agent_wording_number_tokens(value)
    if isinstance(value, list):
        for item in value:
            numbers.update(agent_wording_allowed_numbers(item))
        return numbers
    if isinstance(value, dict):
        for item in value.values():
            numbers.update(agent_wording_allowed_numbers(item))
        return numbers
    return numbers


def agent_wording_text_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(agent_wording_text_values(item))
        return values
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(agent_wording_text_values(item))
        return values
    return []


def agent_wording_has_disallowed_key(value: object) -> bool:
    disallowed_keys = {
        "summary_facts",
        "quality_notes",
        "suggested_next_actions",
        "proposed_action",
        "brief_fingerprint",
        "plan_fingerprint",
        "fingerprint",
        "counts",
        "approval_state",
        "approval_required",
        "requires_approval",
        "executable",
        "planner_mode",
        "filters",
        "scoring",
        "dedupe",
        "location_logic",
        "query",
        "queries",
        "query_plan",
        "candidate",
        "candidates",
        "url",
        "urls",
    }

    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in disallowed_keys:
                return True
            if agent_wording_has_disallowed_key(item):
                return True
    if isinstance(value, list):
        return any(agent_wording_has_disallowed_key(item) for item in value)
    return False


def agent_wording_language_matches(text: str, language: str) -> bool:
    has_cyrillic = bool(re.search(r"[\u0400-\u04ff]", text or ""))
    if language == "ru":
        return has_cyrillic
    return not has_cyrillic


def agent_wording_has_prohibited_content(text: str) -> bool:
    prohibited_patterns = [
        r"https?://\S+",
        r"\bwww\.\S+",
        r"\bsite:linkedin\.com\b",
        r"\blinkedin\.com/in/\S*",
        r"\bdirect\s+web[- ]search\b",
        r"\bdirect\s+linkedin\s+(search|inspection|check|review)\b",
        r"\bsearched\s+linkedin\s+directly\b",
        r"\b(opened|viewed|visited|checked|inspected).{0,50}linkedin\b",
        r"\blinkedin.{0,50}\b(opened|viewed|visited|checked|inspected)\b",
        r"\blinkedin.{0,40}\b(log\s?in|login|sign in)\b",
        r"\b(log\s?in|login|sign in)\b.{0,40}linkedin",
        r"\b(scrape|scraping|scraper|crawl|crawler|bypass)\b",
        r"\binmail\b",
        r"\bsend.{0,30}(message|dm|email|outreach).{0,40}(candidates?|profiles?)\b",
        r"\bmessage.{0,40}(candidates?|profiles?)\b",
        r"\boutreach.{0,40}(candidates?|profiles?)\b",
        r"\bcontact.{0,40}(candidates?|profiles?)\b",
        r"\b(use|used).{0,30}(my|user|recruiter).{0,30}account\b",
        r"\bi\s+(will|can|am going to)\s+(run|execute|search|contact|message|scrape|log in)\b",
        r"\bi\s+(ran|executed|searched|contacted|messaged|scraped|logged in)\b",
        r"\bperfect\s+candidates?\b",
        r"\bguarantee(d|s)?\b",
        r"\u044f\s+(\u0437\u0430\u043f\u0443\u0449\u0443|\u0437\u0430\u043f\u0443\u0441\u0442\u0438\u043b|\u043d\u0430\u043f\u0438\u0441\u0430\u043b|\u0441\u0432\u044f\u0437\u0430\u043b\u0441\u044f)",
        r"\u0441\u043a\u0440\u0435\u0439\u043f|\u043f\u0430\u0440\u0441.{0,40}linkedin",
        r"\u0432\u043e\u0439\u0434.{0,40}linkedin|linkedin.{0,40}\u0432\u043e\u0439\u0434",
        r"\u0430\u043a\u043a\u0430\u0443\u043d\u0442",
        r"\u0433\u0430\u0440\u0430\u043d\u0442\u0438\u0440|\u0438\u0434\u0435\u0430\u043b\u044c\u043d",
    ]
    return any(re.search(pattern, text or "", re.IGNORECASE) for pattern in prohibited_patterns)


def normalize_agent_wording_warnings(value: object) -> list[str] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None

    warnings: list[str] = []
    for item in value[:5]:
        if not isinstance(item, str):
            return None
        normalized_item = normalize_text_value(item)
        if normalized_item:
            warnings.append(normalized_item)
    return warnings


def normalize_agent_wording_limitations(value: object) -> list[dict[str, str]] | None:
    if value is None:
        return []
    if not isinstance(value, list):
        return None

    limitations: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            return None
        kind = normalize_text_value(str(item.get("kind") or ""))
        message = normalize_text_value(str(item.get("message") or ""))
        if not kind or not message:
            return None
        limitations.append({"kind": kind, "message": message})
    return limitations


def validate_agent_wording_output(
    llm_output: dict,
    *,
    language: str,
    allowed_numbers: set[str],
    wording_use_case: str | None = None,
    existing_limitation_kinds: set[str] | None = None,
) -> tuple[dict | None, str | None]:
    if agent_wording_has_disallowed_key(llm_output):
        return None, "llm_output_disallowed_fields"

    allowed_keys = {"message", "warnings", "limitations"}
    if any(key not in allowed_keys for key in llm_output):
        return None, "llm_output_unknown_fields"

    message_value = llm_output.get("message")
    if not isinstance(message_value, str):
        return None, "llm_output_missing_message"
    message = normalize_text_value(message_value)
    if not message:
        return None, "llm_output_missing_message"

    warnings = normalize_agent_wording_warnings(llm_output.get("warnings"))
    if warnings is None:
        return None, "llm_output_invalid_warnings"

    limitations = normalize_agent_wording_limitations(llm_output.get("limitations"))
    if limitations is None:
        return None, "llm_output_invalid_limitations"

    if wording_use_case == AGENT_WORDING_USE_CASE_AGENT_PLAN and limitations:
        return None, "llm_output_agent_plan_limitations_not_allowed"

    if existing_limitation_kinds is not None:
        for limitation in limitations:
            if limitation["kind"] not in existing_limitation_kinds:
                return None, "llm_output_new_limitation_kind"

    combined_text = "\n".join(
        [message] + warnings + [limitation["message"] for limitation in limitations]
    )
    if not agent_wording_language_matches(combined_text, language):
        return None, "llm_output_wrong_language"
    if agent_wording_has_prohibited_content(combined_text):
        return None, "llm_output_unsafe_content"

    output_numbers = agent_wording_number_tokens(combined_text)
    if not output_numbers.issubset(allowed_numbers):
        return None, "llm_output_disallowed_numbers"

    return {
        "message": message,
        "warnings": warnings,
        "limitations": limitations,
    }, None


def agent_wording_provenance_source(message_type: str) -> dict[str, str]:
    if message_type == AGENT_WORDING_USE_CASE_AGENT_PLAN:
        return {
            "source_owner": "Agent Plan backend; bounded wording overlay",
            "source_object": "/api/agent/plan agent_plan.message",
        }
    if message_type == AGENT_WORDING_USE_CASE_AGENT_RESPONSE:
        return {
            "source_owner": "deterministic Agent Response backend; bounded wording overlay",
            "source_object": "approved search response agent_response.message",
        }
    return {
        "source_owner": "bounded wording overlay",
        "source_object": message_type,
    }


def build_agent_wording_provenance(
    *,
    message_type: str,
    language: str,
    wording_mode: str,
    fallback_reason: str | None = None,
    no_call_reason: str | None = None,
    model: str | None = None,
) -> dict[str, str]:
    provenance = {
        "message_type": message_type,
        "surface": "chat",
        **agent_wording_provenance_source(message_type),
        "language": language,
        "wording_mode": wording_mode,
        "taxonomy_version": AGENT_WORDING_TAXONOMY_VERSION,
        "facts_contract_version": AGENT_WORDING_FACTS_CONTRACT_VERSION,
        "style_policy_version": AGENT_WORDING_STYLE_POLICY_VERSION,
        "routing_policy_version": AGENT_WORDING_ROUTING_POLICY_VERSION,
        "payload_contract_version": AGENT_WORDING_PAYLOAD_CONTRACT_VERSION,
        "prompt_contract_version": AGENT_WORDING_PROMPT_CONTRACT_VERSION,
        "prompt_version": AGENT_WORDING_PROMPT_VERSION,
        "validator_version": AGENT_WORDING_VALIDATOR_VERSION,
        "deterministic_builder_version": AGENT_WORDING_DETERMINISTIC_BUILDER_VERSION,
    }
    if fallback_reason:
        provenance["fallback_reason"] = fallback_reason
    if no_call_reason:
        provenance["no_call_reason"] = no_call_reason
    if model:
        provenance["model"] = model
    return provenance


def with_agent_wording_metadata(
    value: dict,
    *,
    message_type: str,
    language: str,
    wording_mode: str,
    fallback_reason: str | None = None,
    no_call_reason: str | None = None,
    model: str | None = None,
    llm_warnings: list[str] | None = None,
) -> dict:
    updated_value = copy.deepcopy(value)
    updated_value["wording_mode"] = wording_mode
    updated_value["fallback_reason"] = fallback_reason
    updated_value["llm_warnings"] = llm_warnings or []
    updated_value["wording_provenance"] = build_agent_wording_provenance(
        message_type=message_type,
        language=language,
        wording_mode=wording_mode,
        fallback_reason=fallback_reason,
        no_call_reason=no_call_reason,
        model=model,
    )
    return updated_value


def agent_plan_wording_payload(
    agent_plan: dict,
    normalized_request: dict,
    language: str,
) -> dict:
    payload = {
        "wording_use_case": AGENT_WORDING_USE_CASE_AGENT_PLAN,
        "language": language,
        "deterministic_message": agent_plan.get("message"),
        "normalized_brief": agent_plan.get("input_snapshot") or {},
        "normalized_structured_request": normalized_request,
        "proposed_action": agent_plan.get("proposed_action") or {},
        "approval_requirement": {
            "build_plan_requires_approval": False,
            "search_execution_requires_explicit_approval": True,
        },
        "hard_boundaries": agent_wording_hard_boundaries(),
    }
    payload["allowed_numbers"] = sorted(agent_wording_allowed_numbers(payload))
    return payload


def agent_response_wording_payload(agent_response: dict) -> dict:
    payload = {
        "wording_use_case": AGENT_WORDING_USE_CASE_AGENT_RESPONSE,
        "language": agent_response.get("language"),
        "deterministic_message": agent_response.get("message"),
        "summary_facts": agent_response.get("summary_facts") or {},
        "quality_notes": agent_response.get("quality_notes") or [],
        "limitations": agent_response.get("limitations") or [],
        "suggested_next_actions": agent_response.get("suggested_next_actions") or [],
        "requires_approval_for_execution": agent_response.get(
            "requires_approval_for_execution"
        ),
        "hard_boundaries": agent_wording_hard_boundaries(),
    }
    payload["allowed_numbers"] = sorted(agent_wording_allowed_numbers(payload))
    return payload


async def apply_llm_wording_to_agent_plan(
    agent_plan: dict,
    normalized_request: dict,
    language: str,
    *,
    wording_runner=run_openai_json_agent_wording,
) -> dict:
    if not agent_wording_has_openai_config():
        return with_agent_wording_metadata(
            agent_plan,
            message_type=AGENT_WORDING_USE_CASE_AGENT_PLAN,
            language=language,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
            no_call_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
        )

    payload = agent_plan_wording_payload(agent_plan, normalized_request, language)
    model = normalize_text_value(os.getenv("OPENAI_MODEL") or "") or None
    llm_output, fallback_reason = await wording_runner(payload)
    if fallback_reason or llm_output is None:
        return with_agent_wording_metadata(
            agent_plan,
            message_type=AGENT_WORDING_USE_CASE_AGENT_PLAN,
            language=language,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=fallback_reason or "openai_wording_empty_output",
            model=model,
        )

    validated_output, validation_reason = validate_agent_wording_output(
        llm_output,
        language=language,
        allowed_numbers=set(payload["allowed_numbers"]),
        wording_use_case=AGENT_WORDING_USE_CASE_AGENT_PLAN,
    )
    if validation_reason or validated_output is None:
        return with_agent_wording_metadata(
            agent_plan,
            message_type=AGENT_WORDING_USE_CASE_AGENT_PLAN,
            language=language,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=validation_reason or "llm_output_invalid",
            model=model,
        )

    updated_agent_plan = with_agent_wording_metadata(
        agent_plan,
        message_type=AGENT_WORDING_USE_CASE_AGENT_PLAN,
        language=language,
        wording_mode=AGENT_WORDING_MODE_LLM_ASSISTED,
        model=model,
        llm_warnings=validated_output["warnings"],
    )
    updated_agent_plan["message"] = validated_output["message"]
    return updated_agent_plan


async def apply_llm_wording_to_agent_response(
    agent_response: dict,
    *,
    wording_runner=run_openai_json_agent_wording,
) -> dict:
    language = agent_response.get("language") or "en"
    if not agent_wording_has_openai_config():
        return with_agent_wording_metadata(
            agent_response,
            message_type=AGENT_WORDING_USE_CASE_AGENT_RESPONSE,
            language=language,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
            no_call_reason=AGENT_WORDING_FALLBACK_NOT_CONFIGURED,
        )

    payload = agent_response_wording_payload(agent_response)
    model = normalize_text_value(os.getenv("OPENAI_MODEL") or "") or None
    existing_limitation_kinds = {
        str(item.get("kind"))
        for item in agent_response.get("limitations") or []
        if isinstance(item, dict) and item.get("kind")
    }
    llm_output, fallback_reason = await wording_runner(payload)
    if fallback_reason or llm_output is None:
        return with_agent_wording_metadata(
            agent_response,
            message_type=AGENT_WORDING_USE_CASE_AGENT_RESPONSE,
            language=language,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=fallback_reason or "openai_wording_empty_output",
            model=model,
        )

    validated_output, validation_reason = validate_agent_wording_output(
        llm_output,
        language=language,
        allowed_numbers=set(payload["allowed_numbers"]),
        wording_use_case=AGENT_WORDING_USE_CASE_AGENT_RESPONSE,
        existing_limitation_kinds=existing_limitation_kinds,
    )
    if validation_reason or validated_output is None:
        return with_agent_wording_metadata(
            agent_response,
            message_type=AGENT_WORDING_USE_CASE_AGENT_RESPONSE,
            language=language,
            wording_mode=AGENT_WORDING_MODE_DETERMINISTIC_FALLBACK,
            fallback_reason=validation_reason or "llm_output_invalid",
            model=model,
        )

    updated_agent_response = with_agent_wording_metadata(
        agent_response,
        message_type=AGENT_WORDING_USE_CASE_AGENT_RESPONSE,
        language=language,
        wording_mode=AGENT_WORDING_MODE_LLM_ASSISTED,
        model=model,
        llm_warnings=validated_output["warnings"],
    )
    updated_agent_response["message"] = validated_output["message"]

    if validated_output["limitations"]:
        limitation_messages = {
            item["kind"]: item["message"]
            for item in validated_output["limitations"]
        }
        updated_limitations = []
        for limitation in updated_agent_response.get("limitations") or []:
            updated_limitation = dict(limitation)
            kind = updated_limitation.get("kind")
            if kind in limitation_messages:
                updated_limitation["message"] = limitation_messages[kind]
            updated_limitations.append(updated_limitation)
        updated_agent_response["limitations"] = updated_limitations

    return updated_agent_response


