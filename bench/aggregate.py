#!/usr/bin/env python3
"""aggregate.py — turn per-commit verdicts into a per-model scorecard.

Usage:  python3 bench/aggregate.py [verdicts_dir]   (default ./ai-review-jury-bench/verdicts)

Reads every <sha>.json written per the judge brief and reports, for each model:
  raised        findings it made (excluding pure STYLE)
  REAL          real bugs it raised
  unique-REAL   real bugs ONLY it raised   <- the real reason to add a model
  FP            false positives it raised  <- the triage tax it charges you
  precision     REAL / raised
  recall        REAL / (all real bugs the panel found)

Model names are discovered from the `found_by` fields — no hard-coding.
"""
import json, glob, os, sys
from collections import defaultdict

VDIR = sys.argv[1] if len(sys.argv) > 1 else "./ai-review-jury-bench/verdicts"
files = sorted(glob.glob(os.path.join(VDIR, "*.json")))
if not files:
    sys.exit(f"no verdict JSON found in {VDIR} (see bench/judge-brief.md)")

stat = defaultdict(lambda: defaultdict(int))   # model -> counters
models = set()
panel_real = 0
real_bugs = []                                 # (summary, found_by, severity)

for path in files:
    try:
        data = json.load(open(path))
    except Exception as e:
        print(f"! skipping {path}: {e}", file=sys.stderr); continue
    for f in data.get("findings", []):
        v = f.get("verdict", "").upper()
        fb = [m for m in f.get("found_by", []) if m]
        sev = f.get("severity", "P3").upper()
        models.update(fb)
        if v == "REAL":
            panel_real += 1
            real_bugs.append((f.get("summary", ""), fb, sev))
        for m in fb:
            if v == "STYLE":
                continue
            stat[m]["raised"] += 1
            if v == "REAL":
                stat[m]["real"] += 1
                if len(fb) == 1:
                    stat[m]["unique"] += 1
            elif v == "FALSE_POSITIVE":
                stat[m]["fp"] += 1
            elif v == "UNCERTAIN":
                stat[m]["uncertain"] += 1

models = sorted(models, key=lambda m: (-stat[m]["real"], -stat[m]["unique"]))
print(f"=== AI Review Jury benchmark — {len(files)} commits, {panel_real} distinct REAL bugs found by the panel ===\n")
hdr = f"{'model':<28} {'raised':>6} {'REAL':>5} {'uniqREAL':>8} {'FP':>4} {'prec':>5} {'recall':>6}"
print(hdr); print("-" * len(hdr))
for m in models:
    s = stat[m]
    prec = f"{s['real']/s['raised']*100:.0f}%" if s["raised"] else "—"
    rec = f"{s['real']/panel_real*100:.0f}%" if panel_real else "—"
    print(f"{m:<28} {s['raised']:>6} {s['real']:>5} {s['unique']:>8} {s['fp']:>4} {prec:>5} {rec:>6}")

print("\n=== marginal value: unique-REAL vs FP (would adding this model to your panel pay off?) ===")
for m in sorted(models, key=lambda m: -stat[m]["unique"]):
    s = stat[m]
    print(f"  {m}: {s['unique']} unique real, {s['fp']} false positives")

print("\n=== the REAL bugs (severity · found_by · summary) ===")
for summ, fb, sev in sorted(real_bugs, key=lambda x: x[2]):
    print(f"  [{sev}] {'+'.join(fb) or '?'}: {summ[:100]}")
