using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Community.VisualStudio.Toolkit;
using Microsoft.VisualStudio.Shell;

namespace RdFormatVS
{
    /// <summary>
    /// Manages the rd-format daemon ( --serve ) and a tiny JSON-Lines protocol:
    ///   request: {"id":1,"op":"format","text":"..."}
    ///   reply:   {"id":1,"ok":true,"text":"..."}  or {"id":1,"ok":false,"error":"..."}
    /// </summary>
    public sealed class RdFormatDaemon
    {
        public static RdFormatDaemon Instance { get; } = new RdFormatDaemon();

        private RdFormatDaemon() { }

        private Process _proc;
        private StreamWriter _stdin;
        private int _nextId = 0;
        private readonly ConcurrentDictionary<int, TaskCompletionSource<string>> _pending =
            new ConcurrentDictionary<int, TaskCompletionSource<string>>();

        // Naive JSON field extractors to avoid extra dependencies.
        private static readonly Regex RxId = new Regex(
            @"""id""\s*:\s*(\d+)",
            RegexOptions.Compiled
        );
        private static readonly Regex RxOk = new Regex(
            @"""ok""\s*:\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex RxText = new Regex(
            @"""text""\s*:\s*""((?:\\""|\\\\|[^""])*)""",
            RegexOptions.Compiled
        );
        private static readonly Regex RxError = new Regex(
            @"""error""\s*:\s*""((?:\\""|\\\\|[^""])*)""",
            RegexOptions.Compiled
        );

        private static string Unescape(string s) =>
            s?.Replace("\\\"", "\"").Replace("\\\\", "\\") ?? "";

        /// <summary>
        /// Starts the daemon if not already running. Idempotent.
        /// </summary>
        public async Task InitializeAsync()
        {
            await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();

            if (_proc != null && !_proc.HasExited)
                return;

            string exePath = ResolveExePath();
            if (!File.Exists(exePath))
            {
                await VS.MessageBox.ShowErrorAsync(
                    "rd-format",
                    $"rd-format executable not found:\n{exePath}\n\n"
                        + $"Set environment variable RD_FORMAT_PATH to override."
                );
                throw new FileNotFoundException("rd-format not found", exePath);
            }

            try
            {
                var psi = new ProcessStartInfo(exePath, "--serve")
                {
                    UseShellExecute = false,
                    RedirectStandardInput = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    WorkingDirectory = Environment.CurrentDirectory
                };

                _proc = new Process { StartInfo = psi, EnableRaisingEvents = true };
                _proc.OutputDataReceived += (s, e) =>
                {
                    if (e.Data != null)
                        OnStdoutLine(e.Data);
                };
                _proc.ErrorDataReceived += (s, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                        VS.OutputWindow.WriteLine($"[rd-format][stderr] {e.Data}");
                };
                _proc.Exited += (s, e) =>
                {
                    VS.OutputWindow.WriteLine($"[rd-format] daemon exited code={_proc.ExitCode}");
                    foreach (var kv in _pending)
                        kv.Value.TrySetException(new Exception("daemon exited"));
                    _pending.Clear();
                };

                _proc.Start();
                _stdin = _proc.StandardInput;
                _proc.BeginOutputReadLine();

                VS.OutputWindow.WriteLine($"[rd-format] daemon started: {exePath} --serve");
            }
            catch (Exception ex)
            {
                await VS.MessageBox.ShowErrorAsync(
                    "rd-format",
                    $"Failed to start daemon: {ex.Message}"
                );
                throw;
            }
        }

        /// <summary>
        /// Format text via the daemon. Throws OperationCanceledException if canceled.
        /// </summary>
        public async Task<string> FormatAsync(string text, CancellationToken token)
        {
            if (_proc == null || _proc.HasExited || _stdin == null)
                throw new InvalidOperationException("daemon not running");

            int id = Interlocked.Increment(ref _nextId);
            var tcs = new TaskCompletionSource<string>(
                TaskCreationOptions.RunContinuationsAsynchronously
            );
            _pending[id] = tcs;

            string payload = $"{{\"id\":{id},\"op\":\"format\",\"text\":{ToJsonString(text)}}}";

            try
            {
                await _stdin.WriteLineAsync(payload);
                await _stdin.FlushAsync();
            }
            catch (Exception ex)
            {
                _pending.TryRemove(id, out _);
                throw new Exception($"write to daemon failed: {ex.Message}");
            }

            using (
                token.Register(() =>
                {
                    if (_pending.TryRemove(id, out var x))
                        x.TrySetException(new OperationCanceledException("canceled"));
                })
            )
            {
                return await tcs.Task.ConfigureAwait(false);
            }
        }

        /// <summary>
        /// Stop the daemon (best-effort).
        /// </summary>
        public void Shutdown()
        {
            try
            {
                _stdin?.WriteLine("{\"op\":\"shutdown\"}");
                _stdin?.Flush();
            }
            catch
            { /* ignore */
            }

            try
            {
                if (_proc != null && !_proc.HasExited)
                    _proc.Kill();
            }
            catch
            { /* ignore */
            }
        }

        private void OnStdoutLine(string line)
        {
            try
            {
                // Parse minimal fields: id, ok, text, error
                int id = -1;
                bool hasId = false,
                    ok = false,
                    hasOk = false;

                var mId = RxId.Match(line);
                if (mId.Success && int.TryParse(mId.Groups[1].Value, out var parsedId))
                {
                    id = parsedId;
                    hasId = true;
                }

                var mOk = RxOk.Match(line);
                if (mOk.Success)
                {
                    ok = string.Equals(
                        mOk.Groups[1].Value,
                        "true",
                        StringComparison.OrdinalIgnoreCase
                    );
                    hasOk = true;
                }

                string text = null,
                    error = null;
                var mText = RxText.Match(line);
                if (mText.Success)
                    text = Unescape(mText.Groups[1].Value);
                var mErr = RxError.Match(line);
                if (mErr.Success)
                    error = Unescape(mErr.Groups[1].Value);

                if (!hasId)
                {
                    VS.OutputWindow.WriteLine($"[rd-format] unsolicited: {line}");
                    return;
                }

                if (_pending.TryRemove(id, out var tcs))
                {
                    if (hasOk && ok)
                        tcs.TrySetResult(text ?? string.Empty);
                    else
                        tcs.TrySetException(new Exception(error ?? "unknown error"));
                }
                else
                {
                    VS.OutputWindow.WriteLine($"[rd-format] late/unknown id={id}: {line}");
                }
            }
            catch
            {
                VS.OutputWindow.WriteLine($"[rd-format] bad json: {line}");
            }
        }

        private static string ResolveExePath()
        {
            // 1) Allow override via environment variable (useful for dev/testing)
            var env = Environment.GetEnvironmentVariable("RD_FORMAT_PATH");
            if (!string.IsNullOrWhiteSpace(env))
                return env;

            // 2) Embedded path relative to the VSIX assembly location
            var asmDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location) ?? "";
            var exeName = RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
                ? "rd-format.exe"
                : "rd-format";

            // Visual Studio itself runs on Windows, but we keep layout parity.
            var candidate = Path.Combine(asmDir, "dist", "rd-format", "win-x64", exeName);
            return candidate;
        }

        private static string ToJsonString(string s)
        {
            if (s == null)
                return "null";
            var sb = new StringBuilder();
            sb.Append('"');
            foreach (var ch in s)
            {
                switch (ch)
                {
                    case '\\':
                        sb.Append("\\\\");
                        break;
                    case '"':
                        sb.Append("\\\"");
                        break;
                    case '\r':
                        sb.Append("\\r");
                        break;
                    case '\n':
                        sb.Append("\\n");
                        break;
                    case '\t':
                        sb.Append("\\t");
                        break;
                    case '\b':
                        sb.Append("\\b");
                        break;
                    case '\f':
                        sb.Append("\\f");
                        break;
                    default:
                        if (char.IsControl(ch))
                            sb.Append("\\u").Append(((int)ch).ToString("x4"));
                        else
                            sb.Append(ch);
                        break;
                }
            }
            sb.Append('"');
            return sb.ToString();
        }
    }
}
