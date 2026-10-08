using System;
using System.Collections.Generic;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// <see cref="IDatabase"/> 的 SQLite 实现（P/Invoke 直连原生库）。
    ///
    /// ==================================================================
    /// 【连接管理策略：一个长连接 + 一把锁】
    /// ==================================================================
    ///   存档库的访问模式是"低频、极小、偶尔并发"（一局结束写一次、每次改设置写一次），
    ///   所以：
    ///     · 不做连接池 —— 池化在这里只增加复杂度，没有任何收益；
    ///     · 用一个**长连接**（打开一次，一直用到进程退出），避免每次操作都 open/close
    ///       带来的文件句柄抖动；
    ///     · 打开时带 `SQLITE_OPEN_FULLMUTEX`，并在托管侧再加一把锁，
    ///       于是"主线程写档 + 后台线程读档"也不会踩到 prepared statement 的竞态。
    ///
    /// 【语句不缓存】每条 SQL 走一次 prepare → bind → step → finalize。
    ///   prepare 的解析开销在这个调用频率下完全可以忽略（微秒级），
    ///   而缓存会引入"语句句柄泄漏 / schema 变更后失效"这两类难查的问题。
    ///
    /// 【资源释放】所有语句都在 try/finally 里 finalize；Dispose 关连接。
    ///   即使中途抛异常也不会留下悬空的 statement 句柄。
    /// </summary>
    internal sealed class SqliteDatabase : IDatabase
    {
        private IntPtr _db = IntPtr.Zero;
        private readonly object _gate = new object();
        private bool _open;
        private int _txDepth;
        private string _path;
        private string _version;

        // ------------------------------------------------------------------
        // 打开 / 关闭
        // ------------------------------------------------------------------

        /// <summary>
        /// 尝试打开数据库。**不抛异常**，失败时返回 false 并给出原因文本。
        ///
        /// 【为什么要"尝试"而不是"直接打开"】原生库可能不存在（例如换了平台却没带库、
        /// 精简版 Windows 缺少 winsqlite3）。这种情况必须能让上层优雅降级到 JSON 存档，
        /// 而不是把玩家挡在启动画面外。
        /// </summary>
        public static bool TryOpen(string path, out SqliteDatabase db, out string error)
        {
            db = null;
            error = null;
            SqliteDatabase instance = new SqliteDatabase();
            try
            {
                IntPtr handle;
                int rc = SqliteNative.Open(
                    Utf8Z(path), out handle,
                    SqliteNative.OPEN_READWRITE | SqliteNative.OPEN_CREATE | SqliteNative.OPEN_FULLMUTEX,
                    IntPtr.Zero);

                if (rc != SqliteNative.OK || handle == IntPtr.Zero)
                {
                    error = "sqlite3_open_v2 失败，返回码 " + rc;
                    if (handle != IntPtr.Zero)
                    {
                        SqliteNative.Close(handle);
                    }
                    return false;
                }

                instance._db = handle;
                instance._path = path;
                instance._open = true;

                try
                {
                    IntPtr vp = SqliteNative.LibVersion();
                    instance._version = PtrToUtf8Z(vp);
                }
                catch (Exception)
                {
                    instance._version = "unknown";
                }

                SqliteNative.BusyTimeout(handle, 5000);
                instance.ApplyPragmas();
                db = instance;
                return true;
            }
            catch (DllNotFoundException ex)
            {
                error = "找不到原生 SQLite 库（" + SqliteNative.Library + "）：" + ex.Message;
                instance.SafeClose();
                return false;
            }
            catch (EntryPointNotFoundException ex)
            {
                error = "原生库缺少所需导出函数： " + ex.Message;
                instance.SafeClose();
                return false;
            }
            catch (Exception ex)
            {
                error = "打开数据库异常：" + ex.Message;
                instance.SafeClose();
                return false;
            }
        }

        /// <summary>
        /// 打开时统一设置 PRAGMA。逐条注释见下方，配置理由集中在函数头。
        ///
        /// · journal_mode=WAL  —— 写不阻塞读，且崩溃后能自动恢复；
        ///                        存档在移动端被杀进程是常态，这一点很关键。
        /// · synchronous=NORMAL —— WAL 下的推荐档位：进程崩溃不会丢已提交数据，
        ///                        只在操作系统级掉电时可能丢最后几条。存档可以接受。
        /// · foreign_keys=ON   —— 让快照子表随主表级联删除，避免"孤儿塔"。
        /// · temp_store=MEMORY —— 临时结果放内存，省掉 sd 卡上的临时文件。
        /// </summary>
        private void ApplyPragmas()
        {
            ExecRaw("PRAGMA journal_mode=WAL;");
            ExecRaw("PRAGMA synchronous=NORMAL;");
            ExecRaw("PRAGMA foreign_keys=ON;");
            ExecRaw("PRAGMA temp_store=MEMORY;");
        }

        /// <summary>执行一条不需要参数、不关心结果的语句（PRAGMA / DDL）。失败只告警。</summary>
        private void ExecRaw(string sql)
        {
            try
            {
                Execute(sql);
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[DB] PRAGMA 设置失败（可忽略）：" + sql + " → " + ex.Message);
            }
        }

        public bool IsOpen { get { return _open; } }

        public string BackendName
        {
            get { return "SQLite " + (_version ?? "?"); }
        }

        public string DatabasePath { get { return _path; } }

        // ------------------------------------------------------------------
        // 写 / 查
        // ------------------------------------------------------------------

        public int Execute(string sql, params object[] args)
        {
            lock (_gate)
            {
                EnsureOpen();
                IntPtr stmt = PrepareStatement(sql, args);
                try
                {
                    StepToCompletion(stmt, sql);
                    return SqliteNative.Changes(_db);
                }
                finally
                {
                    SqliteNative.Finalize(stmt);
                }
            }
        }

        public long ExecuteInsert(string sql, params object[] args)
        {
            lock (_gate)
            {
                EnsureOpen();
                IntPtr stmt = PrepareStatement(sql, args);
                try
                {
                    StepToCompletion(stmt, sql);
                    return SqliteNative.LastInsertRowId(_db);
                }
                finally
                {
                    SqliteNative.Finalize(stmt);
                }
            }
        }

        public List<DbRow> Query(string sql, params object[] args)
        {
            lock (_gate)
            {
                EnsureOpen();
                IntPtr stmt = PrepareStatement(sql, args);
                try
                {
                    List<DbRow> rows = new List<DbRow>();
                    int rc;
                    while ((rc = SqliteNative.Step(stmt)) == SqliteNative.ROW)
                    {
                        rows.Add(ReadRow(stmt));
                    }
                    if (rc != SqliteNative.DONE)
                    {
                        throw MakeException(rc, sql);
                    }
                    return rows;
                }
                finally
                {
                    SqliteNative.Finalize(stmt);
                }
            }
        }

        public DbRow QuerySingle(string sql, params object[] args)
        {
            lock (_gate)
            {
                EnsureOpen();
                IntPtr stmt = PrepareStatement(sql, args);
                try
                {
                    int rc = SqliteNative.Step(stmt);
                    if (rc == SqliteNative.ROW)
                    {
                        return ReadRow(stmt);
                    }
                    if (rc != SqliteNative.DONE)
                    {
                        throw MakeException(rc, sql);
                    }
                    return null;
                }
                finally
                {
                    SqliteNative.Finalize(stmt);
                }
            }
        }

        public T QueryScalar<T>(string sql, T defaultValue, params object[] args)
        {
            DbRow row = QuerySingle(sql, args);
            if (row == null || row.ColumnCount == 0)
            {
                return defaultValue;
            }
            object raw = row.GetRaw(row.GetColumnName(0));
            if (raw == null || raw is DBNull)
            {
                return defaultValue;
            }
            return ConvertScalar<T>(raw, defaultValue);
        }

        // ------------------------------------------------------------------
        // 事务
        // ------------------------------------------------------------------

        public IDbTransaction BeginTransaction()
        {
            lock (_gate)
            {
                EnsureOpen();
                if (_txDepth == 0)
                {
                    // IMMEDIATE：立刻拿写锁，避免在"读→改→写"的临界区里
                    // 到提交那一刻才发现拿不到锁而失败（那会让整个事务白做）。
                    ExecInner("BEGIN IMMEDIATE;");
                }
                _txDepth++;
                return new SqliteTransaction(this);
            }
        }

        /// <summary>内层事务句柄调用：只有最外层真正提交/回滚。</summary>
        internal void EndTransaction(bool commit)
        {
            lock (_gate)
            {
                if (_txDepth <= 0)
                {
                    return;
                }
                _txDepth--;
                if (_txDepth > 0)
                {
                    return;
                }
                try
                {
                    ExecInner(commit ? "COMMIT;" : "ROLLBACK;");
                }
                catch (Exception ex)
                {
                    Debug.LogError("[DB] " + (commit ? "COMMIT" : "ROLLBACK") + " 失败：" + ex.Message);
                }
            }
        }

        private void ExecInner(string sql)
        {
            IntPtr stmt = PrepareStatement(sql, null);
            try
            {
                StepToCompletion(stmt, sql);
            }
            finally
            {
                SqliteNative.Finalize(stmt);
            }
        }

        public void Flush()
        {
            lock (_gate)
            {
                if (!_open)
                {
                    return;
                }
                try
                {
                    // 把 WAL 收拢回主库文件。失败不影响正确性（WAL 里的数据不会丢），
                    // 所以这里吞掉异常只做提示 —— 关机流程里绝不能因为 checkpoint 失败而报错。
                    ExecInner("PRAGMA wal_checkpoint(TRUNCATE);");
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[DB] wal_checkpoint 失败（可忽略）：" + ex.Message);
                }
            }
        }

        // ------------------------------------------------------------------
        // 内部：语句准备 / 绑定 / 读取
        // ------------------------------------------------------------------

        private void EnsureOpen()
        {
            if (!_open || _db == IntPtr.Zero)
            {
                throw new DatabaseException("数据库连接已关闭", null, 0);
            }
        }

        /// <summary>准备语句并绑定全部参数。失败时抛异常（语句句柄已回收）。</summary>
        private IntPtr PrepareStatement(string sql, object[] args)
        {
            if (string.IsNullOrEmpty(sql))
            {
                throw new DatabaseException("SQL 为空", sql, 0);
            }
            byte[] sqlBytes = Encoding.UTF8.GetBytes(sql);
            IntPtr stmt;
            // 传精确长度（而非 -1）：这样 SQL 不需要以 0 结尾，也就没有"越界读"的风险。
            int rc = SqliteNative.Prepare(_db, sqlBytes, sqlBytes.Length, out stmt, IntPtr.Zero);
            if (rc != SqliteNative.OK || stmt == IntPtr.Zero)
            {
                throw MakeException(rc, sql);
            }
            try
            {
                Bind(stmt, args, sql);
            }
            catch
            {
                SqliteNative.Finalize(stmt);
                throw;
            }
            return stmt;
        }

        private void Bind(IntPtr stmt, object[] args, string sql)
        {
            if (args == null || args.Length == 0)
            {
                return;
            }
            for (int i = 0; i < args.Length; i++)
            {
                // 占位符下标从 1 开始，所以这里 +1。
                int index = i + 1;
                object v = args[i];
                int rc;
                if (v == null || v is DBNull)
                {
                    rc = SqliteNative.BindNull(stmt, index);
                }
                else if (v is byte[])
                {
                    byte[] b = (byte[])v;
                    // SQLITE_TRANSIENT：让 SQLite 立刻拷贝，避免托管数组被 GC 后读到脏内存。
                    rc = SqliteNative.BindBlob(stmt, index, b, b.Length, SqliteNative.TRANSIENT);
                }
                else if (v is string)
                {
                    byte[] b = Encoding.UTF8.GetBytes((string)v);
                    rc = SqliteNative.BindText(stmt, index, b, b.Length, SqliteNative.TRANSIENT);
                }
                else if (v is bool)
                {
                    rc = SqliteNative.BindInt64(stmt, index, ((bool)v) ? 1L : 0L);
                }
                else if (v is float || v is double || v is decimal)
                {
                    rc = SqliteNative.BindDouble(stmt, index, Convert.ToDouble(v, CultureInfo.InvariantCulture));
                }
                else if (v is sbyte || v is byte || v is short || v is ushort ||
                         v is int || v is uint || v is long || v is ulong)
                {
                    rc = SqliteNative.BindInt64(stmt, index, Convert.ToInt64(v, CultureInfo.InvariantCulture));
                }
                else if (v is Enum)
                {
                    rc = SqliteNative.BindInt64(stmt, index, Convert.ToInt64(v, CultureInfo.InvariantCulture));
                }
                else
                {
                    byte[] b = Encoding.UTF8.GetBytes(Convert.ToString(v, CultureInfo.InvariantCulture));
                    rc = SqliteNative.BindText(stmt, index, b, b.Length, SqliteNative.TRANSIENT);
                }

                if (rc != SqliteNative.OK)
                {
                    throw MakeException(rc, sql);
                }
            }
        }

        /// <summary>把语句执行到结束。语句自带结果集时（DONE 之前的 ROW）直接丢弃。</summary>
        private void StepToCompletion(IntPtr stmt, string sql)
        {
            int rc;
            while ((rc = SqliteNative.Step(stmt)) == SqliteNative.ROW)
            {
                // 故意空转：调用方要的是"执行完"，结果集由 Query 系列负责。
            }
            if (rc != SqliteNative.DONE)
            {
                throw MakeException(rc, sql);
            }
        }

        private DbRow ReadRow(IntPtr stmt)
        {
            int n = SqliteNative.ColumnCount(stmt);
            string[] names = new string[n];
            object[] values = new object[n];
            for (int i = 0; i < n; i++)
            {
                names[i] = PtrToUtf8Z(SqliteNative.ColumnName(stmt, i));
                int type = SqliteNative.ColumnType(stmt, i);
                switch (type)
                {
                    case SqliteNative.TYPE_INTEGER:
                        values[i] = SqliteNative.ColumnInt64(stmt, i);
                        break;
                    case SqliteNative.TYPE_FLOAT:
                        values[i] = SqliteNative.ColumnDouble(stmt, i);
                        break;
                    case SqliteNative.TYPE_TEXT:
                        int len = SqliteNative.ColumnBytes(stmt, i);
                        // 【空串 ≠ NULL】UTF-8 长度 0 表示"存的是空字符串"，
                        // 必须还原成 string.Empty；若返回 null，调用方就无法区分
                        // "这个键存在但值为空" 与 "这个键根本不存在"。
                        values[i] = len <= 0 ? string.Empty : PtrToUtf8(SqliteNative.ColumnText(stmt, i), len);
                        break;
                    case SqliteNative.TYPE_BLOB:
                        int blen = SqliteNative.ColumnBytes(stmt, i);
                        values[i] = PtrToBytes(SqliteNative.ColumnBlob(stmt, i), blen);
                        break;
                    default:
                        values[i] = null;
                        break;
                }
            }
            return new DbRow(names, values);
        }

        private DatabaseException MakeException(int rc, string sql)
        {
            string msg = "(无法读取错误信息)";
            try
            {
                if (_db != IntPtr.Zero)
                {
                    msg = PtrToUtf8Z(SqliteNative.ErrMsg(_db));
                    int ext = SqliteNative.ExtendedErrCode(_db);
                    if (ext != 0)
                    {
                        msg = msg + "（extended code " + ext + "）";
                    }
                }
            }
            catch (Exception)
            {
                // 取错误信息本身失败时，不要掩盖原始错误。
            }
            return new DatabaseException("SQLite 错误 " + rc + "：" + msg, sql, rc);
        }

        // ------------------------------------------------------------------
        // 内部：UTF-8 与指针互转
        // ------------------------------------------------------------------

        /// <summary>托管字符串 → 以 0 结尾的 UTF-8 字节（给只接受 C 字符串的原生接口用）。</summary>
        internal static byte[] Utf8Z(string s)
        {
            byte[] body = Encoding.UTF8.GetBytes(s ?? string.Empty);
            byte[] z = new byte[body.Length + 1];
            Buffer.BlockCopy(body, 0, z, 0, body.Length);
            return z;
        }

        /// <summary>把原生 UTF-8 指针按给定长度解成字符串（不依赖 0 结尾）。</summary>
        internal static string PtrToUtf8(IntPtr p, int byteLength)
        {
            if (p == IntPtr.Zero || byteLength <= 0)
            {
                return null;
            }
            byte[] buf = new byte[byteLength];
            Marshal.Copy(p, buf, 0, byteLength);
            return Encoding.UTF8.GetString(buf, 0, buf.Length);
        }

        private static byte[] PtrToBytes(IntPtr p, int byteLength)
        {
            if (p == IntPtr.Zero || byteLength <= 0)
            {
                return null;
            }
            byte[] buf = new byte[byteLength];
            Marshal.Copy(p, buf, 0, byteLength);
            return buf;
        }

        /// <summary>读取以 0 结尾的原生 UTF-8 字符串（errmsg / column_name / libversion）。</summary>
        internal static string PtrToUtf8Z(IntPtr p)
        {
            if (p == IntPtr.Zero)
            {
                return null;
            }
            int len = 0;
            // 上限只是防御性护栏：原生字符串不可能超过这个长度，
            // 万一拿到野指针也不会把进程读挂。
            while (len < 65536 && Marshal.ReadByte(p, len) != 0)
            {
                len++;
            }
            return PtrToUtf8(p, len);
        }

        // ------------------------------------------------------------------
        // 标量类型转换
        // ------------------------------------------------------------------

        private static T ConvertScalar<T>(object raw, T defaultValue)
        {
            Type t = typeof(T);
            try
            {
                if (t == typeof(string))
                {
                    string s = raw as string;
                    if (s == null)
                    {
                        byte[] b = raw as byte[];
                        s = b != null ? Encoding.UTF8.GetString(b) : Convert.ToString(raw, CultureInfo.InvariantCulture);
                    }
                    return (T)(object)s;
                }
                if (t == typeof(int)) return (T)(object)(int)Convert.ToInt64(raw, CultureInfo.InvariantCulture);
                if (t == typeof(long)) return (T)(object)Convert.ToInt64(raw, CultureInfo.InvariantCulture);
                if (t == typeof(short)) return (T)(object)(short)Convert.ToInt64(raw, CultureInfo.InvariantCulture);
                if (t == typeof(byte)) return (T)(object)(byte)Convert.ToInt64(raw, CultureInfo.InvariantCulture);
                if (t == typeof(double)) return (T)(object)Convert.ToDouble(raw, CultureInfo.InvariantCulture);
                if (t == typeof(float)) return (T)(object)(float)Convert.ToDouble(raw, CultureInfo.InvariantCulture);
                if (t == typeof(decimal)) return (T)(object)Convert.ToDecimal(raw, CultureInfo.InvariantCulture);
                if (t == typeof(bool)) return (T)(object)(Convert.ToInt64(raw, CultureInfo.InvariantCulture) != 0L);
                if (t == typeof(byte[]))
                {
                    byte[] b = raw as byte[];
                    if (b != null) return (T)(object)b;
                    return (T)(object)Encoding.UTF8.GetBytes(Convert.ToString(raw, CultureInfo.InvariantCulture));
                }
                return (T)Convert.ChangeType(raw, t, CultureInfo.InvariantCulture);
            }
            catch (Exception)
            {
                return defaultValue;
            }
        }

        // ------------------------------------------------------------------
        // 释放
        // ------------------------------------------------------------------

        public void Dispose()
        {
            lock (_gate)
            {
                if (!_open)
                {
                    return;
                }
                try
                {
                    Flush();
                }
                catch (Exception)
                {
                    // 关库流程里不再抛异常。
                }
                _open = false;
                SafeClose();
            }
        }

        private void SafeClose()
        {
            if (_db != IntPtr.Zero)
            {
                try
                {
                    SqliteNative.Close(_db);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[DB] 关闭连接失败：" + ex.Message);
                }
                _db = IntPtr.Zero;
            }
        }
    }
}
