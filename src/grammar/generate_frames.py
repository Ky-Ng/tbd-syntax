"""Turn (Grammar, Lexicon, SplitSpec) into the Frames and Filled CSV datasets.

Library plus CLI. Contains no grammar logic; everything linguistic lives in
``grammar.grammar`` and the experiment's data files.

Output layout (``out_dir``)::

    frames.csv                  one row per frame: id, split, both yields, alignment,
                                derivation, and one column per metadata key
    filled/<subset>.csv         one file per filling subset, e.g. train.csv, dev.csv,
                                ood_level1_select.csv, ood_level1_report.csv, ...

Command line::

    uv run python -m grammar.generate_frames \\
        --experiment grammar.zapanese_zenglish_simple --out data/zapanese_zenglish_simple
"""

from __future__ import annotations

import argparse
import csv
import importlib
import random
from pathlib import Path

from grammar.grammar import Frame, Grammar, Lexicon
from grammar.splits import SplitSpec

FRAME_COLUMNS = ("frame_id", "split", "source_frame", "target_frame", "alignment", "derivation")
FILLED_COLUMNS = ("frame_id", "frame_split", "subset", "source", "target")


def load_experiment(module: str) -> tuple[Grammar, Lexicon, SplitSpec]:
    """Import an experiment package and return its three data objects.

    The package must contain ``cfg.py`` exposing ``GRAMMAR``, ``lexicon.py``
    exposing ``LEXICON`` and ``splits.py`` exposing ``SPLITS``. This is the whole
    contract between the engine and an experiment.

    Parameters
    ----------
    module : str
        Dotted package name, e.g. ``"grammar.zapanese_zenglish_simple"``.

    Returns
    -------
    grammar : Grammar
    lexicon : Lexicon
    splits : SplitSpec

    Examples
    --------
    >>> grammar, lexicon, splits = load_experiment("grammar.zapanese_zenglish_simple")  # doctest: +SKIP
    """
    cfg = importlib.import_module(f"{module}.cfg")
    lex = importlib.import_module(f"{module}.lexicon")
    spl = importlib.import_module(f"{module}.splits")
    return cfg.GRAMMAR, lex.LEXICON, spl.SPLITS


def frame_rows(frames: list[Frame], spec: SplitSpec) -> tuple[list[str], list[dict[str, str]]]:
    """Rows for ``frames.csv``.

    Parameters
    ----------
    frames : list[Frame]
    spec : SplitSpec
        Used to look up each frame's split.

    Returns
    -------
    columns : list[str]
        ``FRAME_COLUMNS`` followed by every metadata key seen, sorted.
    rows : list[dict[str, str]]
        One per frame; missing metadata keys are ``""``.

    Examples
    --------
    >>> from grammar.grammar import Rule
    >>> from grammar.splits import FrameSplit, FillingSplit
    >>> g = Grammar((Rule("S", "S", ("N", "V_i"), (0, 1), {"matrix": "intrans"}),),
    ...             "S", frozenset({"N", "V_i"}), {"T1": {"matrix": "intrans"}})
    >>> spec = SplitSpec((FrameSplit("train", "", frozenset({"T1"})),),
    ...                  (FillingSplit("train", {"train": 1.0}),), repeat=1, seed=0)
    >>> cols, rows = frame_rows(g.enumerate_frames(), spec)
    >>> cols[-1], rows[0]["source_frame"], rows[0]["matrix"]
    ('matrix', 'N V_i', 'intrans')
    """
    meta_keys = sorted({k for f in frames for k in f.metadata})
    columns = list(FRAME_COLUMNS) + meta_keys
    rows = []
    for f in frames:
        row = {
            "frame_id": f.frame_id,
            "split": spec.frame_split_of(f.frame_id),
            "source_frame": " ".join(f.source_yield),
            "target_frame": " ".join(f.target_yield),
            "alignment": " ".join(map(str, f.alignment)),
            "derivation": " ".join(r.name for r in f.derivation),
        }
        for k in meta_keys:
            v = f.metadata.get(k, "")
            row[k] = "" if v is None else str(v)
        rows.append(row)
    return columns, rows


def generate(grammar: Grammar, lexicon: Lexicon, spec: SplitSpec, out_dir: Path) -> dict[str, Path]:
    """Write ``frames.csv`` and one ``filled/<subset>.csv`` per filling subset.

    For each frame, ``spec.repeat`` fillings are sampled without replacement with
    ``random.Random(f"{spec.seed}:{frame_id}")``, shuffled, and cut by the
    frame split's :class:`~grammar.splits.FillingSplit` fractions. No sentence
    appears in two subsets.

    Parameters
    ----------
    grammar : Grammar
    lexicon : Lexicon
    spec : SplitSpec
    out_dir : Path
        Created if missing. Existing files with the same names are overwritten.

    Returns
    -------
    paths : dict[str, Path]
        ``{"frames": out_dir/frames.csv, <subset>: out_dir/filled/<subset>.csv, ...}``.

    Raises
    ------
    ValueError
        From the grammar / lexicon / split validations.

    Examples
    --------
    >>> paths = generate(GRAMMAR, LEXICON, SPLITS, Path("data/zapanese_zenglish_simple"))  # doctest: +SKIP
    >>> sorted(paths)  # doctest: +SKIP
    ['dev', 'frames', 'ood_level1_report', 'ood_level1_select', 'ood_level2_report', 'ood_level2_select', 'train']
    """
    grammar.validate_lexicon(lexicon)
    frames = grammar.enumerate_frames()
    spec.validate(frozenset(f.frame_id for f in frames))

    out_dir = Path(out_dir)
    filled_dir = out_dir / "filled"
    filled_dir.mkdir(parents=True, exist_ok=True)

    columns, rows = frame_rows(frames, spec)
    frames_path = out_dir / "frames.csv"
    with frames_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)

    subset_rows: dict[str, list[dict[str, str]]] = {
        s: [] for fl in spec.filling_splits for s in fl.subsets
    }
    for f in frames:
        frame_split = spec.frame_split_of(f.frame_id)
        filling = spec.filling_split_of(frame_split)
        rng = random.Random(f"{spec.seed}:{f.frame_id}")
        sentences = f.fill(lexicon, spec.repeat, rng)
        rng.shuffle(sentences)
        start = 0
        for subset, count in filling.cut(len(sentences)).items():
            for s in sentences[start:start + count]:
                subset_rows[subset].append({
                    "frame_id": s.frame_id, "frame_split": frame_split,
                    "subset": subset, "source": s.source, "target": s.target,
                })
            start += count

    paths = {"frames": frames_path}
    for subset, srows in subset_rows.items():
        p = filled_dir / f"{subset}.csv"
        with p.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FILLED_COLUMNS)
            w.writeheader()
            w.writerows(srows)
        paths[subset] = p
    return paths


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    Parameters
    ----------
    argv : list[str] | None
        Arguments; ``None`` means ``sys.argv[1:]``.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--experiment", required=True,
                    help="dotted experiment package, e.g. grammar.zapanese_zenglish_simple")
    ap.add_argument("--out", required=True, type=Path, help="output directory")
    args = ap.parse_args(argv)

    grammar, lexicon, spec = load_experiment(args.experiment)
    paths = generate(grammar, lexicon, spec, args.out)
    width = max(len(k) for k in paths)
    for name, p in paths.items():
        with p.open(newline="") as fh:
            n_rows = sum(1 for _ in fh) - 1
        print(f"{name:<{width}}  {n_rows:>7} rows  {p}")


if __name__ == "__main__":
    main()
