using System;
using System.Collections.Generic;

namespace FTProject
{
    public static class LevelCheckpointValidator
    {
        public static bool IsCompatible(LevelSnapshot snapshot, LevelRatingProfile profile, int waveCount, out string reason)
        {
            reason = "Checkpoint incompatible: restart level";
            if (snapshot == null || !snapshot.valid || snapshot.formatVersion != 2 || snapshot.metrics == null || snapshot.ratingProfile == null || profile == null || !profile.IsValid) return false;
            var m = snapshot.metrics;
            if (snapshot.levelId != profile.id || snapshot.ratingProfile.versionKey != profile.versionKey || m.versionKey != profile.versionKey || m.profileRevision != profile.profileRevision || string.IsNullOrEmpty(m.runId) || m.debugOverride || !m.statisticsValid || !m.timingValid) return false;
            if (snapshot.roundCursor < 0 || snapshot.roundCursor > waveCount || snapshot.roundCursor != m.completedWaveCount || waveCount != profile.expectedWaveCount || m.expectedWaveCount != waveCount || m.expectedEnemyCount != profile.expectedEnemyCount) return false;
            if (snapshot.hp <= 0 || snapshot.maxHp <= 0 || snapshot.hp > snapshot.maxHp || snapshot.gold < 0 || m.hp != snapshot.hp || m.maxHp != snapshot.maxHp || m.killed < 0 || m.leaked < 0 || m.killed + m.leaked != m.successfulSpawned || m.successfulSpawned > m.expectedEnemyCount || m.bossLeaked < 0 || m.criticalLeaked < m.bossLeaked || m.criticalLeaked > m.leaked) return false;
            if (double.IsNaN(m.combatElapsedSeconds) || double.IsInfinity(m.combatElapsedSeconds) || m.combatElapsedSeconds < 0 || double.IsNaN(m.levelElapsedSeconds) || double.IsInfinity(m.levelElapsedSeconds) || m.levelElapsedSeconds < m.combatElapsedSeconds || (snapshot.roundCursor > 0 && m.combatElapsedMs <= 0)) return false;
            if (float.IsNaN(snapshot.autoNextRemainingSeconds) || float.IsInfinity(snapshot.autoNextRemainingSeconds) || snapshot.autoNextRemainingSeconds < 0f || (!snapshot.levelTimerStarted && m.levelElapsedSeconds > 0d)) return false;
            if (m.waves == null || m.waves.Count != snapshot.roundCursor || snapshot.towers == null) return false;
            int spawned = 0, killed = 0, leaked = 0, boss = 0, critical = 0;
            for (int i = 0; i < m.waves.Count; i++)
            {
                var w = m.waves[i];
                if (w == null || w.ordinal != i + 1 || w.expected <= 0 || w.successfulSpawned != w.expected || w.killed < 0 || w.leaked < 0 || w.killed + w.leaked != w.expected || w.combatEndSeconds < w.combatStartSeconds) return false;
                spawned += w.successfulSpawned; killed += w.killed; leaked += w.leaked; boss += w.bossLeaked; critical += w.criticalLeaked;
            }
            if (spawned != m.successfulSpawned || killed != m.killed || leaked != m.leaked || boss != m.bossLeaked || critical != m.criticalLeaked) return false;
            var cells = new HashSet<string>();
            foreach (var t in snapshot.towers) if (t == null || t.level < 1 || t.level > 3 || t.type < 1 || t.type > 3 || t.row < 0 || t.col < 0 || !t.HasValidRuntimeState() || !cells.Add(t.row + ":" + t.col)) return false;
            reason = null; return true;
        }
    }
}
