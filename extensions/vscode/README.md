# wformat VS Code Extension

This extension integrates the **`wformat`** code formatter into VS Code for C and C++ files.  
It runs an embedded `wformat` executable as a background daemon and communicates via JSON over stdin/stdout.

## Features

- Formats **C / C++** files on demand (via `Format Document`).
- Runs a persistent **`wformat` daemon** for fast repeated requests.
- Supports **cancellation** of in-progress formatting (e.g., if VS Code cancels the request).
- Handles errors gracefully and shows logs in the `wformat` output channel.

## Installation

1. Build the formatter (`wformat`) by calling ```pyinstaller -y --clean wformat.spec```

2. Package the VS Code extension (`vsce package`) and install it.

3. Open any C or C++ file in VS Code and use **Format Document** (`Shift+Alt+F` / `⌥⇧F`).

## Development

- Entry point: [`vscode.ts`](./extensions/vscode/vscode.ts)  
- Daemon management: `startDaemon()`  
- Formatting requests: `requestFormat()` → `format()`  
- Builds with standard VS Code extension tooling.
- Press ```F5``` in vscode to test

## License

MIT
