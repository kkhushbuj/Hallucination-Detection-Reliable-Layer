# -*- coding: utf-8 -*-
# Content blocks, part 1: title, abstract, introduction, related work.
# Block types: ("h1"|"h2"|"h3", text), ("p", text), ("pf", text) paragraph without indent,
# ("bul", [items]), ("table", ...), ("fig", ...)

TITLE = ["LLM Trust Score: Scoring the Reliability of", "Language-Model Answers with Cross-Model", "Judges and Self-Consistency"]
AUTHOR = "Khushbu Kapade"
AFFIL = "WMG, University of Warwick, United Kingdom"
RUNNING = "LLM Trust Score"

ABSTRACT = (
    "Large language models (LLMs) often give fluent answers that are wrong, and users have no cheap way to tell which "
    "answers to trust. This paper presents LLM Trust Score, a black-box layer that scores one answer from 0 to 100 without "
    "access to token probabilities. A writer model (gpt-4o-mini) answers each question three times at temperature 0.9. "
    "A Gemini model checks whether the three answers reach the same conclusion. Three judges from three other developers "
    "(Qwen, Mistral and Llama) rate each answer as correct or hallucinated with the help of web-search snippets, and the "
    "best-scoring answer receives a score and a High, Medium or Low label. A separate tie-breaker model (NVIDIA Nemotron) checks only the "
    "winning answer and removes 10 points when it disagrees with the judge majority. We evaluate on 200 fresh questions "
    "(66 TruthfulQA, 66 HaluEval and 68 TriviaQA) graded by Claude Haiku 5.5, a model that plays no part in the scoring. "
    "The writer was correct on 61.0% of questions. The trust score separated correct from incorrect answers with an AUROC "
    "of 0.674 (95% bootstrap interval 0.604–0.740) and a mean gap of 18.1 points (11.1–25.5). The labels were ordered as "
    "intended: 71.1% of High, 55.0% of Medium and 26.3% of Low answers were correct. The score is not a calibrated "
    "probability. Of the answers that scored 100, 28.0% were wrong, and the Brier score (0.272) was worse than always "
    "predicting the base rate (0.238). Discrimination was weakest on TruthfulQA (AUROC 0.568, interval 0.450–0.682). A "
    "simple proxy that uses only the judges’ hallucination flags ranked answers at least as well as the full score "
    "(AUROC 0.721). Reading the tie-breaker’s penalty back from the scores, it disagreed with the judges on 17 answers "
    "(8.5%), of which 35.3% were correct against 63.4% for the rest, and it added only 0.013 to the AUROC (interval "
    "−0.003 to +0.033). We give the reasons for every design choice, including why a Gemini agreement checker was preferred to "
    "a natural-language-inference (NLI) model, and we state which components were not evaluated on their own."
)
KEYWORDS = ("large language models; hallucination detection; LLM-as-a-judge; self-consistency; confidence estimation; "
            "retrieval grounding; TruthfulQA")

B1 = []
A = B1.append

# ------------------------------------------------------------------ 1 Introduction
A(("h1", "1. Introduction"))
A(("h2", "1.1 Background and Motivation"))
A(("pf",
   "Large language models (LLMs) now answer questions on medicine, law, science and everyday facts, and they do so in a "
   "confident, fluent style whether or not the answer is correct. The research literature calls an answer that is "
   "fluent but unsupported or false a hallucination, and surveys describe it as one of the main obstacles to using "
   "these models where mistakes matter (Ji et al., 2023; Huang et al., 2025). The problem has a theoretical side as well. "
   "Kalai and Vempala (2024) show that a language model that is well calibrated as a predictor of text must still "
   "hallucinate at roughly the rate at which the facts it was trained on appear only once, even when the training data "
   "contain no errors. They also stress that hallucination is not inevitable for facts that are seen repeatedly, and that "
   "post-training may reduce it. In practice, hallucination remains a property of deployed systems, not a solved problem."))
A(("p",
   "Farquhar et al. (2024) describe one important kind of hallucination, which they call confabulation: an answer that is "
   "arbitrary and incorrect, and that changes from one sampling of the model to the next. They note that confident false "
   "outputs block adoption in areas such as law and medicine, and they show that the amount of variation across sampled "
   "answers, measured over meaning and not over wording, can flag such errors. The authors are explicit that this "
   "addresses only one error type. A model can also be consistently wrong, because its training data contain a false "
   "belief, and sampling alone cannot expose that."))
A(("p",
   "A user who receives a single answer from a chat system has no way of knowing which of these situations applies. "
   "What the user needs is a per-answer reliability signal that is cheap to compute, that works with models offered only "
   "through an API, and that can be explained in plain language. Many hosted models do not expose token probabilities, "
   "so a useful signal has to be computed from outputs alone. Xiong et al. (2024) evaluated such black-box confidence "
   "methods on five dataset types and found that they reach failure-prediction performance close to white-box methods "
   "(AUROC 0.522 against 0.605 in their comparison), although none of the methods was consistently best and all of them "
   "struggled on tasks that need professional knowledge. This paper builds on that finding."))
A(("h2", "1.2 Problem Statement"))
A(("pf",
   "Given a factual question, the aim is to return one answer and a trust score between 0 and 100 that is higher when "
   "the answer is more likely to be correct. The setting has four constraints. First, the layer must be black-box: it may "
   "call models but may not read their internal state. Second, it must not need a labelled answer at the time of use. "
   "Third, its cost and delay must be small enough for an interactive web page. Fourth, its output must be explainable, "
   "so that a user can see how many models confirmed the answer and whether the answers agreed with each other."))
A(("p",
   "Existing approaches each use one source of evidence. Self-consistency methods compare several samples from one model "
   "(Wang et al., 2023; Manakul et al., 2023; Kuhn et al., 2023). LLM-as-a-judge methods ask a second model for a verdict "
   "(Zheng et al., 2023). Each source has a known weakness. Samples from one model share that model’s beliefs, and a single "
   "judge has its own biases, among them a preference for its own writing (Panickssery et al., 2024). Combining sources "
   "that fail in different ways is the motivation for the layer studied here."))
A(("h2", "1.3 Aim and Objectives"))
A(("pf",
   "The aim is to design, implement and critically evaluate a black-box trust layer that combines agreement between "
   "sampled answers with the verdicts of independent judges, and to state honestly what the resulting score can and "
   "cannot be used for. The objectives are:"))
A(("bul", [
    "to specify a pipeline in which the model that writes the answers, the model that checks agreement, the judges, "
    "the tie-breaker and the grader are all different models, so that no model checks its own work;",
    "to give, for every design decision, the published evidence that motivates it and to say plainly where no direct "
    "evidence exists;",
    "to evaluate the layer on 200 questions that were not used while developing it, with confidence intervals;",
    "to test whether the score ranks correct answers above incorrect ones, whether the High, Medium and Low labels are "
    "ordered, and whether the score behaves like a probability; and",
    "to document the limitations of the design and of the evaluation, including the components that were not evaluated "
    "separately.",
]))
A(("h2", "1.4 Research Questions"))
A(("bul", [
    "RQ1: Does the trust score separate correct answers from incorrect answers, and by how much?",
    "RQ2: Does the separation hold across benchmarks with different kinds of error (TriviaQA, HaluEval and TruthfulQA)?",
    "RQ3: Are the confidence labels useful, and can the score be read as a probability of being correct?",
    "RQ4: Which part of the pipeline carries the signal, and what can be said about the parts that were not isolated?",
]))
A(("h2", "1.5 Contributions"))
A(("pf", "The paper makes four contributions."))
A(("bul", [
    "A fully specified black-box pipeline in which the writer, agreement checker, judges, tie-breaker and "
    "grader all come from different developers, together with the evidence for and against each choice (Section 3 and Table 3.1).",
    "A reasoned comparison of an LLM agreement checker with an NLI checker, supported by the results of Manakul et al. "
    "(2023), and an explicit statement that the two were not compared on our own data.",
    "An evaluation on 200 fresh questions with bootstrap intervals, in which the main finding is moderate discrimination "
    "(AUROC 0.674) but poor calibration, with no claim beyond that.",
    "An open implementation and a public web page that serve the same pipeline (Section 3.10).",
]))
A(("h2", "1.6 Structure of the Paper"))
A(("pf",
   "Section 2 reviews related work. Section 3 describes the method and the evaluation protocol. Section 4 reports the "
   "results. Section 5 discusses them, Section 6 states the limitations, and Section 7 concludes with future work."))

# ------------------------------------------------------------------ 2 Related work
A(("h1", "2. Related Work"))
A(("h2", "2.1 Hallucination in Language Models"))
A(("pf",
   "Ji et al. (2023) survey hallucination in natural language generation, define it as generated content that is "
   "nonsensical or unfaithful to the source, and organise the field by task and by cause. Huang et al. (2025) give a "
   "taxonomy specific to LLMs and review detection and mitigation methods. Benchmarks measure the problem in different "
   "ways. TruthfulQA (Lin et al., 2022) contains 817 questions in 38 categories that were written so that some humans "
   "would answer falsely because of a misconception. The best model in the original study was truthful on 58% of "
   "questions against 94% for humans, and the largest models were generally the least truthful, which the authors "
   "explain by models learning false statements that are common in their training text. HaluEval (Li et al., 2023) "
   "provides 35,000 samples that were built with a sampling-then-filtering procedure using ChatGPT and human labellers, "
   "and it reports that LLMs find it hard to recognise hallucinations unless they are given external knowledge or "
   "reasoning steps. TriviaQA (Joshi et al., 2017) is a large question-answering dataset of trivia questions."))
A(("h2", "2.2 Detection from Sampled Answers"))
A(("pf",
   "Wang et al. (2023) introduced self-consistency for reasoning: instead of one greedy answer, sample several reasoning "
   "paths and keep the most frequent final answer. The method improved accuracy on GSM8K (+17.9 points), AQuA (+12.2), "
   "StrategyQA (+6.4) and ARC-challenge (+3.9) across four language models, with no extra training. Its use here is the "
   "sampling idea, not the claim that agreement implies truth, which the paper does not make."))
A(("p",
   "SelfCheckGPT (Manakul et al., 2023) turns the sampling idea into a detector for hallucination. The premise is that "
   "facts a model knows tend to recur across samples while invented facts diverge. It needs no external database and no "
   "access to model internals, and it was evaluated on passages about people generated by GPT-3 and annotated for "
   "factuality. The authors compare five ways of scoring consistency (BERTScore, question answering, n-gram, an NLI "
   "model and a prompt to an LLM) and we return to that comparison in Section 3.3."))
A(("p",
   "Kuhn et al. (2023) argue that uncertainty over generated language should be measured over meanings and not over "
   "strings, because different sentences can mean the same thing. They group sampled answers into meaning classes using "
   "bidirectional entailment, computed with a DeBERTa-large model fine-tuned on MNLI, and compute the entropy over the "
   "classes. This semantic entropy predicted accuracy better than the baselines on question-answering data. "
   "Farquhar et al. (2024) extended the idea in <i>Nature</i> and showed that entropy over meanings flags confabulations "
   "across datasets and tasks without task-specific data. Both papers motivate the agreement check in Section 3.3, and "
   "Kuhn et al. also record its limitations: equivalence is soft and need not be transitive, so clusters can depend on "
   "the order in which pairs are compared."))
A(("h2", "2.3 Elicited Confidence and Calibration"))
A(("pf",
   "A second line of work asks the model for its confidence. Tian et al. (2023) studied models tuned with human feedback "
   "on TriviaQA, SciQ and TruthfulQA and found that confidences the model states in words are typically better "
   "calibrated than its token probabilities, often reducing expected calibration error by a relative 50%. Xiong et al. "
   "(2024) found that verbalised confidence is often too high, and that sampling several answers and aggregating their "
   "consistency reduces the overconfidence. These results explain why the layer relies on judgments and agreement and "
   "not on a stated confidence from the writer."))
A(("p",
   "Calibration itself has a standard vocabulary. Guo et al. (2017) showed that modern neural networks are often "
   "miscalibrated and popularised the expected calibration error. The Brier (1950) score measures the squared error of "
   "probability forecasts, and Fawcett (2006) describes ROC analysis and the area under the curve (AUROC), which "
   "measures how well a score ranks positive cases above negative ones without fixing a threshold. We use these tools in "
   "Section 3.9."))
A(("h2", "2.4 LLM Judges and Their Biases"))
A(("pf",
   "Zheng et al. (2023) showed that a strong LLM judge reaches more than 80% agreement with human preferences on chat "
   "responses, the same level as humans reach with each other. They also documented position bias, verbosity bias and "
   "self-enhancement bias (a preference for text the judge wrote), and noted that some of these biases are small or can "
   "be reduced. Wang et al. (2024) showed that the ranking of two candidate answers can be changed by swapping their order "
   "and proposed calibration methods. Because each judge in our pipeline sees one answer at a time, order effects between "
   "candidates do not arise, but the other biases remain possible."))
A(("p",
   "Panickssery et al. (2024) found that GPT-3.5, GPT-4 and Llama 2 favour their own summaries, that GPT-4 recognises its "
   "own text 73.5% of the time, and that stronger self-recognition goes with stronger self-preference. Huang et al. "
   "(2024) showed that, without external feedback, LLMs struggle to correct their own reasoning and sometimes become "
   "worse. Both findings concern other tasks, summarisation and reasoning, so they motivate keeping the writer, the "
   "judges and the grader apart without proving that the same effect occurs for factual verdicts. Kamalloo et al. "
   "(2023) examined how to grade open-domain question answering in the era of LLMs. Matching against a list of gold "
   "answers underestimates generative models, with one model gaining nearly 60% under human judgment, and automated "
   "evaluators help but cannot fully replace human evaluation. This is the basis for using an LLM as the grader in "
   "Section 3.9 and the reason that its agreement with people is listed as a limitation."))
A(("h2", "2.5 Correlated Errors and Multi-Model Checking"))
A(("pf",
   "Using several models is only useful if their errors differ. Kim et al. (2025) studied more than 350 LLMs and found "
   "that, on one leaderboard, two models that are both wrong give the same wrong answer 60% of the time. Shared "
   "architecture and shared provider raise the correlation, and larger, more accurate models are more correlated even "
   "across providers. The paper also shows the effect on LLM-as-a-judge evaluation. The finding supports choosing judges "
   "from different developers, and it also warns that doing so does not remove shared mistakes."))
A(("p",
   "Du et al. (2024) had several instances of a model propose answers and debate them over several rounds, and reported "
   "better mathematical and strategic reasoning and fewer factual errors and hallucinations. Their instances mostly "
   "came from one model family, so the result motivates cross-checking by several models but is not evidence for "
   "cross-lab panels in particular."))
A(("h2", "2.6 Retrieval Grounding"))
A(("pf",
   "Retrieval gives a model access to knowledge it does not hold in its parameters. Lewis et al. (2020) combined "
   "parametric and non-parametric memory for knowledge-intensive tasks. Shuster et al. (2021) reported that "
   "retrieval-augmented dialogue models reduced hallucinated responses by more than 60%, using Wikipedia as the source. "
   "Li et al. (2023) found that supplying external knowledge helps LLMs recognise hallucinations. These studies concern "
   "generation and dialogue more than verification of short factual answers, so they motivate web grounding of the "
   "judges in Section 3.4 without measuring its effect here."))
A(("h2", "2.7 Research Gap and Positioning"))
A(("pf",
   "Table 2.1 places the layer among the families above. Sampling methods use one model and measure agreement, judge "
   "methods use one model and measure a verdict, and confidence methods rely on what a model says about itself. The "
   "layer studied here combines agreement from the writer with verdicts from three other developers, adds web grounding "
   "and a fifth independent check, and reports a bounded score with labels. What is missing from the literature, and "
   "what this paper tries to supply, is a transparent evaluation of such a combination on fresh questions, with intervals "
   "and with a clear statement of which parts were not tested."))
A(("table", "Table 2.1 — How the trust layer relates to published approaches.",
   ["Approach", "Evidence used", "What it does not cover"],
   [["Self-consistency (Wang et al., 2023)", "Agreement among samples from one model", "Truth of the agreed answer"],
    ["SelfCheckGPT (Manakul et al., 2023)", "Consistency of sampled passages", "Consistently wrong answers"],
    ["Semantic entropy (Kuhn et al., 2023; Farquhar et al., 2024)", "Entropy over meaning classes of samples", "False beliefs shared by all samples"],
    ["Verbalised confidence (Tian et al., 2023; Xiong et al., 2024)", "The model’s stated confidence", "Overconfidence of the stated value"],
    ["LLM judge (Zheng et al., 2023)", "One model’s verdict", "That model’s own biases"],
    ["This layer", "Agreement, three cross-lab judges, web snippets, one extra check", "Shared errors across developers (Kim et al., 2025)"]],
   [150, 150, 154]))
