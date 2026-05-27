MULTI_WAVE_DEFAULT_MAX_WAVES = 5
MULTI_WAVE_MAX_ALLOWED_WAVES = 7
MULTI_WAVE_DEFAULT_MIN_NEW_UNIQUE_PER_WAVE = 3
MULTI_WAVE_DEFAULT_PATIENCE = 2

SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION = "needs_clarification"
SEARCH_BRIEF_STATUS_READY_FOR_PLANNING = "ready_for_planning"
SEARCH_BRIEF_STATUSES = {
    SEARCH_BRIEF_STATUS_NEEDS_CLARIFICATION,
    SEARCH_BRIEF_STATUS_READY_FOR_PLANNING,
}

SEARCH_DEPTH_STANDARD = "standard"
SEARCH_DEPTH_DEEP = "deep"
SEARCH_DEPTH_VALUES = {SEARCH_DEPTH_STANDARD, SEARCH_DEPTH_DEEP}

PROFILE_SOURCE_LINKEDIN_PUBLIC = "linkedin_public"
PROFILE_SOURCE_VALUES = {PROFILE_SOURCE_LINKEDIN_PUBLIC}

PLANNER_MODE_RULE_BASED = "rule_based"
PLANNER_MODE_AI = "ai"
PLANNER_MODE_AI_WITH_FALLBACK = "ai_with_fallback"
PLANNER_MODES = {
    PLANNER_MODE_RULE_BASED,
    PLANNER_MODE_AI,
    PLANNER_MODE_AI_WITH_FALLBACK,
}

QUERY_PLANNER_VERSION = "rule_based_v1"
QUERY_PLAN_MAX_RESULTS = 20
QUERY_PLAN_REPORTING_FIELDS = [
    "queries_total",
    "queries_succeeded",
    "queries_failed",
    "raw_total",
    "normalized_total",
    "unique_profiles",
    "duplicates_removed",
    "displayed",
    "hidden_by_profile_filter",
    "hidden_by_location_filter",
    "rescued_by_header_location",
    "hidden_by_foreign_current_location",
    "weak_location_history_only",
    "unknown_non_country_domain_location",
    "location_filter_report",
    "query_contribution",
]

FORBIDDEN_AI_QUERY_TERMS = [
    "linkedin.com/login",
    "login",
    "password",
    "scrape",
    "scraping",
    "crawler",
    "bypass",
    "restriction bypass",
    "inmail",
    "send message",
    "message candidate",
    "contact candidate",
    "account",
]

AI_PLANNER_COVERAGE_POLICY_VERSION = "ai_planner_coverage_policy_v0"
AI_PLANNER_COVERAGE_NOT_CONFIGURED_WARNING = (
    "coverage_policy_not_configured: Strict AI planner coverage policy is not "
    "configured for this brief."
)
CANDIDATE_QUALITY_SCORE_VERSION = "candidate_quality_v1"
CANDIDATE_SENIORITY_CONFIG = {
    "junior": {
        "display": "Junior",
        "terms": ["Junior", "Jr", "Trainee", "Intern"],
    },
    "middle": {
        "display": "Middle",
        "terms": ["Middle", "Mid", "Mid-level"],
    },
    "senior": {
        "display": "Senior",
        "terms": ["Senior", "Sr"],
    },
    "leadership": {
        "display": "Lead",
        "terms": ["Team Lead", "Tech Lead", "Lead"],
    },
}
REVIEW_FLAG_TAXONOMY = {
    "role_missing": {
        "category": "role",
        "severity": "medium",
        "label": "Role not confirmed",
        "description": "Target or similar role was not found in candidate public text.",
        "affects_quality_score": True,
        "score_penalty_group": "role_fit",
    },
    "role_similar_only": {
        "category": "role",
        "severity": "low",
        "label": "Similar role only",
        "description": "Candidate role looks close, but it is not a direct target-role phrase.",
        "affects_quality_score": True,
        "score_penalty_group": "role_fit",
    },
    "role_from_snippet_only": {
        "category": "role",
        "severity": "low",
        "label": "Role from snippet",
        "description": "Role evidence was found only in lower-confidence snippet text.",
        "affects_quality_score": True,
        "score_penalty_group": "low_confidence_source",
    },
    "technology_missing": {
        "category": "technology",
        "severity": "medium",
        "label": "Technology not confirmed",
        "description": "Selected technology was not directly found in candidate public text.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_fit",
    },
    "technology_related_only": {
        "category": "technology",
        "severity": "low",
        "label": "Related technology only",
        "description": "Only a configured related technology signal was found.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_fit",
    },
    "technology_ambiguous": {
        "category": "technology",
        "severity": "high",
        "label": "Technology ambiguous",
        "description": "Technology evidence may indicate a false positive.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_false_positive",
    },
    "possible_technology_false_positive": {
        "category": "technology",
        "severity": "high",
        "label": "Possible technology false positive",
        "description": "Candidate text includes an exclude term that can look like the selected technology.",
        "affects_quality_score": True,
        "score_penalty_group": "technology_false_positive",
    },
    "selected_stack_missing": {
        "category": "stack",
        "severity": "medium",
        "label": "Stack not confirmed",
        "description": "Selected stack was not directly found in candidate public text.",
        "affects_quality_score": True,
        "score_penalty_group": "stack_fit",
    },
    "stack_from_query_source_only": {
        "category": "stack",
        "severity": "low",
        "label": "Stack only from query source",
        "description": "Candidate came from a stack-focused OR query, but no specific stack term was directly observed.",
        "affects_quality_score": True,
        "score_penalty_group": "stack_fit",
    },
    "stack_related_only": {
        "category": "stack",
        "severity": "low",
        "label": "Related stack only",
        "description": "Only a configured related stack signal was found.",
        "affects_quality_score": True,
        "score_penalty_group": "stack_fit",
    },
    "seniority_missing": {
        "category": "seniority",
        "severity": "info",
        "label": "Seniority not found",
        "description": "Seniority was not found in candidate public text.",
        "affects_quality_score": False,
        "score_penalty_group": None,
    },
    "seniority_ambiguous": {
        "category": "seniority",
        "severity": "low",
        "label": "Seniority ambiguous",
        "description": "Multiple seniority signals were found and should be reviewed.",
        "affects_quality_score": True,
        "score_penalty_group": "low_confidence_seniority",
    },
    "seniority_from_snippet_only": {
        "category": "seniority",
        "severity": "low",
        "label": "Seniority from snippet",
        "description": "Seniority was found only in lower-confidence snippet text.",
        "affects_quality_score": True,
        "score_penalty_group": "low_confidence_source",
    },
}

CANONICAL_ROLE_FAMILIES = {
    "backend developer": "Backend Developer",
}

KNOWN_BACKEND_TECHNOLOGIES = {
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "python": "Python",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "c#": "C#",
    "csharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    "go": "Go",
    "golang": "Go",
    "php": "PHP",
    "ruby": "Ruby",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "swift": "Swift",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue",
    "devops": "DevOps",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "salesforce": "Salesforce",
    "sap": "SAP",
}

IMPLEMENTED_BACKEND_TECHNOLOGIES = set(KNOWN_BACKEND_TECHNOLOGIES.values())

JAVA_STACK_VALUES = {
    "spring": "Spring",
    "sping": "Spring",
    "спринг": "Spring",
    "spring boot": "Spring Boot",
    "спринг бут": "Spring Boot",
    "hibernate": "Hibernate",
    "хайбернейт": "Hibernate",
    "хибернейт": "Hibernate",
    "kafka": "Kafka",
    "kafak": "Kafka",
    "кафка": "Kafka",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "aws": "AWS",
    "авс": "AWS",
    "docker": "Docker",
    "докер": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "кубернетес": "Kubernetes",
    "кубернетис": "Kubernetes",
    "кубер": "Kubernetes",
    "microservices": "Microservices",
    "микросервисы": "Microservices",
    "rest": "REST",
    "react": "React",
}

JAVA_STACK_TERMS = [
    "Spring",
    "Spring Boot",
    "Hibernate",
    "Kafka",
    "PostgreSQL",
    "AWS",
    "Docker",
    "Kubernetes",
    "Microservices",
    "REST",
    "React",
]

SEARCH_DOMAIN_CONFIG = {
    "Backend Developer": {
        "Java": {
            "planner": {
                "queries": [
                    {
                        "id": "Q01",
                        "category": "role_based",
                        "purpose": "Find broad Java Developer profiles for the selected location.",
                        "role_phrase": "Java Developer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q02",
                        "category": "role_based",
                        "purpose": "Find Java Software Engineer profiles for the selected location.",
                        "role_phrase": "Java Software Engineer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q03",
                        "category": "backend_role",
                        "purpose": "Find Java Backend Engineer profiles for the selected location.",
                        "role_phrase": "Java Backend Engineer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q04",
                        "category": "role_based",
                        "purpose": "Find Java Engineer profiles for the selected location.",
                        "role_phrase": "Java Engineer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q05",
                        "category": "role_based",
                        "purpose": "Find Java Programmer profiles for the selected location.",
                        "role_phrase": "Java Programmer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q06",
                        "category": "role_based",
                        "purpose": "Find Java Application Developer profiles for the selected location.",
                        "role_phrase": "Java Application Developer",
                        "uses_selected_stack": False,
                    },
                    {
                        "id": "Q07",
                        "category": "stack_focused",
                        "purpose": "Find Java Developer profiles that mention selected stack signals.",
                        "role_phrase": "Java Developer",
                        "uses_selected_stack": True,
                    },
                    {
                        "id": "Q08",
                        "category": "stack_focused",
                        "purpose": "Find Java Engineer profiles that mention selected stack signals.",
                        "role_phrase": "Java Engineer",
                        "uses_selected_stack": True,
                    },
                    {
                        "id": "Q09",
                        "category": "stack_focused",
                        "purpose": "Find Java Backend Engineer profiles that mention selected stack signals.",
                        "role_phrase": "Java Backend Engineer",
                        "uses_selected_stack": True,
                    },
                    {
                        "id": "Q10",
                        "category": "stack_focused",
                        "purpose": "Find Java Application Developer profiles that mention selected stack signals.",
                        "role_phrase": "Java Application Developer",
                        "uses_selected_stack": True,
                    },
                ]
            },
            "quality": {
                "technology": {
                    "exact_terms": ["Java"],
                    "exclude_terms": ["JavaScript"],
                    "related_terms": ["Kotlin", "Scala"],
                },
                "stack": {
                    "allowed_terms": JAVA_STACK_TERMS,
                    "related_terms": [],
                },
            },
        },
    },
}

AI_PLANNER_COVERAGE_POLICIES = [
    {
        "policy_id": "java_backend_ukraine_standard_v0",
        "policy_version": AI_PLANNER_COVERAGE_POLICY_VERSION,
        "role_family": "Backend Developer",
        "technology": "Java",
        "location": "Ukraine",
        "search_depth": SEARCH_DEPTH_STANDARD,
        "expected_query_count": 10,
        "role_based_min": 6,
        "stack_focused_min": 4,
        "min_role_phrase_diversity": 5,
        "max_ai_plan_revision_attempts": 1,
    }
]

LOCATION_FILTER_CONFIG = {
    "ukraine": {
        "label": "Ukraine",
        "linkedin_domains": ["ua.linkedin.com"],
        "target_location_terms": [
            "Ukraine",
            "Kyiv",
            "Kiev",
            "Lviv",
            "Kharkiv",
            "Odesa",
            "Odessa",
            "Dnipro",
            "Vinnytsia",
            "Zaporizhzhia",
            "Chernivtsi",
            "Ternopil",
            "Ivano-Frankivsk",
        ],
    }
}


def generic_quality_config_for(technology: str, stack: list[str] | None = None) -> dict:
    selected_stack = stack or []
    return {
        "quality": {
            "technology": {
                "exact_terms": [technology] if technology else [],
                "exclude_terms": [],
                "related_terms": [],
            },
            "stack": {
                "allowed_terms": selected_stack,
                "related_terms": [],
            },
        }
    }


def search_domain_config_for(
    role_family: str,
    technology: str,
    stack: list[str] | None = None,
) -> dict:
    configured = SEARCH_DOMAIN_CONFIG.get(role_family, {}).get(technology)
    if configured is not None:
        return configured
    return generic_quality_config_for(technology, stack)


def location_filter_config_for(location: str) -> dict | None:
    return LOCATION_FILTER_CONFIG.get(location.strip().lower())
