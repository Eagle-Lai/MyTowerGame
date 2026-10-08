using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace FTProject
{
    /// <summary>键值文件里的一条记录（JsonUtility 要求 [Serializable] + public 字段）。</summary>
    [Serializable]
    public class KvEntry
    {
        public string k;
        public string v;
        public bool sensitive;
    }

    /// <summary>键值文件的根对象。</summary>
    [Serializable]
    public class KvFile
    {
        public List<KvEntry> items = new List<KvEntry>();
    }

    /// <summary>
    /// <see cref="ISaveStorage"/> 的纯托管回退实现：整体 JSON 落盘（内容再整体 AES 加密）。
    ///
    /// ==================================================================
    /// 【它为什么必须存在】
    ///   原生 SQLite 库在个别环境里可能缺失（换平台没带库、精简版系统等）。
    ///   没有回退实现的话，那种情况下玩家连设置都存不了 —— 而这类失败是**环境问题**，
    ///   不该由一个游戏功能来承担。所以架构上把"后端"做成可替换的，
    ///   SQLite 打不开就自动退到这里，功能不减、只是查询能力弱一些。
    ///
    /// 【顺带承担旧存档迁移】
    ///   文件路径与旧版本 SaveManager 使用的 `freetower_save.json` **完全一致**，
    ///   且读取时先尝试解密、不是密文就按明文 JSON 解析 —— 于是老玩家的存档
    ///   可以无缝读入，不需要任何手工迁移步骤。
    /// ==================================================================
    /// </summary>
    internal sealed class JsonSaveStorage : ISaveStorage
    {
        private const string SaveFileName = "freetower_save.json";
        private const string KvFileName = "freetower_kv.json";

        private readonly ICryptoService _crypto;
        private SaveData _data;
        private KvFile _kv;
        private bool _initialized;

        internal JsonSaveStorage(ICryptoService crypto)
        {
            _crypto = crypto;
        }

        public string BackendName { get { return "JSON 文件（SQLite 回退）"; } }

        public string Location
        {
            get { return Path.Combine(Application.persistentDataPath, SaveFileName); }
        }

        private string KvPath
        {
            get { return Path.Combine(Application.persistentDataPath, KvFileName); }
        }

        public bool IsReady { get { return _initialized; } }

        public bool IsEncrypted { get { return _crypto != null && _crypto.IsAvailable; } }

        public string LastError { get; private set; }

        public void Initialize()
        {
            _data = ReadSaveFile();
            _kv = ReadKvFile();
            _initialized = true;
            Debug.Log(string.Format(
                "[Save] 存档后端就绪：{0}\n  位置：{1}\n  内容加密：{2}",
                BackendName, Location, IsEncrypted ? "已启用" : "未启用"));
        }

        // ------------------------------------------------------------------
        // 文件读写
        // ------------------------------------------------------------------

        private SaveData ReadSaveFile()
        {
            string path = Location;
            try
            {
                if (!File.Exists(path))
                {
                    return new SaveData();
                }
                string text = File.ReadAllText(path);
                if (string.IsNullOrEmpty(text))
                {
                    return new SaveData();
                }

                // 先解密。老存档是明文 JSON，Decrypt 会原样返回 → 兼容读入。
                string json = text;
                if (_crypto != null)
                {
                    json = _crypto.Decrypt(text);
                }
                if (string.IsNullOrEmpty(json))
                {
                    return new SaveData();
                }

                SaveData d = JsonUtility.FromJson<SaveData>(json);
                if (d == null)
                {
                    Debug.LogWarning("[Save] 存档解析为 null，按新档处理：" + path);
                    return new SaveData();
                }
                if (d.version != SaveData.CurrentVersion)
                {
                    Debug.LogWarning(string.Format(
                        "[Save] 存档版本 {0} != 当前 {1}，已重置为新档", d.version, SaveData.CurrentVersion));
                    return new SaveData();
                }
                Normalize(d);
                return d;
            }
            catch (Exception ex)
            {
                LastError = "读档失败：" + ex.Message;
                Debug.LogWarning("[Save] " + LastError + "（按新档处理）\n  路径：" + path);
                return new SaveData();
            }
        }

        /// <summary>补齐可能缺失的字段（手改过文件 / 老版本没有该字段）。</summary>
        private static void Normalize(SaveData d)
        {
            if (d.levels == null) d.levels = new List<LevelProgress>();
            if (d.settings == null) d.settings = new GameSettings();
            if (d.snapshot == null) d.snapshot = new LevelSnapshot();
            if (d.snapshot.towers == null) d.snapshot.towers = new List<TowerSnapshot>();
            d.settings.Clamp();
        }

        private void WriteSaveFile()
        {
            try
            {
                string json = JsonUtility.ToJson(_data, true);
                string payload = _crypto != null ? _crypto.Encrypt(json) : json;
                // 同样用"临时文件 + 替换"，避免写一半崩溃留下半截存档。
                string path = Location;
                string tmp = path + ".tmp";
                File.WriteAllText(tmp, payload);
                if (File.Exists(path))
                {
                    File.Delete(path);
                }
                File.Move(tmp, path);
            }
            catch (Exception ex)
            {
                LastError = "写档失败：" + ex.Message;
                Debug.LogWarning("[Save] " + LastError + "\n  路径：" + Location);
            }
        }

        private KvFile ReadKvFile()
        {
            try
            {
                string path = KvPath;
                if (!File.Exists(path))
                {
                    return new KvFile();
                }
                string text = File.ReadAllText(path);
                if (string.IsNullOrEmpty(text))
                {
                    return new KvFile();
                }
                string json = _crypto != null ? _crypto.Decrypt(text) : text;
                KvFile f = JsonUtility.FromJson<KvFile>(json);
                if (f == null)
                {
                    return new KvFile();
                }
                if (f.items == null)
                {
                    f.items = new List<KvEntry>();
                }
                return f;
            }
            catch (Exception ex)
            {
                LastError = "读取键值文件失败：" + ex.Message;
                Debug.LogWarning("[Save] " + LastError + "（按空处理）");
                return new KvFile();
            }
        }

        private void WriteKvFile()
        {
            try
            {
                string json = JsonUtility.ToJson(_kv, true);
                string payload = _crypto != null ? _crypto.Encrypt(json) : json;
                File.WriteAllText(KvPath, payload);
            }
            catch (Exception ex)
            {
                LastError = "写入键值文件失败：" + ex.Message;
                Debug.LogWarning("[Save] " + LastError);
            }
        }

        private KvEntry FindKv(string key)
        {
            if (_kv == null || _kv.items == null)
            {
                return null;
            }
            for (int i = 0; i < _kv.items.Count; i++)
            {
                KvEntry e = _kv.items[i];
                if (e != null && e.k == key)
                {
                    return e;
                }
            }
            return null;
        }

        // ------------------------------------------------------------------
        // ISaveStorage
        // ------------------------------------------------------------------

        public GameSettings LoadSettings()
        {
            return _data != null ? _data.settings : new GameSettings();
        }

        public void SaveSettings(GameSettings settings)
        {
            if (settings == null)
            {
                return;
            }
            settings.Clamp();
            _data.settings = settings;
            WriteSaveFile();
        }

        public List<LevelProgress> LoadLevels()
        {
            return _data != null ? _data.levels : new List<LevelProgress>();
        }

        public void SaveLevel(LevelProgress progress)
        {
            if (progress == null || progress.levelId <= 0)
            {
                return;
            }
            LevelProgress p = _data.GetOrCreate(progress.levelId);
            p.stars = progress.stars;
            p.bestHpLeft = progress.bestHpLeft;
            p.clearCount = progress.clearCount;
            WriteSaveFile();
        }

        public void DeleteLevel(int levelId)
        {
            LevelProgress p = _data.Find(levelId);
            if (p != null)
            {
                _data.levels.Remove(p);
                WriteSaveFile();
            }
        }

        public LevelSnapshot LoadSnapshot()
        {
            return _data != null ? _data.snapshot : new LevelSnapshot();
        }

        public void SaveSnapshot(LevelSnapshot snapshot)
        {
            _data.snapshot = snapshot != null ? snapshot : new LevelSnapshot();
            WriteSaveFile();
        }

        public bool TryGetValue(string key, out string value)
        {
            value = null;
            KvEntry e = FindKv(key);
            if (e == null)
            {
                return false;
            }
            if (e.sensitive && _crypto != null)
            {
                try
                {
                    value = _crypto.Decrypt(e.v);
                }
                catch (Exception ex)
                {
                    LastError = "解密键值失败：" + ex.Message;
                    Debug.LogWarning("[Save] " + LastError);
                    value = null;
                }
            }
            else
            {
                value = e.v;
            }
            return value != null;
        }

        public void SetValue(string key, string value, bool sensitive)
        {
            if (string.IsNullOrEmpty(key))
            {
                return;
            }
            string stored = (sensitive && _crypto != null) ? _crypto.Encrypt(value) : value;
            KvEntry e = FindKv(key);
            if (e == null)
            {
                e = new KvEntry();
                e.k = key;
                _kv.items.Add(e);
            }
            e.v = stored;
            e.sensitive = sensitive;
            WriteKvFile();
        }

        public void DeleteValue(string key)
        {
            KvEntry e = FindKv(key);
            if (e != null)
            {
                _kv.items.Remove(e);
                WriteKvFile();
            }
        }

        public void ResetAll()
        {
            _data = new SaveData();
            _kv = new KvFile();
            try
            {
                if (File.Exists(Location)) File.Delete(Location);
                if (File.Exists(KvPath)) File.Delete(KvPath);
            }
            catch (Exception ex)
            {
                LastError = "删除存档文件失败：" + ex.Message;
                Debug.LogWarning("[Save] " + LastError);
            }
            Debug.Log("[Save] 存档已清空（JSON 后端）");
        }

        public void Flush()
        {
            // JSON 后端每次写入即落盘，没有缓冲需要刷。
        }

        public void Dispose()
        {
            _initialized = false;
        }
    }
}
