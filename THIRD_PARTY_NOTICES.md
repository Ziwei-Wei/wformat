# Third-Party Notices

This extension bundles / relies on third-party software. Their licenses and notices are reproduced below.

## LLVM / clang-format

- **Project:**  LLVM / clang-format
- **License:**  Apache License 2.0 with LLVM exceptions
- **Source:**   <https://llvm.org/>
- **Files:**    `dist/wformat/bin/clang-format(.exe)`
- **License**   `licenses/clang-format/LICENSE`.

## Uncrustify

- **Project:**  Uncrustify
- **License:**  GPL-2.0-or-later
- **Source:**   <https://github.com/uncrustify/uncrustify>
- **Files:**    `dist/wformat/bin/uncrustify(.exe)`
- **License**   `licenses/uncrustify/COPYING`.

## Satisfy new tests

### [Task] make all tests pass

### [Task.Fallback] if that is impossible to do, show me the reason why

### [Task.Expectation] try as many combination as possible, then comeback with your best effort

### [Test] try run ```pytest```

### [Test.CurrentStatus] tests under tests/sample/new is not passing

### [Test.Expecting] all tests pass

### [Hint]

you should alter the tests results by changing the following 2 files:
src\wformat\data\.clang-format
src\wformat\data\uncrustify.cfg
