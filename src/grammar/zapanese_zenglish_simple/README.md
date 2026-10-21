# Experiment Setup - Zapanese --> Zenglish CFG Simple

## Research Question
1. [RQ1](../../../README.md) "Do LLMs use hierarchical representations?"

## Hypothesis
Behavioral Analysis: If a model can translate OOD frames where the (1) training data minimally requires using linear heuristics, then (2) the model has likely learned a hierarchical algorithm.

- Note: what may seem "easy" to humans may be different for language models, however we will make assumptions that linear "Reverse string" is easier than a hierarchical pattern say "building a complex variable binding/pointer system"

- Link to [results](RESULTS.md)

## Risks

1. Even if a model cannot generalize unseen frames does not guarantee that the model did not learn a hierarchical rule. 

2. Similarly, generalizing to unseen frames is a strong indicator but not guarantee of a hiearchical algorithm

3. The resutls from small models may not generalize to larger models

## Methods

1. Use a CFG to generate the distribution of Zapanese sentences with a single relative clause that allow for scrambling

2. Each Zapanese rule corresponds to a Zenglish rule. For a CFG written in Chomsky Normal Form, an example of the Zapanese rule being `VP -> NP V` would be `VP -> V NP`. 

### Deliverable
1. Six CSC files detailed in Stimuli

## Stimuli

An example of each stimuli is in [Japanese RC Stimuli - RC Frames with Stimuli.csv](stimuli_examples/Japanese%20RC%20Stimuli%20-%20RC%20Frames%20with%20Stimuli.csv) with the filled in frames with Dog always used as Subject, Cat used as Object, Bird as the embedded noun, chases or swims as the matrix verb, sees and swims as the embedded verb.

<small>The following description of the data is written by AI describing a handwritten description of the split</small>

Tokens are `dog` `NOM`, i.e. the noun and its case marker are separate tokens. Brackets `[ ]`, the gap `__`, and `(that)` in the tables below are reading aids only and never appear in the data.

### Frame-level split

Frames are the unit of generalization. Every one of the 18 frames belongs to exactly one split (enforced by `splits.py`).

- **train**: no RC, or an RC on the *first* noun with a *subject* gap. The embedded noun is always ACC, so a linear heuristic suffices: the noun directly before the matrix verb picks the algorithm (scrambled vs. unscrambled) and the RC translates by reversing `noun case` chunks.
- **ood_level1**: RC still on the first noun, but with an *object* gap. Chunk reversal now gives the wrong RC order, and the model sees two NOM nouns in one sentence for the first time.
- **ood_level2**: RC on the *second* noun. The noun before the matrix verb no longer identifies the algorithm.

| Split | Frame | Zapanese frame | Zenglish frame | Scrambled | RC on | Gap | Same Zenglish as |
|---|---|---|---|---|---|---|---|
| train | F11 | SUBJ NOM VERB | SUBJ NOM VERB | n/a | none | n/a | |
| train | F01 | SUBJ NOM OBJ ACC VERB | SUBJ NOM VERB OBJ ACC | no | none | n/a | F02 |
| train | F02 | OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC | yes | none | n/a | F01 |
| train | F03 | [__ RC-OBJ ACC RC-VERB] SUBJ NOM OBJ ACC VERB | SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB OBJ ACC | no | subject | subject | F07 (L2) |
| train | F12 | [__ RC-VERB] SUBJ NOM OBJ ACC VERB | SUBJ NOM [__ RC-VERB] VERB OBJ ACC | no | subject | subject | F14 (L2) |
| train | F16 | [__ RC-OBJ ACC RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB | n/a | subject | subject | |
| train | F18 | [__ RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB] VERB | n/a | subject | subject | |
| train | F08 | [__ RC-OBJ ACC RC-VERB] OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB RC-OBJ ACC] | yes | object | subject | F04 (L2) |
| train | F15 | [__ RC-VERB] OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB] | yes | object | subject | F13 (L2) |
| ood_level1 | F10 | [RC-SUBJ NOM __ RC-VERB] OBJ ACC SUBJ NOM VERB | SUBJ NOM VERB OBJ ACC [RC-SUBJ NOM RC-VERB __] | yes | object | object | F06 (L2) |
| ood_level1 | F05 | [RC-SUBJ NOM __ RC-VERB] SUBJ NOM OBJ ACC VERB | SUBJ NOM [RC-SUBJ NOM RC-VERB __] VERB OBJ ACC | no | subject | object | F09 (L2) |
| ood_level1 | F17 | [RC-SUBJ NOM __ RC-VERB] SUBJ NOM VERB | SUBJ NOM [RC-SUBJ NOM RC-VERB __] VERB | n/a | subject | object | |
| ood_level2 | F04 | SUBJ NOM [__ RC-OBJ ACC RC-VERB] OBJ ACC VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB RC-OBJ ACC] | no | object | subject | F08 (train) |
| ood_level2 | F13 | SUBJ NOM [__ RC-VERB] OBJ ACC VERB | SUBJ NOM VERB OBJ ACC [__ RC-VERB] | no | object | subject | F15 (train) |
| ood_level2 | F06 | SUBJ NOM [RC-SUBJ NOM __ RC-VERB] OBJ ACC VERB | SUBJ NOM VERB OBJ ACC [RC-SUBJ NOM RC-VERB __] | no | object | object | F10 (L1) |
| ood_level2 | F07 | OBJ ACC [__ RC-OBJ ACC RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB RC-OBJ ACC] VERB OBJ ACC | yes | subject | subject | F03 (train) |
| ood_level2 | F09 | OBJ ACC [RC-SUBJ NOM __ RC-VERB] SUBJ NOM VERB | SUBJ NOM [RC-SUBJ NOM RC-VERB __] VERB OBJ ACC | yes | subject | object | F05 (L1) |
| ood_level2 | F14 | OBJ ACC [__ RC-VERB] SUBJ NOM VERB | SUBJ NOM [__ RC-VERB] VERB OBJ ACC | yes | subject | subject | F12 (train) |

The last column lists Zapanese frames that translate to the *same* Zenglish frame. Four train frames (F03, F12, F08, F15) have an out-of-distribution twin, which is what makes comparing their internal representations possible.

### Filling-level split

Within each frame, `REPEAT` filled sentences are sampled without replacement from the lexicon (same noun may fill several slots, e.g. `dog NOM dog ACC chases`), then divided into disjoint subsets with a fixed seed. Frames are never split between subsets; only sentences are. This removes filling-level noise from checkpoint selection without changing the frame-level question.

| Frame split | Filling subset | Purpose |
|---|---|---|
| train | train | gradient updates |
| train | dev | early stopping and in-distribution checkpoint selection |
| ood_level1 | select | choosing which checkpoints to analyze mechanistically |
| ood_level1 | report | the Level 1 accuracy that is reported |
| ood_level2 | select | as above |
| ood_level2 | report | the Level 2 accuracy that is reported |

Accuracy is reported per frame, not only per split, so partial generalization (e.g. F10 but not F17) is visible. A checkpoint is never selected on the fillings it is reported on.
