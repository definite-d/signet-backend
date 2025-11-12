from jinja2 import Template
import re

ZERO_WIDTH_START = "\u200b"  # Zero-width space
ZERO_WIDTH_END = "\u200c"  # Zero-width non-joiner


def render_with_positions(template_text, **context) -> tuple[str, dict]:
    """Render a Jinja2 template and return both text and variable positions."""
    # Wrap each field value with invisible markers
    tracked_context = {
        k: f"{ZERO_WIDTH_START}{v}{ZERO_WIDTH_END}" if isinstance(v, str) else v
        for k, v in context.items()
    }

    # Render the text
    template = Template(template_text)
    rendered = template.render(**tracked_context)

    # Extract variable positions by detecting zero-width markers
    positions = {}
    for k, v in context.items():
        pattern = (
            re.escape(ZERO_WIDTH_START) + re.escape(str(v)) + re.escape(ZERO_WIDTH_END)
        )
        match = re.search(pattern, rendered)
        if match:
            start, end = match.start(0), match.end(0)
            # adjust indices to exclude markers
            positions[k] = (start + 1, end - 1)
        # strip the markers
        rendered = re.sub(re.escape(ZERO_WIDTH_START), "", rendered)
        rendered = re.sub(re.escape(ZERO_WIDTH_END), "", rendered)

    return rendered, positions
