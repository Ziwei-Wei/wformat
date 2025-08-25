import pytest

from wformat.cli_app import cli_app
from wformat.wformat import WFormat


def test_wformat():
    formatter = WFormat()
    assert formatter is not None
    assert formatter.clang_format is not None
    assert formatter.uncrustify is not None


def test_cli(capsys):
    with pytest.raises(SystemExit) as e:
        cli_app(["-h"])
    if e.value.code != 0:
        print(capsys.readouterr().out)
    assert e.value.code == 0
