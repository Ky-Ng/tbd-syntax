---
pretty_name: Zapanese to Zenglish (syntactic frames)
language:
- en
tags:
- synthetic
- syntax
- translation
- context-free-grammar
- relative-clauses
- scrambling
task_categories:
- translation
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: frames
    path: frames.csv
---

# Zapanese to Zenglish: syntactic frames

The 18 unfilled sentence frames behind the
[filled dataset](https://huggingface.co/datasets/kylelovesllms/zapanese_zenglish_simple-filled).
A frame is a sentence with its words replaced by part-of-speech slots: a Zapanese
(head-final, Japanese word order) slot sequence, its Zenglish (head-initial)
counterpart, and the word alignment between them.

- **Zapanese**: verb last, relative clause before the noun it modifies, explicit case
  markers. The object may be *scrambled* in front of the subject.
- **Zenglish**: subject, verb, object; relative clause after its noun. Scrambling is
  neutralised, so several Zapanese frames map to one Zenglish frame.

The frames are enumerated exhaustively from a 15-rule synchronous context-free
grammar in [Ky-Ng/tbd-syntax](https://github.com/Ky-Ng/tbd-syntax)
(`src/grammar/zapanese_zenglish_simple/cfg.py`). Every sentence has exactly one
relative clause at most, every relative clause has exactly one gap, and no two frames
share a Zapanese slot sequence, so translation is a function.

## Slot symbols

| Symbol | Meaning | Filled by |
|---|---|---|
| `N` | noun | 26 animal nouns |
| `NOM` | nominative case marker | the token `NOM` |
| `ACC` | accusative case marker | the token `ACC` |
| `V_t` | transitive verb | 13 verbs |
| `V_i` | intransitive verb | 13 verbs |

## Columns

| Column | Type | Meaning |
|---|---|---|
| `frame_id` | string | `F01` … `F18`, matching the research stimuli spreadsheet. |
| `split` | string | `train`, `ood_level1` or `ood_level2` (see the filled dataset for what each tests). |
| `source_frame` | string | Zapanese slot sequence, space-separated. |
| `target_frame` | string | Zenglish slot sequence, space-separated. |
| `alignment` | string | Space-separated integers; entry *j* is the index of the source slot that target position *j* copies. Filling the source and copying through the alignment yields the target. |
| `derivation` | string | Names of the grammar rules applied, in preorder. |
| `matrix` | string | Matrix verb: `trans` or `intrans`. |
| `scrambled` | string | `True` / `False`; empty for intransitive frames (nothing to scramble). |
| `rc_on` | string | Which argument carries the relative clause: `subj`, `obj` or `none`. |
| `gap` | string | Gap inside the relative clause: `subj` or `obj`; empty if no relative clause. |
| `rc_verb` | string | Verb inside the relative clause: `trans` or `intrans`; empty if no relative clause. |

Example row (F03):

```
source_frame  N ACC V_t N NOM N ACC V_t
target_frame  N NOM V_t N ACC V_t N ACC
alignment     3 4 2 0 1 7 5 6
derivation    S_trans_rcS NP_nom_rc RC_subj_gap NP_acc
```

Reading the alignment: target position 0 (`N`) is source slot 3, the subject noun;
target position 2 (`V_t`) is source slot 2, the relative-clause verb, which moves from
before the subject noun in Zapanese to after it in Zenglish.

## The 18 frames

`SUBJ`/`OBJ`/`RC-SUBJ`/`RC-OBJ` are all `N` in the data, `VERB`/`RC-VERB` are `V_t` or
`V_i`. `[...]` marks the relative clause and `__` its gap; neither appears in the data.

| Split | Frame | Zapanese | Zenglish | Scrambled | RC on | Gap | RC verb |
|---|---|---|---|---|---|---|---|
| train | F11 | SUBJ NOM VERB | SUBJ NOM VERB | | none | | |
| train | F01 | SUBJ NOM OBJ ACC VERB | SUBJ NOM VERB OBJ ACC | no | none | | |
| train | F02 | OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC | yes | none | | |
| train | F03 | [__ RC-OBJ ACC RC-VERB] SUBJ NOM OBJ ACC VERB | SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB OBJ ACC | no | subj | subj | trans |
| train | F12 | [__ RC-VERB] SUBJ NOM OBJ ACC VERB | SUBJ NOM [__ RC-VERB] VERB OBJ ACC | no | subj | subj | intrans |
| train | F16 | [__ RC-OBJ ACC RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB | | subj | subj | trans |
| train | F18 | [__ RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB] VERB | | subj | subj | intrans |
| train | F08 | [__ RC-OBJ ACC RC-VERB] OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB RC-OBJ ACC] | yes | obj | subj | trans |
| train | F15 | [__ RC-VERB] OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB] | yes | obj | subj | intrans |
| ood_level1 | F10 | [RC-SUBJ NOM __ RC-VERB] OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC [RC-SUBJ NOM RC-VERB __] | yes | obj | obj | trans |
| ood_level1 | F05 | [RC-SUBJ NOM __ RC-VERB] SUBJ NOM OBJ ACC VERB | SUBJ NOM [RC-SUBJ NOM RC-VERB __] VERB OBJ ACC | no | subj | obj | trans |
| ood_level1 | F17 | [RC-SUBJ NOM __ RC-VERB] SUBJ NOM VERB | SUBJ NOM [RC-SUBJ NOM RC-VERB __] VERB | | subj | obj | trans |
| ood_level2 | F04 | SUBJ NOM [__ RC-OBJ ACC RC-VERB] OBJ ACC VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB RC-OBJ ACC] | no | obj | subj | trans |
| ood_level2 | F13 | SUBJ NOM [__ RC-VERB] OBJ ACC VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB] | no | obj | subj | intrans |
| ood_level2 | F06 | SUBJ NOM [RC-SUBJ NOM __ RC-VERB] OBJ ACC VERB | SUBJ NOM VERB OBJ ACC [RC-SUBJ NOM RC-VERB __] | no | obj | obj | trans |
| ood_level2 | F07 | OBJ ACC [__ RC-OBJ ACC RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB OBJ ACC | yes | subj | subj | trans |
| ood_level2 | F09 | OBJ ACC [RC-SUBJ NOM __ RC-VERB] SUBJ NOM VERB | SUBJ NOM [RC-SUBJ NOM RC-VERB __] VERB OBJ ACC | yes | subj | obj | trans |
| ood_level2 | F14 | OBJ ACC [__ RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB] VERB OBJ ACC | yes | subj | subj | intrans |

Zapanese frames that share a Zenglish frame: F01/F02, F03/F07, F12/F14, F08/F04,
F15/F13, F05/F09, F10/F06.

## Loading

```python
from datasets import load_dataset

frames = load_dataset("kylelovesllms/zapanese_zenglish_simple-frames")["frames"]
by_id = {row["frame_id"]: row for row in frames}
by_id["F03"]["alignment"]   # '3 4 2 0 1 7 5 6'
```
