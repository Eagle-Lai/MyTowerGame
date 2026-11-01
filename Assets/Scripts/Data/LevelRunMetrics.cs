using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 单波运行统计。
    ///
    /// 【2026-11-01 变更】星级评分体系整体下线，这里只剩"这一波发生了什么"的原始账目：
    ///   原 `criticalLeaked`（精英/关键怪漏怪）是评级概念，随评级表一起删除；
    ///   `bossLeaked` 保留 —— 首领可以直接由 `EnemyData.Type == 5` 判定，不依赖评级表。
    /// </summary>
    [Serializable]
    public sealed class WaveRunMetrics
    {
        public int ordinal, expected, successfulSpawned, killed, leaked, bossLeaked;
        public int gold, hp, clearGold, peakAlive, spawnDeferredCount;
        /// <summary>本波击杀金合计。2026-10-29 起奖励为小数单价，这里随之为 float。</summary>
        public float killGold;
        public double combatStartSeconds, combatEndSeconds, levelEndSeconds;
    }

    /// <summary>
    /// 一局的运行账目：续局快照与结算界面共用同一份结构。
    ///
    /// 【为什么保留而不是跟评级一起删】
    ///   它是"局内进度落盘"（每波自动存档、重进接着打）的载荷，也是结算界面
    ///   战绩三项（生命 / 击杀 / 漏怪 / 用时）的数据源，与星级判定无关。
    ///
    /// 【删掉了什么】profileId / profileRevision / balanceRevision / ratingRevision /
    ///   planHash / versionKey / statisticsValid / timingValid / criticalLeaked ——
    ///   全部只服务于已下线的评级校验，留着只会让人以为还有一套评分在跑。
    /// </summary>
    [Serializable]
    public sealed class LevelRunMetrics
    {
        public string runId;
        public int expectedWaveCount, completedWaveCount, expectedEnemyCount, successfulSpawned, killed, leaked, bossLeaked, hp, maxHp;
        public bool victory, debugOverride;
        public double combatElapsedSeconds, levelElapsedSeconds;
        public List<WaveRunMetrics> waves = new List<WaveRunMetrics>();
        public long combatElapsedMs { get { return ToMilliseconds(combatElapsedSeconds); } }
        public long levelElapsedMs { get { return ToMilliseconds(levelElapsedSeconds); } }
        public static long ToMilliseconds(double seconds) { return double.IsNaN(seconds) || double.IsInfinity(seconds) ? -1 : (long)Math.Round(seconds * 1000d, MidpointRounding.AwayFromZero); }
        public LevelRunMetrics Clone() { return JsonUtility.FromJson<LevelRunMetrics>(JsonUtility.ToJson(this)); }
    }
}
