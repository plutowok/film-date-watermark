from pathlib import Path

from PIL import Image

from core.batch_processor import collect_jpegs, ensure_output_path


def test_collect_jpegs_recurses(tmp_path: Path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    Image.new("RGB", (10, 10), (1, 2, 3)).save(nested / "photo.jpg", format="JPEG")

    paths = collect_jpegs(tmp_path)

    assert [path.name for path in paths] == ["photo.jpg"]


def test_output_path_preserves_relative_structure(tmp_path: Path):
    root = tmp_path / "root"
    source = root / "x" / "y" / "photo.jpg"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"demo")

    target = ensure_output_path(root, source, "dated_output")

    assert target == root / "dated_output" / "x" / "y" / "photo.jpg"
