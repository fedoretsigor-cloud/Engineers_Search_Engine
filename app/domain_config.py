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

CANONICAL_ROLE_FAMILIES = {
    "backend developer": "Backend Developer",
}

KNOWN_BACKEND_TECHNOLOGIES = {
    "java": "Java",
    "python": "Python",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "c#": "C#",
    "csharp": "C#",
    "go": "Go",
    "golang": "Go",
    "php": "PHP",
}

IMPLEMENTED_BACKEND_TECHNOLOGIES = {"Java"}

JAVA_STACK_VALUES = {
    "spring": "Spring",
    "spring boot": "Spring Boot",
    "hibernate": "Hibernate",
    "kafka": "Kafka",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "aws": "AWS",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "microservices": "Microservices",
    "rest": "REST",
}

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


def location_filter_config_for(location: str) -> dict | None:
    return LOCATION_FILTER_CONFIG.get(location.strip().lower())
