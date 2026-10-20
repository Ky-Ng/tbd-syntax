"""Toy synchronous CFG: 5 frames, one scrambled rule, one subject-gap RC on the object."""

from grammar.grammar import Grammar, Rule

PRETERMINALS = frozenset({"N", "NOM", "ACC", "V_t", "V_i"})

RULES = (
    Rule("S_i", "S", ("NP_nom", "V_i"), (0, 1), {"matrix": "intrans"}),
    Rule("S_t", "S", ("NP_nom", "NP_acc", "V_t"), (0, 2, 1), {"matrix": "trans", "scrambled": False}),
    Rule("S_t_scr", "S", ("NP_acc", "NP_nom", "V_t"), (1, 2, 0), {"matrix": "trans", "scrambled": True}),
    Rule("NP_nom", "NP_nom", ("N", "NOM"), (0, 1)),
    Rule("NP_acc_bare", "NP_acc", ("N", "ACC"), (0, 1), {"rc_on": "none"}),
    Rule("NP_acc_rc", "NP_acc", ("RC", "N", "ACC"), (1, 2, 0), {"rc_on": "obj"}),
    Rule("RC_subj_gap", "RC", ("N", "ACC", "V_t"), (2, 0, 1), {"gap": "subj"}),
)

FRAME_IDS = {
    "T1": {"matrix": "intrans"},
    "T2": {"matrix": "trans", "scrambled": False, "rc_on": "none"},
    "T3": {"matrix": "trans", "scrambled": False, "rc_on": "obj"},
    "T4": {"matrix": "trans", "scrambled": True, "rc_on": "none"},
    "T5": {"matrix": "trans", "scrambled": True, "rc_on": "obj"},
}

GRAMMAR = Grammar(RULES, "S", PRETERMINALS, FRAME_IDS)
