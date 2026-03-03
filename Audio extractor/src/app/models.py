from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class Segment:
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TranscriptionResult:
    language: str
    segments: list[Segment]

    @property
    def text(self) -> str:
        return "\n".join(seg.text.strip() for seg in self.segments if seg.text.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "text": self.text,
            "segments": [seg.to_dict() for seg in self.segments],
        }
