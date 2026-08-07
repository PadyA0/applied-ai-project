# Reliability Report

**6/6 checks passed.**

| Check | Status | Summary |
| --- | --- | --- |
| Determinism | PASS | 4 profiles scored 5 times each |
| Golden snapshot | PASS | 4 baselines compared |
| Genre accuracy at rank 1 | PASS | 32/32 genres (100%) surface themselves at rank 1 |
| Catalog coverage | PASS | 82% of the catalog is reachable |
| Perturbation robustness | PASS | total churn up to 67%, material churn 0% (limit 34%) |
| Fun fact grounding | PASS | 0 ungrounded claims out of 100 songs |

## Determinism (PASS)

4 profiles scored 5 times each

* chill_indie: stable across 5 runs
* smooth_jazz: stable across 5 runs
* upbeat_pop: stable across 5 runs
* deep_ambient: stable across 5 runs

## Golden snapshot (PASS)

4 baselines compared

* chill_indie: unchanged
* smooth_jazz: unchanged
* upbeat_pop: unchanged
* deep_ambient: unchanged

## Genre accuracy at rank 1 (PASS)

32/32 genres (100%) surface themselves at rank 1

* Every genre in the catalog surfaces itself first.

## Catalog coverage (PASS)

82% of the catalog is reachable

* 82/100 songs reachable via genre profiles
* Never surfaced: Aint No Mountain High Enough, As It Was, Back in Black, Chop Suey, Dancing Queen, Everlong, Feeling Good, Firework, Fly Me to the Moon, How You Like That, Le Freak, Mr Brightside, My Favorite Things, Shape of You, Someone Like You, Stairway to Heaven, Toxic, Umbrella

## Perturbation robustness (PASS)

total churn up to 67%, material churn 0% (limit 34%)

* smooth_jazz energy +0.02: 67% of top 3 moved (tie order only)
* smooth_jazz energy -0.02: 33% of top 3 moved (tie order only)
* upbeat_pop energy +0.02: 67% of top 3 moved (tie order only)
* upbeat_pop energy -0.02: 67% of top 3 moved (tie order only)
* Worst material churn 0% against a 34% limit.

## Fun fact grounding (PASS)

0 ungrounded claims out of 100 songs

* 97 facts traced to a note
* 3 songs abstained (no relevant note, correctly refused)
