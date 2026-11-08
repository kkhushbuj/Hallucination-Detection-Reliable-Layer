# LLM Reliability Layer

**Live site:** https://trust.145-241-213-220.sslip.io

Scores how much you can trust an LLM's answer instead of accepting it at face value. Ask any question and get back the answer, a 0–100% **Trust Score**, a plain-English confidence label, and a written explanation of why.

The score combines two independent signals: whether *other* models agree the answer is correct (cross-model judgment, grounded with a web search), and whether the answer stays the same when the question is asked again (self-consistency).

## How it works

1. **Generate** — `gpt-4o-mini` answers the question 3 times at temperature 0.9 (the self-consistency technique).
2. **Check agreement** — Gemini 3.5 Flash-Lite compares the 3 answers in pairs and decides whether they reach the same conclusion. Each answer gets a consistency value: the share of the *other* answers that agree with it.
3. **Ground with a web search** — for each answer, Tavily searches the question plus that answer, and the top results are added to every judge's prompt.
4. **Judge** — each answer is judged `CORRECT` or `HALLUCINATED` by three models from three labs: Qwen3.8-27B (Groq), Mistral Medium 3.5 and Llama 3.3 70B (both via OpenRouter).
5. **Score** — every judge that responds and the consistency value each get an equal share of the score. A failed judge is dropped and the shares rebalance. If every judge fails, the score uses consistency only, so three answers that agree can still score 100 with no judge having confirmed them. The best-scoring answer wins.
6. **Tie-break** — NVIDIA Nemotron 3.5 Lightning checks only the winning answer. If it disagrees with the judge majority, the score drops by 10 points and a caution is shown.

| Score | Label |
|---|---|
| 80% and above | High confidence |
| 75–80% | Medium confidence |
| Below 75% | Low confidence |

The writer, the judges, the agreement checker and the tie-breaker are all different models, so no model judges its own work. Web search and the tie-breaker can be switched off in `config.py` (`USE_WEB_SEARCH`, `USE_TIE_BREAKER`).

### Models

| Role | Model |
|---|---|
| Answer writer | OpenAI `gpt-4o-mini` |
| Judges | Qwen3.8-27B · Mistral Medium 3.5 · Llama 3.3 70B |
| Agreement checker | Google Gemini 3.5 Flash-Lite |
| Tie-breaker | NVIDIA Nemotron 3.5 Lightning 30B |
| Web search | Tavily |
| Evaluation grader | Anthropic Claude Haiku 5.5 |

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in the keys
uvicorn server:app --reload --port 8000
```

Open http://localhost:8000. The API is `POST /api/verify` with `{"question": "..."}`. `GET /health` returns `{"status": "ok"}`.

Run the tests (no API keys needed):

```bash
pip install -r requirements-dev.txt
pytest
```

The tests cover only the scoring maths: verdict parsing, the score formula (including a failed judge) and the consistency calculations. They never call a model, so they say nothing about whether the real models, web search, tie-breaker or server behave correctly.

## Evaluation

`evaluation/evaluate.py` runs a fixed 200-question set drawn from three public benchmarks: TruthfulQA (common misconceptions), HaluEval (hallucination) and TriviaQA (factual recall). A separate grader model (Claude Haiku 5.5) compares each final answer with the benchmark's reference answer. The grader is from a lab that plays no part in the scoring pipeline.

```bash
python evaluation/evaluate.py --seed 7 --batch 1   # batches 1-4, 50 questions each
python evaluation/evaluate.py --seed 7 --backfill  # retry failed rows, then merge
```

The default seed (42) reproduces the earlier baseline questions. Any other seed draws a fresh 200 that share no question with the baseline set, and writes its own result files (`results_seed7_*.csv`).

**Current results** (seed 7, 200 fresh questions, current lineup with web search and tie-breaker):

| Metric | Result |
|---|---|
| Writer accuracy | 61.0% (122/200) |
| Average Trust Score, correct answers | 93.1 |
| Average Trust Score, incorrect answers | 74.9 |
| Gap | 18.1 points (95% interval 11.1–25.5) |
| AUROC (correct vs incorrect) | 0.674 (95% interval 0.604–0.740) |

| Dataset | Accuracy |
|---|---|
| TruthfulQA | 68.2% (45/66) |
| HaluEval | 43.9% (29/66) |
| TriviaQA | 70.6% (48/68) |

| Label | Share of answers that were correct |
|---|---|
| High confidence | 71.1% |
| Medium confidence | 55.0% |
| Low confidence | 26.3% |

The labels are ordered as intended, but the score is **not a calibrated probability**: 28.0% of the answers that scored 100 were wrong, and the Brier score (0.272) is worse than always predicting the base rate (0.238). Discrimination is weakest on TruthfulQA (AUROC 0.568). The full analysis is in the paper ([`paper_build/LLM_Trust_Score_final.pdf`](paper_build/LLM_Trust_Score_final.pdf), built from the sources in `paper_build/`).

**Baseline (earlier version).** A first run on the seed-42 questions used a different setup: judges Qwen3.8-27B, Cohere command-a and gpt-oss-120b, with no web search and no tie-breaker, and Qwen as the grader. It reached 60.0% accuracy and a 15.9-point gap, and is on the `local-backtest-code` branch.

## Known limitations

- The score measures agreement between models, not truth. If every judge shares the same wrong belief, the score will not catch it. The judges come from three labs, but models from different labs still make correlated errors, which fits the 28% of wrong answers at the top score.
- The score ranks answers better than chance (AUROC 0.674) but is not a calibrated probability: 28% of answers scoring 100 were still wrong. Use the label as a rough guide, not a guarantee.
- If every judge fails, the score uses consistency only, so it can read 100 without any judge confirming the answer.
- A model cannot be scored correct on something it does not know. HaluEval's multi-hop trivia is the clearest case.
- Results come from one 200-question sample and one run. LLM calls are probabilistic, so figures vary between runs (`evaluation/stability_check.py` measures this).
- The server limits each visitor to 6 requests per minute and runs at most 8 questions at once, but it has no login. Every question makes about 20 API calls, so a public deployment still spends your LLM quota.

## Project structure

```
├── server.py                    FastAPI app: site, POST /api/verify, GET /health, rate limit
├── static/index.html            Web UI
├── graph.py                     LangGraph pipeline definition
├── config.py                    Models, thresholds, feature flags
├── core/
│   ├── verification.py          Judging, scoring, tie-breaker
│   ├── nli.py                   Agreement checking between answers
│   └── search.py                Tavily web search
├── models/llm_providers.py      One call_model() for every provider
├── evaluation/
│   ├── evaluate.py              Batched evaluation, backfill and merge
│   ├── stability_check.py       Repeats the evaluation, reports mean ± stdev
│   ├── calibrate_thresholds.py  Calibrates confidence thresholds from results
│   └── datasets/                Benchmark source data
└── tests/                       Unit tests for scoring and verdict parsing
```
