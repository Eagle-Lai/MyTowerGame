using System.Globalization;

namespace FTProject
{
    /// <summary>Editor capture and shipped UI share the same stable, unique resource names.</summary>
    public static class LevelPreviewCatalog
    {
        public const string Directory = "Assets/_UIAssets/LevelPreviews";
        public static string LogicalName(int levelId)
        {
            return "LevelPreview_" + levelId.ToString("D3", CultureInfo.InvariantCulture);
        }
        public static string AssetPath(int levelId)
        {
            return Directory + "/" + LogicalName(levelId) + ".png";
        }
    }
}
