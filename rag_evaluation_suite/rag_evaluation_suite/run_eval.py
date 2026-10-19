import csv
import json
import re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
ABSTAIN = "I don't know based on the provided documents."

def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def normalize(text):
    return re.sub(r"[^a-z0-9%.$-]+", " ", text.lower()).strip()

def retrieve(question, documents, vectorizer, matrix, k=3):
    qv = vectorizer.transform([question])
    scores = cosine_similarity(qv, matrix).ravel()
    ranked = sorted(range(len(documents)), key=lambda i: float(scores[i]), reverse=True)
    # A conservative lexical confidence floor: if the top similarity is too low,
    # abstain rather than pretending every question has a source.
    if not ranked or float(scores[ranked[0]]) < 0.08:
        return []
    return [{"doc_id": documents[i]["doc_id"], "score": float(scores[i])}
            for i in ranked[:k] if float(scores[i]) > 0.0]

def generate(question, retrieved, docs_by_id):
    if not retrieved:
        return ABSTAIN
    text = docs_by_id[retrieved[0]["doc_id"]]["text"]
    # Extractive baseline: choose the sentence with greatest overlap with query terms.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    q_terms = set(normalize(question).split())
    stop = {"what","which","how","long","many","does","the","is","are","for","a","an","of","to","in","on","and","must","required","have","has","within","when","who"}
    q_terms -= stop
    ranked = sorted(sentences, key=lambda s: len(q_terms & set(normalize(s).split())), reverse=True)
    return ranked[0] if ranked and len(q_terms & set(normalize(ranked[0]).split())) else ABSTAIN

def answer_is_correct(answer, qa):
    if qa["status"] == "unanswerable":
        return answer.strip().lower() == ABSTAIN.lower()
    if answer.strip().lower() == ABSTAIN.lower():
        return False
    norm = normalize(answer)
    # Required phrase tokens are all required; punctuation is normalized away.
    return all(normalize(term) in norm for term in qa["answer_keywords"])

def main():
    RESULTS.mkdir(exist_ok=True)
    docs = load_jsonl(DATA / "corpus.jsonl")
    qas = load_jsonl(DATA / "questions.jsonl")
    docs_by_id = {d["doc_id"]: d for d in docs}
    corpus_texts = [d["title"] + ". " + d["text"] for d in docs]
    vectorizer = TfidfVectorizer(ngram_range=(1,2), lowercase=True, sublinear_tf=True)
    matrix = vectorizer.fit_transform(corpus_texts)

    rows = []
    reciprocal_ranks = []
    hit1 = hit3 = answerable_count = generation_correct = 0
    unanswerable_count = unanswerable_abstained = false_positive = 0

    for qa in qas:
        ranked = retrieve(qa["question"], docs, vectorizer, matrix, k=3)
        ids = [x["doc_id"] for x in ranked]
        gold = qa["gold_source_id"]
        if qa["status"] == "answerable":
            answerable_count += 1
            rank = ids.index(gold) + 1 if gold in ids else 0
            hit1 += rank == 1
            hit3 += rank > 0
            reciprocal_ranks.append(1 / rank if rank else 0.0)
        else:
            unanswerable_count += 1
            if ranked:
                false_positive += 1

        answer = generate(qa["question"], ranked, docs_by_id)
        correct = answer_is_correct(answer, qa)
        generation_correct += bool(correct)
        if qa["status"] == "unanswerable" and correct:
            unanswerable_abstained += 1

        rows.append({
            "question_id": qa["question_id"],
            "question": qa["question"],
            "status": qa["status"],
            "gold_source_id": gold or "",
            "retrieved_top1": ids[0] if ids else "",
            "retrieved_top3": ";".join(ids),
            "gold_source_rank_top3": (ids.index(gold)+1) if gold in ids else 0,
            "retrieval_hit_at_1": int(bool(gold and ids and ids[0] == gold)),
            "retrieval_hit_at_3": int(bool(gold and gold in ids)),
            "generated_answer": answer,
            "gold_answer": qa["gold_answer"] or "",
            "generation_correct_keyword_proxy": int(bool(correct)),
            "retrieval_top1_score": round(ranked[0]["score"], 4) if ranked else 0.0,
        })

    with open(RESULTS / "per_question.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "corpus_documents": len(docs),
        "total_questions": len(qas),
        "answerable_questions": answerable_count,
        "unanswerable_questions": unanswerable_count,
        "retrieval": {
            "hit_at_1": round(hit1 / answerable_count, 4),
            "hit_at_3": round(hit3 / answerable_count, 4),
            "mrr": round(sum(reciprocal_ranks) / answerable_count, 4),
        },
        "generation": {
            "all_questions_correct_keyword_proxy": round(generation_correct / len(qas), 4),
            "answerable_questions_correct_keyword_proxy": round(
                sum(r["generation_correct_keyword_proxy"] for r in rows if r["status"] == "answerable") / answerable_count, 4),
            "unanswerable_abstention_accuracy": round(unanswerable_abstained / unanswerable_count, 4),
        },
        "unanswerable": {
            "retrieval_false_positive_rate_any_ranked_doc": round(false_positive / unanswerable_count, 4),
            "note": "Proxy only; calibrate a similarity threshold on a separate validation set."
        },
        "scoring_note": "Generation correctness is an automated required-keyword proxy, not human-judged semantic correctness."
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md = [
        "# Results table", "",
        f"Questions: **{len(qas)}** ({answerable_count} answerable, {unanswerable_count} unanswerable).", "",
        "| Dimension | Metric | Result |",
        "|---|---|---:|",
        f"| Retrieval | Hit@1 (answerable only) | {summary['retrieval']['hit_at_1']:.1%} |",
        f"| Retrieval | Hit@3 (answerable only) | {summary['retrieval']['hit_at_3']:.1%} |",
        f"| Retrieval | MRR (answerable only) | {summary['retrieval']['mrr']:.3f} |",
        f"| Generation | Correct, answerable questions (keyword proxy) | {summary['generation']['answerable_questions_correct_keyword_proxy']:.1%} |",
        f"| Generation | Correct across all questions (keyword proxy) | {summary['generation']['all_questions_correct_keyword_proxy']:.1%} |",
        f"| Abstention | Unanswerable abstention accuracy | {summary['generation']['unanswerable_abstention_accuracy']:.1%} |",
        f"| Abstention | Unanswerable retrieval false-positive rate | {summary['unanswerable']['retrieval_false_positive_rate_any_ranked_doc']:.1%} |",
        "", "## Interpretation", "",
        "- **Retrieval and generation are measured separately.** Hit@k/MRR use the known source ID and do not depend on the generated answer.",
        "- The generation score is a deterministic keyword proxy. It is useful for a repeatable baseline but does not establish human-level semantic correctness.",
        "- Unanswerable questions test whether the system can abstain. A ranked document is not automatically evidence that it answers the question, so the false-positive retrieval rate is only a diagnostic.",
        "- Inspect `per_question.csv` to identify failure cases. For a review-ready claim, manually label at least 10–20 outputs (including misses and unanswerables), ideally with a second reviewer, and report agreement.",
        "- These scores are from the included demonstration baseline and corpus. Replace the adapter functions with the actual RAG system before claiming its performance."
    ]
    (RESULTS / "results_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {RESULTS/'per_question.csv'}")
    print(f"Wrote {RESULTS/'summary.json'}")
    print(f"Wrote {RESULTS/'results_table.md'}")

if __name__ == "__main__":
    main()
