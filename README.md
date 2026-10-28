# LLM Reliability Layer

Scores how much you can trust an LLM's answer instead of accepting it at face value. Ask any question and get back the answer, a 0–100% **Trust Score**, a plain-English confidence label, and a written explanation of why.

The score combines two independent signals: whether *other* models agree the answer is correct (cross-model judgment, grounded with a web search), and whether the answer stays the same when the question is asked again (self-consistency).

## How it works

1. **Generate** — `gpt-4o-mini` answers the question 3 times at temperature 0.9 (the self-consistency technique).
2. **Check agreement** — Gemma 4 compares the 3 answers in pairs and decides whether they reach the same conclusion. Each answer gets a consistency value: the share of the *other* answers that agree with it.
3. **Ground with a web search** — for each answer, Tavily searches the question plus that answer, and the top results are added to every judge's prompt.
4. **Judge** — each answer is judged `CORRECT` or `HALLUCINATED` by three models from three labs: Qwen3.8-27B (Groq), Mistral Medium 3.5 and Llama 3.3 70B (both via OpenRouter).
5. **Score** — every judge that responds and the consistency value each get an equal share of the score. A failed judge is dropped and the shares rebalance. The best-scoring answer wins.
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
| Agreement checker | Google Gemma 4 31B |
| Tie-breaker | NVIDIA Nemotron 3.5 Lightning 30B |
| Web search | Tavily |
| Evaluation grader | Anthropic Claude Haiku 5.5 |

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env        # then fill in the keys
uvicorn server:app --reload --port 8000
```

Open http://localhost:8000. The API is `POST /api/verify` with `{"question": "..."}`.

Run the tests (no API keys needed):

```bash
pip install -r requirements-dev.txt
pytest
```

## Evaluation

`evaluation/evaluate.py` runs a fixed 200-question set drawn with seed 42 from three public benchmarks: TruthfulQA (common misconceptions), HaluEval (hallucination) and TriviaQA (factual recall). A separate grader model compares each final answer with the benchmark's reference answer. The grader is from a lab that plays no part in the scoring pipeline.

```bash
python evaluation/evaluate.py --batch 1   # batches 1-4, 50 questions each
python evaluation/evaluate.py --backfill  # retry failed rows, then merge
```

**Baseline (earlier version).** A first full run used a different setup: judges Qwen3.8-27B, Cohere command-a and gpt-oss-120b, with no web search and no tie-breaker, and Qwen as the grader. It is on the `local-backtest-code` branch.

| Metric | Result |
|---|---|
| Accuracy | 60.0% (120/200) |
| Average Trust Score, correct answers | 93.9% |
| Average Trust Score, incorrect answers | 78.0% |
| Gap | 15.9 points |

| Dataset | Accuracy |
|---|---|
| TruthfulQA | 56.1% (37/66) |
| HaluEval | 45.5% (30/66) |
| TriviaQA | 77.9% (53/68) |

The current lineup (web search, tie-breaker, new judges) has not been measured yet, so no results are claimed for it.

## Known limitations

- The score measures agreement between models, not truth. If every judge shares the same wrong belief, the score will not catch it. Web search and the tie-breaker are there to reduce this, but their effect is not yet measured.
- A model cannot be scored correct on something it does not know. HaluEval's multi-hop trivia is the clearest case.
- Results come from one 200-question sample and one run. LLM calls are probabilistic, so figures vary between runs (`evaluation/stability_check.py` measures this).
- The server has no authentication or rate limiting, and every question makes about 20 API calls. Put it behind a gate before exposing it publicly.

## Project structure

```
├── server.py                    FastAPI app: serves the site, POST /api/verify
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
