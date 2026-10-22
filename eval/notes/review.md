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
