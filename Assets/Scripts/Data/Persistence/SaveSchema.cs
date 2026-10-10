using System;
using System.Collections.Generic;
using System.Globalization;

namespace FTProject
{
    /// <summary>
    /// 存档库的表结构与版本迁移。
    ///
    /// ==================================================================
    /// 【表结构设计说明】
    ///   设计原则是「一张表只描述一类事实」，避免把整份存档塞进一个 JSON 大字段：
    ///     · 单行表（player_profile / game_settings / level_snapshot）
    ///       用 `CHECK (id = 1)` 强制只能有一行 —— 从表结构上杜绝"出现两行设置，
    ///       读到的和写进去的不是同一行"这类诡异问题。
    ///     · level_progress 以 level_id 为主键：天然幂等，重复写同一关就是覆盖，不需要先查后写。
    ///     · snapshot_tower 是快照的子表，单行表里存"塔列表"会退化成逗号分隔字符串，
    ///       加一个字段就要改解析代码；独立成表后，塔的字段将来想扩展直接 ALTER 即可。
    ///
    /// 【哪些列加密】
    ///   凡是"改了就能占便宜"的数值一律加密（玩家档案的金币/钻石/昵称、关卡星级/通关次数），
    ///   加密后以 TEXT 列承载 Base64 信封（见 AesCryptoService）。
    ///   代价是这些列**不能用于 SQL 排序/聚合** —— 本工程不需要：
    ///   总星数、已通关数都是在 C# 里遍历累加的（见 SaveManager）。
    ///   会话设置（音量/静音）与局内快照属于"改了也没收益、且要频繁读写"的数据，保持明文。
    ///
    /// 【版本迁移】
    ///   meta 表里存 schema_version。新库写入当前版本；老库按 <see cref="CurrentVersion"/>
    ///   逐版本升级；**库版本高于程序**时只告警不动数据（可能是玩家降级了客户端，
    ///   贸然改表会把他高版本的数据毁掉）。
    /// ==================================================================
    /// </summary>
    public static class SaveSchema
    {
        /// <summary>当前表结构版本。**改动任何列语义时必须 +1，并在 Migrations 里补一段。**</summary>
        /// <remarks>
        /// v2（UI 补全 B4）：level_progress 增加 best_time_ms（最快通关的游戏内毫秒数）。
        /// </remarks>
        public const int CurrentVersion = 2;

        public const string MetaSchemaVersion = "schema_version";
        public const string MetaCreatedAt = "created_at";

        /// <summary>全部业务表名（自检与日志用）</summary>
        public static readonly string[] Tables =
        {
            "meta", "player_profile", "level_progress", "game_settings",
            "level_snapshot", "snapshot_tower", "kv_store"
        };

        /// <summary>
        /// 建表语句。全部带 IF NOT EXISTS，因此**可重复执行** ——
        /// 每次启动都跑一遍，就等于"缺表自动补齐"，不需要单独判断"是不是首次运行"。
        /// </summary>
        private static readonly string[] CreateStatements =
        {
            // 元信息：表结构版本、创建时间等
            "CREATE TABLE IF NOT EXISTS meta (" +
            "  k TEXT PRIMARY KEY NOT NULL," +
            "  v TEXT" +
            ");",

            // 玩家档案（单行）。金色数值列均为密文，故类型是 TEXT。
            "CREATE TABLE IF NOT EXISTS player_profile (" +
            "  id         INTEGER PRIMARY KEY CHECK (id = 1)," +
            "  nickname   TEXT," +
            "  gold       TEXT," +
            "  diamond    TEXT," +
            "  player_lv  TEXT," +
            "  exp        TEXT," +
            "  created_at INTEGER," +
            "  updated_at INTEGER" +
            ");",

            // 关卡进度：主键即关卡 id，写入天然幂等
            // best_time_ms：**最快**通关用时（游戏内毫秒，0 = 尚无记录）。
            //   ⚠️ 与 stars/best_hp_left/clear_count 同为"改了就能占便宜"的数值 → 走密文，
            //   所以列类型是 TEXT 而不是 INTEGER（密文信封是 Base64 字符串）。
            //   代价同其它敏感列：不能参与 SQL 排序/聚合 —— 取最快值在 C# 里做（见 SaveManager）。
            "CREATE TABLE IF NOT EXISTS level_progress (" +
            "  level_id     INTEGER PRIMARY KEY," +
            "  stars        TEXT," +
            "  best_hp_left TEXT," +
            "  clear_count  TEXT," +
            "  last_play_at INTEGER," +
            "  best_time_ms TEXT," +
            "  updated_at   INTEGER" +
            ");",

            // 会话设置（单行，明文）
            "CREATE TABLE IF NOT EXISTS game_settings (" +
            "  id         INTEGER PRIMARY KEY CHECK (id = 1)," +
            "  volume     REAL," +
            "  muted      INTEGER," +
            "  updated_at INTEGER" +
            ");",

            // 局内快照主表（单行，明文）
            "CREATE TABLE IF NOT EXISTS level_snapshot (" +
            "  id           INTEGER PRIMARY KEY CHECK (id = 1)," +
            "  valid        INTEGER," +
            "  level_id     INTEGER," +
            "  round_cursor INTEGER," +
            "  gold         INTEGER," +
            "  hp           INTEGER," +
            "  max_hp       INTEGER," +
            "  updated_at   INTEGER" +
            ");",

            // 局内快照的塔列表（子表）。slot 是槽位序号，整批替换时用它保持顺序稳定。
            "CREATE TABLE IF NOT EXISTS snapshot_tower (" +
            "  slot        INTEGER PRIMARY KEY," +
            "  grid_row    INTEGER," +
            "  grid_col    INTEGER," +
            "  tower_type  INTEGER," +
            "  tower_level INTEGER" +
            ");",

            // 通用键值表：给"设置项/杂项开关"这类零散数据留的扩展位。
            // sensitive = 1 表示该行的 v 会加密存放（由调用方声明）。
            "CREATE TABLE IF NOT EXISTS kv_store (" +
            "  k          TEXT PRIMARY KEY NOT NULL," +
            "  v          TEXT," +
            "  sensitive  INTEGER NOT NULL DEFAULT 0," +
            "  updated_at INTEGER" +
            ");"
        };

        /// <summary>
        /// 确保库结构就绪。**可重复调用**。抛出 <see cref="DatabaseException"/> 表示
        /// 建表失败（此时上层应当降级到 JSON 存档，而不是继续用一张不完整的库）。
        /// </summary>
        public static void Ensure(IDatabase db)
        {
            if (db == null)
            {
                throw new DatabaseException("Ensure 收到 null 数据库", null, 0);
            }

            IDbTransaction tx = db.BeginTransaction();
            try
            {
                for (int i = 0; i < CreateStatements.Length; i++)
                {
                    db.Execute(CreateStatements[i]);
                }

                int existing = db.QueryScalar<int>(
                    "SELECT v FROM meta WHERE k = ?1", 0, MetaSchemaVersion);

                if (existing <= 0)
                {
                    // 全新库：登记版本与创建时间
                    long now = Now();
                    db.Execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?1, ?2)",
                        MetaSchemaVersion, CurrentVersion.ToString(CultureInfo.InvariantCulture));
                    db.Execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?1, ?2)",
                        MetaCreatedAt, now.ToString(CultureInfo.InvariantCulture));
                }
                else if (existing < CurrentVersion)
                {
                    RunMigrations(db, existing);
                    db.Execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?1, ?2)",
                        MetaSchemaVersion, CurrentVersion.ToString(CultureInfo.InvariantCulture));
                }
                else if (existing > CurrentVersion)
                {
                    // 不降级、不清表：只提示。极端情况下宁可让读写走"未知列"的容忍路径。
                    UnityEngine.Debug.LogWarning(string.Format(
                        "[Save] 存档库版本 {0} 高于本程序支持的 {1}（客户端被降级？）。" +
                        "将按只读兼容模式继续，不会修改库结构。", existing, CurrentVersion));
                }

                tx.Commit();
            }
            finally
            {
                tx.Dispose();
            }
        }

        /// <summary>
        /// 逐版本迁移。每个 case 都是"把库从 n 升到 n+1"，逐个串起来自然支持跨多版本升级。
        /// ⚠️ 老库（v1）的 level_progress 没有 best_time_ms 列，必须在这里补 ALTER，
        /// 否则老存档读取时会报"no such column"。
        /// </summary>
        private static void RunMigrations(IDatabase db, int fromVersion)
        {
            UnityEngine.Debug.Log(string.Format("[Save] 开始迁移存档库：{0} → {1}", fromVersion, CurrentVersion));

            for (int v = fromVersion; v < CurrentVersion; v++)
            {
                switch (v)
                {
                    // v1 → v2：关卡时间记录（UI 补全 B4「最佳用时」）
                    // 密文列 → TEXT；老行该列为 NULL，读取端 UnprotectInt(null) 回落 0（= 无记录）。
                    case 1:
                        db.Execute("ALTER TABLE level_progress ADD COLUMN best_time_ms TEXT;");
                        break;

                    default:
                        UnityEngine.Debug.LogWarning("[Save] 没有为版本 " + v + " 定义迁移步骤，已跳过。");
                        break;
                }
            }
        }

        /// <summary>表结构摘要（启动日志里打印一次，排查"表没建出来"最快）。</summary>
        public static string Describe()
        {
            List<string> rows = new List<string>(Tables.Length);
            for (int i = 0; i < Tables.Length; i++)
            {
                rows.Add(Tables[i]);
            }
            return string.Join(", ", rows.ToArray());
        }

        /// <summary>秒级时间戳（UTC）。用 UTC 是为了避免玩家改时区导致时间倒流。</summary>
        public static long Now()
        {
            return DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        }
    }
}
