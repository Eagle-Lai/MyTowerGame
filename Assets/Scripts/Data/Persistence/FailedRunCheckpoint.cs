using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>失败续局里的一座塔：只记身份（格位/类型/等级），不记瞄准、冷却、后坐等瞬态。</summary>
    [Serializable]
    public sealed class FailedRunTower
    {
        public int row;
        public int col;
        public int type;
        public int level;
    }

    /// <summary>
    /// 「失败后继续」的续局存档（2026-10-29 用户需求）。
    ///
    /// ==================================================================
    /// 【它和 LevelSnapshot 的分工 —— 为什么不复用那一份】
    ///   LevelSnapshot 是"退出/回合边界"的续玩存档，读取时被
    ///   <see cref="LevelCheckpointValidator"/> 用 versionKey
    ///   （profileId|balanceRevision|ratingRevision|planHash）严格校验：
    ///   **只要改了配置表，整份快照就作废**。这条规则对星级评定是对的
    ///   （跨配置的成绩不可比），但调试/试玩场景恰恰相反 ——
    ///   玩家失败 → 改数值 → 想从失败的那一波重来。旧快照在
    ///   SaveManager.EnsureRatingVersion 里会被直接清空，正好把这条路堵死。
    ///
    ///   所以这里单独存一份**不校验配置版本**的续局点，落在 kv_store
    ///   （key = checkpoint/failed-run），因此既扛得住改表，也扛得住重启。
    ///
    /// 【为什么只恢复到"失败那一波的开头"】
    ///   半途恢复要记录每只怪的位置/血量/飞行进度、每座塔的冷却相位与弹道，
    ///   收益极低而失配风险极高。波次边界是唯一自洽的时刻：
    ///   场上无怪、金币与塔已结算。用户要的"从失败的关卡继续"正好落在这里。
    ///
    /// 【代价：不计星】
    ///   用这份存档继续的局会把 LevelRunMetrics.statisticsValid 置 false
    ///   （跨配置的击杀/漏怪统计不可能满足评级口径），因此通关不记星，
    ///   只用于验证数值。这一点在续局时会用 Tips 明确告诉玩家。
    /// ==================================================================
    /// </summary>
    [Serializable]
    public sealed class FailedRunCheckpoint
    {
        public const int CurrentFormat = 1;

        public int formatVersion = CurrentFormat;
        public int levelId;
        /// <summary>失败时已经打完的波数（续局从 completedWaves + 1 波开始）</summary>
        public int completedWaves;
        /// <summary>失败的那一波序号（从 1 计）</summary>
        public int failedWave;
        public int gold;
        public int hp;
        public int maxHp;
        public double combatElapsedSeconds;
        public double levelElapsedSeconds;
        /// <summary>写入时的配置版本号，只用于日志排查，**不参与兼容性校验**</summary>
        public string configVersionKey;
        public long savedAtUnix;
        public List<FailedRunTower> towers = new List<FailedRunTower>();

        public bool IsValid()
        {
            return formatVersion == CurrentFormat
                && levelId > 0
                && completedWaves >= 0
                && failedWave >= 1
                && failedWave == completedWaves + 1
                && maxHp > 0
                && hp > 0
                && hp <= maxHp
                && gold >= 0
                && !double.IsNaN(combatElapsedSeconds)
                && !double.IsNaN(levelElapsedSeconds)
                && towers != null;
        }

        public string ToJson()
        {
            return JsonUtility.ToJson(this);
        }

        public static FailedRunCheckpoint FromJson(string json)
        {
            if (string.IsNullOrEmpty(json))
            {
                return null;
            }
            try
            {
                return JsonUtility.FromJson<FailedRunCheckpoint>(json);
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 失败续局存档解析失败，已忽略：" + ex.Message);
                return null;
            }
        }

        public string Describe()
        {
            return string.Format("关卡 {0}｜死于第 {1} 波｜已完成 {2} 波｜金币 {3}｜生命 {4}/{5}｜塔 {6} 座",
                levelId, failedWave, completedWaves, gold, hp, maxHp, towers != null ? towers.Count : 0);
        }
    }
}
