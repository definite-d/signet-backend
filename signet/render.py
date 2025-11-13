import re
from jinja2 import Template

ZERO_WIDTH_START = "\u200b"  # Zero-width space
ZERO_WIDTH_END = "\u200c"  # Zero-width non-joiner


def render_with_positions(
    template_text: str, **context
) -> tuple[str, dict[str, list[tuple[int, int]]]]:
    """
    Render a Jinja2 template and return (clean_text, positions).
    positions maps each context variable name to a list of (start, end) ranges
    in the clean_text (end is exclusive).
    """
    # 1) Ensure every value is a string and wrap with markers
    tracked_context = {
        k: f"{ZERO_WIDTH_START}{str(v)}{ZERO_WIDTH_END}" for k, v in context.items()
    }

    # 2) Render with markers
    template = Template(template_text)
    marked = template.render(**tracked_context)

    # 3) Build index mapping from marked-index -> cleaned-index (or None for markers)
    index_map = []
    clean_idx = 0
    for ch in marked:
        if ch == ZERO_WIDTH_START or ch == ZERO_WIDTH_END:
            index_map.append(None)
        else:
            index_map.append(clean_idx)
            clean_idx += 1

    # 4) For each variable, find all occurrences of the wrapped value and map spans
    positions: dict[str, list[tuple[int, int]]] = {}
    for key, orig_val in context.items():
        s = str(orig_val)
        # pattern ensures we capture only the inner value (so span won't include markers)
        pattern = (
            re.escape(ZERO_WIDTH_START)
            + "("
            + re.escape(s)
            + ")"
            + re.escape(ZERO_WIDTH_END)
        )
        for m in re.finditer(pattern, marked):
            gstart, gend = (
                m.start(1),
                m.end(1),
            )  # span in the marked string for the value itself
            # map to cleaned indices
            # find mapped start: index_map[gstart] should not be None, same for gend-1
            mapped_start = index_map[gstart]
            mapped_end = index_map[gend - 1] + 1
            if mapped_start is None or mapped_end is None:
                # defensive fallback — shouldn't happen
                continue
            positions.setdefault(key, []).append((mapped_start, mapped_end))

    # 5) Produce clean string (strip markers)
    clean = marked.replace(ZERO_WIDTH_START, "").replace(ZERO_WIDTH_END, "")

    return clean, positions
