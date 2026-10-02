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
        /// <summary>星级 0~3；0 表示未通关</summary>
        public int stars;
        /// <summary>历史最好成绩（剩余生命），仅用于展示</summary>
        public int bestHpLeft;
        /// <summary>累计通关次数</summary>
        public int clearCount;

        public bool Cleared { get { return stars > 0; } }
    }

    /// <summary>玩家设置。目前只有音量与静音，后续加画质/语言时往这里加字段即可。</summary>
    [Serializable]
    public class GameSettings
    {
        public float volume = 0.8f;
        public bool muted;

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
        public const int CurrentVersion = 1;

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
