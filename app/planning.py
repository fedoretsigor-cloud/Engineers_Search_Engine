import hashlib
import json

from app.domain_config import (
    PLANNER_MODE_RULE_BASED,
    QUERY_PLAN_MAX_RESULTS,
    QUERY_PLAN_REPORTING_FIELDS,
    QUERY_PLANNER_VERSION,
    search_domain_config_for,
)
from app.role_aliases import build_role_alias_plan, approved_role_aliases_from_plan


def quote_query_value(value: str) -> str:
    escaped_value = value.replace('"', '\\"')
    return f'"{escaped_value}"'


def build_stack_or(stack: list[str]) -> str:
    quoted_stack_values = [quote_query_value(item) for item in stack]
    if len(quoted_stack_values) == 1:
        return quoted_stack_values[0]

    return "(" + " OR ".join(quoted_stack_values) + ")"


def build_query_slot(
    query_id: str,
    category: str,
    purpose: str,
    role_phrase: str,
    location: str,
    technology: str | None = None,
    stack: list[str] | None = None,
) -> dict:
    quoted_location = quote_query_value(location)
    quoted_role_phrase = quote_query_value(role_phrase)
    query_parts = ["site:linkedin.com/in", "AND", quoted_role_phrase]
    uses_stack = stack or []

    if technology and technology.lower() not in role_phrase.lower():
        query_parts.extend(["AND", quote_query_value(technology)])

    if uses_stack:
        query_parts.extend(["AND", build_stack_or(uses_stack)])

    query_parts.extend(["AND", quoted_location])

    return {
        "id": query_id,
        "category": category,
        "purpose": purpose,
        "role_phrase": role_phrase,
        "query": " ".join(query_parts),
        "technology": technology,
        "uses_stack": uses_stack,
        "max_results": QUERY_PLAN_MAX_RESULTS,
    }


def generic_role_phrases(role_family: str, technology: str) -> list[str]:
    role_alias_plan = build_role_alias_plan(
        role_family=role_family,
        technology=technology,
    )
    return approved_role_aliases_from_plan(role_alias_plan)[:10]


def generic_planner_queries(
    normalized_request: dict,
    role_alias_plan: dict | None = None,
) -> list[dict]:
    role_family = normalized_request["role_family"]
    technology = normalized_request["technology"]
    if role_alias_plan:
        role_phrases = approved_role_aliases_from_plan(role_alias_plan)
    else:
        role_phrases = generic_role_phrases(role_family, technology)
    stack_focused_ids = {"Q07", "Q08", "Q09", "Q10"}
    queries: list[dict] = []

    for index in range(10):
        query_id = f"Q{index + 1:02d}"
        role_phrase = role_phrases[index % len(role_phrases)]
        uses_stack = query_id in stack_focused_ids
        category = "stack_focused" if uses_stack else "role_based"
        purpose = (
            "Find profiles that mention selected stack signals."
            if uses_stack
            else "Find profiles for the selected role, technology, and location."
        )
        queries.append(
            build_query_slot(
                query_id=query_id,
                category=category,
                purpose=purpose,
                role_phrase=role_phrase,
                location=normalized_request["location"],
                technology=technology,
                stack=normalized_request["stack"] if uses_stack else None,
            )
        )

    return queries


class RuleBasedQueryPlannerV1:
    version = QUERY_PLANNER_VERSION

    def build(self, normalized_request: dict) -> dict:
        location = normalized_request["location"]
        stack = normalized_request["stack"]
        domain_config = search_domain_config_for(
            normalized_request["role_family"],
            normalized_request["technology"],
        )
        planner_queries = domain_config.get("planner", {}).get("queries", [])
        role_alias_plan = build_role_alias_plan(
            role_family=normalized_request["role_family"],
            technology=normalized_request["technology"],
            configured_role_phrases=[
                query_config["role_phrase"]
                for query_config in planner_queries
                if query_config.get("role_phrase")
            ],
        )
        if planner_queries:
            queries = [
                build_query_slot(
                    query_config["id"],
                    query_config["category"],
                    query_config["purpose"],
                    query_config["role_phrase"],
                    location,
                    normalized_request["technology"],
                    stack if query_config.get("uses_selected_stack") else None,
                )
                for query_config in planner_queries
            ]
        else:
            queries = generic_planner_queries(normalized_request, role_alias_plan)

        return {
            "planner_version": self.version,
            "input_snapshot": normalized_request,
            "role_alias_plan": role_alias_plan,
            "queries": queries,
            "filters": {
                "linkedin_profiles_only": normalized_request["linkedin_profiles_only"],
                "location_filter_enabled": normalized_request["location_filter_enabled"],
            },
            "execution": {
                "mode": "sequential",
                "max_results_per_query": QUERY_PLAN_MAX_RESULTS,
            },
            "reporting": QUERY_PLAN_REPORTING_FIELDS,
        }


def query_plan_fingerprint_payload(query_plan: dict) -> dict:
    return {
        "planner_version": query_plan.get("planner_version"),
        "planner_mode": query_plan.get("planner_mode", PLANNER_MODE_RULE_BASED),
        "input_snapshot": query_plan.get("input_snapshot"),
        "role_alias_plan": query_plan.get("role_alias_plan"),
        "queries": query_plan.get("queries"),
        "filters": query_plan.get("filters"),
        "execution": query_plan.get("execution"),
        "reporting": query_plan.get("reporting"),
    }


def query_plan_fingerprint(query_plan: dict) -> str:
    payload = json.dumps(
        query_plan_fingerprint_payload(query_plan),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def add_query_plan_fingerprint(query_plan: dict) -> dict:
    return {
        **query_plan,
        "plan_fingerprint": query_plan_fingerprint(query_plan),
    }


def add_plan_validation_error(
    errors: list[dict[str, str]],
    field: str,
    code: str,
    message: str,
) -> None:
    errors.append({"field": field, "code": code, "message": message})


def planner_explanation_for_rule_based() -> str:
    return "Using bounded rule-based LinkedIn X-ray planner baseline."
