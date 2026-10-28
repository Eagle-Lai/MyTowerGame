using System;
using UnityEngine;

namespace FTProject
{
    public enum SoundCue
    {
        Menu, Prepare, Battle, Pressure, Victory, Defeat, Rating,
        UiClick, UiConfirm, UiBack, UiInvalid, UiToggle,
        TowerSelect, TowerBuild, TowerBuildFail, TowerUpgrade, TowerSell,
        NormalFire, NormalHit, BlastFire, BlastHit, FrostActivate, FrostPulse, FrostLoop,
        LightHit, LightDeath, WingHit, WingDeath, InsectHit, InsectDeath, HeavyHit, HeavyDeath,
        RoundStart, RoundClear, EnemyLeak, LowHp, Pause, Resume, SpeedChange
    }

    [Serializable]
    public sealed class AudioCueDefinition
    {
        public SoundCue cue;
        public string[] logicalNames;
        [Range(0, 1)] public float gain = .5f;
        public float cooldown = .05f;
        public int priority = 50;
        public int maxConcurrent = 3;
        public bool gameplay;
    }

    /// <summary>Semantic policy only. Addresses remain in ResTable; no direct clips causing eager BGM loads.</summary>
    public sealed class AudioCatalog : ScriptableObject
    {
        public AudioCueDefinition[] cues;
        public int shortVoices = 20;
        public int loopVoices = 4;
        public float fadeSeconds = .8f;
        public float pressureEnter = .3f;
        public float pressureExit = .4f;
        public float musicMinResidence = 8f;
        public float pausedMusicGain = .4f;
        public float enemyHitCooldown = .2f;
        public float frostPulseCooldown = .5f;
    }
}
