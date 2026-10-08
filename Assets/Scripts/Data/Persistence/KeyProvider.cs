using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace FTProject
{
    /// <summary>主密钥来源。抽成接口是为了将来换成"服务端下发 / 平台 Keychain"实现。</summary>
    public interface IKeyProvider
    {
        /// <summary>取 32 字节主密钥。失败返回 false（上层据此降级为明文存储）。</summary>
        bool TryGetMasterKey(out byte[] masterKey);

        /// <summary>密钥是否是本次启动时"重新生成"的（意味着旧密文已无法解密，需要作废旧数据）。</summary>
        bool KeyWasRotated { get; }

        /// <summary>最近一次失败原因（用于日志）。null 表示无错误。</summary>
        string LastError { get; }
    }

    /// <summary>
    /// 本机密钥管理：**代码里没有任何密钥常量**，主密钥在首次运行时随机生成，
    /// 并**拆成两半分处存放**。
    ///
    /// ==================================================================
    /// 【为什么拆成两半】
    ///   单点存放的问题很直白：只要拿到那一个文件（或那一处偏好设置），密钥就到手了。
    ///   拆开后，攻击者必须**同时**取得两处：
    ///     · 分片 A（16 字节）：`{persistentDataPath}/ft_keystore.bin`，应用私有数据目录；
    ///     · 分片 B（16 字节）：PlayerPrefs（Windows 为当前用户注册表 / iOS 为 NSUserDefaults
    ///       / Android 为 SharedPreferences），属于**另一个存储系统**，
    ///       备份策略、清理工具、提权路径都不一样。
    ///   两处都拿到才能拼出主密钥 —— 这显著抬高了"只改存档文件"这类作弊的门槛。
    ///
    /// 【主密钥怎么来的】master = HMAC-SHA256(key = "FT.Persistence/master/v1", data = A ‖ B)。
    ///   即把两分片按固定顺序拼起来，再用带标签的 HMAC 做一次 KDF 展开，
    ///   保证输出是 32 字节且与输入分布无关。
    ///
    /// 【一致性校验】文件里除分片 A 外还存了 8 字节校验值 check = HMAC(A, B)[0..8]。
    ///   它解决一个很隐蔽的故障：玩家用备份工具只还原了 `ft_keystore.bin`（A 变回旧的），
    ///   而 PlayerPrefs 里的 B 是新的 —— 此时 A/B 拼接能算出"一把看起来正常"的密钥，
    ///   但解不开任何旧数据，症状是"存档莫名其妙全没了"。
    ///   有 check 就能识别出"两半不是同一代"，直接走轮换流程并给出明确日志。
    ///
    /// 【威胁模型（必须说清楚）】
    ///   这是**客户端本地加密**，能防的是：直接改存档文件、翻看明文、简单内存/文件篡改。
    ///   防不了的是：具有 root/越权能力、能 dump 进程内存或 hook 运行时的攻击者 ——
    ///   密钥最终必须在客户端参与运算，这是本地加密的固有上限。
    ///   需要真正抗作弊时，应把**关键数值的权威判定放到服务端**，本地加密只当第一道门槛。
    /// ==================================================================
    /// </summary>
    public sealed class LocalKeyProvider : IKeyProvider
    {
        private const string PrefsKey = "FT.KeyShard.B.v1";
        private const string MasterLabel = "FT.Persistence/master/v1";
        private const string CheckLabel = "FT.Persistence/check/v1";
        private const string FileName = "ft_keystore.bin";

        /// <summary>调试用：设置该环境变量（Base64 的 32 字节）可强制指定主密钥，便于自动化测试。</summary>
        private const string EnvOverride = "FT_SAVE_KEY";

        private const int ShardSize = 16;
        private const int CheckSize = 8;

        public bool KeyWasRotated { get; private set; }

        public string LastError { get; private set; }

        /// <summary>密钥文件完整路径（排查问题时打印它最快）</summary>
        public static string KeyFilePath
        {
            get { return Path.Combine(Application.persistentDataPath, FileName); }
        }

        public bool TryGetMasterKey(out byte[] masterKey)
        {
            masterKey = null;

            if (TryEnvOverride(out masterKey))
            {
                return true;
            }

            byte[] shardA;
            byte[] shardB;
            string error = LoadShards(out shardA, out shardB);
            if (error != null)
            {
                LastError = error;
                Debug.LogWarning("[Key] 密钥不可用，重新生成：" + error);
                KeyWasRotated = true;
                if (!CreateShards(out shardA, out shardB))
                {
                    LastError = "生成新密钥失败（磁盘不可写？）";
                    Debug.LogError("[Key] " + LastError + "，本次将退化为明文存储。");
                    return false;
                }
            }

            masterKey = DeriveMaster(shardA, shardB);
            return true;
        }

        // ------------------------------------------------------------------
        // 读取 / 生成
        // ------------------------------------------------------------------

        /// <summary>读取并校验两处分片；任何一步不成立都返回非 null 的错误说明。</summary>
        private string LoadShards(out byte[] shardA, out byte[] shardB)
        {
            shardA = null;
            shardB = null;

            string path = KeyFilePath;
            if (!File.Exists(path))
            {
                return "密钥文件不存在（" + path + "）";
            }

            byte[] fileBytes;
            try
            {
                fileBytes = File.ReadAllBytes(path);
            }
            catch (Exception ex)
            {
                return "读取密钥文件失败：" + ex.Message;
            }

            if (fileBytes.Length != ShardSize + CheckSize)
            {
                return "密钥文件长度异常（" + fileBytes.Length + " 字节，期望 " + (ShardSize + CheckSize) + "）";
            }
            byte[] a = new byte[ShardSize];
            byte[] check = new byte[CheckSize];
            Array.Copy(fileBytes, 0, a, 0, ShardSize);
            Array.Copy(fileBytes, ShardSize, check, 0, CheckSize);

            // 分片 B 存在 PlayerPrefs 里（与文件属于不同存储系统）
            string b64 = null;
            try
            {
                b64 = PlayerPrefs.GetString(PrefsKey, null);
            }
            catch (Exception ex)
            {
                return "读取偏好设置中的密钥分片失败：" + ex.Message;
            }
            if (string.IsNullOrEmpty(b64))
            {
                return "偏好设置中的密钥分片缺失（密钥文件与偏好设置不同步）";
            }

            byte[] b;
            try
            {
                b = Convert.FromBase64String(b64);
            }
            catch (FormatException)
            {
                return "偏好设置中的密钥分片格式非法";
            }
            if (b.Length != ShardSize)
            {
                return "偏好设置中的密钥分片长度异常（" + b.Length + "）";
            }

            // 校验：确认文件里的 A 与偏好设置里的 B 属于同一代
            byte[] expect = Hmac(Concat(a, b), CheckLabel, CheckSize);
            if (!FixedTimeEquals(expect, check))
            {
                return "密钥两半分片不属于同一代（可能只还原了其中一处备份）";
            }

            shardA = a;
            shardB = b;
            return null;
        }

        /// <summary>生成并持久化一对新分片。</summary>
        private bool CreateShards(out byte[] shardA, out byte[] shardB)
        {
            shardA = new byte[ShardSize];
            shardB = new byte[ShardSize];
            using (RandomNumberGenerator rng = RandomNumberGenerator.Create())
            {
                rng.GetBytes(shardA);
                rng.GetBytes(shardB);
            }

            byte[] check = Hmac(Concat(shardA, shardB), CheckLabel, CheckSize);
            byte[] fileBytes = Concat(shardA, check);

            try
            {
                // 先写临时文件再原子替换：直接覆写时若中途崩溃，会留下半截文件，
                // 下次启动就变成"密钥损坏"，玩家的存档会整批作废。
                string path = KeyFilePath;
                string tmp = path + ".tmp";
                File.WriteAllBytes(tmp, fileBytes);
                if (File.Exists(path))
                {
                    File.Delete(path);
                }
                File.Move(tmp, path);

                PlayerPrefs.SetString(PrefsKey, Convert.ToBase64String(shardB));
                PlayerPrefs.Save();
                return true;
            }
            catch (Exception ex)
            {
                LastError = "写入密钥失败：" + ex.Message;
                return false;
            }
        }

        private static byte[] DeriveMaster(byte[] shardA, byte[] shardB)
        {
            return Hmac(Concat(shardA, shardB), MasterLabel, 32);
        }

        // ------------------------------------------------------------------
        // 调试覆盖
        // ------------------------------------------------------------------

        private static bool TryEnvOverride(out byte[] masterKey)
        {
            masterKey = null;
            string raw = null;
            try
            {
                raw = Environment.GetEnvironmentVariable(EnvOverride);
            }
            catch (Exception)
            {
                return false;
            }
            if (string.IsNullOrEmpty(raw))
            {
                return false;
            }
            try
            {
                byte[] key = Convert.FromBase64String(raw);
                if (key.Length < 16)
                {
                    Debug.LogWarning("[Key] 环境变量 " + EnvOverride + " 长度不足，已忽略。");
                    return false;
                }
                Debug.LogWarning("[Key] 正在使用环境变量指定的调试密钥（" + EnvOverride + "），请勿用于正式构建。");
                masterKey = key;
                return true;
            }
            catch (FormatException)
            {
                Debug.LogWarning("[Key] 环境变量 " + EnvOverride + " 不是合法 Base64，已忽略。");
                return false;
            }
        }

        // ------------------------------------------------------------------
        // 工具
        // ------------------------------------------------------------------

        private static byte[] Hmac(byte[] key, string label, int outLen)
        {
            byte[] mac;
            using (HMACSHA256 h = new HMACSHA256(key))
            {
                mac = h.ComputeHash(Encoding.UTF8.GetBytes(label));
            }
            if (mac.Length == outLen)
            {
                return mac;
            }
            byte[] r = new byte[outLen];
            Array.Copy(mac, r, Math.Min(outLen, mac.Length));
            return r;
        }

        private static byte[] Concat(byte[] a, byte[] b)
        {
            byte[] r = new byte[a.Length + b.Length];
            Array.Copy(a, 0, r, 0, a.Length);
            Array.Copy(b, 0, r, a.Length, b.Length);
            return r;
        }

        private static bool FixedTimeEquals(byte[] a, byte[] b)
        {
            if (a == null || b == null || a.Length != b.Length)
            {
                return false;
            }
            int diff = 0;
            for (int i = 0; i < a.Length; i++)
            {
                diff |= a[i] ^ b[i];
            }
            return diff == 0;
        }
    }
}
