using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 存档管理器（业务门面）：关卡解锁与星级、玩家设置、局内快照、通用键值。
    ///
    /// ==================================================================
    /// 【本次改造：从"自己写 JSON"变成"委托给数据层"】
    ///   改造前：本类自己拼 JsonUtility + File.WriteAllText，存储格式与业务逻辑是同一块代码。
    ///   改造后：本类只表达业务意图（"这一关通了，记 2 星"），
    ///           落库、加密、事务、资源释放全部下沉到 <see cref="ISaveStorage"/> 实现里。
    ///
    ///   **对外的公开成员一字未改** —— SelectView / SettingView / GameFlowManager
    ///   等调用方不需要任何改动，这是"替换现有逻辑但保证数据流转正常"的关键：
    ///   接口稳定，实现替换。
    ///
    /// 【为什么内存里还留一份 SaveData】
    ///   星级、总星数这类查询在 UI 上会被频繁读取（每次刷新关卡列表都读一遍）。
    ///   保留内存副本后这些读取是纯内存操作；写入时**同时**更新内存与存储（写穿透），
    ///   两边不会不一致 —— 因为它俩的唯一写入口就是本类的这几个 Set/Record 方法。
    ///
    /// 【失败时的行为：一律当作"没有存档"，绝不抛异常】
    ///   存档损坏、目录只读、磁盘满 —— 这些都不该让玩家连游戏都进不去。
    ///   所有存储调用在数据层内部已做了异常收敛，本类只在最后兜一层。
    ///
    /// 【硬约束：与编辑器 API 完全解耦】
    ///   本类及其依赖的数据层都不得引用 UnityEditor —— 否则打包必炸
    ///   （本项目历史上踩过 `JsonDataManager` 顶层 using UnityEditor 的坑）。
    /// ==================================================================
    /// </summary>
    public class SaveManager : BaseManager<SaveManager>
    {
        private ISaveStorage _storage;
        private SaveData _data;
        private bool _loaded;
        public const int MaxStars = LevelRatingEvaluator.MaxStars;
        public static bool IsTestStorage { get { return !string.IsNullOrEmpty(SaveStorageFactory.ActiveTestContextId); } }
        private sealed class StorageScope : IDisposable
        {
            private readonly SaveManager owner;
            private readonly string previous;
            private bool disposed;
            public StorageScope(SaveManager manager, string prior) { owner = manager; previous = prior; }
            public void Dispose() { if (disposed) return; disposed = true; owner.SwitchStorage(previous); }
        }
        public IDisposable SetTestStorageContext(string contextId)
        {
            if (string.IsNullOrEmpty(contextId)) throw new ArgumentException("A test storage identity is required");
            string previous = SaveStorageFactory.TestContextId;
            SwitchStorage(contextId);
            return new StorageScope(this, previous);
        }
        private void SwitchStorage(string contextId)
        {
            if (_storage != null) { _storage.Flush(); _storage.Dispose(); }
            SaveStorageFactory.TestContextId = contextId; _storage = null; _data = null; _loaded = false;
            EnsureLoaded();
        }

        // ------------------------------------------------------------------
        // 只读信息（自检 / 日志 / 排查用）
        // ------------------------------------------------------------------

        /// <summary>当前后端标识，例如 "SQLite 3.50.2" / "JSON 文件（SQLite 回退）"</summary>
        public string BackendName
        {
            get { EnsureLoaded(); return _storage != null ? _storage.BackendName : "未初始化"; }
        }

        /// <summary>存档落盘位置</summary>
        public string StorageLocation
        {
            get { EnsureLoaded(); return _storage != null ? _storage.Location : null; }
        }

        /// <summary>敏感字段是否真的在加密</summary>
        public bool EncryptionEnabled
        {
            get { EnsureLoaded(); return _storage != null && _storage.IsEncrypted; }
        }

        /// <summary>
        /// 存档文件完整路径（兼容旧调用点；排查问题时打印它最快）。
        /// 注意：实际位置以后端为准，用 <see cref="StorageLocation"/> 更准确。
        /// </summary>
        public static string FilePath
        {
            get { return SaveStorageFactory.DatabasePath; }
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
        // 生命周期
        // ------------------------------------------------------------------

        public override void OnInit()
        {
            base.OnInit();
            EnsureLoaded();
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            if (_storage != null)
            {
                try
                {
                    _storage.Flush();
                    _storage.Dispose();
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[Save] 关闭存储时出错（可忽略）：" + ex.Message);
                }
            }
        }

        /// <summary>懒初始化：即使有人没等 Launcher 就访问存档，也能正常拿到数据。</summary>
        private void EnsureLoaded()
        {
            if (_loaded)
            {
                return;
            }
            _loaded = true;
            _data = new SaveData();
            _storage = null;

            try
            {
                _storage = SaveStorageFactory.Create();

                _data.settings = _storage.LoadSettings() ?? new GameSettings();
                _data.levels = _storage.LoadLevels() ?? new List<LevelProgress>();
                _data.snapshot = _storage.LoadSnapshot() ?? new LevelSnapshot();
                if (_data.settings == null) _data.settings = new GameSettings();
                if (_data.levels == null) _data.levels = new List<LevelProgress>();
                if (_data.snapshot == null) _data.snapshot = new LevelSnapshot();
                if (_data.snapshot.towers == null) _data.snapshot.towers = new List<TowerSnapshot>();
            }
            catch (Exception ex)
            {
                // 连存储都建不起来时，用一个内存存档把游戏跑起来（本局有效、退出即失）。
                Debug.LogError("[Save] 存档存储初始化失败，本次运行将使用内存存档（不会落盘）：" + ex.Message);
                _data = new SaveData();
            }
        }

        // ------------------------------------------------------------------
        // 读 / 写（存储层）
        // ------------------------------------------------------------------

        /// <summary>
        /// 把内存里的存档整体写盘。
        /// 【什么时候需要它】正常改设置/记成绩都会即时写穿透，一般不需要手工调用；
        /// 保留它是为了给"批量改了很多字段后一次性提交"留一个明确入口（例如调试命令）。
        /// </summary>
        public void Save()
        {
            EnsureLoaded();
            if (_storage == null)
            {
                return;
            }
            try
            {
                _storage.SaveSettings(_data.settings);
                for (int i = 0; i < _data.levels.Count; i++)
                {
                    _storage.SaveLevel(_data.levels[i]);
                }
                _storage.SaveSnapshot(_data.snapshot);
                _storage.Flush();
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 写档失败：" + ex.Message);
            }
        }

        /// <summary>清空存档（设置界面用）。表结构/后端实例保留，只清业务数据。</summary>
        public void ResetAll()
        {
            EnsureLoaded();
            _data = new SaveData();
            _loaded = true;
            if (_storage == null)
            {
                return;
            }
            try
            {
                _storage.ResetAll();
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 重置存档失败：" + ex.Message);
            }
        }

        /// <summary>把缓冲区刷到磁盘（切后台 / 退出前调用）。</summary>
        public void Flush()
        {
            EnsureLoaded();
            if (_storage == null)
            {
                return;
            }
            try
            {
                _storage.Flush();
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] 刷盘失败（可忽略）：" + ex.Message);
            }
        }

        /// <summary>单关写穿透：把内存中的某关进度落库。</summary>
        private void PersistLevel(int levelId)
        {
            if (_storage == null)
            {
                return;
            }
            LevelProgress p = _data.Find(levelId);
            if (p != null)
            {
                _storage.SaveLevel(p);
            }
        }

        private void PersistSettings()
        {
            if (_storage != null)
            {
                _storage.SaveSettings(_data.settings);
            }
        }

        private void PersistSnapshot()
        {
            if (_storage != null)
            {
                _storage.SaveSnapshot(_data.snapshot);
            }
        }

        // ------------------------------------------------------------------
        // 关卡解锁与星级
        // ------------------------------------------------------------------

#if UNITY_EDITOR
        /// <summary>
        /// 编辑器内是否**无视破关进度、全部关卡直接可进**。
        ///
        /// 【为什么需要】调新地图时不该为了看第 15 关先把中间每一关挨个通关；
        ///   选关界面 / 关卡详情页 / 「下一关」都只看 IsUnlocked，所以一处开关就够。
        ///
        /// 【为什么不影响真机】整段包在 #if UNITY_EDITOR 里，玩家构建连这个字段都不存在，
        ///   真机仍然走下面"前一关通关才解锁下一关"的正常逻辑。
        /// 想在编辑器里验证锁定态（比如检查锁图标）时，把它改成 false 即可。
        /// 【为什么不用 const】const true 会让编译器把后面的正常逻辑判成"不可达代码"并报 CS0162，
        ///   static readonly 不参与常量折叠，编译干净。
        /// </summary>
        private static readonly bool UnlockAllLevelsInEditor = true;
        private static bool _testProductionUnlockRules;
        private sealed class UnlockRuleScope : IDisposable
        {
            private readonly bool previous;
            public UnlockRuleScope(bool prior) { previous = prior; }
            public void Dispose() { _testProductionUnlockRules = previous; }
        }
        /// <summary>Exercise the actual player unlock path against isolated test storage only.</summary>
        public IDisposable UseProductionUnlockRulesForTest()
        {
            if (!IsTestStorage) throw new InvalidOperationException("Unlock tests require isolated storage");
            bool prior = _testProductionUnlockRules;
            _testProductionUnlockRules = true;
            return new UnlockRuleScope(prior);
        }
#endif

        /// <summary>
        /// 关卡是否已解锁。
        /// 【规则】第 1 关永远开放；其余关卡需要**前一关至少通关一次**。
        /// 用"关卡 id 排序后的前一个"而不是 id-1，这样以后中间插关卡也不会把解锁链弄断。
        /// 【编辑器例外】见 UnlockAllLevelsInEditor：仅编辑器内全解锁，真机不受影响。
        /// </summary>
        public bool IsUnlocked(int levelId)
        {
#if UNITY_EDITOR
            if (UnlockAllLevelsInEditor && !_testProductionUnlockRules)
            {
                return true;
            }
#endif
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
            EnsureRatingVersion(levelId);
            LevelProgress p = _data.Find(levelId);
            return IsCurrentRating(p, levelId) ? p.stars : 0;
        }

        /// <summary>
        /// 历史**最快**通关用时（游戏内毫秒）。0 = 尚无记录（未通关 / 老存档）。
        /// 【展示约定】调用方把 0 显示成 `--:--`，不要显示 `00:00` ——
        /// "没有记录"和"0 秒通关"必须一眼分得开。
        /// </summary>
        public int GetBestTimeMs(int levelId)
        {
            EnsureLoaded();
            EnsureRatingVersion(levelId);
            LevelProgress p = _data.Find(levelId);
            return IsCurrentRating(p, levelId) ? p.bestTimeMs : 0;
        }

        /// <summary>历史最好成绩（剩余生命），仅用于展示。0 = 无记录。</summary>
        public int GetBestHpLeft(int levelId)
        {
            EnsureLoaded();
            EnsureRatingVersion(levelId);
            LevelProgress p = _data.Find(levelId);
            return IsCurrentRating(p, levelId) ? p.bestHpLeft : 0;
        }
        private static bool IsCurrentRating(LevelProgress progress, int levelId)
        {
            var profile = Configs.GetLevelRating(levelId);
            return progress != null && Configs.RatingContentVerified && profile != null && profile.IsValid && progress.ratingVersionKey == profile.versionKey;
        }
        public int GetBestCombatTimeMs(int levelId) { EnsureLoaded(); EnsureRatingVersion(levelId); var p = _data.Find(levelId); return IsCurrentRating(p, levelId) ? p.bestCombatTimeMs : 0; }
        public int GetLegacyStars(int levelId)
        {
            EnsureLoaded(); EnsureRatingVersion(levelId); var p = _data.Find(levelId); int result = 0;
            if (p != null && !IsCurrentRating(p, levelId)) result = p.stars;
            if (p != null && p.legacy != null) foreach (var old in p.legacy) result = Math.Max(result, old.stars);
            return result;
        }
        public bool IsCurrentVersionRated(int levelId) { return GetStars(levelId) > 0; }
        public bool IsRunCommitted(int levelId, string runId)
        {
            EnsureLoaded(); var p = _data.Find(levelId);
            return p != null && p.committedRunIds != null && p.committedRunIds.Contains(runId);
        }
        /// <summary>Back up first, then archive and change the current content identity. Re-entry is idempotent.</summary>
        public void EnsureRatingVersion(int levelId)
        {
            EnsureLoaded();
            LevelRatingProfile profile = Configs.GetLevelRating(levelId);
            if (!Configs.RatingContentVerified || profile == null || !profile.IsValid) return;
            LevelProgress p = _data.Find(levelId);
            if (p == null || p.ratingVersionKey == profile.versionKey) return;
            if (_storage == null) return;
            string oldKey = string.IsNullOrEmpty(p.ratingVersionKey) ? "legacy-v1-three-stars" : p.ratingVersionKey;
            string backupKey = "rating-backup/" + levelId + "/" + oldKey;
            string backup;
            string originalJson = JsonUtility.ToJson(p);
            if (_storage != null)
            {
                if (!_storage.TryGetValue(backupKey, out backup)) { _storage.SetValue(backupKey, originalJson, true); _storage.Flush(); }
                if (!_storage.TryGetValue(backupKey, out backup) || string.IsNullOrEmpty(backup)) { Debug.LogWarning("[Save] Rating migration deferred: legacy backup could not be persisted"); return; }
            }
            var candidate = JsonUtility.FromJson<LevelProgress>(originalJson);
            SaveProgressMigration.ArchiveForVersion(candidate, profile.versionKey);
            if (_storage != null && !_storage.CommitClear(candidate)) { Debug.LogWarning("[Save] Rating migration deferred: archive could not be persisted"); return; }
            _data.levels[_data.levels.IndexOf(p)] = candidate;
            _data.snapshot = new LevelSnapshot();
            if (_storage != null) { _storage.SetValue("rating-migrated/" + levelId, profile.versionKey, true); _storage.Flush(); }
        }
        public bool RecordClear(int levelId, LevelRatingResult result)
        {
            EnsureLoaded();
            if (_storage == null || result == null || !result.valid || !result.victory || result.stars <= 0 || result.metrics == null || result.metrics.debugOverride) return false;
            var current = Configs.GetLevelRating(levelId);
            if (current == null || current.versionKey != result.versionKey) return false;
            result = LevelRatingEvaluator.Evaluate(current, result.metrics);
            if (!result.valid || !result.victory || result.stars <= 0) return false;
            EnsureRatingVersion(levelId);
            var existing = _data.Find(levelId);
            if (existing != null && existing.ratingVersionKey != current.versionKey) return false;
            LevelProgress original = existing ?? new LevelProgress { levelId = levelId, ratingVersionKey = current.versionKey };
            if (IsRunCommitted(levelId, result.metrics.runId)) return true;
            LevelProgress p = JsonUtility.FromJson<LevelProgress>(JsonUtility.ToJson(original));
            if (p.committedRunIds == null) p.committedRunIds = new List<string>();
            p.ratingVersionKey = result.versionKey;
            if (result.stars > p.stars) { p.stars = Mathf.Clamp(result.stars, 0, MaxStars); p.bestRating = result; }
            p.bestHpLeft = Math.Max(p.bestHpLeft, result.metrics.hp);
            int levelMs = (int)Math.Min(int.MaxValue, result.metrics.levelElapsedMs), combatMs = (int)Math.Min(int.MaxValue, result.metrics.combatElapsedMs);
            if (p.bestTimeMs <= 0 || levelMs < p.bestTimeMs) p.bestTimeMs = levelMs;
            if (p.bestCombatTimeMs <= 0 || combatMs < p.bestCombatTimeMs) p.bestCombatTimeMs = combatMs;
            p.clearCount++; p.committedRunIds.Add(result.metrics.runId);
            int index = _data.levels.IndexOf(original);
            if (_storage != null && !_storage.CommitClear(p)) return false;
            if (index < 0) _data.levels.Add(p); else _data.levels[index] = p;
            _data.snapshot = new LevelSnapshot();
            if (_storage != null) _storage.Flush();
            return true;
        }

        /// <summary>把毫秒格式化成 `m:ss` 或 `--:--`（无记录）。UI 与日志共用一处口径。</summary>
        public static string FormatTime(int timeMs)
        {
            if (timeMs <= 0)
            {
                return "--:--";
            }
            int totalSec = timeMs / 1000;
            return string.Format("{0}:{1:00}", totalSec / 60, totalSec % 60);
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

        /// <summary>累计星数（用于"12/24 星"这类展示）</summary>
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
                        n += GetStars(_data.levels[i].levelId);
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

        /// <summary>
        /// 读玩家显式选择的语言。从未选择过返回 false（此时应回退到配置里的默认语言）。
        /// </summary>
        public bool TryGetLanguage(out Language lang)
        {
            EnsureLoaded();
            string code = _data.settings != null ? _data.settings.language : null;
            if (string.IsNullOrEmpty(code))
            {
                lang = Language.English;
                return false;
            }
            lang = LanguageUtil.FromCode(code);
            return true;
        }

        /// <summary>写玩家选择的语言并落盘。</summary>
        public void SetLanguage(Language lang)
        {
            EnsureLoaded();
            _data.settings.language = lang.ToCode();
            PersistSettings();
            if (_storage != null) _storage.Flush();
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
            TrySetSnapshot(snap);
        }

        /// <summary>Publish a checkpoint only after storage confirms the complete write.</summary>
        public bool TrySetSnapshot(LevelSnapshot snap)
        {
            EnsureLoaded();
            if (_storage == null) return false;
            var candidate = snap != null ? JsonUtility.FromJson<LevelSnapshot>(JsonUtility.ToJson(snap)) : new LevelSnapshot();
            try
            {
                _storage.SaveSnapshot(candidate);
                _storage.Flush();
                if (!string.IsNullOrEmpty(_storage.LastError)) return false;
                LevelSnapshot persisted = _storage.LoadSnapshot();
                if (!string.IsNullOrEmpty(_storage.LastError) || persisted == null || JsonUtility.ToJson(persisted) != JsonUtility.ToJson(candidate)) return false;
                _data.snapshot = persisted;
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Save] Checkpoint was not published: " + ex.Message);
                return false;
            }
        }

        /// <summary>Keep the previous resumable boundary if durable invalidation fails.</summary>
        public bool TryClearSnapshot()
        {
            return TrySetSnapshot(new LevelSnapshot());
        }

        /// <summary>开始新一局时作废快照。</summary>
        public void ClearSnapshot(bool save)
        {
            EnsureLoaded();
            if (save) TryClearSnapshot();
            else _data.snapshot = new LevelSnapshot();
        }

        // ------------------------------------------------------------------
        // 通用键值（给其它模块存取零散本地数据用）
        // ------------------------------------------------------------------

        /// <summary>
        /// 读一个自定义键值。不存在返回 false。
        /// 【用途】设置项、新手引导进度、上次选择等"不值得单独建表"的数据。
        /// </summary>
        public bool TryGetUserValue(string key, out string value)
        {
            EnsureLoaded();
            value = null;
            if (_storage == null)
            {
                return false;
            }
            return _storage.TryGetValue(key, out value);
        }

        /// <summary>
        /// 写一个自定义键值。<paramref name="sensitive"/>=true 时该值会加密后落库。
        /// 【怎么选】凡是"改了能占便宜"或"属于用户隐私"的内容（货币、昵称、内购凭证）
        ///   一律传 true；纯粹的界面偏好（音量以外的开关、窗口位置）可以传 false，
        ///   这样在"密钥不可用"的降级场景下这些偏好仍然可读。
        /// </summary>
        public void SetUserValue(string key, string value, bool sensitive)
        {
            EnsureLoaded();
            if (_storage == null || string.IsNullOrEmpty(key))
            {
                return;
            }
            _storage.SetValue(key, value, sensitive);
            _storage.Flush();
        }

        public void DeleteUserValue(string key)
        {
            EnsureLoaded();
            if (_storage == null || string.IsNullOrEmpty(key))
            {
                return;
            }
            _storage.DeleteValue(key);
        }
    }
}
