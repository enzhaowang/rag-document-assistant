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
