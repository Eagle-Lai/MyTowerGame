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
                _data.settings.Clamp();
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

        /// <summary>关卡通关结算：更新星级（只升不降）与累计次数，并立刻落库。</summary>
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

            PersistLevel(levelId);   // 只写这一关，而不是整表重写
            PersistSnapshot();
            if (_storage != null) _storage.Flush();
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
            PersistSettings();
            if (_storage != null) _storage.Flush();
        }

        public void SetMuted(bool muted)
        {
            EnsureLoaded();
            _data.settings.muted = muted;
            ApplyToAudio();
            PersistSettings();
            if (_storage != null) _storage.Flush();
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
            PersistSnapshot();
            if (_storage != null) _storage.Flush();
        }

        /// <summary>开始新一局时作废快照。</summary>
        public void ClearSnapshot(bool save)
        {
            EnsureLoaded();
            _data.snapshot = new LevelSnapshot();
            if (save)
            {
                PersistSnapshot();
                if (_storage != null) _storage.Flush();
            }
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
