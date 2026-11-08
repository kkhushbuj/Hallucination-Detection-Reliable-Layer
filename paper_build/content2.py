# -*- coding: utf-8 -*-
# Content blocks, part 2: method and evaluation protocol.
B2 = []
A = B2.append

A(("h1", "3. Method"))
A(("h2", "3.1 Overview"))
A(("pf",
   "For a question <i>q</i>, the pipeline produces one answer, a trust score between 0 and 100, a label and a written "
   "reason. It has six steps (Figure 3.1). A writer model produces three independent answers. A second model decides "
   "which of those answers reach the same conclusion. For each answer, a web search supplies context and three judges "
   "from three other developers return one verdict each. Each answer is scored from the verdicts and the agreement, and "
   "the highest-scoring answer is chosen. A further model then checks the chosen answer, and the score is reduced if it "
   "disagrees with the judge majority. Finally the score is mapped to a label."))
A(("p",
   "Every role is filled by a model from a different developer (Table 3.1). This separation is the central design rule. "
   "It is motivated by the self-preference results of Panickssery et al. (2024) and the self-enhancement bias reported "
   "by Zheng et al. (2023), and by the finding of Kim et al. (2025) that errors are more strongly correlated within a "
   "provider than across providers. The rule reduces the chance that a model grades its own work. It does not make the "
   "models independent, as Section 6 explains."))
A(("fig", "fig_pipeline.png", 5.6,
   "Figure 3.1 — The trust-score pipeline. Orange boxes are the agreement check and the tie-breaker; green boxes are web grounding and the output."))
A(("table", "Table 3.1 — Models, roles and settings used in the evaluated configuration.",
   ["Role", "Model (provider)", "Developer", "Setting"],
   [["Writer", "gpt-4o-mini (OpenAI API)", "OpenAI", "3 calls, T = 0.9"],
    ["Agreement checker", "Gemini 3.5 Flash-Lite (Gemini API)", "Google", "T = 0, YES or NO"],
    ["Judge 1", "Qwen3.8-27B (Groq)", "Alibaba", "T = 0, low reasoning effort"],
    ["Judge 2", "Mistral Medium 3.5 (OpenRouter)", "Mistral AI", "T = 0, max 512 tokens"],
    ["Judge 3", "Llama 3.3 70B Instruct (OpenRouter)", "Meta", "T = 0, max 512 tokens"],
    ["Tie-breaker", "Nemotron 3.5 Lightning 30B (NVIDIA API)", "NVIDIA", "T = 0, winner only"],
    ["Web search", "Tavily, basic depth", "Tavily", "top 3 results plus summary"],
    ["Grader (evaluation only)", "Claude Haiku 5.5 (OpenRouter)", "Anthropic", "T = 0, YES or NO"]],
   [96, 160, 66, 132]))

A(("h2", "3.2 Answer Generation"))
A(("pf",
   "The writer, gpt-4o-mini, receives the question and answers it three times at temperature 0.9, each call independent "
   "of the others. Sampling at a temperature above zero follows the practice of Wang et al. (2023), who sample diverse "
   "outputs and compare them, and of Manakul et al. (2023), who use sampled passages as evidence about the main answer. "
   "A system instruction, sent with every model call in the pipeline, tells the model that when a question concerns "
   "something that does not exist, such as a fake study, person or event, it must say so and stop, without inventing "
   "details. If a generation call fails, the pipeline continues with the answers that were returned, and if all three "
   "fail it returns a score of zero with an error label."))
A(("p",
   "Three samples is a small number. Manakul et al. (2023) report results with larger numbers of samples, and the "
   "value of three here is a cost decision made because every extra sample multiplies the number of judge calls "
   "(Section 3.10). Section 6 lists this as a limitation."))

A(("h2", "3.3 Agreement Check"))
A(("h3", "3.3.1 What the check does"))
A(("pf",
   "The agreement check supplies the self-consistency signal. The checker receives two answers and is asked whether "
   "they reach the <i>same final conclusion</i>. The prompt states that extra explanation or detail in one answer does "
   "not count as disagreement, and it gives a worked example in which a bare number and a step-by-step derivation of "
   "the same number agree. The model must reply with one word, YES or NO, at temperature 0. Answers are then grouped "
   "greedily. Answer 1 is compared with answers 2 and 3, the first answer not yet assigned starts a new group, and "
   "so on, which costs two or three checker calls per question. For one answer, the consistency fraction is the share of "
   "the <i>other</i> answers that fall in its group. With three answers it takes the values 0, 0.5 or 1."))
A(("p",
   "The design follows the idea of Kuhn et al. (2023) and Farquhar et al. (2024), who group sampled answers into "
   "meaning classes using bidirectional entailment and measure the spread of those classes. We use the group sizes in a "
   "simpler way, as the share of agreeing answers, because the score must be easy to explain. An entropy value over the "
   "groups is also computed and shown to the user, but it is not part of the trust score."))
A(("h3", "3.3.2 Why a Gemini checker and not an NLI model"))
A(("pf",
   "The obvious alternative is the NLI approach of Kuhn et al. (2023), who check entailment in both directions with a "
   "DeBERTa-large model fine-tuned on MNLI, with the question added as context because a short reply such as “Paris.” "
   "does not entail “The capital of France is Paris” without it. We chose an LLM prompt instead, for four reasons, "
   "the first of which is the strongest."))
A(("bul", [
    "<b>Published evidence favours the prompted LLM for consistency scoring.</b> Manakul et al. (2023) compared an NLI "
    "variant of SelfCheckGPT with a variant that prompts an LLM (ChatGPT) to judge consistency. In their Table 2 the "
    "prompted variant scored higher on every reported metric: sentence-level AUC-PR of 93.42 against 92.50 on "
    "non-factual sentences, 53.19 against 45.17 on the harder non-factual subset and 67.09 against 66.08 on factual "
    "sentences, and a passage-level Pearson correlation of 78.32 against 74.14. The data were GPT-3 passages about "
    "people, so the comparison is indirect for short factual answers, but it is the closest published test of the "
    "choice that we know of.",
    "<b>Our answers are short statements with variable extra detail.</b> A reply such as “Bell, who received the first US "
    "patent for the telephone in 1876” and a reply that is only “Bell” reach the same conclusion. A strict two-way "
    "entailment test can label such a pair neutral and so count it as disagreement, which would lower the consistency "
    "score for the wrong reason. The prompt states the rule that extra detail is not disagreement. This reasoning is a "
    "hypothesis. It was not tested on our data (Section 6).",
    "<b>Deployment weight.</b> An NLI classifier needs a deep-learning runtime and a model file of about one gigabyte "
    "on the server, and it slows the first request of the public web page. The Gemini checker is an API call.",
    "<b>Role separation.</b> Gemini is from a developer that plays no other role in the pipeline, which keeps the checker "
    "from agreeing with answers that resemble its own output (Panickssery et al., 2024).",
]))
A(("p",
   "The choice has costs that we accept and state. An LLM checker is not perfectly repeatable and adds a small API cost "
   "per question, while an NLI model is free to run and deterministic. Kuhn et al. (2023) validated their NLI checker "
   "manually and reported high agreement with people on short TriviaQA and CoQA answers (about 93% on TriviaQA, "
   "taken from their appendix). We have not run an equivalent validation for the Gemini checker, so the superiority of the "
   "LLM checker for our data is a design judgment supported by indirect evidence and is not a measured result. Hand "
   "labelling 30 answer sets and comparing both checkers would turn it into one."))

A(("h2", "3.4 Web Grounding and the Judges"))
A(("pf",
   "For each answer the pipeline runs one web search with the query “question plus answer”, using Tavily at basic depth, "
   "and keeps the generated summary and the titles and contents of the top three results. This context is added to the "
   "prompt of every judge for that answer. If the search fails, the judges receive the question and answer alone. The "
   "motivation is the evidence that retrieval reduces hallucination in generation (Shuster et al., 2021; Lewis et al., "
   "2020) and that external knowledge helps LLMs recognise hallucinations (Li et al., 2023). Section 6 notes that web "
   "grounding was not switched off in a separate run, so its effect on the score is not measured."))
A(("p",
   "Each judge sees the question, the proposed answer, the search context and one instruction: based on its own "
   "knowledge and the context, is the answer factually correct and not hallucinated? It must reply with one word, "
   "CORRECT or HALLUCINATED, at temperature 0. The reply is read with a conservative parser. Negations such as "
   "HALLUCINATED, INCORRECT, NOT CORRECT, NOT ACCURATE and WRONG are tested first and return a negative verdict, only then "
   "is the word CORRECT accepted, and an unreadable reply makes the judge count as failed. This order avoids a "
   "known pitfall, because a plain substring test for CORRECT would also accept INCORRECT."))
A(("p",
   "The panel has three judges from three developers: Qwen3.8-27B (Alibaba, through Groq), Mistral Medium 3.5 (Mistral AI) "
   "and Llama 3.3 70B (Meta). Three developers are used because Kim et al. (2025) found that error correlation rises "
   "with shared provider and architecture, so judges from one provider would add less information. The same paper "
   "found that accurate models from different providers are still correlated, which is why the panel cannot be "
   "described as independent. Judging one answer at a time, not comparing two, means that the position bias reported "
   "by Wang et al. (2024) does not apply, while the other biases listed by Zheng et al. (2023) remain possible. When a "
   "judge fails, for example because of a rate limit, the pipeline retries with waiting and drops the judge if it still "
   "fails, so that one failed call does not stop a question."))

A(("h2", "3.5 Scoring"))
A(("pf",
   "Let <i>m</i> be the number of judges that responded for answer <i>i</i>, let <i>v<sub>ij</sub></i> be 1 when judge "
   "<i>j</i> returned CORRECT and 0 otherwise, and let <i>c<sub>i</sub></i> be the consistency fraction of answer "
   "<i>i</i>. The score of the answer is"))
A(("eq", "S<sub>i</sub> = ( Σ<sub>j</sub> v<sub>ij</sub> + c<sub>i</sub> ) / ( m + 1 )"))
A(("pf",
   "Each responding judge and the consistency fraction therefore carry an equal share of the score. With three judges, "
   "each of the four parts is worth 25 points, and because <i>c<sub>i</sub></i> takes three values, scores are multiples "
   "of 12.5 (0, 12.5, 25, … 100). If a judge fails, the shares are renormalised so that the maximum stays 100. The answer "
   "with the highest score is shown, and ties go to the first answer. The reported trust score is that score times 100."))
A(("p",
   "Equal weights are a simplicity choice. We did not fit the weights to data, because no labelled development set was "
   "reserved for that purpose, and Section 4.5 shows that the equal-weight sum is not clearly better than a "
   "judge-only signal. The score also treats a judge vote and the consistency fraction as comparable, an assumption that "
   "has no direct support in the literature."))

A(("pf",
   "Table 3.4 shows how the rule works on illustrative cases. The numbers are arithmetic from the formula and are not "
   "results. A score of exactly 75 is the lowest that reaches the Medium label, and a single failed judge changes the "
   "grid of possible scores."))
A(("table", "Table 3.4 — Worked examples of the scoring rule (illustrative arithmetic, not data).",
   ["Judges responding", "Judges correct", "Consistency fraction", "Tie-breaker", "Trust score", "Label"],
   [["3", "3", "1.0", "agrees", "100", "High"],
    ["3", "3", "0.5", "agrees", "87.5", "High"],
    ["3", "2", "1.0", "agrees", "75", "Medium"],
    ["3", "2", "0.5", "agrees", "62.5", "Low"],
    ["3", "3", "1.0", "disagrees", "90", "High"],
    ["3", "2", "1.0", "disagrees", "65", "Low"],
    ["3", "1", "0", "agrees", "25", "Low"],
    ["2 (one failed)", "1", "1.0", "agrees", "66.7", "Low"],
    ["2 (one failed)", "2", "0.5", "agrees", "83.3", "High"]],
   [80, 66, 84, 68, 62, 52]))

A(("h2", "3.6 Tie-Breaker"))
A(("h3", "3.6.1 What the tie-breaker does"))
A(("pf",
   "A further model, NVIDIA Nemotron 3.5 Lightning 30B, receives the question and only the winning answer and returns one "
   "verdict with the same prompt as the judges but without the search context. If its verdict differs from the "
   "majority of the three judges for that answer, the score is reduced by 10 points (not below 0), and the reason shown "
   "to the user adds a caution that an independent check disagreed. If the tie-breaker fails, the score is not changed. "
   "The tie-breaker makes one call per question, not three, because it checks only the winner."))
A(("h3", "3.6.2 Why a tie-breaker"))
A(("pf", "We added it for three reasons. Its effect could be tested only indirectly (Section 4.6)."))
A(("bul", [
    "<b>A further developer for the cases that matter.</b> Judges from three developers can still share an error "
    "(Kim et al., 2025). A further model from another developer adds one more opinion at the point where a "
    "wrong answer would otherwise be shown with high confidence. It cannot remove shared mistakes, but it gives the panel "
    "a chance to be contradicted.",
    "<b>Cross-checking by several models has a published benefit for factual accuracy.</b> Du et al. (2024) report that "
    "several model instances that propose and debate answers reduce factual errors and hallucinations. Their method "
    "mostly used copies of one model and a debate procedure, so we treat it as motivation for a second check, not as "
    "evidence for this particular design.",
    "<b>Low cost.</b> One call on the winner adds a small fraction of the roughly sixteen calls that a question needs.",
]))
A(("p",
   "The size of the penalty, 10 points, is a design choice that we did not tune. The evaluation file does not store the "
   "tie-breaker’s verdict, but the penalty leaves a trace in the score. An unpenalised score is a multiple of 12.5, or a "
   "multiple of 16.7 when a judge failed, so a score that lies on neither grid must have been reduced by 10 points. "
   "Section 4.6 uses this to estimate how often the tie-breaker disagreed and what it did to the ranking. This is an "
   "inference from the scoring rule and not a logged event, and it does not replace a run with the tie-breaker switched "
   "off (Section 7)."))

A(("h2", "3.7 Confidence Labels"))
A(("pf",
   "A score of 80 or more is labelled High confidence, a score from 75 up to but not including 80 is labelled Medium "
   "confidence, and a lower score is labelled Low confidence. These cutoffs have not changed since the first commit "
   "of the repository (16 August 2026), which is before the seed-7 questions were drawn, and none was fitted to the "
   "seed-7 results. The repository also holds a script that explores thresholds on an earlier 200-question run (seed 42), "
   "so the cutoffs may have been informed by that run. The seed-7 sample excludes every one of its questions, so the "
   "labels are tested on questions that did not shape them, although we cannot rule out that the cutoffs were set with "
   "similar models and benchmarks in mind. Because the scores are multiples of 12.5 when all judges "
   "respond, the Medium band is in practice narrow. A score of 75 is Medium, 83.3 and above is High, and a penalised "
   "score such as 77.5 can also be Medium."))

A(("table", "Table 3.2 — Design decisions, the evidence behind them and whether this paper tests them.",
   ["Decision", "Main supporting evidence", "Tested here?"],
   [["Sample several answers and compare", "Wang et al. (2023); Manakul et al. (2023)", "Not isolated"],
    ["LLM agreement check, not NLI", "Manakul et al. (2023), Table 2; Kuhn et al. (2023) for the NLI alternative", "No"],
    ["Judges from three developers", "Kim et al. (2025); Panickssery et al. (2024); Zheng et al. (2023)", "Not isolated"],
    ["Web search for the judges", "Shuster et al. (2021); Li et al. (2023); Lewis et al. (2020)", "No"],
    ["Tie-breaker on the winner", "Du et al. (2024); Kim et al. (2025)", "Partly (Section 4.6, inferred)"],
    ["Grader from a separate developer", "Panickssery et al. (2024); Kamalloo et al. (2023)", "No (not checked against people)"],
    ["Equal weights, 10-point penalty", "None (design choices)", "Partly (Sections 4.5 and 4.6)"]],
   [140, 214, 100]))

A(("h2", "3.8 Evaluation Data"))
A(("pf",
   "The test set has 200 questions drawn from three benchmarks: 66 from TruthfulQA (Lin et al., 2022), 66 from the "
   "question-answering part of HaluEval (Li et al., 2023) and 68 from the validation split of TriviaQA (Joshi et al., "
   "2017). The set was sampled with random seed 7 and with every question of the earlier seed-42 run removed, so the "
   "two samples do not overlap. Each benchmark supplies a reference answer (the best answer for TruthfulQA, the right "
   "answer for HaluEval and the answer value for TriviaQA). The 200 questions were processed in four batches of 50, and "
   "the batches were merged into one file. Rows that failed during a batch, for example because of a rate limit, were "
   "re-run with the script’s backfill option, and the merged file holds a score for all 200 questions. We use a single "
   "run and a single seed."))
A(("table", "Table 3.3 — Composition of the 200-question evaluation set (seed 7).",
   ["Benchmark", "Questions", "Reference", "Role in the study"],
   [["TruthfulQA", "66", "Best answer", "Common misconceptions"],
    ["HaluEval (QA)", "66", "Right answer", "Hallucination detection"],
    ["TriviaQA (validation)", "68", "Answer value", "Factual recall"],
    ["Total", "200", "", ""]],
   [120, 70, 110, 154]))

A(("h2", "3.9 Ground Truth, Metrics and Statistics"))
A(("h3", "3.9.1 The grader and why it is a separate model"))
A(("pf",
   "Whether an answer is correct is decided by Claude Haiku 5.5, which receives the question, the reference answer and the "
   "model’s answer and is asked whether the answer conveys the same core truth as the reference, ignoring extra "
   "explanation, tone and length. It replies YES or NO at temperature 0, and the answer counts as correct only when the "
   "reply starts with YES. We use a language-model grader because exact matching against a gold answer underestimates "
   "generative models (Kamalloo et al., 2023), and because the answers here are free text of variable length."))
A(("pf",
   "The grader comes from Anthropic, a developer that plays no other role. Using a different developer for grading avoids "
   "the situation in which a model that took part in the scoring also decides what is correct, and so avoids the "
   "self-preference reported by Panickssery et al. (2024) and the self-enhancement bias described by Zheng et al. (2023). "
   "The code supports majority voting across several graders, but one grader was used. Kamalloo et al. (2023) report that "
   "automated evaluators cannot fully replace human evaluation, and we have not measured how often this grader agrees with "
   "people. Cohen’s (1960) kappa on a human-labelled subsample is the planned check (Section 7). Until it is done, "
   "every accuracy and AUROC in this paper is conditional on the grader."))
A(("h3", "3.9.2 Metrics"))
A(("bul", [
    "<b>Accuracy</b> is the share of questions whose chosen answer the grader marks correct.",
    "<b>Score gap</b> is the mean trust score of correct answers minus the mean trust score of incorrect answers.",
    "<b>AUROC</b> is the probability that a randomly chosen correct answer has a higher trust score than a randomly chosen "
    "incorrect one, with ties counted as half (Fawcett, 2006). It is computed from ranks. A value of 0.5 means no "
    "separation, and unlike the gap it does not depend on the scale of the score.",
    "<b>Brier score</b> (Brier, 1950) is the mean squared difference between the score divided by 100 and the outcome (1 for "
    "correct, 0 for incorrect). The reference value is the Brier score of always predicting the observed accuracy.",
    "<b>Expected calibration error</b> (Guo et al., 2017) is computed with five equal-width bins of the score.",
    "<b>Flagging analysis</b> treats a score below a threshold as a prediction that the answer is wrong, and reports the "
    "share of flagged answers that are wrong (precision), the share of wrong answers that were flagged (recall) and the "
    "accuracy of the answers that are not flagged.",
]))
A(("pf",
   "Intervals are 95% percentile bootstrap intervals from 5,000 resamples of the 200 questions with a fixed seed "
   "(Efron and Tibshirani, 1993). The comparison of two scores on the same questions uses the same resamples for both, "
   "so the interval for the difference accounts for the pairing. With only 200 questions the intervals are wide, and "
   "differences smaller than their width should not be read as findings."))

A(("h2", "3.10 Implementation, Cost and Deployment"))
A(("pf",
   "The pipeline is written in Python with a one-node LangGraph graph and calls every provider through one function that "
   "speaks the OpenAI chat interface, with a separate client for Groq. A question needs three writer calls, two or "
   "three agreement calls, nine judge calls, one tie-breaker call and three web searches, about sixteen model calls and "
   "three searches in total, and one more call when the grader is used during evaluation. The calls to the judges are "
   "the largest part of the cost, which is the reason for keeping the number of samples at three."))
A(("p",
   "The same code serves a public web page, https://trust.145-241-213-220.sslip.io, built with FastAPI. It runs on an "
   "Oracle Cloud ARM virtual machine (4 cores and 24 GB of memory, Ubuntu 22.04) behind a Caddy proxy that provides "
   "HTTPS. The service runs under systemd with a 4 GB memory limit so that it cannot starve other services on the same "
   "machine. To protect the model quotas, each visitor is limited to six questions per minute and at most eight "
   "verification runs may be in progress at once, with a short wait before a busy response is returned. A health route "
   "reports that the service is running. The source code is in the public repository listed under Declarations."))
