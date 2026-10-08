namespace FTProject
{
    /// <summary>
    /// 音效逻辑名常量（M2-W6）。
    ///
    /// 【为什么要有这个类】业务代码里写裸字符串有两个后果：
    ///   ① 拼错了不会有任何提示（音效是静默降级的），只能靠人耳发现；
    ///   ② 想换"某个动作播哪个音"时，得全局搜字符串。
    /// 集中成常量后，改名与查漏都只在这一个文件里发生。
    ///
    /// 【与 TBAudio 表的对应】每个常量都必须能在
    /// Luban/Config/Datas/AudioData.xlsx 的 logicalName 列里找到同名行；
    /// 找不到时 AudioManager 只会限流警告一次，不会报错。
    /// </summary>
    public static class AudioName
    {
        // ---- 塔 · 开火（按塔型区分）----
        public const string TowerFireNormal = "sfx_tower_fire_normal";
        public const string TowerFirePower = "sfx_tower_fire_power";
        public const string TowerFireRetard = "sfx_tower_fire_retard";
        public const string TowerFirePierce = "sfx_tower_fire_pierce";
        public const string TowerFireLaser = "sfx_tower_fire_laser";

        // ---- 塔 · 操作 ----
        public const string TowerBuild = "sfx_tower_build";
        public const string TowerUpgrade = "sfx_tower_upgrade";
        public const string TowerSell = "sfx_tower_sell";

        // ---- 怪物 ----
        public const string EnemyHit = "sfx_enemy_hit";
        public const string EnemyDeath = "sfx_enemy_death";
        public const string EnemyLeak = "sfx_enemy_leak";

        // ---- 流程 ----
        public const string RoundStart = "sfx_round_start";
        public const string RoundClear = "sfx_round_clear";
        public const string Victory = "sfx_victory";
        public const string Defeat = "sfx_defeat";

        // ---- UI ----
        public const string UiClick = "sfx_ui_click";

        // ---- BGM（循环背景乐，走 AudioManager 的 BGM 通道）----
        public const string BgmSelect = "bgm_select";
        public const string BgmBattle = "bgm_battle";

        /// <summary>
        /// 按塔型取开火音效逻辑名。
        /// 【为什么要显式映射】与 HudView 的按钮名同理：Slow(3) 的节点/资源名是 Retard，
        /// 这类"名字与枚举不同形"的地方一律用映射表，不要用字符串拼接去猜。
        /// </summary>
        public static string TowerFire(int towerType)
        {
            switch (towerType)
            {
                case 2: return TowerFirePower;
                case 3: return TowerFireRetard;
                case 4: return TowerFirePierce;
                case 5: return TowerFireLaser;
                default: return TowerFireNormal;
            }
        }
    }
}
