# RdFormatVS (Visual Studio Extension)

A Visual Studio 2022 extension that formats C/C++ files using the `rd-format` daemon (`--serve`)—the same protocol used by your VS Code extension.

## Features

- Context menu command: **Format with rd-format**
- Optional **Format on Save**
- Uses an embedded or user-provided `rd-format` binary
- Simple JSON Lines protocol: `{"id", "op":"format", "text"}`

## Prerequisites

- **Visual Studio 2022** (17.x) with **Visual Studio extension development** workload
- .NET Framework targeting pack for **.NET 4.7.2** (installed with VS workload)
- Your `rd-format` binary for Windows (e.g., `rd-format.exe`)

## Getting Started (Debug / F5)

1. Open the `RdFormatVS.csproj` in Visual Studio 2022.
2. Build once to restore packages.
3. Ensure the daemon can be found by the extension:
   - **Option A (env var):** set `RD_FORMAT_PATH` (User or System) to the full path of your `rd-format.exe`.
   - **Option B (embedded):** place `rd-format.exe` at  
     `$(TargetDir)\dist\rd-format\win-x64\rd-format.exe`  
     (i.e., next to the built `RdFormatVS.dll` in the experimental instance folder).  
     You can also copy it manually to your `bin\Debug\` output after the first build.
   - **Option C (options page):** after launching the experimental instance, open  
     **Tools → Options → rd-format → General → rd-format path (optional)** and set the full path.
4. Press **F5** to launch the experimental instance of Visual Studio.
5. Open any `.cpp`/`.h` file, right-click in the editor → **Format with rd-format**.

> If the daemon is not found, you’ll see an error message with the resolved path.

## Format on Save (optional)

- In the experimental instance: **Tools → Options → rd-format → General → Format on Save** (enable).
- The package hooks document save and formats **only C/C++** buffers.

## Packaging / Installing

- From Visual Studio: **Build** → produces a `.vsix` in `bin\<Config>\<Platform>\`.
- Double-click the `.vsix` to install into your main VS 2022 instance.
- Publish to the Visual Studio Marketplace if desired.

## Customizing the rd-format Path

The lookup order is:

1. `RD_FORMAT_PATH` environment variable (if set).
2. Embedded path: `$(AssemblyDir)\dist\rd-format\win-x64\rd-format.exe`
3. Options page override (if provided).

## Troubleshooting

- **“daemon not running” / “rd-format not found”**  
  Ensure the binary exists at the resolved path (see error text) or set `RD_FORMAT_PATH`.
- **No changes applied**  
  The daemon returned the same text; or file type isn’t recognized as C/C++ by VS.
- **Slow format**  
  Check the daemon logs (stderr appears in **View → Output → General** while debugging).
- **Crashes / bad JSON**  
  The daemon must reply per line with JSON:  
  `{"id":123, "ok":true, "text":"..."}`
  or  
  `{"id":123, "ok":false, "error":"reason"}`

## Notes

- This extension targets **VS 2022** only (`[17.0, 18.0)`).
- The JSON handling is minimal and optimized for the rd-format protocol.
- You can wire this to the default **Format Document** command later if you prefer to replace the built-in formatter.

## License

- Extension code: your choice (e.g., same as repository license).
- `rd-format` binary: distributed under its own license.
