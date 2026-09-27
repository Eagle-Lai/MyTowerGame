using System;
using System.Collections.Generic;
using cfg;
using SimpleJSON;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 配置表总入口。
    ///
    /// 职责：
    ///   1. 经 ResLoader 从 config 包加载 8 张表的 JSON（TextAsset）
    ///   2. 启动时做一次自检（记录数 / 交叉引用），问题一次性汇总打印
    ///   3. 对外提供**不会抛异常**的访问器：找不到 id 时返回 null 并打印明确错误
    ///
    /// 【重要】Luban 生成的 TB* 类里 `Get(id)` 是 `_dataMap[key]`，
    /// 找不到会抛 KeyNotFoundException。本类统一改用 `GetOrDefault(id)`。
    ///
    /// 【单位口径】v2.1 起游戏逻辑统一使用「世界单位 / 格 / 秒」：
    ///   - 位置与距离：世界单位（1 世界单位 = 1 格，PPU=100）
    ///   - 速度：格/秒
    ///   - 时间：秒（表里多为毫秒，已在包装类里换算）
    /// </summary>
    public static class Configs
    {
        // ------------------------------------------------------------------
        // 表实例
        // ------------------------------------------------------------------

        public static TBEnemyData EnemyTable { get; private set; }
        public static TBTowerInfo TowerTable { get; private set; }
        public static TBBulletData BulletTable { get; private set; }
        public static TBEnemyList WaveTable { get; private set; }
        public static TBRoundData RoundTable { get; private set; }
        public static TBSceneInfo LevelTable { get; private set; }
        public static TBLevelMap LevelMapTable { get; private set; }
        public static TBGlobal GlobalTable { get; private set; }

        /// <summary>全局参数（单行）</summary>
        public static GlobalConfig Global { get; private set; }

        public static bool IsLoaded { get; private set; }

        /// <summary>加载失败的表名列表（供 UI 显示与自检）</summary>
        public static readonly List<string> FailedTables = new List<string>();

        private static readonly string[] ConfigKeys =
        {
            "tbenemydata", "tbtowerinfo", "tbbulletdata", "tbenemylist",
            "tbrounddata", "tbsceneinfo", "tblevelmap", "tbglobal"
        };

        // ------------------------------------------------------------------
        // 加载
        // ------------------------------------------------------------------

        /// <summary>
        /// 异步加载全部配置表。回调参数为 true 表示全部加载成功。
        /// 可重复调用（已加载则直接回调）。
        /// </summary>
        public static void LoadAsync(Action<bool> onDone)
        {
            if (IsLoaded)
            {
                if (onDone != null)
                {
                    onDone(true);
                }
                return;
            }

            // 先整包预热，顺带做一次"资源是否存在"的自检
            ResLoader.Instance.Preload(ConfigKeys, () =>
            {
                FailedTables.Clear();

                EnemyTable = LoadTable("tbenemydata", n => new TBEnemyData(n));
                TowerTable = LoadTable("tbtowerinfo", n => new TBTowerInfo(n));
                BulletTable = LoadTable("tbbulletdata", n => new TBBulletData(n));
                WaveTable = LoadTable("tbenemylist", n => new TBEnemyList(n));
                RoundTable = LoadTable("tbrounddata", n => new TBRoundData(n));
                LevelTable = LoadTable("tbsceneinfo", n => new TBSceneInfo(n));
                LevelMapTable = LoadTable("tblevelmap", n => new TBLevelMap(n));
                GlobalTable = LoadTable("tbglobal", n => new TBGlobal(n));

                // Global 是单行表，单独取
                if (GlobalTable != null)
                {
                    Global g = GlobalTable.GetOrDefault(1);
                    if (g == null && GlobalTable.DataList != null && GlobalTable.DataList.Count > 0)
                    {
                        g = GlobalTable.DataList[0];
                    }
                    if (g != null)
                    {
                        Global = new GlobalConfig(g);
                    }
                    else
                    {
                        Debug.LogError("[Config] TBGlobal 表为空，全局参数将全部使用代码内置默认值");
                        FailedTables.Add("tbglobal(空表)");
                    }
                }
                else
                {
                    FailedTables.Add("tbglobal");
                }

                bool ok = FailedTables.Count == 0;
                IsLoaded = true;

                LogSummary(ok);
                if (ok)
                {
                    ValidateCrossReferences();
                    ApplyGlobalSettings();
                }

                if (onDone != null)
                {
                    onDone(ok);
                }
            });
        }

        /// <summary>读取并解析单张表；失败返回 null 并记录</summary>
        private static T LoadTable<T>(string key, Func<JSONNode, T> ctor) where T : class
        {
            TextAsset ta = ResLoader.Instance.Load<TextAsset>(key);
            if (ta == null)
            {
                Debug.LogError(string.Format("[Config] 读取失败：{0}.json（详见上一条资源错误）", key));
                FailedTables.Add(key);
                return null;
            }
            if (string.IsNullOrEmpty(ta.text))
            {
                Debug.LogError(string.Format("[Config] {0}.json 内容为空", key));
                FailedTables.Add(key + "(空)");
                return null;
            }
            try
            {
                JSONNode node = JSONNode.Parse(ta.text);
                T table = ctor(node);
                if (table == null)
                {
                    FailedTables.Add(key + "(构造返回 null)");
                }
                return table;
            }
            catch (Exception ex)
            {
                Debug.LogError(string.Format("[Config] {0}.json 解析异常：{1}\n{2}", key, ex.Message, ex.StackTrace));
                FailedTables.Add(key + "(解析异常)");
                return null;
            }
        }

        private static void LogSummary(bool ok)
        {
            string summary = string.Format(
                "[Config] 配置加载{0}\n" +
                "  TBEnemyData  : {1} 条\n" +
                "  TBTowerInfo  : {2} 条\n" +
                "  TBBulletData : {3} 条\n" +
                "  TBEnemyList  : {4} 条\n" +
                "  TBRoundData  : {5} 条\n" +
                "  TBSceneInfo  : {6} 条\n" +
                "  TBLevelMap   : {7} 条\n" +
                "  TBGlobal     : {8} 条",
                ok ? "完成" : "完成（有失败项）",
                Count(EnemyTable), Count(TowerTable), Count(BulletTable), Count(WaveTable),
                Count(RoundTable), Count(LevelTable), Count(LevelMapTable), Count(GlobalTable));

            if (ok)
            {
                Debug.Log(summary);
            }
            else
            {
                Debug.LogError(summary + "\n  失败的表：" + string.Join("、", FailedTables.ToArray()));
            }
        }

        private static int Count(TBEnemyData t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBTowerInfo t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBBulletData t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBEnemyList t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBRoundData t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBSceneInfo t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBLevelMap t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }
        private static int Count(TBGlobal t) { return t != null && t.DataList != null ? t.DataList.Count : 0; }

        /// <summary>交叉引用自检：波次引用的怪物、关卡引用的回合/棋盘是否都存在</summary>
        private static void ValidateCrossReferences()
        {
            int problems = 0;
            System.Text.StringBuilder sb = new System.Text.StringBuilder();

            // 关卡 → 回合 → 波次 → 怪物
            foreach (SceneInfo lv in LevelTable.DataList)
            {
                if (LevelMapTable.GetOrDefault(lv.MapId) == null)
                {
                    sb.AppendLine(string.Format("  · 关卡 {0} 引用的棋盘 mapId={1} 不存在", lv.Id, lv.MapId));
                    problems++;
                }
                if (lv.RoundList == null || lv.RoundList.Count == 0)
                {
                    sb.AppendLine(string.Format("  · 关卡 {0} 的 RoundList 为空", lv.Id));
                    problems++;
                    continue;
                }
                foreach (int roundId in lv.RoundList)
                {
                    RoundData rd = RoundTable.GetOrDefault(roundId);
                    if (rd == null)
                    {
                        sb.AppendLine(string.Format("  · 关卡 {0} 引用的回合 id={1} 不存在", lv.Id, roundId));
                        problems++;
                        continue;
                    }
                    if (rd.EnemyIndexs == null || rd.EnemyIndexs.Count == 0)
                    {
                        sb.AppendLine(string.Format("  · 回合 {0} 的 EnemyIndexs(波次列表) 为空", roundId));
                        problems++;
                        continue;
                    }
                    foreach (int waveId in rd.EnemyIndexs)
                    {
                        EnemyList wg = WaveTable.GetOrDefault(waveId);
                        if (wg == null)
                        {
                            sb.AppendLine(string.Format("  · 回合 {0} 引用的波次 id={1} 不存在", roundId, waveId));
                            problems++;
                            continue;
                        }
                        if (wg.EnemyIndexs == null)
                        {
                            continue;
                        }
                        foreach (int enemyId in wg.EnemyIndexs)
                        {
                            if (EnemyTable.GetOrDefault(enemyId) == null)
                            {
                                sb.AppendLine(string.Format("  · 波次 {0} 引用的怪物 id={1} 不存在", waveId, enemyId));
                                problems++;
                            }
                        }
                    }
                }
            }

            // 塔 → 子弹
            foreach (TowerInfo tw in TowerTable.DataList)
            {
                if (BulletTable.GetOrDefault(tw.BulletId) == null)
                {
                    sb.AppendLine(string.Format("  · 塔 {0}(lv{1}) 引用的子弹 bulletId={2} 不存在",
                        tw.Id, tw.Level, tw.BulletId));
                    problems++;
                }
            }

            if (problems > 0)
            {
                Debug.LogWarning(string.Format(
                    "[Config] 交叉引用自检发现 {0} 处问题（不影响启动，但运行到对应内容时会缺数据）：\n{1}",
                    problems, sb.ToString()));
            }
            else
            {
                Debug.Log("[Config] 交叉引用自检通过。");
            }
        }

        private static void ApplyGlobalSettings()
        {
            if (Global != null)
            {
                Application.targetFrameRate = Global.TargetFrameRate;
            }
        }

        // ------------------------------------------------------------------
        // 访问器（全部不抛异常，找不到就返回 null + 明确日志）
        // ------------------------------------------------------------------

        public static EnemyConfig GetEnemy(int id)
        {
            EnemyData d = EnemyTable != null ? EnemyTable.GetOrDefault(id) : null;
            if (d == null)
            {
                Debug.LogError(string.Format("[Config] TBEnemyData 中找不到 id={0}", id));
                return null;
            }
            return new EnemyConfig(d);
        }

        public static TowerConfig GetTower(int id)
        {
            TowerInfo t = TowerTable != null ? TowerTable.GetOrDefault(id) : null;
            if (t == null)
            {
                Debug.LogError(string.Format("[Config] TBTowerInfo 中找不到 id={0}", id));
                return null;
            }
            return new TowerConfig(t);
        }

        /// <summary>取某类塔的指定等级（M0 只用 level=1）</summary>
        public static TowerConfig GetTowerByTypeAndLevel(int type, int level)
        {
            if (TowerTable == null || TowerTable.DataList == null)
            {
                Debug.LogError("[Config] TBTowerInfo 未加载");
                return null;
            }
            foreach (TowerInfo t in TowerTable.DataList)
            {
                if (t.Type == type && t.Level == level)
                {
                    return new TowerConfig(t);
                }
            }
            Debug.LogError(string.Format("[Config] TBTowerInfo 中找不到 type={0} level={1} 的塔", type, level));
            return null;
        }

        public static BulletConfig GetBullet(int id)
        {
            BulletData b = BulletTable != null ? BulletTable.GetOrDefault(id) : null;
            if (b == null)
            {
                Debug.LogError(string.Format("[Config] TBBulletData 中找不到 id={0}", id));
                return null;
            }
            return new BulletConfig(b);
        }

        public static LevelConfig GetLevel(int id)
        {
            SceneInfo s = LevelTable != null ? LevelTable.GetOrDefault(id) : null;
            if (s == null)
            {
                Debug.LogError(string.Format("[Config] TBSceneInfo 中找不到关卡 id={0}", id));
                return null;
            }
            return new LevelConfig(s);
        }

        /// <summary>取某关卡对应的棋盘布局（经 LevelConfig.MapId 关联）</summary>
        public static LevelMapConfig GetLevelMapOfLevel(int levelId)
        {
            LevelConfig lv = GetLevel(levelId);
            if (lv == null)
            {
                return null;
            }
            LevelMap m = LevelMapTable != null ? LevelMapTable.GetOrDefault(lv.MapId) : null;
            if (m == null)
            {
                Debug.LogError(string.Format("[Config] TBLevelMap 中找不到 id={0}（关卡 {1} 引用）", lv.MapId, levelId));
                return null;
            }
            LevelMapConfig cfg = new LevelMapConfig(m);
            string err = cfg.Validate();
            if (!string.IsNullOrEmpty(err))
            {
                Debug.LogError(string.Format("[Config] TBLevelMap id={0} 格式非法：{1}", m.Id, err));
            }
            return cfg;
        }

        public static RoundConfig GetRound(int id)
        {
            RoundData r = RoundTable != null ? RoundTable.GetOrDefault(id) : null;
            if (r == null)
            {
                Debug.LogError(string.Format("[Config] TBRoundData 中找不到 id={0}", id));
                return null;
            }
            return new RoundConfig(r);
        }

        public static WaveGroupConfig GetWaveGroup(int id)
        {
            EnemyList w = WaveTable != null ? WaveTable.GetOrDefault(id) : null;
            if (w == null)
            {
                Debug.LogError(string.Format("[Config] TBEnemyList 中找不到 id={0}", id));
                return null;
            }
            return new WaveGroupConfig(w);
        }

        /// <summary>取第一个关卡 id（用于 M0 直接开局）</summary>
        public static int GetFirstLevelId()
        {
            if (LevelTable == null || LevelTable.DataList == null || LevelTable.DataList.Count == 0)
            {
                Debug.LogError("[Config] TBSceneInfo 为空，无法确定关卡");
                return 0;
            }
            return LevelTable.DataList[0].Id;
        }
    }
}
