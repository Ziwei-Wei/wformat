import subprocess, sys
from wformat.wformat import WFormat

def run_wformat_stdin(inp: str):
    # Run module entry point so it uses current source tree
    proc = subprocess.run(
        [sys.executable, "-m", "wformat", "--stdin"],
        input=inp,
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr

def test_stdin_matches_memory():
    source = "#include <vector>\nint   main( ) {  return  0 ; }\n"
    expected = WFormat().format_memory(source)
    rc, out, err = run_wformat_stdin(source)
    assert rc == 0, f"Non-zero exit (stderr={err!r})"
    assert out == expected

def test_stdin_empty_ok():
    rc, out, err = run_wformat_stdin("")
    assert rc == 0
    assert out == ""

def test_stdin_idempotent():
    source = "#include <vector>\nint main(){return 0;}\n"
    rc, out1, _ = run_wformat_stdin(source)
    rc, out2, _ = run_wformat_stdin(out1)
    assert out1 == out2