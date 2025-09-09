# WFormat

Opinionated code formatter for C++ code.

## Availability

limit: only support Format Document in IDEs for now

### Visual Studio Code

- [x] win-x64
- [ ] win-arm64
- [x] macos
- [x] linux-64
- [ ] linux-arm64

### Visual Studio

- [x] win-x64
- [ ] win-arm64

### XCode

- [ ] macos

### Python Package Index(PyPI)

- [x] win-x64
- [ ] win-arm64
- [x] macos
- [ ] linux-64
- [ ] linux-arm64

## Tutorials

### Installation

#### Use Visual Studio Code Extension

Install ```wformat``` from extension market.

In any C++ file, Press ```ctrl + alt + P``` to bring up the command menu.

Type ```Format Document With...``` select ```Config Default Formatter...``` pick ```wformat```.

Next time you call ```Format Document```, vscode will use ```wformat```.

#### Use Visual Studio Extension

Install ```wformat``` from extension market.

By default, you can only click ```Run WFormat``` in your Right Click Menu to format on the file.

You can find ```wformat.General```(or search ```wformat```) in ```Tools > Options``` menu.

By change ```Override default formatter``` to ```True```, you can use Format Document(```ctrl + K```, ```ctrl + D```) with wformat instead.

#### Use as console app from ```Python Package Index (PyPI)```

Run ```pip install wformat```, then you can use ```wformat``` in your console.

### Usage

Run ```wformat -v``` to check your current version.

Run ```wformat``` or ```wformat -h``` to get the usage help doc.
Find developer friendly use examples under the ```tutorials:``` section.
