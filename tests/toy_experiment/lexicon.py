"""Toy lexicon."""

from grammar.grammar import Lexicon

LEXICON = Lexicon({
    "N": ("dog", "cat"),
    "V_t": ("chases", "sees"),
    "V_i": ("swims",),
    "NOM": ("NOM",),
    "ACC": ("ACC",),
})
