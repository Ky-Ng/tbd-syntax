import csv

import pytest

from grammar.generate_frames import FILLED_COLUMNS, FRAME_COLUMNS, generate, load_experiment, main


def _rows(path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def test_generate_writes_expected_files_and_counts(grammar, lexicon, spec, tmp_path):
    with pytest.warns(UserWarning, match="'T1'"):  # T1 has only 2 fillings, repeat is 8
        paths = generate(grammar, lexicon, spec, tmp_path)
    assert sorted(paths) == ["dev", "frames", "ood_report", "ood_select", "train"]
    assert all(p.is_file() for p in paths.values())

    frames = _rows(paths["frames"])
    assert [r["frame_id"] for r in frames] == ["T1", "T2", "T3", "T4", "T5"]
    assert list(frames[0]) == list(FRAME_COLUMNS) + ["gap", "matrix", "rc_on", "scrambled"]
    assert frames[0]["split"] == "train" and frames[2]["split"] == "ood"
    assert frames[0]["gap"] == "" and frames[2]["gap"] == "subj"
    assert frames[2]["alignment"] == "0 1 7 5 6 4 2 3"

    # T1: 2 fillings -> train 2, dev 0.  T2, T4: 8 -> 6 / 2.  T3, T5: 8 -> 4 / 4.
    counts = {k: len(_rows(p)) for k, p in paths.items() if k != "frames"}
    assert counts == {"train": 14, "dev": 4, "ood_select": 8, "ood_report": 8}
    assert list(_rows(paths["train"])[0]) == list(FILLED_COLUMNS)


def test_generate_subsets_are_disjoint_and_deterministic(grammar, lexicon, spec, tmp_path):
    with pytest.warns(UserWarning):
        a = generate(grammar, lexicon, spec, tmp_path / "a")
    with pytest.warns(UserWarning):
        b = generate(grammar, lexicon, spec, tmp_path / "b")
    seen = {}
    for name, p in a.items():
        if name == "frames":
            continue
        for r in _rows(p):
            assert r["source"] not in seen, f"{r['source']} in both {seen.get(r['source'])} and {name}"
            seen[r["source"]] = name
            assert r["subset"] == name
    for name in a:
        assert a[name].read_text() == b[name].read_text()


def test_load_experiment_contract(grammar, lexicon, spec):
    g, l, s = load_experiment("toy_experiment")
    assert (g, l, s) == (grammar, lexicon, spec)


def test_main_cli(tmp_path, capsys):
    with pytest.warns(UserWarning):
        main(["--experiment", "toy_experiment", "--out", str(tmp_path)])
    out = capsys.readouterr().out
    assert "frames" in out and "5 rows" in out and "ood_report" in out
