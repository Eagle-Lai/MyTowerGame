using System;
using System.Collections.Generic;
using System.Globalization;

namespace FTProject
{
    /// <summary>
    /// 一行查询结果（列名 → 值）。
    ///
    /// 【为什么不用 DataTable / DataRow】那是 System.Data 的东西，Unity 的
    /// .NET Standard 2.1 剖面里没有 System.Data；而且我们的查询都是小结果集，
    /// 一个"列名 → 值"的轻量容器足够了。
    ///
    /// 【取值一律不抛异常】列名写错、类型对不上、值为 NULL —— 都返回调用方给的默认值。
    /// 读档路径上抛异常等于"玩家进不去游戏"，这个代价太大；真正的错误由
    /// 建表/迁移阶段的严格校验去拦（见 SaveSchema）。
    /// </summary>
    public sealed class DbRow
    {
        private readonly string[] _names;
        private readonly object[] _values;
        private readonly Dictionary<string, int> _index;

        public DbRow(string[] names, object[] values)
        {
            _names = names != null ? names : new string[0];
            _values = values != null ? values : new object[0];
            // 列名大小写不敏感：SQLite 的列名比对就是大小写不敏感的，
            // 这里保持一致，避免 `SELECT Stars ...` 之后用 row.GetInt("stars") 取不到。
            _index = new Dictionary<string, int>(_names.Length, StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < _names.Length; i++)
            {
                string n = _names[i];
                if (!string.IsNullOrEmpty(n) && !_index.ContainsKey(n))
                {
                    _index.Add(n, i);
                }
            }
        }

        public int ColumnCount { get { return _names.Length; } }

        public string GetColumnName(int i)
        {
            return (i >= 0 && i < _names.Length) ? _names[i] : null;
        }

        public bool HasColumn(string column)
        {
            return !string.IsNullOrEmpty(column) && _index.ContainsKey(column);
        }

        public bool IsNull(string column)
        {
            object v = GetRaw(column);
            return v == null || v is DBNull;
        }

        /// <summary>取原始值（string / long / double / byte[] / null）。</summary>
        public object GetRaw(string column)
        {
            int i;
            if (string.IsNullOrEmpty(column) || !_index.TryGetValue(column, out i))
            {
                return null;
            }
            return _values[i];
        }

        public string GetString(string column, string defaultValue)
        {
            object v = GetRaw(column);
            if (v == null || v is DBNull)
            {
                return defaultValue;
            }
            string s = v as string;
            if (s != null)
            {
                return s;
            }
            byte[] b = v as byte[];
            if (b != null)
            {
                return System.Text.Encoding.UTF8.GetString(b);
            }
            return Convert.ToString(v, CultureInfo.InvariantCulture);
        }

        public string GetString(string column)
        {
            return GetString(column, null);
        }

        public long GetLong(string column, long defaultValue)
        {
            object v = GetRaw(column);
            if (v == null || v is DBNull)
            {
                return defaultValue;
            }
            if (v is long)
            {
                return (long)v;
            }
            if (v is int)
            {
                return (int)v;
            }
            if (v is double)
            {
                return (long)(double)v;
            }
            long r;
            // 【为什么要走不变文化】`"1.0"` 在德/法语区会被解析成 1，
            // 但 `"1,5"` 这类字符串若按本地文化解析会得到 15 —— 存档必须与语言环境无关。
            return long.TryParse(GetString(column), NumberStyles.Integer, CultureInfo.InvariantCulture, out r)
                ? r : defaultValue;
        }

        public long GetLong(string column)
        {
            return GetLong(column, 0L);
        }

        public int GetInt(string column, int defaultValue)
        {
            return (int)GetLong(column, defaultValue);
        }

        public int GetInt(string column)
        {
            return (int)GetLong(column, 0L);
        }

        public bool GetBool(string column, bool defaultValue)
        {
            long v = GetLong(column, defaultValue ? 1L : 0L);
            return v != 0;
        }

        public bool GetBool(string column)
        {
            return GetBool(column, false);
        }

        public double GetDouble(string column, double defaultValue)
        {
            object v = GetRaw(column);
            if (v == null || v is DBNull)
            {
                return defaultValue;
            }
            if (v is double)
            {
                return (double)v;
            }
            if (v is long)
            {
                return (long)v;
            }
            double r;
            return double.TryParse(GetString(column), NumberStyles.Float, CultureInfo.InvariantCulture, out r)
                ? r : defaultValue;
        }

        public double GetDouble(string column)
        {
            return GetDouble(column, 0d);
        }

        public float GetFloat(string column, float defaultValue)
        {
            return (float)GetDouble(column, defaultValue);
        }

        public float GetFloat(string column)
        {
            return (float)GetDouble(column, 0d);
        }

        public byte[] GetBlob(string column)
        {
            object v = GetRaw(column);
            if (v == null || v is DBNull)
            {
                return null;
            }
            return v as byte[];
        }
    }
}
