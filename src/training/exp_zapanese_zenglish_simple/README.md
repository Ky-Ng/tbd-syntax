# Experiment Setup - Zapanese Zenglish Simple OOD Generalization

## Research Question

1. What training pressures, data and architecture, allow the model to learn a hierarchical structure if any?

## Hypothesis
If a model can translate OOD frames where the (1) training data minimally requires using linear heuristics, then (2) the model has likely learned a hierarchical algorithm.

- Note: what may seem "easy" to humans may be different for language models, however we will make assumptions that linear "Reverse string" is easier than a hierarchical pattern say "building a complex variable binding/pointer system"

- Link to [results](RESULTS.md)

## Risks

1. Even if a model cannot generalize unseen frames does not guarantee that the model did not learn a hierarchical rule. 

2. Similarly, generalizing to unseen frames is a strong indicator but not guarantee of a hiearchical algorithm

3. The results from small models may not generalize to larger models

4. Using a `<copy>` token for unfamiliar frames may lead the model to memorize to only build a structure relevant for `copying`. However, this seems unlikely since the same structure should have to be built for translation of in-distribution frames as well. Note: we balance the number of copy and translate tasks in training for this reason.

## Methods

1. Architecture: Train toy GPT-2 models with the cartesian product of {2, 4, 8} Attention Heads and {2, 4, 6} Layers, embedding and unembedding matrix are not tied
2. Training Data
    a. Training: the model sees translation pairs from the train set in [kylelovesllms/zapanese_zenglish_simple-filled](https://huggingface.co/datasets/kylelovesllms/zapanese_zenglish_simple-filled), and copy of source Zapanese sentences from train, dev and the OOD `*_select` subsets (never `*_report`), with as many copy examples as translation examples
    b. Validation: withheld populated frames of the train set
    c. Test: Test is translation task on withheld frames which have the RC on the first noun but also allow Nominative case (object gap) and RCs on the second noun
3. Loss
    a. Training: Computed on every single token (i.e. not just on the target translation side) except the `<task>` position, which is arbitrary by construction and masked
    b. Eval: Loss is computed on the target translation side (note only translation tasks are in test)
4. Checkpoints
    a. Every 10,000 steps is a single checkpoint; evaluation and WandB logging every 1,000 steps
5. During training, logs from WandB should report validation and test loss both on raw token accuracy and complete string match
6. At each evaluation checkpoint, the model's greedily sampled outputs will be in the gitignored `artifacts/<run_slug>/decodes/` folder; at the final endpoint, an AI Agent will populate RESULTS.md with the checkpoint when the model has saturated the validation set and the errors the model makes (if any) on the test set using tables and a detailed analysis of each type of error and how often the error occurs

## Stimuli
- [kylelovesllms/zapanese_zenglish_simple-filled](https://huggingface.co/datasets/kylelovesllms/zapanese_zenglish_simple-filled)

## Specification

Everything below is what the `*.py` files in this folder will instantiate (object definitions:
[../DESIGN.md](../DESIGN.md)).

### Architecture grid

GPT-2, untied embedding and unembedding, 9 models = {2, 4, 6} layers x {2, 4, 8} heads.

| Field | Value |
|---|---|
| `d_model` | 256 |
| `d_mlp` | 1024 (4 x `d_model`) |
| `n_layer` | 2, 4, 6 |
| `n_head` | 2, 4, 8 (256 is not divisible by 6, so 6 was replaced by 8) |
| `dropout` | 0.0 |
| `tie_embeddings` | False |
| vocabulary | 26 nouns + 13 + 13 verbs + `NOM` `ACC` + 6 specials = 60 tokens |
| context | `max_len` = 20 |

### Optimisation

| Field | Value |
|---|---|
| `optimizer` | AdamW |
| `lr` | 1e-3 |
| `warmup_steps` | 1,000, linear |
| `lr_schedule` | constant after warmup |
| `weight_decay` | 0.0 |
| `batch_size` | 256 sequences |
| `total_steps` | 125,000 |
| `seq_len` | 20 (= `format.max_len`) |
| `examples_per_epoch` | 15,008 (7,504 translate + 7,504 copy) |
| `loss_segments` | `{SOURCE, SEP, OUTPUT, EOS}` (every token except the `<task>` position) |
| *derived* `tokens_per_step` | 256 x 20 = 5,120 (padding included) |
| *derived* `tokens_per_epoch` | 15,008 x 20 = 300,160 |
| *derived* `total_token_budget` | 125,000 x 5,120 = 640,000,000 |
| *derived* `epochs` | 125,000 x 256 / 15,008 = 2,132.2 |

### Data mixture

Translate pairs come from `train` only. Copy examples use the *source* Zapanese sentence
and are drawn from every subset **except** `*_report`. Copy and translate counts are equal
and copy is spread as evenly as possible over all 18 frames.

| subset | task | role | rows available |
|---|---|---|---|
| `train` | translate | TRAIN | 7,504 |
| `train` | copy | TRAIN | pool |
| `dev` | translate | SELECT | 834 |
| `dev` | copy | TRAIN | pool |
| `ood_level1_select` | translate | SELECT | 1,500 |
| `ood_level1_select` | copy | TRAIN | pool |
| `ood_level2_select` | translate | SELECT | 3,000 |
| `ood_level2_select` | copy | TRAIN | pool |
| `ood_level1_report` | translate | REPORT | 1,500 |
| `ood_level2_report` | translate | REPORT | 3,000 |

Copy budget, computed from the CSVs:

| | |
|---|---|
| translate examples | 7,504 |
| copy examples | 7,504 (matched) |
| even share per frame | 7,504 / 18 = 416.9 |
| copy pool per train frame | 1,000 (`train` + `dev` sources); F11 only 338 |
| copy pool per OOD frame | 500 (`*_select` sources) |
| water-fill result | F11: 338; the other 17 frames: 421 or 422 each |

Sampling is without replacement with the **data seed**, so all 36 runs see the identical
dataset. `Role.SELECT` subsets may inform checkpoint choice. `Role.REPORT` subsets are
evaluated at every eval but never consulted for a decision, and never seen as copy.

### Sequence format

`<bos> SOURCE <sep> <task> OUTPUT <eos>` padded to 20. The task token comes *after* the source
so the model must parse the sentence before it knows the task (an extra training pressure).

Consequences:

1. **The `<task>` position is masked out of the training loss.** The same source is followed
   by either task token, so that position is arbitrary by construction and scoring it would
   only add a constant floor. The model still receives the task token as input.
2. **Predicting `<sep>` is a real signal**: the model must know the source string is complete.
   Its per-token loss is not expected to reach 0, because three train frames are proper prefixes
   of three level-2 frames (F01/F04, F02/F09, F11/F13: a finished-looking clause can continue as
   a relative clause) and the level-2 sources appear as copy examples. This ambiguity is a
   feature of head-final grammar, not a bug.
3. **Loss is logged per segment** (`source`, `sep`, `task`, `output`, `eos`) so that the
   source segment's large, unavoidable loss (source words are sampled uniformly) never hides
   convergence of the output.
4. **Eval prompts** are `<bos> SOURCE <sep> <task>`, greedily decoded until `<eos>`.

### Evaluation and checkpoints

| | Value |
|---|---|
| metrics | token accuracy, exact match, per-segment loss |
| eval loss | the `output` segment only (translate task), per the Methods above; training loss scores every segment except `<task>` |
| keyed by | `(step, subset, task, frame_id)` so RESULTS.md's per-frame error analysis is a group-by, not a second pass |
| eval + wandb log every | 1,000 steps |
| checkpoint to disk every | 10,000 steps (13 checkpoints per run incl. final) |
| greedy decodes | written per eval as `artifacts/<slug>/decodes/step<N>.csv` |

### Run order and the cluster

36 runs = 9 models x 4 seeds (42, 43, 44, 45). `Experiment.runs()` is **seed-major**: indices
0-8 are seed 42 across all nine architectures, 9-17 are seed 43, and so on, so the first
nine jobs already give one reading per architecture.

```
uv sync --extra train                                     # torch, transformers, wandb
uv run python src/training/exp_zapanese_zenglish_simple/run.py list        # index -> slug
sbatch --array=0-35 slurm/run_array.sbatch \
    src/training/exp_zapanese_zenglish_simple/run.py train --index $SLURM_ARRAY_TASK_ID
```

### Wandb

| | |
|---|---|
| project | `zapanese_zenglish_simple-125000` |
| group | model slug, e.g. `gpt2-2l4h256d` |
| job_type | `seed42` ... `seed45` |
| run name | `gpt2-2l4h256d-s42` |
| config | full `run_config.json` plus its path, so the UI can group by `n_head`, `n_layer`, `seed` in any combination |

### Artifacts

```
src/training/exp_zapanese_zenglish_simple/artifacts/<slug>/
    run_config.json
    checkpoints/step010000/  ...  step125000/     HF save_pretrained directories
    decodes/step001000.csv  ...
    metrics.csv
```

Roughly 20 MB per checkpoint, 13 per run, 36 runs: about 9.5 GB, gitignored, staged here
before upload to the `translation-syntax-exp_zapanese_zenglish_simple-125000` collection.

---


## Model table

Shared: `d_model` 256, `d_ff` 1024, AdamW lr 1e-3 (1,000-step warmup, constant, no weight
decay), batch 256, 125K steps, 5,120 tokens/step, 300,160 tokens/epoch, 640 M token budget.

| Model Name | layers | n_heads | d_model | lr | dropout | steps | tokens/step | total token budget |
|---|---|---|---|---|---|---|---|---|
| gpt2-2l2h256d | 2 | 2 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-2l4h256d | 2 | 4 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-2l8h256d | 2 | 8 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-4l2h256d | 4 | 2 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-4l4h256d | 4 | 4 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-4l8h256d | 4 | 8 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-6l2h256d | 6 | 2 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-6l4h256d | 6 | 4 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
| gpt2-6l8h256d | 6 | 8 | 256 | 1e-3 | 0.0 | 125,000 | 5,120 | 640 M |
