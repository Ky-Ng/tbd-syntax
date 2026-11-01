# Training Runs

One row per training experiment. Package design: [DESIGN.md](DESIGN.md).

| Experiment Name | Model(s) | Dataset(s) | Hypothesis | Results | Follow Up |
|---|---|---|---|---|---|
| [exp_zapanese_zenglish_simple](exp_zapanese_zenglish_simple/README.md) | GPT-2, {2, 4, 6} layers x {2, 4, 8} heads, d_model 256, 4 seeds, 125K steps | [zapanese_zenglish_simple-filled](https://huggingface.co/datasets/kylelovesllms/zapanese_zenglish_simple-filled) | OOD frame generalisation implies a hierarchical translation algorithm | [RESULTS.md](exp_zapanese_zenglish_simple/RESULTS.md) | |
