import random

import pytest

from grammar.grammar import Frame, Grammar, Lexicon, Rule
from toy_experiment.cfg import FRAME_IDS, PRETERMINALS, RULES

PT = frozenset({"N", "V_i"})


# ------------------------------------------------------------------ Rule / Lexicon
def test_rule_target_rhs_applies_permutation():
    assert Rule("r", "S", ("A", "B", "C"), (1, 2, 0)).target_rhs == ("B", "C", "A")


@pytest.mark.parametrize("perm", [(0, 0), (0, 1, 2), (1,), ()])
def test_rule_rejects_non_permutation(perm):
    with pytest.raises(ValueError, match="not a permutation"):
        Rule("r", "S", ("A", "B"), perm)


def test_rule_rejects_empty_rhs():
    with pytest.raises(ValueError, match="rhs must not be empty"):
        Rule("r", "S", (), ())


def test_lexicon_rejects_empty_category():
    with pytest.raises(ValueError, match="no words"):
        Lexicon({"N": ()})


def test_lexicon_rejects_word_in_two_categories():
    with pytest.raises(ValueError, match="two categories"):
        Lexicon({"V_t": ("sees",), "V_i": ("sees",)})


def test_lexicon_rejects_duplicate_word_in_category():
    with pytest.raises(ValueError, match="twice"):
        Lexicon({"N": ("dog", "dog")})


# ------------------------------------------------------------------ Grammar validation
def test_grammar_rejects_duplicate_rule_names():
    with pytest.raises(ValueError, match="duplicate rule names"):
        Grammar((Rule("a", "S", ("N",), (0,)), Rule("a", "S", ("V_i",), (0,))), "S", PT, {})


def test_grammar_rejects_unknown_rhs_symbol():
    with pytest.raises(ValueError, match="neither a rule lhs nor a preterminal"):
        Grammar((Rule("a", "S", ("N", "X"), (0, 1)),), "S", PT, {})


def test_grammar_rejects_preterminal_as_lhs():
    with pytest.raises(ValueError, match="preterminals used as rule lhs"):
        Grammar((Rule("a", "N", ("V_i",), (0,)),), "N", PT, {})


def test_grammar_rejects_missing_start():
    with pytest.raises(ValueError, match="start symbol"):
        Grammar((Rule("a", "S", ("N",), (0,)),), "X", PT, {})


def test_grammar_rejects_cycle():
    rules = (Rule("a", "S", ("NP", "V_i"), (0, 1)),
             Rule("b", "NP", ("N",), (0,)),
             Rule("c", "NP", ("NP", "N"), (0, 1)))
    with pytest.raises(ValueError, match="not finite.*NP -> NP"):
        Grammar(rules, "S", PT, {})


def test_grammar_rejects_ambiguity():
    rules = (Rule("a", "S", ("N", "V_i"), (0, 1)), Rule("b", "S", ("N", "V_i"), (1, 0)))
    with pytest.raises(ValueError, match="ambiguous grammar"):
        Grammar(rules, "S", PT, {"x": {}, "y": {}}).enumerate_frames()


def test_grammar_rejects_conflicting_tags():
    rules = (Rule("a", "S", ("NP", "V_i"), (0, 1), {"k": 1}), Rule("b", "NP", ("N",), (0,), {"k": 2}))
    with pytest.raises(ValueError, match="conflicting tag 'k'"):
        Grammar(rules, "S", PT, {"x": {}}).enumerate_frames()


# ------------------------------------------------------------------ frame ids
def test_frame_ids_missing_entry_raises():
    ids = {k: v for k, v in FRAME_IDS.items() if k != "T5"}
    with pytest.raises(ValueError, match="matches \\[\\]"):
        Grammar(RULES, "S", PRETERMINALS, ids).enumerate_frames()


def test_frame_ids_unused_entry_raises():
    ids = dict(FRAME_IDS, T9={"matrix": "nonexistent"})
    with pytest.raises(ValueError, match="no matching frame: \\['T9'\\]"):
        Grammar(RULES, "S", PRETERMINALS, ids).enumerate_frames()


def test_frame_ids_underspecified_entry_raises():
    ids = dict(FRAME_IDS, T2={"matrix": "trans", "scrambled": False})  # also matches T3
    with pytest.raises(ValueError, match="exactly one id"):
        Grammar(RULES, "S", PRETERMINALS, ids).enumerate_frames()


# ------------------------------------------------------------------ enumeration
def test_enumerate_toy_frames(grammar):
    frames = grammar.enumerate_frames()
    assert [f.frame_id for f in frames] == ["T1", "T2", "T3", "T4", "T5"]
    by_id = {f.frame_id: f for f in frames}
    t3 = by_id["T3"]
    assert t3.source_yield == ("N", "NOM", "N", "ACC", "V_t", "N", "ACC", "V_t")
    assert t3.target_yield == ("N", "NOM", "V_t", "N", "ACC", "V_t", "N", "ACC")
    assert t3.alignment == (0, 1, 7, 5, 6, 4, 2, 3)
    assert [r.name for r in t3.derivation] == ["S_t", "NP_nom", "NP_acc_rc", "RC_subj_gap"]
    assert t3.metadata == {"matrix": "trans", "scrambled": False, "rc_on": "obj", "gap": "subj"}
    assert by_id["T5"].source_yield == ("N", "ACC", "V_t", "N", "ACC", "N", "NOM", "V_t")


def test_scrambled_frames_share_target_with_unscrambled(grammar):
    by_id = {f.frame_id: f for f in grammar.enumerate_frames()}
    assert by_id["T2"].source_yield != by_id["T4"].source_yield
    assert by_id["T2"].target_yield == by_id["T4"].target_yield
    assert by_id["T3"].target_yield == by_id["T5"].target_yield


def test_validate_lexicon_mismatch(grammar):
    with pytest.raises(ValueError, match="missing \\['V_i'\\], extra \\['X'\\]"):
        grammar.validate_lexicon(Lexicon({"N": ("a",), "NOM": ("NOM",), "ACC": ("ACC",),
                                          "V_t": ("b",), "X": ("c",)}))


# ------------------------------------------------------------------ fill
def test_fill_is_without_replacement(grammar, lexicon):
    t3 = next(f for f in grammar.enumerate_frames() if f.frame_id == "T3")
    assert t3.product_size(lexicon) == 32  # 3 N slots x 2 V_t slots, 2 words each
    out = t3.fill(lexicon, 20, random.Random(1))
    assert len(out) == 20
    assert len({s.source for s in out}) == 20


def test_fill_caps_and_warns(grammar, lexicon):
    t1 = next(f for f in grammar.enumerate_frames() if f.frame_id == "T1")
    with pytest.warns(UserWarning, match="only 2 exist"):
        out = t1.fill(lexicon, 10, random.Random(0))
    assert sorted(s.source for s in out) == ["cat NOM swims", "dog NOM swims"]


def test_fill_is_deterministic(grammar, lexicon):
    t2 = next(f for f in grammar.enumerate_frames() if f.frame_id == "T2")
    a = t2.fill(lexicon, 5, random.Random(7))
    b = t2.fill(lexicon, 5, random.Random(7))
    assert a == b


def test_fill_target_follows_alignment(grammar, lexicon):
    for f in grammar.enumerate_frames():
        for s in f.fill(lexicon, 8, random.Random(3)):
            src = s.source.split()
            assert s.target.split() == [src[i] for i in f.alignment]


def test_fill_allows_repeated_words(grammar, lexicon):
    t2 = next(f for f in grammar.enumerate_frames() if f.frame_id == "T2")
    sources = {s.source for s in t2.fill(lexicon, 8, random.Random(0))}
    assert "dog NOM dog ACC chases" in sources


def test_frame_rejects_bad_alignment():
    with pytest.raises(ValueError, match="alignment"):
        Frame("x", (), ("N", "V_i"), ("V_i", "N"), (0, 1))
