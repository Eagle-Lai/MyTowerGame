using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using UnityEngine;

namespace FTProject.AOT
{
    public static class BootLocalization
    {
        private const string Preference = "FT.Boot.Language";
        public static Language Current { get; private set; }
        public static bool HasSelection { get; private set; }
        [Serializable] private class LegacySave { public LegacySettings settings; }
        [Serializable] private class LegacySettings { public string language; }

        public static void Initialize()
        {
            // Read the existing SQLite selection without creating/migrating/writing its database.
            string code = ReadSqlite();
            if (string.IsNullOrEmpty(code))
            {
                try
                {
                    string path = Path.Combine(Application.persistentDataPath, "freetower_save.json");
                    if (File.Exists(path)) code = JsonUtility.FromJson<LegacySave>(File.ReadAllText(path))?.settings?.language;
                }
                catch (Exception e) { Debug.LogWarning("[BootLoc] Legacy save: " + e.Message); }
            }
            if (string.IsNullOrEmpty(code)) code = PlayerPrefs.GetString(Preference, "");
            HasSelection = code == "en" || code == "zh-Hans" || code == "zh-Hant";
            Current = LanguageUtil.FromCode(code);
        }

        public static void Remember(Language language)
        {
            Current = language; HasSelection = true;
            PlayerPrefs.SetString(Preference, language.ToCode());
            PlayerPrefs.Save();
        }

        public static string Get(string key)
        {
            bool traditional = Current == Language.ChineseTraditional;
            if (Current == Language.English) return English(key);
            switch (key)
            {
                case "Preparing": return traditional ? "正在準備啟動資源" : "正在准备启动资源";
                case "Checking": return traditional ? "正在檢查更新" : "正在检查更新";
                case "DLL": return traditional ? "正在下載與校驗程式" : "正在下载与校验程序";
                case "Loading DLL": return traditional ? "正在載入程式" : "正在加载程序";
                case "Initializing": return traditional ? "正在初始化資源" : "正在初始化资源";
                case "Resources": return traditional ? "正在下載與校驗資源" : "正在下载与校验资源";
                case "Offline": return traditional ? "離線：校驗本機資源" : "离线：校验本地资源";
                case "Ready": return traditional ? "更新完成，正在進入遊戲" : "更新完成，正在进入游戏";
                case "Failed": return traditional ? "更新失敗，請重試" : "更新失败，请重试";
                case "Restart": return traditional ? "程式載入失敗，請重新啟動遊戲" : "程序加载失败，请重新启动游戏";
                case "Pause": return traditional ? "暫停" : "暂停";
                case "Resume": return traditional ? "繼續" : "继续";
                case "Retry": return traditional ? "重試" : "重试";
                case "Paused": return traditional ? "已暫停" : "已暂停";
                case "Title": return traditional ? "遊戲更新" : "游戏更新";
                case "Overall": return traditional ? "整體" : "总体";
                case "Stage": return traditional ? "階段" : "阶段";
                default: return key;
            }
        }

        public static string EnglishText(string key) { return English(key); }

        private static string English(string key)
        {
            switch (key)
            {
                case "Preparing": return "Preparing startup files";
                case "Checking": return "Checking for updates";
                case "DLL": return "Downloading and verifying code";
                case "Loading DLL": return "Loading code";
                case "Initializing": return "Initializing resources";
                case "Resources": return "Downloading and verifying resources";
                case "Offline": return "Offline: verifying local resources";
                case "Ready": return "Update complete, entering game";
                case "Failed": return "Update failed. Please retry";
                case "Restart": return "Code loading failed. Please restart the game";
                case "Title": return "GAME UPDATE";
                default: return key;
            }
        }

#if UNITY_EDITOR_WIN || UNITY_STANDALONE_WIN
        private const string Sqlite = "winsqlite3";
#elif UNITY_IOS
        private const string Sqlite = "__Internal";
#else
        private const string Sqlite = "sqlite3";
#endif
        [DllImport(Sqlite, CallingConvention = CallingConvention.Cdecl)] private static extern int sqlite3_open_v2(byte[] path, out IntPtr db, int flags, IntPtr vfs);
        [DllImport(Sqlite, CallingConvention = CallingConvention.Cdecl)] private static extern int sqlite3_prepare_v2(IntPtr db, byte[] sql, int len, out IntPtr stmt, IntPtr tail);
        [DllImport(Sqlite, CallingConvention = CallingConvention.Cdecl)] private static extern int sqlite3_step(IntPtr stmt);
        [DllImport(Sqlite, CallingConvention = CallingConvention.Cdecl)] private static extern IntPtr sqlite3_column_text(IntPtr stmt, int col);
        [DllImport(Sqlite, CallingConvention = CallingConvention.Cdecl)] private static extern int sqlite3_finalize(IntPtr stmt);
        [DllImport(Sqlite, CallingConvention = CallingConvention.Cdecl)] private static extern int sqlite3_close(IntPtr db);

        private static string ReadSqlite()
        {
            IntPtr db = IntPtr.Zero, stmt = IntPtr.Zero;
            try
            {
                string path = Path.Combine(Application.persistentDataPath, "freetower.db");
                if (!File.Exists(path)) return null;
                if (sqlite3_open_v2(Encoding.UTF8.GetBytes(path + "\0"), out db, 1, IntPtr.Zero) != 0) return null;
                byte[] sql = Encoding.UTF8.GetBytes("SELECT v FROM kv_store WHERE k='settings.language' AND sensitive=0 LIMIT 1\0");
                if (sqlite3_prepare_v2(db, sql, sql.Length, out stmt, IntPtr.Zero) != 0) return null;
                return sqlite3_step(stmt) == 100 ? Marshal.PtrToStringAnsi(sqlite3_column_text(stmt, 0)) : null;
            }
            catch (Exception e) { Debug.LogWarning("[BootLoc] Saved language fallback: " + e.Message); return null; }
            finally
            {
                if (stmt != IntPtr.Zero) sqlite3_finalize(stmt);
                if (db != IntPtr.Zero) sqlite3_close(db);
            }
        }
    }
}
