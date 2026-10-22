# Evaluation Summary: Lumora Document Assistant

_Generated 2026-10-22T17:35:54+08:00 by `make eval` - 20 questions - chat model `openai/gpt-4o-mini` - chunk 500/80 tokens, top-k 6, threshold 0.40._

## Bottom line

- **All 4 quality targets were met.**
- Of the 15 questions whose answer is in the documents, the assistant answered 15 and cited the correct document and page for 15 (100%).
- It declined 5 of 5 questions that the documents do not cover (for example "Who is the CEO of Lumora Home Systems?"): it never invented an answer.
- 15 of 15 answers contain every key fact of the reference answer.
- On average 98% of the statements in an answer are directly supported by the quoted source passages (RAGAS faithfulness).
- An answer takes 3.0 s on average and costs about $0.0004 in API fees (about $0.39 per 1,000 questions).

## Scorecard

| Metric | What it measures | Result | Target | Status |
|---|---|---|---|---|
| Faithfulness | Share of statements in an answer that are backed by the source passages (no made-up facts). | 0.98 | >= 0.85 | Met |
| Citation hit rate | Answers that cite the correct document and page. | 100% | >= 85% | Met |
| Out-of-scope refusal rate | Questions the documents do not cover that the assistant declined instead of guessing. | 100% | = 100% | Met |
| In-scope false refusal rate | Questions the documents do cover that the assistant wrongly declined. | 0% | <= 10% | Met |
| Key fact accuracy | Answers that contain every key fact of the reference answer (numbers, names, codes), checked word for word. | 100% | - | - |
| Answer relevancy | How directly the answer addresses the question. | 0.89 | - | - |
| Context precision | Whether the passages that contain the answer are ranked first. | 0.76 | - | - |
| Context recall | Whether the passages given to the model contain everything in the reference answer. | 0.97 | - | - |
| Retrieval hit rate (top-k) | Questions where the page with the answer was among the passages retrieved by the search step. | 100% | - | - |
| Average latency | - | 3.0 s | - | - |
| 95th percentile latency | - | 3.9 s | - | - |
| Average cost per question | - | $0.00039 | - | - |

## Results by question type

The 20 questions are based on facts in the sample documents: 10 single facts (numbers, steps, error codes), 3 facts that span two pages or sit in a table, 2 facts that differ between the similar T2 and T3 thermostats, and 5 questions the documents do not answer.

| Question type | Questions | Passed | Correct citation | Refused |
|---|---|---|---|---|
| Single fact | 10 | 9/10 | 10/10 | 0/10 |
| Cross-page / table | 3 | 3/3 | 3/3 | 0/3 |
| Confusable (T2 vs T3) | 2 | 2/2 | 2/2 | 0/2 |
| Out of scope | 5 | 5/5 | - | 5/5 |

## Failure analysis

**SF-09 (Single fact): Does a T2 customer without a C-wire have to pay for the Power Extender Kit PEK-1?**

- What went wrong: The right page was cited, but only 67% of the statements in the answer are supported by the retrieved passages (RAGAS faithfulness).
- Expected source: Product Guide - Lumora Thermostat T2.pdf p.4
- Assistant's answer: "A T2 customer without a C-wire can receive the Power Extender Kit PEK-1 free of charge if they request it within 60 days of delivery. After that, it costs $24.99."
- Cited: Product Guide - Lumora Thermostat T2.pdf p.4
- Top retrieved: Product Guide - Lumora Thermostat T2.pdf p.4 (0.62); Product Guide - Lumora Thermostat T3.pdf p.4 (0.53); Product Guide - Lumora Thermostat T3.pdf p.3 (0.51)


### Risks and near misses

- 3 of 5 out-of-scope questions scored above the relevance threshold (0.40) and were stopped by the model's own refusal, not by the threshold: OOS-01 (0.53), OOS-03 (0.58), OOS-04 (0.51). These questions sound like real support topics, so the second safety layer matters.
- The weakest in-scope match was CP-02 (best score 0.42, threshold 0.40). A higher threshold would start refusing questions like this one.
- For SF-03 (rank 4), SF-04 (rank 5) the page with the answer was ranked below the top 3 passages; a smaller top-k would lose these answers.
- Low context precision (below 0.50): SF-03 (0.25), SF-04 (0.37), SF-05 (0.45).

## Recommendations

1. Some answers contain statements that are not in the passages. Tighten the prompt ('only facts from the excerpts') or use a stronger model.
2. Re-run this evaluation with 15-20 real questions from your support team before go-live; the harness is ready (`eval/questions.yaml` + `make eval`).
3. Keep the evaluation in the delivery checklist: re-run `make eval` after adding documents or changing models, and compare against this report.
4. Most questions that are not covered by the documents still look similar to real topics (for example a product feature that is not documented). They are caught by the model's refusal, not by the score threshold, so keep out-of-scope questions in every test set.

## Per-question details

| ID | Question | Outcome | Cited | Key facts | Top score | Faith. | Relev. | Ctx prec. | Ctx rec. | Latency | Cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SF-01 | Who has to approve a refund of $800 on a single order? | Answered | SOP - Returns and Refunds.pdf p.4; SOP - Returns and Refunds.pdf p.3 | 1/1 | 0.60 | 1.00 | 0.84 | 0.68 | 1.00 | 3.9 s | $0.00045 |
| SF-02 | What does error code E7 mean on the Thermostat T2? | Answered | Product Guide - Lumora Thermostat T2.pdf p.6 | 2/2 | 0.78 | 1.00 | 0.99 | 0.70 | 1.00 | 3.3 s | $0.00036 |
| SF-03 | How do I factory reset a Lumora Thermostat T2? | Answered | Product Guide - Lumora Thermostat T2.pdf p.5 | 2/2 | 0.67 | 1.00 | 0.98 | 0.25 | 1.00 | 3.7 s | $0.00055 |
| SF-04 | How long do customers have to return a product they bought directly from Lumora? | Answered | SOP - Returns and Refunds.pdf p.1 | 2/2 | 0.66 | 1.00 | 0.85 | 0.37 | 1.00 | 3.3 s | $0.00050 |
| SF-05 | What are the first response and resolution targets for a P1 critical ticket? | Answered | SOP - Ticket Escalation.pdf p.1 | 2/2 | 0.60 | 1.00 | 0.97 | 0.45 | 1.00 | 2.6 s | $0.00046 |
| SF-06 | What format do RMA numbers use, and how long is an RMA valid? | Answered | SOP - RMA Process.pdf p.1 | 2/2 | 0.66 | 1.00 | 0.96 | 0.83 | 1.00 | 3.1 s | $0.00050 |
| SF-07 | How many failed sign-in attempts lock a Lumora account, and for how long? | Answered | FAQ - App and Account.pdf p.1 | 2/2 | 0.55 | 1.00 | 0.62 | 1.00 | 1.00 | 2.7 s | $0.00051 |
| SF-08 | How much does a Lumora Plus subscription cost? | Answered | FAQ - Billing and Subscriptions.pdf p.3 | 2/2 | 0.70 | 1.00 | 0.89 | 1.00 | 1.00 | 2.9 s | $0.00050 |
| SF-09 | Does a T2 customer without a C-wire have to pay for the Power Extender Kit PEK-1? | Answered, low faithfulness | Product Guide - Lumora Thermostat T2.pdf p.4 | 2/2 | 0.62 | 0.67 | 0.84 | 0.67 | 1.00 | 3.3 s | $0.00042 |
| SF-10 | How quickly must the Safety Officer be notified about a safety case? | Answered | SOP - Ticket Escalation.pdf p.3 | 1/1 | 0.60 | 1.00 | 0.98 | 1.00 | 1.00 | 2.5 s | $0.00017 |
| CP-01 | In which cases is a C-wire mandatory for the Thermostat T3? | Answered | Product Guide - Lumora Thermostat T3.pdf p.4 | 3/3 | 0.68 | 1.00 | 0.96 | 0.71 | 1.00 | 3.3 s | $0.00047 |
| CP-02 | How does the holiday return extension work, and which orders are excluded? | Answered | SOP - Returns and Refunds.pdf p.1; SOP - Returns and Refunds.pdf p.2 | 5/5 | 0.42 | 1.00 | 0.60 | 1.00 | 1.00 | 3.9 s | $0.00026 |
| CP-03 | List all refund approval levels by refund amount per order. | Answered | SOP - Returns and Refunds.pdf p.4; SOP - Returns and Refunds.pdf p.3 | 5/5 | 0.55 | 1.00 | 0.89 | 1.00 | 1.00 | 4.1 s | $0.00039 |
| CF-01 | How long is the warranty on the Thermostat T3? | Answered | Policy - Limited Warranty.pdf p.2; Product Guide - Lumora Thermostat T3.pdf p.7 | 1/1 | 0.69 | 1.00 | 0.97 | 0.95 | 1.00 | 3.8 s | $0.00054 |
| CF-02 | What does error E4 mean on the Thermostat T3? | Answered | Product Guide - Lumora Thermostat T3.pdf p.5 | 1/1 | 0.69 | 1.00 | 0.99 | 0.72 | 0.50 | 3.3 s | $0.00037 |
| OOS-01 | Who is the CEO of Lumora Home Systems? | Refused (correct) | - | - | 0.53 | - | - | - | - | 2.7 s | $0.00047 |
| OOS-02 | How do I make pizza dough at home? | Refused (correct) | - | - | 0.15 | - | - | - | - | 1.4 s | $0.00000 |
| OOS-03 | Does the Thermostat T3 work with Apple HomeKit? | Refused (correct) | - | - | 0.58 | - | - | - | - | 3.8 s | $0.00044 |
| OOS-04 | What was Lumora's total revenue last year? | Refused (correct) | - | - | 0.51 | - | - | - | - | 2.0 s | $0.00048 |
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

- Answer: Customers may return any product bought directly from Lumora within 30 calendar days of the delivery date, for any reason. If the delivery is between November 15 and December 31, returns can be made until January 31 of the following year, or within the standard 30 days if that is later.
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

- Answer: A T2 customer without a C-wire can receive the Power Extender Kit PEK-1 free of charge if they request it within 60 days of delivery. After that, it costs $24.99.
- Reference: The PEK-1 is free for T2 customers who request it within 60 days of delivery; after that it costs $24.99. Only Tier 2 Technical Support may authorize a free PEK-1 outside the 60-day window.

**SF-10. How quickly must the Safety Officer be notified about a safety case?**

- Answer: The Safety Officer must be notified through the safety hotline queue within 1 hour of the first report of a safety case.
- Reference: Within 1 hour of the first report, at any time of day, through the safety hotline queue.

**CP-01. In which cases is a C-wire mandatory for the Thermostat T3?**

- Answer: A C-wire is mandatory for the Thermostat T3 in the following cases: 1. Heat pump systems that use auxiliary or emergency heat. 2. Any system with more than one cooling stage. 3. Homes where the T3 controls a humidifier or dehumidifier through the ACC terminals.
- Reference: The T3 usually runs without a C-wire, but a C-wire or the PEK-1 is mandatory for heat pump systems that use auxiliary or emergency heat, any system with more than one cooling stage, and homes where the T3 controls a humidifier or dehumidifier through the ACC terminals. Otherwise the T3 shows error E10 within 24 hours.

**CP-02. How does the holiday return extension work, and which orders are excluded?**

- Answer: Orders delivered between November 15 and December 31 can be returned until January 31 of the following year, or within the standard 30 days if that is later. This extension applies to both change-of-mind and defective returns, but does not apply to orders placed by business accounts or to orders containing more than five units of the same product.
- Reference: Orders delivered between November 15 and December 31 can be returned until January 31 of the following year (or within the standard 30 days if that is later). The extension does not apply to business accounts or to orders with more than five units of the same product. Agents select the reason modifier HOL in OMS.

**CP-03. List all refund approval levels by refund amount per order.**

- Answer: Refund approval levels by refund amount per order are as follows: 1. Up to $250.00 - Customer Care agent (Tier 1) - Approve in OMS directly. 2. $250.01 to $1,000.00 - Team Lead - Approval request in OMS; Team Lead responds within 4 business hours. 3. $1,000.01 to $5,000.00 - Customer Care Manager - Attach order history and ticket summary. 4. Above $5,000.00 - Customer Care Manager and Finance Controller - Both approvals required before the refund is released.
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
