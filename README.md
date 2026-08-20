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

2. **Judge** — each of the 3 answers is independently checked by 3 different models — **GPT-OSS-120B (via Groq), Gemini, and Mistral** — each verifying whether that specific answer looks correct or hallucinated. The model that generates answers never judges its own work.

3. **Check consistency** — the 3 original answers are compared against each other using NLI (natural language inference — checking whether two answers logically agree, not just whether they're worded similarly), to measure how consistent the model was with itself.

4. **Score** — each answer gets a score built from equal-weighted parts: every judge that responds contributes an equal share, and the answer's agreement with the other attempts contributes an equal share too, all summing to 100%. Whichever of the 3 answers scores highest is shown as the final answer.

## Why this design

- **Two independent signals** (cross-model judgment + self-consistency) have to both hold up before something is called reliable — a weak signal on either side shows up plainly in the score, not hidden behind confident-sounding text.
- **The generator never judges its own answers.** All 3 judges are fully separate models from the one producing the answer.
- **Fails gracefully.** If a judge doesn't respond, or if generating an answer fails, the pipeline continues with whatever succeeded instead of crashing — and any failures are shown in plain language, not raw error dumps.

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

*Note: these numbers were measured with Claude as the judge/consistency-checker model (the setup used at evaluation time). The app has since switched to GPT-OSS-120B via Groq in that role; results have not yet been re-measured against the new configuration.*

**Confidence thresholds** were calibrated from this real data (not guessed):
- High confidence: Trust Score ≥ 80%
- Medium confidence: Trust Score ≥ 75%
- Low confidence: below 75%

## Known limitations

- Trust Score reflects how much independent models agree, not ground-truth fact-checking against an external source — if all judges share the same wrong belief, the score won't catch it.
- Base model knowledge is a hard ceiling — no scoring method can produce a correct answer the underlying model doesn't know.
- Evaluated on a 200-question sample; a larger sample would tighten confidence in the exact accuracy numbers.

## Tech stack

Python, LangGraph (pipeline orchestration), LangSmith (tracing), OpenAI / Groq / Gemini / Mistral APIs, Streamlit (UI)

## Project structure

├── app.py                          # Streamlit UI
├── graph.py                        # LangGraph pipeline definition
├── config.py                       # Models, thresholds, settings
├── core/
│   ├── verification.py             # Main scoring pipeline
│   └── nli.py                      # Consistency checking (NLI-based)
├── models/
│   └── llm_providers.py            # API calls to all 4 providers
├── evaluation/
│   ├── evaluate.py                 # Runs the evaluation suite
│   ├── calibrate_thresholds.py     # Calibrates confidence thresholds from real results
│   ├── datasets/                   # TruthfulQA, HaluEval source data
│   └── results_v4_claude_checker.csv  # Final evaluation results
└── requirements.txt

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Add your API keys to `.env`:
3. Run the app: `streamlit run app.py`