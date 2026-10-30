"""Zapanese -> Zenglish grammar: cfg.py, lexicon.py, splits.py are the source of truth.

The HuggingFace names below are the one place they are written; ``run.py`` (upload) and
``training.exp_zapanese_zenglish_simple`` (download) both import them.
"""

EXPERIMENT = "zapanese_zenglish_simple"
HF_USER = "kylelovesllms"
HF_FRAMES_REPO = f"{HF_USER}/{EXPERIMENT}-frames"
HF_FILLED_REPO = f"{HF_USER}/{EXPERIMENT}-filled"
COLLECTION = f"translation-syntax-datasets-{EXPERIMENT}"
