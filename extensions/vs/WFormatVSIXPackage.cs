using EnvDTE;
using Microsoft.VisualStudio;
using Microsoft.VisualStudio.Shell;
using System;
using System.Runtime.InteropServices;
using System.Threading;
using Task = System.Threading.Tasks.Task;

namespace WFormatVSIX
{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [Guid(WFormatVSIXPackage.PackageGuidString)]
    [ProvideMenuResource("Menus.ctmenu", 1)]
    [ProvideAutoLoad(VSConstants.UICONTEXT.NoSolution_string, PackageAutoLoadFlags.BackgroundLoad)]
    [ProvideAutoLoad(VSConstants.UICONTEXT.SolutionExists_string, PackageAutoLoadFlags.BackgroundLoad)]
    [ProvideOptionPage(typeof(OptionsPage), "wformat", "General", 0, 0, true)]
    public sealed class WFormatVSIXPackage : AsyncPackage
    {
        public const string PackageGuidString = "00870c79-a09d-4f89-a4d1-ef8790a9d79f";

        private CommandEvents _formatDocumentEvents;
        private CommandEvents _formatSelectionEvents;

        private OptionsPage OptionsPage => (OptionsPage)GetDialogPage(typeof(OptionsPage));

        protected override async Task InitializeAsync(CancellationToken cancellationToken, IProgress<ServiceProgressData> progress)
        {
            await base.InitializeAsync(cancellationToken, progress);
            // Touch singleton so it starts (errors already logged inside constructor)
            try { var _ = WFormatDaemon.Instance; } catch { }
            await JoinableTaskFactory.SwitchToMainThreadAsync(cancellationToken);
            await RightClickMenuButtonCommand.InitializeAsync(this);
            HookFormatEvents();
            Logger.Log("WFormatVSIXPackage initialized");
        }

        protected override void Dispose(bool disposing)
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            try
            {
                if (_formatDocumentEvents != null) _formatDocumentEvents.BeforeExecute -= OnFormatBeforeExecute;
                if (_formatSelectionEvents != null) _formatSelectionEvents.BeforeExecute -= OnFormatBeforeExecute;
            }
            catch { }
            base.Dispose(disposing);
        }

        private void HookFormatEvents()
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            var dte = (DTE)GetGlobalService(typeof(DTE));
            if (dte == null) return;
            var events = dte.Events; if (events == null) return;
            string vsStd2KGuid = VSConstants.VSStd2K.ToString("B");
            _formatDocumentEvents = events.get_CommandEvents(vsStd2KGuid, (int)VSConstants.VSStd2KCmdID.FORMATDOCUMENT);
            _formatSelectionEvents = events.get_CommandEvents(vsStd2KGuid, (int)VSConstants.VSStd2KCmdID.FORMATSELECTION);
            if (_formatDocumentEvents != null) _formatDocumentEvents.BeforeExecute += OnFormatBeforeExecute;
            if (_formatSelectionEvents != null) _formatSelectionEvents.BeforeExecute += OnFormatBeforeExecute;
        }

        private void OnFormatBeforeExecute(string Guid, int ID, object CustomIn, object CustomOut, ref bool CancelDefault)
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            try
            {
                if (OptionsPage.OverrideDefaultFormat)
                {
                    CancelDefault = true;
                    var server = WFormatDaemon.Instance;
                    _ = server.TryStartEditorBasedFormat(JoinableTaskFactory);
                }
                else
                {
                    CancelDefault = false;
                }
            }
            catch (Exception ex)
            {
                Logger.Log("Format hook error: " + ex.Message);
            }
        }
    }
}
