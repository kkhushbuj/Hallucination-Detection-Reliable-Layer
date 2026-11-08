# -*- coding: utf-8 -*-
# Content blocks, part 4: appendices.
B4 = []
A = B4.append

A(("h1", "Appendix A. Prompts Used in the Pipeline"))
A(("pf",
   "The prompts are reproduced from the source code, with typographic dashes and arrows simplified. Text in braces is "
   "filled in at run time. Every call also carries the system instruction in the first block."))
A(("prompt",
   "SYSTEM INSTRUCTION (sent with every model call)\n"
   "If the user asks about something that does not exist (a fake study, fake person, fake event, fake\n"
   "citation, etc.), clearly state that it does not exist and STOP there. Do not invent hypothetical\n"
   "details, fake findings, fake quotes, or fictional elaboration, even if you label it as imaginative\n"
   "or hypothetical."))
A(("prompt",
   "WRITER (three calls, temperature 0.9)\n"
   "{question}"))
A(("prompt",
   "AGREEMENT CHECK (Gemini 3.5 Flash-Lite, temperature 0)\n"
   "Answer A: {answer_a}\n\n"
   "Answer B: {answer_b}\n\n"
   "Do these two answers reach the SAME final conclusion? IMPORTANT: one answer may include extra\n"
   "explanation, steps, or detail that the other doesn't have; this does NOT count as disagreement.\n"
   "Only judge based on the final conclusion/result itself.\n\n"
   "Example: 'The answer is 12.' and 'To solve this, multiply 80 by 0.15, which equals 12.' -> these\n"
   "AGREE, both conclude 12.\n\n"
   "Respond with ONLY the single word YES or the single word NO. Do not include any explanation or\n"
   "other text."))
A(("prompt",
   "JUDGE (three models, temperature 0)\n"
   "Question: {question}\n\n"
   "Proposed answer: {answer}\n\n"
   "Web search context:\n{summary and top three results}      (omitted when the search fails)\n\n"
   "Based on your own knowledge and the web search context above, is this answer factually correct\n"
   "and not hallucinated? Respond with exactly one word: CORRECT or HALLUCINATED."))
A(("prompt",
   "TIE-BREAKER (Nemotron 3.5 Lightning, temperature 0, winning answer only, no search context)\n"
   "Question: {question}\n\n"
   "Proposed answer: {winning answer}\n\n"
   "Based on your own knowledge, is this answer factually correct and not hallucinated? Respond with\n"
   "exactly one word: CORRECT or HALLUCINATED."))
A(("prompt",
   "GRADER (Claude Haiku 5.5, temperature 0, evaluation only)\n"
   "Question: {question}\n\n"
   "Expected correct answer: {reference}\n\n"
   "Model's actual answer: {answer}\n\n"
   "Does the model's answer convey the same core truth/conclusion as the expected correct answer, even\n"
   "if worded very differently or with more detail? Ignore extra explanation, tone, or length. Focus\n"
   "only on whether the core factual conclusion matches.\n\n"
   "Respond with exactly one word: YES or NO."))

A(("h1", "Appendix B. Distribution of Trust Scores"))
A(("pf",
   "Table B.1 lists every score that occurred in the seed-7 run. Scores such as 15, 40, 65, 77.5 and 90 lie off the grid "
   "of unpenalised scores and are the ones attributed to the tie-breaker penalty in Section 4.6. Scores such as 33.3, "
   "66.7 and 83.3 arise when a judge failed."))
_dist = [(0, 5, 0), (15, 1, 0), (25, 3, 1), (33.3, 1, 0), (40, 5, 3), (50, 12, 2), (56.7, 2, 0), (62.5, 3, 1),
         (65, 2, 0), (66.7, 3, 2), (73.3, 1, 1), (75, 18, 10), (77.5, 2, 1), (83.3, 5, 4), (87.5, 1, 1), (90, 4, 1),
         (100, 132, 95)]
_rows = [[("%g" % sc), str(n), str(c), str(n - c), "%.1f%%" % (100.0 * c / n)] for sc, n, c in _dist]
_rows.append(["Total", "200", "122", "78", "61.0%"])
A(("table", "Table B.1 — Number of answers and correct answers at each trust score (seed-7 run).",
   ["Trust score", "Answers", "Correct", "Wrong", "Share correct"], _rows, [90, 70, 70, 70, 100]))

A(("h1", "Appendix C. Reproducing the Results"))
A(("pf",
   "The evaluation uses the scripts in the repository. Each command needs the provider keys in a local environment "
   "file. The run for this paper used the seed-7 sample."))
A(("code",
   "python evaluation/evaluate.py --seed 7 --batch 1     # repeat for --batch 2, 3 and 4\n"
   "python evaluation/evaluate.py --seed 7 --backfill    # re-run failed rows, then merge\n"
   "python evaluation/evaluate.py --seed 7 --merge       # write results_seed7_final.csv"))
A(("pf",
   "The statistics in Section 4 are computed from <font face='Courier'>results_seed7_final.csv</font>, which has one row per "
   "question with the columns question, source, model_answer, best_answer, trust_score, label, flagged_count, "
   "majority_flagged and correct. The bootstrap uses 5,000 resamples with random seed 7. Because the models are hosted and "
   "the writer samples at temperature 0.9, a new run will not reproduce the same answers exactly."))

A(("h1", "Appendix D. Evidence Behind the Main Statements"))
A(("pf",
   "Table D.1 lists the main statements about the world that the paper makes, the source, and what the source "
   "actually covers. Statements about our own system rest on our own data (Section 4) or are labelled as design choices."))
A(("table", "Table D.1 — Statements, their sources and the scope of each source.",
   ["Statement", "Source", "Scope of the source"],
   [["Calibrated models must hallucinate on facts seen once", "Kalai and Vempala (2024)", "Theory; hallucination not inevitable overall"],
    ["Confabulation is flagged by variation over meaning", "Farquhar et al. (2024)", "One error type"],
    ["Sampling several answers and taking the most frequent helps", "Wang et al. (2023)", "Reasoning tasks, four models"],
    ["Facts recur across samples, invented ones diverge", "Manakul et al. (2023)", "GPT-3 passages about people"],
    ["Prompted LLM beat NLI for consistency scoring", "Manakul et al. (2023), Table 2", "Passage and sentence level, not short answers"],
    ["Meaning classes by bidirectional entailment", "Kuhn et al. (2023)", "DeBERTa-large MNLI, QA datasets"],
    ["Black-box confidence close to white-box", "Xiong et al. (2024)", "Five dataset types, five models"],
    ["Stated confidence is better calibrated than token probabilities", "Tian et al. (2023)", "RLHF models on three benchmarks"],
    ["LLM judges agree with people over 80%", "Zheng et al. (2023)", "Chat preferences"],
    ["Judges favour their own writing", "Panickssery et al. (2024); Zheng et al. (2023)", "Summarisation; chat"],
    ["Models cannot self-correct reasoning without feedback", "Huang et al. (2024)", "Reasoning"],
    ["Errors correlate across models and providers", "Kim et al. (2025)", "350+ models; leaderboards"],
    ["Models imitate human falsehoods; larger ones less truthful", "Lin et al. (2022)", "817 questions, GPT-3 era models"],
    ["Retrieval cuts hallucination", "Shuster et al. (2021)", "Dialogue, Wikipedia"],
    ["External knowledge helps detection", "Li et al. (2023)", "HaluEval"],
    ["Lexical matching underestimates generative QA", "Kamalloo et al. (2023)", "Open-domain QA"],
    ["Several instances debating reduce factual errors", "Du et al. (2024)", "Mostly one model family"]],
   [196, 130, 128]))
