"""Push a generated dataset folder to the HuggingFace Hub and file it in a collection.

Authentication uses ``huggingface_hub``'s defaults (the ``HF_TOKEN`` environment
variable or a prior ``huggingface-cli login``). The token is never read, logged or
printed by this module.

Naming convention (see CLAUDE.md), with ``<exp>`` the experiment folder name::

    repo_id     kylelovesllms/<exp>-frames    kylelovesllms/<exp>-filled
    collection  translation-syntax-datasets-<exp>
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class _HubApi(Protocol):
    """The subset of ``huggingface_hub.HfApi`` this module uses (for test doubles)."""

    def create_repo(self, repo_id: str, *, repo_type: str, private: bool, exist_ok: bool) -> Any: ...
    def upload_folder(self, *, folder_path: str, repo_id: str, repo_type: str, allow_patterns: list[str]) -> Any: ...
    def upload_file(self, *, path_or_fileobj: str, path_in_repo: str, repo_id: str, repo_type: str) -> Any: ...
    def create_collection(self, title: str, *, namespace: str, exists_ok: bool) -> Any: ...
    def add_collection_item(self, collection_slug: str, *, item_id: str, item_type: str, exists_ok: bool) -> Any: ...


def upload_dataset(
    local_dir: Path,
    repo_id: str,
    readme_path: Path,
    collection_title: str,
    private: bool = False,
    api: _HubApi | None = None,
) -> str:
    """Upload every ``*.csv`` under ``local_dir`` as a dataset repo and add it to a collection.

    Steps: create the repo if missing, upload the CSVs (directory structure kept),
    upload ``readme_path`` as the dataset card ``README.md``, create the collection
    if missing, add the repo to it.

    Parameters
    ----------
    local_dir : Path
        Folder produced by ``grammar.generate_frames.generate`` (or one of its
        subfolders, e.g. ``filled/``).
    repo_id : str
        ``"<namespace>/<name>"``, e.g. ``"kylelovesllms/zapanese_zenglish_simple-filled"``.
    readme_path : Path
        Markdown dataset card, e.g. ``hugging_face_frame_descriptions/Filled.md``.
    collection_title : str
        Collection title; created under the repo's namespace if it does not exist.
    private : bool, optional
        Datasets are public by default (project policy).
    api : HfApi-like, optional
        Injected for tests; defaults to ``huggingface_hub.HfApi()``.

    Returns
    -------
    url : str
        ``https://huggingface.co/datasets/<repo_id>``.

    Examples
    --------
    >>> upload_dataset(Path("data/zapanese_zenglish_simple/filled"),
    ...                "kylelovesllms/zapanese_zenglish_simple-filled",
    ...                Path("src/grammar/zapanese_zenglish_simple/hugging_face_frame_descriptions/Filled.md"),
    ...                "translation-syntax-datasets-zapanese_zenglish_simple")  # doctest: +SKIP
    'https://huggingface.co/datasets/kylelovesllms/zapanese_zenglish_simple-filled'
    """
    local_dir = Path(local_dir)
    readme_path = Path(readme_path)
    if not local_dir.is_dir():
        raise FileNotFoundError(f"{local_dir} is not a directory")
    if not any(local_dir.rglob("*.csv")):
        raise FileNotFoundError(f"no .csv files under {local_dir}")
    if not readme_path.is_file():
        raise FileNotFoundError(f"README not found: {readme_path}")
    if "/" not in repo_id:
        raise ValueError(f"repo_id must be '<namespace>/<name>', got {repo_id!r}")

    if api is None:
        from huggingface_hub import HfApi

        api = HfApi()

    namespace = repo_id.split("/", 1)[0]
    api.create_repo(repo_id, repo_type="dataset", private=private, exist_ok=True)
    api.upload_folder(folder_path=str(local_dir), repo_id=repo_id, repo_type="dataset",
                      allow_patterns=["*.csv", "**/*.csv"])
    api.upload_file(path_or_fileobj=str(readme_path), path_in_repo="README.md",
                    repo_id=repo_id, repo_type="dataset")
    collection = api.create_collection(collection_title, namespace=namespace, exists_ok=True)
    api.add_collection_item(collection.slug, item_id=repo_id, item_type="dataset", exists_ok=True)
    return f"https://huggingface.co/datasets/{repo_id}"


def upload_model(*args: Any, **kwargs: Any) -> str:
    """Upload a model checkpoint folder. Not implemented until the first training experiment.

    Raises
    ------
    NotImplementedError
    """
    raise NotImplementedError("upload_model is implemented with the first training experiment")
