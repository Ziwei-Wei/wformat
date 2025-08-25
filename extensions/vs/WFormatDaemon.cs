using Microsoft.VisualStudio;
using Microsoft.VisualStudio.Editor;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Text;
using Microsoft.VisualStudio.Text.Editor;
using Microsoft.VisualStudio.TextManager.Interop;
using Microsoft.VisualStudio.Threading;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Runtime.InteropServices; // added for RuntimeInformation

namespace WFormatVSIX
{
    internal sealed class WFormatDaemon
    {
        private static readonly Lazy<WFormatDaemon> _instance = new Lazy<WFormatDaemon>(() => new WFormatDaemon(), LazyThreadSafetyMode.ExecutionAndPublication);
        public static WFormatDaemon Instance { get { return _instance.Value; } }

        private readonly Process _process;
        private int _nextId;
        private readonly object _sync = new object();
        private readonly Dictionary<int, TaskCompletionSource<string>> _pending = new Dictionary<int, TaskCompletionSource<string>>();
        private volatile bool _formattingInProgress;

        private WFormatDaemon()
        {
            try
            {
                string baseDir = Path.GetDirectoryName(typeof(WFormatVSIXPackage).Assembly.Location);

                // Determine architecture-specific executable candidates
                var candidateRelPaths = new List<string>();
                try
                {
                    var arch = RuntimeInformation.ProcessArchitecture; // Architecture enum
                    switch (arch)
                    {
                        case Architecture.Arm64:
                            candidateRelPaths.Add(Path.Combine("dist", "win-arm64", "wformat", "wformat.exe"));
                            break;
                        case Architecture.X64:
                            candidateRelPaths.Add(Path.Combine("dist", "win-x64", "wformat", "wformat.exe"));
                            break;
                    }
                }
                catch { }
                candidateRelPaths.Add(Path.Combine("dist", "wformat", "wformat.exe"));

                string exePath = null;
                foreach (var rel in candidateRelPaths)
                {
                    var full = Path.Combine(baseDir, rel);
                    if (File.Exists(full)) { exePath = full; break; }
                }
                if (exePath == null)
                {
                    throw new FileNotFoundException("wformat executable not found");
                }

                var psi = new ProcessStartInfo
                {
                    FileName = exePath,
                    Arguments = "--serve",
                    WorkingDirectory = Path.GetDirectoryName(exePath),
                    UseShellExecute = false,
                    RedirectStandardInput = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = Encoding.UTF8
                };

                _process = new Process { StartInfo = psi, EnableRaisingEvents = true };

                _process.ErrorDataReceived += (s, e) =>
                {
                    var data = e.Data;
                    if (string.IsNullOrEmpty(data)) return;
                    Logger.Log("wformat stderr: " + data);
                };

                _process.Exited += (s, e) =>
                {
                    try { FailAllPending(new Exception("wformat exited (code " + _process.ExitCode + ")")); }
                    catch { }
                };

                _process.OutputDataReceived += (s, e) =>
                {
                    var data = e.Data;
                    if (string.IsNullOrEmpty(data)) return;
                    try
                    {
                        int id; bool ok; string formatted; string error;
                        if (TryDecodeLine(data, out id, out ok, out formatted, out error))
                        {
                            TaskCompletionSource<string> tcs = null;
                            lock (_sync)
                            {
                                if (_pending.TryGetValue(id, out tcs))
                                {
                                    _pending.Remove(id);
                                }
                            }
                            if (tcs != null)
                            {
                                if (ok) tcs.TrySetResult(formatted ?? string.Empty);
                                else tcs.TrySetException(new Exception(error ?? "unknown error"));
                            }
                        }
                    }
                    catch { }
                };

                if (!_process.Start()) throw new Exception("Failed to start wformat");

                try { _process.BeginOutputReadLine(); } catch { }
                try { _process.BeginErrorReadLine(); } catch { }

                Logger.Log("wformat --serve started (PID " + _process.Id + ")");
            }
            catch (Exception ex)
            {
                Logger.Log("Failed to launch wformat: " + ex.Message);
                throw;
            }
        }

        ~WFormatDaemon()
        {
            try
            {
                if (_process != null && !_process.HasExited)
                {
                    try { _process.Kill(); } catch { }
                    try { _process.WaitForExit(2000); } catch { }
                }
            }
            catch { }
            try { _process?.Dispose(); } catch { }
        }

        public bool TryStartEditorBasedFormat(JoinableTaskFactory jtf)
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            if (_formattingInProgress)
            {
                Logger.Log("Format skipped: already running");
                return true; // treat as handled to avoid duplicate triggers
            }

            IVsTextManager textManager = Package.GetGlobalService(typeof(SVsTextManager)) as IVsTextManager;
            if (textManager == null) return false;
            IVsTextView vsTextView;
            if (textManager.GetActiveView(1, null, out vsTextView) != VSConstants.S_OK || vsTextView == null) return false;

            var userData = vsTextView as IVsUserData;
            if (userData == null) return false;
            object hostObj;
            var hostGuid = DefGuidList.guidIWpfTextViewHost;
            if (userData.GetData(ref hostGuid, out hostObj) != VSConstants.S_OK) return false;
            var host = hostObj as IWpfTextViewHost;
            if (host == null) return false;
            var view = host.TextView;
            var buffer = view.TextBuffer;
            if (buffer == null) return false;

            var snapshot = buffer.CurrentSnapshot;
            // Always format the entire document; ignore any selection.
            view.Selection.Clear(); // ensure no selection logic is relied upon downstream
            SnapshotSpan span = new SnapshotSpan(snapshot, 0, snapshot.Length);
            string originalText = span.GetText() ?? string.Empty;

            ITrackingSpan tracking = snapshot.CreateTrackingSpan(span, SpanTrackingMode.EdgeInclusive);
            var cts = new CancellationTokenSource();

            EventHandler<TextContentChangedEventArgs> changedHandler = null;
            changedHandler = (s, e) =>
            {
                try
                {
                    var currentSpan = tracking.GetSpan(buffer.CurrentSnapshot);
                    string currentText = currentSpan.GetText();
                    if (!string.Equals(currentText, originalText, StringComparison.Ordinal))
                    {
                        cts.Cancel();
                    }
                }
                catch { }
            };
            buffer.Changed += changedHandler;

            _formattingInProgress = true;
            Logger.Log("Queued format (whole document)");

            _ = jtf.RunAsync(async delegate
            {
                string formatted = null;
                try
                {
                    formatted = await FormatAsync(originalText, cancellationToken: cts.Token).ConfigureAwait(false);
                }
                catch (OperationCanceledException)
                {
                    Logger.Log("Format canceled (user edit)");
                }
                catch (Exception ex)
                {
                    Logger.Log("External format error: " + ex.Message);
                }

                try
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    if (cts.IsCancellationRequested || formatted == null)
                    {
                        Logger.Log("Cancelled; skip apply");
                        return;
                    }
                    if (formatted == originalText)
                    {
                        Logger.Log("Format applied (no change)");
                        return;
                    }
                    var currentSpan = tracking.GetSpan(buffer.CurrentSnapshot);
                    string currentText = currentSpan.GetText();
                    if (!string.Equals(currentText, originalText, StringComparison.Ordinal))
                    {
                        Logger.Log("Region mutated; skip apply");
                        return;
                    }
                    using (var edit = buffer.CreateEdit())
                    {
                        edit.Replace(currentSpan.Span, formatted);
                        edit.Apply();
                    }
                    Logger.Log("Format applied (whole document)");
                }
                catch (Exception ex)
                {
                    Logger.Log("Async apply error: " + ex.Message);
                }
                finally
                {
                    buffer.Changed -= changedHandler;
                    cts.Dispose();
                    _formattingInProgress = false;
                }
            });

            return true;
        }

        private async Task<string> FormatAsync(string text, int timeoutMs = 10000, CancellationToken cancellationToken = default(CancellationToken))
        {
            if (text == null) text = string.Empty;
            int id = Interlocked.Increment(ref _nextId);
            var tcs = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
            lock (_sync) { _pending[id] = tcs; }

            string b64 = Convert.ToBase64String(Encoding.UTF8.GetBytes(text));
            string json = "{\"id\":" + id + ",\"op\":\"format\",\"b64\":\"" + b64 + "\"}\n";
            try
            {
                await _process.StandardInput.WriteAsync(json);
                await _process.StandardInput.FlushAsync();
            }
            catch (Exception ex)
            {
                lock (_sync) { _pending.Remove(id); }
                Logger.Log("Send failed: " + ex.Message);
                throw;
            }

            using (cancellationToken.Register(() =>
            {
                lock (_sync) { _pending.Remove(id); }
                tcs.TrySetCanceled();
            }))
            {
                Task timeoutTask = timeoutMs > 0 ? Task.Delay(timeoutMs) : Task.Delay(Timeout.Infinite, CancellationToken.None);
                Task completed = await Task.WhenAny(tcs.Task, timeoutTask).ConfigureAwait(false);
                if (completed != tcs.Task)
                {
                    lock (_sync) { _pending.Remove(id); }
                    tcs.TrySetException(new TimeoutException("format request timed out"));
                }
                return await tcs.Task.ConfigureAwait(false);
            }
        }

        private void FailAllPending(Exception ex)
        {
            KeyValuePair<int, TaskCompletionSource<string>>[] copy;
            lock (_sync)
            {
                copy = new KeyValuePair<int, TaskCompletionSource<string>>[_pending.Count];
                int i = 0; foreach (var kv in _pending) copy[i++] = kv; _pending.Clear();
            }
            foreach (var kv in copy)
            {
                try { kv.Value.TrySetException(ex); } catch { }
            }
        }

        private bool TryDecodeLine(string line, out int id, out bool ok, out string formatted, out string error)
        {
            id = 0; ok = false; formatted = null; error = null;
            if (string.IsNullOrWhiteSpace(line)) return false;
            try
            {
                if (!(line[0] == '{' && line[line.Length - 1] == '}')) return false;
                var idMatch = Regex.Match(line, "\"id\"\\s*:\\s*(\\d+)");
                var okMatch = Regex.Match(line, "\"ok\"\\s*:\\s*(true|false)");
                if (!idMatch.Success || !okMatch.Success) return false;
                id = int.Parse(idMatch.Groups[1].Value);
                ok = string.Equals(okMatch.Groups[1].Value, "true", StringComparison.OrdinalIgnoreCase);
                if (ok)
                {
                    var b64Match = Regex.Match(line, "\\\"b64\\\"\\s*:\\s*\\\"([^\\\"]*)\\\"");
                    string b64 = b64Match.Success ? b64Match.Groups[1].Value : string.Empty;
                    if (!string.IsNullOrEmpty(b64))
                    {
                        try { formatted = Encoding.UTF8.GetString(Convert.FromBase64String(b64)); }
                        catch { formatted = string.Empty; }
                    }
                    else formatted = string.Empty;
                }
                else
                {
                    var errMatch = Regex.Match(line, "\"error\"\\s*:\\s*\"([^\"]*)\"");
                    error = errMatch.Success ? errMatch.Groups[1].Value : "unknown error";
                }
                return true;
            }
            catch { return false; }
        }
    }
}
