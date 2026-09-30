using System.Collections.Generic;

namespace FTProject
{
    /// <summary>
    /// AssetBundle 名常量表。
    ///
    /// 命名规范：全小写下划线，禁止带平台或版本号（由构建脚本按平台分目录）。
    ///
    /// 【怪物分包】怪物按**家族**分包（`enemy_rats` / `enemy_dogs` …），
    /// 包名由 MonsterCatalog 生成代码提供（见 .workbuddy/tools/gen_monster_catalog.py）。
    /// 这样做的意义：119 个怪物若打成一个包，进关卡就要整体加载；
    /// 按家族分包后，只加载**本关波次真正用到的**几个家族，启动与内存都更可控。
    ///
    /// 【为什么 All 是属性而不是常量数组】它要合并"固定包"与"生成的家族包"，
    /// 后者随怪物清单变化，不能在编译期写死。
    /// </summary>
    public static class ResBundle
    {
        /// <summary>配置表 JSON（TextAsset），常驻不卸载</summary>
        public const string Config = "config";

        /// <summary>程序生成的占位美术（格子/箭头/血条/子弹点），常驻不卸载</summary>
        public const string CoreArt = "core_art";

        /// <summary>防御塔：普通（type=1）</summary>
        public const string TowerNormal = "tower_normal";

        /// <summary>防御塔：强力（type=2）</summary>
        public const string TowerPower = "tower_power";

        /// <summary>防御塔：减速（type=3）</summary>
        public const string TowerRetard = "tower_retard";

        /// <summary>子弹</summary>
        public const string BulletNormal = "bullet_normal";

        /// <summary>战斗 HUD 与提示</summary>
        public const string UiHud = "ui_hud";

        /// <summary>
        /// 音效（M2）。逻辑名 Audio_&lt;文件名&gt;，文件来自 Assets/Audio/。
        /// 【注意】该包只在真的存在音频文件时才进入 All（见下面），
        /// 否则打 AB 时会多出一个空包，自检里也会一直提示"包为空"。
        /// </summary>
        public const string Audio = "audio";

        /// <summary>不随怪物清单变化的固定包</summary>
        public static readonly string[] Fixed =
        {
            Config, CoreArt, TowerNormal, TowerPower, TowerRetard, BulletNormal, UiHud
        };

        /// <summary>常驻包：初始化后不参与卸载</summary>
        public static readonly string[] Persistent =
        {
            Config, CoreArt
        };

        private static string[] _all;

        /// <summary>全部包名（固定包 + 生成的怪物家族包）</summary>
        public static string[] All
        {
            get
            {
                if (_all == null)
                {
                    List<string> list = new List<string>(Fixed.Length + MonsterCatalog.Bundles.Length + 1);
                    list.AddRange(Fixed);
                    // 有音频文件才把 audio 包纳入（见 Audio 常量注释）
                    if (AudioCatalog.Count > 0 && !list.Contains(Audio))
                    {
                        list.Add(Audio);
                    }
                    for (int i = 0; i < MonsterCatalog.Bundles.Length; i++)
                    {
                        if (!list.Contains(MonsterCatalog.Bundles[i]))
                        {
                            list.Add(MonsterCatalog.Bundles[i]);
                        }
                    }
                    _all = list.ToArray();
                }
                return _all;
            }
        }

        /// <summary>怪物家族包数量（自检报告用）</summary>
        public static int MonsterBundleCount
        {
            get { return MonsterCatalog.Bundles.Length; }
        }
    }
}
