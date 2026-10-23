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
        /// 引导期界面（SplashView / LoadingView / HotUpdateView，资产在 Assets/Resources/BootUI/）。
        ///
        /// 【为什么这些 prefab 也要进 AB】它们挂的 View 脚本在**热更程序集**里，
        /// 真机上 Resources 直接加载必然 "missing script"（HybridCLR 官方：挂热更脚本的
        /// 资源必须 AB 打包）。真机时序下 main 场景加载前 ResLoader.Init 已完成
        /// （见 HotUpdateEntry.EnterMainScene），所以 UIManager.Open 能走 ResTable 正常链路。
        /// Assets/Resources/BootUI 的 Resources 兜底仅剩"编辑器未 Init"一种场景。
        /// </summary>
        public const string BootUi = "boot_ui";

        /// <summary>
        /// Reporter 调试控制台图标（Assets/Reporter/Images，收集器 ReporterData 组）。
        ///
        /// 【为什么单独一个包】Reporter 界面图片由运行时动态装配（见
        /// GameSceneLauncher.EnsureReporter 的说明），走 ResTable Reporter_* 逻辑名，
        /// 与游戏 UI 资源解耦；单独成包便于整包管理与将来按需扩展。
        /// </summary>
        public const string Reporter = "reporter";

        /// <summary>
        /// 字体（TMP 字体资产与描边材质）。
        ///
        /// 【为什么要单独分包】全工程 UI 文本统一用 TextMeshPro，字体资产
        /// （`SiYuanSongTi SDF.asset` + 它的图集贴图 + 描边材质）是**所有 UI prefab 的共享依赖**。
        ///   若不给它单独打包，Unity 会把它**隐式复制进每一个引用了它的包**（ui_hud 等），
        ///   字体图集较大，重复打包既浪费包体又是内存隐患。
        ///   单独成包后，各 UI 包只是"引用"它，运行时加载一次即可。
        /// </summary>
        public const string Font = "font";

        /// <summary>不随怪物清单变化的固定包</summary>
        public static readonly string[] Fixed =
        {
            Config, CoreArt, Font, TowerNormal, TowerPower, TowerRetard, BulletNormal, UiHud, BootUi, Reporter
        };

        /// <summary>常驻包：初始化后不参与卸载</summary>
        public static readonly string[] Persistent =
        {
            Config, CoreArt, Font, BootUi, Reporter
        };

        private static string[] _all;

        /// <summary>全部包名（固定包 + 生成的怪物家族包）</summary>
        public static string[] All
        {
            get
            {
                if (_all == null)
                {
                    List<string> list = new List<string>(Fixed.Length + MonsterCatalog.Bundles.Length);
                    list.AddRange(Fixed);
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
