from pathlib import Path


def test_packaging_files_exist():
    assert Path("H:/代码/胶片日期水印/build.ps1").exists()
    assert Path("H:/代码/胶片日期水印/README.md").exists()
