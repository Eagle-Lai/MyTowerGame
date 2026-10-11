using System.Collections.Generic;

namespace FTProject
{
    /// <summary>一条多语言记录（语言无关的载体）。</summary>
    public struct LocEntry
    {
        public string En;
        public string ZhHans;
        public string ZhHant;

        /// <summary>取指定语言的文本；当前未支持的语言回退英文。</summary>
        public string Get(Language lang)
        {
            switch (lang)
            {
                case Language.ChineseSimplified:  return ZhHans;
                case Language.ChineseTraditional: return ZhHant;
                default:                          return En;
            }
        }
    }

    /// <summary>
    /// key → 多语言文本 的运行时字典。
    ///
    /// 【存在意义】Luban 表 `TBLocalization` 的 `DataList` 只能顺序遍历，
    /// 而 UI 每次取词都是按 key 随机查 —— 建一次字典把查询变成 O(1)。
    /// 【谁负责重建】LanguageManager.RefreshLookup()，在配置表加载完之后调用。
    /// </summary>
    public sealed class LocalizationLookup
    {
        private readonly Dictionary<string, LocEntry> _map = new Dictionary<string, LocEntry>();

        public int Count { get { return _map.Count; } }

        /// <summary>从 Luban 表构建字典。传 null / 空表时不抛异常，只得到空字典。</summary>
        public void Build(cfg.TBLocalization raw)
        {
            _map.Clear();
            if (raw == null || raw.DataList == null)
            {
                return;
            }

            for (int i = 0; i < raw.DataList.Count; i++)
            {
                cfg.Localization r = raw.DataList[i];
                if (r == null || string.IsNullOrEmpty(r.Id))
                {
                    continue;
                }

                LocEntry e;
                e.En = r.En;
                e.ZhHans = r.ZhHans;
                e.ZhHant = r.ZhHant;
                // 重名 key 直接覆盖（不抛异常），与 Configs/AudioTable 的处理风格一致
                _map[r.Id] = e;
            }
        }

        public bool TryGet(string key, out LocEntry entry)
        {
            return _map.TryGetValue(key, out entry);
        }
    }
}
