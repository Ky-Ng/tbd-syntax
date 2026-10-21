"""Generate the Zapanese -> Zenglish datasets and upload them to the HuggingFace Hub.

Examples::

    # write frames.csv and filled/*.csv into src/grammar/zapanese_zenglish_simple/frames
    uv run python src/grammar/zapanese_zenglish_simple/run.py generate

    # same, elsewhere
    uv run python src/grammar/zapanese_zenglish_simple/run.py generate --out data/zzs

    # push both datasets (needs HF_TOKEN or `huggingface-cli login`)
    uv run python src/grammar/zapanese_zenglish_simple/run.py upload
    uv run python src/grammar/zapanese_zenglish_simple/run.py upload --private

Datasets created (public by default, per project policy)::

    kylelovesllms/zapanese_zenglish_simple-frames   <- frames.csv  + Frames.md card
    kylelovesllms/zapanese_zenglish_simple-filled   <- filled/*.csv + Filled.md card
    collection: translation-syntax-datasets-zapanese_zenglish_simple
"""

from __future__ import annotations

import argparse
from pathlib import Path

from grammar.generate_frames import generate
from grammar.zapanese_zenglish_simple.cfg import GRAMMAR
from grammar.zapanese_zenglish_simple.lexicon import LEXICON
from grammar.zapanese_zenglish_simple.splits import SPLITS
from upload.upload_hf import upload_dataset

EXPERIMENT = "zapanese_zenglish_simple"
HF_USER = "kylelovesllms"
COLLECTION = f"translation-syntax-datasets-{EXPERIMENT}"

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "frames"
CARDS = HERE / "hugging_face_frame_descriptions"


def cmd_generate(out: Path) -> dict[str, Path]:
    """Write the datasets and print a row-count table.

    Parameters
    ----------
    out : Path
        Output directory (``frames.csv`` and ``filled/`` go inside it).

    Returns
    -------
    paths : dict[str, Path]
        As returned by :func:`grammar.generate_frames.generate`.
    """
    paths = generate(GRAMMAR, LEXICON, SPLITS, out)
    width = max(len(k) for k in paths)
    for name, p in paths.items():
        with p.open(newline="") as fh:
            n_rows = sum(1 for _ in fh) - 1
        print(f"{name:<{width}}  {n_rows:>7} rows  {p.relative_to(Path.cwd()) if p.is_relative_to(Path.cwd()) else p}")
    return paths


def cmd_upload(out: Path, private: bool) -> list[str]:
    """Upload the frames and filled datasets and print their URLs.

    Parameters
    ----------
    out : Path
        Directory previously written by ``generate``.
    private : bool

    Returns
    -------
    urls : list[str]
    """
    if not (out / "frames.csv").is_file() or not (out / "filled").is_dir():
        raise SystemExit(f"{out} does not contain frames.csv and filled/; run `generate` first")
    urls = [
        upload_dataset(out, f"{HF_USER}/{EXPERIMENT}-frames", CARDS / "Frames.md", COLLECTION,
                       private=private, patterns=["frames.csv"]),
        upload_dataset(out / "filled", f"{HF_USER}/{EXPERIMENT}-filled", CARDS / "Filled.md", COLLECTION,
                       private=private),
    ]
    for u in urls:
        print(u)
    return urls


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    Parameters
    ----------
    argv : list[str] | None
        Arguments; ``None`` means ``sys.argv[1:]``.
    """
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate", help="write frames.csv and filled/*.csv")
    g.add_argument("--out", type=Path, default=DEFAULT_OUT)
    u = sub.add_parser("upload", help="upload a generated directory to the HF Hub")
    u.add_argument("--out", type=Path, default=DEFAULT_OUT, help="directory written by `generate`")
    u.add_argument("--private", action="store_true")
    args = ap.parse_args(argv)

    if args.command == "generate":
        cmd_generate(args.out)
    else:
        cmd_upload(args.out, args.private)


if __name__ == "__main__":
    main()
