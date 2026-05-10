from __future__ import annotations

import re

from app.schemas.domain import ClauseMatch


def locate_clauses(text: str, patterns: dict[str, str]) -> list[ClauseMatch]:
    matches: list[ClauseMatch] = []
    for label, pattern in patterns.items():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            snippet = text[max(0, match.start() - 30) : min(len(text), match.end() + 120)].strip()
            matches.append(
                ClauseMatch(
                    label=label,
                    snippet=snippet,
                    start=match.start(),
                    end=match.end(),
                )
            )
    return matches
