using System;
using System.Security.Cryptography;
using System.Text;

namespace FTProject
{
    /// <summary>
    /// 字段级加解密服务。
    ///
    /// 【设计目标】把"加密"这件事收敛到一个可替换的接口后面，
    ///   让仓储层只关心"这个字段是敏感的 → 交给 ICryptoService"，
    ///   而不需要知道用的是什么算法、密钥从哪来。
    ///   将来换成国密 SM4 或服务端下发的密钥，只替换实现即可。
    ///
    /// 【幂等约定（很重要）】<see cref="Decrypt"/> 对"没有加密标记"的输入**原样返回**。
    ///   这样带来两个好处：
    ///     1. 老版本明文存档可以直接被读到（自动兼容旧数据）；
    ///     2. 同一列可以同时存在明文与密文（加密策略是逐字段开关的），
    ///        不需要为"该列是否已加密"再做一次全表迁移。
    /// </summary>
    public interface ICryptoService
    {
        /// <summary>
        /// 服务是否真的可用（密钥是否正确加载 / 平台是否支持所需算法）。
        /// 为 false 时 <see cref="Encrypt"/> 会原样返回明文 —— 属于降级而非崩溃，
        /// 但上层应当在初始化时把这条信息打出来，避免"以为加密了其实没有"。
        /// </summary>
        bool IsAvailable { get; }

        /// <summary>加密。null / 空串原样返回；已加密的输入不会二次加密。</summary>
        string Encrypt(string plainText);

        /// <summary>解密。未加密的输入原样返回；密文损坏时抛 <see cref="CryptoServiceException"/>。</summary>
        string Decrypt(string cipherText);

        /// <summary>该值是否是本服务产出的密文（用于自检与迁移工具）。</summary>
        bool IsEncrypted(string value);
    }

    /// <summary>密文损坏 / 被篡改 / 版本不认识时抛出。</summary>
    public class CryptoServiceException : Exception
    {
        public CryptoServiceException(string message) : base(message) { }
        public CryptoServiceException(string message, Exception inner) : base(message, inner) { }
    }

    /// <summary>
    /// AES-256-CBC 加密 + HMAC-SHA256 认证实现（Encrypt-then-MAC）。
    ///
    /// ==================================================================
    /// 【为什么不直接用 AES-GCM】
    ///   GCM 更现代，但 `AesGcm` 在 Unity 的 Mono / 部分 IL2CPP 平台上是
    ///   PlatformNotSupportedException 的重灾区。CBC + 独立 HMAC 是**到处都能跑**
    ///   的方案，安全性等价（前提是"先加密后验签"，本实现严格遵循）。
    ///
    /// 【密文封装格式】（定长头 + 变长体，整体再做 Base64 存进 TEXT 列）
    ///   ┌──────┬──────────┬──────────┬────────────────────┐
    ///   │ 版本 │  IV(16)  │ MAC(16)  │  密文（CBC/PKCS7）   │
    ///   │ 1B   │          │          │                     │
    ///   └──────┴──────────┴──────────┴────────────────────┘
    ///   外层文本前缀固定为 "ft1:"。
    ///
    ///   · IV **每次加密都随机重新生成**，并随密文一起保存 —— 复用 IV 会让
    ///     相同明文产出相同密文，等于把"玩家的金币是不是 0"这类信息泄漏出去。
    ///   · MAC 覆盖「版本 ‖ IV ‖ 密文」，因此任何一段被改写都会被验签拦下
    ///     （防止有人直接改动存档里的数字）。
    ///
    /// 【两把子密钥】加密密钥与认证密钥**必须不同**（否则存在跨用途攻击面）。
    ///   它们由同一把主密钥经 HMAC 打上不同标签派生得到，见 DeriveSubKeys。
    /// ==================================================================
    /// </summary>
    public sealed class AesCryptoService : ICryptoService
    {
        /// <summary>密文标记。解密时靠它区分"明文存档"与"密文"。</summary>
        public const string Prefix = "ft1:";

        private const byte Version = 1;
        private const int IvSize = 16;
        private const int MacSize = 16;   // SHA-256 截断到 128 位，足够且省空间

        private readonly byte[] _encKey;
        private readonly byte[] _macKey;
        private readonly bool _available;

        /// <summary>主密钥不可用时的降级实例（原样读写）。</summary>
        private AesCryptoService()
        {
            _available = false;
        }

        private AesCryptoService(byte[] masterKey)
        {
            byte[] enc, mac;
            DeriveSubKeys(masterKey, out enc, out mac);
            _encKey = enc;
            _macKey = mac;
            _available = true;
        }

        /// <summary>
        /// 由主密钥构造服务。主密钥为 null / 长度不足时返回降级实例（IsAvailable == false）。
        /// 【为什么不在构造里抛异常】存档服务不应因为"拿不到密钥"就让游戏起不来，
        ///   降级 + 明确告警是更合适的行为。
        /// </summary>
        public static AesCryptoService Create(byte[] masterKey)
        {
            if (masterKey == null || masterKey.Length < 16)
            {
                return new AesCryptoService();
            }
            try
            {
                return new AesCryptoService(masterKey);
            }
            catch (Exception ex)
            {
                UnityEngine.Debug.LogError("[Crypto] 初始化 AES 失败，将退化为明文存储：" + ex.Message);
                return new AesCryptoService();
            }
        }

        public bool IsAvailable { get { return _available; } }

        // ------------------------------------------------------------------
        // 对外：加解密
        // ------------------------------------------------------------------

        public string Encrypt(string plainText)
        {
            if (string.IsNullOrEmpty(plainText))
            {
                return plainText;
            }
            if (!_available)
            {
                return plainText;   // 降级：明文直存
            }
            if (IsEncrypted(plainText))
            {
                return plainText;   // 已经是密文，不二次加密
            }

            byte[] plain = Encoding.UTF8.GetBytes(plainText);
            // 每次加密都用新的随机 IV —— 复用 IV 会让相同明文产出相同密文。
            byte[] iv = new byte[IvSize];
            using (RandomNumberGenerator rng = RandomNumberGenerator.Create())
            {
                rng.GetBytes(iv);
            }

            byte[] cipher = AesTransform(true, plain, iv);

            // Encrypt-then-MAC：先有完整密文，再对「版本 ‖ IV ‖ 密文」算 MAC。
            byte[] macInput = Concat(new byte[] { Version }, iv, cipher);
            byte[] mac;
            using (HMACSHA256 h = new HMACSHA256(_macKey))
            {
                mac = h.ComputeHash(macInput);
            }

            byte[] envelope = Concat(new byte[] { Version }, iv, Truncate(mac, MacSize), cipher);
            return Prefix + Convert.ToBase64String(envelope);
        }

        public string Decrypt(string cipherText)
        {
            if (string.IsNullOrEmpty(cipherText))
            {
                return cipherText;
            }
            if (!IsEncrypted(cipherText))
            {
                return cipherText;   // 明文（含旧存档）原样返回
            }
            if (!_available)
            {
                throw new CryptoServiceException("数据是加密的，但当前密钥不可用，无法解密。");
            }

            byte[] envelope;
            try
            {
                envelope = Convert.FromBase64String(cipherText.Substring(Prefix.Length));
            }
            catch (FormatException ex)
            {
                throw new CryptoServiceException("密文 Base64 解码失败（数据可能被截断）", ex);
            }

            if (envelope.Length < 1 + IvSize + MacSize)
            {
                throw new CryptoServiceException("密文长度不足，封装头不完整。");
            }
            if (envelope[0] != Version)
            {
                throw new CryptoServiceException(
                    "密文版本 " + envelope[0] + " 不被当前版本（" + Version + "）支持。");
            }

            byte[] iv = new byte[IvSize];
            byte[] mac = new byte[MacSize];
            byte[] cipher = new byte[envelope.Length - 1 - IvSize - MacSize];
            Array.Copy(envelope, 1, iv, 0, IvSize);
            Array.Copy(envelope, 1 + IvSize, mac, 0, MacSize);
            Array.Copy(envelope, 1 + IvSize + MacSize, cipher, 0, cipher.Length);

            byte[] macInput = Concat(new byte[] { Version }, iv, cipher);
            byte[] expected;
            using (HMACSHA256 h = new HMACSHA256(_macKey))
            {
                expected = h.ComputeHash(macInput);
            }
            // 常量时间比较：普通逐字节比较会提前 return，理论上可从耗时差异里
            // 逐字节猜出正确 MAC（时序攻击）。存档虽小，但这是零成本的正确做法。
            if (!FixedTimeEquals(Truncate(expected, MacSize), mac))
            {
                throw new CryptoServiceException("密文完整性校验失败（MAC 不匹配，数据可能被篡改或密钥已更换）。");
            }

            byte[] plain = AesTransform(false, cipher, iv);
            return Encoding.UTF8.GetString(plain);
        }

        public bool IsEncrypted(string value)
        {
            return !string.IsNullOrEmpty(value) && value.StartsWith(Prefix, StringComparison.Ordinal);
        }

        // ------------------------------------------------------------------
        // 内部：算法与工具
        // ------------------------------------------------------------------

        /// <summary>
        /// 由主密钥派生两把子密钥。
        /// 【为什么用 HMAC 打标签而不是"切一半"】切一半要求主密钥足够长，
        ///   而且两半之间可能存在代数关系；用 HMAC(master, "用途标签") 派生是
        ///   标准的 KDF 做法：只要主密钥是密码学随机的，两把子密钥就互相独立。
        /// </summary>
        private static void DeriveSubKeys(byte[] masterKey, out byte[] encKey, out byte[] macKey)
        {
            encKey = HmacSha256(masterKey, "FT.Persistence/enc/v1");
            macKey = HmacSha256(masterKey, "FT.Persistence/mac/v1");
        }

        private static byte[] HmacSha256(byte[] key, string label)
        {
            using (HMACSHA256 h = new HMACSHA256(key))
            {
                return h.ComputeHash(Encoding.UTF8.GetBytes(label));
            }
        }

        /// <summary>一次性的 AES 变换（CBC + PKCS7 正好适合 TransformFinalBlock 单次调用）。</summary>
        private byte[] AesTransform(bool encrypt, byte[] data, byte[] iv)
        {
            using (Aes aes = Aes.Create())
            {
                aes.KeySize = 256;
                aes.BlockSize = 128;
                aes.Mode = CipherMode.CBC;
                aes.Padding = PaddingMode.PKCS7;
                aes.Key = _encKey;
                aes.IV = iv;

                using (ICryptoTransform t = encrypt ? aes.CreateEncryptor() : aes.CreateDecryptor())
                {
                    try
                    {
                        return t.TransformFinalBlock(data, 0, data.Length);
                    }
                    catch (CryptographicException ex)
                    {
                        throw new CryptoServiceException("AES 变换失败（密文损坏或密钥不匹配）", ex);
                    }
                }
            }
        }

        private static byte[] Truncate(byte[] src, int len)
        {
            if (src.Length == len)
            {
                return src;
            }
            byte[] dst = new byte[len];
            Array.Copy(src, dst, Math.Min(len, src.Length));
            return dst;
        }

        /// <summary>
        /// 按顺序拼接若干字节数组。
        /// 【为什么用 params 而不是固定 2/3 参重载】信封由「版本 + IV + MAC + 密文」四段拼成，
        /// MAC 的输入只要三段 —— 固定参数就不得不写多个重载，多一处就多一处调错的风险。
        /// </summary>
        private static byte[] Concat(params byte[][] parts)
        {
            int total = 0;
            for (int i = 0; i < parts.Length; i++)
            {
                total += parts[i].Length;
            }
            byte[] r = new byte[total];
            int offset = 0;
            for (int i = 0; i < parts.Length; i++)
            {
                Array.Copy(parts[i], 0, r, offset, parts[i].Length);
                offset += parts[i].Length;
            }
            return r;
        }

        /// <summary>常量时间比较（长度不同直接判否，长度本身不是秘密）。</summary>
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
