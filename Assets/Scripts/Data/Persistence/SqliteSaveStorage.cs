using System;
using System.Collections.Generic;
using System.Globalization;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// <see cref="ISaveStorage"/> 的 SQLite 实现。
    ///
    /// 【职责边界】
    ///   · 把「关卡进度 / 会话设置 / 局内快照 / 键值」翻译成对若干张表的读写；
    ///   · 对声明为敏感的列，写入前加密、读取后解密（业务层完全无感）；
    ///   · 事务边界：凡是一次操作会碰多行/多表的（保存快照、重置存档），一律包在事务里。
    ///
    /// 【为什么所有 public 方法都不抛异常】
    ///   见 <see cref="ISaveStorage"/> 的说明。这里统一的做法是：
    ///   用一个 try/catch 包住，失败 → 记 LastError + 打日志 + 返回安全默认值。
    ///   唯一的例外是 <see cref="Initialize"/>，它必须把失败暴露给上层以便降级。
    /// </summary>
    internal sealed class SqliteSaveStorage : ISaveStorage
    {
        private const int SingleRowId = 1;

        private readonly IDatabase _db;
        private readonly ICryptoService _crypto;
        private bool _initialized;

        internal SqliteSaveStorage(IDatabase db, ICryptoService crypto)
        {
            _db = db;
            _crypto = crypto;
        }

        public string BackendName
        {
            get { return _db != null ? _db.BackendName : "未连接"; }
        }

        public string Location
        {
            get { return _db != null ? _db.DatabasePath : null; }
        }

        public bool IsReady
        {
            get { return _initialized && _db != null && _db.IsOpen; }
        }

        public bool IsEncrypted
        {
            get { return _crypto != null && _crypto.IsAvailable; }
        }

        public string LastError { get; private set; }

        // ------------------------------------------------------------------
        // 初始化
        // ------------------------------------------------------------------

        public void Initialize()
        {
            SaveSchema.Ensure(_db);
            _initialized = true;
            Debug.Log(string.Format(
                "[Save] 存档库就绪：{0}\n  位置：{1}\n  数据表：{2}\n  敏感字段加密：{3}",
                BackendName, Location, SaveSchema.Describe(), IsEncrypted ? "已启用（AES-256-CBC + HMAC-SHA256）" : "未启用（密钥不可用）"));
        }

        // ------------------------------------------------------------------
        // 会话设置（明文）
        // ------------------------------------------------------------------

        public GameSettings LoadSettings()
        {
            GameSettings s = new GameSettings();
            try
            {
                DbRow row = _db.QuerySingle(
                    "SELECT volume, muted FROM game_settings WHERE id = ?1", SingleRowId);
                if (row != null)
                {
                    s.volume = row.GetFloat("volume", s.volume);
                    s.muted = row.GetBool("muted", s.muted);
                    s.Clamp();
                }
            }
            catch (Exception ex)
            {
                Fail("读取会话设置失败", ex);
            }
            return s;
        }

        public void SaveSettings(GameSettings settings)
        {
            if (settings == null)
            {
                return;
            }
            try
            {
                settings.Clamp();
                _db.Execute(
                    "INSERT OR REPLACE INTO game_settings (id, volume, muted, updated_at) " +
                    "VALUES (?1, ?2, ?3, ?4)",
                    SingleRowId, settings.volume, settings.muted ? 1 : 0, SaveSchema.Now());
            }
            catch (Exception ex)
            {
                Fail("写入会话设置失败", ex);
            }
        }

        // ------------------------------------------------------------------
        // 关卡进度（星级/最佳成绩/通关次数 → 加密列）
        // ------------------------------------------------------------------

        public List<LevelProgress> LoadLevels()
        {
            List<LevelProgress> list = new List<LevelProgress>();
            try
            {
                List<DbRow> rows = _db.Query(
                    "SELECT level_id, stars, best_hp_left, clear_count, best_time_ms FROM level_progress ORDER BY level_id");
                for (int i = 0; i < rows.Count; i++)
                {
                    DbRow r = rows[i];
                    LevelProgress p = new LevelProgress();
                    p.levelId = r.GetInt("level_id");
                    p.stars = UnprotectInt(r.GetString("stars"), 0);
                    p.bestHpLeft = UnprotectInt(r.GetString("best_hp_left"), 0);
                    p.clearCount = UnprotectInt(r.GetString("clear_count"), 0);
                    // 老库（v1）迁移后该列为 NULL → UnprotectInt 回落 0（= 无记录），不会报错
                    p.bestTimeMs = UnprotectInt(r.GetString("best_time_ms"), 0);
                    // 星级非法（>3）说明密文被换过或历史脏数据 —— 夹紧而不是丢弃整条记录，
                    // 丢掉会让玩家平白少一关进度。
                    if (p.stars < 0) p.stars = 0;
                    if (p.stars > 3) p.stars = 3;
                    if (p.levelId > 0)
                    {
                        list.Add(p);
                    }
                }
            }
            catch (Exception ex)
            {
                Fail("读取关卡进度失败", ex);
            }
            return list;
        }

        public void SaveLevel(LevelProgress progress)
        {
            if (progress == null || progress.levelId <= 0)
            {
                return;
            }
            try
            {
                long now = SaveSchema.Now();
                _db.Execute(
                    "INSERT OR REPLACE INTO level_progress " +
                    "(level_id, stars, best_hp_left, clear_count, best_time_ms, last_play_at, updated_at) " +
                    "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                    progress.levelId,
                    ProtectInt(progress.stars),
                    ProtectInt(progress.bestHpLeft),
                    ProtectInt(progress.clearCount),
                    ProtectInt(progress.bestTimeMs),
                    now,
                    now);
            }
            catch (Exception ex)
            {
                Fail("写入关卡进度失败", ex);
            }
        }

        public void DeleteLevel(int levelId)
        {
            try
            {
                _db.Execute("DELETE FROM level_progress WHERE level_id = ?1", levelId);
            }
            catch (Exception ex)
            {
                Fail("删除关卡进度失败", ex);
            }
        }

        // ------------------------------------------------------------------
        // 局内快照（主表单行 + 塔子表，整批替换）
        // ------------------------------------------------------------------

        public LevelSnapshot LoadSnapshot()
        {
            LevelSnapshot snap = new LevelSnapshot();
            try
            {
                DbRow row = _db.QuerySingle(
                    "SELECT valid, level_id, round_cursor, gold, hp, max_hp " +
                    "FROM level_snapshot WHERE id = ?1", SingleRowId);
                if (row == null)
                {
                    return snap;   // 没有快照 → 返回 valid=false 的空快照
                }

                snap.valid = row.GetBool("valid");
                snap.levelId = row.GetInt("level_id");
                snap.roundCursor = row.GetInt("round_cursor");
                snap.gold = row.GetInt("gold");
                snap.hp = row.GetInt("hp");
                snap.maxHp = row.GetInt("max_hp");

                if (snap.towers == null)
                {
                    snap.towers = new List<TowerSnapshot>();
                }
                List<DbRow> towers = _db.Query(
                    "SELECT grid_row, grid_col, tower_type, tower_level " +
                    "FROM snapshot_tower ORDER BY slot");
                for (int i = 0; i < towers.Count; i++)
                {
                    DbRow t = towers[i];
                    TowerSnapshot ts = new TowerSnapshot();
                    ts.row = t.GetInt("grid_row");
                    ts.col = t.GetInt("grid_col");
                    ts.type = t.GetInt("tower_type");
                    ts.level = t.GetInt("tower_level");
                    snap.towers.Add(ts);
                }
            }
            catch (Exception ex)
            {
                Fail("读取局内快照失败", ex);
                return new LevelSnapshot();
            }
            return snap;
        }

        public void SaveSnapshot(LevelSnapshot snapshot)
        {
            if (snapshot == null)
            {
                return;
            }
            IDbTransaction tx = null;
            try
            {
                // 主表与塔子表必须整体替换 —— 中途失败若留下"新主表 + 旧塔表"，
                // 下次恢复会建出一批本不该存在的塔。所以走事务。
                tx = _db.BeginTransaction();

                long now = SaveSchema.Now();
                _db.Execute(
                    "INSERT OR REPLACE INTO level_snapshot " +
                    "(id, valid, level_id, round_cursor, gold, hp, max_hp, updated_at) " +
                    "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
                    SingleRowId,
                    snapshot.valid ? 1 : 0,
                    snapshot.levelId,
                    snapshot.roundCursor,
                    snapshot.gold,
                    snapshot.hp,
                    snapshot.maxHp,
                    now);

                _db.Execute("DELETE FROM snapshot_tower");

                if (snapshot.towers != null)
                {
                    for (int i = 0; i < snapshot.towers.Count; i++)
                    {
                        TowerSnapshot ts = snapshot.towers[i];
                        if (ts == null)
                        {
                            continue;
                        }
                        _db.Execute(
                            "INSERT OR REPLACE INTO snapshot_tower " +
                            "(slot, grid_row, grid_col, tower_type, tower_level) " +
                            "VALUES (?1, ?2, ?3, ?4, ?5)",
                            i, ts.row, ts.col, ts.type, ts.level);
                    }
                }

                tx.Commit();
            }
            catch (Exception ex)
            {
                Fail("写入局内快照失败", ex);
            }
            finally
            {
                if (tx != null)
                {
                    tx.Dispose();
                }
            }
        }

        // ------------------------------------------------------------------
        // 通用键值
        // ------------------------------------------------------------------

        public bool TryGetValue(string key, out string value)
        {
            value = null;
            if (string.IsNullOrEmpty(key))
            {
                return false;
            }
            try
            {
                DbRow row = _db.QuerySingle(
                    "SELECT v, sensitive FROM kv_store WHERE k = ?1", key);
                if (row == null)
                {
                    return false;
                }
                string raw = row.GetString("v");
                value = row.GetBool("sensitive")
                    ? Unprotect(raw)     // 敏感行 → 解密
                    : raw;
                return true;
            }
            catch (Exception ex)
            {
                Fail("读取键值「" + key + "」失败", ex);
                return false;
            }
        }

        public void SetValue(string key, string value, bool sensitive)
        {
            if (string.IsNullOrEmpty(key))
            {
                return;
            }
            try
            {
                string stored = sensitive ? Protect(value) : value;
                _db.Execute(
                    "INSERT OR REPLACE INTO kv_store (k, v, sensitive, updated_at) " +
                    "VALUES (?1, ?2, ?3, ?4)",
                    key, stored, sensitive ? 1 : 0, SaveSchema.Now());
            }
            catch (Exception ex)
            {
                Fail("写入键值「" + key + "」失败", ex);
            }
        }

        public void DeleteValue(string key)
        {
            try
            {
                _db.Execute("DELETE FROM kv_store WHERE k = ?1", key);
            }
            catch (Exception ex)
            {
                Fail("删除键值「" + key + "」失败", ex);
            }
        }

        // ------------------------------------------------------------------
        // 维护
        // ------------------------------------------------------------------

        public void ResetAll()
        {
            IDbTransaction tx = null;
            try
            {
                tx = _db.BeginTransaction();
                // meta 表刻意保留：它存的是表结构版本，删掉只会让下次启动误判为"全新库"。
                _db.Execute("DELETE FROM player_profile");
                _db.Execute("DELETE FROM level_progress");
                _db.Execute("DELETE FROM game_settings");
                _db.Execute("DELETE FROM level_snapshot");
                _db.Execute("DELETE FROM snapshot_tower");
                _db.Execute("DELETE FROM kv_store");
                tx.Commit();
                Debug.Log("[Save] 存档已清空（表结构保留）");
            }
            catch (Exception ex)
            {
                Fail("重置存档失败", ex);
            }
            finally
            {
                if (tx != null)
                {
                    tx.Dispose();
                }
            }
        }

        public void Flush()
        {
            if (_db == null)
            {
                return;
            }
            _db.Flush();
        }

        public void Dispose()
        {
            _initialized = false;
            // 连接的所有权在本类：由 SaveStorageFactory 创建后即交接过来，
            // 没有第二个持有者。所以这里负责关闭它 —— 否则进程内会一直挂着一个
            // 已无用的 SQLite 连接与文件句柄（编辑器里反复进出播放模式时尤其明显）。
            if (_db != null)
            {
                try
                {
                    _db.Dispose();
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[Save] 关闭数据库连接失败（可忽略）：" + ex.Message);
                }
            }
        }

        // ------------------------------------------------------------------
        // 加密包装（只在这里出现，业务层看不到）
        // ------------------------------------------------------------------

        private string Protect(string plain)
        {
            if (_crypto == null || string.IsNullOrEmpty(plain))
            {
                return plain;
            }
            try
            {
                return _crypto.Encrypt(plain);
            }
            catch (Exception ex)
            {
                LastError = "加密失败：" + ex.Message;
                Debug.LogError("[Save] " + LastError + "（该项将以明文写入）");
                return plain;
            }
        }

        private string Unprotect(string stored)
        {
            if (_crypto == null || string.IsNullOrEmpty(stored))
            {
                return stored;
            }
            try
            {
                return _crypto.Decrypt(stored);
            }
            catch (Exception ex)
            {
                // 密钥变了 / 有人改了密文 → 这一项当"没有"，但不影响其余数据。
                LastError = "解密失败：" + ex.Message;
                Debug.LogWarning("[Save] " + LastError + "（该项按默认值处理）");
                return null;
            }
        }

        private string ProtectInt(int value)
        {
            return Protect(value.ToString(CultureInfo.InvariantCulture));
        }

        private int UnprotectInt(string stored, int defaultValue)
        {
            if (string.IsNullOrEmpty(stored))
            {
                return defaultValue;
            }
            string plain = Unprotect(stored);
            int r;
            return int.TryParse(plain, NumberStyles.Integer, CultureInfo.InvariantCulture, out r)
                ? r : defaultValue;
        }

        private void Fail(string what, Exception ex)
        {
            LastError = what + "：" + ex.Message;
            Debug.LogWarning("[Save] " + LastError);
        }
    }
}
