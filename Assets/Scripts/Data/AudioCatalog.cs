// =============================================================================
// 本文件由工具自动生成，请勿手改。
//   生成脚本：.workbuddy/tools/gen_audio_catalog.py
//   运行方式：python .workbuddy/tools/gen_audio_catalog.py
//
// 数据来源：Assets/Audio/ 下的音频文件（.wav / .ogg / .mp3 / .aiff）
// 当前数量：18
//
// 【为什么需要一个"生成的清单"】
//   ResTable 是资源寻址的唯一数据源，而它需要在**运行时**就能枚举逻辑名。
//   手写清单会跟实际文件分叉（加了音频忘了登记 → 静默无声），
//   所以与怪物一样改成扫描目录生成。
//
// 【放音频文件后要做什么】
//   把文件丢进 Assets/Audio/，跑一次本生成器即可 —— 代码一行都不用改。
// =============================================================================

namespace FTProject
{
    /// <summary>音频清单（生成代码）。逻辑名 = "Audio_" + 文件名（不含扩展名）。</summary>
    public static class AudioCatalog
    {
        /// <summary>文件名（不含扩展名），与 TBAudio.logicalName 一一对应</summary>
        public static readonly string[] Names =
        {
            "bgm_battle", "bgm_select", "sfx_defeat", "sfx_enemy_death",
            "sfx_enemy_hit", "sfx_enemy_leak", "sfx_round_clear", "sfx_round_start",
            "sfx_tower_build", "sfx_tower_fire_laser", "sfx_tower_fire_normal", "sfx_tower_fire_pierce",
            "sfx_tower_fire_power", "sfx_tower_fire_retard", "sfx_tower_sell", "sfx_tower_upgrade",
            "sfx_ui_click", "sfx_victory",
        };

        /// <summary>资源路径（Assets/Audio/xxx.wav），下标与 Names 一一对应</summary>
        public static readonly string[] AssetPaths =
        {
            "Assets/Audio/BGM/bgm_battle.mp3", "Assets/Audio/BGM/bgm_select.wav", "Assets/Audio/SFX/sfx_defeat.mp3", "Assets/Audio/SFX/sfx_enemy_death.mp3",
            "Assets/Audio/SFX/sfx_enemy_hit.mp3", "Assets/Audio/SFX/sfx_enemy_leak.mp3", "Assets/Audio/SFX/sfx_round_clear.mp3", "Assets/Audio/SFX/sfx_round_start.mp3",
            "Assets/Audio/SFX/sfx_tower_build.mp3", "Assets/Audio/SFX/sfx_tower_fire_laser.mp3", "Assets/Audio/SFX/sfx_tower_fire_normal.mp3", "Assets/Audio/SFX/sfx_tower_fire_pierce.mp3",
            "Assets/Audio/SFX/sfx_tower_fire_power.mp3", "Assets/Audio/SFX/sfx_tower_fire_retard.mp3", "Assets/Audio/SFX/sfx_tower_sell.mp3", "Assets/Audio/SFX/sfx_tower_upgrade.mp3",
            "Assets/Audio/SFX/sfx_ui_click.mp3", "Assets/Audio/SFX/sfx_victory.mp3",
        };

        public static int Count { get { return Names.Length; } }

        /// <summary>逻辑名：Audio_&lt;文件名&gt;（与 TBAudio.logicalName 拼前缀后一致）</summary>
        public static string LogicalName(int i)
        {
            return "Audio_" + Names[i];
        }
    }
}
