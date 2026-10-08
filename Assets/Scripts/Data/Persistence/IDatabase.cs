using System;
using System.Collections.Generic;

namespace FTProject
{
    /// <summary>
    /// 数据库访问层的统一抽象。
    ///
    /// 【为什么要抽这一层】SQLite 只是"当前选定的后端"，不是架构本身。
    ///   业务/存储层只依赖本接口，所以：
    ///     · 换后端（写死 JSON、内置 KV、服务端同步）不需要动上层代码；
    ///     · 单测里可以塞一个内存假实现，不需要真的落盘。
    ///
    /// 【约定】
    ///   · SQL 一律使用 **参数化占位符**（`?1` / `?2`），禁止字符串拼接 ——
    ///     拼接既是被注入的入口，也会因为中文/引号转义问题直接把语句写坏。
    ///   · 所有方法遇到错误都抛 <see cref="DatabaseException"/>，调用方要么接住降级，
    ///     要么让它上抛；**不允许静默失败**（否则存档"看起来写了"其实没写）。
    /// </summary>
    public interface IDatabase : IDisposable
    {
        /// <summary>连接是否可用</summary>
        bool IsOpen { get; }

        /// <summary>后端标识（日志与自检用），例如 "SQLite 3.43.2" / "JSON"</summary>
        string BackendName { get; }

        /// <summary>数据库文件路径（JSON 回退后端下为 JSON 文件路径）</summary>
        string DatabasePath { get; }

        /// <summary>执行一条写语句（INSERT/UPDATE/DELETE/DDL），返回受影响行数。参数按 ?1、?2… 顺序绑定。</summary>
        int Execute(string sql, params object[] args);

        /// <summary>
        /// 执行一条 INSERT 并返回自增主键（`last_insert_rowid`）。
        /// 与 Execute 分开是为了避免"到处都要再查一次 max(id)"这种既慢又容易错的写法。
        /// </summary>
        long ExecuteInsert(string sql, params object[] args);

        /// <summary>执行查询，返回全部行。结果集不可为空集合（无行时返回空 List，不返回 null）。</summary>
        List<DbRow> Query(string sql, params object[] args);

        /// <summary>查询单行；无结果返回 null。</summary>
        DbRow QuerySingle(string sql, params object[] args);

        /// <summary>
        /// 查询单值。无结果或值为 NULL 时返回 <paramref name="defaultValue"/>。
        /// 内部转成 string 后按不变文化解析，因此 int / long / double / bool 都能用。
        /// </summary>
        T QueryScalar<T>(string sql, T defaultValue, params object[] args);

        /// <summary>
        /// 开启事务。**必须 Dispose**：未 Commit 就 Dispose 会视为 Rollback。
        /// 支持嵌套调用（内层复用外层事务，只有最外层提交/回滚）。
        /// </summary>
        IDbTransaction BeginTransaction();

        /// <summary>把缓冲区落盘（SQLite 下执行 WAL checkpoint）。无缓冲的后端是空实现。</summary>
        void Flush();
    }

    /// <summary>事务句柄。语义见 <see cref="IDatabase.BeginTransaction"/>。</summary>
    public interface IDbTransaction : IDisposable
    {
        /// <summary>提交。可重复调用，只有第一次生效。</summary>
        void Commit();

        /// <summary>回滚。可重复调用，只有第一次生效。</summary>
        void Rollback();

        /// <summary>是否已结束（提交或回滚过）</summary>
        bool IsFinished { get; }
    }

    /// <summary>
    /// 数据层统一异常。
    /// 【为什么不直接抛 SQLite 的返回码】返回码是 int，很容易被无声忽略；
    /// 抛出带语句与错误信息的异常，排查时能直接定位到是哪条 SQL 出了问题。
    /// </summary>
    public class DatabaseException : Exception
    {
        /// <summary>触发出错的 SQL（已截断到 200 字符，避免日志被超长语句刷屏）</summary>
        public string Sql { get; private set; }

        /// <summary>后端原始错误码（SQLite 的 result code）；非 SQLite 后端为 0</summary>
        public int ResultCode { get; private set; }

        public DatabaseException(string message, string sql, int resultCode)
            : base(message)
        {
            Sql = Truncate(sql);
            ResultCode = resultCode;
        }

        public DatabaseException(string message, string sql, int resultCode, Exception inner)
            : base(message, inner)
        {
            Sql = Truncate(sql);
            ResultCode = resultCode;
        }

        private static string Truncate(string sql)
        {
            if (string.IsNullOrEmpty(sql))
            {
                return string.Empty;
            }
            string one = sql.Replace('\n', ' ').Replace('\r', ' ').Trim();
            return one.Length <= 200 ? one : one.Substring(0, 200) + "...";
        }

        public override string ToString()
        {
            return Message + (string.IsNullOrEmpty(Sql) ? string.Empty : "\n  SQL: " + Sql);
        }
    }
}
