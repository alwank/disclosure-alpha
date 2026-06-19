from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

PairStatus = Literal["pass", "fail", "skipped"]


@dataclass
class CorpusRow:
    ticker: str
    fiscal_year: int | None
    section_name: str
    cleaned_text: str
    word_count: int
    extraction_confidence: float | None
    accession_number: str | None = None


@dataclass
class ConstructPairResult:
    name: str
    status: PairStatus
    spearman_rho: float | None
    threshold: float
    n: int
    ours_field: str
    ref_field: str
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationReport:
    validation_level: str
    generated_at: str
    versions: dict[str, str]
    corpus: dict[str, Any]
    pairs: dict[str, ConstructPairResult]
    edgar_gates: dict[str, Any]
    edgar_pass: bool
    construct_pass: bool
    overall_l2_pass: bool
    discordant_tickers: dict[str, list[str]] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "validation_level": self.validation_level,
            "generated_at": self.generated_at,
            "versions": self.versions,
            "corpus": self.corpus,
            "pairs": {k: v.to_dict() for k, v in self.pairs.items()},
            "edgar_gates": self.edgar_gates,
            "edgar_pass": self.edgar_pass,
            "construct_pass": self.construct_pass,
            "overall_l2_pass": self.overall_l2_pass,
            "discordant_tickers": self.discordant_tickers,
            "diagnostics": self.diagnostics,
        }
