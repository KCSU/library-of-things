"""Inline SVG icon rendering.

Read once at startup and inlined into templates.
"""

import logging
from pathlib import Path

from flask import Flask
from markupsafe import Markup

logger = logging.getLogger(__name__)


def register_icon_helper(app: Flask) -> None:
    root = Path(app.root_path) / 'static' / 'icons'
    icons = {
        str(path.relative_to(root).with_suffix('')): path.read_text()
        for path in root.rglob('*.svg')
    }
    logger.info('Loaded %d icons from %s', len(icons), root)

    @app.template_global()
    def icon(name: str, css_class: str = 'icon') -> Markup:
        svg = icons.get(name)
        if svg is None:
            # An unknown icon leaves an empty span.
            logger.warning('Unknown icon: %r', name)
        return Markup(f'<span class="{css_class}">{svg or ""}</span>')
