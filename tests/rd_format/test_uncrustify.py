from rd_format.uncrustify import Uncrustify


def test_sanity():
    formatter = Uncrustify()
    assert formatter is not None
