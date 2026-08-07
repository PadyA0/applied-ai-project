"""Regenerate every execution log in evidence/ from a single command.

    python capture_evidence.py

The point is that nothing in evidence/ is hand written or pasted from a
terminal I happened to have open. Every file in there is produced by this
script, so anyone can rerun it and get the same content back. That is what
makes the evidence checkable rather than just illustrative.

The two failure demonstrations run inside temporary directories rather than by
renaming the real data files. A crash halfway through this script therefore
cannot leave the repository in a broken state.
"""

import os
import shutil
import subprocess
import sys
import tempfile

EVIDENCE_DIR = "evidence"
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def run(command, cwd=None):
    """Run a command and return (exit_code, combined output)."""
    env = dict(os.environ)
    # Let a subprocess started elsewhere still import src/.
    env["PYTHONPATH"] = PROJECT_ROOT
    # Stop Python buffering stderr separately from stdout, so the warning lines
    # appear in the log in the order they were actually emitted.
    env["PYTHONUNBUFFERED"] = "1"
    result = subprocess.run(
        command,
        cwd=cwd or PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result.returncode, result.stdout


def write_log(filename, title, command, description, exit_code, output, notes=None):
    """Write one evidence file with a header explaining how to reproduce it."""
    path = os.path.join(EVIDENCE_DIR, filename)
    lines = [
        "=" * 78,
        title,
        "=" * 78,
        "",
        f"Command:   {command}",
        f"Run from:  the project root",
        f"Exit code: {exit_code}",
        "",
        description.strip(),
        "",
    ]
    if notes:
        lines += [notes.strip(), ""]
    lines += ["-" * 78, "", output.rstrip(), ""]

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"  wrote {path} (exit {exit_code})")


def capture_recommender():
    code, out = run([sys.executable, "-m", "src.main"])
    write_log(
        "01_recommender_run.txt",
        "RECOMMENDER: full run across all four demo profiles",
        "python -m src.main",
        """
Ranked recommendations for each of the four demo profiles, with the reasons
behind every score and a retrieved fun fact underneath each table.

The fourth profile (Deep Ambient) is the one to look at. No note in the corpus
covers ambient, so the retriever abstains instead of returning its best guess.
        """,
        code, out,
    )


def capture_reliability():
    code, out = run([sys.executable, "-m", "src.reliability"])
    write_log(
        "02_reliability_run.txt",
        "RELIABILITY HARNESS: six checks over the whole system",
        "python -m src.reliability",
        """
Measures the system as a whole rather than function by function. Exits 0 when
every check passes and 1 otherwise, so it can be wired into CI.

The full per check breakdown is written to tests/results/reliability_report.md.
        """,
        code, out,
    )


def capture_tests():
    code, out = run([sys.executable, "-m", "pytest", "-q"])
    write_log(
        "03_test_suite.txt",
        "TEST SUITE: full pytest run",
        "python -m pytest -q",
        """
Every unit test across nine files: loader, scorer, ranker, formatter,
retriever, the reliability harness itself, and the data files.
        """,
        code, out,
        notes="Note: the elapsed time on the final line varies between runs. "
              "Everything else in this file is deterministic.",
    )


def capture_missing_corpus():
    """Run in a temp dir that has the catalog but no notes corpus."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "data"))
        shutil.copy(
            os.path.join(PROJECT_ROOT, "data", "songs.csv"),
            os.path.join(tmp, "data", "songs.csv"),
        )
        code, out = run([sys.executable, "-m", "src.main"], cwd=tmp)

    # Only the first table is needed to show the recommender survived.
    trimmed = out.split("==============================================================================")
    short = "".join(trimmed[:3]) if len(trimmed) > 3 else out

    write_log(
        "04_missing_corpus.txt",
        "ERROR HANDLING: the notes corpus is missing",
        "python -m src.main   (run where data/music_notes.md does not exist)",
        """
The notes corpus is optional, so losing it must not take the recommender down.
The system logs a warning, continues with an empty index, and every song
abstains from giving a fun fact. Exit code is 0 because nothing actually failed.

Reproduced here by running from a temporary directory containing data/songs.csv
but no data/music_notes.md, so no real file is ever moved or deleted.
        """,
        code, short,
        notes="Output truncated after the first profile; the remaining profiles "
              "behave identically.",
    )


def capture_missing_catalog():
    """Run in a temp dir with no data/ directory at all."""
    with tempfile.TemporaryDirectory() as tmp:
        code, out = run([sys.executable, "-m", "src.main"], cwd=tmp)

    write_log(
        "05_missing_catalog.txt",
        "ERROR HANDLING: the song catalog is missing",
        "python -m src.main   (run where data/songs.csv does not exist)",
        """
The catalog is not optional. Without it there is nothing to recommend, so the
system logs an error naming the file and the likely cause, then exits 1 instead
of printing an empty table or raising a stack trace at the user.

This is the deliberate contrast with 04: one missing file degrades the output,
the other one stops the program, and the difference is a decision rather than
an accident.
        """,
        code, out,
    )


def write_index():
    path = os.path.join(EVIDENCE_DIR, "README.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("""# Execution Evidence

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
""")
    print(f"  wrote {path}")


def main() -> int:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    print(f"Capturing execution evidence into {EVIDENCE_DIR}/")
    capture_recommender()
    capture_reliability()
    capture_tests()
    capture_missing_corpus()
    capture_missing_catalog()
    write_index()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
