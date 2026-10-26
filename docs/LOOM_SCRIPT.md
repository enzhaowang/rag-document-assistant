# Loom demo script (3-5 minutes)

A walkthrough of the RAG Document Assistant for a client who needs a chatbot over their
internal PDFs (SOPs, product guides, FAQs). Target length: about 4 minutes. Spoken lines are
in quotes; actions are in brackets.

## Before recording

- [ ] `docker compose up -d --build` and `docker compose run --rm api python -m app.ingestion.pipeline`
      have been run; `curl http://localhost:8080/health` shows `"chunk_count":68`.
- [ ] Ask one warm-up question so the first answer in the video is fast.
- [ ] Browser tabs, in order:
  1. The UI: <http://localhost:8501> (click "Clear conversation" first)
  2. `data/pdfs/Policy - Limited Warranty.pdf`, page 1
  3. The code editor with the repository open (`app/` expanded)
  4. `eval/reports/summary.md` (rendered, e.g. on GitHub or in the editor preview)
  5. `README.md`, scrolled to "Quick start (Docker)"
- [ ] Hide bookmarks, notifications and any terminal that shows `.env`. Never show the API key.
- [ ] Screen at 1280x800 or larger, browser zoom 110% so the text is readable.

## 1. The problem (0:00-0:30)

[UI tab, empty conversation]

"Hi, I'm Eric. Your support team answers questions from a few dozen PDFs: product guides,
SOPs and FAQs. Searching them by hand is slow, and a generic chatbot will happily make up an
answer. So I built a small assistant that answers only from your documents, shows the exact
document and page for every answer, and says so when the documents don't cover a question.

This demo runs on twelve PDFs of a fictional smart-home company, Lumora, about 63 pages.
Everything you see runs locally with one `docker compose` command."

## 2. A normal answer with citations (0:30-1:30)

[Click the example "What does error E4 mean on the Thermostat T3?"]

"Let's ask a typical agent question: what does error E4 mean on the Thermostat T3?"

[Wait for the answer. Expand the source.]

"E4 on the T3 is a humidity sensor fault: power-cycle, and if it persists, start a warranty
claim. This is a tricky one, because E4 means something different on the T2, and the answer
picks the right model. Below it is the source: the T3 product guide, page 5, section 6, with
the passage the answer came from and a relevance score. The model never writes the citation
itself: it only returns the IDs of the passages it used, and the code turns those into
document and page. So a citation can't point to a page that doesn't exist."

[Type: "How long is the warranty on the Lumora Thermostat T2?" Then: "And on the T3?"]

"Follow-up questions work too. 'And on the T3?' is rewritten into a full question using the
chat history, and the answer cites both the warranty policy and the T3 product guide."

[Optional, 10 seconds: switch to the warranty PDF tab, page 1, point at the coverage terms.]

"Here is that page in the original PDF, so an agent can verify it in one click."

## 3. Declining instead of guessing (1:30-2:05)

[Click the example "Who is the CEO of Lumora?"]

"Now something the documents don't say: who is the CEO? The assistant declines with a
fixed message instead of inventing a name. There are three layers behind this: passages
below a relevance threshold are dropped before the model is called, the model must return a
structured 'is answerable' flag, and an answer that claims to be answerable but cites no
valid passage is turned into a refusal by the code."

## 4. Quick tour of the code (2:05-2:55)

[Editor tab, `app/` expanded; click each folder as you mention it]

"The code is plain Python with LangChain, and it is organized the way the data flows.

- `ingestion` reads the PDFs page by page with PyMuPDF, splits them into token-sized chunks
  and stores metadata: file name, page, section. Re-running it is incremental, so unchanged
  files cost nothing.
- `retrieval` wraps the Chroma vector database and applies the relevance threshold.
- `rag/chain.py` has one entry point, `answer_question`: rewrite the follow-up, retrieve,
  ask the model for a structured answer, build the citations.
- `api` is a FastAPI service with `/chat`, `/health` and an admin `/ingest`; the Streamlit UI
  is just a client of that API, so you can plug the same backend into Slack, Zendesk or your
  intranet.

All settings, including the model and the endpoint, come from one `.env` file. It works with
OpenAI or any OpenAI-compatible endpoint such as OpenRouter."

## 5. Evaluation results (2:55-3:35)

[Summary tab, scroll from "Bottom line" to the "Scorecard" table]

"I don't want you to take quality on trust, so there is an evaluation: 20 questions with
known answers, including five that the documents don't cover. All four targets are met:
94% faithfulness measured with RAGAS, the correct document and page cited for every
in-scope question, every out-of-scope question declined, and no in-scope question wrongly
declined. An answer takes about three seconds and costs about four hundredths of a cent.

[Scroll to "Tuning"]

I also tested 40 combinations of chunk size, number of passages and threshold, and the
report explains the trade-offs in plain language. With your documents, I'd write 15 to 20
questions together with your team and re-run exactly this."

## 6. Deployment and next steps (3:35-4:15)

[README tab, "Quick start (Docker)"]

"Running it is three steps: copy the example settings and add your key, `docker compose
up`, run the ingestion. The index lives in a Docker volume and survives restarts. The README
covers deploying on a small VPS behind HTTPS with a password, how to add your own PDFs, the
API, costs, and how to switch to Qdrant or pgvector.

For your project, the work is mostly swapping in your documents, tuning on your questions
and deploying. I'd plan it like this:

- Day 1: ingest your PDFs, check parsing quality, agree on the evaluation questions.
- Day 2: retrieval, citations and refusals tuned on your data; you get sample answers.
- Day 3: API and chat UI on a staging link you can try.
- Day 4: evaluation run, fixes for failing questions, before/after report.
- Day 5: Docker setup, README and handover to your repository, plus a walkthrough video.

Thanks for watching. I'm happy to run this on a couple of your real documents first."

[Stop recording]

## Fallbacks during recording

- An answer takes more than 10 seconds: keep talking about the citation design, then cut the
  pause in the Loom editor.
- The sidebar shows "Backend unreachable" or "The index is empty": check
  `docker compose ps` and `docker compose logs api`; usually the stack was not started or the
  ingestion was not run (`docker compose run --rm api python -m app.ingestion.pipeline`).
- A refusal for an in-scope question: re-ask once; mention that refusals are measured in the
  evaluation (0% false refusals on the test set).
