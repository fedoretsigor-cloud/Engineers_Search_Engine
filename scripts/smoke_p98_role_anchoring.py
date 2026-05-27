import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.candidate_quality import build_candidate_quality
from app.planning import RuleBasedQueryPlannerV1
from app.role_aliases import is_technology_only_role_phrase


def normalized_request(
    role_family: str,
    technology: str,
    stack: list[str],
    location: str = "Spain",
) -> dict:
    return {
        "role_family": role_family,
        "technology": technology,
        "stack": stack,
        "location": location,
        "search_depth": "standard",
        "linkedin_profiles_only": True,
        "location_filter_enabled": False,
    }


def role_phrases(query_plan: dict) -> list[str]:
    return [query["role_phrase"] for query in query_plan["queries"]]


def assert_no_role_drift(
    *,
    role_family: str,
    technology: str,
    stack: list[str],
    forbidden_phrases: set[str],
) -> dict:
    query_plan = RuleBasedQueryPlannerV1().build(
        normalized_request(role_family, technology, stack)
    )
    phrases = role_phrases(query_plan)

    assert len(query_plan["queries"]) == 10, phrases
    assert query_plan["role_alias_plan"]["approved_aliases"], query_plan
    assert not forbidden_phrases.intersection(phrases), phrases
    for phrase in phrases:
        assert not is_technology_only_role_phrase(
            phrase,
            role_family=role_family,
            technology=technology,
        ), phrase

    return query_plan


def assert_generic_planner_blocks_technology_only_roles() -> None:
    assert_no_role_drift(
        role_family="QA Automation",
        technology="Java",
        stack=["Java"],
        forbidden_phrases={
            "Java Developer",
            "Java Engineer",
            "Java Software Engineer",
            "Java Specialist",
            "Java Consultant",
        },
    )
    assert_no_role_drift(
        role_family="Data Analyst",
        technology="Python",
        stack=["SQL"],
        forbidden_phrases={"Python Developer", "Python Engineer"},
    )
    assert_no_role_drift(
        role_family="DevOps",
        technology="AWS",
        stack=["Kubernetes"],
        forbidden_phrases={"AWS Developer", "AWS Engineer"},
    )
    assert_no_role_drift(
        role_family="Product Manager",
        technology="AI",
        stack=["Analytics"],
        forbidden_phrases={"AI Developer", "AI Engineer"},
    )


def assert_configured_backend_java_baseline_is_preserved() -> None:
    query_plan = RuleBasedQueryPlannerV1().build(
        normalized_request(
            "Backend Developer",
            "Java",
            ["Spring"],
            location="Ukraine",
        )
    )
    phrases = role_phrases(query_plan)
    aliases = query_plan["role_alias_plan"]["approved_aliases"]

    assert query_plan["role_alias_plan"]["source"] == "configured_domain"
    assert "Java Developer" in phrases
    assert "Java Developer" in aliases


def assert_candidate_scoring_uses_role_anchored_aliases() -> None:
    query_plan = RuleBasedQueryPlannerV1().build(
        normalized_request("QA Automation", "Java", ["Java"])
    )
    query_sources = [
        {
            "id": "Q01",
            "role_phrase": query_plan["queries"][0]["role_phrase"],
            "category": query_plan["queries"][0]["category"],
            "uses_stack": query_plan["queries"][0]["uses_stack"],
        }
    ]

    java_developer = {
        "name": "Sample Candidate",
        "title": "Junior Java Developer - LinkedIn",
        "headline": "Junior Java Developer",
        "snippet": "Junior Java Developer with Java experience in Spain.",
        "raw_content": "Java Developer",
        "review_flags": [],
    }
    java_developer_quality = build_candidate_quality(
        java_developer,
        query_sources,
        query_plan,
    )
    assert java_developer_quality["role_fit"] == "missing_role", java_developer_quality
    assert "role_missing" in java_developer_quality["review_flags"]
    assert java_developer_quality["quality_score"] < 100, java_developer_quality

    qa_automation = {
        "name": "Sample QA",
        "title": "QA Automation Engineer - LinkedIn",
        "headline": "QA Automation Engineer with Java skills",
        "snippet": "QA Automation Engineer using Java in Spain.",
        "raw_content": "QA Automation Engineer Java",
        "review_flags": [],
    }
    qa_quality = build_candidate_quality(qa_automation, query_sources, query_plan)
    assert qa_quality["role_fit"] == "target_or_close_role", qa_quality


def main() -> None:
    assert_generic_planner_blocks_technology_only_roles()
    assert_configured_backend_java_baseline_is_preserved()
    assert_candidate_scoring_uses_role_anchored_aliases()
    print("P9.8 role anchoring smoke passed")


if __name__ == "__main__":
    main()
