from rd_format.clang_format import ClangFormat


def test_sanity():
    formatter = ClangFormat()
    assert formatter is not None
