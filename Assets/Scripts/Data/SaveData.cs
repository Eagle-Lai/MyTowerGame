using System;
using System.Collections.Generic;

namespace FTProject
{
    /// <summary>
    /// 单个关卡的进度。
    /// 【为什么用 public 字段而不是属性】Unity 的 JsonUtility **只序列化字段**，
    /// 属性会被静默忽略 —— 那样存出来的 json 永远是空的，而且不报错。
    /// </summary>
    [Serializable]
    public class LevelProgress
    {
        public int levelId;
        /// <summary>当前完整评级版本的星级 0~5；0 表示本版尚未评定。</summary>
        public int stars;
        /// <summary>历史最好成绩（剩余生命），仅用于展示</summary>
        public int bestHpLeft;
        /// <summary>累计通关次数</summary>
        public int clearCount;
        /// <summary>
        /// 历史**最快**通关用时（游戏内毫秒，0 = 尚无记录）。
        /// 【为什么是游戏内时间】见 GameClock.LevelElapsedSec：它是确定性的、跨倍速可比，
        /// 作为"最佳记录"才公平；用墙钟时间会让高倍速玩家的记录失真。
        /// </summary>
        public int bestTimeMs;
        public int bestCombatTimeMs;
        public string ratingVersionKey;
        public LevelRatingResult bestRating;
        public List<LegacyLevelProgress> legacy = new List<LegacyLevelProgress>();
        public List<string> committedRunIds = new List<string>();
        public bool Cleared { get { return stars > 0 || clearCount > 0 || (legacy != null && legacy.Exists(p => p.stars > 0 || p.clearCount > 0)); } }
    }

    [Serializable]
    public class LegacyLevelProgress
    {
        public string versionKey;
        public int stars, bestTimeMs, bestCombatTimeMs, bestHpLeft, clearCount;
        public LevelRatingResult bestRating;
    }

    /// <summary>玩家设置。目前只有音量、静音、语言。</summary>
    [Serializable]
    public class GameSettings
    {
        public float volume = 0.8f;
        public bool muted;

        /// <summary>
        /// 玩家选择的语言码（如 "en" / "zh-Hans" / "zh-Hant"）。
        /// 空字符串 = 尚无显式选择，用 LocalizationSettings.defaultLanguage。
        /// 【为什么存字符串码而不是枚举 int】将来在枚举中间插语言会让老存档的 int 含义漂移。
        /// </summary>
        public string language = "";

        public void Clamp()
        {
            if (volume < 0f) volume = 0f;
            if (volume > 1f) volume = 1f;
        }
    }

    /// <summary>局内快照里的单座塔。</summary>
    [Serializable]
    public class TowerSnapshot
    {
        public int row;
        public int col;
        public int type;
        public int level;
        public bool runtimeStateSaved;
        public float fireTimer, searchTimer, recoilTimer, auraPulseTimer;
        public UnityEngine.Vector2 lastDirection;
        public bool barrelPoseSaved, barrelBaseCached;
        public UnityEngine.Vector3 barrelLocalPosition, barrelBasePosition;
        public UnityEngine.Quaternion barrelLocalRotation;

        public bool HasValidRuntimeState()
        {
            if (!runtimeStateSaved || !Finite(fireTimer) || fireTimer < 0f || !Finite(searchTimer) || searchTimer < 0f || !Finite(recoilTimer) || recoilTimer < 0f || !Finite(auraPulseTimer) || auraPulseTimer < 0f || !Finite(lastDirection.x) || !Finite(lastDirection.y)) return false;
            if (!barrelPoseSaved) return !barrelBaseCached;
            if (!Finite(barrelLocalPosition) || !Finite(barrelBasePosition) || !Finite(barrelLocalRotation.x) || !Finite(barrelLocalRotation.y) || !Finite(barrelLocalRotation.z) || !Finite(barrelLocalRotation.w)) return false;
            float norm = barrelLocalRotation.x * barrelLocalRotation.x + barrelLocalRotation.y * barrelLocalRotation.y + barrelLocalRotation.z * barrelLocalRotation.z + barrelLocalRotation.w * barrelLocalRotation.w;
            return Finite(norm) && System.Math.Abs(norm - 1f) < 0.001f;
        }
        private static bool Finite(float value) { return !float.IsNaN(value) && !float.IsInfinity(value); }
        private static bool Finite(UnityEngine.Vector3 value) { return Finite(value.x) && Finite(value.y) && Finite(value.z); }
    }

    /// <summary>
    /// 局内快照：支持"退出后继续"。
    /// 【为什么不存整个棋盘】棋盘完全由 TBLevelMap 决定，存 levelId 就能重建；
    /// 真正会变、且重建不出来的只有"玩家干了什么"：花了多少钱、掉了多少血、建了哪些塔、打到第几回合。
    /// </summary>
    [Serializable]
    public class LevelSnapshot
    {
        public bool valid;
        public int levelId;
        /// <summary>下一个要打的回合在 RoundList 里的下标</summary>
        public int roundCursor;
        public int gold;
        public int hp;
        public int maxHp;
        public List<TowerSnapshot> towers = new List<TowerSnapshot>();
        public int formatVersion;
        public LevelRatingProfile ratingProfile;
        public LevelRunMetrics metrics;
        public bool levelTimerStarted;
        public float autoNextRemainingSeconds;
    }

    /// <summary>
    /// 存档根对象。
    /// 【version 是干什么的】将来改了字段语义时，老存档必须能被识别并安全丢弃，
    /// 而不是让游戏在读到一个"看起来能解析、其实语义不同"的 json 后行为错乱。
    /// </summary>
    [Serializable]
    public class SaveData
    {
        /// <summary>当前存档格式版本。改动字段语义时必须 +1。</summary>
        public const int CurrentVersion = 2;

        public int version = CurrentVersion;
        public List<LevelProgress> levels = new List<LevelProgress>();
        public GameSettings settings = new GameSettings();
        public LevelSnapshot snapshot = new LevelSnapshot();

        public LevelProgress GetOrCreate(int levelId)
        {
            for (int i = 0; i < levels.Count; i++)
            {
                if (levels[i] != null && levels[i].levelId == levelId)
                {
                    return levels[i];
                }
            }
            LevelProgress p = new LevelProgress();
            p.levelId = levelId;
            levels.Add(p);
            return p;
        }

        public LevelProgress Find(int levelId)
        {
            for (int i = 0; i < levels.Count; i++)
            {
                if (levels[i] != null && levels[i].levelId == levelId)
                {
                    return levels[i];
                }
            }
            return null;
        }
    }
}
