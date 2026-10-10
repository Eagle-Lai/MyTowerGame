using System.Collections.Generic;

namespace FTProject
{
    /// <summary>
    /// 资源地址总表：逻辑名 → ResAddress。
    ///
    /// 【维护约定】
    ///   1. 业务代码与配置表里的 resName 字段，写的都是这里 key（逻辑名）
    ///   2. 换 AB 分包方案时只改这张表，业务与配置表都不用动
    ///   3. 新增资源必须在此登记，否则运行时会报 "找不到资源地址"
    ///
    /// EditorPath 派生自工程实际目录；Bundle 与 Resources 目录下的目录结构一一对应。
    /// </summary>
    public static class ResTable
    {
        private static readonly Dictionary<string, ResAddress> _map =
            new Dictionary<string, ResAddress>(64)
        {
            // ------------------------------------------------------------------
            // 配置表 JSON
            //
            // 【为什么放 Assets/ConfigJson 而不是 StreamingAssets/json】
            //   StreamingAssets 下的文件被 Unity 当作"原始文件"（DefaultAsset）处理，
            //   **不会导入成 TextAsset** —— 于是会出现一种很隐蔽的故障：
            //   `AssetDatabase.LoadAssetAtPath<Object>()` 能拿到（所以"资源存在"自检通过），
            //   但 `LoadAssetAtPath<TextAsset>()` 返回 null，读配置直接失败。
            //   而配置表既要被编辑器直读、又要被打进 config 包，两者都要求它是普通 Assets 资源。
            //   所以 Luban 的 --output_data_dir 指向 Assets/ConfigJson（见 gen_code_json.bat）。
            // ------------------------------------------------------------------
            { "tbenemydata",  new ResAddress(ResBundle.Config, "tbenemydata",  "Assets/ConfigJson/tbenemydata.json") },
            { "tbtowerinfo",  new ResAddress(ResBundle.Config, "tbtowerinfo",  "Assets/ConfigJson/tbtowerinfo.json") },
            { "tbenemylist",  new ResAddress(ResBundle.Config, "tbenemylist",  "Assets/ConfigJson/tbenemylist.json") },
            { "tbrounddata",  new ResAddress(ResBundle.Config, "tbrounddata",  "Assets/ConfigJson/tbrounddata.json") },
            { "tbsceneinfo",  new ResAddress(ResBundle.Config, "tbsceneinfo",  "Assets/ConfigJson/tbsceneinfo.json") },
            { "tbbulletdata", new ResAddress(ResBundle.Config, "tbbulletdata", "Assets/ConfigJson/tbbulletdata.json") },
            { "tblevelmap",   new ResAddress(ResBundle.Config, "tblevelmap",   "Assets/ConfigJson/tblevelmap.json") },
            { "tbglobal",     new ResAddress(ResBundle.Config, "tbglobal",     "Assets/ConfigJson/tbglobal.json") },
            { "tbaudio",      new ResAddress(ResBundle.Config, "tbaudio",      "Assets/ConfigJson/tbaudio.json") },

            // ------------------------------------------------------------------
            // 程序生成的占位美术（Editor/PlaceholderArtGenerator.cs 产出）
            // ------------------------------------------------------------------
            { "Cell_Ground",  new ResAddress(ResBundle.CoreArt, "Cell_Ground",  "Assets/Art/Generated/Cell_Ground.png") },
            { "Cell_Blocked", new ResAddress(ResBundle.CoreArt, "Cell_Blocked", "Assets/Art/Generated/Cell_Blocked.png") },
            { "Cell_Spawn",   new ResAddress(ResBundle.CoreArt, "Cell_Spawn",   "Assets/Art/Generated/Cell_Spawn.png") },
            { "Cell_End",     new ResAddress(ResBundle.CoreArt, "Cell_End",     "Assets/Art/Generated/Cell_End.png") },
            { "Cell_Buildable", new ResAddress(ResBundle.CoreArt, "Cell_Ground", "Assets/Art/Generated/Cell_Ground.png") },
            { "Path_Arrow",   new ResAddress(ResBundle.CoreArt, "Path_Arrow",   "Assets/Art/Generated/Path_Arrow.png") },
            { "Bullet_Dot",   new ResAddress(ResBundle.CoreArt, "Bullet_Dot",   "Assets/Art/Generated/Bullet_Dot.png") },
            { "HP_Bar_Bg",    new ResAddress(ResBundle.CoreArt, "HP_Bar_Bg",    "Assets/Art/Generated/HP_Bar_Bg.png") },
            { "HP_Bar_Fill",  new ResAddress(ResBundle.CoreArt, "HP_Bar_Fill",  "Assets/Art/Generated/HP_Bar_Fill.png") },
            // 射程提示圈（M2-C2）。登记的是**贴图**而不是 prefab：
            // RangeIndicatorView 走 Load<Sprite> 后运行时建 GameObject，
            // 这样少一个需要在 Unity 里生成的资产，纯代码即可交付。
            { "Range_Ring",   new ResAddress(ResBundle.CoreArt, "Range_Ring",   "Assets/Art/Generated/Range_Ring.png") },

            // ------------------------------------------------------------------
            // 防御塔
            // ------------------------------------------------------------------
            // 【M-3 分等级模型】普通塔也是 3 个**独立 prefab**，每级一套美术：
            //   Tower_Normal0|1|2 → Assets/Prefabs/Tower/Normal/ （贴图 turret[_mkii|_mkiii]_base|barrel_128）
            // 0 级沿用原 Tower_Normal 的美术（turret_base/barrel_128），1/2 级为 mkii/mkiii。
            // ⚠️ 逐级登记而不是靠目录扫描：ResTable 是唯一寻址源，漏登记运行时报"找不到资源地址"。
            // 另注：Pierce(4)/Laser(5) 塔暂无独立美术，配置里仍复用 Tower_Normal0 作占位模型。
            { "Tower_Normal0", new ResAddress(ResBundle.TowerNormal, "Tower_Normal0", "Assets/Prefabs/Tower/Normal/Tower_Normal0.prefab") },
            { "Tower_Normal1", new ResAddress(ResBundle.TowerNormal, "Tower_Normal1", "Assets/Prefabs/Tower/Normal/Tower_Normal1.prefab") },
            { "Tower_Normal2", new ResAddress(ResBundle.TowerNormal, "Tower_Normal2", "Assets/Prefabs/Tower/Normal/Tower_Normal2.prefab") },

            // 塔身贴图显式登记：否则 AB 构建时它们会作为"隐式依赖"被复制进每个引用到的包
            { "Tower_Base_Sprite",        new ResAddress(ResBundle.TowerNormal, "turret_base_128",        "Assets/_UIAssets/Tower/Normal/turret_base_128.png") },
            { "Tower_Barrel_Sprite",      new ResAddress(ResBundle.TowerNormal, "turret_barrel_128",      "Assets/_UIAssets/Tower/Normal/turret_barrel_128.png") },
            { "Tower_Base_Lv2_Sprite",    new ResAddress(ResBundle.TowerNormal, "turret_mkii_base_128",   "Assets/_UIAssets/Tower/Normal/turret_mkii_base_128.png") },
            { "Tower_Barrel_Lv2_Sprite",  new ResAddress(ResBundle.TowerNormal, "turret_mkii_barrel_128", "Assets/_UIAssets/Tower/Normal/turret_mkii_barrel_128.png") },
            { "Tower_Base_Lv3_Sprite",    new ResAddress(ResBundle.TowerNormal, "turret_mkiii_base_128",  "Assets/_UIAssets/Tower/Normal/turret_mkiii_base_128.png") },
            { "Tower_Barrel_Lv3_Sprite",  new ResAddress(ResBundle.TowerNormal, "turret_mkiii_barrel_128","Assets/_UIAssets/Tower/Normal/turret_mkiii_barrel_128.png") },

            // 【M-3 分等级模型】强力塔 / 减速塔各有 3 个**独立 prefab**，每级一套美术：
            //   Tower_Power0|1|2  → Assets/Prefabs/Tower/Power/  （贴图 tower_base[_lv2|_lv3]）
            //   Tower_Retard0|1|2 → Assets/Prefabs/Tower/Retard/ （贴图 slowtower_base[_lv2|_lv3]）
            // tbtowerinfo.json 的 resName 逐级指向它们，升级时 BaseTower 会换实例。
            // ⚠️ 逐级登记而不是靠目录扫描：ResTable 是唯一寻址源，漏登记运行时报"找不到资源地址"。
            { "Tower_Power0", new ResAddress(ResBundle.TowerPower, "Tower_Power0", "Assets/Prefabs/Tower/Power/Tower_Power0.prefab") },
            { "Tower_Power1", new ResAddress(ResBundle.TowerPower, "Tower_Power1", "Assets/Prefabs/Tower/Power/Tower_Power1.prefab") },
            { "Tower_Power2", new ResAddress(ResBundle.TowerPower, "Tower_Power2", "Assets/Prefabs/Tower/Power/Tower_Power2.prefab") },

            { "Tower_Retard0", new ResAddress(ResBundle.TowerRetard, "Tower_Retard0", "Assets/Prefabs/Tower/Retard/Tower_Retard0.prefab") },
            { "Tower_Retard1", new ResAddress(ResBundle.TowerRetard, "Tower_Retard1", "Assets/Prefabs/Tower/Retard/Tower_Retard1.prefab") },
            { "Tower_Retard2", new ResAddress(ResBundle.TowerRetard, "Tower_Retard2", "Assets/Prefabs/Tower/Retard/Tower_Retard2.prefab") },

            // ------------------------------------------------------------------
            // 子弹
            // ------------------------------------------------------------------
            { "Bullet_Normal", new ResAddress(ResBundle.BulletNormal, "Bullet_Normal", "Assets/Prefabs/Bullet/Bullet_Normal.prefab") },

            // ------------------------------------------------------------------
            // 怪物
            //
            // 【为什么这里没有逐条列出来】怪物有 119 个，且会随美术包更新而变化，
            // 逐条手写必然与实际资源分叉。所以改为由**生成代码**提供清单：
            //   Assets/Scripts/Data/MonsterCatalog.cs（见 .workbuddy/tools/gen_monster_catalog.py）
            // 在下面的静态构造里统一登记，规则：
            //   逻辑名      Enemy_<怪名>          → Assets/Prefabs/Enemy/Enemy_<怪名>.prefab
            //   图集        Atlas_<怪名>          → 源目录下的 <怪名>.png
            //   资源包      enemy_<家族小写>      （按家族分包，只加载本关用到的家族）
            // ------------------------------------------------------------------

            // ------------------------------------------------------------------
            // 背景
            // ------------------------------------------------------------------
            { "Background",   new ResAddress(ResBundle.CoreArt, "Paper", "Assets/_UIAssets/Backgrounds/Paper.png") },

            // ------------------------------------------------------------------
            // UI
            // ------------------------------------------------------------------
            { "HudView",      new ResAddress(ResBundle.UiHud, "HudView",  "Assets/Prefabs/UI/HudView.prefab") },
            { "TipsView",     new ResAddress(ResBundle.UiHud, "TipsView", "Assets/Prefabs/UI/TipsView.prefab") },
            { "TowerInfoView", new ResAddress(ResBundle.UiHud, "TowerInfoView", "Assets/Prefabs/UI/TowerInfoView.prefab") },
            { "SelectView",   new ResAddress(ResBundle.UiHud, "SelectView",   "Assets/Prefabs/UI/SelectView.prefab") },
            { "PauseView",    new ResAddress(ResBundle.UiHud, "PauseView",    "Assets/Prefabs/UI/PauseView.prefab") },
            { "SettingView",  new ResAddress(ResBundle.UiHud, "SettingView",  "Assets/Prefabs/UI/SettingView.prefab") },
            { "LevelClearView", new ResAddress(ResBundle.UiHud, "LevelClearView", "Assets/Prefabs/UI/LevelClearView.prefab") },

            // ------------------------------------------------------------------
            // UI 补全（策划案 §3）：启动链 3 + 内容 3 + 弹窗 3
            // ------------------------------------------------------------------
            // 逻辑名一律与 prefab 名逐字相同（UIManager.Open 直接传这个字符串）。
            // ⚠️ **SplashView / LoadingView / HotUpdateView 刻意不在这里登记**：
            //   它们必须在 `ResLoader.Init` 之前就能显示，而 YooAsset 在 Init 完成前拒绝加载资源，
            //   所以走的是 `Resources/BootUI/` 兜底路径（见 UIManager.Open 的说明）。
            //   登记在此反而会误导——让人以为它们走 ui_hud 包。
            // 卡片类资产（TowerCodexItem / MonsterCodexItem）同理**不登记**：
            // 它们只被已登记的 View prefab 直接引用、由 LoopListView2 按 prefab 引用池化克隆，
            // YooAsset 收集整目录树时依赖会自然进同包 —— 与 SelectLevelItem 同理。
            { "MainMenuView",    new ResAddress(ResBundle.UiHud, "MainMenuView",    "Assets/Prefabs/UI/MainMenuView.prefab") },
            { "TowerCodexView",  new ResAddress(ResBundle.UiHud, "TowerCodexView",  "Assets/Prefabs/UI/TowerCodexView.prefab") },
            { "MonsterCodexView",new ResAddress(ResBundle.UiHud, "MonsterCodexView","Assets/Prefabs/UI/MonsterCodexView.prefab") },
            { "LevelDetailView", new ResAddress(ResBundle.UiHud, "LevelDetailView", "Assets/Prefabs/UI/LevelDetailView.prefab") },
            { "SellConfirmView", new ResAddress(ResBundle.UiHud, "SellConfirmView", "Assets/Prefabs/UI/SellConfirmView.prefab") },
            { "ConfirmView",     new ResAddress(ResBundle.UiHud, "ConfirmView",     "Assets/Prefabs/UI/ConfirmView.prefab") },

            // 塔图鉴图标（UI 补全 B2）
            // 【为什么必须登记】图鉴卡片是**池化复用**的同一个模板，5 种塔共用一张卡，
            // 图标只能运行时按塔型换 —— 而 UIPrefabBuilder 生成时烘 sprite 的写法
            // （HudView 建造栏那种）只能表达"固定一张图"，救不了复用场景。
            // 于是这里登记为运行时逻辑名，TowerCodexItem 用 ResLoader.Load<Sprite>() 取。
            { "UI_TowerIcon_Normal", new ResAddress(ResBundle.UiHud, "UI_TowerIcon_Normal", "Assets/_UIAssets/UI/UI_TowerIcon_Normal.png") },
            { "UI_TowerIcon_Power",  new ResAddress(ResBundle.UiHud, "UI_TowerIcon_Power",  "Assets/_UIAssets/UI/UI_TowerIcon_Power.png") },
            { "UI_TowerIcon_Retard", new ResAddress(ResBundle.UiHud, "UI_TowerIcon_Retard", "Assets/_UIAssets/UI/UI_TowerIcon_Retard.png") },
            { "UI_TowerIcon_Pierce", new ResAddress(ResBundle.UiHud, "UI_TowerIcon_Pierce", "Assets/_UIAssets/UI/UI_TowerIcon_Pierce.png") },
            { "UI_TowerIcon_Laser",  new ResAddress(ResBundle.UiHud, "UI_TowerIcon_Laser",  "Assets/_UIAssets/UI/UI_TowerIcon_Laser.png") },

            // ------------------------------------------------------------------
            // 字体（TextMeshPro）
            //
            // 【为什么必须登记】全工程 UI 文本统一用 TMP，其字体资产是 ui_hud 各 prefab 的
            //   共享依赖。登记进 ResTable 有**两个**作用：
            //     ① ABNameSetter 会给它们打上 font 包标记 → 打包时进入独立 font 包，
            //        而不是被隐式复制进每个引用它的 UI 包（字体图集大，重复是浪费）。
            //     ② 自检脚本能核对"登记了 → 文件存在"，字体丢失会被提前发现。
            //   运行时不通过 ResLoader 加载它们（TMP 靠引用直接取用），登记只为打包与自检。
            { "Font_SiYuanSongTi_SDF", new ResAddress(ResBundle.Font, "SiYuanSongTi SDF", "Assets/Font/SiYuanSongTi SDF.asset") },

            // 描边材质（UIPrefabBuilder 生成；不存在时文本退化为无描边，不报错）
            { "Font_Outline_Mat", new ResAddress(ResBundle.Font, "SiYuanSongTi SDF - Outline", "Assets/Font/SiYuanSongTi SDF - Outline.mat") },
        };

        static ResTable()
        {
            RegisterMonsters();
            RegisterAudio();
        }

        /// <summary>
        /// 把 AudioCatalog（生成代码）里的音频登记进来。
        /// 逻辑名 = Audio_&lt;文件名&gt;，与 TBAudio.logicalName 拼上前缀后一致。
        /// 工程里没有音频文件时这里是空循环，不产生任何条目 ——
        /// 于是"没有音效"不会污染自检报告（不会报"登记了但文件不存在"）。
        /// </summary>
        private static void RegisterAudio()
        {
            for (int i = 0; i < AudioCatalog.Count; i++)
            {
                string logical = AudioCatalog.LogicalName(i);
                _map[logical] = new ResAddress(ResBundle.Audio, AudioCatalog.Names[i], AudioCatalog.AssetPaths[i]);
            }
        }

        /// <summary>
        /// 把 MonsterCatalog（生成代码）里的全部怪物登记进来。
        /// 用索引器写入而非 Add：即使清单里出现重名也只会覆盖，不会抛重复键异常。
        /// </summary>
        private static void RegisterMonsters()
        {
            for (int i = 0; i < MonsterCatalog.Count; i++)
            {
                string logical = MonsterCatalog.LogicalName(i);
                string bundle = MonsterCatalog.BundleOf(i);
                _map[logical] = new ResAddress(bundle, logical, MonsterCatalog.PrefabPath(i));

                string atlas = MonsterCatalog.AtlasPaths[i];
                if (!string.IsNullOrEmpty(atlas))
                {
                    // 图集也显式登记，且与 prefab 同包：
                    // 不登记的话 Unity 会把它作为"隐式依赖"复制进每个引用到它的包里，
                    // 多个包各存一份，包体白白变大。
                    _map["Atlas_" + MonsterCatalog.Names[i]] =
                        new ResAddress(bundle, MonsterCatalog.Names[i], atlas);
                }
            }
        }

        /// <summary>全部逻辑名（构建脚本打标与自检用）</summary>
        public static IEnumerable<string> AllKeys
        {
            get { return _map.Keys; }
        }

        public static IEnumerable<KeyValuePair<string, ResAddress>> All
        {
            get { return _map; }
        }

        public static bool TryGet(string logicalName, out ResAddress addr)
        {
            if (string.IsNullOrEmpty(logicalName))
            {
                addr = default(ResAddress);
                return false;
            }
            return _map.TryGetValue(logicalName, out addr);
        }

        /// <summary>
        /// 取地址；找不到时打印明确错误（而不是静默返回 null）。
        /// 调用方仍必须对返回值判空。
        /// </summary>
        public static ResAddress Get(string logicalName)
        {
            ResAddress addr;
            if (_map.TryGetValue(logicalName, out addr))
            {
                return addr;
            }
            UnityEngine.Debug.LogError(
                string.Format("[Res] 资源地址表中找不到逻辑名「{0}」，请在 ResTable.cs 中登记", logicalName));
            return default(ResAddress);
        }

        /// <summary>按包名收集该包下的全部逻辑名（构建打标与预加载用）</summary>
        public static List<string> GetKeysByBundle(string bundleName)
        {
            List<string> result = new List<string>();
            foreach (KeyValuePair<string, ResAddress> kv in _map)
            {
                if (kv.Value.Bundle == bundleName)
                {
                    result.Add(kv.Key);
                }
            }
            return result;
        }
    }
}
