using System;

namespace FTProject
{
    /// <summary>Player-facing tower text, shared by runtime UI and isolated previews.</summary>
    public static class TowerPresentation
    {
        public static string Description(TowerConfig tower, Func<string, string> translate = null)
        {
            if (tower == null) return string.Empty;
            if (tower.IsSlowAura)
                return Text(translate, "Tower description: slow", "Slows enemies in range. Upgrade to strengthen the slow and widen coverage.");
            if (tower.IsAoe)
                return Text(translate, "Tower description: blast", "Area damage against groups. Upgrade to increase damage and reach.");
            return Text(translate, "Tower description: normal", "Fast single-target attacks. Upgrade to increase damage, range and attack speed.");
        }

        public static string UpgradeSummary(TowerConfig current, TowerConfig next, Func<string, string> translate = null)
        {
            if (current == null || next == null) return string.Empty;
            string heading = Format(translate, "Tower level upgrade: {0} → {1}", "Level {0} → {1}", current.Level, next.Level);
            string primary = current.IsSlowAura
                ? Format(translate, "Slow upgrade: {0:P0} → {1:P0}", "Slow {0:P0} → {1:P0}", current.EffectValue, next.EffectValue)
                : Format(translate, "Damage upgrade: {0:0.#} → {1:0.#} · DPS {2:0.#} → {3:0.#}",
                    "Damage {0:0.#} → {1:0.#} · DPS {2:0.#} → {3:0.#}", current.Power, next.Power, Dps(current), Dps(next));
            string range = Format(translate, "Range upgrade: {0:0.##} → {1:0.##}", "Range {0:0.##} → {1:0.##} tiles", current.RadiusGrid, next.RadiusGrid);
            string interval = current.IsSlowAura
                ? Format(translate, "Aura refresh upgrade: {0:0.00}s → {1:0.00}s", "Aura refresh {0:0.00}s → {1:0.00}s", current.CooldownSec, next.CooldownSec)
                : Format(translate, "Attack interval upgrade: {0:0.00}s → {1:0.00}s", "Attack interval {0:0.00}s → {1:0.00}s", current.CooldownSec, next.CooldownSec);
            return heading + "\n" + primary + "\n" + range + "\n" + interval;
        }

        private static float Dps(TowerConfig tower)
        { return tower.CooldownSec > 0 ? tower.Power / tower.CooldownSec : 0; }
        private static string Text(Func<string, string> translate, string key, string fallback)
        {
            string value = translate != null ? translate(key) : Localization.Get(key);
            return string.IsNullOrEmpty(value) || value == key ? fallback : value;
        }
        private static string Format(Func<string, string> translate, string key, string fallback, params object[] args)
        { return string.Format(Text(translate, key, fallback), args); }
    }
}
