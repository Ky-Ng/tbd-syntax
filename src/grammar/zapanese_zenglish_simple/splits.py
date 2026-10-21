"""Train / OOD partition of the 18 frames, and how each frame's fillings are divided.

Source of truth: README.md "Stimuli" (frame-level and filling-level tables), which
mirrors the research journal "Japanese -> Zenglish Training and Interventions".

Frame-level:
    train       RC on the *first* noun with a *subject* gap, or no RC. A linear
                chunk-reversal heuristic suffices.
    ood_level1  RC on the first noun with an *object* gap (two NOM nouns).
    ood_level2  RC on the *second* noun.

Filling-level (subset names are the output file names and must be unique):
    train frames  -> train / dev          (dev = in-distribution checkpoint selection)
    OOD frames    -> *_select / *_report  (select = choose analysis checkpoints,
                                           report = the accuracy that is published)

REPEAT fillings are drawn per frame without replacement and capped at the number of
distinct fillings. With the current lexicon (26 nouns, 13 + 13 verbs) only F11 is
capped (26 * 13 = 338 fillings); the next smallest, F18, has 13 * 26 * 13 = 4394.
"""

from grammar.splits import FillingSplit, FrameSplit, SplitSpec

REPEAT = 1000
SEED = 0

SPLITS = SplitSpec(
    frame_splits=(
        FrameSplit(
            "train",
            "no RC, or RC on the first noun with a subject gap (embedded noun always ACC)",
            frozenset({"F11", "F01", "F02", "F03", "F12", "F16", "F18", "F08", "F15"}),
        ),
        FrameSplit(
            "ood_level1",
            "RC on the first noun with an object gap (embedded noun NOM)",
            frozenset({"F10", "F05", "F17"}),
        ),
        FrameSplit(
            "ood_level2",
            "RC on the second noun",
            frozenset({"F04", "F13", "F06", "F07", "F09", "F14"}),
        ),
    ),
    filling_splits=(
        FillingSplit("train", {"train": 0.9, "dev": 0.1}),
        FillingSplit("ood_level1", {"ood_level1_select": 0.5, "ood_level1_report": 0.5}),
        FillingSplit("ood_level2", {"ood_level2_select": 0.5, "ood_level2_report": 0.5}),
    ),
    repeat=REPEAT,
    seed=SEED,
)
