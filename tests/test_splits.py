import pytest

from grammar.splits import FillingSplit, FrameSplit, SplitSpec


def test_frame_split_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        FrameSplit("x", "", frozenset())


def test_filling_split_rejects_bad_sum():
    with pytest.raises(ValueError, match="sum to 0.6"):
        FillingSplit("train", {"a": 0.5, "b": 0.1})


def test_filling_split_rejects_negative():
    with pytest.raises(ValueError, match="negative"):
        FillingSplit("train", {"a": 1.5, "b": -0.5})


@pytest.mark.parametrize("n", [0, 1, 7, 8, 100])
def test_cut_sums_to_n(n):
    counts = FillingSplit("x", {"a": 0.75, "b": 0.25}).cut(n)
    assert sum(counts.values()) == n
    assert list(counts) == ["a", "b"]


def _spec(**kw):
    base = dict(
        frame_splits=(FrameSplit("train", "", frozenset({"A", "B"})), FrameSplit("ood", "", frozenset({"C"}))),
        filling_splits=(FillingSplit("train", {"train": 0.8, "dev": 0.2}), FillingSplit("ood", {"sel": 0.5, "rep": 0.5})),
        repeat=10, seed=0,
    )
    base.update(kw)
    return SplitSpec(**base)


def test_spec_validate_partition_ok():
    _spec().validate(frozenset({"A", "B", "C"}))


def test_spec_validate_reports_unassigned_unknown_duplicated():
    s = _spec(frame_splits=(FrameSplit("train", "", frozenset({"A", "B"})), FrameSplit("ood", "", frozenset({"B", "Z"}))))
    with pytest.raises(ValueError, match="unassigned \\['C'\\], unknown \\['Z'\\], duplicated \\['B'\\]"):
        s.validate(frozenset({"A", "B", "C"}))


def test_spec_rejects_filling_split_mismatch():
    with pytest.raises(ValueError, match="exactly once"):
        _spec(filling_splits=(FillingSplit("train", {"train": 1.0}),))


def test_spec_rejects_duplicate_subset_names():
    with pytest.raises(ValueError, match="unique across the spec"):
        _spec(filling_splits=(FillingSplit("train", {"x": 1.0}), FillingSplit("ood", {"x": 1.0})))


def test_spec_rejects_nonpositive_repeat():
    with pytest.raises(ValueError, match="repeat"):
        _spec(repeat=0)


def test_spec_lookups():
    s = _spec()
    assert s.frame_split_of("C") == "ood"
    assert s.filling_split_of("ood").subsets == {"sel": 0.5, "rep": 0.5}
    with pytest.raises(KeyError):
        s.frame_split_of("nope")
