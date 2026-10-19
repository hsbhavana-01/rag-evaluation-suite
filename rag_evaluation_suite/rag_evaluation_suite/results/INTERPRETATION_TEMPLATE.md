# Written analysis template

Replace the bracketed fields after running the evaluation against your actual RAG pipeline.

## Setup
- Corpus/version: [name, date, document count]
- Evaluation set: [N] questions, [A] answerable, [U] deliberately unanswerable
- Retrieval configuration: [embedding/model, vector DB, top-k]
- Generation configuration: [LLM, prompt version, temperature]
- Scoring: retrieval Hit@1, Hit@3, MRR; generation correctness judged against reference answers; abstention accuracy on unanswerable questions.

## Results
- Hit@1: [x%]
- Hit@3: [x%]
- MRR: [x]
- Generation correctness on answerable questions: [x%]
- Unanswerable abstention accuracy: [x%]

## Interpretation
Retrieval and generation should not be collapsed into one score. If Hit@3 is high but generation correctness is low, the source is usually being found but the generator may be misreading, omitting, or inventing details. If Hit@3 is low, improving prompts alone is unlikely to fix the main problem; inspect chunk boundaries, metadata filters, query rewriting, and embeddings. If abstention accuracy is low, calibrate a confidence threshold using a separate validation set and test again on held-out questions.

## Limitations and next steps
The automated keyword metric is a proxy and may penalize valid paraphrases. Manually review failed cases and a random sample of successful cases. Keep the final evaluation set held out from prompt and retrieval tuning. Record versions and rerun the suite after changes.
