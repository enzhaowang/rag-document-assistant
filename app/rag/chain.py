"""RAG chain. `answer_question()` is the only public entry point.

TODO(P4): rewrite follow-ups, retrieve and threshold, refuse early without calling the
LLM when nothing relevant is found, generate a structured answer, and build citations
in code from retrieved chunk IDs only.
"""
