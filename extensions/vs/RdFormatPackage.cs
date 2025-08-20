using System;
using System.Runtime.InteropServices;
using System.Threading;
using Community.VisualStudio.Toolkit;
using Microsoft.VisualStudio.Shell;
using Task = System.Threading.Tasks.Task;

namespace RdFormatVS
{
    [PackageRegistration(UseManagedResourcesOnly = true, AllowsBackgroundLoading = true)]
    [InstalledProductRegistration("rd-format", "Formats C/C++ using rd-format daemon", "1.0")]
    [ProvideMenuResource("Menus.ctmenu", 1)]
    [Guid(PackageGuidString)]
    [ProvideOptionPage(typeof(RdFormatOptions), "rd-format", "General", 0, 0, true)]
    public sealed class RdFormatPackage : AsyncPackage
    {
        // You can regenerate this GUID if you want a fresh identity for your package
        public const string PackageGuidString = "2B1E0B1D-7A76-4F1E-B6D8-2C8A2BFB6E32";

        protected override async Task InitializeAsync(
            CancellationToken cancellationToken,
            IProgress<ServiceProgressData> progress
        )
        {
            // Register commands (Community.VisualStudio.Toolkit handles discovery via attributes)
            await this.RegisterCommandsAsync();

            // Optionally: initialize daemon here or lazily on first format
            // await RdFormatDaemon.Instance.InitializeAsync(this);

            // Optional: hook save to support "format on save" later
            DocumentEvents.Saved += async view =>
            {
                try
                {
                    var opts = (RdFormatOptions)GetDialogPage(typeof(RdFormatOptions));
                    if (opts.FormatOnSave)
                    {
                        await FormatCurrentDocumentAsync();
                    }
                }
                catch (Exception ex)
                {
                    await VS.MessageBox.ShowErrorAsync("rd-format", ex.Message);
                }
            };
        }

        public static async Task FormatCurrentDocumentAsync()
        {
            var doc = await VS.Documents.GetActiveDocumentViewAsync();
            if (doc?.TextBuffer == null)
                return;

            string before = doc.TextBuffer.CurrentSnapshot.GetText();
            string after;

            try
            {
                // Ensure daemon is running (lazy init)
                await RdFormatDaemon.Instance.InitializeAsync();

                // Format via daemon
                using var token = VS.StatusBar.AttachCancellationToken();
                after = await RdFormatDaemon.Instance.FormatAsync(before, token);
            }
            catch (OperationCanceledException)
            {
                // user canceled – no popup needed
                return;
            }
            catch (Exception ex)
            {
                await VS.MessageBox.ShowErrorAsync("rd-format", ex.Message);
                return;
            }

            if (!string.Equals(before, after, StringComparison.Ordinal))
            {
                using var edit = doc.TextBuffer.CreateEdit();
                edit.Replace(0, doc.TextBuffer.CurrentSnapshot.Length, after);
                edit.Apply();
            }
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                RdFormatDaemon.Instance.Shutdown();
            }
            base.Dispose(disposing);
        }
    }
}
