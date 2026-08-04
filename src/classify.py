from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


@dataclass
class MatchResult:
    score: float = 0.0
    level: str = "none"
    matched_terms: list[str] = field(default_factory=list)
    writing_only: bool = False
    details: dict[str, Any] = field(default_factory=dict)


class KeywordClassifier:
    """Two-stage keyword scorer: loose hit + strict tiering."""

    def __init__(
        self,
        loose: dict[str, Any],
        strict: dict[str, Any],
        level_thresholds: dict[str, float] | None = None,
    ) -> None:
        self.loose_terms = [t.lower() for t in (loose.get("terms") or [])]
        self.loose_regex = [
            re.compile(p, re.IGNORECASE) for p in (loose.get("regex") or [])
        ]
        self.writing_hints = [t.lower() for t in (loose.get("writing_only_hints") or [])]

        self.strong = [t.lower() for t in (strict.get("strong_terms") or [])]
        self.formal = [t.lower() for t in (strict.get("formal_terms") or [])]
        self.ai_models = [t.lower() for t in (strict.get("ai_model_terms") or [])]
        self.open_problem = [t.lower() for t in (strict.get("open_problem_terms") or [])]
        self.exclude_if_only = [t.lower() for t in (strict.get("exclude_if_only") or [])]

        thr = level_thresholds or {"L0": 1, "L1": 4, "L2": 7, "L3": 10}
        self.thresholds = {k: float(v) for k, v in thr.items()}

    def classify_text(self, title: str, abstract: str) -> MatchResult:
        text = _norm(f"{title}\n{abstract}")
        if not text:
            return MatchResult()

        matched: list[str] = []
        score = 0.0

        for term in self.loose_terms:
            if term in text:
                matched.append(term)
                score += 1.0

        for rx in self.loose_regex:
            if rx.search(text):
                label = f"re:{rx.pattern}"
                if label not in matched:
                    matched.append(label)
                    score += 1.0

        if not matched:
            return MatchResult()

        # Strict boosts
        strong_hits = [t for t in self.strong if t in text]
        formal_hits = [t for t in self.formal if t in text]
        ai_hits = [t for t in self.ai_models if t in text]
        open_hits = [t for t in self.open_problem if t in text]
        writing_hits = [t for t in self.writing_hints if t in text]
        exclude_hits = [t for t in self.exclude_if_only if t in text]

        score += 3.0 * len(strong_hits)
        score += 1.5 * len(formal_hits)
        score += 1.0 * len(ai_hits)
        score += 1.0 * len(open_hits)

        # Combo bonuses
        if strong_hits:
            score += 2.0
        if formal_hits and ai_hits:
            score += 2.5
        if strong_hits and open_hits:
            score += 3.0
        if formal_hits and open_hits and ai_hits:
            score += 2.0

        writing_only = False
        if writing_hits or exclude_hits:
            # Demote pure writing assistance if no strong/formal proof signals
            if not strong_hits and not (formal_hits and ai_hits):
                score = max(1.0, score * 0.35)
                writing_only = True

        level = self._level_for(score, strong_hits, formal_hits, ai_hits, open_hits, writing_only)
        # de-dup matched, keep order
        seen: set[str] = set()
        ordered: list[str] = []
        for m in matched + strong_hits + formal_hits + ai_hits + open_hits:
            if m not in seen:
                seen.add(m)
                ordered.append(m)

        return MatchResult(
            score=round(score, 2),
            level=level,
            matched_terms=ordered,
            writing_only=writing_only,
            details={
                "strong_hits": strong_hits,
                "formal_hits": formal_hits,
                "ai_hits": ai_hits,
                "open_hits": open_hits,
                "writing_hits": writing_hits,
            },
        )

    def _level_for(
        self,
        score: float,
        strong_hits: list[str],
        formal_hits: list[str],
        ai_hits: list[str],
        open_hits: list[str],
        writing_only: bool,
    ) -> str:
        if writing_only and score < self.thresholds.get("L1", 4):
            return "L0"
        # L3: open-problem language + (strong AI-proof signal OR AI+formal) + high score
        l3_signal = bool(strong_hits) or (bool(formal_hits) and bool(ai_hits)) or (
            bool(ai_hits) and len(open_hits) >= 2 and score >= self.thresholds.get("L3", 10)
        )
        if score >= self.thresholds.get("L3", 10) and open_hits and l3_signal:
            return "L3"
        if score >= self.thresholds.get("L2", 7) and (formal_hits or strong_hits or (ai_hits and open_hits)):
            return "L2"
        if score >= self.thresholds.get("L1", 4) or strong_hits:
            return "L1"
        if score >= self.thresholds.get("L0", 1):
            return "L0"
        return "none"

    def is_loose_hit(self, title: str, abstract: str) -> bool:
        return self.classify_text(title, abstract).level != "none"
