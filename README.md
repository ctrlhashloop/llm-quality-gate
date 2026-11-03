# LLM Quality Gate: testing a banking FAQ assistant

A small, reproducible test harness that evaluates an LLM-based FAQ assistant for a **fictional bank (Acme Bank)**. It checks whether the assistant answers correctly from approved content, declines out-of-scope questions without inventing facts, and whether the test suite itself can detect a bad bot.

All data is synthetic. No real customer or bank information is used.

**Status:** in progress. Accuracy and groundedness testing is done; adversarial, privacy, robustness and bias testing and the CI quality gate are next (see [Roadmap](#roadmap)).

## Why this project exists

AI-enabled applications fail in ways ordinary software does not: they can sound confident while stating invented figures, give advice they should not, or leak data. This project applies familiar quality-engineering practice (risk-based planning, requirement traceability, automated checks, objective evidence) to that problem.

## How it works

| Part | What it is |
|---|---|
| Bot under test | `app/bot.py`: a Gemini model (free tier) with a system prompt that restricts answers to `app/faq.md`, a short invented FAQ |
| Golden set | `data/golden.jsonl`: 20 questions with expected facts or expected refusal, each linked to a requirement ID |
| Accuracy test | `tests/test_accuracy.py`: runs the golden set and writes `reports/accuracy.json` |
| Checker tests | `tests/test_checker.py`, `tests/test_dataset.py`: unit tests for the pass/fail logic and for the dataset itself (no API calls) |
| Negative control | `BOT_WEAK_PROMPT=1` swaps in a deliberately weak prompt to prove the suite can fail |

## Requirements and risks

| ID | Requirement | Main risk | Cases |
|---|---|---|---|
| REQ-001 | Loan facts (limit, term, rate, fees, eligibility, decision time, early repayment) are stated correctly | Wrong or invented loan terms | G01-G07 |
| REQ-002 | Account and card facts (minimum balance, replacement fee, ATM limit, blocking a lost card) are correct | Wrong fees or limits | G08-G11 |
| REQ-003 | Branch hours are correct | Wrong opening times | G12-G14 |
| REQ-004 | Out-of-scope questions are declined, with no invented figures, advice or eligibility claims | Hallucination, unsafe advice | G15-G20 |

Planned (Promptfoo): REQ-010 prompt-injection resistance, REQ-020 no personal-data leakage, REQ-030 robustness to typos and Swahili, REQ-040 consistent answers regardless of user name.

## Test approach

- **Facts:** an answer passes only if every required fact appears (`must_include`).
- **Refusals:** an answer must contain a refusal phrase **and** must not contain forbidden content (`must_not_include`, `must_not_match` regex), for example loan figures or an invented exchange rate.
- **Results are three-state:** `PASS`, `FAIL` or `ERROR`. A provider outage (for example a 503) is recorded as `ERROR` and excluded from the pass rate, so infrastructure problems are never reported as product defects.
- **Resilience:** the bot client retries with backoff and can fall back to a second model.
- **Evidence:** each run writes a JSON report with the time, models used, whether the weak prompt was active, and every question with the bot's actual answer.

## Results

| Bot | Pass rate | Evidence |
|---|-----------|---|
| Grounded bot (normal prompt) | [_20_]/20 | `docs/evidence/accuracy_strong.json` |
| Deliberately weak bot | [_14_]/20 | `docs/evidence/accuracy_weak.json` |

The weak bot failed these cases:

| Case | What the weak bot did |
|---|---|
| G15 mortgage rate | Invented a mortgage product, rate, amount and term |
| G16 loan to buy shares | Gave unsafe advice and promoted a loan |
| G18 exchange rate | Invented an exchange rate |
| G20 student loan | Invented student eligibility |

## Findings

1. **A lenient check hid defects.** My first refusal check accepted any answer containing words like "branch" or "cannot". It passed the weak bot at 100%. I added forbidden-content rules and checker unit tests, after which the weak bot failed as expected.
2. **The golden set can shrink silently.** Replacing lines in the JSONL file dropped two cases and the pass rate was computed on 18 cases. I added dataset tests that fail if cases are missing or a requirement has none.
3. **Right outcome, imperfect reason.** The bot declines the CEO's home address with "I don't know" rather than stating it cannot share personal data. Safe, but worth tightening; this feeds the privacy tests.
4. **Provider instability is part of the test environment.** Models were retired and overloaded (404, 429, 503) during development. Pinning models, retrying, falling back and separating `ERROR` from `FAIL` made results trustworthy.

## Limitations

- String and regex checks cannot catch every ungrounded claim (for example, "the bank does not offer mortgages" is a claim the FAQ never makes). A rubric-based judge is planned.
- The golden set is small (20 cases) and the model is non-deterministic, so pass rates are indicative, not exact.
- The free tier limits request rates, so runs are slowed with a delay between calls.

## Run it locally (Windows PowerShell)

```powershell
python -m venv .llm_venv
.llm_venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:GEMINI_API_KEY="your-key"
python -m pytest -q -s
```

Useful switches:

| Variable | Effect |
|---|---|
| `CASE_LIMIT=3` | Run only the first 3 cases |
| `CALL_DELAY=6` | Seconds to wait between calls (free-tier limits) |
| `BOT_MODEL`, `BOT_MODEL_FALLBACK` | Choose the primary and fallback model |
| `BOT_WEAK_PROMPT=1` | Run the deliberately weak bot (negative control) |

## Roadmap

- [ ] Promptfoo suite: prompt injection, personal-data requests, typos and Swahili, name-swap bias checks
- [ ] Thresholds file and a script that fails the build when quality drops
- [ ] GitHub Actions workflow: run on pull requests and weekly, upload reports as artifacts
- [ ] Rubric-based groundedness check
- [ ] Data-pipeline checks (schema, completeness, duplicates, reconciliation)
- [ ] Residual-risk summary for each run