from __future__ import annotations

from pathlib import Path

import pytest

MARKER = "### RECORD "


def make_record(i: int, body: str = "some payload line") -> bytes:
    return f"{MARKER}{i}\r\nplayer: Alice\r\n{body}\r\n\r\n".encode()


def write_dataset(root: Path, spec: dict[str, dict[str, int]]) -> int:
    """Create a dataset tree: {folder: {filename: record_count}}. Returns total records."""
    total = 0
    counter = 0
    for folder, files in spec.items():
        for name, n in files.items():
            path = root / folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"".join(make_record(counter + i) for i in range(n)))
            counter += n
            total += n
    return total


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    write_dataset(root, {
        "alpha": {"a1.txt": 10, "a2.txt": 3, "a3.txt": 1},
        "beta": {"b1.txt": 25, "b2.txt": 0},
    })
    return root
