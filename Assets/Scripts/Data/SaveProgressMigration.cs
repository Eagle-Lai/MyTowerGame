using System.Collections.Generic;

namespace FTProject
{
    public static class SaveProgressMigration
    {
        public static bool ArchiveForVersion(LevelProgress p, string versionKey)
        {
            if (p == null || string.IsNullOrEmpty(versionKey) || p.ratingVersionKey == versionKey) return false;
            if (p.legacy == null) p.legacy = new List<LegacyLevelProgress>();
            if (p.committedRunIds == null) p.committedRunIds = new List<string>();
            string oldKey = string.IsNullOrEmpty(p.ratingVersionKey) ? "legacy-v1-three-stars" : p.ratingVersionKey;
            if (!p.legacy.Exists(x => x.versionKey == oldKey))
                p.legacy.Add(new LegacyLevelProgress { versionKey = oldKey, stars = p.stars, bestHpLeft = p.bestHpLeft, bestTimeMs = p.bestTimeMs, bestCombatTimeMs = p.bestCombatTimeMs, clearCount = p.clearCount, bestRating = p.bestRating });
            p.stars = 0; p.bestTimeMs = 0; p.bestCombatTimeMs = 0; p.bestHpLeft = 0; p.bestRating = null;
            p.ratingVersionKey = versionKey;
            return true;
        }
    }
}
