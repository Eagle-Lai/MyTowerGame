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
            { "Tower_Normal", new ResAddress(ResBundle.TowerNormal, "Tower_Normal", "Assets/Prefabs/Tower/Tower_Normal.prefab") },
            // 塔身贴图显式登记：否则 AB 构建时它们会作为"隐式依赖"被复制进每个引用到的包
            { "Tower_Base_Sprite",   new ResAddress(ResBundle.TowerNormal, "turret_base_128",   "Assets/_UIAssets/Tower/Normal/turret_base_128.png") },
            { "Tower_Barrel_Sprite", new ResAddress(ResBundle.TowerNormal, "turret_barrel_128", "Assets/_UIAssets/Tower/Normal/turret_barrel_128.png") },

            { "Tower_Power", new ResAddress(ResBundle.TowerPower, "Tower_Power", "Assets/Prefabs/Tower/Tower_Power.prefab") },
            { "Tower_Power_Base_Sprite",   new ResAddress(ResBundle.TowerPower, "tower_base",   "Assets/_UIAssets/Tower/Power/tower_base.png") },
            { "Tower_Power_Barrel_Sprite", new ResAddress(ResBundle.TowerPower, "tower_barrel", "Assets/_UIAssets/Tower/Power/tower_barrel.png") },

            { "Tower_Retard", new ResAddress(ResBundle.TowerRetard, "Tower_Retard", "Assets/Prefabs/Tower/Tower_Retard.prefab") },
            { "Tower_Retard_Base_Sprite",   new ResAddress(ResBundle.TowerRetard, "slowtower_base",    "Assets/_UIAssets/Tower/retard/slowtower_base.png") },
            { "Tower_Retard_Barrel_Sprite", new ResAddress(ResBundle.TowerRetard, "slowtower_crystal", "Assets/_UIAssets/Tower/retard/slowtower_crystal.png") },

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
