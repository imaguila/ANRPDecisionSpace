EXCLUDE_EXACT = {
    "id",
    "highlight",
    "label",
    "highlight_label"
}

EXCLUDE_PREFIXES = (
    "req_",
    "stcov_"
)


def is_excluded_column(col_name, extra_exact=None, extra_prefixes=None):
    extra_exact = set(extra_exact or [])
    extra_prefixes = tuple(extra_prefixes or [])

    if col_name in EXCLUDE_EXACT or col_name in extra_exact:
        return True

    if any(col_name.startswith(p) for p in EXCLUDE_PREFIXES):
        return True

    if any(col_name.startswith(p) for p in extra_prefixes):
        return True

    return False