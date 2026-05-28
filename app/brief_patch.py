BRIEF_PATCH_ADD_STACK = "add_stack"
BRIEF_PATCH_REMOVE_STACK = "remove_stack"
BRIEF_PATCH_REPLACE_STACK = "replace_stack"
BRIEF_PATCH_ADD_MUST_HAVE = "add_must_have"
BRIEF_PATCH_REMOVE_MUST_HAVE = "remove_must_have"
BRIEF_PATCH_REPLACE_MUST_HAVE = "replace_must_have"
BRIEF_PATCH_SET_SENIORITY = "set_seniority"
BRIEF_PATCH_SET_SEARCH_DEPTH = "set_search_depth"
BRIEF_PATCH_SET_LOCATION = "set_location"
BRIEF_PATCH_RECONFIRM_FIELD = "reconfirm_field"
BRIEF_PATCH_UNSUPPORTED = "unsupported"
BRIEF_PATCH_NOOP = "noop"


def build_brief_patch(
    *,
    source_message: str,
    operations: list[dict],
    requires_clarification: bool = False,
    assistant_message: str | None = None,
) -> dict:
    return {
        "operations": operations,
        "source_message": source_message,
        "requires_clarification": requires_clarification,
        "assistant_message": assistant_message,
    }


