# Hallucination + Reliability Layer for LLMs

A tool that scores how much you can actually trust a plain-question answer from an LLM, instead of accepting it at face value. Given any question, it produces an answer along with a percentage trust score, a plain-English confidence label, and a written explanation of why.

## What it does

Ask it any question. Instead of just returning an answer, it tells you:
- **The answer**
- **A Trust Score** (0-100%)
- **A confidence label** (High / Medium / Low confidence)
- **Why** — which independent models agreed, and how consistent the answer was across multiple attempts

## How it works

1. **Generate** — the base model (OpenAI `gpt-4o-mini`) answers the same question 3 separate times at a fixed temperature (0.9), following the standard published "self-consistency" technique.

2. **Judge** — each of the 3 answers is independently checked by 3 different models — **Qwen3.8-27B (via Groq), Gemini, and Mistral** — each verifying whether that specific answer looks correct or hallucinated. The model that generates answers never judges its own work.

3. **Check consistency** — the 3 original answers are compared against each other using NLI (natural language inference — checking whether two answers logically agree, not just whether they're worded similarly), to measure how consistent the model was with itself.

4. **Score** — each answer gets a score built from equal-weighted parts: every judge that responds contributes an equal share, and the answer's agreement with the other attempts contributes an equal share too, all summing to 100%. Whichever of the 3 answers scores highest is shown as the final answer.

5. **Ground with a web search (optional)** — before a judge votes, a Tavily web search on the question + answer is run once per answer and injected into each judge's prompt as extra context, so judges aren't relying purely on training-data recall. If the search fails, judging falls back to the model's own knowledge silently. Toggle: `config.USE_WEB_SEARCH`.

6. **Tie-break the winner (optional)** — after the panel picks a winning answer, a single extra check runs on just that answer using GPT-OSS-20B (via Groq — same key/quota as the rest of the panel, no separate cost). If it disagrees with the panel's majority verdict, the trust score takes a fixed penalty and a caution note is shown. Toggle: `config.USE_TIE_BREAKER`.

## Why this design

- **Two independent signals** (cross-model judgment + self-consistency) have to both hold up before something is called reliable — a weak signal on either side shows up plainly in the score, not hidden behind confident-sounding text.
- **The generator never judges its own answers.** All 3 judges are fully separate models from the one producing the answer.
- **Fails gracefully.** If a judge doesn't respond, or if generating an answer fails, the pipeline continues with whatever succeeded instead of crashing — and any failures are shown in plain language, not raw error dumps.
- **Cost-aware extras stay optional.** Web search and the tie-breaker each add real value but aren't required for the core pipeline to work, so both are feature-flagged in `config.py` and can be switched off to save API calls/quota.

## Evaluation

Tested against a combined 200-question set pulled from 3 real published research benchmarks:
- **TruthfulQA** — designed to catch models repeating common human misconceptions
- **HaluEval** — designed specifically to test hallucination
- **TriviaQA** — general factual accuracy

**Results (200 questions, final architecture):**

| Metric | Result |
|---|---|
| Overall accuracy | 66.0% (132/200) |
| Avg. Trust Score on correct answers | 92.1% |
| Avg. Trust Score on incorrect answers | 69.1% |
| **Gap** | **23.0 points** |

The 23-point gap between correct and incorrect answers is the key result — it shows the Trust Score reliably separates good answers from bad ones, not just producing a number that looks confident either way.

**By source:**
| Dataset | Accuracy |
|---|---|
| TruthfulQA | 68.2% |
| HaluEval | 50.0% |
| TriviaQA | 79.4% |

HaluEval is the hardest category by design — its questions are built from multi-hop trivia requiring several chained, obscure facts, which is a limitation of the base model's raw knowledge rather than the scoring system.

*Note: these numbers were measured with Claude as the judge/consistency-checker model (the setup used at evaluation time). The app has since switched to Qwen3.8-27B via Groq in that role, and added a multi-model ground-truth checker, web search grounding, and a tie-breaker (see below); results have not yet been re-measured against the new configuration.*

**Confidence thresholds** were calibrated from this real data (not guessed):
- High confidence: Trust Score ≥ 80%
- Medium confidence: Trust Score ≥ 75%
- Low confidence: below 75%

### Ground-truth checking during evaluation

`evaluation/evaluate.py` needs its own model(s) to decide whether the system's answer actually matches a benchmark's reference answer — a separate concern from the trust-score panel above. `is_correct()` calls 3 independent models (Groq/Qwen, Gemini, Mistral) with the same correctness prompt and takes a 2-of-3 majority vote, rather than trusting a single model's call. Runs also report how often those 3 checkers split 2-1, since that disagreement rate is itself a useful signal on how clear-cut the benchmark labels are.

### Stability testing

Since every judge/checker call is itself a probabilistic LLM call, the same 200-question evaluation can vary somewhat from run to run. `evaluation/stability_check.py` runs the full evaluation multiple times (default 3, `--runs N` to change it) and reports accuracy and trust-score gap per run plus their mean ± standard deviation, saved to `evaluation/results_stability.csv` — so the headline numbers above can be reported with a sense of their run-to-run variance, not just a single sample.

## Known limitations

- Trust Score reflects how much independent models agree, not ground-truth fact-checking against an external source — if all judges share the same wrong belief, the score won't catch it.
- Base model knowledge is a hard ceiling — no scoring method can produce a correct answer the underlying model doesn't know.
- Evaluated on a 200-question sample; a larger sample would tighten confidence in the exact accuracy numbers.

## Tech stack

Python, LangGraph (pipeline orchestration), LangSmith (tracing), OpenAI / Groq / Gemini / Mistral APIs, Tavily (web search grounding), Streamlit (UI)

## Project structure

├── app.py                          # Streamlit UI
├── graph.py                        # LangGraph pipeline definition
├── config.py                       # Models, thresholds, feature flags, settings
├── core/
│   ├── verification.py             # Main scoring pipeline, tie-breaker
│   ├── nli.py                      # Consistency checking (NLI-based)
│   └── search.py                   # Tavily web search grounding for judges
├── models/
│   └── llm_providers.py            # API calls to all 4 providers
├── evaluation/
│   ├── evaluate.py                 # Runs the evaluation suite (majority-vote ground-truth checker)
│   ├── stability_check.py          # Repeats the evaluation N times, reports mean ± stdev
│   ├── calibrate_thresholds.py     # Calibrates confidence thresholds from real results
│   ├── datasets/                   # TruthfulQA, HaluEval source data
│   └── results_v3_final.csv        # Latest evaluation results (results_final.csv once a fresh full run completes)
└── requirements.txt

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Add your API keys to `.env`:
   - `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY` — required
   - `TAVILY_API_KEY` — required only if `config.USE_WEB_SEARCH` is `True` (get a free key at [tavily.com](https://tavily.com), 1,000 searches/month free)
3. Run the app: `streamlit run app.py`

Feature flags in `config.py` (`USE_WEB_SEARCH`, `USE_TIE_BREAKER`) can be set to `False` to skip the web-search and tie-breaker steps and save on API calls/quota.