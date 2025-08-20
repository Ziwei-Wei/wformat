import pytest

from rd_format.cli_app import cli_app


def test_sanity():
    with pytest.raises(SystemExit) as e:
        cli_app(["-h"])
    assert e.value.code == 0
