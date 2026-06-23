from __future__ import annotations

import tomllib
import zipfile
from pathlib import Path


def test_sentence_transformers_is_runtime_dependency() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    assert any(item.startswith("sentence-transformers") for item in dependencies)


def test_built_wheel_metadata_requires_sentence_transformers() -> None:
    wheel_dir = Path(".tmp/packaging_check")
    wheels = sorted(wheel_dir.glob("membrain-*.whl"))
    if not wheels:
        return
    with zipfile.ZipFile(wheels[-1]) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
    assert "Requires-Dist: sentence-transformers" in metadata
    assert 'extra == "local-embedding"' not in metadata


def test_docs_do_not_advertise_embedding_fallback() -> None:
    checked_files = [
        Path("README.md"),
        Path("INTEGRATION.md"),
        Path("pi-extension/mb-memory.ts"),
    ]
    forbidden_phrases = [
        "sentence-transformers` 可选",
        "不装也能用关键词检索",
        "关键词检索）",
        "local-embedding",
        "full features",
        "向量后端升级",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in checked_files)
    for phrase in forbidden_phrases:
        assert phrase not in combined
