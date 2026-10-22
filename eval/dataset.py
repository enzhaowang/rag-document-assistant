"""Evaluation question set: schema and loader for eval/questions.yaml."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

DEFAULT_QUESTIONS_PATH = Path(__file__).resolve().parent / "questions.yaml"


class Category(StrEnum):
    """Question types of the evaluation set."""

    SINGLE_FACT = "single_fact"
    CROSS_PAGE_OR_TABLE = "cross_page_or_table"
    CONFUSABLE = "confusable"
    OUT_OF_SCOPE = "out_of_scope"


CATEGORY_LABELS: dict[Category, str] = {
    Category.SINGLE_FACT: "Single fact",
    Category.CROSS_PAGE_OR_TABLE: "Cross-page / table",
    Category.CONFUSABLE: "Confusable (T2 vs T3)",
    Category.OUT_OF_SCOPE: "Out of scope",
}


class ExpectedSource(BaseModel):
    """A document and the page(s) where the answer is stated (1-based page numbers)."""

    document: str = Field(min_length=1)
    pages: list[int] = Field(min_length=1)

    def page_keys(self) -> set[tuple[str, int]]:
        return {(self.document, page) for page in self.pages}


class EvalQuestion(BaseModel):
    """One evaluation question."""

    id: str = Field(min_length=1)
    category: Category
    question: str = Field(min_length=1)
    ground_truth: str = Field(min_length=1)
    expected_sources: list[ExpectedSource] = Field(default_factory=list)
    should_answer: bool
    fact_ids: list[str] = Field(default_factory=list)
    # Short phrases a correct answer must contain (case-insensitive); "a|b" accepts either.
    key_facts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> EvalQuestion:
        if self.should_answer and not self.expected_sources:
            raise ValueError(f"{self.id}: in-scope questions need expected_sources")
        if not self.should_answer and self.expected_sources:
            raise ValueError(f"{self.id}: out-of-scope questions must not list expected_sources")
        if not self.should_answer and self.key_facts:
            raise ValueError(f"{self.id}: out-of-scope questions must not list key_facts")
        if (self.category is Category.OUT_OF_SCOPE) == self.should_answer:
            raise ValueError(
                f"{self.id}: category out_of_scope must match should_answer=false and vice versa"
            )
        return self

    def expected_pages(self) -> set[tuple[str, int]]:
        """All (document, page) pairs that count as a correct citation."""
        keys: set[tuple[str, int]] = set()
        for source in self.expected_sources:
            keys |= source.page_keys()
        return keys


def load_questions(path: Path | str = DEFAULT_QUESTIONS_PATH) -> list[EvalQuestion]:
    """Load and validate the question set; question IDs must be unique."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    items = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(items, list) or not items:
        raise ValueError(f"{path}: expected a non-empty 'questions' list")
    questions = [EvalQuestion.model_validate(item) for item in items]
    seen: set[str] = set()
    for question in questions:
        if question.id in seen:
            raise ValueError(f"{path}: duplicate question id {question.id!r}")
        seen.add(question.id)
    return questions
