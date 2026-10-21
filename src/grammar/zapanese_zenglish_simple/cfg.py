"""Zapanese -> Zenglish synchronous CFG. Data only; see ``grammar.grammar`` for the engine.

Zapanese is head-final (verb last, RC before its noun); Zenglish is head-initial
(verb after the subject, RC after its noun). Each rule gives the Zapanese order and
the permutation that produces the Zenglish order.

Design decisions (see README.md, "Stimuli"):

* **Flat ternary rules.** The matrix clause and the RC are single rules, not a VP.
  That is what lets scrambling be one extra rule (``S_scr``: object before subject)
  with the *same* Zenglish permutation target as the unscrambled rule.
* **Exactly one RC per sentence**, enforced by spelling out which argument carries
  it in the ``S`` rules. RC arguments are bare nouns, so RCs never nest.
* **Every RC has exactly one gap.** Scrambling inside an RC is therefore string-
  vacuous and not modelled.
* Case markers are preterminals (``NOM``, ``ACC``) filled by the lexicon, so the
  grammar never hard-codes surface strings.

Frame metadata columns (merged ``tags``): ``matrix`` (trans/intrans), ``scrambled``
(True/False; absent for intransitive matrix), ``rc_on`` (subj/obj/none), ``gap``
(subj/obj) and ``rc_verb`` (trans/intrans) (both absent when there is no RC).
``FRAME_IDS`` ties these to the F-numbers of the stimuli spreadsheet and the README.
"""

from grammar.grammar import Grammar, Rule

START = "S"
PRETERMINALS = frozenset({"N", "NOM", "ACC", "V_t", "V_i"})

RULES: tuple[Rule, ...] = (
    # ------------------------------------------------------------- matrix clause
    # intransitive: no object, so nothing to scramble
    Rule("S_intrans",      "S", ("NP_nom", "V_i"),                 (0, 1),    {"matrix": "intrans", "rc_on": "none"}),
    Rule("S_intrans_rcS",  "S", ("NP_nom_rc", "V_i"),              (0, 1),    {"matrix": "intrans"}),
    # transitive, canonical SOV  ->  SVO
    Rule("S_trans",        "S", ("NP_nom", "NP_acc", "V_t"),       (0, 2, 1), {"matrix": "trans", "scrambled": False, "rc_on": "none"}),
    Rule("S_trans_rcS",    "S", ("NP_nom_rc", "NP_acc", "V_t"),    (0, 2, 1), {"matrix": "trans", "scrambled": False}),
    Rule("S_trans_rcO",    "S", ("NP_nom", "NP_acc_rc", "V_t"),    (0, 2, 1), {"matrix": "trans", "scrambled": False}),
    # transitive, scrambled OSV  ->  SVO (same Zenglish as above)
    Rule("S_scr",          "S", ("NP_acc", "NP_nom", "V_t"),       (1, 2, 0), {"matrix": "trans", "scrambled": True, "rc_on": "none"}),
    Rule("S_scr_rcS",      "S", ("NP_acc", "NP_nom_rc", "V_t"),    (1, 2, 0), {"matrix": "trans", "scrambled": True}),
    Rule("S_scr_rcO",      "S", ("NP_acc_rc", "NP_nom", "V_t"),    (1, 2, 0), {"matrix": "trans", "scrambled": True}),
    # ------------------------------------------------------------- noun phrases
    Rule("NP_nom",         "NP_nom",    ("N", "NOM"),              (0, 1)),
    Rule("NP_acc",         "NP_acc",    ("N", "ACC"),              (0, 1)),
    # RC is pre-nominal in Zapanese, post-nominal in Zenglish:  RC N CASE -> N CASE RC
    Rule("NP_nom_rc",      "NP_nom_rc", ("RC", "N", "NOM"),        (1, 2, 0), {"rc_on": "subj"}),
    Rule("NP_acc_rc",      "NP_acc_rc", ("RC", "N", "ACC"),        (1, 2, 0), {"rc_on": "obj"}),
    # ------------------------------------------------------------- relative clauses (one gap each)
    # subject gap, transitive:   [__ RC-OBJ ACC RC-VERB]  ->  [__ RC-VERB RC-OBJ ACC]
    Rule("RC_subj_gap",    "RC", ("N", "ACC", "V_t"),              (2, 0, 1), {"gap": "subj", "rc_verb": "trans"}),
    # object gap:                [RC-SUBJ NOM __ RC-VERB]  ->  [RC-SUBJ NOM RC-VERB __]
    Rule("RC_obj_gap",     "RC", ("N", "NOM", "V_t"),              (0, 1, 2), {"gap": "obj", "rc_verb": "trans"}),
    # subject gap, intransitive: [__ RC-VERB]  ->  [__ RC-VERB]
    Rule("RC_subj_gap_i",  "RC", ("V_i",),                         (0,),      {"gap": "subj", "rc_verb": "intrans"}),
)

# Spreadsheet frame id -> identifying metadata. Must be a bijection with the frames
# the grammar enumerates (checked by Grammar.enumerate_frames).
FRAME_IDS: dict[str, dict[str, object]] = {
    # no RC
    "F11": {"matrix": "intrans", "rc_on": "none"},
    "F01": {"matrix": "trans", "scrambled": False, "rc_on": "none"},
    "F02": {"matrix": "trans", "scrambled": True,  "rc_on": "none"},
    # RC on subject, unscrambled
    "F03": {"matrix": "trans", "scrambled": False, "rc_on": "subj", "gap": "subj", "rc_verb": "trans"},
    "F05": {"matrix": "trans", "scrambled": False, "rc_on": "subj", "gap": "obj",  "rc_verb": "trans"},
    "F12": {"matrix": "trans", "scrambled": False, "rc_on": "subj", "gap": "subj", "rc_verb": "intrans"},
    # RC on subject, intransitive matrix
    "F16": {"matrix": "intrans", "rc_on": "subj", "gap": "subj", "rc_verb": "trans"},
    "F17": {"matrix": "intrans", "rc_on": "subj", "gap": "obj",  "rc_verb": "trans"},
    "F18": {"matrix": "intrans", "rc_on": "subj", "gap": "subj", "rc_verb": "intrans"},
    # RC on object, scrambled (object + its RC come first)
    "F10": {"matrix": "trans", "scrambled": True,  "rc_on": "obj", "gap": "obj",  "rc_verb": "trans"},
    "F08": {"matrix": "trans", "scrambled": True,  "rc_on": "obj", "gap": "subj", "rc_verb": "trans"},
    "F15": {"matrix": "trans", "scrambled": True,  "rc_on": "obj", "gap": "subj", "rc_verb": "intrans"},
    # RC on object, unscrambled
    "F04": {"matrix": "trans", "scrambled": False, "rc_on": "obj", "gap": "subj", "rc_verb": "trans"},
    "F13": {"matrix": "trans", "scrambled": False, "rc_on": "obj", "gap": "subj", "rc_verb": "intrans"},
    "F06": {"matrix": "trans", "scrambled": False, "rc_on": "obj", "gap": "obj",  "rc_verb": "trans"},
    # RC on subject, scrambled (bare object comes first)
    "F07": {"matrix": "trans", "scrambled": True,  "rc_on": "subj", "gap": "subj", "rc_verb": "trans"},
    "F09": {"matrix": "trans", "scrambled": True,  "rc_on": "subj", "gap": "obj",  "rc_verb": "trans"},
    "F14": {"matrix": "trans", "scrambled": True,  "rc_on": "subj", "gap": "subj", "rc_verb": "intrans"},
}

GRAMMAR = Grammar(RULES, START, PRETERMINALS, FRAME_IDS)
