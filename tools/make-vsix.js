// node tools/make-vsix.js win32 x64    # or: darwin arm64 | linux x64
const fs = require("fs");
const path = require("path");

const [, , osName, cpu] = process.argv;
if (!osName || !cpu) {
    console.error("usage: node tools/make-vsix.js <win32|darwin|linux> <x64|arm64>");
    process.exit(1);
}

const root = path.resolve(__dirname, "..");
const pkgPath = path.join(root, "package.json");
const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));

// inject platform selectors
pkg.os = [osName];
pkg.cpu = [cpu];

// ensure only this platform’s binary is included
const exeName = osName === "win32" ? "rd_format.exe" : "rd_format";
const srcBin = path.join(root, "bin-src", `${osName}-${cpu}`, exeName); // your source binaries
const dstDir = path.join(root, "bin");
const dstExe = path.join(dstDir, exeName);

if (!fs.existsSync(srcBin)) {
    console.error("missing binary:", srcBin);
    process.exit(1);
}
fs.rmSync(dstDir, { recursive: true, force: true });
fs.mkdirSync(dstDir, { recursive: true });
fs.copyFileSync(srcBin, dstExe);
if (osName !== "win32") {
    fs.chmodSync(dstExe, 0o755);
}

// write a temp package.json with os/cpu injected
const tmpPkgPath = path.join(root, "package.platform.json");
fs.writeFileSync(tmpPkgPath, JSON.stringify(pkg, null, 2));

// run vsce with the temp package.json
const { spawnSync } = require("child_process");
const res = spawnSync("npx", ["vsce", "package", "--no-dependencies", "--packageJsonPath", tmpPkgPath], {
    cwd: root, stdio: "inherit"
});
process.exit(res.status ?? 1);
