import json
import os
import re

import httpx

from app.search_validation import add_validation_error
from app.text_utils import compact_spaces, contains_cyrillic_text, normalize_text_value


HELP_SMALLTALK_RESOLVER_VERSION = "help_smalltalk_resolver_v1"
HELP_SMALLTALK_MAX_COMPLETION_TOKENS = 350
HELP_SMALLTALK_TIMEOUT_SECONDS = 20
DEFAULT_OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

HELP_SMALLTALK_INTENT_HELP_OR_ONBOARDING = "help_or_onboarding"
HELP_SMALLTALK_INTENT_SMALL_TALK = "small_talk"
HELP_SMALLTALK_INTENT_CANDIDATE_SEARCH = "candidate_search"
HELP_SMALLTALK_INTENT_OFF_TOPIC = "off_topic"
HELP_SMALLTALK_INTENT_UNCLEAR = "unclear"
HELP_SMALLTALK_INTENTS = {
    HELP_SMALLTALK_INTENT_HELP_OR_ONBOARDING,
    HELP_SMALLTALK_INTENT_SMALL_TALK,
    HELP_SMALLTALK_INTENT_CANDIDATE_SEARCH,
    HELP_SMALLTALK_INTENT_OFF_TOPIC,
    HELP_SMALLTALK_INTENT_UNCLEAR,
}

HELP_SMALLTALK_CONFIDENCE_HIGH = "high"
HELP_SMALLTALK_CONFIDENCE_MEDIUM = "medium"
HELP_SMALLTALK_CONFIDENCE_LOW = "low"
HELP_SMALLTALK_CONFIDENCES = {
    HELP_SMALLTALK_CONFIDENCE_HIGH,
    HELP_SMALLTALK_CONFIDENCE_MEDIUM,
    HELP_SMALLTALK_CONFIDENCE_LOW,
}

HELP_SMALLTALK_ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "intent",
    "confidence",
    "response_style",
    "evidence",
    "should_preserve_brief",
    "can_mutate_search_brief",
    "can_execute",
    "reason_code",
}
HELP_SMALLTALK_RESPONSE_STYLES = {"friendly", "concise", "neutral"}
SAFE_REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


def help_smalltalk_system_prompt() -> str:
    return (
        "You classify a short harmless recruiter-chat message for a "
        "human-approved IT sourcing assistant. Return strict JSON only. You may "
        "classify help/onboarding or small-talk intent, but you must not create "
        "or mutate Search Briefs, generate queries, browse, call providers, "
        "access LinkedIn, scrape, automate profiles, message candidates, approve "
        "searches, perform account actions, or persist data."
    )


def help_smalltalk_user_prompt(*, latest_message: str, language: str) -> str:
    return json.dumps(
        {
            "task": (
                "Classify whether the latest clean-state or current-state "
                "message is harmless help/onboarding or small talk."
            ),
            "required_output": {
                "schema_version": HELP_SMALLTALK_RESOLVER_VERSION,
                "intent": "help_or_onboarding | small_talk | candidate_search | off_topic | unclear",
                "confidence": "high | medium | low",
                "response_style": "friendly | concise | neutral",
                "evidence": ["short evidence from latest_message only"],
                "should_preserve_brief": True,
                "can_mutate_search_brief": False,
                "can_execute": False,
                "reason_code": "short_snake_case",
            },
            "latest_message": latest_message,
            "language": language,
            "classification_rules": [
                "Classify messages like 'Can you help me?', 'I need help', 'What can you do?', or 'How does this work?' as help_or_onboarding.",
                "Classify harmless greetings, thanks, and presence checks as small_talk.",
                "Classify messages with actual role, technology, location, or requirement criteria as candidate_search.",
                "Classify unrelated requests such as weather, jokes, news, or restaurants as off_topic.",
                "Use unclear when the message is noise or too ambiguous.",
                "Never add Search Brief fields. Never infer role, technology, stack, or location.",
            ],
            "hard_boundaries": [
                "No Search Brief mutation.",
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
            "resolver_version": HELP_SMALLTALK_RESOLVER_VERSION,
        },
        ensure_ascii=False,
        indent=2,
    )


def help_smalltalk_openai_payload(
    *,
    model: str,
    latest_message: str,
    language: str = "en",
) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": help_smalltalk_system_prompt()},
            {
                "role": "user",
                "content": help_smalltalk_user_prompt(
                    latest_message=latest_message,
                    language=language,
                ),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": HELP_SMALLTALK_MAX_COMPLETION_TOKENS,
        "response_format": {"type": "json_object"},
    }


async def run_openai_json_help_smalltalk_intent(
    *,
    latest_message: str,
    language: str = "en",
    chat_completions_url: str | None = None,
) -> tuple[dict | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    if not api_key or not model:
        return None, "openai_not_configured"

    payload = help_smalltalk_openai_payload(
        model=model,
        latest_message=latest_message,
        language=language,
    )

    try:
        async with httpx.AsyncClient(timeout=HELP_SMALLTALK_TIMEOUT_SECONDS) as client:
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
        return None, "openai_help_smalltalk_timeout"
    except httpx.HTTPStatusError as exc:
        return None, f"openai_help_smalltalk_http_{exc.response.status_code}"
    except httpx.HTTPError:
        return None, "openai_help_smalltalk_request_failed"

    data = response.json()
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        return None, "openai_help_smalltalk_empty_content"

    try:
        parsed_content = json.loads(content)
    except json.JSONDecodeError:
        return None, "openai_help_smalltalk_invalid_json"
    if not isinstance(parsed_content, dict):
        return None, "openai_help_smalltalk_wrong_shape"

    return parsed_content, None


def safe_help_smalltalk_text_value(value: object, max_length: int = 120) -> str | None:
    if value is not None and not isinstance(value, str):
        return None
    text = normalize_text_value(value)
    if not text:
        return None
    text = compact_spaces(text).strip(" .,:;\"'")
    if not text or len(text) > max_length:
        return None
    if contains_cyrillic_text(text):
        return None
    if re.search(r"https?://|www\.|@|<|>|`|{|}|\[|\]", text, flags=re.IGNORECASE):
        return None
    return text


def safe_help_smalltalk_text_list(
    value: object,
    *,
    max_items: int = 3,
    item_max_length: int = 100,
) -> tuple[list[str], str | None]:
    if value is None:
        return [], None
    if not isinstance(value, list):
        return [], "help_smalltalk_list_wrong_shape"

    values: list[str] = []
    for raw_item in value:
        safe_item = safe_help_smalltalk_text_value(
            raw_item,
            max_length=item_max_length,
        )
        if not safe_item:
            return [], "help_smalltalk_unsafe_value"
        if safe_item not in values:
            values.append(safe_item)
    if len(values) > max_items:
        return [], "help_smalltalk_too_many_values"
    return values, None


def safe_optional_bool(value: object) -> tuple[bool | None, bool]:
    if value is None:
        return None, True
    if isinstance(value, bool):
        return value, True
    return None, False


def normalize_help_smalltalk_reason_code(value: object) -> str:
    raw_code = safe_help_smalltalk_text_value(value, max_length=64)
    if not raw_code:
        return "validated"
    code = raw_code.lower().replace("-", "_").replace(" ", "_")
    return code if SAFE_REASON_CODE_PATTERN.match(code) else "validated"


def normalized_help_text(text: object) -> str:
    normalized = normalize_text_value(text).lower()
    normalized = normalized.replace("'", "")
    normalized = re.sub(r"[^a-z0-9+#./&() _-]+", " ", normalized)
    return compact_spaces(normalized)


def has_concrete_search_criteria(text: str) -> bool:
    concrete_patterns = [
        r"\bdeveloper\b",
        r"\bengineer\b",
        r"\bqa\b",
        r"\btester\b",
        r"\banalyst\b",
        r"\bproject manager\b",
        r"\bproduct manager\b",
        r"\bdevops\b",
        r"\bjava\b",
        r"\bpython\b",
        r"\bsql\b",
        r"\bselenium\b",
        r"\bcucumber\b",
        r"\baws\b",
        r"\bazure\b",
        r"\bukraine\b",
        r"\bpoland\b",
        r"\bspain\b",
        r"\bcanada\b",
        r"\bgermany\b",
        r"\bremote\b",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in concrete_patterns)


def should_run_help_smalltalk_resolver(text: object) -> bool:
    normalized = normalized_help_text(text)
    if not normalized or len(normalized) > 140:
        return False
    if has_concrete_search_criteria(normalized):
        return False

    exact_phrases = {
        "can you help",
        "can you help me",
        "could you help",
        "could you help me",
        "help",
        "help me",
        "help please",
        "i need help",
        "need help",
        "i want help",
        "what can you do",
        "how can you help",
        "how does this work",
        "how to start",
        "what should i write",
        "help me find candidates",
        "can you help me find candidates",
        "can you help me search candidates",
        "can you help me source candidates",
    }
    if normalized in exact_phrases:
        return True

    patterns = [
        r"^(can|could|would|will) you help( me)?$",
        r"^(i )?(need|want) help( please)?$",
        r"^help( me)?( please)?$",
        r"^(what can you do|how can you help|how does this work)$",
        r"^(help me|can you help me) (find|search|source) candidates$",
    ]
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in patterns)


def deterministic_help_smalltalk_intent(text: object) -> dict | None:
    if not should_run_help_smalltalk_resolver(text):
        return None
    return {
        "resolver_version": HELP_SMALLTALK_RESOLVER_VERSION,
        "schema_version": HELP_SMALLTALK_RESOLVER_VERSION,
        "intent": HELP_SMALLTALK_INTENT_HELP_OR_ONBOARDING,
        "confidence": HELP_SMALLTALK_CONFIDENCE_HIGH,
        "response_style": "friendly",
        "evidence": [safe_help_smalltalk_text_value(text, max_length=100) or "help"],
        "should_preserve_brief": True,
        "can_mutate_search_brief": False,
        "can_execute": False,
        "reason_code": "deterministic_help_opening",
    }


def validate_help_smalltalk_intent_output(
    llm_output: dict | None,
    *,
    latest_message: str,
) -> tuple[dict | None, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    if not isinstance(llm_output, dict):
        add_validation_error(errors, "help_smalltalk", "Help/small-talk output must be an object.")
        return None, errors

    unknown_keys = set(llm_output) - HELP_SMALLTALK_ALLOWED_TOP_LEVEL_KEYS
    if unknown_keys:
        add_validation_error(errors, "help_smalltalk", "Help/small-talk output contains unsupported fields.")

    schema_version = safe_help_smalltalk_text_value(
        llm_output.get("schema_version"),
        max_length=80,
    )
    if schema_version != HELP_SMALLTALK_RESOLVER_VERSION:
        add_validation_error(errors, "schema_version", "Unsupported help/small-talk schema version.")

    intent = safe_help_smalltalk_text_value(llm_output.get("intent"), max_length=32)
    if intent not in HELP_SMALLTALK_INTENTS:
        add_validation_error(errors, "intent", "Unsupported help/small-talk intent.")

    confidence = safe_help_smalltalk_text_value(
        llm_output.get("confidence"),
        max_length=24,
    )
    if confidence not in HELP_SMALLTALK_CONFIDENCES:
        add_validation_error(errors, "confidence", "Unsupported help/small-talk confidence.")
    elif confidence == HELP_SMALLTALK_CONFIDENCE_LOW:
        add_validation_error(errors, "confidence", "Help/small-talk confidence is too low.")

    response_style = (
        safe_help_smalltalk_text_value(llm_output.get("response_style"), max_length=24)
        or "friendly"
    )
    if response_style not in HELP_SMALLTALK_RESPONSE_STYLES:
        add_validation_error(errors, "response_style", "Unsupported response style.")

    evidence, evidence_error = safe_help_smalltalk_text_list(llm_output.get("evidence"))
    if evidence_error:
        add_validation_error(errors, "evidence", "Help/small-talk evidence is invalid.")

    should_preserve_brief, valid_preserve = safe_optional_bool(
        llm_output.get("should_preserve_brief")
    )
    can_mutate, valid_mutate = safe_optional_bool(llm_output.get("can_mutate_search_brief"))
    can_execute, valid_execute = safe_optional_bool(llm_output.get("can_execute"))
    if not valid_preserve or should_preserve_brief is not True:
        add_validation_error(errors, "should_preserve_brief", "Help/small-talk must preserve current brief.")
    if not valid_mutate or can_mutate is not False:
        add_validation_error(errors, "can_mutate_search_brief", "Help/small-talk must not mutate Search Brief.")
    if not valid_execute or can_execute is not False:
        add_validation_error(errors, "can_execute", "Help/small-talk must not execute actions.")

    if intent in {
        HELP_SMALLTALK_INTENT_HELP_OR_ONBOARDING,
        HELP_SMALLTALK_INTENT_SMALL_TALK,
    } and not should_run_help_smalltalk_resolver(latest_message):
        add_validation_error(errors, "intent", "Help/small-talk intent lacks source-message support.")

    if errors:
        return None, errors

    return {
        "resolver_version": HELP_SMALLTALK_RESOLVER_VERSION,
        "schema_version": schema_version,
        "intent": intent,
        "confidence": confidence,
        "response_style": response_style,
        "evidence": evidence,
        "should_preserve_brief": True,
        "can_mutate_search_brief": False,
        "can_execute": False,
        "reason_code": normalize_help_smalltalk_reason_code(
            llm_output.get("reason_code")
        ),
    }, []
