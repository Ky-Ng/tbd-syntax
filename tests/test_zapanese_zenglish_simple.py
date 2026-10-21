"""The real experiment's grammar must reproduce the hand-written stimuli spreadsheet exactly."""

import csv
from pathlib import Path

import pytest

from grammar.generate_frames import load_experiment
from grammar.zapanese_zenglish_simple.cfg import GRAMMAR
from grammar.zapanese_zenglish_simple.lexicon import LEXICON, N_VERBS
from grammar.zapanese_zenglish_simple.splits import SPLITS

CSV = (Path(__file__).parent.parent / "src/grammar/zapanese_zenglish_simple/stimuli_examples"
       / "Japanese RC Stimuli - RC Frames with Stimuli.csv")

NOUN_TOKENS = {"SUBJ", "OBJ", "RC-SUBJ", "RC-OBJ"}


def _frame_tokens(frame: str, matrix_verb: str, rc_verb: str) -> tuple[str, ...]:
    """'SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB OBJ ACC' -> ('N','NOM','V_t','N','ACC','V_t','N','ACC')."""
    out = []
    for tok in frame.split():
        tok = tok.strip("[]")
        if tok in ("", "__"):
            continue
        if tok in NOUN_TOKENS:
            out.append("N")
        elif tok in ("NOM", "ACC"):
            out.append(tok)
        elif tok == "VERB":
            out.append("V_t" if matrix_verb == "Transitive" else "V_i")
        elif tok == "RC-VERB":
            out.append("V_t" if rc_verb == "Transitive" else "V_i")
        else:
            raise ValueError(tok)
    return tuple(out)


def _expected_metadata(row: dict[str, str]) -> dict[str, object]:
    md: dict[str, object] = {"matrix": "trans" if row["Matrix Verb"] == "Transitive" else "intrans"}
    if row["Is Scrambled?"] != "N/A":
        md["scrambled"] = row["Is Scrambled?"] == "Yes"
    md["rc_on"] = {"Subject": "subj", "Object": "obj", "N/A": "none"}[row["Attachment Site"]]
    if row["RC Gap Type"] != "N/A":
        md["gap"] = {"Subj-Gap": "subj", "Obj-Gap": "obj"}[row["RC Gap Type"]]
        md["rc_verb"] = "trans" if row["RC Verb"] == "Transitive" else "intrans"
    return md


@pytest.fixture(scope="module")
def csv_rows():
    with CSV.open(newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["Frame ID"]]


@pytest.fixture(scope="module")
def frames():
    return {f.frame_id: f for f in GRAMMAR.enumerate_frames()}


def test_exactly_18_frames_matching_spreadsheet_ids(frames, csv_rows):
    assert len(csv_rows) == 18
    assert set(frames) == {r["Frame ID"] for r in csv_rows}


def test_every_frame_matches_spreadsheet(frames, csv_rows):
    for row in csv_rows:
        f = frames[row["Frame ID"]]
        exp_src = _frame_tokens(row["Japanese Frame"], row["Matrix Verb"], row["RC Verb"])
        exp_tgt = _frame_tokens(row["English Frame"], row["Matrix Verb"], row["RC Verb"])
        assert f.source_yield == exp_src, (row["Frame ID"], "Zapanese")
        assert f.target_yield == exp_tgt, (row["Frame ID"], "Zenglish")
        assert dict(f.metadata) == _expected_metadata(row), row["Frame ID"]


def test_same_english_pairs_share_target(frames, csv_rows):
    pairs = [(r["Frame ID"], r["Same English"]) for r in csv_rows if r["Same English"]]
    assert len(pairs) == 14
    for a, b in pairs:
        assert frames[a].target_yield == frames[b].target_yield, (a, b)
        assert frames[a].source_yield != frames[b].source_yield, (a, b)


def test_splits_partition_frames_and_match_readme(frames):
    SPLITS.validate(frozenset(frames))
    by_split = {fs.name: fs.frames for fs in SPLITS.frame_splits}
    assert by_split["train"] == {"F11", "F01", "F02", "F03", "F12", "F16", "F18", "F08", "F15"}
    assert by_split["ood_level1"] == {"F10", "F05", "F17"}
    assert by_split["ood_level2"] == {"F04", "F13", "F06", "F07", "F09", "F14"}
    # train invariant from the journal: any RC in a train frame has a subject gap
    for fid in by_split["train"]:
        assert frames[fid].metadata.get("gap", "subj") == "subj"


def test_lexicon_shape_and_coverage():
    GRAMMAR.validate_lexicon(LEXICON)
    assert len(LEXICON.words["V_t"]) == len(LEXICON.words["V_i"]) == N_VERBS
    assert len(LEXICON.words["N"]) == 2 * N_VERBS


def test_load_experiment_contract():
    g, l, s = load_experiment("grammar.zapanese_zenglish_simple")
    assert (g, l, s) == (GRAMMAR, LEXICON, SPLITS)
