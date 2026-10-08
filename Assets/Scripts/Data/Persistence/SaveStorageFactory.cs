using System;
using System.IO;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 组装并选择存档后端：密钥 → 加密服务 → (SQLite → 失败则 JSON)。
    ///
    /// ==================================================================
    /// 【启动顺序（每一步失败都有明确的降级去向）】
    ///   ① 取密钥（LocalKeyProvider：两处存储各自持有一半，代码里无任何密钥常量）
    ///      ├─ 成功 → 建 AES 服务
    ///      └─ 失败 → 建"降级 AES 服务"（IsAvailable=false，读写走明文）
    ///   ② 尝试打开 SQLite（路径：persistentDataPath/freetower.db）
    ///      ├─ 成功 → 建表/迁移 → 用它
    ///      └─ 失败（原生库缺失、目录只读…）→ 打警告，落到 ③
    ///   ③ JSON 文件后端（顺带兼容旧版明文存档）
    ///
    /// 【为什么降级而不是报错退出】
    ///   这三步里任何一步都是"环境/权限"问题，不是玩家的错。降级之后游戏功能完整，
    ///   只是"没加密"或"没用到 SQL"，而这两种情况都会在日志里留下明确痕迹。
    /// ==================================================================
    /// </summary>
    internal static class SaveStorageFactory
    {
        /// <summary>数据库文件名（放在 Application.persistentDataPath 下）</summary>
        internal const string DatabaseFileName = "freetower.db";

        /// <summary>数据库完整路径（排查问题时打印它最快）</summary>
        internal static string DatabasePath
        {
            get { return Path.Combine(Application.persistentDataPath, DatabaseFileName); }
        }

        /// <summary>创建存档存储。**永不抛异常** —— 最差情况也会返回一个可用的 JSON 后端。</summary>
        internal static ISaveStorage Create()
        {
            ICryptoService crypto = CreateCrypto();

            // ② 优先 SQLite
            string dbPath = DatabasePath;
            SqliteDatabase db;
            string openError;
            if (SqliteDatabase.TryOpen(dbPath, out db, out openError))
            {
                try
                {
                    SqliteSaveStorage storage = new SqliteSaveStorage(db, crypto);
                    storage.Initialize();   // 建表 + 版本迁移；失败会抛
                    return storage;
                }
                catch (Exception ex)
                {
                    Debug.LogError("[Save] 建表/迁移失败，将改用 JSON 后端：" + ex.Message + "\n  位置：" + dbPath);
                    db.Dispose();
                }
            }
            else
            {
                Debug.LogWarning("[Save] 无法使用 SQLite，改用 JSON 文件后端。原因：" + openError);
            }

            // ③ 回退
            JsonSaveStorage fallback = new JsonSaveStorage(crypto);
            fallback.Initialize();
            return fallback;
        }

        // ------------------------------------------------------------------

        private static ICryptoService CreateCrypto()
        {
            LocalKeyProvider provider = new LocalKeyProvider();
            byte[] masterKey;
            if (!provider.TryGetMasterKey(out masterKey))
            {
                Debug.LogError("[Save] 无法取得加密密钥：" + provider.LastError +
                               "\n  敏感数据将以明文存储（功能不受影响）。");
                return AesCryptoService.Create(null);
            }

            ICryptoService crypto = AesCryptoService.Create(masterKey);

            if (!crypto.IsAvailable)
            {
                Debug.LogError("[Save] 加密服务初始化失败，敏感数据将以明文存储。");
            }
            else if (provider.KeyWasRotated)
            {
                // 密钥轮换意味着旧密文已解不开。这里刻意**不删除任何数据**：
                // 解密失败的项会各自退化为默认值（效果等同于新档），
                // 但万一是误判，文件还在，仍有人工抢救的余地。
                Debug.LogWarning(string.Format(
                    "[Save] 检测到密钥已重新生成（原因：{0}）。\n" +
                    "  旧存档中的加密字段将无法解密，会被当作未设置处理（等同新档）。\n" +
                    "  这是预期行为，不是崩溃；仅在你手动删除了 keystore 或偏好设置时才应出现。",
                    provider.LastError));
            }
            return crypto;
        }
    }
}
