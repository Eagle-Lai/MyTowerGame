using System.Collections.Generic;
namespace FTProject
{
    public sealed class AudioResourceRegistration
    {
        public readonly SoundCue cue;
        public readonly string key, path, bundle;
        public AudioResourceRegistration(SoundCue cue, string key, string path, string bundle)
        { this.cue = cue; this.key = key; this.path = path; this.bundle = bundle; }
    }
    // Explicit registration of the commissioned 93 WAVs; the CSV is production evidence, not a runtime dependency.
    public static class AudioResourceMap
    {
        public const string CatalogKey = "GameAudioCatalog";
        public const string MixerKey = "GameAudioMixer";
        public const string RuntimePath = "Assets/Audio/Runtime";
        public static readonly AudioResourceRegistration[] Assets =
        {
            new AudioResourceRegistration(SoundCue.Menu, "ft_bgm_menu", "Assets/Audio/OriginalPack_20261023/BGM/ft_bgm_menu.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.Prepare, "ft_bgm_prepare", "Assets/Audio/OriginalPack_20261023/BGM/ft_bgm_prepare.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.Battle, "ft_bgm_battle", "Assets/Audio/OriginalPack_20261023/BGM/ft_bgm_battle.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.Pressure, "ft_bgm_pressure", "Assets/Audio/OriginalPack_20261023/BGM/ft_bgm_pressure.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.Victory, "ft_stinger_victory", "Assets/Audio/OriginalPack_20261023/Stingers/ft_stinger_victory.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.Defeat, "ft_stinger_defeat", "Assets/Audio/OriginalPack_20261023/Stingers/ft_stinger_defeat.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.Rating, "ft_stinger_rating", "Assets/Audio/OriginalPack_20261023/Stingers/ft_stinger_rating.wav", ResBundle.AudioMusic),
            new AudioResourceRegistration(SoundCue.UiClick, "ft_sfx_ui_click_01", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_click_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiClick, "ft_sfx_ui_click_02", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_click_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiClick, "ft_sfx_ui_click_03", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_click_03.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiConfirm, "ft_sfx_ui_confirm_01", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_confirm_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiConfirm, "ft_sfx_ui_confirm_02", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_confirm_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiBack, "ft_sfx_ui_back_01", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_back_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiBack, "ft_sfx_ui_back_02", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_back_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiInvalid, "ft_sfx_ui_invalid_01", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_invalid_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiInvalid, "ft_sfx_ui_invalid_02", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_invalid_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiToggle, "ft_sfx_ui_toggle_01", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_toggle_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiToggle, "ft_sfx_ui_toggle_02", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_toggle_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.UiToggle, "ft_sfx_ui_toggle_03", "Assets/Audio/OriginalPack_20261023/SFX/UI/ft_sfx_ui_toggle_03.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.TowerSelect, "ft_sfx_tower_select_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_select_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerSelect, "ft_sfx_tower_select_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_select_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerSelect, "ft_sfx_tower_select_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_select_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerBuild, "ft_sfx_tower_build_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_build_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerBuild, "ft_sfx_tower_build_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_build_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerBuild, "ft_sfx_tower_build_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_build_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerBuildFail, "ft_sfx_tower_build_fail_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_build_fail_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerBuildFail, "ft_sfx_tower_build_fail_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_build_fail_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerUpgrade, "ft_sfx_tower_upgrade_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_upgrade_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerUpgrade, "ft_sfx_tower_upgrade_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_upgrade_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerUpgrade, "ft_sfx_tower_upgrade_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_upgrade_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerSell, "ft_sfx_tower_sell_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_sell_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerSell, "ft_sfx_tower_sell_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_sell_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.TowerSell, "ft_sfx_tower_sell_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_tower_sell_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalFire, "ft_sfx_normal_fire_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_fire_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalFire, "ft_sfx_normal_fire_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_fire_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalFire, "ft_sfx_normal_fire_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_fire_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalFire, "ft_sfx_normal_fire_04", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_fire_04.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalHit, "ft_sfx_normal_hit_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_hit_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalHit, "ft_sfx_normal_hit_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_hit_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.NormalHit, "ft_sfx_normal_hit_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_normal_hit_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.BlastFire, "ft_sfx_blast_fire_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_blast_fire_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.BlastFire, "ft_sfx_blast_fire_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_blast_fire_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.BlastFire, "ft_sfx_blast_fire_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_blast_fire_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.BlastHit, "ft_sfx_blast_hit_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_blast_hit_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.BlastHit, "ft_sfx_blast_hit_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_blast_hit_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.BlastHit, "ft_sfx_blast_hit_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_blast_hit_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostActivate, "ft_sfx_frost_activate_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_activate_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostActivate, "ft_sfx_frost_activate_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_activate_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostActivate, "ft_sfx_frost_activate_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_activate_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostPulse, "ft_sfx_frost_pulse_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_pulse_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostPulse, "ft_sfx_frost_pulse_02", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_pulse_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostPulse, "ft_sfx_frost_pulse_03", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_pulse_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.FrostLoop, "ft_sfx_frost_loop_01", "Assets/Audio/OriginalPack_20261023/SFX/Tower/ft_sfx_frost_loop_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.LightHit, "ft_sfx_light_hit_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_light_hit_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.LightHit, "ft_sfx_light_hit_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_light_hit_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.LightHit, "ft_sfx_light_hit_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_light_hit_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.LightDeath, "ft_sfx_light_death_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_light_death_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.LightDeath, "ft_sfx_light_death_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_light_death_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.LightDeath, "ft_sfx_light_death_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_light_death_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.WingHit, "ft_sfx_wing_hit_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_wing_hit_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.WingHit, "ft_sfx_wing_hit_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_wing_hit_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.WingHit, "ft_sfx_wing_hit_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_wing_hit_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.WingDeath, "ft_sfx_wing_death_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_wing_death_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.WingDeath, "ft_sfx_wing_death_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_wing_death_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.WingDeath, "ft_sfx_wing_death_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_wing_death_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.InsectHit, "ft_sfx_insect_hit_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_insect_hit_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.InsectHit, "ft_sfx_insect_hit_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_insect_hit_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.InsectHit, "ft_sfx_insect_hit_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_insect_hit_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.InsectDeath, "ft_sfx_insect_death_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_insect_death_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.InsectDeath, "ft_sfx_insect_death_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_insect_death_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.InsectDeath, "ft_sfx_insect_death_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_insect_death_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.HeavyHit, "ft_sfx_heavy_hit_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_heavy_hit_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.HeavyHit, "ft_sfx_heavy_hit_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_heavy_hit_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.HeavyHit, "ft_sfx_heavy_hit_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_heavy_hit_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.HeavyDeath, "ft_sfx_heavy_death_01", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_heavy_death_01.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.HeavyDeath, "ft_sfx_heavy_death_02", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_heavy_death_02.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.HeavyDeath, "ft_sfx_heavy_death_03", "Assets/Audio/OriginalPack_20261023/SFX/Enemy/ft_sfx_heavy_death_03.wav", ResBundle.AudioCombat),
            new AudioResourceRegistration(SoundCue.RoundStart, "ft_sfx_round_start_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_round_start_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.RoundStart, "ft_sfx_round_start_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_round_start_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.RoundClear, "ft_sfx_round_clear_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_round_clear_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.RoundClear, "ft_sfx_round_clear_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_round_clear_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.EnemyLeak, "ft_sfx_enemy_leak_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_enemy_leak_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.EnemyLeak, "ft_sfx_enemy_leak_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_enemy_leak_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.EnemyLeak, "ft_sfx_enemy_leak_03", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_enemy_leak_03.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.LowHp, "ft_sfx_low_hp_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_low_hp_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.LowHp, "ft_sfx_low_hp_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_low_hp_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.Pause, "ft_sfx_pause_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_pause_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.Pause, "ft_sfx_pause_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_pause_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.Resume, "ft_sfx_resume_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_resume_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.Resume, "ft_sfx_resume_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_resume_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.SpeedChange, "ft_sfx_speed_change_01", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_speed_change_01.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.SpeedChange, "ft_sfx_speed_change_02", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_speed_change_02.wav", ResBundle.AudioUI),
            new AudioResourceRegistration(SoundCue.SpeedChange, "ft_sfx_speed_change_03", "Assets/Audio/OriginalPack_20261023/SFX/Feedback/ft_sfx_speed_change_03.wav", ResBundle.AudioUI),
        };
        public static void Register(Dictionary<string, ResAddress> map)
        {
            foreach (var asset in Assets) map.Add(asset.key, new ResAddress(asset.bundle, asset.key, asset.path));
            map.Add(CatalogKey, new ResAddress(ResBundle.AudioRuntime, CatalogKey, RuntimePath + "/GameAudioCatalog.asset"));
            map.Add(MixerKey, new ResAddress(ResBundle.AudioRuntime, MixerKey, RuntimePath + "/GameAudioMixer.mixer"));
        }
    }
}
