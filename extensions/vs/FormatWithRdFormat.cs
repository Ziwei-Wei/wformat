using System.Threading.Tasks;
using Community.VisualStudio.Toolkit;
using Microsoft.VisualStudio.Shell;

namespace RdFormatVS
{
    // Matches the button defined in VSCommandTable.vsct (id="cmdFormatNow")
    [Command(PackageIds.cmdFormatNow)]
    internal sealed class FormatWithRdFormat : BaseCommand<FormatWithRdFormat>
    {
        protected override async Task ExecuteAsync(OleMenuCmdEventArgs e)
        {
            await VS.StatusBar.ShowMessageAsync("rd-format: formatting…");
            await RdFormatPackage.FormatCurrentDocumentAsync();
            await VS.StatusBar.ShowMessageAsync("rd-format: done");
        }
    }
}
