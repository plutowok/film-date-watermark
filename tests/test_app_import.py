import importlib


def test_app_module_importable():
    module = importlib.import_module("app")
    assert module is not None
