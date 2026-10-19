# RAG Evaluation Suite

A small, reproducible evaluation harness that separates **retrieval quality** from **answer-generation quality**. It includes 40 questions (38 answerable, 2 deliberately unanswerable), a compact fictional policy corpus, a baseline lexical retriever, an extractive baseline answerer, per-question results, aggregate metrics, and an interpretation template.

> **Important:** The included corpus and scores are a reproducible demonstration fixture, not results from your production/assignment RAG system. To report results for your actual RAG app, connect its retriever/generator using the adapter interface described below and rerun the evaluation.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python run_eval.py
```

The runner uses scikit-learn TF-IDF + cosine similarity for retrieval and a simple extractive answer baseline. It writes:
- `results/per_question.csv`
- `results/summary.json`
- `results/results_table.md`

No API key or paid service is required.

## What is scored

### Retrieval (independent of generation)
- **Hit@1**: the gold source document is ranked first.
- **Hit@3**: the gold source document appears in the top three.
- **MRR**: mean reciprocal rank of the gold source (0 when absent).
- **Unanswerable false-positive retrieval**: fraction of unanswerable questions for which the baseline ranks any document above the abstention threshold. This is a simple proxy; a production system should calibrate a retrieval-confidence threshold on a validation set.

### Generation (independent of retrieval)
The extractive baseline selects a sentence from the retrieved top document. Answer correctness is checked against question-specific required keywords in the generated answer. For answerable questions, a question is counted correct only when **all** expected keywords are present. For unanswerable questions, the answer is correct only if the system abstains with `I don't know based on the provided documents.`

This is an automated proxy, not a substitute for human review. It can mark a semantically correct paraphrase wrong and can miss unsupported claims. For a defensible review, inspect the per-question CSV and manually audit a sample; ideally have two reviewers label correctness and resolve disagreements.

## Dataset format

`data/corpus.jsonl`: `doc_id`, `title`, `text`

`data/questions.jsonl`: `question_id`, `question`, `gold_source_id`, `gold_answer`, `answer_keywords`, `status`

Every answerable question has a known source document and answer. The two unanswerable questions intentionally ask for facts absent from the entire corpus.

## Plug in your RAG system

Edit `run_eval.py`:
- Replace `retrieve(question, documents, k)` with your vector database / hybrid retrieval call. Return a ranked list of document IDs.
- Replace `generate(question, retrieved_docs)` with your actual generator. Return the final answer string.
- Keep the evaluation functions unchanged so the benchmark stays comparable.
- If your app uses chunk IDs rather than document IDs, store `gold_source_id` as the source document ID and map retrieved chunks back to source documents before scoring.

Do not tune your system on the held-out evaluation questions and then present the same score as an unbiased test result. Use a development set for tuning and keep a separate test set for final reporting.
