/// <reference types="vscode" />
/// <reference types="node" />
import * as vscode from "vscode";
import * as cp from "child_process";
import * as fs from "fs";
import * as path from "path";
import { performance } from "node:perf_hooks";

let g_daemon: cp.ChildProcessWithoutNullStreams | null = null;
let g_nextId = 1;
const g_pending_events = new Map<number, { resolve: (s: string) => void, reject: (e: any) => void }>();
const g_canceled_ids = new Set<number>();
let g_stdoutBuf = "";

function startDaemon(exePath: string, out: vscode.OutputChannel) {
    if (g_daemon) return;

    g_daemon = cp.spawn(
        exePath,
        ["--serve"],
        {
            cwd: process.cwd(),
            shell: false,
            stdio: ["pipe", "pipe", "pipe"]
        }
    );

    out.appendLine(`Start Daemon: ${exePath} --serve`);

    g_daemon.on("error", (e: Error) => {
        out.appendLine(`daemon error: ${String(e)}`);
        for (const [, p] of g_pending_events) p.reject(e);
        g_pending_events.clear();
        g_daemon = null;
    });

    g_daemon.on("exit", (code: number | null, sig: NodeJS.Signals | null) => {
        out.appendLine(`daemon exit code=${code} sig=${sig ?? ""}`);
        for (const [, p] of g_pending_events) p.reject(new Error("daemon exited"));
        g_pending_events.clear();
        g_daemon = null;
    });

    g_daemon.stderr.on("data", (d: Buffer) => out.appendLine(`stderr: ${d.toString()}`));

    g_daemon.stdout.on("data", (chunk: Buffer) => {
        g_stdoutBuf += chunk.toString();
        let idx: number;
        while ((idx = g_stdoutBuf.indexOf("\n")) >= 0) {
            const line = g_stdoutBuf.slice(0, idx);
            g_stdoutBuf = g_stdoutBuf.slice(idx + 1);
            if (!line.trim()) continue;

            try {
                const msg = JSON.parse(line);
                const id = msg.id;

                if (typeof id === "number" && g_pending_events.has(id)) {
                    const p = g_pending_events.get(id)!;
                    g_pending_events.delete(id);

                    if (g_canceled_ids.has(id)) {
                        g_canceled_ids.delete(id);
                        out.appendLine(`reply for canceled id=${id} dropped`);
                        continue;
                    }

                    if (msg.ok) {
                        try {
                            const buf = Buffer.from(msg.b64, 'base64');
                            p.resolve(buf.toString('utf8'));
                        } catch {
                            p.resolve("");
                        }
                    } else {
                        p.reject(new Error(msg.error ?? "unknown error"));
                    }
                } else {
                    if (typeof id === "number" && g_canceled_ids.delete(id)) {
                        out.appendLine(`late reply for canceled id=${id} swallowed`);
                        continue;
                    }
                    out.appendLine(`unsolicited: ${line}`);
                }
            } catch {
                out.appendLine(`bad json: ${line}`);
            }
        }
    });
}

async function requestFormat(
    text: string,
    token: vscode.CancellationToken,
    out: vscode.OutputChannel
): Promise<string> {
    return new Promise((resolve, reject) => {
        if (!g_daemon || !g_daemon.stdin) {
            return reject(new Error("daemon not running"));
        }

        const id = g_nextId++;
        const b64 = Buffer.from(text, "utf8").toString("base64");
        const msg = JSON.stringify({ id, op: "format", b64: b64 }) + "\n";

        g_pending_events.set(id, { resolve, reject });

        const sub = token.onCancellationRequested(() => {
            if (g_pending_events.has(id)) {
                g_canceled_ids.add(id);
                g_pending_events.delete(id);
                out.appendLine(`request canceled id=${id}`);
                reject(new Error("canceled"));
            }
            sub.dispose();
        });

        const ok = g_daemon.stdin.write(msg, "utf8", () => {
            try { sub.dispose(); } catch { }
        });

        if (!ok) {
            g_daemon.stdin.once("drain", () => { });
        }
    });
}

async function formatSelection(
    out: vscode.OutputChannel,
    doc: vscode.TextDocument,
    range: vscode.Range,
    token: vscode.CancellationToken,
): Promise<vscode.TextEdit[]> {
    out.appendLine(`Formatting: ${doc.uri.fsPath} START`);
    const start = performance.now();

    let edits: vscode.TextEdit[] = [];
    try {
        const before = doc.getText(range);
        const after = await requestFormat(before, token, out);
        if (after !== before) {
            edits = [vscode.TextEdit.replace(range, after)];
        }
    } catch (e: any) {
        let msg = String(e?.message ?? e);
        if (msg === "canceled") msg = "canceled by VS Code";
        out.appendLine(`error: ${msg}`);
        vscode.window.showErrorMessage(`wformat error: ${msg}`);
    }

    out.appendLine(`Formatting: ${doc.uri.fsPath} END (${(performance.now() - start).toFixed(1)} ms)`);
    return edits;
}

async function formatDocument(
    out: vscode.OutputChannel,
    doc: vscode.TextDocument,
    token: vscode.CancellationToken,
): Promise<vscode.TextEdit[]> {
    const full = new vscode.Range(doc.positionAt(0), doc.positionAt(doc.getText().length));
    return formatSelection(out, doc, full, token);
}

function resolveBinaryPath(context: vscode.ExtensionContext): string {
    const exeName = process.platform === "win32" ? "wformat.exe" : "wformat";

    const candidates: string[] = [];
    if (process.platform === 'win32' && process.arch === 'x64') candidates.push('wformat-win32-x64');
    if (process.platform === 'darwin' && process.arch === 'x64') candidates.push('wformat-darwin-x64');
    if (process.platform === 'darwin' && process.arch === 'arm64') candidates.push('wformat-darwin-arm64');
    if (process.platform === 'linux' && process.arch === 'x64') candidates.push('wformat-linux-x64');
    if (process.platform === 'linux' && process.arch === 'arm64') candidates.push('wformat-linux-arm64');

    for (const folder of candidates) {
        const full = context.asAbsolutePath(path.join('dist', folder, exeName));
        if (fs.existsSync(full)) return full;
    }

    // Single-folder layout fallback
    return context.asAbsolutePath(path.join('dist', 'wformat', exeName));
}

export function activate(context: vscode.ExtensionContext) {
    const out = vscode.window.createOutputChannel("wformat");

    const exePath = resolveBinaryPath(context);

    if (!fs.existsSync(exePath)) {
        const msg = `wformat is currently unavailable for platform=${process.platform} arch=${process.arch}.`;
        out.appendLine(msg);
        vscode.window.showErrorMessage(msg);
        context.subscriptions.push(out);
        return;
    }

    // One-time permissions / quarantine handling
    try {
        if (process.platform !== "win32") {
            fs.chmodSync(exePath, 0o755);
        }
        if (process.platform === "darwin") {
            cp.spawnSync("/usr/bin/xattr", ["-dr", "com.apple.quarantine", exePath], { stdio: "ignore" });
        }
    } catch {
    }

    out.appendLine(`Using binary: ${exePath}`);

    startDaemon(exePath, out);

    const selector: vscode.DocumentSelector = [
        { language: "cpp", scheme: "file" }
    ];

    const provider: vscode.DocumentFormattingEditProvider = {
        provideDocumentFormattingEdits: (doc: vscode.TextDocument, _opts: vscode.FormattingOptions, token: vscode.CancellationToken) =>
            formatDocument(out, doc, token)
    };

    const rangeProvider: vscode.DocumentRangeFormattingEditProvider = {
        provideDocumentRangeFormattingEdits: async (doc: vscode.TextDocument, range: vscode.Range, _opts: vscode.FormattingOptions, token: vscode.CancellationToken) => formatSelection(out, doc, range, token)
    };

    context.subscriptions.push(
        vscode.languages.registerDocumentFormattingEditProvider(selector, provider),
        vscode.languages.registerDocumentRangeFormattingEditProvider(selector, rangeProvider),
        out
    );
}

export function deactivate() {
    try {
        if (g_daemon && g_daemon.stdin) {
            g_daemon.stdin.write(JSON.stringify({ op: "shutdown" }) + "\n");
        }
    } catch { }
}
