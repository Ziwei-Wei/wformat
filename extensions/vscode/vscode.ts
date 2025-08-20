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

    out.appendLine(`${exePath} --serve`);

    g_daemon.on("error", (e) => {
        out.appendLine(`daemon error: ${String(e)}`);
        for (const [, p] of g_pending_events) p.reject(e);
        g_pending_events.clear();
        g_daemon = null;
    });

    g_daemon.on("exit", (code, sig) => {
        out.appendLine(`daemon exit code=${code} sig=${sig ?? ""}`);
        for (const [, p] of g_pending_events) p.reject(new Error("daemon exited"));
        g_pending_events.clear();
        g_daemon = null;
    });

    g_daemon.stderr.on("data", d => out.appendLine(`stderr: ${d.toString()}`));

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
                        p.resolve(msg.text ?? "");
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
        const msg = JSON.stringify({ id, op: "format", text }) + "\n";

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

async function format(
    out: vscode.OutputChannel,
    doc: vscode.TextDocument,
    token: vscode.CancellationToken,
): Promise<vscode.TextEdit[]> {
    const start = performance.now();
    out.appendLine(`Formatting: ${doc.uri.fsPath} START`);

    let edits: vscode.TextEdit[] = [];
    try {
        const before = doc.getText();
        const after = await requestFormat(before, token, out);
        if (after !== before) {
            const full = new vscode.Range(doc.positionAt(0), doc.positionAt(before.length));
            edits = [vscode.TextEdit.replace(full, after)];
        }
    } catch (e: any) {
        let msg = String(e?.message ?? e);
        if (msg === "canceled") msg = "canceled by VS Code";
        out.appendLine(`error: ${msg}`);
        vscode.window.showErrorMessage(`rd-format error: ${msg}`);
    }

    out.appendLine(`Formatting: ${doc.uri.fsPath} END (${(performance.now() - start).toFixed(1)} ms)`);
    return edits;
}

export function activate(context: vscode.ExtensionContext) {
    const out = vscode.window.createOutputChannel("rd-format");
    const exeName = process.platform === "win32" ? "rd-format.exe" : "rd-format";
    const exePath = context.asAbsolutePath(path.join("dist", "rd-format", exeName));

    out.show(true);

    if (!fs.existsSync(exePath)) {
        const msg = `Embedded rd-format executable not found at: ${exePath}`;
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

    startDaemon(exePath, out);

    const selector: vscode.DocumentSelector = [
        { language: "cpp", scheme: "file" }
    ];

    const provider: vscode.DocumentFormattingEditProvider = {
        provideDocumentFormattingEdits: (doc, _, token) =>
            format(out, doc, token)
    };

    context.subscriptions.push(
        vscode.languages.registerDocumentFormattingEditProvider(selector, provider),
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
