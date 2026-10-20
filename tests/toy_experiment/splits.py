"""Toy splits: T1, T2, T4 in distribution; T3, T5 (the RC frames) held out."""

from grammar.splits import FillingSplit, FrameSplit, SplitSpec

SPLITS = SplitSpec(
    frame_splits=(
        FrameSplit("train", "no RC", frozenset({"T1", "T2", "T4"})),
        FrameSplit("ood", "subject-gap RC on the object", frozenset({"T3", "T5"})),
    ),
    filling_splits=(
        FillingSplit("train", {"train": 0.75, "dev": 0.25}),
        FillingSplit("ood", {"ood_select": 0.5, "ood_report": 0.5}),
    ),
    repeat=8,
    seed=0,
)
