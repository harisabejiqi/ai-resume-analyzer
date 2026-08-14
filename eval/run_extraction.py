"""Information-extraction evaluation: real precision / recall / F1.

Runs the *production* analyzer (app.services.analyzer.analyze_resume) over a small
hand-labeled gold set (eval/extraction/) and scores each extracted field against
the ground truth, so the numbers in the thesis describe what the app actually does.

Field scoring:
  * Atomic fields (name, email, phone, experience_years) -- one prediction per
    resume. A prediction counts as TP if a value was produced and it matches the
    gold value; FP if a value was produced but is wrong (or no gold value exists);
    FN if a gold value exists but was missed or mismatched.
      - name / email: case-insensitive exact string match.
      - phone: digit-suffix match (the gold national number must be a suffix of the
        extracted digits) so a +CC international form still counts as correct.
      - experience_years: correct within +/- 1 year (tenure is inherently fuzzy).
  * Set field (skills_technical): micro counts -- TP = |pred ∩ gold|,
    FP = |pred − gold|, FN = |gold − pred|.
  * education_present: detection accuracy (did it find an education section?).

Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2PR/(P+R). Per-field rows plus a
micro-average over all fields are written to eval/results/extraction.md.

Run from the repo root:  python -m eval.run_extraction
"""
import json
import os
import re

from app.services.analyzer import analyze_resume

HERE = os.path.dirname(__file__)
RESUME_DIR = os.path.join(HERE, "extraction", "resumes")
GOLD_PATH = os.path.join(HERE, "extraction", "gold.json")
OUT_DIR = os.path.join(HERE, "results")
OUT_MD = os.path.join(OUT_DIR, "extraction.md")


def _digits(s):
    return re.sub(r"\D", "", s or "")


def _norm(s):
    return (s or "").strip().lower()


class Counter:
    """Accumulates TP/FP/FN for one field and reports P/R/F1."""

    def __init__(self):
        self.tp = self.fp = self.fn = 0

    def add(self, tp=0, fp=0, fn=0):
        self.tp += tp
        self.fp += fp
        self.fn += fn

    def precision(self):
        d = self.tp + self.fp
        return self.tp / d if d else float("nan")

    def recall(self):
        d = self.tp + self.fn
        return self.tp / d if d else float("nan")

    def f1(self):
        p, r = self.precision(), self.recall()
        if not p or not r or p != p or r != r:
            return 0.0 if (p == 0 or r == 0) else float("nan")
        return 2 * p * r / (p + r)


def score_atomic(counter, gold_val, pred_val, equal):
    """Score one atomic field for one resume. `equal(g, p)` -> bool."""
    gold_has = gold_val is not None
    pred_has = pred_val is not None and str(pred_val).strip() != ""
    correct = gold_has and pred_has and equal(gold_val, pred_val)
    if correct:
        counter.add(tp=1)
    else:
        if pred_has:
            counter.add(fp=1)
        if gold_has:
            counter.add(fn=1)
    return correct


def main():
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold = {k: v for k, v in json.load(f).items() if not k.startswith("_")}

    fields = ["name", "email", "phone", "skills_technical", "education", "experience"]
    counters = {fld: Counter() for fld in fields}
    audit = []

    for fname, g in sorted(gold.items()):
        with open(os.path.join(RESUME_DIR, fname), encoding="utf-8") as fh:
            text = fh.read()
        a = analyze_resume(text)

        score_atomic(counters["name"], g["name"], a["name"],
                     lambda x, y: _norm(x) == _norm(y))
        score_atomic(counters["email"], g["email"], a["email"],
                     lambda x, y: _norm(x) == _norm(y))
        score_atomic(counters["phone"], g["phone"], a["phone"],
                     lambda x, y: _digits(y).endswith(_digits(x)) and _digits(x) != "")
        score_atomic(counters["experience"], g["experience_years"], a["experience_years"],
                     lambda x, y: abs(float(x) - float(y)) <= 1.0)

        gold_sk = set(g["skills_technical"])
        pred_sk = set(a["skills"]["technical"])
        counters["skills_technical"].add(
            tp=len(gold_sk & pred_sk), fp=len(pred_sk - gold_sk), fn=len(gold_sk - pred_sk)
        )

        gold_edu = bool(g["education_present"])
        pred_edu = len(a["education"]) > 0
        if gold_edu and pred_edu:
            counters["education"].add(tp=1)
        elif pred_edu and not gold_edu:
            counters["education"].add(fp=1)
        elif gold_edu and not pred_edu:
            counters["education"].add(fn=1)

        audit.append((fname, g, a, gold_sk, pred_sk))

    print("=" * 70)
    print("PER-RESUME AUDIT (gold  ->  predicted)")
    print("=" * 70)
    for fname, g, a, gold_sk, pred_sk in audit:
        print(f"\n# {fname}")
        print(f"  name : {g['name']!r:35} -> {a['name']!r}")
        print(f"  email: {g['email']!r:35} -> {a['email']!r}")
        print(f"  phone: {g['phone']!r:35} -> {a['phone']!r}")
        print(f"  exp  : {g['experience_years']!r:35} -> {a['experience_years']!r}")
        print(f"  edu  : present={g['education_present']!s:27} -> {len(a['education'])} line(s)")
        print(f"  skills miss (FN): {sorted(gold_sk - pred_sk)}")
        print(f"  skills extra(FP): {sorted(pred_sk - gold_sk)}")

    label = {
        "name": "Emër", "email": "Email", "phone": "Telefon",
        "skills_technical": "Aftësi teknike", "education": "Arsim (zbulim)",
        "experience": "Vite përvoje",
    }
    order = ["name", "email", "phone", "skills_technical", "education", "experience"]

    micro = Counter()
    for fld in order:
        c = counters[fld]
        micro.add(tp=c.tp, fp=c.fp, fn=c.fn)

    lines = []
    lines.append("# Saktësia e ekstraktimit të informacionit")
    lines.append("")
    lines.append(f"Grup testimi: **{len(gold)} CV të etiketuara me dorë** "
                 "(eval/extraction/). Metrikat janë llogaritur duke ekzekutuar "
                 "`analyze_resume` e prodhimit dhe duke krahasuar daljen me ground-truth.")
    lines.append("")
    lines.append("| Fusha | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|---|---|---|---|---|---|---|")
    for fld in order:
        c = counters[fld]
        lines.append(f"| {label[fld]} | {c.tp} | {c.fp} | {c.fn} | "
                     f"{c.precision():.2f} | {c.recall():.2f} | {c.f1():.2f} |")
    lines.append(f"| **Mikro-mesatare** | {micro.tp} | {micro.fp} | {micro.fn} | "
                 f"{micro.precision():.2f} | {micro.recall():.2f} | {micro.f1():.2f} |")
    lines.append("")
    report = "\n".join(lines)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(report + "\n")

    print("\n" + "=" * 70)
    print(report)
    print("=" * 70)
    print(f"\nWrote {OUT_MD}")


if __name__ == "__main__":
    main()
