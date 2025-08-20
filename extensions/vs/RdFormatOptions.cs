using System.ComponentModel;
using Microsoft.VisualStudio.Shell;

namespace RdFormatVS
{
    public class RdFormatOptions : DialogPage
    {
        [Category("General")]
        [DisplayName("Format on Save")]
        [Description("Automatically format C/C++ documents on save.")]
        public bool FormatOnSave { get; set; } = false;

        [Category("General")]
        [DisplayName("rd-format path (optional)")]
        [Description(
            "Leave empty to use the embedded rd-format binary. Provide a full path to override."
        )]
        public string RdFormatPath { get; set; } = string.Empty;
    }
}
