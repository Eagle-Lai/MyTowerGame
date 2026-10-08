using System;
using System.Runtime.InteropServices;

namespace FTProject
{
    /// <summary>
    /// SQLite 原生库的 P/Invoke 声明（只放签名与常量，不放任何业务逻辑）。
    ///
    /// ==================================================================
    /// 【为什么用 P/Invoke 直连原生库，而不是 Mono.Data.Sqlite / sqlite-net】
    /// ==================================================================
    ///   · `Mono.Data.Sqlite.dll` 在 Unity 2022 里**不再随工程自动引用**，
    ///     要手工把 DLL 复制进 Assets/Plugins，Android/iOS 上还要另外带原生库，
    ///     一旦漏了就是"整个工程编译不过"，风险全压在接入方身上。
    ///   · `sqlite-net`（SQLite.cs）是 4000+ 行的第三方单文件，引入即需长期维护。
    ///   · 本项目只用到极少一部分能力（建表、带参增删改查、事务），
    ///     自己写这 30 个函数的绑定，代码量小、无第三方依赖、行为完全可控。
    ///
    /// ==================================================================
    /// 【原生库从哪来：按平台的库名解析】
    /// ==================================================================
    ///   · Windows（编辑器 / 独立版）：`winsqlite3.dll` —— **Windows 10 1709+ 自带的
    ///     完整 SQLite**，位于 C:\Windows\System32，开发期无需随包分发任何二进制。
    ///     （已实测：导出符号齐全，建表/绑定/查询/事务全部可用。）
    ///   · Android：**必须随包自带 `libsqlite3.so`**，见下。
    ///   · iOS：SQLite 是系统库且被静态链接，必须用 "__Internal"。
    ///
    ///   ⚠️ 关于 Android —— 这一点很容易想当然，实际是错的：
    ///     Android 系统里**确实**存在 `/system/lib64/libsqlite3.so`，但它属于
    ///     **平台私有库**；应用 targetSdk ≥ 24 时，链接器（linker namespace）会拒绝
    ///     应用 dlopen 非公开 NDK 库，运行时会直接抛异常。
    ///     所以工程里自带了一份：
    ///       Assets/Plugins/Android/libs/arm64-v8a/libsqlite3.so
    ///       Assets/Plugins/Android/libs/armeabi-v7a/libsqlite3.so
    ///     （与 PlayerSettings 的 AndroidTargetArchitectures = ARMv7|ARM64 对齐；
    ///       由 SQLite 官方 amalgamation 用 Android NDK 交叉编译得到，
    ///       带 `-DSQLITE_OMIT_LOAD_EXTENSION -DHAVE_USLEEP=1`。）
    ///
    ///   ⚠️ 发布到 Windows 独立版时，若想摆脱"依赖操作系统自带的 sqlite3"，
    ///     可自带一份 `sqlite3.dll` 放进 `Assets/Plugins/x86_64/`，
    ///     然后把下面的 <see cref="WindowsLibrary"/> 改成 "sqlite3" 即可 —— 只改这一处。
    /// </summary>
    internal static class SqliteNative
    {
        internal const string WindowsLibrary = "winsqlite3";
        internal const string PosixLibrary = "sqlite3";

#if UNITY_IOS && !UNITY_EDITOR
        internal const string Library = "__Internal";
#elif UNITY_ANDROID && !UNITY_EDITOR
        // 解析到随包分发的 libsqlite3.so（Assets/Plugins/Android/libs/<abi>/）
        internal const string Library = PosixLibrary;
#elif UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
        internal const string Library = WindowsLibrary;
#else
        internal const string Library = PosixLibrary;
#endif

        // ---- 返回码 ----------------------------------------------------
        internal const int OK = 0;
        internal const int ROW = 100;
        internal const int DONE = 101;

        // ---- sqlite3_open_v2 的 flags --------------------------------
        internal const int OPEN_READWRITE = 0x00000002;
        internal const int OPEN_CREATE = 0x00000004;
        // FULLMUTEX：句柄自身串行化。我们用一个长连接跨线程访问，必须开。
        internal const int OPEN_FULLMUTEX = 0x00010000;

        // ---- 列类型（sqlite3_column_type 的返回值）-------------------
        internal const int TYPE_INTEGER = 1;
        internal const int TYPE_FLOAT = 2;
        internal const int TYPE_TEXT = 3;
        internal const int TYPE_BLOB = 4;
        internal const int TYPE_NULL = 5;

        /// <summary>
        /// SQLITE_TRANSIENT：告诉 SQLite "这份数据不归你管，请立刻拷贝一份"。
        /// 【必须用它，不能用 SQLITE_STATIC】我们传进去的是托管 byte[]，
        /// 语句执行完之前就可能被 GC 回收；用 STATIC 会读到已释放内存（表现为随机乱码/崩溃）。
        /// 其定义是 (void(*)(void*))-1。
        /// </summary>
        internal static readonly IntPtr TRANSIENT = new IntPtr(-1);

        // ==================================================================
        // 连接
        // ==================================================================

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_open_v2")]
        internal static extern int Open(byte[] filenameUtf8, out IntPtr db, int flags, IntPtr vfs);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_close_v2")]
        internal static extern int Close(IntPtr db);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_errmsg")]
        internal static extern IntPtr ErrMsg(IntPtr db);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_extended_errcode")]
        internal static extern int ExtendedErrCode(IntPtr db);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_busy_timeout")]
        internal static extern int BusyTimeout(IntPtr db, int ms);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_libversion")]
        internal static extern IntPtr LibVersion();

        // ==================================================================
        // 语句
        // ==================================================================

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_prepare_v2")]
        internal static extern int Prepare(IntPtr db, byte[] sqlUtf8, int numBytes, out IntPtr stmt, IntPtr tail);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_step")]
        internal static extern int Step(IntPtr stmt);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_reset")]
        internal static extern int Reset(IntPtr stmt);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_finalize")]
        internal static extern int Finalize(IntPtr stmt);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_clear_bindings")]
        internal static extern int ClearBindings(IntPtr stmt);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_changes")]
        internal static extern int Changes(IntPtr db);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_last_insert_rowid")]
        internal static extern long LastInsertRowId(IntPtr db);

        // ==================================================================
        // 绑定参数（下标从 1 开始）
        // ==================================================================

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_bind_null")]
        internal static extern int BindNull(IntPtr stmt, int index);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_bind_int64")]
        internal static extern int BindInt64(IntPtr stmt, int index, long value);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_bind_double")]
        internal static extern int BindDouble(IntPtr stmt, int index, double value);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_bind_text")]
        internal static extern int BindText(IntPtr stmt, int index, byte[] valueUtf8, int numBytes, IntPtr destructor);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_bind_blob")]
        internal static extern int BindBlob(IntPtr stmt, int index, byte[] value, int numBytes, IntPtr destructor);

        // ==================================================================
        // 读取列
        // ==================================================================

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_count")]
        internal static extern int ColumnCount(IntPtr stmt);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_name")]
        internal static extern IntPtr ColumnName(IntPtr stmt, int index);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_type")]
        internal static extern int ColumnType(IntPtr stmt, int index);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_int64")]
        internal static extern long ColumnInt64(IntPtr stmt, int index);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_double")]
        internal static extern double ColumnDouble(IntPtr stmt, int index);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_text")]
        internal static extern IntPtr ColumnText(IntPtr stmt, int index);

        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_blob")]
        internal static extern IntPtr ColumnBlob(IntPtr stmt, int index);

        /// <summary>
        /// 取当前列的数据字节数。
        /// 【text 也用它】`sqlite3_column_text` 返回的指针**不保证以 0 结尾**，
        /// 必须配合本函数拿到精确长度再按 UTF-8 解码；用 Marshal.PtrToStringAnsi
        /// 会走系统 ANSI 代码页，中文直接变乱码。
        /// </summary>
        [DllImport(Library, CallingConvention = CallingConvention.Cdecl, EntryPoint = "sqlite3_column_bytes")]
        internal static extern int ColumnBytes(IntPtr stmt, int index);
    }
}
