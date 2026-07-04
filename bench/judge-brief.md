# Judge brief — turn raw model reviews into a ground-truth verdict

`collect.sh` gives you, per commit, one review file per model. Those are *claims*.
To benchmark the models you have to decide which claims are **real bugs** — by
reading the actual code, not by trusting the model. Do this yourself, or hand this
brief to a strong "judge" model (ideally a *different* one than the panel) per commit.

## For each commit
1. `git show <SHA>` — read the diff. Understand what changed.
2. Read every model's review file for that commit (`<SHA>__<model>.txt`).
3. Extract every DISTINCT claimed bug across all the files. If two models report the
   SAME underlying issue, MERGE them into one finding and record both in `found_by`.
4. VERIFY each finding against the real code:
   - Open the cited file/line. Trace the actual control/data flow.
   - **REAL** only if you can state a concrete input/state that yields a wrong
     output/crash/security hole given the code as merged. If the model misread the
     code, the guard it worried about already exists, or the behavior is actually
     correct → **FALSE_POSITIVE**.
   - Pure style/naming with no wrong behavior → **STYLE**.
   - Genuinely can't tell without running it → **UNCERTAIN** (use sparingly).
5. Be skeptical: a vague "this might have edge cases" with no concrete failing case
   is FALSE_POSITIVE. You are measuring precision — false positives are the cost.

## Output — one JSON file per commit at `verdicts/<SHA>.json`
```json
{
  "sha": "<SHA>",
  "findings": [
    {
      "summary": "one-line description of the claimed bug",
      "location": "path/to/file:123",
      "found_by": ["glm", "minimax"],
      "verdict": "REAL",
      "severity": "P1",
      "evidence": "given X the code does Y which is wrong because Z (or: why it's a FP)"
    }
  ]
}
```
- `found_by`: the short names you passed to `aggregate.py` (e.g. `glm`, `minimax`, `deepseek`).
- `verdict`: `REAL` | `FALSE_POSITIVE` | `STYLE` | `UNCERTAIN`.
- `severity`: `P1` (blocking) | `P2` (likely bug) | `P3` (minor) — your call, even for FPs.
- A model that returned an empty/"no issues" review just contributes no findings — don't invent any.

Then: `python3 bench/aggregate.py verdicts/` → per-model precision, recall, and
**unique-real** (bugs only that model caught — its true marginal value).
