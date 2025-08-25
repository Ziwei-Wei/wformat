using Microsoft.VisualStudio.Shell;
using System.ComponentModel;

namespace WFormatVSIX
{
    public class OptionsPage : DialogPage
    {
        [Category("Formatting")]
        [DisplayName("Override default formatter")]
        [Description("If true, the extension replace Visual Studio's built-in Format Document and Format Selection. If false, only use \"Run WFormat\" in the right click menu.")]
        public bool OverrideDefaultFormat { get; set; } = false;
    }
}
