import hashlib
import json

from app.domain_config import (
    PLANNER_MODE_RULE_BASED,
    QUERY_PLAN_MAX_RESULTS,
    QUERY_PLAN_REPORTING_FIELDS,
    QUERY_PLANNER_VERSION,
    search_domain_config_for,
)


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
    stack: list[str] | None = None,
) -> dict:
    quoted_location = quote_query_value(location)
    quoted_role_phrase = quote_query_value(role_phrase)
    query_parts = ["site:linkedin.com/in", "AND", quoted_role_phrase]
    uses_stack = stack or []

    if uses_stack:
        query_parts.extend(["AND", build_stack_or(uses_stack)])

    query_parts.extend(["AND", quoted_location])

    return {
        "id": query_id,
        "category": category,
        "purpose": purpose,
        "role_phrase": role_phrase,
        "query": " ".join(query_parts),
        "uses_stack": uses_stack,
        "max_results": QUERY_PLAN_MAX_RESULTS,
    }


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
        queries = [
            build_query_slot(
                query_config["id"],
                query_config["category"],
                query_config["purpose"],
                query_config["role_phrase"],
                location,
                stack if query_config.get("uses_selected_stack") else None,
            )
            for query_config in planner_queries
        ]

        return {
            "planner_version": self.version,
            "input_snapshot": normalized_request,
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
    return "Using tested Java Backend rule-based planner baseline."
