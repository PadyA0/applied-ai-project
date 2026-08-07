# Execution Evidence

Every file in this folder is generated, not pasted. Regenerate all of it with:

```bash
python capture_evidence.py
```

Each log carries a header stating the exact command, the working directory and
the exit code, so any claim in the README can be traced back to a command you
can run yourself.

| File | Command | Shows |
| --- | --- | --- |
| [01_recommender_run.txt](01_recommender_run.txt) | `python -m src.main` | Ranked results for four profiles, with reasons and retrieved fun facts |
| [02_reliability_run.txt](02_reliability_run.txt) | `python -m src.reliability` | Six reliability checks over the whole system |
| [03_test_suite.txt](03_test_suite.txt) | `python -m pytest -q` | The full unit test suite |
| [04_missing_corpus.txt](04_missing_corpus.txt) | `python -m src.main` without the notes corpus | Optional data missing: warns, degrades, exits 0 |
| [05_missing_catalog.txt](05_missing_catalog.txt) | `python -m src.main` without the catalog | Required data missing: errors, exits 1 |

## What each one is worth looking at for

**01** is the system working normally. The last profile is the interesting one,
because ambient has no note in the corpus and the retriever says so rather than
inventing something.

**02** is where the honest numbers live. Catalog coverage is 82 percent and
total churn reaches 67 percent, and neither of those is hidden.

**03** should be all passing. If it is not, the README is out of date.

**04 and 05** are a matched pair. The same missing file problem produces two
deliberately different outcomes depending on whether the data is optional.

## Reproducibility notes

The recommender and the reliability harness are fully deterministic, so 01, 02,
04 and 05 are byte for byte identical between runs on the same commit. In 03,
the elapsed time on the final pytest line varies; nothing else does.

The two failure demonstrations run inside temporary directories. No real data
file is renamed or deleted at any point.
