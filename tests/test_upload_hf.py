from pathlib import Path
from types import SimpleNamespace

import pytest

from upload.upload_hf import upload_dataset, upload_model


class FakeApi:
    def __init__(self):
        self.calls = []

    def _rec(self, name):
        def f(*a, **k):
            self.calls.append((name, a, k))
            return SimpleNamespace(slug="ns/my-collection-abc123")
        return f

    def __getattr__(self, name):
        return self._rec(name)


def test_upload_dataset_call_sequence(tmp_path):
    (tmp_path / "filled").mkdir()
    (tmp_path / "filled" / "train.csv").write_text("a,b\n")
    readme = tmp_path / "README.md"
    readme.write_text("# card\n")
    api = FakeApi()
    url = upload_dataset(tmp_path, "ns/exp-filled", readme, "my collection", api=api)
    assert url == "https://huggingface.co/datasets/ns/exp-filled"
    names = [c[0] for c in api.calls]
    assert names == ["create_repo", "upload_folder", "upload_file", "create_collection", "add_collection_item"]
    assert api.calls[0][2] == {"repo_type": "dataset", "private": False, "exist_ok": True}
    assert api.calls[1][2]["allow_patterns"] == ["*.csv", "**/*.csv"]
    assert api.calls[3][1] == ("my collection",) and api.calls[3][2]["namespace"] == "ns"
    assert api.calls[4][1] == ("ns/my-collection-abc123",) and api.calls[4][2]["item_id"] == "ns/exp-filled"


def test_upload_dataset_requires_csv_and_readme(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("x")
    with pytest.raises(FileNotFoundError, match="no files matching"):
        upload_dataset(tmp_path, "ns/x", readme, "c", api=FakeApi())
    (tmp_path / "a.csv").write_text("a\n")
    with pytest.raises(FileNotFoundError, match="README"):
        upload_dataset(tmp_path, "ns/x", tmp_path / "missing.md", "c", api=FakeApi())
    with pytest.raises(ValueError, match="namespace"):
        upload_dataset(tmp_path, "nonamespace", readme, "c", api=FakeApi())


def test_upload_model_is_stub():
    with pytest.raises(NotImplementedError):
        upload_model()


def test_upload_dataset_custom_patterns(tmp_path):
    (tmp_path / "frames.csv").write_text("a\n")
    (tmp_path / "filled").mkdir()
    (tmp_path / "filled" / "train.csv").write_text("a\n")
    readme = tmp_path / "README.md"
    readme.write_text("x")
    api = FakeApi()
    upload_dataset(tmp_path, "ns/x-frames", readme, "c", api=api, patterns=["frames.csv"])
    assert api.calls[1][2]["allow_patterns"] == ["frames.csv"]
