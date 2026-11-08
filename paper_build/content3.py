# -*- coding: utf-8 -*-
# Content blocks, part 3: results, discussion, limitations, conclusion, declarations.
B3 = []
A = B3.append

A(("h1", "4. Results"))
A(("h2", "4.1 Overview"))
A(("pf",
   "All 200 questions produced an answer and a score. The writer’s chosen answer was correct for 122 questions, an "
   "accuracy of 61.0% (95% interval 54.5–67.5). The mean trust score was 93.1 for correct answers and 74.9 for incorrect "
   "answers, a gap of 18.1 points (interval 11.1–25.5). The AUROC was 0.674 (interval 0.604–0.740). The interval "
   "excludes 0.5, so the score separates correct from incorrect answers better than chance, but the separation is "
   "moderate. Table 4.1 gives these and the calibration figures, which are discussed in Section 4.4."))
A(("table", "Table 4.1 — Main results on the 200 fresh questions (95% bootstrap intervals in brackets).",
   ["Measure", "Value"],
   [["Questions", "200"],
    ["Accuracy of the chosen answer", "61.0% [54.5, 67.5]"],
    ["Mean trust score, correct answers", "93.1"],
    ["Mean trust score, incorrect answers", "74.9"],
    ["Score gap (correct minus incorrect)", "18.1 [11.1, 25.5]"],
    ["AUROC", "0.674 [0.604, 0.740]"],
    ["Answers with trust score 100", "132 (37 of them wrong, 28.0%)"],
    ["Answers with trust score 0", "5 (all five wrong)"],
    ["Brier score (reference: 0.238)", "0.272"],
    ["Expected calibration error (5 bins)", "0.250"]],
   [270, 184]))
A(("pf",
   "Figure 4.1 shows where the answers fall. Most answers, 132 of 200, received the maximum score, and 95 of those were "
   "correct. The score is discrete, because three judges and a three-valued consistency fraction produce multiples of "
   "12.5, so the figure groups the values into five bands. The share of wrong answers is 73% in the 0–49 band (11 of 15) "
   "and 74% in the 50–74 band (17 of 23), 44% at exactly 75 (8 of 18), 42% in the 76–99 band (5 of 12) and 28% at 100 "
   "(37 of 132)."))
A(("fig", "fig_hist.png", 4.1,
   "Figure 4.1 — Trust score of the chosen answer, grouped into five bands, split by whether the grader marked it correct. "
   "Labels give the number of wrong answers in each band."))

A(("h2", "4.2 Results by Benchmark"))
A(("pf",
   "The separation differs by benchmark (Table 4.2 and Figure 4.2). TriviaQA gave the highest AUROC (0.700), with a gap of "
   "24.9 points, and the writer was correct on 70.6% of its 68 questions. HaluEval gave an AUROC of 0.686 and a gap of 17.3, "
   "but the writer was correct on only 43.9% of its 66 questions, so this benchmark was the hardest for the writer. "
   "TruthfulQA gave the weakest separation, an AUROC of 0.568 and a gap of 9.3 points, even though the writer was "
   "correct on 68.2% of its questions. The interval for TruthfulQA (0.450–0.682) includes 0.5, so on this sample we "
   "cannot say that the score separates correct from incorrect answers on TruthfulQA at all. The intervals for all "
   "three benchmarks overlap, so the ordering of the benchmarks is suggestive and not established."))
A(("table", "Table 4.2 — Results by benchmark (AUROC with 95% bootstrap interval).",
   ["Benchmark", "n", "Accuracy", "Mean trust, correct", "Mean trust, wrong", "Gap", "AUROC [interval]"],
   [["TriviaQA", "68", "70.6%", "92.5", "67.5", "24.9", "0.700 [0.564, 0.823]"],
    ["HaluEval", "66", "43.9%", "89.6", "72.3", "17.3", "0.686 [0.564, 0.800]"],
    ["TruthfulQA", "66", "68.2%", "95.9", "86.7", "9.3", "0.568 [0.450, 0.682]"],
    ["All", "200", "61.0%", "93.1", "74.9", "18.1", "0.674 [0.604, 0.740]"]],
   [80, 30, 62, 66, 60, 40, 122]))
A(("fig", "fig_bench.png", 4.1,
   "Figure 4.2 — Accuracy and mean trust score by benchmark. The gap between the blue and orange bars is the score gap."))
A(("pf",
   "The pattern for TruthfulQA is the one expected from the design of the benchmark. Lin et al. (2022) built the questions "
   "so that models imitate human falsehoods, and they found that larger models were generally less truthful. When "
   "a false belief is common in the training text, every model in the panel may hold it, which is the situation in which "
   "agreement and cross-model verdicts add little (Kim et al., 2025). Our data are consistent with this explanation, "
   "but they do not test it, because we did not analyse which questions the judges got wrong together."))

A(("h2", "4.3 Confidence Labels and Flagging"))
A(("pf",
   "The labels were ordered as intended (Table 4.3 and Figure 4.3a). Of the 142 answers labelled High confidence, 71.1% "
   "were correct. Of the 20 labelled Medium, 55.0% were correct, and of the 38 labelled Low, 26.3% were correct. The "
   "High label is therefore not a guarantee, because more than one in four answers with that label were wrong. The "
   "Medium band holds only 20 answers, so its 55.0% rests on a small number and has a wide interval."))
A(("table", "Table 4.3 — Accuracy by confidence label.",
   ["Label", "Score range", "Answers", "Share of all answers", "Correct"],
   [["High confidence", "80 or more", "142", "71.0%", "71.1%"],
    ["Medium confidence", "75 to below 80", "20", "10.0%", "55.0%"],
    ["Low confidence", "below 75", "38", "19.0%", "26.3%"]],
   [100, 90, 56, 112, 96]))
A(("fig", "fig_calib.png", 5.5,
   "Figure 4.3 — (a) Accuracy for each confidence label. (b) Reliability diagram with four bins of the trust score. "
   "The dashed line is perfect calibration."))
A(("pf",
   "Table 4.4 treats a score below a threshold as a prediction that the answer is wrong. With the strictest rule, flagging "
   "everything below 100, 68 answers are flagged and 60.3% of them are wrong. Flagging at the Low cutoff (below 75) "
   "flags 38 answers, and 73.7% of those are wrong, but only 35.9% of all wrong answers are caught. The accuracy of "
   "the answers that are not flagged is between 64% and 72% for every threshold, against 61.0% overall, so "
   "filtering by score improves the accuracy of what remains by about eleven points at most."))
A(("table", "Table 4.4 — Flagging answers whose trust score is below a threshold as likely wrong.",
   ["Flag if score below", "Flagged", "Wrong among flagged", "Wrong answers caught", "Accuracy of the rest"],
   [["100", "68", "60.3%", "52.6%", "72.0% (132 kept)"],
    ["80", "58", "63.8%", "47.4%", "71.1% (142 kept)"],
    ["75", "38", "73.7%", "35.9%", "69.1% (162 kept)"],
    ["66.7", "34", "79.4%", "34.6%", "69.3% (166 kept)"],
    ["50", "15", "73.3%", "14.1%", "63.8% (185 kept)"]],
   [90, 52, 106, 106, 100]))

A(("h2", "4.4 Calibration"))
A(("pf",
   "The score should not be read as a probability. The Brier score of the trust score divided by 100 was 0.272, which is "
   "worse than 0.238, the Brier score of a constant forecast equal to the observed accuracy of 61%. The expected "
   "calibration error with five equal-width bins was 0.250. Figure 4.3b shows why. The 136 answers with a mean score of "
   "0.997 were correct 70.6% of the time, and the 23 answers with a mean score of 0.57 were correct only 26.1% of the time, "
   "no better than the 15 answers with a mean score of 0.22 (26.7%). The score orders the answers but its numerical "
   "value is too high, which is the kind of miscalibration that Guo et al. (2017) describe for modern models and that "
   "Xiong et al. (2024) report for verbalised confidence."))

A(("h2", "4.5 Which Signal Carries the Information?"))
A(("pf",
   "The saved results do not contain the per-judge votes, the consistency fraction or the tie-breaker verdict, so the "
   "components of the score cannot be separated exactly. They do contain, for each question, how many of the three "
   "generated answers were flagged as hallucinated by at least one judge. The share of answers that no judge flagged "
   "is a signal that uses judge verdicts only, over all three answers, with no consistency fraction and no tie-breaker. "
   "It is a proxy, not a clean ablation, because it uses the verdicts on all three answers and not only on the winner."))
A(("pf",
   "This judge-flag proxy ranked answers at least as well as the full trust score (Table 4.5). Its AUROC was 0.721 "
   "(interval 0.655–0.782) against 0.674 for the trust score, a difference of +0.046 whose paired interval "
   "(−0.005 to +0.098) just includes zero. The data therefore do not show that adding the agreement check and the "
   "tie-breaker improved the ranking, and a reader should not conclude from this table that they hurt it either. "
   "Accuracy fell steadily as judges flagged more of the three answers (Table 4.6). When no judge flagged any answer "
   "(138 questions), 75.4% of the chosen answers were correct. When all three answers were flagged (22 questions), only "
   "13.6% were."))
A(("table", "Table 4.5 — Ranking quality of the trust score and of a judge-only proxy on the same 200 questions.",
   ["Signal", "AUROC [95% interval]"],
   [["Trust score (agreement, judges, tie-breaker)", "0.674 [0.604, 0.740]"],
    ["Judge-flag proxy (answers no judge flagged)", "0.721 [0.655, 0.782]"],
    ["Difference, proxy minus trust score (paired)", "+0.046 [−0.005, +0.098]"]],
   [270, 184]))
A(("table", "Table 4.6 — Accuracy by the number of the three answers that no judge flagged.",
   ["Answers no judge flagged", "Questions", "Chosen answer correct"],
   [["0 of 3", "22", "13.6%"],
    ["1 of 3", "15", "33.3%"],
    ["2 of 3", "25", "40.0%"],
    ["3 of 3", "138", "75.4%"]],
   [150, 100, 204]))
A(("pf",
   "Two simple flagging rules based on the same field give a comparison with Table 4.4. Flagging a question when any judge "
   "flagged any of the three answers flags 62 questions, 71.0% of which are wrong, and catches 56.4% of the wrong "
   "answers. Flagging when more than half of the answers were flagged flags 37 questions, 78.4% of which are wrong, and "
   "catches 37.2% of the wrong answers. The first rule flags about as many questions as the strictest score rule in Table "
   "4.4 (62 against 68) and is more precise (71.0% against 60.3%) with a similar recall (56.4% against 52.6%)."))

A(("h2", "4.6 What the Scores Reveal About the Tie-Breaker and Failed Judges"))
A(("pf",
   "Section 3.5 gives the grids on which scores can fall. With three judges an unpenalised score is a multiple of 12.5. "
   "With one failed judge it is a multiple of 16.7. A score on neither grid must have had the 10-point tie-breaker "
   "penalty applied, and a score on the second grid only, such as 33.3, 66.7 or 83.3, shows that a judge failed and the "
   "shares were renormalised. Reading the saved scores this way gives the counts in Table 4.7. It relies on the scoring "
   "rule being as described and on no other step changing the score, and it is an inference, not a logged event."))
A(("p",
   "The tie-breaker disagreed with the judge majority on 17 of the 200 answers (8.5%). Only 6 of those 17 answers "
   "(35.3%) were correct, against 116 of the other 183 (63.4%), a difference of 28.1 points whose interval "
   "(2.3 to 51.6) excludes zero. Adding the 10 points back to those 17 scores lowers the AUROC from 0.674 to 0.661, so "
   "the penalty raised the AUROC by 0.013 (paired interval −0.003 to +0.033). The tie-breaker therefore flagged a group of "
   "answers that were mostly wrong, but its overall effect on the ranking is small and cannot be told apart from zero "
   "with 200 questions. Eleven of the 17 penalised answers received a Low label, four High and two Medium. "
   "At least 12 answers (6.0%) have scores that arise only when a judge failed. The true number is larger, because a "
   "failure that leaves the score on the main grid, such as 50 or 100, cannot be seen."))
A(("table", "Table 4.7 — Tie-breaker penalties and failed judges, inferred from the saved scores.",
   ["Quantity", "Value"],
   [["Answers with the 10-point penalty", "17 of 200 (8.5%)"],
    ["Correct among penalised answers", "6 of 17 (35.3%)"],
    ["Correct among other answers", "116 of 183 (63.4%)"],
    ["Difference in accuracy (other minus penalised)", "+28.1 points [2.3, 51.6]"],
    ["AUROC with the penalty / with it added back", "0.674 / 0.661"],
    ["Effect of the penalty on AUROC (paired)", "+0.013 [−0.003, +0.033]"],
    ["Score gap with the penalty / with it added back", "18.1 / 17.2"],
    ["Answers whose score shows a failed judge (lower bound)", "12 of 200 (6.0%)"]],
   [270, 184]))

A(("h2", "4.7 Summary of Findings"))
A(("bul", [
    "<b>RQ1.</b> The score separates correct from incorrect answers moderately well (AUROC 0.674, interval 0.604–0.740; gap "
    "18.1 points, interval 11.1–25.5).",
    "<b>RQ2.</b> The separation is strongest on TriviaQA (0.700) and HaluEval (0.686) and not distinguishable from chance on "
    "TruthfulQA (0.568, interval 0.450–0.682), although the intervals overlap.",
    "<b>RQ3.</b> The labels are ordered (71.1%, 55.0% and 26.3% correct for High, Medium and Low), but the score is not a "
    "calibrated probability, and 28.0% of answers with the maximum score were wrong.",
    "<b>RQ4.</b> A judge-only proxy ranked at least as well as the full score (0.721). The tie-breaker disagreed on 8.5% of "
    "answers, mostly wrong ones, but added only +0.013 to the AUROC (interval −0.003 to +0.033). The effects of the "
    "agreement check and of web search were not isolated and remain open.",
]))

# ------------------------------------------------------------------ 5 Discussion
A(("h1", "5. Discussion"))
A(("h2", "5.1 What the Results Support"))
A(("pf",
   "The main supported statement is a modest one. On 200 fresh questions the trust score ranked correct answers above "
   "incorrect ones more often than chance, with an AUROC near 0.67, and the three labels sorted the answers into groups "
   "with clearly different accuracy. That is useful for triage. A user who sees a Low label has good reason to check "
   "the answer, because about three in four such answers were wrong. The results do not support stronger statements. "
   "The score does not make the answer more accurate, since the layer only chooses among three samples from the writer, "
   "and we did not measure whether that choice beats a random sample. The score is not a probability. And a High label "
   "leaves more than a quarter of the answers wrong."))
A(("h2", "5.2 Why High Scores Can Still Be Wrong"))
A(("pf",
   "Of the 132 answers with the maximum score, 37 were wrong (15 from TruthfulQA, 13 from HaluEval and 9 from TriviaQA). "
   "Three explanations are consistent with the design and with the literature. The first is shared belief. Kim et al. "
   "(2025) found that models often make the same wrong choice, and that the correlation does not disappear across "
   "providers, so three judges and a Gemini checker can all accept a false claim that the writer also believes. Agreement "
   "between samples cannot expose it, because a model can be consistently wrong, as Farquhar et al. (2024) note when "
   "they restrict their claim to confabulations. The second is abstention. The writer was told not to invent details, "
   "and when it replies that it cannot find information about a person, the judges tend to count the reply as not "
   "hallucinated, while the grader compares it with the reference and marks it incorrect. The third is the reference "
   "itself, which for some questions is ambiguous or follows a convention that the answer does not."))
A(("pf",
   "To illustrate these three explanations, we read nine of the 37 wrong top-scoring answers chosen at random "
   "(random seed 3). This is an informal reading and not a measured result. Three were abstentions, such as a reply "
   "that no information could be found about a named person. Three involved an ambiguous or conventional reference, "
   "for example a question about the Nobel Peace Prize in 1920, where the answer names one laureate and the reference "
   "names a different person. Three were plausible but wrong or hedged "
   "answers, such as one that repeats a popular but disputed meaning of a phrase. These examples suggest that part of "
   "the apparent error rate comes from the single LLM grader and the references, not only from the pipeline, which is "
   "why Section 3.9 treats every accuracy as conditional on the grader."))
A(("h2", "5.3 The Judge-Only Result"))
A(("pf",
   "The judge-flag proxy matched or exceeded the full score in this sample, and the paired difference was not "
   "statistically distinguishable from zero. This does not show that agreement or the tie-breaker are useless. The "
   "proxy sees the verdicts on all three answers, and the trust score sees the verdicts on each answer separately and "
   "then picks the winner, so the two are not the same quantity. The result is a reason for follow-up, not for a "
   "design change. One plausible explanation for a weak agreement signal is that three samples give the consistency "
   "fraction only three values, while Manakul et al. (2023) report results with larger numbers of samples (their "
   "main results use 20). Whether more samples would help here is untested. The tie-breaker, in contrast, flagged a "
   "group of answers that were mostly wrong (Section 4.6), although its effect on the ranking was small."))
A(("h2", "5.4 Use in Practice"))
A(("pf",
   "The results suggest three rules for presenting the score. First, show the label and the reasons, such as how many "
   "judges confirmed the answer and whether the answers agreed, and avoid presenting the number as a probability. "
   "Second, treat the Low label as a request to verify and the High label as the absence of a warning, not as a "
   "guarantee. Third, do not rely on the score for questions about common misconceptions, where our evidence of "
   "separation is weakest. The public page follows the first rule by showing the judges’ verdicts and any tie-breaker "
   "caution next to the score."))
A(("h2", "5.5 Relation to Earlier Work"))
A(("pf",
   "The AUROC values of this study cannot be compared directly with published ones. Xiong et al. (2024) report AUROC "
   "values for failure prediction on other models and datasets (0.522 for black-box and 0.605 for white-box methods in "
   "one comparison), Kuhn et al. (2023) and Farquhar et al. (2024) use semantic entropy with open models, and "
   "Manakul et al. (2023) evaluate passage-level detection with a different metric. What the present results add is a "
   "measurement of a layer that combines several of these ideas, on questions from three benchmarks, with intervals."))

# ------------------------------------------------------------------ 6 Limitations
A(("h1", "6. Limitations and Threats to Validity"))
A(("pf", "Every result above has to be read with the following limits."))
A(("bul", [
    "<b>The grader is a model, not a person.</b> Correctness is decided by Claude Haiku 5.5 against a reference answer. "
    "We did not measure its agreement with human labels, which Kamalloo et al. (2023) identify as the safeguard "
    "that automated evaluation still needs. Section 5.2 shows cases where the reference or the grader, and not the "
    "pipeline, may explain a wrong label. Every accuracy and AUROC is conditional on the grader.",
    "<b>Small sample and a single run.</b> There are 200 questions, one seed and one run, so the intervals are wide and "
    "many differences are within noise. The per-benchmark intervals overlap. Model outputs at temperature 0.9 are not "
    "reproducible bit for bit, and hosted models change over time, so a repeat run may give different numbers.",
    "<b>Judges are not independent.</b> The three judges come from three developers, but Kim et al. (2025) show that "
    "accurate models from different providers still make correlated errors. The 28.0% of wrong answers at the "
    "maximum score and the weak TruthfulQA result are consistent with this.",
    "<b>Agreement is not truth.</b> The consistency fraction measures whether the writer repeats itself. A consistently "
    "wrong writer scores full consistency. With three samples it takes only three values.",
    "<b>The agreement prompt leans towards agreement.</b> The prompt tells the checker that extra detail is not "
    "disagreement. That is intended, but it can raise the consistency score for answers that differ in substance.",
    "<b>The components were not isolated.</b> There is no run with web search, the tie-breaker or the agreement check "
    "switched off, and the saved results do not store per-judge votes, the consistency fraction or the tie-breaker "
    "verdict. The effect of the tie-breaker is inferred from the scores (Section 4.6). The Gemini checker was not compared with an NLI checker on our data. The effect of web grounding on the "
    "judges was not measured. These are design choices supported by indirect evidence (Table 3.2).",
    "<b>Equal weights and the penalty are untuned.</b> The equal weights and the 10-point penalty were not fitted, "
    "and the judge-only proxy suggests the sum may not be optimal.",
    "<b>Cutoffs.</b> The 80 and 75 cutoffs have not changed since 16 August 2026 and none was fitted to the seed-7 "
    "results, but a script that explores thresholds on an earlier run exists, so we cannot call the label evaluation "
    "fully out-of-sample.",
    "<b>Failures are not logged per question.</b> The evaluation file does not record rate-limit retries or dropped "
    "judges for each question. When a judge is dropped the remaining shares are renormalised, so a failure can change "
    "a score without leaving a trace. From the score arithmetic we can see that at least 12 answers (6.0%) had a judge "
    "fail, and the true number is larger.",
    "<b>Scope of the benchmarks.</b> The three benchmarks have short factual questions with reference answers. The "
    "results say nothing about long answers, other languages, or domain questions in medicine or law, where the "
    "motivation for the work is strongest.",
    "<b>Supporting studies are not on our task.</b> Several cited studies were run on summarisation, reasoning, chat "
    "preferences or dialogue (Panickssery et al., 2024; Huang et al., 2024; Zheng et al., 2023; Shuster et al., 2021). "
    "They motivate the design and do not prove that each effect occurs for short factual verdicts.",
]))

# ------------------------------------------------------------------ 7 Conclusion
A(("h1", "7. Conclusion and Future Work"))
A(("h2", "7.1 Summary of Contributions"))
A(("pf",
   "This paper described LLM Trust Score, a black-box layer that scores a language-model answer by combining agreement "
   "between three sampled answers, the verdicts of three judges from three developers grounded by web search, and a "
   "check of the winning answer by a further model. On 200 fresh questions the score separated correct from incorrect "
   "answers moderately well (AUROC 0.674, interval 0.604–0.740), and its High, Medium and Low labels were ordered "
   "(71.1%, 55.0% and 26.3% correct). It was weakest on TruthfulQA, it was not calibrated, and a quarter of the answers "
   "with the maximum score were wrong. We explained why each component was chosen, including why a Gemini agreement "
   "checker was preferred to an NLI model on the evidence of Manakul et al. (2023), and we stated which components were "
   "not evaluated on their own."))
A(("h2", "7.2 Recommendations for Future Work"))
A(("pf", "The following experiments would turn the open design questions into measured results, in priority order."))
A(("bul", [
    "<b>Check the grader against people.</b> Label about 100 answers by hand and report agreement and Cohen’s (1960) "
    "kappa for the grader, with a second grader from another developer for comparison.",
    "<b>Run ablations on the same questions.</b> Switch off, one at a time, the agreement check, web search and the "
    "tie-breaker, and use a single judge, and store per-judge votes and the consistency fraction so that the components can "
    "be analysed.",
    "<b>Compare checkers.</b> Label 30 answer sets by hand and compare the Gemini checker with the DeBERTa NLI "
    "checker of Kuhn et al. (2023) on accuracy, repeatability and cost.",
    "<b>Repeat with more questions and seeds.</b> Use several seeds and a larger sample so that the benchmark "
    "differences can be tested, and run the full TruthfulQA and HaluEval question-answering sets.",
    "<b>Vary the number of samples.</b> Test five and ten samples against three, following Manakul et al. (2023).",
    "<b>Fit the cutoffs and the weights on one half and test on the other,</b> or use cross-validation, and test a "
    "calibration map of the score to a probability on held-out data.",
    "<b>Test on harder, domain-specific questions</b> where the cost of a wrong answer is high.",
]))

# ------------------------------------------------------------------ Declarations
A(("h1", "Declarations"))
A(("pf",
   "<b>Data and code availability.</b> The code, the evaluation scripts and the results file for the seed-7 run "
   "(<font face='Courier'>evaluation/results_seed7_final.csv</font>) are in the project repository, "
   "github.com/kkhushbuj/Hallucination-Detection-Reliable-Layer. The benchmark data are the public TruthfulQA, HaluEval and "
   "TriviaQA datasets. The model identifiers are those recorded in <font face='Courier'>config.py</font> at the time of the run "
   "(29 October 2026). A public web page serves the same pipeline at https://trust.145-241-213-220.sslip.io."))
A(("p",
   "<b>Ethics.</b> The study used public benchmark data and model outputs and involved no human participants and no "
   "personal data."))
A(("p",
   "<b>Use of AI tools.</b> Language models are the object of this study and are used inside the pipeline as described. "
   "An AI assistant also helped to draft the text of this paper and to compute the statistics from the saved results file. "
   "The author is responsible for the content."))
A(("p",
   "<b>Funding and competing interests.</b> No external funding was received. The author declares no competing interests."))
