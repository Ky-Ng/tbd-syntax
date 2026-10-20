"""Shared engine for synchronous-CFG grammar experiments.

An experiment lives in ``src/grammar/<experiment>/`` and is fully specified by three
declarative files that a researcher reads or edits. None of them contains logic.

    cfg.py       RULES: tuple[Rule, ...]     the synchronous CFG (source order + target permutation)
                 FRAME_IDS: dict[str, dict]  spreadsheet frame id -> identifying metadata
                 GRAMMAR: Grammar            Grammar(RULES, START, PRETERMINALS, FRAME_IDS)
    lexicon.py   LEXICON: Lexicon            preterminal category -> words
    splits.py    SPLITS: SplitSpec           see ``grammar.splits``

This module turns that data into the two HuggingFace datasets:

    GRAMMAR.enumerate_frames()          -> list[Frame]    the "Frames" dataset (unfilled)
    frame.fill(LEXICON, n, rng)         -> list[Filled]   the "Filled" dataset

Terminology
-----------
category      Any symbol: a nonterminal (``"S"``, ``"NP_nom"``) or a preterminal
              (``"N"``, ``"V_t"``, ``"ACC"``). Rules may have right-hand sides of any
              length; ternary flat rules are the norm here and nothing is binarised.
derivation    The ordered sequence of rules used to expand the start symbol, stored
              in preorder (a tree flattened depth-first, left to right).
frame         One derivation plus its two preterminal yields, e.g.
              source ``N NOM N ACC V_t`` / target ``N NOM V_t N ACC``.
alignment     For each target position, the index of the source slot it was copied
              from. Filling a frame fills the source slots and copies words through
              the alignment, so source and target always agree word for word.
filled        A frame whose preterminal slots hold words from the lexicon.
frame_id      A stable, human-chosen id (``"F03"``) resolved by matching the frame's
              metadata against ``Grammar.frame_ids``.
metadata      The union of ``Rule.tags`` over a derivation, e.g.
              ``{"scrambled": True, "rc_on": "obj", "gap": "subj"}``. Becomes the
              extra columns of ``frames.csv``.

Constraints enforced at construction / enumeration time
--------------------------------------------------------
* The grammar is finite: no category can reach itself. This is what lets
  ``enumerate_frames`` be exhaustive and lets a duplicate check replace a parser.
* No two frames share a source yield. Otherwise translation would not be a function.
* ``frame_ids`` is a bijection with the enumerated frames.
* Lexicon categories are pairwise disjoint and exactly cover the preterminals, so the
  frame-level unambiguity check implies sentence-level unambiguity.
"""

from __future__ import annotations

import itertools
import math
import random
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Rule:
    """One synchronous rewrite rule ``lhs -> rhs`` with a target-side permutation.

    Parameters
    ----------
    name : str
        Unique, human-readable rule name (used in error messages and derivations).
    lhs : str
        Left-hand side category.
    rhs : tuple[str, ...]
        Right-hand side in *source* (Zapanese) order. Any length >= 1.
    target_perm : tuple[int, ...]
        Indices into ``rhs`` giving the *target* (Zenglish) order. Must be a
        permutation of ``range(len(rhs))``.
    tags : Mapping[str, Any], optional
        Metadata contributed to any frame whose derivation uses this rule. Tags
        from different rules in one derivation are merged; the same key with two
        different values is an error. Ignored for equality and hashing.

    Raises
    ------
    ValueError
        If ``target_perm`` is not a permutation of ``range(len(rhs))`` or ``rhs``
        is empty.

    Examples
    --------
    The scrambled matrix clause: object before subject in Zapanese, but the same
    Zenglish order as the unscrambled rule.

    >>> r = Rule("S_trans_scr", "S", ("NP_acc", "NP_nom", "V_t"), (1, 2, 0),
    ...          {"scrambled": True})
    >>> r.target_rhs
    ('NP_nom', 'V_t', 'NP_acc')
    >>> Rule("bad", "S", ("A", "B"), (0, 0))
    Traceback (most recent call last):
        ...
    ValueError: rule 'bad': target_perm (0, 0) is not a permutation of range(2)
    """

    name: str
    lhs: str
    rhs: tuple[str, ...]
    target_perm: tuple[int, ...]
    tags: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rhs", tuple(self.rhs))
        object.__setattr__(self, "target_perm", tuple(self.target_perm))
        object.__setattr__(self, "tags", dict(self.tags))
        if not self.rhs:
            raise ValueError(f"rule {self.name!r}: rhs must not be empty")
        if sorted(self.target_perm) != list(range(len(self.rhs))):
            raise ValueError(
                f"rule {self.name!r}: target_perm {self.target_perm} is not a "
                f"permutation of range({len(self.rhs)})"
            )

    @property
    def target_rhs(self) -> tuple[str, ...]:
        """Right-hand side in target (Zenglish) order.

        Returns
        -------
        rhs : tuple[str, ...]
            ``self.rhs`` reordered by ``self.target_perm``.

        Examples
        --------
        >>> Rule("RC_subj_gap", "RC", ("N", "ACC", "V_t"), (2, 0, 1)).target_rhs
        ('V_t', 'N', 'ACC')
        """
        return tuple(self.rhs[i] for i in self.target_perm)


@dataclass(frozen=True)
class Lexicon:
    """Preterminal category -> words.

    Parameters
    ----------
    words : Mapping[str, tuple[str, ...]]
        For each preterminal category, the words that may fill it. Case markers
        are ordinary one-word categories (``{"NOM": ("NOM",)}``) so the grammar
        never hard-codes surface strings.

    Raises
    ------
    ValueError
        If a category is empty, a word is listed twice in one category, or a word
        appears under two categories (which would make filled sentences ambiguous
        even when the frames are not).

    Examples
    --------
    >>> lex = Lexicon({"N": ("dog", "cat"), "V_t": ("chases",), "V_i": ("swims",),
    ...                "NOM": ("NOM",), "ACC": ("ACC",)})
    >>> sorted(lex.categories)
    ['ACC', 'N', 'NOM', 'V_i', 'V_t']
    >>> Lexicon({"V_t": ("sees",), "V_i": ("sees",)})
    Traceback (most recent call last):
        ...
    ValueError: word 'sees' appears in two categories: 'V_i' and 'V_t'
    """

    words: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "words", {c: tuple(w) for c, w in self.words.items()})
        seen: dict[str, str] = {}
        for cat in sorted(self.words):
            ws = self.words[cat]
            if not ws:
                raise ValueError(f"category {cat!r} has no words")
            if len(set(ws)) != len(ws):
                raise ValueError(f"category {cat!r} lists a word twice: {ws}")
            for w in ws:
                if w in seen:
                    raise ValueError(
                        f"word {w!r} appears in two categories: {seen[w]!r} and {cat!r}"
                    )
                seen[w] = cat

    @property
    def categories(self) -> frozenset[str]:
        """The set of preterminal categories this lexicon covers.

        Returns
        -------
        categories : frozenset[str]
        """
        return frozenset(self.words)


@dataclass(frozen=True)
class Filled:
    """A filled sentence pair.

    Parameters
    ----------
    frame_id : str
        Id of the frame this sentence instantiates.
    source : str
        Space-joined source (Zapanese) tokens.
    target : str
        Space-joined target (Zenglish) tokens.

    Examples
    --------
    >>> Filled("F02", "cat ACC dog NOM chases", "dog NOM chases cat ACC").target
    'dog NOM chases cat ACC'
    """

    frame_id: str
    source: str
    target: str


@dataclass(frozen=True)
class Frame:
    """An unfilled sentence: one derivation and its two preterminal yields.

    Instances are produced by :meth:`Grammar.enumerate_frames`; constructing them
    by hand is only useful in tests.

    Parameters
    ----------
    frame_id : str
        Human-chosen id resolved from ``Grammar.frame_ids`` (e.g. ``"F03"``).
    derivation : tuple[Rule, ...]
        Rules applied, in preorder.
    source_yield : tuple[str, ...]
        Preterminal categories in source order. Each position is a *slot*.
    target_yield : tuple[str, ...]
        Preterminal categories in target order.
    alignment : tuple[int, ...]
        ``alignment[j]`` is the source slot that target position ``j`` copies.
    metadata : Mapping[str, Any]
        Merged ``Rule.tags`` over the derivation.

    Examples
    --------
    >>> f = Frame("F02", (), ("N", "ACC", "N", "NOM", "V_t"),
    ...           ("N", "NOM", "V_t", "N", "ACC"), (2, 3, 4, 0, 1), {"scrambled": True})
    >>> f.length
    5
    """

    frame_id: str
    derivation: tuple[Rule, ...]
    source_yield: tuple[str, ...]
    target_yield: tuple[str, ...]
    alignment: tuple[int, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False, hash=False)

    def __post_init__(self) -> None:
        if len(self.alignment) != len(self.target_yield):
            raise ValueError("alignment must have one entry per target position")
        if tuple(self.source_yield[i] for i in self.alignment) != tuple(self.target_yield):
            raise ValueError("alignment does not map source_yield onto target_yield")

    @property
    def length(self) -> int:
        """Number of source tokens.

        Returns
        -------
        length : int
        """
        return len(self.source_yield)

    def product_size(self, lexicon: Lexicon) -> int:
        """Number of distinct fillings this frame has under ``lexicon``.

        Parameters
        ----------
        lexicon : Lexicon

        Returns
        -------
        size : int
            Product over source slots of the category's word count.

        Examples
        --------
        >>> lex = Lexicon({"N": ("dog", "cat"), "NOM": ("NOM",), "V_i": ("swims", "dances")})
        >>> f = Frame("T1", (), ("N", "NOM", "V_i"), ("N", "NOM", "V_i"), (0, 1, 2))
        >>> f.product_size(lex)
        4
        """
        return math.prod(len(lexicon.words[cat]) for cat in self.source_yield)

    def fill(self, lexicon: Lexicon, n: int, rng: random.Random) -> list[Filled]:
        """Sample ``n`` distinct fillings **without replacement**.

        The Cartesian product of word choices is never materialised: ``n`` distinct
        integers are drawn from ``range(product_size)`` and each is un-ranked
        (mixed radix, slot 0 least significant) into one word per source slot.
        The target sentence copies words through ``alignment``. The same word may
        fill several slots (``dog NOM dog ACC chases`` is legal).

        Parameters
        ----------
        lexicon : Lexicon
            Must cover every category in ``source_yield``.
        n : int
            Number of fillings requested.
        rng : random.Random
            Seeded generator; the same seed gives the same fillings.

        Returns
        -------
        filled : list[Filled]
            ``min(n, product_size)`` distinct sentences.

        Warns
        -----
        UserWarning
            If ``n`` exceeds ``product_size``; the result is then every filling.

        Examples
        --------
        >>> lex = Lexicon({"N": ("dog", "cat"), "NOM": ("NOM",), "ACC": ("ACC",),
        ...                "V_t": ("chases",)})
        >>> f = Frame("F02", (), ("N", "ACC", "N", "NOM", "V_t"),
        ...           ("N", "NOM", "V_t", "N", "ACC"), (2, 3, 4, 0, 1))
        >>> for s in f.fill(lex, 2, random.Random(0)):
        ...     print(s.source, "->", s.target)
        cat ACC cat NOM chases -> cat NOM chases cat ACC
        cat ACC dog NOM chases -> dog NOM chases cat ACC
        """
        size = self.product_size(lexicon)
        if n > size:
            warnings.warn(
                f"frame {self.frame_id!r}: requested {n} fillings but only {size} exist; "
                f"returning all {size}",
                stacklevel=2,
            )
        indices = rng.sample(range(size), min(n, size))
        out: list[Filled] = []
        for idx in indices:
            words: list[str] = []
            for cat in self.source_yield:
                choices = lexicon.words[cat]
                idx, r = divmod(idx, len(choices))
                words.append(choices[r])
            target = [words[i] for i in self.alignment]
            out.append(Filled(self.frame_id, " ".join(words), " ".join(target)))
        return out


# One partially expanded category: (rules in preorder, source categories, alignment).
_Expansion = tuple[tuple[Rule, ...], tuple[str, ...], tuple[int, ...]]


@dataclass(frozen=True)
class Grammar:
    """A finite synchronous CFG whose language can be enumerated exhaustively.

    Parameters
    ----------
    rules : tuple[Rule, ...]
        All rules. Names must be unique. Order within one ``lhs`` is the order
        derivations are generated in.
    start : str
        Start category; must be the ``lhs`` of at least one rule.
    preterminals : frozenset[str]
        Categories expanded by the lexicon, never by a rule.
    frame_ids : Mapping[str, Mapping[str, Any]]
        Human-chosen frame id -> metadata that identifies that frame. An entry
        matches a frame when every key/value in the entry appears in the frame's
        metadata. ``enumerate_frames`` requires this to be a bijection.

    Raises
    ------
    ValueError
        Duplicate rule name; a preterminal used as a ``lhs``; a right-hand-side
        symbol that is neither a ``lhs`` nor a preterminal; ``start`` not a ``lhs``;
        or a category that can reach itself (infinite language).

    Examples
    --------
    A two-frame grammar: intransitive and transitive matrix clauses.

    >>> rules = (
    ...     Rule("S_i", "S", ("N", "NOM", "V_i"), (0, 1, 2), {"matrix": "intrans"}),
    ...     Rule("S_t", "S", ("N", "NOM", "N", "ACC", "V_t"), (0, 1, 4, 2, 3), {"matrix": "trans"}),
    ... )
    >>> g = Grammar(rules, "S", frozenset({"N", "NOM", "ACC", "V_t", "V_i"}),
    ...             {"F11": {"matrix": "intrans"}, "F01": {"matrix": "trans"}})
    >>> [(f.frame_id, " ".join(f.source_yield), " ".join(f.target_yield))
    ...  for f in g.enumerate_frames()]
    [('F01', 'N NOM N ACC V_t', 'N NOM V_t N ACC'), ('F11', 'N NOM V_i', 'N NOM V_i')]
    """

    rules: tuple[Rule, ...]
    start: str
    preterminals: frozenset[str]
    frame_ids: Mapping[str, Mapping[str, Any]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))
        object.__setattr__(self, "preterminals", frozenset(self.preterminals))
        object.__setattr__(self, "frame_ids", {k: dict(v) for k, v in self.frame_ids.items()})

        names = [r.name for r in self.rules]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            raise ValueError(f"duplicate rule names: {sorted(dup)}")
        lhs_set = {r.lhs for r in self.rules}
        bad_lhs = lhs_set & self.preterminals
        if bad_lhs:
            raise ValueError(f"preterminals used as rule lhs: {sorted(bad_lhs)}")
        for r in self.rules:
            unknown = [s for s in r.rhs if s not in lhs_set and s not in self.preterminals]
            if unknown:
                raise ValueError(
                    f"rule {r.name!r}: rhs symbols {unknown} are neither a rule lhs "
                    f"nor a preterminal"
                )
        if self.start not in lhs_set:
            raise ValueError(f"start symbol {self.start!r} is not the lhs of any rule")
        cycle = self._find_cycle(lhs_set)
        if cycle:
            raise ValueError(
                f"grammar is not finite: category cycle {' -> '.join(cycle)}"
            )

    # ----------------------------------------------------------------- validation
    def _find_cycle(self, nonterminals: set[str]) -> list[str] | None:
        """Return a category cycle as a path, or ``None`` if the grammar is acyclic."""
        graph: dict[str, set[str]] = {nt: set() for nt in nonterminals}
        for r in self.rules:
            graph[r.lhs].update(s for s in r.rhs if s in nonterminals)
        WHITE, GREY, BLACK = 0, 1, 2
        colour = {nt: WHITE for nt in nonterminals}
        path: list[str] = []

        def visit(u: str) -> list[str] | None:
            colour[u] = GREY
            path.append(u)
            for v in sorted(graph[u]):
                if colour[v] == GREY:
                    return path[path.index(v):] + [v]
                if colour[v] == WHITE:
                    found = visit(v)
                    if found:
                        return found
            path.pop()
            colour[u] = BLACK
            return None

        for nt in sorted(nonterminals):
            if colour[nt] == WHITE:
                found = visit(nt)
                if found:
                    return found
        return None

    def validate_lexicon(self, lexicon: Lexicon) -> None:
        """Check that ``lexicon`` covers exactly this grammar's preterminals.

        Parameters
        ----------
        lexicon : Lexicon

        Raises
        ------
        ValueError
            Listing missing and extra categories.

        Examples
        --------
        >>> g = Grammar((Rule("S", "S", ("N", "V_i"), (0, 1)),), "S",
        ...             frozenset({"N", "V_i"}), {"T": {}})
        >>> g.validate_lexicon(Lexicon({"N": ("dog",)}))
        Traceback (most recent call last):
            ...
        ValueError: lexicon does not match grammar preterminals: missing ['V_i'], extra []
        """
        missing = sorted(self.preterminals - lexicon.categories)
        extra = sorted(lexicon.categories - self.preterminals)
        if missing or extra:
            raise ValueError(
                f"lexicon does not match grammar preterminals: missing {missing}, extra {extra}"
            )

    # ---------------------------------------------------------------- enumeration
    def _expand(self, category: str, memo: dict[str, list[_Expansion]]) -> list[_Expansion]:
        """All expansions of ``category``: (rules preorder, source yield, alignment)."""
        if category in self.preterminals:
            return [((), (category,), (0,))]
        if category in memo:
            return memo[category]
        out: list[_Expansion] = []
        for rule in self.rules:
            if rule.lhs != category:
                continue
            child_options = [self._expand(sym, memo) for sym in rule.rhs]
            for combo in itertools.product(*child_options):
                offsets: list[int] = []
                off = 0
                for _, src, _ in combo:
                    offsets.append(off)
                    off += len(src)
                rules = (rule,) + tuple(r for child_rules, _, _ in combo for r in child_rules)
                source = tuple(s for _, src, _ in combo for s in src)
                alignment = tuple(
                    offsets[i] + j for i in rule.target_perm for j in combo[i][2]
                )
                out.append((rules, source, alignment))
        memo[category] = out
        return out

    @staticmethod
    def _merge_tags(derivation: tuple[Rule, ...]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for r in derivation:
            for k, v in r.tags.items():
                if k in merged and merged[k] != v:
                    raise ValueError(
                        f"conflicting tag {k!r} in derivation "
                        f"{[r.name for r in derivation]}: {merged[k]!r} vs {v!r} (rule {r.name!r})"
                    )
                merged[k] = v
        return merged

    def enumerate_frames(self) -> list[Frame]:
        """Exhaustively enumerate every derivation from ``start``.

        Returns
        -------
        frames : list[Frame]
            One per derivation, sorted by ``frame_id``.

        Raises
        ------
        ValueError
            If two derivations yield the same source string (translation would not
            be a function); if a derivation merges conflicting tags; or if
            ``frame_ids`` is not a bijection with the derivations (a frame with no
            or several matching ids, or an id matching no or several frames).

        Examples
        --------
        See the class docstring. A grammar whose two rules produce the same
        source yield is rejected:

        >>> rules = (Rule("a", "S", ("N", "V_i"), (0, 1)), Rule("b", "S", ("N", "V_i"), (1, 0)))
        >>> g = Grammar(rules, "S", frozenset({"N", "V_i"}), {"x": {}, "y": {}})
        >>> g.enumerate_frames()
        Traceback (most recent call last):
            ...
        ValueError: ambiguous grammar: derivations ['a'] and ['b'] both yield 'N V_i'
        """
        expansions = self._expand(self.start, {})

        seen: dict[tuple[str, ...], tuple[Rule, ...]] = {}
        for rules, source, _ in expansions:
            if source in seen:
                raise ValueError(
                    f"ambiguous grammar: derivations {[r.name for r in seen[source]]} and "
                    f"{[r.name for r in rules]} both yield {' '.join(source)!r}"
                )
            seen[source] = rules

        frames: list[Frame] = []
        used: dict[str, tuple[str, ...]] = {}
        for rules, source, alignment in expansions:
            metadata = self._merge_tags(rules)
            matches = [
                fid for fid, spec in self.frame_ids.items()
                if all(k in metadata and metadata[k] == v for k, v in spec.items())
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"frame_ids must match exactly one id per frame: derivation "
                    f"{[r.name for r in rules]} with metadata {metadata} matches {matches}"
                )
            fid = matches[0]
            if fid in used:
                raise ValueError(
                    f"frame id {fid!r} matches two frames: {' '.join(used[fid])!r} and "
                    f"{' '.join(source)!r}; add tags to distinguish them"
                )
            used[fid] = source
            target = tuple(source[i] for i in alignment)
            frames.append(Frame(fid, rules, source, target, alignment, metadata))

        unused = sorted(set(self.frame_ids) - set(used))
        if unused:
            raise ValueError(f"frame ids with no matching frame: {unused}")
        frames.sort(key=lambda f: f.frame_id)
        return frames
