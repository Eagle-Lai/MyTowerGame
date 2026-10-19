using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    [Serializable]
    public sealed class LevelRatingProfile
    {
        public int id, difficultyTier, expectedWaveCount, expectedEnemyCount;
        public string profileId, profileRevision, balanceRevision, ratingRevision, planHash, runtimeContentHash;
        public string calibrationStatus;
        public int twoStarHpPermille = 500, threeStarHpPermille = 750, fourStarHpPermille = 900;
        public int maxFourStarLeaks = 2, fourStarTimePermille = 1250, parCombatTimeMs;
        public List<int> bossVariantIds = new List<int>(), criticalVariantIds = new List<int>();
        public string versionKey { get { return string.Join("|", profileId, balanceRevision, ratingRevision, planHash); } }
        // The exact count is verified against this level's RoundList by Configs;
        // completed inventory is then checked again by the sole evaluator below.
        public bool IsValid { get { return id > 0 && expectedWaveCount > 0 && expectedEnemyCount > 0 && parCombatTimeMs > 0 && !string.IsNullOrEmpty(profileId) && !string.IsNullOrEmpty(profileRevision) && !string.IsNullOrEmpty(balanceRevision) && !string.IsNullOrEmpty(ratingRevision) && !string.IsNullOrEmpty(planHash) && twoStarHpPermille > 0 && twoStarHpPermille <= threeStarHpPermille && threeStarHpPermille <= fourStarHpPermille && fourStarHpPermille <= 1000 && fourStarTimePermille >= 1000 && maxFourStarLeaks >= 0; } }
        public LevelRatingProfile Clone() { return JsonUtility.FromJson<LevelRatingProfile>(JsonUtility.ToJson(this)); }
        public static LevelRatingProfile From(cfg.LevelRating r)
        {
            if (r == null) return null;
            return new LevelRatingProfile { id = r.Id, difficultyTier = r.DifficultyTier, profileId = r.ProfileId, profileRevision = r.ProfileRevision, expectedWaveCount = r.ExpectedWaveCount, expectedEnemyCount = r.ExpectedEnemyCount, twoStarHpPermille = r.TwoStarHpPermille, threeStarHpPermille = r.ThreeStarHpPermille, fourStarHpPermille = r.FourStarHpPermille, maxFourStarLeaks = r.MaxFourStarLeaks, fourStarTimePermille = r.FourStarTimePermille, parCombatTimeMs = r.ParCombatTimeMs, bossVariantIds = new List<int>(r.BossVariantIds), criticalVariantIds = new List<int>(r.CriticalVariantIds), balanceRevision = r.BalanceRevision, ratingRevision = r.RatingRevision, planHash = r.PlanHash, runtimeContentHash = r.RuntimeContentHash, calibrationStatus = r.CalibrationStatus };
        }
    }

    [Serializable]
    public sealed class WaveRunMetrics
    {
        public int ordinal, expected, successfulSpawned, killed, leaked, bossLeaked, criticalLeaked;
        public int gold, hp, killGold, clearGold, peakAlive, spawnDeferredCount;
        public double combatStartSeconds, combatEndSeconds, levelEndSeconds;
    }

    [Serializable]
    public sealed class LevelRunMetrics
    {
        public string runId, profileId, profileRevision, balanceRevision, ratingRevision, planHash;
        public int expectedWaveCount, completedWaveCount, expectedEnemyCount, successfulSpawned, killed, leaked, bossLeaked, criticalLeaked, hp, maxHp;
        public bool victory, debugOverride, statisticsValid, timingValid;
        public double combatElapsedSeconds, levelElapsedSeconds;
        public List<WaveRunMetrics> waves = new List<WaveRunMetrics>();
        public long combatElapsedMs { get { return ToMilliseconds(combatElapsedSeconds); } }
        public long levelElapsedMs { get { return ToMilliseconds(levelElapsedSeconds); } }
        public string versionKey { get { return string.Join("|", profileId, balanceRevision, ratingRevision, planHash); } }
        public static long ToMilliseconds(double seconds) { return double.IsNaN(seconds) || double.IsInfinity(seconds) ? -1 : (long)Math.Round(seconds * 1000d, MidpointRounding.AwayFromZero); }
        public LevelRunMetrics Clone() { return JsonUtility.FromJson<LevelRunMetrics>(JsonUtility.ToJson(this)); }
    }

    [Serializable]
    public sealed class LevelRatingResult
    {
        public int stars;
        public bool valid, victory, fiveStarConditions, fourStarConditions, threeStarConditions, twoStarConditions;
        public string[] reasons;
        public string versionKey;
        public LevelRunMetrics metrics;
        public LevelRatingProfile profile;
    }

    /// <summary>The sole rating authority. Invalid or debugging evidence is never a formal clear.</summary>
    public static class LevelRatingEvaluator
    {
        public const int MaxStars = 5;
        public static LevelRatingResult Evaluate(LevelRatingProfile profile, LevelRunMetrics metrics)
        {
            var r = new LevelRatingResult { profile = profile != null ? profile.Clone() : null, metrics = metrics != null ? metrics.Clone() : null, versionKey = profile != null ? profile.versionKey : "", victory = metrics != null && metrics.victory };
            var reasons = new List<string>();
            if (profile == null || !profile.IsValid) reasons.Add("Rating config missing or invalid");
            if (metrics == null) reasons.Add("Invalid rating evidence");
            else
            {
                if (!metrics.victory || metrics.hp <= 0) reasons.Add("Defense failed");
                if (metrics.debugOverride) reasons.Add("Debug result: progress not saved");
                if (!metrics.statisticsValid || metrics.maxHp <= 0 || metrics.hp > metrics.maxHp || metrics.killed < 0 || metrics.leaked < 0 || metrics.bossLeaked < 0 || metrics.criticalLeaked < metrics.bossLeaked || metrics.criticalLeaked > metrics.leaked || string.IsNullOrEmpty(metrics.runId)) reasons.Add("Invalid rating evidence");
                if (!metrics.timingValid || metrics.combatElapsedMs <= 0 || metrics.levelElapsedMs < metrics.combatElapsedMs || double.IsNaN(metrics.combatElapsedSeconds) || double.IsInfinity(metrics.combatElapsedSeconds)) reasons.Add("Invalid combat timer");
                if (profile != null)
                {
                    if (metrics.versionKey != profile.versionKey || metrics.profileRevision != profile.profileRevision) reasons.Add("Rating version mismatch");
                    if (metrics.completedWaveCount != profile.expectedWaveCount || metrics.expectedWaveCount != profile.expectedWaveCount) reasons.Add("Incomplete waves");
                    if (metrics.expectedEnemyCount != profile.expectedEnemyCount || metrics.successfulSpawned != profile.expectedEnemyCount) reasons.Add("Spawn count mismatch");
                    if ((long)metrics.killed + metrics.leaked != metrics.successfulSpawned) reasons.Add("Enemy accounting mismatch");
                    int waveSpawned = 0, waveKilled = 0, waveLeaked = 0, waveBoss = 0, waveCritical = 0;
                    bool wavesValid = metrics.waves != null && metrics.waves.Count == profile.expectedWaveCount;
                    if (wavesValid)
                    {
                        for (int i = 0; i < metrics.waves.Count; i++)
                        {
                            var w = metrics.waves[i];
                            if (w == null || w.ordinal != i + 1 || w.expected <= 0 || w.successfulSpawned != w.expected || w.killed < 0 || w.leaked < 0 || w.killed + w.leaked != w.expected || w.bossLeaked < 0 || w.criticalLeaked < w.bossLeaked || w.criticalLeaked > w.leaked) { wavesValid = false; break; }
                            waveSpawned += w.successfulSpawned; waveKilled += w.killed; waveLeaked += w.leaked; waveBoss += w.bossLeaked; waveCritical += w.criticalLeaked;
                        }
                    }
                    if (!wavesValid || waveSpawned != metrics.successfulSpawned || waveKilled != metrics.killed || waveLeaked != metrics.leaked || waveBoss != metrics.bossLeaked || waveCritical != metrics.criticalLeaked) reasons.Add("Invalid rating evidence");
                }
            }
            r.valid = reasons.Count == 0;
            if (!r.valid) { r.reasons = reasons.ToArray(); return r; }
            long hp = metrics.hp, maxHp = metrics.maxHp, time = metrics.combatElapsedMs;
            r.fiveStarConditions = hp == maxHp && metrics.leaked == 0 && metrics.killed == profile.expectedEnemyCount && time <= profile.parCombatTimeMs;
            r.fourStarConditions = 1000L * hp >= (long)profile.fourStarHpPermille * maxHp && metrics.leaked <= profile.maxFourStarLeaks && metrics.criticalLeaked == 0 && 1000L * time <= (long)profile.fourStarTimePermille * profile.parCombatTimeMs;
            r.threeStarConditions = 1000L * hp >= (long)profile.threeStarHpPermille * maxHp && metrics.bossLeaked == 0;
            r.twoStarConditions = 1000L * hp >= (long)profile.twoStarHpPermille * maxHp;
            r.stars = r.fiveStarConditions ? 5 : r.fourStarConditions ? 4 : r.threeStarConditions ? 3 : r.twoStarConditions ? 2 : 1;
            if (hp != maxHp) reasons.Add("Full health required");
            if (metrics.leaked != 0) reasons.Add("No leaks required");
            if (metrics.killed != profile.expectedEnemyCount) reasons.Add("Defeat every planned enemy");
            if (time > profile.parCombatTimeMs) reasons.Add("Five-star combat time exceeded");
            if (1000L * hp < (long)profile.fourStarHpPermille * maxHp) reasons.Add("Four-star health required");
            if (metrics.leaked > profile.maxFourStarLeaks) reasons.Add("Four-star leak limit exceeded");
            if (metrics.criticalLeaked > 0) reasons.Add("Critical enemy leaked");
            if (1000L * time > (long)profile.fourStarTimePermille * profile.parCombatTimeMs) reasons.Add("Four-star combat time exceeded");
            if (1000L * hp < (long)profile.threeStarHpPermille * maxHp) reasons.Add("Three-star health required");
            if (metrics.bossLeaked > 0) reasons.Add("Boss leaked");
            if (!r.twoStarConditions) reasons.Add("Two-star health required");
            r.reasons = reasons.ToArray();
            return r;
        }
    }
}
