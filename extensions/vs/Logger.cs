using Microsoft.VisualStudio;
using Microsoft.VisualStudio.Shell;
using Microsoft.VisualStudio.Shell.Interop;
using System;

namespace WFormatVSIX
{
    // Centralized logger that writes to a dedicated Output pane.
    // Safe to call Log from any thread.
    internal static class Logger
    {
        private static readonly Guid OutputPaneGuid = new Guid("43E12C7F-6C2C-4F3D-9A53-6F4E3E4E5A1F");
        private const string OutputPaneTitle = "WFormatVSIX";
        private static IVsOutputWindowPane _pane; // protected by UI thread access during creation only
        private static bool _creating;

        internal static void Initialize()
        {
            // Intentionally empty for now � kept for future extensibility.
        }

        internal static void Log(string message)
        {
            if (string.IsNullOrEmpty(message)) return;
            ThreadHelper.JoinableTaskFactory.Run(async delegate
            {
                await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                EnsurePane();
                if (_pane != null)
                {
                    try { _pane.OutputStringThreadSafe(message + Environment.NewLine); } catch { }
                }
            });
        }

        private static void EnsurePane()
        {
            if (_pane != null || _creating) return;
            _creating = true;
            try
            {
                ThreadHelper.JoinableTaskFactory.Run(async delegate
                {
                    await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync();
                    if (_pane != null) return;
                    var outputWindow = (IVsOutputWindow)Package.GetGlobalService(typeof(SVsOutputWindow));
                    if (outputWindow == null) return;
                    Guid paneGuid = OutputPaneGuid;
                    outputWindow.CreatePane(ref paneGuid, OutputPaneTitle, 1, 1);
                    IVsOutputWindowPane pane;
                    if (outputWindow.GetPane(ref paneGuid, out pane) == VSConstants.S_OK)
                    {
                        _pane = pane;
                    }
                });
            }
            catch { }
            finally { _creating = false; }
        }
    }
}
