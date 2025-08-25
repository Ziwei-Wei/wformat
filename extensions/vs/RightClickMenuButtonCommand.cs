using Microsoft.VisualStudio.Shell;
using System;
using System.ComponentModel.Design;
using Task = System.Threading.Tasks.Task;

namespace WFormatVSIX
{
    internal sealed class RightClickMenuButtonCommand
    {
        public const int CommandId = 256;
        public static readonly Guid CommandSet = new Guid("6118f133-6a38-4e1d-b201-6d63a737d025");
        private readonly AsyncPackage package;

        private RightClickMenuButtonCommand(AsyncPackage package, OleMenuCommandService commandService)
        {
            this.package = package ?? throw new ArgumentNullException(nameof(package));
            commandService = commandService ?? throw new ArgumentNullException(nameof(commandService));
            var menuCommandID = new CommandID(CommandSet, CommandId);
            var menuItem = new MenuCommand(this.Execute, menuCommandID);
            commandService.AddCommand(menuItem);
        }

        public static RightClickMenuButtonCommand Instance { get; private set; }
        private Microsoft.VisualStudio.Shell.IAsyncServiceProvider ServiceProvider => this.package;

        public static async Task InitializeAsync(AsyncPackage package)
        {
            await ThreadHelper.JoinableTaskFactory.SwitchToMainThreadAsync(package.DisposalToken);
            OleMenuCommandService commandService = await package.GetServiceAsync(typeof(IMenuCommandService)) as OleMenuCommandService;
            Instance = new RightClickMenuButtonCommand(package, commandService);
        }

        private void Execute(object sender, EventArgs e)
        {
            ThreadHelper.ThrowIfNotOnUIThread();
            var daemon = WFormatDaemon.Instance;
            bool handled = daemon.TryStartEditorBasedFormat(ThreadHelper.JoinableTaskFactory);
            if (!handled)
            {
                Logger.Log("Could not start editor-based format (editor unavailable)");
            }
        }
    }
}
