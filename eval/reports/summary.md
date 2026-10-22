# Evaluation Summary: Lumora Document Assistant

_Generated 2026-10-22T18:02:32+08:00 by `make eval` - 20 questions - chat model `openai/gpt-4o-mini` - chunk 500/80 tokens, top-k 6, threshold 0.35._

## Bottom line

- **All 4 quality targets were met.**
- Of the 15 questions whose answer is in the documents, the assistant answered 15 and cited the correct document and page for 15 (100%).
- It declined 5 of 5 questions that the documents do not cover (for example "Who is the CEO of Lumora Home Systems?"): it never invented an answer.
- 14 of 15 answers contain every key fact of the reference answer; incomplete: CP-03.
- On average 94% of the statements in an answer are directly supported by the quoted source passages (RAGAS faithfulness).
- 1 of the 2 flagged questions (SF-09) was flagged only by the automatic faithfulness judge; its citation and key facts are correct (see the failure analysis).
- An answer takes 3.0 s on average and costs about $0.0004 in API fees (about $0.42 per 1,000 questions).
- 40 combinations of chunk size, number of retrieved passages and relevance threshold were tested; the chosen settings are chunk 500/80 tokens, top-k 6, threshold 0.35 (see Tuning below for the trade-offs).

## Scorecard

| Metric | What it measures | Result | Target | Status |
|---|---|---|---|---|
| Faithfulness | Share of statements in an answer that are backed by the source passages (no made-up facts). | 0.94 | >= 0.85 | Met |
| Citation hit rate | Answers that cite the correct document and page. | 100% | >= 85% | Met |
| Out-of-scope refusal rate | Questions the documents do not cover that the assistant declined instead of guessing. | 100% | = 100% | Met |
| In-scope false refusal rate | Questions the documents do cover that the assistant wrongly declined. | 0% | <= 10% | Met |
| Key fact accuracy | Answers that contain every key fact of the reference answer (numbers, names, codes), checked word for word. | 93% | - | - |
| Answer relevancy | How directly the answer addresses the question. | 0.87 | - | - |
| Context precision | Whether the passages that contain the answer are ranked first. | 0.78 | - | - |
| Context recall | Whether the passages given to the model contain everything in the reference answer. | 0.97 | - | - |
| Retrieval hit rate (top-k) | Questions where the page with the answer was among the passages retrieved by the search step. | 100% | - | - |
| Average latency | - | 3.0 s | - | - |
| 95th percentile latency | - | 3.8 s | - | - |
| Average cost per question | - | $0.00042 | - | - |

## Results by question type

The 20 questions are based on facts in the sample documents: 10 single facts (numbers, steps, error codes), 3 facts that span two pages or sit in a table, 2 facts that differ between the similar T2 and T3 thermostats, and 5 questions the documents do not answer.

| Question type | Questions | Passed | Correct citation | Refused |
|---|---|---|---|---|
| Single fact | 10 | 9/10 | 10/10 | 0/10 |
| Cross-page / table | 3 | 2/3 | 3/3 | 0/3 |
| Confusable (T2 vs T3) | 2 | 2/2 | 2/2 | 0/2 |
| Out of scope | 5 | 5/5 | - | 5/5 |

## Tuning

**Decision: keep the initial settings (500-token chunks with 80 overlap, 6 passages per
question, relevance threshold 0.35).** We tested 40 combinations of the three settings
that matter most and repeated the most promising ones three times, because answers vary
slightly from run to run even with a deterministic model setting. What we learned:

- **Chunk size: 500 tokens is the sweet spot.** With 300-token chunks the T2 factory-reset
  instructions (SF-03) end up in a small piece that ranks 8th, below other T2 passages, and
  the question failed in 9 of 12 configurations. With 800-token chunks a whole page becomes
  one passage, and the T3 error-code question (CF-02) failed in all 12 configurations: the
  answer was right, but it cited the continuation page of the error table (p.6) instead of
  the page with the E4 row (p.5).
- **Passages per question (top-k): 6.** With 3 or 4 passages, the page with the answer is
  sometimes not retrieved at all: the return-window page (SF-04) ranks 5th and the T2 reset
  page (SF-03) ranks 4th. At top-k 4 the assistant even answered SF-04 with "the documents do
  not specify a general return window", which is worse than declining. Going to 8 passages
  costs about 15% more per question and fixed nothing.
- **Relevance threshold: 0.35.** The threshold only removes clearly unrelated passages
  (small talk scores about 0.15). It cannot separate realistic out-of-scope questions such as
  "Does the T3 work with Apple HomeKit?" (0.58) from real ones (lowest 0.42); those are
  declined by the model's own check, which caught 100% of them in every configuration.
  At 0.50 the assistant starts refusing the holiday-return question (CP-02) every time.

**Why not 0.40?** On this question set 0.40 looked slightly better: every answer was correct
and correctly cited in four runs, all targets were met, and it is about 6% cheaper because
fewer loosely related passages are sent (see the side-by-side table). We still did not
adopt it. For the holiday-return question the second page of the rule, which holds the
exclusions, scores 0.40, exactly at that threshold: continuation pages score lower because
they do not repeat the section heading.
A slightly different wording of the question would drop that page, and the assistant would
state the holiday rule without its exclusions, an incomplete answer that looks complete.
The failures that 0.40 avoided all come from one table that is split across two pages
(see the failure analysis); the right fix for those is table-aware chunking, not a stricter
threshold.

Full evaluation (including RAGAS) of the chosen settings next to the closest alternative:

| Metric | This run (chosen settings) | Runner-up (threshold 0.40) |
|---|---|---|
| Settings | chunk 500/80 tokens, top-k 6, threshold 0.35 | chunk 500/80 tokens, top-k 6, threshold 0.40 |
| Faithfulness | 0.94 | 0.93 |
| Answer relevancy | 0.87 | 0.87 |
| Context precision | 0.78 | 0.77 |
| Context recall | 0.97 | 0.97 |
| Citation hit rate | 100% | 100% |
| Key fact accuracy | 93% | 100% |
| Out-of-scope refusal rate | 100% | 100% |
| In-scope false refusal rate | 0% | 0% |
| Retrieval hit rate (top-k) | 100% | 100% |
| Average latency | 3.0 s | 4.7 s |
| Average cost per question | $0.00042 | $0.00039 |

<details><summary>Full parameter sweep (40 configurations, custom metrics only)</summary>

Same 20 questions; 4 questions run in parallel, so latencies are higher than in a single-user run. 'Runs' > 1 means the configuration was repeated and the metrics are averages; failed questions show how often they failed.

| Chunk size / overlap | Top-k | Threshold | Runs | Correct citation | Key facts | Out-of-scope refused | False refusals | Retrieval hit | Avg latency | Avg cost | Failed questions |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 300 / 50 | 3 | 0.30 | 1 | 87% | 87% | 100% | 7% | 93% | 3.3 s | $0.00021 | SF-03 CP-02 CF-02 |
| 300 / 50 | 3 | 0.40 | 1 | 87% | 87% | 100% | 7% | 93% | 2.9 s | $0.00021 | SF-03 CP-02 CF-02 |
| 300 / 50 | 3 | 0.50 | 1 | 87% | 87% | 100% | 7% | 93% | 3.0 s | $0.00020 | SF-03 CP-02 CF-02 |
| 300 / 50 | 4 | 0.30 | 1 | 93% | 93% | 100% | 7% | 100% | 3.0 s | $0.00025 | SF-03 |
| 300 / 50 | 4 | 0.40 | 1 | 93% | 93% | 100% | 7% | 100% | 2.9 s | $0.00024 | SF-03 |
| 300 / 50 | 4 | 0.50 | 1 | 93% | 87% | 100% | 7% | 100% | 2.9 s | $0.00022 | SF-03 CP-02 |
| 300 / 50 | 6 | 0.30 | 1 | 87% | 93% | 100% | 7% | 100% | 3.2 s | $0.00032 | SF-03 CF-02 |
| 300 / 50 | 6 | 0.40 | 1 | 87% | 80% | 100% | 7% | 100% | 3.1 s | $0.00031 | SF-03 CP-02 CP-03 CF-02 |
| 300 / 50 | 6 | 0.50 | 1 | 87% | 87% | 100% | 7% | 100% | 3.4 s | $0.00027 | SF-03 CP-02 CF-02 |
| 300 / 50 | 8 | 0.30 | 1 | 93% | 93% | 100% | 0% | 100% | 3.4 s | $0.00039 | CP-03 CF-02 |
| 300 / 50 | 8 | 0.40 | 1 | 93% | 87% | 100% | 0% | 100% | 3.4 s | $0.00037 | CP-02 CP-03 CF-02 |
| 300 / 50 | 8 | 0.50 | 1 | 93% | 93% | 100% | 0% | 100% | 3.3 s | $0.00030 | CP-02 CF-02 |
| 500 / 80 | 3 | 0.30 | 1 | 87% | 87% | 100% | 7% | 87% | 3.7 s | $0.00027 | SF-03 SF-04 |
| 500 / 80 | 3 | 0.35 | 1 | 87% | 87% | 100% | 7% | 87% | 3.4 s | $0.00027 | SF-03 SF-04 |
| 500 / 80 | 3 | 0.40 | 1 | 87% | 87% | 100% | 7% | 87% | 3.2 s | $0.00026 | SF-03 SF-04 |
| 500 / 80 | 3 | 0.50 | 1 | 80% | 80% | 100% | 13% | 87% | 2.9 s | $0.00023 | SF-03 SF-04 CP-02 |
| 500 / 80 | 4 | 0.30 | 1 | 93% | 87% | 100% | 0% | 93% | 3.2 s | $0.00033 | SF-04 CP-03 |
| 500 / 80 | 4 | 0.35 | 1 | 93% | 93% | 100% | 7% | 93% | 3.0 s | $0.00032 | SF-04 |
| 500 / 80 | 4 | 0.40 | 1 | 93% | 100% | 100% | 0% | 93% | 2.9 s | $0.00031 | SF-04 |
| 500 / 80 | 4 | 0.50 | 1 | 87% | 93% | 100% | 7% | 93% | 3.2 s | $0.00026 | SF-04 CP-02 |
| 500 / 80 | 6 | 0.30 | 3 | 100% | 98% | 100% | 0% | 100% | 3.1 s | $0.00043 | CP-03 (1/3) |
| 500 / 80 **(final)** | 6 | 0.35 | 3 | 98% | 100% | 100% | 0% | 100% | 3.0 s | $0.00042 | SF-01 (1/3) |
| 500 / 80 | 6 | 0.40 | 3 | 100% | 100% | 100% | 0% | 100% | 3.0 s | $0.00039 | - |
| 500 / 80 | 6 | 0.50 | 3 | 93% | 93% | 100% | 7% | 100% | 2.9 s | $0.00031 | CP-02 (3/3) |
| 500 / 80 | 8 | 0.30 | 1 | 100% | 93% | 100% | 0% | 100% | 3.4 s | $0.00051 | CP-03 |
| 500 / 80 | 8 | 0.35 | 1 | 100% | 93% | 100% | 0% | 100% | 3.2 s | $0.00048 | CP-03 |
| 500 / 80 | 8 | 0.40 | 1 | 100% | 100% | 100% | 0% | 100% | 3.6 s | $0.00045 | - |
| 500 / 80 | 8 | 0.50 | 1 | 93% | 93% | 100% | 7% | 100% | 3.1 s | $0.00033 | CP-02 |
| 800 / 120 | 3 | 0.30 | 1 | 80% | 87% | 100% | 7% | 87% | 3.3 s | $0.00027 | SF-03 SF-04 CF-02 |
| 800 / 120 | 3 | 0.40 | 1 | 80% | 87% | 100% | 7% | 87% | 3.3 s | $0.00027 | SF-03 SF-04 CF-02 |
| 800 / 120 | 3 | 0.50 | 1 | 73% | 80% | 100% | 13% | 87% | 3.3 s | $0.00023 | SF-03 SF-04 CP-02 CF-02 |
| 800 / 120 | 4 | 0.30 | 1 | 80% | 93% | 100% | 7% | 87% | 3.4 s | $0.00034 | SF-03 SF-04 CF-02 |
| 800 / 120 | 4 | 0.40 | 1 | 80% | 87% | 100% | 7% | 87% | 3.1 s | $0.00032 | SF-03 SF-04 CF-02 |
| 800 / 120 | 4 | 0.50 | 1 | 73% | 80% | 100% | 13% | 87% | 3.0 s | $0.00027 | SF-03 SF-04 CP-02 CF-02 |
| 800 / 120 | 6 | 0.30 | 1 | 93% | 100% | 100% | 0% | 100% | 3.3 s | $0.00046 | CF-02 |
| 800 / 120 | 6 | 0.40 | 1 | 93% | 100% | 100% | 0% | 100% | 3.3 s | $0.00041 | CF-02 |
| 800 / 120 | 6 | 0.50 | 1 | 87% | 93% | 100% | 7% | 100% | 3.0 s | $0.00032 | CP-02 CF-02 |
| 800 / 120 | 8 | 0.30 | 1 | 93% | 93% | 100% | 0% | 100% | 3.0 s | $0.00052 | CP-03 CF-02 |
| 800 / 120 | 8 | 0.40 | 1 | 93% | 100% | 100% | 0% | 100% | 3.3 s | $0.00046 | CF-02 |
| 800 / 120 | 8 | 0.50 | 1 | 87% | 93% | 100% | 7% | 100% | 3.2 s | $0.00034 | CP-02 CF-02 |

</details>

## Failure analysis

**SF-09 (Single fact): Does a T2 customer without a C-wire have to pay for the Power Extender Kit PEK-1?**

- What went wrong: The right page was cited, but only 67% of the statements in the answer are supported by the retrieved passages (RAGAS faithfulness).
- Note: Flagged by the automatic judge only: the correct page was cited and every key fact is in the answer. Check it by hand before treating it as a real error.
- Expected source: Product Guide - Lumora Thermostat T2.pdf p.4
- Assistant's answer: "A T2 customer without a C-wire can receive the Power Extender Kit PEK-1 free of charge if they request it within 60 days of delivery. After that period, it costs $24.99."
- Cited: Product Guide - Lumora Thermostat T2.pdf p.4
- Top retrieved: Product Guide - Lumora Thermostat T2.pdf p.4 (0.62); Product Guide - Lumora Thermostat T3.pdf p.4 (0.53); Product Guide - Lumora Thermostat T3.pdf p.3 (0.51)

**CP-03 (Cross-page / table): List all refund approval levels by refund amount per order.**

- What went wrong: The right page was cited, but the answer is incomplete or wrong: it does not contain 'above $5000', 'Finance Controller'.
- Expected source: SOP - Returns and Refunds.pdf p.3,4
- Assistant's answer: "1. Up to $250.00: Customer Care agent (Tier 1) - Approve in OMS directly. 2. $250.01 to $1,000.00: Team Lead - Approval request in OMS; Team Lead responds within 4 business hours. 3. $1,000.01 to $5,000.00: Customer Care Manager - Both approvals required before the refund is released."
- Cited: SOP - Returns and Refunds.pdf p.4; SOP - Returns and Refunds.pdf p.3
- Top retrieved: SOP - Returns and Refunds.pdf p.4 (0.55); SOP - Returns and Refunds.pdf p.3 (0.52); SOP - Returns and Refunds.pdf p.5 (0.49)


### Manual review

_Known failure patterns, checked by hand against the PDFs over several evaluation runs. Answers vary slightly between runs, so not every pattern appears in every run._

- **Refund approval table (CP-03, and SF-01 in some runs).** Table 4-1 of the Returns and
  Refunds SOP starts on page 3 and continues on page 4. Because passages are cut per page,
  the last row ("Above $5,000.00: Customer Care Manager and Finance Controller") sits in a
  separate passage. When CP-03 fails, the assistant lists three of the four levels and
  attaches the note of the missing row ("Both approvals required") to the
  $1,000.01-$5,000.00 row. When SF-01 fails, the assistant gives the right $800 answer but
  cites page 4 instead of page 3. The RAGAS faithfulness score of such a CP-03 answer is
  still high, because every phrase does appear in the passages; only the word-for-word key
  fact check catches the mix-up. **Fix:** keep tables that continue on the next page
  together (merge the continuation and repeat the header) before chunking; this is a small
  change to the ingestion step.
- **Faithfulness false alarms (SF-09, CF-02), flagged in some runs with faithfulness
  0.67.** Both answers are correct. For SF-09 (PEK-1 cost: "free within 60 days of
  delivery, $24.99 after that") the RAGAS judge marked the phrase "a T2 customer without a
  C-wire" as unsupported because the guide states the C-wire condition in the previous
  sentence. For CF-02 (T3 error E4: humidity sensor fault, power-cycle and start a warranty
  claim if it persists) the guide gives the same steps in a table row worded differently,
  which the judge did not match. These failures are reported as "judge only": the correct
  page is cited and every key fact is in the answer. The judge is the same small model as
  the assistant; for a sign-off run use a stronger judge:
  `make eval ARGS="--judge-model openai/gpt-4o"`.
- **Low context precision (SF-03, SF-04, SF-05)** means the right page was retrieved but
  ranked behind pages on similar topics (for SF-04 the return-window page ranks 5th, behind
  shipping and warranty pages that also mention days and delivery). The answers were still
  correct, but this is the main reason a smaller top-k fails. A reranking step would move
  the right page to the top and allow fewer, cheaper passages per question.

### Risks and near misses

- 3 of 5 out-of-scope questions scored above the relevance threshold (0.35) and were stopped by the model's own refusal, not by the threshold: OOS-01 (0.53), OOS-03 (0.58), OOS-04 (0.51). These questions sound like real support topics, so the second safety layer matters.
- The weakest in-scope match was CP-02 (best score 0.42, threshold 0.35). A higher threshold would start refusing questions like this one.
- For SF-03 (rank 4), SF-04 (rank 5) the page with the answer was ranked below the top 3 passages; a smaller top-k would lose these answers.
- Low context precision (below 0.50): SF-03 (0.25), SF-04 (0.37), SF-05 (0.45).

## Recommendations

1. Some answers contain statements that are not in the passages. Tighten the prompt ('only facts from the excerpts') or use a stronger model.
2. Some answers cite the right page but leave out or mix up details, typically in tables that continue on the next page. Use table-aware parsing (keep each table, with its header, in one chunk even across a page break) and ask the model to reproduce every row when listing table contents.
3. Re-run this evaluation with 15-20 real questions from your support team before go-live; the harness is ready (`eval/questions.yaml` + `make eval`).
4. Keep the evaluation in the delivery checklist: re-run `make eval` after adding documents or changing models, and compare against this report.
5. Most questions that are not covered by the documents still look similar to real topics (for example a product feature that is not documented). They are caught by the model's refusal, not by the score threshold, so keep out-of-scope questions in every test set.

## Per-question details

| ID | Question | Outcome | Cited | Key facts | Top score | Faith. | Relev. | Ctx prec. | Ctx rec. | Latency | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SF-01 | Who has to approve a refund of $800 on a single order? | Answered | SOP - Returns and Refunds.pdf p.4; SOP - Returns and Refunds.pdf p.3 | 1/1 | 0.60 | 1.00 | 0.83 | 0.71 | 1.00 | 4.0 s | $0.00052 |
| SF-02 | What does error code E7 mean on the Thermostat T2? | Answered | Product Guide - Lumora Thermostat T2.pdf p.6 | 2/2 | 0.78 | 1.00 | 0.99 | 0.70 | 1.00 | 2.8 s | $0.00036 |
| SF-03 | How do I factory reset a Lumora Thermostat T2? | Answered | Product Guide - Lumora Thermostat T2.pdf p.5 | 2/2 | 0.67 | 1.00 | 0.98 | 0.25 | 1.00 | 3.1 s | $0.00055 |
| SF-04 | How long do customers have to return a product they bought directly from Lumora? | Answered | SOP - Returns and Refunds.pdf p.1 | 2/2 | 0.66 | 0.75 | 0.84 | 0.37 | 1.00 | 3.2 s | $0.00050 |
| SF-05 | What are the first response and resolution targets for a P1 critical ticket? | Answered | SOP - Ticket Escalation.pdf p.1 | 2/2 | 0.60 | 1.00 | 0.97 | 0.45 | 1.00 | 2.7 s | $0.00046 |
| SF-06 | What format do RMA numbers use, and how long is an RMA valid? | Answered | SOP - RMA Process.pdf p.1 | 2/2 | 0.66 | 1.00 | 0.90 | 1.00 | 1.00 | 3.8 s | $0.00050 |
| SF-07 | How many failed sign-in attempts lock a Lumora account, and for how long? | Answered | FAQ - App and Account.pdf p.1 | 2/2 | 0.55 | 1.00 | 0.62 | 1.00 | 1.00 | 2.5 s | $0.00051 |
| SF-08 | How much does a Lumora Plus subscription cost? | Answered | FAQ - Billing and Subscriptions.pdf p.3 | 2/2 | 0.70 | 1.00 | 0.89 | 1.00 | 1.00 | 2.8 s | $0.00050 |
| SF-09 | Does a T2 customer without a C-wire have to pay for the Power Extender Kit PEK-1? | Answered, low faithfulness | Product Guide - Lumora Thermostat T2.pdf p.4 | 2/2 | 0.62 | 0.67 | 0.84 | 0.67 | 1.00 | 3.3 s | $0.00042 |
| SF-10 | How quickly must the Safety Officer be notified about a safety case? | Answered | SOP - Ticket Escalation.pdf p.3 | 1/1 | 0.60 | 1.00 | 0.98 | 1.00 | 1.00 | 3.1 s | $0.00027 |
| CP-01 | In which cases is a C-wire mandatory for the Thermostat T3? | Answered | Product Guide - Lumora Thermostat T3.pdf p.4 | 3/3 | 0.68 | 1.00 | 0.96 | 0.97 | 1.00 | 3.7 s | $0.00047 |
| CP-02 | How does the holiday return extension work, and which orders are excluded? | Answered | SOP - Returns and Refunds.pdf p.1; SOP - Returns and Refunds.pdf p.2 | 5/5 | 0.42 | 1.00 | 0.60 | 0.92 | 1.00 | 3.5 s | $0.00054 |
| CP-03 | List all refund approval levels by refund amount per order. | Incomplete answer | SOP - Returns and Refunds.pdf p.4; SOP - Returns and Refunds.pdf p.3 | 3/5 | 0.55 | 0.75 | 0.70 | 1.00 | 1.00 | 3.7 s | $0.00043 |
| CF-01 | How long is the warranty on the Thermostat T3? | Answered | Product Guide - Lumora Thermostat T3.pdf p.7; Policy - Limited Warranty.pdf p.2 | 1/1 | 0.69 | 1.00 | 0.97 | 0.95 | 1.00 | 3.4 s | $0.00054 |
| CF-02 | What does error E4 mean on the Thermostat T3? | Answered | Product Guide - Lumora Thermostat T3.pdf p.5 | 1/1 | 0.69 | 1.00 | 0.99 | 0.72 | 0.50 | 3.2 s | $0.00037 |
| OOS-01 | Who is the CEO of Lumora Home Systems? | Refused (correct) | - | - | 0.53 | - | - | - | - | 2.7 s | $0.00047 |
| OOS-02 | How do I make pizza dough at home? | Refused (correct) | - | - | 0.15 | - | - | - | - | 1.3 s | $0.00000 |
| OOS-03 | Does the Thermostat T3 work with Apple HomeKit? | Refused (correct) | - | - | 0.58 | - | - | - | - | 3.4 s | $0.00044 |
| OOS-04 | What was Lumora's total revenue last year? | Refused (correct) | - | - | 0.51 | - | - | - | - | 2.4 s | $0.00048 |
| OOS-05 | Write a Python function that sorts a list of numbers. | Refused (correct) | - | - | 0.15 | - | - | - | - | 1.0 s | $0.00000 |

Faith. = faithfulness, Relev. = answer relevancy, Ctx prec. / Ctx rec. = context precision / recall (RAGAS, 0-1; '-' = not scored, e.g. refusals). Top score = cosine similarity of the best retrieved passage.

<details><summary>Answers next to the reference answers</summary>

**SF-01. Who has to approve a refund of $800 on a single order?**

- Answer: A refund of $800 on a single order requires approval from a Team Lead. The approval request must be made in OMS, and the Team Lead is expected to respond within 4 business hours.
- Reference: A Team Lead. Refunds from $250.01 to $1,000.00 per order need Team Lead approval through an approval request in OMS, and the Team Lead responds within 4 business hours.

**SF-02. What does error code E7 mean on the Thermostat T2?**

- Answer: Error code E7 on the Thermostat T2 indicates low supply voltage, specifically that R-C is below 18 VAC. The recommended action is to check the C-wire and transformer, and to install a PEK-1 if there is no C-wire.
- Reference: E7 on the T2 means low supply voltage: R-C is below 18 VAC. Check the C-wire and the transformer, and install a PEK-1 if there is no C-wire.

**SF-03. How do I factory reset a Lumora Thermostat T2?**

- Answer: To factory reset the Lumora Thermostat T2, press and hold the control ring for 12 seconds until the display shows RESET, then release. The device will restart in setup mode. Agents should only suggest a factory reset after the standard troubleshooting steps fail, and must note it in the ticket.
- Reference: Press and hold the control ring for 12 seconds until the display shows RESET, then release. The T2 restarts in setup mode; the reset erases schedules, network credentials and the link to the customer account.

**SF-04. How long do customers have to return a product they bought directly from Lumora?**

- Answer: Customers may return any product bought directly from Lumora within 30 calendar days of the delivery date, for any reason. If the delivery is between November 15 and December 31, the return can be made until January 31 of the following year, or within the standard 30 days if that is later.
- Reference: 30 calendar days, counted from the delivery date shown in OMS (not the order date). The return is on time if the RMA is created within the window.

**SF-05. What are the first response and resolution targets for a P1 critical ticket?**

- Answer: For a P1 critical ticket, the first response target is 15 minutes, and the resolution target is 4 hours.
- Reference: P1 (Critical) tickets need a first response within 15 minutes and have a 4-hour resolution target, with customer updates every 2 hours. P1 covers safety hazards or no heat when the indoor temperature is below 50 °F.

**SF-06. What format do RMA numbers use, and how long is an RMA valid?**

- Answer: RMA numbers use the format RMA-YYMM-NNNNN, where YYMM is the year and month of creation and NNNNN is a sequence number. An RMA is valid for 30 days from creation.
- Reference: RMA numbers use the format RMA-YYMM-NNNNN (for example RMA-2603-00417). An RMA is valid for 30 days from creation, and the customer must ship the item within 14 days.

**SF-07. How many failed sign-in attempts lock a Lumora account, and for how long?**

- Answer: After 5 failed sign-in attempts, the account is locked for 15 minutes.
- Reference: After 5 failed sign-in attempts the account is locked for 15 minutes. Password reset links are valid for 1 hour, and agents cannot unlock accounts manually.

**SF-08. How much does a Lumora Plus subscription cost?**

- Answer: Lumora Plus costs $4.99 per month or $49.00 per year. One subscription covers all devices in one home.
- Reference: Lumora Plus costs $4.99 per month or $49.00 per year, and one subscription covers all devices in one home.

**SF-09. Does a T2 customer without a C-wire have to pay for the Power Extender Kit PEK-1?**

- Answer: A T2 customer without a C-wire can receive the Power Extender Kit PEK-1 free of charge if they request it within 60 days of delivery. After that period, it costs $24.99.
- Reference: The PEK-1 is free for T2 customers who request it within 60 days of delivery; after that it costs $24.99. Only Tier 2 Technical Support may authorize a free PEK-1 outside the 60-day window.

**SF-10. How quickly must the Safety Officer be notified about a safety case?**

- Answer: The Safety Officer must be notified through the safety hotline queue within 1 hour of the first report of a safety case.
- Reference: Within 1 hour of the first report, at any time of day, through the safety hotline queue.

**CP-01. In which cases is a C-wire mandatory for the Thermostat T3?**

- Answer: A C-wire is mandatory for the Thermostat T3 in the following cases: 1. Heat pump systems that use auxiliary or emergency heat. 2. Any system with more than one cooling stage. 3. Homes where the T3 controls a humidifier or dehumidifier through the ACC terminals.
- Reference: The T3 usually runs without a C-wire, but a C-wire or the PEK-1 is mandatory for heat pump systems that use auxiliary or emergency heat, any system with more than one cooling stage, and homes where the T3 controls a humidifier or dehumidifier through the ACC terminals. Otherwise the T3 shows error E10 within 24 hours.

**CP-02. How does the holiday return extension work, and which orders are excluded?**

- Answer: Orders delivered between November 15 and December 31 can be returned until January 31 of the following year, or within the standard 30 days if that is later. However, this extension does not apply to orders placed by business accounts or to orders containing more than five units of the same product.
- Reference: Orders delivered between November 15 and December 31 can be returned until January 31 of the following year (or within the standard 30 days if that is later). The extension does not apply to business accounts or to orders with more than five units of the same product. Agents select the reason modifier HOL in OMS.

**CP-03. List all refund approval levels by refund amount per order.**

- Answer: 1. Up to $250.00: Customer Care agent (Tier 1) - Approve in OMS directly. 2. $250.01 to $1,000.00: Team Lead - Approval request in OMS; Team Lead responds within 4 business hours. 3. $1,000.01 to $5,000.00: Customer Care Manager - Both approvals required before the refund is released.
- Reference: Up to $250.00: the Customer Care agent (Tier 1). $250.01 to $1,000.00: a Team Lead. $1,000.01 to $5,000.00: the Customer Care Manager. Above $5,000.00: both the Customer Care Manager and the Finance Controller.

**CF-01. How long is the warranty on the Thermostat T3?**

- Answer: The Thermostat T3 carries a 3-year (36-month) limited warranty from the date of delivery. If installed by a Lumora Certified Installer, the warranty can be extended to a total of 4 years from delivery.
- Reference: The Thermostat T3 has a 3-year (36-month) limited warranty from the date of delivery, one year longer than the T2. It can be extended to 4 years when installed by a Lumora Certified Installer, under the conditions of the Limited Warranty Policy.

**CF-02. What does error E4 mean on the Thermostat T3?**

- Answer: On the Thermostat T3, error E4 refers to a humidity sensor fault. The recommended action is to power-cycle the device; if the issue persists, a warranty claim should be initiated.
- Reference: On the T3, E4 means a humidity sensor fault: power-cycle the thermostat and start a warranty claim if it persists. (Network problems are reported as E12 on the T3; E4 means a network problem only on the T2.)

**OOS-01. Who is the CEO of Lumora Home Systems?**

- Answer: I'm sorry, I couldn't find this information in the available documents, so I can't answer this question.
- Reference: The documents do not contain this information; the assistant should refuse.

**OOS-02. How do I make pizza dough at home?**

- Answer: I'm sorry, I couldn't find this information in the available documents, so I can't answer this question.
- Reference: The question is unrelated to the documents; the assistant should refuse.

**OOS-03. Does the Thermostat T3 work with Apple HomeKit?**

- Answer: I'm sorry, I couldn't find this information in the available documents, so I can't answer this question.
- Reference: The documents do not mention HomeKit compatibility; the assistant should refuse rather than guess.

**OOS-04. What was Lumora's total revenue last year?**

- Answer: I'm sorry, I couldn't find this information in the available documents, so I can't answer this question.
- Reference: The documents do not contain financial results; the assistant should refuse.

**OOS-05. Write a Python function that sorts a list of numbers.**

- Answer: I'm sorry, I couldn't find this information in the available documents, so I can't answer this question.
- Reference: The request is out of scope for a support assistant; it should refuse.

</details>

## Method

- Every question is sent to the same `answer_question()` function the API uses (no HTTP), one at a time, so latency is end-to-end for one request.
- **Citation hit**: an in-scope answer counts as correct when its sources include at least one expected document page (`expected_sources` in `eval/questions.yaml`). A refusal counts as a miss.
- **Refusal rates**: out-of-scope refusal rate = refused / out-of-scope questions; false refusal rate = refused / in-scope questions.
- **RAGAS** (v0.4) scores in-scope questions only, using `openai/gpt-4o-mini` as the judge. Faithfulness and answer relevancy are not scored for refusals (a refusal makes no claims).
- **Cost** = chat tokens (question rewrite and answer) + query embedding tokens, at $0.15 / $0.60 per 1M input / output tokens and $0.02 per 1M embedding tokens. Evaluation (judge) calls are not included.
- Raw data: `eval/reports/results.csv` (one row per question) and `eval/reports/metrics.json`.
- Reproduce: `make ingest && make eval`. Parameter sweep: `make eval-tune`.
