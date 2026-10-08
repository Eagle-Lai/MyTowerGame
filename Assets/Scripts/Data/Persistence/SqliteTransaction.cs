using System;

namespace FTProject
{
    /// <summary>
    /// SQLite 事务句柄。
    ///
    /// 【为什么单独成类而不是嵌套在 SqliteDatabase 里】嵌套私有类会让"类的成员声明"
    /// 出现在更深的括号层级，本项目的静态校验脚本（check_code.py 的嵌套层级检查）
    /// 会把它误判为"方法跑到类外面"。平级声明既避开误报，也更易读。
    ///
    /// 【语义】
    ///   · 支持嵌套（SaveManager 可能在外层"存档整体保存"里再调用某个 Upsert），
    ///     但只有最外层那个真正 COMMIT / ROLLBACK；
    ///   · Dispose 而未 Commit 视为 **Rollback** —— 这是"异常时就该什么都不留下"的正确默认；
    ///   · Commit / Rollback / Dispose 都幂等，重复调用不会二次递减事务深度。
    /// </summary>
    internal sealed class SqliteTransaction : IDbTransaction
    {
        private readonly SqliteDatabase _db;
        private bool _finished;

        internal SqliteTransaction(SqliteDatabase db)
        {
            _db = db;
        }

        public bool IsFinished { get { return _finished; } }

        public void Commit()
        {
            if (_finished)
            {
                return;
            }
            _finished = true;
            if (_db != null)
            {
                _db.EndTransaction(true);
            }
        }

        public void Rollback()
        {
            if (_finished)
            {
                return;
            }
            _finished = true;
            if (_db != null)
            {
                _db.EndTransaction(false);
            }
        }

        public void Dispose()
        {
            // 未显式提交 → 回滚。这样 `using (var tx = db.BeginTransaction()) { ... }`
            // 中途抛异常时不会把半截数据留在库里。
            Rollback();
        }
    }
}
