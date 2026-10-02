using System;
using System.IO;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 存档管理器（M3-3）：关卡解锁与星级、玩家设置、局内快照。
    ///
    /// 【硬约束：与编辑器 API 完全解耦】
    ///   设计文档明确要求本类不得引用 UnityEditor —— 否则打包必炸
    ///   （本项目历史上就踩过 `JsonDataManager` 顶层 using UnityEditor 的坑）。
    ///   所以只允许用：Application.persistentDataPath + System.IO + JsonUtility。
    ///
    /// 【失败时的行为：一律当作"没有存档"，绝不抛异常】
    ///   存档损坏、路径只读、磁盘满 —— 这些都不该让玩家连游戏都进不去。
    ///   所有 IO 都在 try/catch 里，失败只打一条 Warning。
    ///
    /// 【什么时候写盘】改设置后立刻写；关卡结果与快照也立刻写。
    ///   本游戏的存档极小（几 KB），没必要做延迟批量写。
    /// </summary>
    public class SaveManager : BaseManager<SaveManager>
    {
        private const string FileName = "freetower_save.json";

        private SaveData _data;
        private bool _loaded;

        /// <summary>存档文件完整路径（排查问题时打印它最快）</summary>
        public static string FilePath
        {
            get { return Path.Combine(Application.persistentDataPath, FileName); }
        }

        public SaveData Data
        {
            get
            {
                EnsureLoaded();
                return _data;
            }
        }

        // ------------------------------------------------------------------
        // 读 / 写
        // ------------------------------------------------------------------

        private void EnsureLoaded()
        {
            if (_loaded)
            {
                return;
            }
            _loaded = true;
            _data = LoadFromDisk();
        }

        private static SaveData LoadFromDisk()
        {
            try
            {
                string path = FilePath;
                if (!File.Exists(path))
                {
                    return new SaveData();
                }
                string json = File.ReadAllText(path);
                if (string.IsNullOrEmpty(json))
                {
                    return new SaveData();
                }
                SaveData d = JsonUtility.FromJson<SaveData>(json);
                if (d == null)
                {
                    Debug.LogWarning("[Save] 存档解析为 null，按新档处理：" + path);
                    return new SaveData();
                }
                // 版本不符 → 丢弃旧档。宁可让玩家重打，也不要带着错误的语义继续跑。
                if (d.version != SaveData.CurrentVersion)
                {
                    Debug.LogWarning(string.Format(
                        "[Save] 存档版本 {0} != 当前 {1}，已重置为新档", d.version, SaveData.CurrentVersion));
                    return new SaveData();
                }
                // 字段可能是 null（手改过 json / 老版本缺字段），补齐再返回
                if (d.levels == null) d.levels = new System.Collections.Generic.List<LevelProgress>();
                if (d.settings == null) d.settings = new GameSettings();
                if (d.snapshot == null) d.snapshot = new LevelSnapshot();
                if (d.snapshot.towers == null) d.snapshot.towers = new System.Collections.Generic.List<TowerSnapshot>();
                d.settings.Clamp();
                return d;
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 读档失败，按新档处理：" + ex.Message + "\n  路径：" + FilePath);
                return new SaveData();
            }
        }

        /// <summary>把内存里的存档写盘。失败只警告，不影响游戏继续。</summary>
        public void Save()
        {
            EnsureLoaded();
            try
            {
                string json = JsonUtility.ToJson(_data, true);
                File.WriteAllText(FilePath, json);
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 写档失败：" + ex.Message + "\n  路径：" + FilePath);
            }
        }

        /// <summary>清空存档（设置界面用）。会同时删掉磁盘文件。</summary>
        public void ResetAll()
        {
            _data = new SaveData();
            _loaded = true;
            try
            {
                if (File.Exists(FilePath))
                {
                    File.Delete(FilePath);
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 删除存档失败：" + ex.Message);
            }
        }

        // ------------------------------------------------------------------
        // 关卡解锁与星级
        // ------------------------------------------------------------------

        /// <summary>
        /// 关卡是否已解锁。
        /// 【规则】第 1 关永远开放；其余关卡需要**前一关至少通关一次**。
        /// 用"关卡 id 排序后的前一个"而不是 id-1，这样以后中间插关卡也不会把解锁链弄断。
        /// </summary>
        public bool IsUnlocked(int levelId)
        {
            EnsureLoaded();
            int prev = PreviousLevelId(levelId);
            if (prev <= 0)
            {
                return true;   // 第一关
            }
            LevelProgress p = _data.Find(prev);
            return p != null && p.Cleared;
        }

        /// <summary>取"排序上紧邻的前一关"的 id；没有则返回 0。</summary>
        private int PreviousLevelId(int levelId)
        {
            if (Configs.LevelTable == null || Configs.LevelTable.DataList == null)
            {
                return levelId <= 1 ? 0 : levelId - 1;
            }
            int best = 0;
            for (int i = 0; i < Configs.LevelTable.DataList.Count; i++)
            {
                cfg.SceneInfo s = Configs.LevelTable.DataList[i];
                if (s != null && s.Id < levelId && s.Id > best)
                {
                    best = s.Id;
                }
            }
            return best;
        }

        public int GetStars(int levelId)
        {
            EnsureLoaded();
            LevelProgress p = _data.Find(levelId);
            return p != null ? p.stars : 0;
        }

        /// <summary>关卡通关结算：更新星级（只升不降）与累计次数。</summary>
        public void RecordClear(int levelId, int stars, int hpLeft)
        {
            EnsureLoaded();
            LevelProgress p = _data.GetOrCreate(levelId);
            if (stars > p.stars)
            {
                p.stars = Mathf.Clamp(stars, 0, 3);
            }
            if (hpLeft > p.bestHpLeft)
            {
                p.bestHpLeft = hpLeft;
            }
            p.clearCount++;
            // 通关即视为本局结束，快照作废（否则下次进关会莫名其妙"接着上一局"）
            ClearSnapshot(false);
            Save();
        }

        /// <summary>
        /// 星级评定。
        /// 【为什么这样定】塔防的"打得好"最直观的度量就是"漏了多少怪"：
        /// 一滴血没掉 = 3 星；掉不超过一半 = 2 星；通关即可 = 1 星。
        /// 放在这里而不是结算界面里，是为了让"什么算 3 星"只有一处定义。
        /// </summary>
        public static int EvaluateStars(int hpLeft, int maxHp)
        {
            if (maxHp <= 0)
            {
                return 1;
            }
            if (hpLeft >= maxHp)
            {
                return 3;
            }
            if (hpLeft * 2 >= maxHp)
            {
                return 2;
            }
            return 1;
        }

        /// <summary>已通关的关卡数（关卡选择界面顶部汇总用）</summary>
        public int ClearedCount
        {
            get
            {
                EnsureLoaded();
                int n = 0;
                for (int i = 0; i < _data.levels.Count; i++)
                {
                    if (_data.levels[i] != null && _data.levels[i].Cleared)
                    {
                        n++;
                    }
                }
                return n;
            }
        }

        /// <summary>累计星数 / 满星数（用于"12/24 星"这类展示）</summary>
        public int TotalStars
        {
            get
            {
                EnsureLoaded();
                int n = 0;
                for (int i = 0; i < _data.levels.Count; i++)
                {
                    if (_data.levels[i] != null)
                    {
                        n += _data.levels[i].stars;
                    }
                }
                return n;
            }
        }

        // ------------------------------------------------------------------
        // 设置
        // ------------------------------------------------------------------

        public GameSettings Settings
        {
            get
            {
                EnsureLoaded();
                return _data.settings;
            }
        }

        public void SetVolume(float v)
        {
            EnsureLoaded();
            _data.settings.volume = Mathf.Clamp01(v);
            ApplyToAudio();
            Save();
        }

        public void SetMuted(bool muted)
        {
            EnsureLoaded();
            _data.settings.muted = muted;
            ApplyToAudio();
            Save();
        }

        /// <summary>把设置推给音频系统。AudioManager 可能还没初始化，所以判空。</summary>
        public void ApplyToAudio()
        {
            EnsureLoaded();
            AudioManager am = AudioManager.Instance;
            if (am == null)
            {
                return;
            }
            am.Muted = _data.settings.muted;
            am.MasterVolume = _data.settings.volume;
        }

        // ------------------------------------------------------------------
        // 局内快照
        // ------------------------------------------------------------------

        public bool HasSnapshot
        {
            get
            {
                EnsureLoaded();
                return _data.snapshot != null && _data.snapshot.valid;
            }
        }

        public LevelSnapshot Snapshot
        {
            get
            {
                EnsureLoaded();
                return _data.snapshot;
            }
        }

        /// <summary>写入局内快照并立刻落盘（回合结束时由 GameFlowManager 调用）。</summary>
        public void SetSnapshot(LevelSnapshot snap)
        {
            EnsureLoaded();
            _data.snapshot = snap != null ? snap : new LevelSnapshot();
            Save();
        }

        /// <summary>开始新一局时作废快照。</summary>
        public void ClearSnapshot(bool save)
        {
            EnsureLoaded();
            _data.snapshot = new LevelSnapshot();
            if (save)
            {
                Save();
            }
        }
    }
}
