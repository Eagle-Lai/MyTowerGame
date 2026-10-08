using System;
using System.Collections.Generic;

namespace FTProject
{
    /// <summary>
    /// 存档存储的**语义化**接口 —— 这是业务层（SaveManager）唯一认识的数据层契约。
    ///
    /// ==================================================================
    /// 【为什么要这一层，而不是让 SaveManager 直接写 SQL】
    ///   如果 SaveManager 里出现 `INSERT INTO level_progress ...`，那么：
    ///     · 表结构一改，业务代码必须跟着改；
    ///     · 想做"存档后端可切换"（SQLite / 云同步 / 内存）就无从下手；
    ///     · "加密哪些字段"这个决策会散落在业务逻辑里。
    ///   所以这一层负责"把业务概念映射成存储动作"，业务层只表达意图：
    ///   "保存这一关的进度" —— 至于落到哪张表、哪些列加密，这里说了算。
    ///
    /// 【异常策略】
    ///   读：**不抛异常**，缺数据就返回默认值（空档），读坏了按"这一项没有"处理。
    ///   写：**不抛异常**，失败只记日志。理由与项目原有的 SaveManager 一致 ——
    ///       存档写失败不该让玩家中断游戏；真正的错误在日志里可查。
    ///   <see cref="Initialize"/> 是例外：它会抛 <see cref="DatabaseException"/>，
    ///   好让上层有机会降级到备用后端（创建失败必须当场知道）。
    /// ==================================================================
    /// </summary>
    public interface ISaveStorage : IDisposable
    {
        /// <summary>后端标识，例如 "SQLite 3.43.2" / "JSON 文件"。日志与自检用。</summary>
        string BackendName { get; }

        /// <summary>数据落盘位置（数据库文件路径 / JSON 文件路径）。</summary>
        string Location { get; }

        /// <summary>是否已成功初始化</summary>
        bool IsReady { get; }

        /// <summary>敏感字段是否真的在加密（密钥不可用时会退化为明文）。</summary>
        bool IsEncrypted { get; }

        /// <summary>最近一次错误（null 表示无）。</summary>
        string LastError { get; }

        /// <summary>创建/校验表结构、准备后端。失败抛 <see cref="DatabaseException"/>。</summary>
        void Initialize();

        // ---- 会话设置 ----------------------------------------------------

        GameSettings LoadSettings();
        void SaveSettings(GameSettings settings);

        // ---- 关卡进度 ----------------------------------------------------

        List<LevelProgress> LoadLevels();
        void SaveLevel(LevelProgress progress);
        void DeleteLevel(int levelId);

        // ---- 局内快照 ----------------------------------------------------

        LevelSnapshot LoadSnapshot();
        void SaveSnapshot(LevelSnapshot snapshot);

        // ---- 通用键值（设置项 / 其它零散数据）-----------------------------

        /// <summary>读一个键值（自动解密）。不存在返回 false。</summary>
        bool TryGetValue(string key, out string value);

        /// <summary>写一个键值。<paramref name="sensitive"/> 决定该值是否加密后落库。</summary>
        void SetValue(string key, string value, bool sensitive);

        void DeleteValue(string key);

        // ---- 维护 --------------------------------------------------------

        /// <summary>清空全部业务数据（保留表结构）。设置界面的"重置存档"走这里。</summary>
        void ResetAll();

        /// <summary>把缓冲区刷到磁盘。</summary>
        void Flush();
    }
}
