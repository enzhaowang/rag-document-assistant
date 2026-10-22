"""Ask the RAG chain questions from the command line (manual debugging).

Requires an indexed vector store (`make ingest`) and makes real API calls.

Usage:
    python scripts/ask.py "How long is the warranty on the Thermostat T3?"
    python scripts/ask.py            # interactive mode; follow-up questions use history
    python scripts/ask.py --json "..."   # print the full ChatResult as JSON
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.rag.chain import answer_question  # noqa: E402
from app.rag.schemas import ChatResult, HistoryMessage  # noqa: E402
from app.retrieval.vectorstore import get_vectorstore  # noqa: E402


def print_result(result: ChatResult, question: str) -> None:
    if result.standalone_question != question:
        print(f"(rewritten as: {result.standalone_question})")
    status = "answered" if result.is_answerable else f"REFUSED ({result.refusal_reason})"
    print(f"\n{result.answer}\n")
    print(f"[{status} | model {result.model} | {result.latency_ms} ms]")
    if result.sources:
        print("Sources:")
        for i, source in enumerate(result.sources, start=1):
            section = f" - {source.section}" if source.section else ""
            print(f"  {i}. {source.document}, p. {source.page}{section} (score {source.score:.3f})")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask the document assistant a question.")
    parser.add_argument("question", nargs="?", help="Question; omit for interactive mode.")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show INFO logs.")
    args = parser.parse_args(argv)

    configure_logging("INFO" if args.verbose else "WARNING")
    settings = get_settings()
    store = get_vectorstore(settings)

    def ask(question: str, history: list[HistoryMessage]) -> ChatResult:
        result = answer_question(question, history, settings=settings, vectorstore=store)
        if args.json:
            print(result.model_dump_json(indent=2))
        else:
            print_result(result, question.strip())
        return result

    if args.question:
        ask(args.question, [])
        return 0

    print("Interactive mode. Follow-up questions use the conversation. Ctrl-D or 'exit' quits.")
    history: list[HistoryMessage] = []
    while True:
        try:
            question = input("\nYou: ").strip()
        except EOFError:
            print()
            return 0
        if question.lower() in {"exit", "quit"}:
            return 0
        if not question:
            continue
        result = ask(question, history)
        history += [
            HistoryMessage(role="user", content=question),
            HistoryMessage(role="assistant", content=result.answer),
        ]


if __name__ == "__main__":
    raise SystemExit(main())
