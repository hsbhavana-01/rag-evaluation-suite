# Evaluation analysis

## Executive summary

The included baseline was evaluated on **40 questions** over **12 fictional policy documents**: 38 answerable questions with known source documents and reference answers, plus 2 deliberately unanswerable questions. The experiment separates source retrieval from answer correctness.

| Dimension | Metric | Result |
|---|---|---:|
| Retrieval | Hit@1, answerable questions | 97.37% (37/38) |
| Retrieval | Hit@3, answerable questions | 97.37% (37/38) |
| Retrieval | Mean reciprocal rank (MRR) | 0.974 |
| Generation | Correct answerable outputs, required-keyword proxy | 89.47% (34/38) |
| Generation | Correct across all questions, required-keyword proxy | 85.00% (34/40) |
| Abstention | Correct abstentions on unanswerable questions | 0% (0/2) |
| Unanswerable handling | Any document retrieved for unanswerable questions | 100% (2/2) |

## Interpretation

**Retrieval is strong on this small, in-domain fixture.** The correct source document is ranked first for 37 of 38 answerable questions. Hit@3 matches Hit@1, so the one retrieval miss is not recovered by expanding the candidate list from one document to three. This suggests the next diagnostic step is to inspect that miss and test query wording, chunking, and retrieval representation rather than assuming a larger top-k will solve it.

**Generation is weaker than retrieval.** The answerer passes the required-keyword proxy for 34 of 38 answerable questions (89.47%), despite the correct source being retrieved for 37. This illustrates why retrieval and generation must be reported separately: locating the right passage does not guarantee that the final response includes the expected fact in the expected form.

**Abstention is the clearest failure.** Both deliberately unanswerable questions caused at least one document to be retrieved, and the extractive baseline did not return the required abstention response. Abstention accuracy is therefore 0% on this tiny two-question sample. This is not enough data to estimate a reliable production rate, but it is a useful failure signal: the current baseline has no robust evidence-sufficiency check. A production implementation should calibrate a retrieval-confidence threshold using a separate validation set and should test whether the retrieved passage actually entails an answer, rather than treating any lexical match as sufficient.

## Can these numbers be defended?

They are **reproducible baseline measurements**, not a claim about a deployed or previously built RAG application. The retrieval scores use known source document IDs; the generation score uses a deterministic all-required-keywords check. That check is transparent and repeatable, but it is not a full semantic judge: it can mark a correct paraphrase wrong and can fail to detect unsupported claims. The corpus is intentionally small and synthetic, so the results should not be generalized to a real document collection.

For a review of the actual project, replace `retrieve()` and `generate()` in `run_eval.py` with the project's real retriever and generator, run the same 40 questions, then manually review all errors plus a random sample of successful answers. Keep this evaluation set held out from prompt tuning. If possible, use two reviewers and report agreement. Do not present the fixture scores as the performance of the actual RAG app.

## Reproduction

```bash
pip install -r requirements.txt
python run_eval.py
```

The script regenerates `results/per_question.csv`, `results/summary.json`, and `results/results_table.md`.
