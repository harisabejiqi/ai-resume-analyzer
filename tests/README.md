# Tests

```bash
python -m pytest
```

The suite never loads the sentence-transformer model. `conftest.py` blocks model
loading, and tests that need semantic matching use a deterministic hashed
bag-of-words encoder instead. The suite therefore runs offline in a few seconds,
but the match scores it checks are NOT the real SBERT scores.

## Checking that the research results are unaffected

The thesis numbers come from the evaluation harness, which calls the production
scoring code. After any change to `app/services/`, regenerate the comparison into
a scratch folder and compare it with the committed one:

```bash
python -m eval.run_eval --out <temp folder> --no-plots
```

Then compare `<temp folder>/comparison.md` with `eval/results/comparison.md`
(e.g. `diff` or `fc`). The two files must be identical. All randomness in the
harness is seeded, so any difference means a scoring change, not noise. This
needs the SBERT model (`all-MiniLM-L6-v2`), which is downloaded on first use and
cached afterwards.
