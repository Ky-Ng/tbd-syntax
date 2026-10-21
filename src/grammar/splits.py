"""Shared split types. An experiment's ``splits.py`` only instantiates these.

Two levels of split:

* **frame-level** (:class:`FrameSplit`): which frames are in distribution and which
  are held out. Frames are the unit of generalisation, so every frame belongs to
  exactly one frame split.
* **filling-level** (:class:`FillingSplit`): within each frame split, how that
  frame's sampled fillings are divided into subsets (e.g. ``train``/``dev`` for
  in-distribution frames, ``select``/``report`` for out-of-distribution frames).
  Frames are never split between subsets; only sentences are.

:class:`SplitSpec` bundles both with the per-frame sample count and the RNG seed,
and validates the whole thing against the grammar's frame ids.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class FrameSplit:
    """A named set of frame ids.

    Parameters
    ----------
    name : str
        Split name, e.g. ``"train"``, ``"ood_level1"``.
    description : str
        One line saying what the split tests.
    frames : frozenset[str]
        Frame ids in this split.

    Examples
    --------
    >>> FrameSplit("ood_level1", "object-gap RC on the first noun",
    ...            frozenset({"F10", "F05", "F17"})).frames == {"F05", "F10", "F17"}
    True
    """

    name: str
    description: str
    frames: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", frozenset(self.frames))
        if not self.frames:
            raise ValueError(f"frame split {self.name!r} is empty")


@dataclass(frozen=True)
class FillingSplit:
    """How the fillings of one frame split are divided into output subsets.

    Parameters
    ----------
    frame_split : str
        Name of the :class:`FrameSplit` this applies to.
    subsets : Mapping[str, float]
        Output subset name -> fraction of each frame's fillings. Subset names are
        the output file names (``<name>.csv``) and must be unique across the whole
        :class:`SplitSpec`. Fractions must be non-negative and sum to 1.

    Raises
    ------
    ValueError
        If the fractions do not sum to 1 or any is negative.

    Examples
    --------
    >>> FillingSplit("train", {"train": 0.9, "dev": 0.1}).subsets
    {'train': 0.9, 'dev': 0.1}
    >>> FillingSplit("train", {"train": 0.5, "dev": 0.1})
    Traceback (most recent call last):
        ...
    ValueError: filling split for 'train': fractions sum to 0.6, not 1
    """

    frame_split: str
    subsets: Mapping[str, float]

    def __post_init__(self) -> None:
        object.__setattr__(self, "subsets", dict(self.subsets))
        if not self.subsets:
            raise ValueError(f"filling split for {self.frame_split!r} has no subsets")
        if any(f < 0 for f in self.subsets.values()):
            raise ValueError(f"filling split for {self.frame_split!r}: negative fraction")
        total = sum(self.subsets.values())
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(
                f"filling split for {self.frame_split!r}: fractions sum to {total:g}, not 1"
            )

    def cut(self, n: int) -> dict[str, int]:
        """Number of items each subset receives out of ``n``.

        Uses cumulative rounding so the counts always sum to ``n`` exactly.

        Parameters
        ----------
        n : int

        Returns
        -------
        counts : dict[str, int]
            Subset name -> count, in declaration order.

        Examples
        --------
        >>> FillingSplit("train", {"train": 0.9, "dev": 0.1}).cut(7)
        {'train': 6, 'dev': 1}
        """
        counts: dict[str, int] = {}
        cum = 0.0
        prev = 0
        for name, frac in self.subsets.items():
            cum += frac
            boundary = round(cum * n)
            counts[name] = boundary - prev
            prev = boundary
        counts[name] += n - prev  # absorb any rounding residue in the last subset
        return counts


@dataclass(frozen=True)
class SplitSpec:
    """Complete split specification for one experiment.

    Parameters
    ----------
    frame_splits : tuple[FrameSplit, ...]
        Must partition the grammar's frame ids (checked by :meth:`validate`).
    filling_splits : tuple[FillingSplit, ...]
        Exactly one per frame split.
    repeat : int
        Fillings sampled per frame (without replacement; capped at the number of
        distinct fillings).
    seed : int
        Base RNG seed. Each frame uses ``random.Random(f"{seed}:{frame_id}")`` so
        adding a frame never changes another frame's samples.

    Examples
    --------
    >>> spec = SplitSpec(
    ...     frame_splits=(FrameSplit("train", "in distribution", frozenset({"A", "B"})),
    ...                   FrameSplit("ood", "held out", frozenset({"C"}))),
    ...     filling_splits=(FillingSplit("train", {"train": 0.8, "dev": 0.2}),
    ...                     FillingSplit("ood", {"ood_select": 0.5, "ood_report": 0.5})),
    ...     repeat=100, seed=0)
    >>> spec.validate(frozenset({"A", "B", "C"}))
    >>> spec.frame_split_of("C")
    'ood'
    >>> spec.validate(frozenset({"A", "B", "C", "D"}))
    Traceback (most recent call last):
        ...
    ValueError: frame splits do not partition the grammar's frames: unassigned ['D'], unknown [], duplicated []
    """

    frame_splits: tuple[FrameSplit, ...]
    filling_splits: tuple[FillingSplit, ...]
    repeat: int
    seed: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "frame_splits", tuple(self.frame_splits))
        object.__setattr__(self, "filling_splits", tuple(self.filling_splits))
        if self.repeat <= 0:
            raise ValueError("repeat must be positive")
        names = [fs.name for fs in self.frame_splits]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate frame split names: {names}")
        targets = [fl.frame_split for fl in self.filling_splits]
        if sorted(targets) != sorted(names):
            raise ValueError(
                f"filling splits must name each frame split exactly once: "
                f"frame splits {sorted(names)}, filling splits {sorted(targets)}"
            )
        subset_names = [s for fl in self.filling_splits for s in fl.subsets]
        if len(set(subset_names)) != len(subset_names):
            raise ValueError(f"subset names must be unique across the spec: {subset_names}")

    def validate(self, frame_ids: frozenset[str]) -> None:
        """Check that the frame splits exactly partition ``frame_ids``.

        Parameters
        ----------
        frame_ids : frozenset[str]
            Usually ``{f.frame_id for f in grammar.enumerate_frames()}``.

        Raises
        ------
        ValueError
            Listing unassigned, unknown, and duplicated frame ids.
        """
        all_listed = [fid for fs in self.frame_splits for fid in fs.frames]
        duplicated = sorted({f for f in all_listed if all_listed.count(f) > 1})
        unassigned = sorted(frame_ids - set(all_listed))
        unknown = sorted(set(all_listed) - frame_ids)
        if duplicated or unassigned or unknown:
            raise ValueError(
                f"frame splits do not partition the grammar's frames: "
                f"unassigned {unassigned}, unknown {unknown}, duplicated {duplicated}"
            )

    def frame_split_of(self, frame_id: str) -> str:
        """Name of the frame split containing ``frame_id``.

        Parameters
        ----------
        frame_id : str

        Returns
        -------
        name : str

        Raises
        ------
        KeyError
            If no frame split lists ``frame_id``.
        """
        for fs in self.frame_splits:
            if frame_id in fs.frames:
                return fs.name
        raise KeyError(frame_id)

    def filling_split_of(self, frame_split: str) -> FillingSplit:
        """The :class:`FillingSplit` for a frame split name.

        Parameters
        ----------
        frame_split : str

        Returns
        -------
        filling_split : FillingSplit
        """
        for fl in self.filling_splits:
            if fl.frame_split == frame_split:
                return fl
        raise KeyError(frame_split)
