"""Zapanese / Zenglish lexicon. Data only.

Both languages share the same words; only the order differs. Sizes follow the
design decision of N transitive verbs, N intransitive verbs and 2N nouns, with the
two verb classes disjoint (required for unambiguity, checked by ``Lexicon``).

Case markers are one-word categories so that the grammar can treat them as
ordinary preterminals; change the surface form here (e.g. ``"ga"``/``"o"``) without
touching cfg.py.
"""

from grammar.grammar import Lexicon

N_VERBS = 13  # transitive = intransitive = N_VERBS ; nouns = 2 * N_VERBS

TRANSITIVE_VERBS = ("chases", "sees", "follows", "likes", "bites", "hears", "pushes",
                    "finds", "hugs", "kicks", "watches", "carries", "touches")
INTRANSITIVE_VERBS = ("swims", "dances", "sleeps", "runs", "jumps", "sits", "laughs",
                      "waits", "flies", "hides", "sings", "walks", "crawls")
# one animal per letter, A to Z
NOUNS = ("aardvark", "bird", "cat", "dog", "elephant", "fox", "goat", "horse", "iguana",
         "jaguar", "koala", "lion", "mouse", "newt", "owl", "pig", "quail", "rabbit",
         "snake", "tiger", "urchin", "vulture", "wolf", "xerus", "yak", "zebra")

assert len(TRANSITIVE_VERBS) == N_VERBS, "transitive verbs must number N_VERBS"
assert len(INTRANSITIVE_VERBS) == N_VERBS, "intransitive verbs must number N_VERBS"
assert len(NOUNS) == 2 * N_VERBS, "nouns must number 2 * N_VERBS"

LEXICON = Lexicon({
    "N": NOUNS,
    "V_t": TRANSITIVE_VERBS,
    "V_i": INTRANSITIVE_VERBS,
    "NOM": ("NOM",),
    "ACC": ("ACC",),
})
