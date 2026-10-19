# Results table

Questions: **40** (38 answerable, 2 unanswerable).

| Dimension | Metric | Result |
|---|---|---:|
| Retrieval | Hit@1 (answerable only) | 97.4% |
| Retrieval | Hit@3 (answerable only) | 97.4% |
| Retrieval | MRR (answerable only) | 0.974 |
| Generation | Correct, answerable questions (keyword proxy) | 89.5% |
| Generation | Correct across all questions (keyword proxy) | 85.0% |
| Abstention | Unanswerable abstention accuracy | 0.0% |
| Abstention | Unanswerable retrieval false-positive rate | 100.0% |

## Interpretation

- **Retrieval and generation are measured separately.** Hit@k/MRR use the known source ID and do not depend on the generated answer.
- The generation score is a deterministic keyword proxy. It is useful for a repeatable baseline but does not establish human-level semantic correctness.
- Unanswerable questions test whether the system can abstain. A ranked document is not automatically evidence that it answers the question, so the false-positive retrieval rate is only a diagnostic.
- Inspect `per_question.csv` to identify failure cases. For a review-ready claim, manually label at least 10–20 outputs (including misses and unanswerables), ideally with a second reviewer, and report agreement.
- These scores are from the included demonstration baseline and corpus. Replace the adapter functions with the actual RAG system before claiming its performance.
