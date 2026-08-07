"""Reliability harness: measure whether the recommender behaves consistently.

The pytest suite answers "does each function do what I said it does". This file
answers a different question: "does the system as a whole stay trustworthy when
I change something". Those are separate jobs, so this is a separate module.

Six checks run here:

  1. determinism        same input scored repeatedly gives the identical ranking
  2. golden snapshot    the current ranking still matches a human approved one
  3. genre accuracy     a genre profile actually surfaces that genre at rank 1
  4. catalog coverage   how much of the catalog can ever reach a top 3 slot
  5. perturbation       a tiny change in energy does not reshuffle the results
  6. grounding          every fun fact printed exists verbatim in the corpus

Run it with:

    python -m src.reliability

It writes tests/results/reliability_report.md and exits non zero if any check
fails, so it can be wired into CI later.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from .recommender import load_songs, recommend_songs
    from .rag import load_index, fun_fact_for, NoteIndex
except ImportError:
    from recommender import load_songs, recommend_songs
    from rag import load_index, fun_fact_for, NoteIndex

SONGS_PATH = "data/songs.csv"
NOTES_PATH = "data/music_notes.md"
GOLDEN_PATH = "tests/golden_recommendations.json"
REPORT_PATH = "tests/results/reliability_report.md"

# The profiles the harness measures against. Kept here rather than imported from
# main.py so that changing the demo output cannot silently move the baseline.
EVAL_PROFILES: List[Tuple[str, Dict]] = [
    ("chill_indie", {"genre": "indie pop", "mood": "melancholic", "energy": 0.2}),
    ("smooth_jazz", {"genre": "jazz", "mood": "cool", "energy": 0.4}),
    ("upbeat_pop", {"genre": "pop", "mood": "happy", "energy": 0.8}),
    ("deep_ambient", {"genre": "ambient", "mood": "chill", "energy": 0.1}),
]

# A tiny nudge to a preference. Smaller than any meaningful taste difference, so
# the ranking should barely notice it.
PERTURBATION = 0.02

# Ceiling on how much the top 3 may churn *materially* under that nudge before
# the check fails. 0.34 allows roughly one of three slots to genuinely move.
MAX_CHURN = 0.34

# Two scores closer than this are treated as a tie. Their relative order is
# arbitrary, so swapping them is not evidence the system is unstable.
TIE_MARGIN = 0.05


@dataclass
class CheckResult:
    """Outcome of one reliability check."""
    name: str
    passed: bool
    summary: str
    details: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


def top_titles(prefs: Dict, songs: List[Dict], k: int = 3) -> List[str]:
    """Titles of the top k recommendations, in rank order."""
    return [song["title"] for song, _, _ in recommend_songs(prefs, songs, k=k)]


def check_determinism(songs: List[Dict], runs: int = 5) -> CheckResult:
    """Scoring the same profile repeatedly must give byte identical rankings.

    Nothing in the scorer is random, so a failure here means state is leaking
    between calls, which would make every other measurement meaningless.
    """
    details = []
    passed = True
    for name, prefs in EVAL_PROFILES:
        rankings = {tuple(top_titles(prefs, songs)) for _ in range(runs)}
        if len(rankings) == 1:
            details.append(f"{name}: stable across {runs} runs")
        else:
            passed = False
            details.append(f"{name}: UNSTABLE, saw {len(rankings)} different rankings")
    return CheckResult(
        "Determinism", passed,
        f"{len(EVAL_PROFILES)} profiles scored {runs} times each", details,
    )


def check_golden_snapshot(songs: List[Dict], path: str = GOLDEN_PATH) -> CheckResult:
    """Compare today's rankings against a saved, human approved baseline.

    This is the check that catches accidental damage. Tuning a weight is allowed
    to change the output, but it has to be a decision: the baseline only moves
    when a human reruns this with --update-golden.
    """
    current = {name: top_titles(prefs, songs) for name, prefs in EVAL_PROFILES}

    if not os.path.exists(path):
        return CheckResult(
            "Golden snapshot", False,
            f"no baseline at {path}; run with --update-golden to create one",
            ["Baseline missing, nothing to compare against."],
        )

    with open(path, encoding="utf-8") as f:
        golden = json.load(f)

    details = []
    passed = True
    for name, expected in golden.items():
        actual = current.get(name)
        if actual == expected:
            details.append(f"{name}: unchanged")
        else:
            passed = False
            details.append(f"{name}: DRIFT expected {expected} but got {actual}")

    for name in current:
        if name not in golden:
            passed = False
            details.append(f"{name}: no baseline recorded for this profile")

    return CheckResult(
        "Golden snapshot", passed, f"{len(golden)} baselines compared", details,
    )


def write_golden(songs: List[Dict], path: str = GOLDEN_PATH) -> None:
    """Record the current rankings as the approved baseline."""
    snapshot = {name: top_titles(prefs, songs) for name, prefs in EVAL_PROFILES}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
        f.write("\n")


def check_genre_accuracy(songs: List[Dict]) -> CheckResult:
    """A profile asking for one genre should put that genre at rank 1.

    Genre carries the heaviest weight (2.0), so this is really a check that the
    weight ordering still means what the README claims it means.
    """
    genres = sorted({song["genre"] for song in songs})
    hits = 0
    misses = []
    for genre in genres:
        ranked = recommend_songs({"genre": genre}, songs, k=1)
        if ranked and ranked[0][0]["genre"] == genre:
            hits += 1
        else:
            got = ranked[0][0]["genre"] if ranked else "nothing"
            misses.append(f"{genre}: rank 1 was {got}")

    rate = hits / len(genres) if genres else 0.0
    return CheckResult(
        "Genre accuracy at rank 1", not misses,
        f"{hits}/{len(genres)} genres ({rate:.0%}) surface themselves at rank 1",
        misses or ["Every genre in the catalog surfaces itself first."],
    )


def check_catalog_coverage(songs: List[Dict]) -> CheckResult:
    """How much of the catalog can ever reach a top 3 slot.

    Run one profile per genre and collect every song that appears. Songs that
    never appear are effectively invisible: they are in the CSV but no user can
    reach them through the genre based profiles. This puts a number on the
    small catalog limitation described in the README.
    """
    genres = sorted({song["genre"] for song in songs})
    reachable = set()
    for genre in genres:
        for song, _, _ in recommend_songs({"genre": genre}, songs, k=3):
            reachable.add(song["title"])

    unreachable = sorted({song["title"] for song in songs} - reachable)
    rate = len(reachable) / len(songs) if songs else 0.0

    details = [f"{len(reachable)}/{len(songs)} songs reachable via genre profiles"]
    if unreachable:
        details.append("Never surfaced: " + ", ".join(unreachable))

    # Reported as a measurement, not a pass/fail bar: low coverage on a 40 song
    # catalog is a known property, not a regression.
    return CheckResult(
        "Catalog coverage", True, f"{rate:.0%} of the catalog is reachable", details,
    )


def check_perturbation_robustness(songs: List[Dict]) -> CheckResult:
    """Nudging target energy by a hair should not meaningfully reshuffle results.

    Churn is the fraction of the top 3 positions that changed. Raw churn alone
    is misleading though. On a catalog this dense, several songs routinely score
    within a hundredth of each other, and reordering songs that are effectively
    tied is not instability, it is arbitrary tie ordering.

    So churn is split in two. Material churn counts only the positions where the
    swap crossed a score gap wider than TIE_MARGIN, meaning the system actually
    changed its mind. That is the number that has to stay low. Total churn is
    still reported, because a high tie churn is worth knowing about even though
    it is not a failure.
    """
    details = []
    total_churns = []
    material_churns = []

    for name, prefs in EVAL_PROFILES:
        # Score the entire catalog, not just the top 3. A song that replaces
        # another was usually sitting at rank 4 with a nearly identical score,
        # and without its baseline score there is no way to tell that swap apart
        # from a genuine change of mind.
        full = recommend_songs(prefs, songs, k=len(songs))
        scores = {song["title"]: score for song, score, _ in full}
        baseline_titles = [song["title"] for song, _, _ in full[:3]]

        for direction in (PERTURBATION, -PERTURBATION):
            nudged = dict(prefs)
            nudged["energy"] = round(prefs["energy"] + direction, 4)
            shifted = top_titles(nudged, songs)

            changed = material = 0
            for before, after in zip(baseline_titles, shifted):
                if before == after:
                    continue
                changed += 1
                if abs(scores[before] - scores[after]) > TIE_MARGIN:
                    material += 1

            size = len(baseline_titles) or 1
            total_churns.append(changed / size)
            material_churns.append(material / size)
            if changed:
                kind = "material" if material else "tie order only"
                details.append(
                    f"{name} energy {direction:+.2f}: "
                    f"{changed / size:.0%} of top 3 moved ({kind})"
                )

    worst_total = max(total_churns) if total_churns else 0.0
    worst_material = max(material_churns) if material_churns else 0.0
    passed = worst_material <= MAX_CHURN
    if not details:
        details.append(f"No ranking changed under a {PERTURBATION} energy nudge.")
    details.append(
        f"Worst material churn {worst_material:.0%} against a {MAX_CHURN:.0%} limit."
    )

    return CheckResult(
        "Perturbation robustness", passed,
        f"total churn up to {worst_total:.0%}, material churn {worst_material:.0%} "
        f"(limit {MAX_CHURN:.0%})",
        details,
    )


def check_grounding(songs: List[Dict], index: NoteIndex) -> CheckResult:
    """Every fun fact must be corpus text or an honest refusal.

    This is the check that makes the retrieval layer trustworthy. It walks the
    whole catalog, generates a fact for each song, and confirms the output is
    either verbatim note text or the abstain message. Anything else would mean
    the layer produced a claim no human wrote.
    """
    bodies = [note.body for note in index.notes]
    ungrounded = []
    abstained = 0

    for song in songs:
        fact = fun_fact_for(song, index)
        if "nothing in the notes about" in fact:
            abstained += 1
            continue
        if not any(body in fact for body in bodies):
            ungrounded.append(f"{song['title']}: not traceable to any note")

    grounded = len(songs) - abstained - len(ungrounded)
    details = [
        f"{grounded} facts traced to a note",
        f"{abstained} songs abstained (no relevant note, correctly refused)",
    ]
    details.extend(ungrounded)

    return CheckResult(
        "Fun fact grounding", not ungrounded,
        f"{len(ungrounded)} ungrounded claims out of {len(songs)} songs", details,
    )


def run_all(songs: List[Dict], index: NoteIndex) -> List[CheckResult]:
    """Run every check and return the results in report order."""
    return [
        check_determinism(songs),
        check_golden_snapshot(songs),
        check_genre_accuracy(songs),
        check_catalog_coverage(songs),
        check_perturbation_robustness(songs),
        check_grounding(songs, index),
    ]


def format_report(results: List[CheckResult]) -> str:
    """Render the results as a markdown report."""
    passed = sum(1 for r in results if r.passed)
    lines = [
        "# Reliability Report",
        "",
        f"**{passed}/{len(results)} checks passed.**",
        "",
        "| Check | Status | Summary |",
        "| --- | --- | --- |",
    ]
    for r in results:
        lines.append(f"| {r.name} | {r.status} | {r.summary} |")
    lines.append("")

    for r in results:
        lines.append(f"## {r.name} ({r.status})")
        lines.append("")
        lines.append(r.summary)
        lines.append("")
        for detail in r.details:
            lines.append(f"* {detail}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    songs = load_songs(SONGS_PATH)
    index = load_index(NOTES_PATH)

    if "--update-golden" in sys.argv:
        write_golden(songs)
        print(f"Baseline written to {GOLDEN_PATH}")

    results = run_all(songs, index)

    print(f"Reliability: {len(songs)} songs, {len(index)} notes\n")
    for r in results:
        print(f"[{r.status}] {r.name}: {r.summary}")

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(format_report(results))
    print(f"\nReport written to {REPORT_PATH}")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
