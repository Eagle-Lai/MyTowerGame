using SuperScrollView;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 生成 HUD 与提示界面的 UGUI 预制体（P0-9）。
    ///
    /// 【节点名必须与代码严格一致】HudView / TipsView 用 `transform.Find("...")` 取节点，
    /// 名字对不上会在 Console 里报明确错误（查找是显式报错的，不静默失败）。
    /// 所以这个脚本和那两个 .cs 是**成对修改**的：改一边必须改另一边。
    ///
    /// HudView 节点：
    ///   HudView
    ///   ├── GoldText        金币
    ///   ├── HpText          生命
    ///   ├── RoundText       回合 / 波次
    ///   ├── Btn_Tower_Normal 建塔·单体（type=1）→ PriceText
    ///   ├── Btn_Tower_Power  建塔·范围（type=2）→ PriceText
    ///   ├── Btn_Tower_Retard 建塔·减速（type=3）→ PriceText ★ 名字 Retard ↔ 枚举 Slow，映射见 HudView
    ///   ├── Btn_Tower_Pierce 建塔·穿透（type=4）→ PriceText
    ///   ├── Btn_Tower_Laser  建塔·激光（type=5）→ PriceText
    ///   └── StartButton     开始 / 下一回合（→ StartButton/Label）
    ///
    ///   ★ 塔按钮**不带 Label**，价格走 PriceText 子节点（契约见 Docs/HudView_Sync_and_TowerUI_Plan.md §2）
    ///
    /// TipsView 节点：
    ///   TipsView（CanvasGroup）
    ///   └── TipText
    ///
    /// LevelClearView 节点（通关 / 失败结算弹窗）：
    ///   LevelClearView
    ///   ├── Bg（全屏遮罩；刻意**不接**"点击关闭"，见 LevelClearView.cs 的说明）
    ///   └── Panel（640×680）
    ///       ├── Title         通关完成！ / 防御失败
    ///       ├── LevelName     关卡名
    ///       ├── Stars         本次星级（大号，★☆ 字形）
    ///       ├── StarDetail    本次 vs 历史最高
    ///       ├── RecordTip     新纪录提示（默认隐藏）
    ///       ├── Stats         剩余生命 / 击杀 / 漏怪
    ///       ├── NextBtn       → SelectLevelRequestEvent(nextLevelId)
    ///       ├── RetryBtn      → RestartLevelRequestEvent
    ///       └── SelectBtn     → QuitToSelectRequestEvent
    ///
    /// SelectView 节点（关卡选择；**整页全屏** + 横向画廊）：
    ///   SelectView
    ///   ├── Bg（全屏底色；被 Panel 盖住，点不到）
    ///   └── Panel（铺满屏幕，四边内缩 0）
    ///       ├── Title / Summary
    ///       ├── List            ScrollRect + LoopListView2（横向、条目吸附居中）
    ///       │                  Image(轨道/拖动接收) + RectMask2D(**裁切在这一层**)
    ///       │   └── Viewport    900 宽（比 List 的 1300 窄），只当"居中/吸附参照"，无 Graphic
    ///       │       └── Content 运行时由 LoopListView2 往里放关卡卡片
    ///       ├── LeftBtn " < "   居中的关卡往前挪一格
    ///       ├── RightBtn " > "  往后挪一格
    ///       └── CloseBtn
    ///   ★ Viewport 刻意比 List 窄 —— 这是"首末条也能精确居中"与"看得见邻卡"能同时成立的
    ///     关键，理由见 SelectItemW 的注释。
    ///   ★ 箭头用 ASCII 的 < / > ：中文 SDF 字体不保证有 ◀▶ 的码位，缺字形只会渲染成空白且不报错。
    ///   ★ 关卡卡片本身是**独立资产** SelectLevelItem.prefab（LoopListView2 按预制体引用池化克隆），
    ///     它不在本文件的节点契约里，见 BuildSelectItemPrefab。
    ///
    /// 【关于中文字体】全工程统一使用 **TextMeshPro（TMP）**，不再使用 UGUI Text。
    /// 字体取 TMP 默认字体资产（`Assets/Font/SiYuanSongTi SDF.asset`，源思源宋体，
    /// 已配置在 TMP Settings 的 m_defaultFontAsset）。TMP 的 SDF 字体资产包含中文字形，
    /// 编辑器 / PC 包 / 移动包都能正常显示中文，不需要再回退系统字体。
    /// 描边不再用 UGUI 的 Outline 组件（TMP 不支持），改用 TMP 的 faceted/outline 材质属性。
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 补缺 UI 预制体（安全：只补缺失）
    ///   Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 生成 UI 预制体（全量重建，危险）
    /// 【破坏性】全量重建会 DeleteAsset 后重写 prefab；
    ///   若 prefab 内存在生成器不认识的节点会中止（见 EditorUtil.IsSafeToRebuild）。
    ///   日常补缺请走 EnsureMissing /「补缺 UI 预制体（安全）」。
    /// </summary>
    public static class UIPrefabBuilder
    {
        public const string HudPath = "Assets/Prefabs/UI/HudView.prefab";
        public const string TipsPath = "Assets/Prefabs/UI/TipsView.prefab";
        public const string TowerInfoPath = "Assets/Prefabs/UI/TowerInfoView.prefab";

        // ---- M3 新增的三个界面 ----
        public const string SelectPath = "Assets/Prefabs/UI/SelectView.prefab";
        public const string PausePath = "Assets/Prefabs/UI/PauseView.prefab";
        public const string SettingPath = "Assets/Prefabs/UI/SettingView.prefab";
        public const string LevelClearPath = "Assets/Prefabs/UI/LevelClearView.prefab";

        // ---- UI 补全 P1：启动链三界面 ----
        // ⚠️ **刻意放在 Resources/BootUI 而不是 Assets/Prefabs/UI**（别顺手挪回去）：
        //   开屏页与加载页必须在 `ResLoader.Init` **之前**就能显示，而 YooAsset 在 Init 完成前
        //   拒绝加载任何资源 → 走 ResTable/YooAsset 是"先有鸡还是先有蛋"，必然失败（已实测）。
        //   Resources 不依赖资源系统初始化；且 `Assets/Resources` **不在**
        //   BundleCollectorSetting 的收集目录里 → 不进任何 AB 包、也不参与热更
        //   （引导期界面本来就不该被热更换掉，否则可能出现"更新完打不开新的引导界面"）。
        public const string SplashPath = "Assets/Resources/BootUI/SplashView.prefab";
        public const string LoadingPath = "Assets/Resources/BootUI/LoadingView.prefab";
        public const string HotUpdatePath = "Assets/Resources/BootUI/HotUpdateView.prefab";

        // ---- UI 补全 P2/P3：内容界面与弹窗 ----
        public const string MainMenuPath = "Assets/Prefabs/UI/MainMenuView.prefab";
        public const string LevelDetailPath = "Assets/Prefabs/UI/LevelDetailView.prefab";
        public const string SellConfirmPath = "Assets/Prefabs/UI/SellConfirmView.prefab";
        public const string ConfirmPath = "Assets/Prefabs/UI/ConfirmView.prefab";
        public const string TowerCodexPath = "Assets/Prefabs/UI/TowerCodexView.prefab";

        /// <summary>塔图鉴的卡片（独立 prefab，被 LoopListView2 池化克隆；**不登记 ResTable**，靠引用进包）。</summary>
        public const string TowerCodexItemPath = "Assets/Prefabs/UI/TowerCodexItem.prefab";

        /// <summary>塔图鉴卡片尺寸与间距。条目宽 **必须 ≡ 视口宽**（见 SelectItemW 的硬约束说明）。</summary>
        private const float CodexListW = 1300f;
        private const float CodexListH = 640f;
        private const float CodexItemW = 460f;
        private const float CodexItemH = 640f;
        private const float CodexItemGap = 70f;
        private const int CodexArrowFontSize = 64;

        /// <summary>
        /// 关卡选择界面的**条目预制体**（一张关卡卡片）。
        ///
        /// 【为什么单独成一个 prefab】LoopListView2 是"给一个 prefab 引用，自己池化克隆"的写法
        ///   （见 LoopListView2.NewListViewItem：按 prefab 名字取池），
        ///   所以条目必须是能独立被引用的资产，而不是藏在 SelectView.prefab 里的子节点
        ///   （藏进去会让那份"模板"永远挂在 Content 下，滚起来多一个幽灵条目）。
        /// 【要不要登记 ResTable】不需要：它是被 SelectView.prefab **直接引用**的，
        ///   不是运行时按逻辑名加载的资源；YooAsset 收集整个目录树，引用依赖自然进同一个包。
        /// </summary>
        public const string SelectItemPath = "Assets/Prefabs/UI/SelectLevelItem.prefab";

        /// <summary>关卡列表的可视区域宽度（= List 节点的宽度，也是真正裁切卡片的那一层）</summary>
        private const float SelectListW = 1300f;
        private const float SelectListH = 500f;

        /// <summary>关卡列表在整页面板里的位置（页面中心为原点）</summary>
        private static readonly Vector2 SelectListPos = new Vector2(0f, 10f);

        /// <summary>
        /// 关卡卡片尺寸与横向间距。
        /// ★ 这三个数与 SelectView.cs 的对应常量必须一致 ——
        ///   那边用它们估算"尚未实例化的条目"的位置，写岔会让初始化定位被 clamp 回 0。
        ///
        /// 【为什么"视口宽度"必须等于卡片宽度，而且必须比可视区窄 —— 两个硬约束】
        ///   约束①（精确居中）：LoopListView2 的横向吸附把容器位置 clamp 在
        ///     `[视口右缘 - 内容宽, 0]`，推出来的结论是
        ///     **步长(卡片宽 + 间距) ≥ 视口宽**，否则首/末条永远到不了正中间
        ///     （偏移量正好等于 步长缺口）。所以卡片宽 ≡ 视口宽、间距取正数即可满足。
        ///   约束②（看得见邻卡）：邻卡能否露出来，取决于
        ///     `步长 < 可视区宽 - 卡片内缩`。把视口 ≡ 可视区会得到"绝对看不见邻居"，
        ///     于是这里刻意让 **视口比可视区窄**：视口只负责"居中/吸附的参照"，
        ///     可视区（List 上的 RectMask2D）才负责裁切。两者中心对齐，因此
        ///     "在视口里居中" == "在可视区里居中"。
        ///   结论：视口 900 ≡ 卡片宽 900，可视区 1300 → 左右各留 200 的空槽，
        ///         邻卡因此能露出约 144px；且首关/末关都**精确居中**。
        /// </summary>
        private const float SelectItemW = 900f;
        private const float SelectItemH = 440f;
        private const float SelectItemGap = 56f;

        /// <summary>关卡卡片上文案的基础字号（三行会用富文本逐行再给号，见 SelectView）</summary>
        private const int SelectItemFontSize = 56;

        /// <summary>整页布局的字号：大标题 / 副标题 / 左右翻页箭头</summary>
        private const int FullScreenTitleFontSize = 64;
        private const int SelectSummaryFontSize = 40;
        private const int SelectArrowFontSize = 110;

        /// <summary>
        /// 左右翻页按钮的尺寸与横向位置。
        /// 【为什么放在 x = ±834】整页 1920 宽（±960）；箭头 132 宽 + 距屏幕边 60 → 中心 ±834，
        ///   按钮占据 [768, 900]，而列表占据 [-650, 650]，中间留 118 的缝，互不遮挡。
        /// </summary>
        private const float SelectArrowW = 132f;
        private const float SelectArrowH = 160f;
        private const float SelectArrowX = 834f;


        private static readonly string[] SelectChildren = { "Bg", "Panel" };
        private static readonly string[] PauseChildren = { "Bg", "Panel" };
        private static readonly string[] SettingChildren = { "Bg", "Panel" };
        private static readonly string[] LevelClearChildren = { "Bg", "Panel" };

        // ---- UI 补全：三个启动链界面的直接子节点集合（安全护栏用）----
        private static readonly string[] SplashChildren = { "Bg", "Panel" };
        private static readonly string[] LoadingChildren = { "Bg", "Panel" };
        private static readonly string[] HotUpdateChildren = { "Bg", "Panel" };

        private static readonly string[] MainMenuChildren = { "Bg", "Panel" };
        private static readonly string[] LevelDetailChildren = { "Bg", "Panel" };
        private static readonly string[] SellConfirmChildren = { "Bg", "Panel" };
        private static readonly string[] ConfirmChildren = { "Bg", "Panel" };
        private static readonly string[] TowerCodexChildren = { "Bg", "Panel" };

        // TowerInfoView 由本生成器管理的直接子节点集合（用于重建前的安全护栏）
        private static readonly string[] TowerInfoChildren = { "Bg", "Panel" };

        // HudView 由本生成器管理的直接子节点集合（用于重建前的安全护栏）
        private static readonly string[] HudChildren =
        {
            "Bg_Gold", "Bg_Hp", "Bg_Round",
            "GoldText", "HpText", "RoundText",
            "Btn_Tower_Normal", "Btn_Tower_Power", "Btn_Tower_Retard",
            "Btn_Tower_Pierce", "Btn_Tower_Laser",
            "StartButton", "SpeedButton",
        };

        // 塔按钮：节点名 / 塔型枚举 / 参考位置（锚点左下）。
        // 【为什么没有 Label 字段】契约规定塔按钮**不配 Label**（纯图标按钮，对齐原作塔栏）。
        // 需要显示价格时用 PriceText 子节点。曾经这里有个 Label 字段，
        // 结果生成器产出的 prefab 与手工版不一致（手工版无 Label），一跑生成器就"多出文字"。
        private struct TowerButtonSpec
        {
            public string NodeName;
            public int TowerType;
            public Vector2 Pos;
        }

        // 五类塔等距铺开（间距 274），整体在 1920 参考宽度下居中。
        // 【为什么改坐标】原来是三颗、位置 -633/-359/-123（偏左）；加到五颗后必须重新居中，
        // 否则最右一颗会顶到「开始」按钮上。
        private static readonly TowerButtonSpec[] TowerButtons =
        {
            new TowerButtonSpec { NodeName = "Btn_Tower_Normal", TowerType = 1, Pos = new Vector2(-548f, -427f) },
            new TowerButtonSpec { NodeName = "Btn_Tower_Power",  TowerType = 2, Pos = new Vector2(-274f, -427f) },
            new TowerButtonSpec { NodeName = "Btn_Tower_Retard", TowerType = 3, Pos = new Vector2(0f,    -427f) },
            new TowerButtonSpec { NodeName = "Btn_Tower_Pierce", TowerType = 4, Pos = new Vector2(274f,  -427f) },
            new TowerButtonSpec { NodeName = "Btn_Tower_Laser",  TowerType = 5, Pos = new Vector2(548f,  -427f) },
        };

        // 参考分辨率下的字号
        private const int SmallFontSize = 32;
        private const int BigFontSize = 38;

        /// <summary>结算弹窗的星级字号：星星是那一屏的主角，明显大于正文</summary>
        private const int StarFontSize = 76;

        /// <summary>
        /// 倍速/开始两颗按钮（各 220×72）相对画布中心的横向偏移。
        ///
        /// 【为什么不放在"底中"】效果图 02 与策划案 §6.2.2 都把这两颗按钮放在底中 (∓140, 60)，
        ///   但那一条 y=49..177 的底带**已经被五颗 128×128 塔按钮占满**（x 348..1572）：
        ///   放在底中会盖住第 3、4 颗塔按钮，点击被 StartButton 抢走
        ///   —— 等于"减速塔/穿透塔点不了"，是实打实的功能缺陷（效果图本身的几何冲突）。
        ///   因此把两颗按钮挪到塔栏**两侧的空白区**（各留 64px 间距），
        ///   纵向与塔栏同一中心线，视觉上仍是"底部一排"，但互不遮挡。
        /// </summary>
        private const float SideBtnX = 786f;   // 中心 x = 960 ± 786，避开塔栏的 348 / 1572
        private const float SideBtnY = 77f;    // 与塔栏同中心线（距画布底边 113，按钮 72 高）

        private static readonly Color TextColor = new Color(1f, 1f, 1f, 1f);
        private static readonly Color ButtonColor = new Color(0.18f, 0.24f, 0.34f, 0.92f);
        private static readonly Color OutlineColor = new Color(0f, 0f, 0f, 0.85f);

        // ---- UI 补全 §2 视觉令牌（唯一配色源，与 UISkinArtGenerator 对齐）----
        // 【为什么在这里再写一份】生成器（Editor 程序集）不能引用运行时的 UI 常量文件，
        // 而 UI 皮肤贴图里已烘进的色值就取自这套令牌 —— 两边必须一致，改要成对改。
        private static readonly Color Cyan = new Color(0.208f, 0.878f, 1f, 1f);          // #35E0FF 主色
        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);          // #FFC94D 金币/胜利
        private static readonly Color DangerRed = new Color(1f, 0.302f, 0.369f, 1f);     // #FF4D5E 危险/失败
        private static readonly Color Fire = new Color(1f, 0.478f, 0.161f, 1f);          // #FF7A29 警示
        private static readonly Color Ice = new Color(0.490f, 0.910f, 1f, 1f);           // #7DE8FF 减速
        private static readonly Color Purple = new Color(0.486f, 0.361f, 1f, 1f);        // #7C5CFF 穿透/激光
        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);   // #E8F0FA
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f); // #9FB3C8
        private static readonly Color TextTertiary = new Color(0.369f, 0.451f, 0.588f, 1f);  // #5E7396

        // ------------------------------------------------------------------
        // 深色科幻皮肤（Assets/_UIAssets/UI/，由 UISkinArtGenerator 生成）
        //
        // 【为什么 sprite 取不到就退化成纯色】皮肤是"表现层"，缺失不应让生成器失败。
        //   取不到 → 用旧的纯色，UI 依然可用可读（与 PlaceholderArtGenerator 同一哲学）。
        // 【九宫格必须配 Image.Type.Sliced】否则 45° 切角与发光会被拉伸成斜楔。
        // ------------------------------------------------------------------

        private const string UiArtDir = "Assets/_UIAssets/UI";

        private static Sprite LoadUiSprite(string name)
        {
            return AssetDatabase.LoadAssetAtPath<Sprite>(UiArtDir + "/" + name + ".png");
        }

        /// <summary>给 Image 套九宫格皮肤；皮肤缺失时退化为 fallbackColor 纯色</summary>
        private static void ApplySlicedSkin(Image img, string spriteName, Color fallbackColor)
        {
            Sprite sp = LoadUiSprite(spriteName);
            if (sp != null)
            {
                img.sprite = sp;
                img.type = Image.Type.Sliced;
                img.color = Color.white;
            }
            else
            {
                img.color = fallbackColor;
            }
        }

        /// <summary>塔型 → 建造栏图标 sprite 名（Normal/Power/Retard/Pierce/Laser）</summary>
        private static string TowerIconSpriteName(int towerType)
        {
            switch (towerType)
            {
                case 2: return "UI_TowerIcon_Power";
                case 3: return "UI_TowerIcon_Retard";
                case 4: return "UI_TowerIcon_Pierce";
                case 5: return "UI_TowerIcon_Laser";
                default: return "UI_TowerIcon_Normal";
            }
        }
        [MenuItem("Tools/塔防/高级（单步重建）/补缺 UI 预制体（安全：只补缺失）", false, 304)]
        public static void EnsureMissingFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            EnsureMissing(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[M0] UI 预制体补缺结果：\n" + report.Text);
            EditorUtility.DisplayDialog("补缺 UI 预制体",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        [MenuItem("Tools/塔防/高级（单步重建）/生成 UI 预制体（全量重建）", false, 305)]
        public static void Build()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            BuildInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[M0] UI 预制体生成结果：\n" + report.Text);
            EditorUtility.DisplayDialog("生成 UI 预制体",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        /// <summary>
        /// 无弹窗全量重建（供 Unity MCP / 批处理调用）。
        /// 【为什么单开一个】带 EditorUtility.DisplayDialog 的菜单会**阻塞编辑器**，自动化会卡死。
        /// </summary>
        [MenuItem("Tools/塔防/自动化（无弹窗）/生成 UI 预制体（全量重建）", false, 902)]
        public static void BuildNoDialog()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            BuildInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[M0] UI 预制体生成结果：\n" + report.Text);
        }

        /// <summary>供一键向导调用（不弹窗）。**全量重建**，会覆盖手工改过的 prefab。</summary>
        public static void BuildInternal(EditorUtil.Report report)
        {
            BuildHud(report);
            BuildTips(report);
            BuildTowerInfo(report);
            BuildSelect(report);
            BuildPause(report);
            BuildSetting(report);
            BuildLevelClear(report);

            // ---- UI 补全 P1：启动链三界面 ----
            BuildSplash(report);
            BuildLoading(report);
            BuildHotUpdate(report);

            // ---- UI 补全 P2/P3：内容界面与弹窗 ----
            BuildMainMenu(report);
            BuildLevelDetail(report);
            BuildSellConfirm(report);
            BuildConfirm(report);
            BuildTowerCodex(report);
        }

        /// <summary>
        /// **安全**入口：只为"尚不存在"的 prefab 调生成器，已存在的一律跳过、一个字节都不动。
        ///
        /// 【为什么必须有这个入口】本类的三个 Build* 都是"DeleteAsset + 重建"。
        /// HudView.prefab 已被手工改造过（三颗塔按钮、手工摆位），
        /// 只要有人跑一次全量生成，手工成果就被整份覆盖。
        /// 一键向导与日常补缺走本方法；确要全量重建时走「高级（单步重建）」菜单。
        ///
        /// 【与 IsSafeToRebuild 的分工（两者叠加，不是二选一）】
        ///   IsSafeToRebuild 防的是"prefab 里有生成器不认识的节点"（防误删未知内容）；
        ///   本方法防的是"prefab 本来就好好存在"（防无谓重建）。
        ///   于是：不存在 → 生成；存在且合规 → 全量入口才会重建；存在但含未知节点 → 中止。
        /// </summary>
        public static void EnsureMissing(EditorUtil.Report report)
        {
            report.Head("补缺 UI 预制体（只生成缺失的，已存在的不动）");
            EnsureOne(HudPath, "HudView", report);
            EnsureOne(TipsPath, "TipsView", report);
            EnsureOne(TowerInfoPath, "TowerInfoView", report);
            EnsureOne(SelectPath, "SelectView", report);
            EnsureOne(PausePath, "PauseView", report);
            EnsureOne(SettingPath, "SettingView", report);
            EnsureOne(LevelClearPath, "LevelClearView", report);

            // ---- UI 补全 P1：启动链三界面 ----
            EnsureOne(SplashPath, "SplashView", report);
            EnsureOne(LoadingPath, "LoadingView", report);
            EnsureOne(HotUpdatePath, "HotUpdateView", report);

            // ---- UI 补全 P2/P3：内容界面与弹窗 ----
            EnsureOne(MainMenuPath, "MainMenuView", report);
            EnsureOne(LevelDetailPath, "LevelDetailView", report);
            EnsureOne(SellConfirmPath, "SellConfirmView", report);
            EnsureOne(ConfirmPath, "ConfirmView", report);
            EnsureOne(TowerCodexPath, "TowerCodexView", report);
        }

        /// <summary>
        /// 按路径派发到对应的 Build*。
        ///
        /// 【为什么改成链式 if/else if 全枚举】原实现把 `SelectPath` 判断了两次、
        /// `SettingPath` 没有任何分支（靠末尾 `else BuildSetting` 兜底）——
        /// 于是给"新增界面"再挂一个 `else` 就会**静默生成 SettingView**（而不是报错）。
        /// 现在最后一个是显式 `else` 兜底 + 报错，漏登记一定看得见。
        /// </summary>
        private static void EnsureOne(string path, string name, EditorUtil.Report report)
        {
            if (AssetDatabase.LoadAssetAtPath<GameObject>(path) != null)
            {
                report.Skip(string.Format("{0}.prefab 已存在，跳过（要重建请用「高级（单步重建）▸ 生成 UI 预制体」）", name));
                return;
            }
            report.Ok(string.Format("{0}.prefab 缺失 → 补齐", name));

            if (path == HudPath) BuildHud(report);
            else if (path == TipsPath) BuildTips(report);
            else if (path == TowerInfoPath) BuildTowerInfo(report);
            else if (path == SelectPath) BuildSelect(report);
            else if (path == PausePath) BuildPause(report);
            else if (path == SettingPath) BuildSetting(report);
            else if (path == LevelClearPath) BuildLevelClear(report);
            else if (path == SplashPath) BuildSplash(report);
            else if (path == LoadingPath) BuildLoading(report);
            else if (path == HotUpdatePath) BuildHotUpdate(report);
            else if (path == MainMenuPath) BuildMainMenu(report);
            else if (path == LevelDetailPath) BuildLevelDetail(report);
            else if (path == SellConfirmPath) BuildSellConfirm(report);
            else if (path == ConfirmPath) BuildConfirm(report);
            else if (path == TowerCodexPath) BuildTowerCodex(report);
            else report.Error("EnsureOne 没有为 " + path + " 登记生成方法（新增界面时忘了在 EnsureOne 里加分支）");
        }

        // ------------------------------------------------------------------
        // HUD
        // ------------------------------------------------------------------

        private static void BuildHud(EditorUtil.Report report)
        {
            report.Head("生成 HUD → " + HudPath);

            // ★ 安全护栏：prefab 里若有生成器不认识的节点，说明有人手工改过，中止而不是抹掉
            string extra;
            if (!EditorUtil.IsSafeToRebuild(HudPath, HudChildren, out extra))
            {
                report.Error("HudView.prefab 检测到生成器不识别的节点：" + extra +
                             "　→ 已中止，未做任何修改。请把手工节点纳入 HudChildren 或手工维护该 prefab。");
                return;
            }

            AssetDatabase.DeleteAsset(HudPath);
            EditorUtil.EnsureFolderOfFile(HudPath);

            GameObject root = new GameObject("HudView", typeof(RectTransform));
            Stretch((RectTransform)root.transform);
            root.AddComponent<HudView>();

            // 芯片底（先建，保证在文本之下）：金币 / 生命 / 回合
            CreateChip(root.transform, "Bg_Gold", new Vector2(0f, 1f), new Vector2(40f, -30f),
                new Vector2(268f, 52f), "UI_Chip_Gold");
            CreateChip(root.transform, "Bg_Hp", new Vector2(0f, 1f), new Vector2(40f, -84f),
                new Vector2(268f, 52f), "UI_Chip_HP");
            CreateChip(root.transform, "Bg_Round", new Vector2(0.5f, 1f), new Vector2(0f, -30f),
                new Vector2(320f, 56f), "UI_Chip_Neutral");

            // 左上：金币 / 生命
            CreateText(root.transform, "GoldText", "金币 0",
                new Vector2(0f, 1f), new Vector2(40f, -30f), new Vector2(520f, 52f),
                TextAnchor.MiddleLeft, SmallFontSize);

            CreateText(root.transform, "HpText", "生命 0/0",
                new Vector2(0f, 1f), new Vector2(40f, -84f), new Vector2(520f, 52f),
                TextAnchor.MiddleLeft, SmallFontSize);

            // 顶部中央：回合 / 波次
            CreateText(root.transform, "RoundText", "准备中",
                new Vector2(0.5f, 1f), new Vector2(0f, -30f), new Vector2(700f, 56f),
                TextAnchor.MiddleCenter, BigFontSize);

            // 底部：五颗塔按钮 + 倍速 + 开始
            for (int i = 0; i < TowerButtons.Length; i++)
            {
                CreateTowerButton(root.transform, TowerButtons[i]);
            }
            // 左=倍速（工具类，次要）、右=开始（主 CTA）—— 与"原设计里 倍速在左、开始在右"一致
            CreateButton(root.transform, "SpeedButton", "×1", new Vector2(-SideBtnX, SideBtnY));
            CreateButton(root.transform, "StartButton", "开始", new Vector2(SideBtnX, SideBtnY), true);

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, HudPath);
            Object.DestroyImmediate(root);

            if (saved == null)
            {
                report.Error("保存失败：" + HudPath);
                return;
            }
            report.Ok("HudView.prefab（Bg_Gold/Bg_Hp/Bg_Round / GoldText / HpText / RoundText / " +
                      "Btn_Tower_Normal·Power·Retard·Pierce·Laser / StartButton / SpeedButton）");
        }

        /// <summary>HUD 上的"芯片底"（金币/生命/回合），不吃点击</summary>
        private static void CreateChip(Transform parent, string name, Vector2 anchor, Vector2 anchoredPos,
            Vector2 size, string spriteName)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.pivot = new Vector2(anchor.x, anchor.y);
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = size;
            Image img = go.AddComponent<Image>();
            img.raycastTarget = false;
            ApplySlicedSkin(img, spriteName, new Color(0.12f, 0.16f, 0.24f, 0.85f));
        }

        // ------------------------------------------------------------------
        // Tips
        // ------------------------------------------------------------------

        private static void BuildTips(EditorUtil.Report report)
        {
            report.Head("生成提示层 → " + TipsPath);

            AssetDatabase.DeleteAsset(TipsPath);
            EditorUtil.EnsureFolderOfFile(TipsPath);

            GameObject root = new GameObject("TipsView", typeof(RectTransform));
            Stretch((RectTransform)root.transform);
            CanvasGroup cg = root.AddComponent<CanvasGroup>();
            cg.alpha = 0f;              // 初始透明，由 TipsView 控制淡入淡出
            cg.blocksRaycasts = false;
            cg.interactable = false;
            root.AddComponent<TipsView>();

            // 提示条底（在文字之下；与 TipText 的 pivot(0.5,0.3) 对齐到同一中心）
            GameObject bar = new GameObject("TipBar", typeof(RectTransform));
            bar.transform.SetParent(root.transform, false);
            RectTransform brt = (RectTransform)bar.transform;
            brt.anchorMin = new Vector2(0.5f, 0.30f);
            brt.anchorMax = new Vector2(0.5f, 0.30f);
            brt.pivot = new Vector2(0.5f, 0.5f);
            brt.anchoredPosition = new Vector2(0f, 18f);
            brt.sizeDelta = new Vector2(1160f, 84f);
            Image barImg = bar.AddComponent<Image>();
            barImg.raycastTarget = false;
            ApplySlicedSkin(barImg, "UI_Tip_Bar", new Color(0.06f, 0.09f, 0.13f, 0.72f));

            TextMeshProUGUI tip = CreateText(root.transform, "TipText", string.Empty,
                new Vector2(0.5f, 0.30f), Vector2.zero, new Vector2(1100f, 60f),
                TextAnchor.MiddleCenter, BigFontSize);
            tip.enableWordWrapping = true;
            tip.overflowMode = TextOverflowModes.Overflow;

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, TipsPath);
            Object.DestroyImmediate(root);

            if (saved == null)
            {
                report.Error("保存失败：" + TipsPath);
                return;
            }
            report.Ok("TipsView.prefab（CanvasGroup + TipText，初始 alpha=0）");
        }

        // ------------------------------------------------------------------
        // TowerInfoView（升级 / 出售面板，M2-B3）
        // ------------------------------------------------------------------

        private static void BuildTowerInfo(EditorUtil.Report report)
        {
            report.Head("生成塔信息面板 → " + TowerInfoPath);

            // 安全护栏：有生成器不认识的一级子节点 → 中止
            string extra;
            if (!EditorUtil.IsSafeToRebuild(TowerInfoPath, TowerInfoChildren, out extra))
            {
                report.Error("TowerInfoView.prefab 检测到生成器不识别的节点：" + extra +
                             "　→ 已中止，未做任何修改。");
                return;
            }

            AssetDatabase.DeleteAsset(TowerInfoPath);
            EditorUtil.EnsureFolderOfFile(TowerInfoPath);

            GameObject root = new GameObject("TowerInfoView", typeof(RectTransform));
            Stretch((RectTransform)root.transform);
            root.AddComponent<TowerInfoView>();

            // 半透明底：点它关闭面板
            GameObject bg = new GameObject("Bg", typeof(RectTransform));
            bg.transform.SetParent(root.transform, false);
            Stretch((RectTransform)bg.transform);
            Image bgImg = bg.AddComponent<Image>();
            bgImg.color = new Color(0f, 0f, 0f, 0.35f);
            Button bgBtn = bg.AddComponent<Button>();
            bgBtn.targetGraphic = bgImg;

            // 中央面板
            GameObject panel = new GameObject("Panel", typeof(RectTransform));
            panel.transform.SetParent(root.transform, false);
            RectTransform prt = (RectTransform)panel.transform;
            prt.anchorMin = new Vector2(0.5f, 0.5f);
            prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.pivot = new Vector2(0.5f, 0.5f);
            prt.anchoredPosition = Vector2.zero;
            prt.sizeDelta = new Vector2(560f, 460f);
            Image panelImg = panel.AddComponent<Image>();
            ApplySlicedSkin(panelImg, "UI_Panel_Cyan", new Color(0.12f, 0.16f, 0.24f, 0.96f));

            // 标题 / 属性
            CreateText(panel.transform, "Title", "防御塔  Lv.1",
                new Vector2(0.5f, 1f), new Vector2(0f, -34f), new Vector2(500f, 52f),
                TextAnchor.MiddleCenter, BigFontSize);

            TextMeshProUGUI stats = CreateText(panel.transform, "Stats", "攻击 -   射程 -   攻速 -",
                new Vector2(0.5f, 1f), new Vector2(0f, -100f), new Vector2(500f, 44f),
                TextAnchor.MiddleCenter, SmallFontSize);
            stats.enableWordWrapping = true;

            // 三个按钮（竖排）
            CreatePanelButton(panel.transform, "UpgradeBtn", "升级", new Vector2(0f, -20f), 320f, true);
            CreatePanelButton(panel.transform, "SellBtn", "出售", new Vector2(0f, -110f));
            CreatePanelButton(panel.transform, "CloseBtn", "关闭", new Vector2(0f, -200f));

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, TowerInfoPath);
            Object.DestroyImmediate(root);

            if (saved == null)
            {
                report.Error("保存失败：" + TowerInfoPath);
                return;
            }
            report.Ok("TowerInfoView.prefab（Bg / Panel( Title / Stats / UpgradeBtn / SellBtn / CloseBtn )）");
        }

        // ------------------------------------------------------------------
        // M3 新增：关卡选择 / 暂停 / 设置
        //
        // 【为什么三者共用 CreateDialogShell】骨架完全一样（全屏 Bg + 居中 Panel + 标题），
        // 各抄一遍迟早分叉 —— 而分叉之后"改一处忘一处"正是本项目反复踩的坑。
        // ------------------------------------------------------------------

        private static GameObject CreateDialogShell(string rootName, string title,
            Vector2 panelSize, EditorUtil.Report report, out GameObject panel,
            float stretchInset = -1f)
        {
            GameObject root = new GameObject(rootName, typeof(RectTransform));
            Stretch((RectTransform)root.transform);

            // 【stretchInset ≥ 0 → 整页外壳】关卡选择是"整页 UI"而不是浮在战斗上的小弹窗：
            //   Panel 四边各内缩 stretchInset 铺满屏幕（此时 panelSize 忽略），
            //   Bg 只是一层兜底底色（会被 Panel 盖住，点了也点不到）。
            bool fullScreen = stretchInset >= 0f;

            GameObject bg = new GameObject("Bg", typeof(RectTransform));
            bg.transform.SetParent(root.transform, false);
            Stretch((RectTransform)bg.transform);
            Image bgImg = bg.AddComponent<Image>();
            // 整页时底色更实：它不再只是"弹窗后面的压暗层"，而是整屏的底
            bgImg.color = fullScreen
                ? new Color(0.02f, 0.03f, 0.05f, 0.98f)
                : new Color(0f, 0f, 0f, 0.55f);
            Button bgBtn = bg.AddComponent<Button>();
            bgBtn.targetGraphic = bgImg;

            panel = new GameObject("Panel", typeof(RectTransform));
            panel.transform.SetParent(root.transform, false);
            RectTransform prt = (RectTransform)panel.transform;
            Image panelImg = panel.AddComponent<Image>();
            ApplySlicedSkin(panelImg, "UI_Panel_Cyan", new Color(0.12f, 0.16f, 0.24f, 0.96f));

            Vector2 titlePos;
            Vector2 titleSize;
            int titleFont;
            if (fullScreen)
            {
                prt.anchorMin = Vector2.zero;
                prt.anchorMax = Vector2.one;
                prt.pivot = new Vector2(0.5f, 0.5f);
                prt.offsetMin = new Vector2(stretchInset, stretchInset);
                prt.offsetMax = new Vector2(-stretchInset, -stretchInset);
                // 整页的标题比弹窗大一号，也更靠上（1920×1080 下距顶 64，高 92）
                titlePos = new Vector2(0f, -64f);
                titleSize = new Vector2(1400f, 92f);
                titleFont = FullScreenTitleFontSize;
            }
            else
            {
                prt.anchorMin = new Vector2(0.5f, 0.5f);
                prt.anchorMax = new Vector2(0.5f, 0.5f);
                prt.pivot = new Vector2(0.5f, 0.5f);
                prt.anchoredPosition = Vector2.zero;
                prt.sizeDelta = panelSize;
                titlePos = new Vector2(0f, -36f);
                titleSize = new Vector2(panelSize.x - 60f, 56f);
                titleFont = BigFontSize;
            }

            CreateText(panel.transform, "Title", title,
                new Vector2(0.5f, 1f), titlePos, titleSize,
                TextAnchor.MiddleCenter, titleFont);

            return root;
        }

        private static void BuildSelect(EditorUtil.Report report)
        {
            report.Head("生成关卡选择 → " + SelectPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(SelectPath, SelectChildren, out extra))
            {
                report.Error("SelectView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            // 关卡卡片先建：下面的 LoopListView2 要引用这份 prefab 资产
            GameObject itemPrefab = BuildSelectItemPrefab(report);
            if (itemPrefab == null)
            {
                report.Error("关卡卡片生成失败，SelectView 未重建（避免产出「列表里没有条目」的空壳）");
                return;
            }

            AssetDatabase.DeleteAsset(SelectPath);
            EditorUtil.EnsureFolderOfFile(SelectPath);

            GameObject panel;
            // 最后一个参数 0 = 整页外壳：Panel 铺满屏幕（关卡选择是全屏页，不是小弹窗）
            GameObject root = CreateDialogShell("SelectView", "选择关卡",
                Vector2.zero, report, out panel, 0f);
            root.AddComponent<SelectView>();

            CreateText(panel.transform, "Summary", "已通关 0/8　★ 0/24",
                new Vector2(0.5f, 1f), new Vector2(0f, -182f), new Vector2(1400f, 60f),
                TextAnchor.MiddleCenter, SelectSummaryFontSize);

            GameObject list = new GameObject("List", typeof(RectTransform));
            list.transform.SetParent(panel.transform, false);
            RectTransform lrt = (RectTransform)list.transform;
            lrt.anchorMin = new Vector2(0.5f, 0.5f);
            lrt.anchorMax = new Vector2(0.5f, 0.5f);
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = SelectListPos;
            lrt.sizeDelta = new Vector2(SelectListW, SelectListH);

            // ★★ 裁切放在 List（可视区）而不是 Viewport —— 这是"精确居中 + 邻卡可见"能同时成立的关键。
            //   见 SelectItemW 的注释：Viewport 只当"居中/吸附的参照"，可以比可视区窄。
            //   List 自己那张 Image 同时充当滚动轨道，并给拖动提供射线目标。
            Image trackImg = list.AddComponent<Image>();
            trackImg.color = new Color(0.04f, 0.06f, 0.10f, 0.6f);
            trackImg.raycastTarget = true;
            list.AddComponent<RectMask2D>();

            // LoopListView2 的硬性结构要求：ScrollRect 的 content / viewport 必须是它的子节点，
            // 且 Content 下**不能挂 LayoutGroup**（节点名自由，下面两句赋值是强制的）。
            //
            // 【Viewport 比 List 窄、且不铺满】它就是"吸附参照系"：
            //   它的中心与 List 中心重合 → 在它里面居中 == 在可视区里居中；
            //   而它更窄，才让"步长 ≥ 视口宽"这条约束在不牺牲邻卡可见性的前提下成立。
            GameObject viewport = new GameObject("Viewport", typeof(RectTransform));
            viewport.transform.SetParent(list.transform, false);
            RectTransform vrt = (RectTransform)viewport.transform;
            // 【pivot 必须预置成"插件待会儿要强改成的那个值"：x = 0】
            //   LoopListView2 在 InitListView 里会执行 AdjustPivot → 把 viewport 的 pivot.x 改 0。
            //   RectTransform 的 offsetMin/offsetMax 是由 anchoredPosition + sizeDelta + pivot
            //   反推出来的（offsetMin = anchoredPosition - sizeDelta*pivot），**pivot 一变矩形就平移**
            //   （实测点了居中锚点时会整块左移 180，所有卡片跟着跑偏）。
            //   所以这里先把 pivot.x 设成 0，再用 offsetMin/offsetMax 直接描述矩形：
            //   这两个值本身就是"相对父矩形四边"的绝对量，与 pivot 无关，之后怎么改都不动。
            vrt.pivot = new Vector2(0f, 0.5f);
            vrt.anchorMin = new Vector2(0f, 0.5f);
            vrt.anchorMax = new Vector2(1f, 0.5f);
            vrt.offsetMin = new Vector2((SelectListW - SelectItemW) * 0.5f, -SelectListH * 0.5f);
            vrt.offsetMax = new Vector2(-(SelectListW - SelectItemW) * 0.5f, SelectListH * 0.5f);
            // 不挂 Graphic：看不见也点不到，纯粹是给 LoopListView2 用的参照矩形

            GameObject content = new GameObject("Content", typeof(RectTransform));
            content.transform.SetParent(viewport.transform, false);
            RectTransform crt = (RectTransform)content.transform;
            // 锚点/轴心取"左侧中点"：LoopListView2 只会改写 pivot.x / anchorMin.x(=0)，
            //   y 保持 0.5 才能让条目纵向与视口中心对齐（吸附居中的前提）。
            crt.anchorMin = new Vector2(0f, 0.5f);
            crt.anchorMax = new Vector2(0f, 0.5f);
            crt.pivot = new Vector2(0f, 0.5f);
            crt.anchoredPosition = Vector2.zero;
            crt.sizeDelta = Vector2.zero;

            ScrollRect sr = list.AddComponent<ScrollRect>();
            sr.viewport = vrt;
            sr.content = crt;
            sr.horizontal = true;
            sr.vertical = false;
            sr.movementType = ScrollRect.MovementType.Elastic;
            sr.elasticity = 0.1f;
            sr.inertia = true;
            sr.decelerationRate = 0.135f;
            sr.scrollSensitivity = 40f;
            // 滚动条留空：若挂了滚动条且 horizontalScrollbarVisibility 是
            //   AutoHideAndExpandViewport，LoopListView2 在 InitListView 里会**直接报错**。

            LoopListView2 lv = list.AddComponent<LoopListView2>();
            ConfigureLoopListView(lv, itemPrefab);

            // 左右翻页箭头：各自把"居中的那一关"前后挪一格（不直接进关，见 SelectView）
            // 【为什么用 ASCII 的 < >】中文 SDF 字体不保证有 ◀▶/‹› 这些码位，
            //   缺字形时 TMP 只会渲染成空白且**不报错**（本工程踩过这个坑）。
            //   "<" / ">" 是 ASCII 必含字形，放大到 72 号就是一副箭头。
            CreatePanelButton(panel.transform, "LeftBtn", "<",
                new Vector2(-SelectArrowX, SelectListPos.y), SelectArrowW, false, SelectArrowH, SelectArrowFontSize);
            CreatePanelButton(panel.transform, "RightBtn", ">",
                new Vector2(SelectArrowX, SelectListPos.y), SelectArrowW, false, SelectArrowH, SelectArrowFontSize);

            CreatePanelButton(panel.transform, "CloseBtn", "返回", new Vector2(0f, -430f), 340f, true, 84f);

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, SelectPath);
            Object.DestroyImmediate(root);
            if (saved == null)
            {
                report.Error("保存失败：" + SelectPath);
                return;
            }
            report.Ok("SelectView.prefab（整页：Bg / Panel( Title / Summary / List(Viewport/Content) / LeftBtn / RightBtn / CloseBtn )）");
        }

        /// <summary>
        /// 关卡卡片（SelectLevelItem.prefab）：一张可点击的关卡按钮。
        /// 生成器**完全拥有**这份资产，每次全量重建都覆盖。
        ///
        /// 结构：
        ///   SelectLevelItem   RT 880×300（锚点/轴心 = 左侧中点）+ LoopListViewItem2
        ///   └── Body          拉伸铺满；Image + Button + CanvasGroup
        ///       └── Label     三行文案
        /// </summary>
        private static GameObject BuildSelectItemPrefab(EditorUtil.Report report)
        {
            AssetDatabase.DeleteAsset(SelectItemPath);   // 幂等：先删后建
            EditorUtil.EnsureFolderOfFile(SelectItemPath);

            GameObject go = new GameObject("SelectLevelItem", typeof(RectTransform));
            RectTransform rt = (RectTransform)go.transform;
            // 【横向列表的统一口径】锚点/轴心都取"左侧中点"：
            //   LoopListView2 排布时只写 localPosition.x（宽度方向），
            //   y 交给 StartPosOffset；轴心取 0.5 才能让卡片纵向与视口中心对齐。
            //   （与官方 HorizontalGalleryDemo 的 ItemPrefab1 同一套锚点约定。）
            rt.anchorMin = new Vector2(0f, 0.5f);
            rt.anchorMax = new Vector2(0f, 0.5f);
            rt.pivot = new Vector2(0f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(SelectItemW, SelectItemH);

            // ★ LoopListView2 认条目靠这个组件（取 RectTransform / 记 padding / 缓存索引）
            go.AddComponent<LoopListViewItem2>();

            // 【为什么视觉全挂在 Body 子节点上】运行时要按"离视口中心多远"把非当前条目缩小 + 压暗。
            //   直接缩条目根节点会**围绕左缘**缩（根节点轴心是 (0,0.5)，不能改，LoopListView2 的排布依赖它），
            //   结果是"居中卡片左右两边的空隙一宽一窄"。放在拉伸铺满的 Body 上，
            //   就是围绕卡片自身中心缩，左右对称。
            GameObject body = new GameObject("Body", typeof(RectTransform));
            body.transform.SetParent(go.transform, false);
            RectTransform brt = (RectTransform)body.transform;
            brt.anchorMin = Vector2.zero;
            brt.anchorMax = Vector2.one;
            brt.pivot = new Vector2(0.5f, 0.5f);
            brt.anchoredPosition = Vector2.zero;
            brt.sizeDelta = Vector2.zero;

            Image img = body.AddComponent<Image>();
            ApplySlicedSkin(img, "UI_Btn_Secondary", ButtonColor);

            Button btn = body.AddComponent<Button>();
            btn.targetGraphic = img;
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            // 运行时按远近改 alpha（SelectView.LateUpdate），预制体里先挂好，避免每帧 AddComponent
            body.AddComponent<CanvasGroup>();

            TextMeshProUGUI t = CreateText(body.transform, "Label", "关卡",
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(SelectItemW, SelectItemH),
                TextAnchor.MiddleCenter, SelectItemFontSize);
            RectTransform trt = (RectTransform)t.transform;
            // 拉伸铺满卡片并留内边距，三行文案居中；卡片够宽，这里可以放心打开自动换行
            trt.anchorMin = Vector2.zero;
            trt.anchorMax = Vector2.one;
            trt.pivot = new Vector2(0.5f, 0.5f);
            trt.anchoredPosition = Vector2.zero;
            trt.sizeDelta = new Vector2(-120f, -80f);
            t.enableWordWrapping = true;
            t.overflowMode = TextOverflowModes.Overflow;

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(go, SelectItemPath);
            Object.DestroyImmediate(go);
            if (saved == null)
            {
                report.Error("保存失败：" + SelectItemPath);
                return null;
            }
            report.Ok("SelectLevelItem.prefab（关卡卡片：LoopListViewItem2 + Body(Image/Button/CanvasGroup/Label)）");
            return saved;
        }

        /// <summary>
        /// 把 LoopListView2 的关键字段写进 prefab。
        ///
        /// 【为什么用 SerializedObject 而不是公开属性】这些字段在插件里是
        ///   `[SerializeField] private`（mItemPrefabDataList / mViewPortSnapPivot / mItemSnapPivot
        ///   都没有 setter），只有在编辑器里按序列化字段写才生效 —— 这正是插件自己在
        ///   Inspector 上做的事，写进 prefab 后运行时零配置、SelectView 也不用碰这些字段。
        /// </summary>
        private static void ConfigureLoopListView(LoopListView2 lv, GameObject itemPrefab)
        {
            ConfigureLoopListView(lv, itemPrefab, SelectItemGap, 3);
        }

        /// <summary>带参版本：不同界面的条目宽度/间距/预创建数不同（关卡卡片 900+56，图鉴卡片 460+70）。</summary>
        private static void ConfigureLoopListView(LoopListView2 lv, GameObject itemPrefab, float padding, int initCreateCount)
        {
            SerializedObject so = new SerializedObject(lv);

            // 横向、从左到右
            so.FindProperty("mArrangeType").intValue = (int)ListItemArrangeType.LeftToRight;
            so.FindProperty("mSupportScrollBar").boolValue = true;

            // ★ "单个条目居中"就是这个组合：开吸附 + 视口与条目都用 0.5 轴心
            //   → 离视口中心最近的那一条会被吸到正中（官方 HorizontalGalleryDemo 同款配置）。
            so.FindProperty("mItemSnapEnable").boolValue = true;
            so.FindProperty("mViewPortSnapPivot").vector2Value = new Vector2(0.5f, 0.5f);
            so.FindProperty("mItemSnapPivot").vector2Value = new Vector2(0.5f, 0.5f);

            SerializedProperty arr = so.FindProperty("mItemPrefabDataList");
            arr.arraySize = 1;
            SerializedProperty e = arr.GetArrayElementAtIndex(0);
            e.FindPropertyRelative("mItemPrefab").objectReferenceValue = itemPrefab;
            e.FindPropertyRelative("mPadding").floatValue = padding;
            e.FindPropertyRelative("mInitCreateCount").intValue = initCreateCount;
            e.FindPropertyRelative("mStartPosOffset").floatValue = 0f;

            so.ApplyModifiedPropertiesWithoutUndo();
        }


        private static void BuildPause(EditorUtil.Report report)
        {
            report.Head("生成暂停界面 → " + PausePath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(PausePath, PauseChildren, out extra))
            {
                report.Error("PauseView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }
            AssetDatabase.DeleteAsset(PausePath);
            EditorUtil.EnsureFolderOfFile(PausePath);

            GameObject panel;
            GameObject root = CreateDialogShell("PauseView", "暂停",
                new Vector2(560f, 520f), report, out panel);
            root.AddComponent<PauseView>();

            CreatePanelButton(panel.transform, "ResumeBtn", "继续", new Vector2(0f, 60f));
            CreatePanelButton(panel.transform, "RestartBtn", "重新开始本关", new Vector2(0f, -30f));
            CreatePanelButton(panel.transform, "SettingsBtn", "设置", new Vector2(0f, -120f));
            CreatePanelButton(panel.transform, "QuitBtn", "返回关卡选择", new Vector2(0f, -210f));

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, PausePath);
            Object.DestroyImmediate(root);
            if (saved == null)
            {
                report.Error("保存失败：" + PausePath);
                return;
            }
            report.Ok("PauseView.prefab（Bg / Panel( Title / ResumeBtn / RestartBtn / SettingsBtn / QuitBtn )）");
        }

        private static void BuildSetting(EditorUtil.Report report)
        {
            report.Head("生成设置界面 → " + SettingPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(SettingPath, SettingChildren, out extra))
            {
                report.Error("SettingView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }
            AssetDatabase.DeleteAsset(SettingPath);
            EditorUtil.EnsureFolderOfFile(SettingPath);

            GameObject panel;
            GameObject root = CreateDialogShell("SettingView", "设置",
                new Vector2(620f, 600f), report, out panel);
            root.AddComponent<SettingView>();

            CreateText(panel.transform, "VolumeText", "音量 80%",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 120f), new Vector2(520f, 56f),
                TextAnchor.MiddleCenter, BigFontSize);

            // 音量用 -/+ 两个按钮而不是 Slider：Slider 需要 Fill/Handle 一整套子节点与互相引用，
            // 写在生成器里长且易错；当前只有两个设置项，按钮调档更简单也更好点。
            CreatePanelButton(panel.transform, "VolDownBtn", "音量 −", new Vector2(-170f, 40f));
            CreatePanelButton(panel.transform, "VolUpBtn", "音量 ＋", new Vector2(170f, 40f));
            CreatePanelButton(panel.transform, "MuteBtn", "静音", new Vector2(0f, -50f));
            CreatePanelButton(panel.transform, "ResetBtn", "重置存档", new Vector2(0f, -140f));
            CreatePanelButton(panel.transform, "CloseBtn", "关闭", new Vector2(0f, -230f));

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, SettingPath);
            Object.DestroyImmediate(root);
            if (saved == null)
            {
                report.Error("保存失败：" + SettingPath);
                return;
            }
            report.Ok("SettingView.prefab（Bg / Panel( Title / VolumeText / VolDownBtn / VolUpBtn / MuteBtn / ResetBtn / CloseBtn )）");
        }

        // ------------------------------------------------------------------
        // 关卡结算弹窗（通关 / 失败）
        //
        // 【节点契约】与 Assets/Scripts/UI/LevelClearView.cs 的 FindText/FindButton 一一对应，
        //   改这里必须同步改那里（两边都写死了节点名，没有中间映射层）。
        // ------------------------------------------------------------------

        private static void BuildLevelClear(EditorUtil.Report report)
        {
            report.Head("生成关卡结算界面 → " + LevelClearPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(LevelClearPath, LevelClearChildren, out extra))
            {
                report.Error("LevelClearView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }
            AssetDatabase.DeleteAsset(LevelClearPath);
            EditorUtil.EnsureFolderOfFile(LevelClearPath);

            GameObject panel;
            GameObject root = CreateDialogShell("LevelClearView", "通关完成！",
                new Vector2(640f, 680f), report, out panel);
            root.AddComponent<LevelClearView>();

            CreateText(panel.transform, "LevelName", "第 1 关",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 210f), new Vector2(560f, 48f),
                TextAnchor.MiddleCenter, SmallFontSize);

            // 本次星级是弹窗的主角，字号明显大于其它文本
            CreateText(panel.transform, "Stars", "☆☆☆",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 118f), new Vector2(560f, 96f),
                TextAnchor.MiddleCenter, StarFontSize);

            // 「本次」与「历史最高」并排 —— 存档里的星级是只升不降的合并值，
            // 不分开显示的话，二次通关打出低分反而会看到高分。
            CreateText(panel.transform, "StarDetail", "本次 ☆☆☆　　历史最高 ☆☆☆",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 42f), new Vector2(560f, 44f),
                TextAnchor.MiddleCenter, SmallFontSize);

            // 新纪录提示：默认隐藏，由 LevelClearView.Show 依据数据决定是否点亮
            TextMeshProUGUI recordTip = CreateText(panel.transform, "RecordTip",
                "★ 新纪录！刷新了本关最高星级",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -6f), new Vector2(560f, 40f),
                TextAnchor.MiddleCenter, SmallFontSize);
            recordTip.gameObject.SetActive(false);

            CreateText(panel.transform, "Stats", "剩余生命 0/0　　击杀 0　　漏怪 0",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -66f), new Vector2(560f, 46f),
                TextAnchor.MiddleCenter, SmallFontSize);

            // 按钮加宽到 420：Label 文案含关卡名（"下一关：雪原前哨"），
            // 而 CreateText 关掉了自动换行，320 宽会溢出到面板外。其余两枚回 320（规范口径）。
            CreatePanelButton(panel.transform, "NextBtn", "下一关", new Vector2(0f, -136f), 420f, true);
            CreatePanelButton(panel.transform, "RetryBtn", "重玩本关", new Vector2(0f, -216f));
            CreatePanelButton(panel.transform, "SelectBtn", "返回关卡选择", new Vector2(0f, -290f));

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, LevelClearPath);
            Object.DestroyImmediate(root);
            if (saved == null)
            {
                report.Error("保存失败：" + LevelClearPath);
                return;
            }
            report.Ok("LevelClearView.prefab（Bg / Panel( Title / LevelName / Stars / StarDetail / RecordTip / Stats / NextBtn / RetryBtn / SelectBtn )）");
        }

        /// <summary>
        /// 面板内按钮：居中锚点、固定尺寸，带 Label 子节点。
        /// <paramref name="width"/> 默认 320；结算界面要放"下一关：关卡名"这类较长文案，
        /// 会显式传更宽的值（TMP 此处关掉了自动换行，宽度不够会直接溢出到面板外）。
        /// <paramref name="height"/> / <paramref name="fontSize"/> 默认是"标准按钮"口径（72 高 / 32 号），
        /// 关卡选择的左右翻页箭头会传更高、更大的值（132×160、72 号）。
        /// </summary>
        private static void CreatePanelButton(Transform parent, string name, string label, Vector2 anchoredPos,
            float width = 320f, bool primary = false, float height = 72f, int fontSize = 0)
        {
            if (fontSize <= 0)
            {
                fontSize = SmallFontSize;
            }

            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);

            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = new Vector2(0.5f, 0.5f);
            rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = new Vector2(width, height);

            Image img = go.AddComponent<Image>();
            ApplySlicedSkin(img, primary ? "UI_Btn_Primary" : "UI_Btn_Secondary", ButtonColor);

            Button btn = go.AddComponent<Button>();
            btn.targetGraphic = img;
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            TextMeshProUGUI t = CreateText(go.transform, "Label", label,
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(width, height),
                TextAnchor.MiddleCenter, fontSize);
            RectTransform lrt = (RectTransform)t.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = Vector2.zero;
            lrt.sizeDelta = Vector2.zero;
        }

        // ==================================================================
        // UI 补全 P1：启动链三界面（Splash / Loading / HotUpdate）
        // ==================================================================
        // 【三者的共同点】都是**整页**（stretchInset = 0），都自带深色底。
        // 【为什么标题不用 CreateDialogShell 的 Title】骨架给整页标题的规格是
        //   "64 号、距顶 64"（那是给"选择关卡""防御塔图鉴"这类页面标题用的）；
        //   而这三个界面要的是自己的主视觉（开屏 96 号品牌名 / 加载与热更新是"居中构图"）。
        //   硬把标题挪过去会让骨架方法的语义变模糊，所以这里传空标题，
        //   再各自建自己的文本节点 —— 骨架的 Title 仍然存在（空串，不可见），不破坏契约。

        private static void BuildSplash(EditorUtil.Report report)
        {
            report.Head("生成开屏页 → " + SplashPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(SplashPath, SplashChildren, out extra))
            {
                report.Error("SplashView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(SplashPath);
            EditorUtil.EnsureFolderOfFile(SplashPath);

            GameObject panel;
            GameObject root = CreateDialogShell("SplashView", "", Vector2.zero, report, out panel, 0f);

            // 自带 CanvasGroup：本界面要自己控制整屏淡入（UIManager.EnsureFadeIn 会因此跳过它）
            root.AddComponent<CanvasGroup>();
            root.AddComponent<SplashView>();

            // Logo：工程里没有专门的品牌图，用已有塔图标占位（换正式 logo 时只改这一处 sprite 名）
            GameObject logo = new GameObject("Logo", typeof(RectTransform));
            logo.transform.SetParent(panel.transform, false);
            RectTransform lrt = (RectTransform)logo.transform;
            lrt.anchorMin = new Vector2(0.5f, 0.5f);
            lrt.anchorMax = new Vector2(0.5f, 0.5f);
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = new Vector2(0f, 60f);
            lrt.sizeDelta = new Vector2(480f, 480f);
            Image logoImg = logo.AddComponent<Image>();
            Sprite logoSprite = LoadUiSprite("UI_TowerIcon_Normal");
            if (logoSprite != null)
            {
                logoImg.sprite = logoSprite;
                logoImg.type = Image.Type.Simple;
                logoImg.preserveAspect = true;
                logoImg.color = new Color(1f, 1f, 1f, 0.92f);
            }
            else
            {
                logoImg.color = new Color(0.208f, 0.878f, 1f, 0.12f);
            }
            logoImg.raycastTarget = false;

            TextMeshProUGUI gameTitle = CreateText(panel.transform, "GameTitle", "自由人塔防",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -160f), new Vector2(900f, 120f),
                TextAnchor.MiddleCenter, 96);
            gameTitle.color = Cyan;

            TextMeshProUGUI sub = CreateText(panel.transform, "Subtitle", "FREEDOM TOWER",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -260f), new Vector2(900f, 48f),
                TextAnchor.MiddleCenter, 28);
            sub.color = TextSecondary;

            // 版本号右下角；anchor(1,0)+pivot(1,0) → anchoredPosition 是"距右下角"的偏移
            TextMeshProUGUI ver = CreateText(panel.transform, "Version", string.Empty,
                new Vector2(1f, 0f), new Vector2(-40f, 40f), new Vector2(320f, 36f),
                TextAnchor.MiddleRight, 22);
            ver.color = TextTertiary;

            TextMeshProUGUI dots = CreateText(panel.transform, "LoadingDots", "正在启动...",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -380f), new Vector2(400f, 40f),
                TextAnchor.MiddleCenter, 26);
            dots.color = TextSecondary;

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, SplashPath);
            Object.DestroyImmediate(root);
            report.Ok("SplashView.prefab（Logo / GameTitle / Subtitle / Version / LoadingDots）");
        }

        private static void BuildLoading(EditorUtil.Report report)
        {
            report.Head("生成加载进度界面 → " + LoadingPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(LoadingPath, LoadingChildren, out extra))
            {
                report.Error("LoadingView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(LoadingPath);
            EditorUtil.EnsureFolderOfFile(LoadingPath);

            GameObject panel;
            GameObject root = CreateDialogShell("LoadingView", "", Vector2.zero, report, out panel, 0f);
            root.AddComponent<LoadingView>();

            GameObject logo = new GameObject("Logo", typeof(RectTransform));
            logo.transform.SetParent(panel.transform, false);
            RectTransform lrt = (RectTransform)logo.transform;
            lrt.anchorMin = new Vector2(0.5f, 0.5f);
            lrt.anchorMax = new Vector2(0.5f, 0.5f);
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = new Vector2(0f, 160f);
            lrt.sizeDelta = new Vector2(240f, 240f);
            Image logoImg = logo.AddComponent<Image>();
            Sprite logoSprite = LoadUiSprite("UI_TowerIcon_Normal");
            if (logoSprite != null)
            {
                logoImg.sprite = logoSprite;
                logoImg.type = Image.Type.Simple;
                logoImg.preserveAspect = true;
                logoImg.color = new Color(1f, 1f, 1f, 0.9f);
            }
            else
            {
                logoImg.color = new Color(0.208f, 0.878f, 1f, 0.12f);
            }
            logoImg.raycastTarget = false;

            TextMeshProUGUI status = CreateText(panel.transform, "StatusText", "正在初始化资源系统...",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -40f), new Vector2(1200f, 56f),
                TextAnchor.MiddleCenter, 32);
            status.color = TextPrimary;

            // ---- 进度条（900×24，y = -140）----
            // 结构固定为 Track(铺满) / Fill(左锚点、宽度随进度) / Glow(同 Fill，半透明)
            GameObject bar = new GameObject("ProgressBar", typeof(RectTransform));
            bar.transform.SetParent(panel.transform, false);
            RectTransform brt = (RectTransform)bar.transform;
            brt.anchorMin = new Vector2(0.5f, 0.5f);
            brt.anchorMax = new Vector2(0.5f, 0.5f);
            brt.pivot = new Vector2(0.5f, 0.5f);
            brt.anchoredPosition = new Vector2(0f, -140f);
            brt.sizeDelta = new Vector2(LoadingView.FillMaxWidth, 24f);

            GameObject track = new GameObject("Track", typeof(RectTransform));
            track.transform.SetParent(bar.transform, false);
            Stretch((RectTransform)track.transform);
            Image trackImg = track.AddComponent<Image>();
            ApplySlicedSkin(trackImg, "UI_Chip_Neutral", new Color(0.075f, 0.102f, 0.149f, 1f));
            trackImg.raycastTarget = false;

            GameObject fill = new GameObject("Fill", typeof(RectTransform));
            fill.transform.SetParent(bar.transform, false);
            RectTransform frt = (RectTransform)fill.transform;
            frt.anchorMin = new Vector2(0f, 0.5f);
            frt.anchorMax = new Vector2(0f, 0.5f);
            frt.pivot = new Vector2(0f, 0.5f);
            frt.anchoredPosition = Vector2.zero;
            frt.sizeDelta = new Vector2(0f, 24f);
            Image fillImg = fill.AddComponent<Image>();
            ApplySlicedSkin(fillImg, "UI_Btn_Primary", Cyan);
            fillImg.raycastTarget = false;

            GameObject glow = new GameObject("Glow", typeof(RectTransform));
            glow.transform.SetParent(bar.transform, false);
            RectTransform grt = (RectTransform)glow.transform;
            grt.anchorMin = new Vector2(0f, 0.5f);
            grt.anchorMax = new Vector2(0f, 0.5f);
            grt.pivot = new Vector2(0f, 0.5f);
            grt.anchoredPosition = Vector2.zero;
            grt.sizeDelta = new Vector2(0f, 24f);
            Image glowImg = glow.AddComponent<Image>();
            ApplySlicedSkin(glowImg, "UI_Btn_Primary", Cyan);
            glowImg.raycastTarget = false;
            Color glowColor = glowImg.color;
            glowColor.a = 0.4f;
            glowImg.color = glowColor;

            TextMeshProUGUI percent = CreateText(panel.transform, "PercentText", "0%",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -190f), new Vector2(400f, 48f),
                TextAnchor.MiddleCenter, 34);
            percent.color = Gold;

            TextMeshProUGUI tip = CreateText(panel.transform, "TipText",
                "可以在任意空地建塔，路径会实时重算",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -300f), new Vector2(1400f, 44f),
                TextAnchor.MiddleCenter, 26);
            tip.color = TextSecondary;

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, LoadingPath);
            Object.DestroyImmediate(root);
            report.Ok("LoadingView.prefab（Logo / StatusText / ProgressBar(Track|Fill|Glow) / PercentText / TipText）");
        }

        private static void BuildHotUpdate(EditorUtil.Report report)
        {
            report.Head("生成热更新界面 → " + HotUpdatePath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(HotUpdatePath, HotUpdateChildren, out extra))
            {
                report.Error("HotUpdateView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(HotUpdatePath);
            EditorUtil.EnsureFolderOfFile(HotUpdatePath);

            GameObject panel;
            GameObject root = CreateDialogShell("HotUpdateView", "", Vector2.zero, report, out panel, 0f);
            root.AddComponent<HotUpdateView>();

            TextMeshProUGUI title = CreateText(panel.transform, "HotTitle", "资源更新",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 220f), new Vector2(900f, 80f),
                TextAnchor.MiddleCenter, 56);
            title.color = TextPrimary;

            TextMeshProUGUI phase = CreateText(panel.transform, "PhaseText", "正在检查更新...",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 100f), new Vector2(1200f, 56f),
                TextAnchor.MiddleCenter, 32);
            phase.color = TextPrimary;

            GameObject bar = new GameObject("ProgressBar", typeof(RectTransform));
            bar.transform.SetParent(panel.transform, false);
            RectTransform brt = (RectTransform)bar.transform;
            brt.anchorMin = new Vector2(0.5f, 0.5f);
            brt.anchorMax = new Vector2(0.5f, 0.5f);
            brt.pivot = new Vector2(0.5f, 0.5f);
            brt.anchoredPosition = Vector2.zero;
            brt.sizeDelta = new Vector2(HotUpdateView.FillMaxWidth, 28f);

            GameObject track = new GameObject("Track", typeof(RectTransform));
            track.transform.SetParent(bar.transform, false);
            Stretch((RectTransform)track.transform);
            Image trackImg = track.AddComponent<Image>();
            ApplySlicedSkin(trackImg, "UI_Chip_Neutral", new Color(0.075f, 0.102f, 0.149f, 1f));
            trackImg.raycastTarget = false;

            GameObject fill = new GameObject("Fill", typeof(RectTransform));
            fill.transform.SetParent(bar.transform, false);
            RectTransform frt = (RectTransform)fill.transform;
            frt.anchorMin = new Vector2(0f, 0.5f);
            frt.anchorMax = new Vector2(0f, 0.5f);
            frt.pivot = new Vector2(0f, 0.5f);
            frt.anchoredPosition = Vector2.zero;
            frt.sizeDelta = new Vector2(0f, 28f);
            Image fillImg = fill.AddComponent<Image>();
            ApplySlicedSkin(fillImg, "UI_Btn_Primary", Cyan);
            fillImg.raycastTarget = false;

            GameObject glow = new GameObject("Glow", typeof(RectTransform));
            glow.transform.SetParent(bar.transform, false);
            RectTransform grt = (RectTransform)glow.transform;
            grt.anchorMin = new Vector2(0f, 0.5f);
            grt.anchorMax = new Vector2(0f, 0.5f);
            grt.pivot = new Vector2(0f, 0.5f);
            grt.anchoredPosition = Vector2.zero;
            grt.sizeDelta = new Vector2(0f, 28f);
            Image glowImg = glow.AddComponent<Image>();
            ApplySlicedSkin(glowImg, "UI_Btn_Primary", Cyan);
            glowImg.raycastTarget = false;
            Color glowColor = glowImg.color;
            glowColor.a = 0.4f;
            glowImg.color = glowColor;

            TextMeshProUGUI percent = CreateText(panel.transform, "PercentText", "0%",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -60f), new Vector2(400f, 56f),
                TextAnchor.MiddleCenter, 40);
            percent.color = Cyan;

            TextMeshProUGUI sizeText = CreateText(panel.transform, "SizeText", "已下载 0.0 MB / 0.0 MB",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -120f), new Vector2(1200f, 40f),
                TextAnchor.MiddleCenter, 26);
            sizeText.color = TextSecondary;

            TextMeshProUGUI speedText = CreateText(panel.transform, "SpeedText", "速度 0.0 MB/s　剩余约 --:--",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -160f), new Vector2(1200f, 40f),
                TextAnchor.MiddleCenter, 24);
            speedText.color = TextSecondary;

            TextMeshProUGUI detailText = CreateText(panel.transform, "DetailText", "文件 0/0　失败 0",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -206f), new Vector2(1200f, 40f),
                TextAnchor.MiddleCenter, 22);
            detailText.color = TextTertiary;

            GameObject btnGroup = new GameObject("BtnGroup", typeof(RectTransform));
            btnGroup.transform.SetParent(panel.transform, false);
            RectTransform bgrt = (RectTransform)btnGroup.transform;
            bgrt.anchorMin = new Vector2(0.5f, 0.5f);
            bgrt.anchorMax = new Vector2(0.5f, 0.5f);
            bgrt.pivot = new Vector2(0.5f, 0.5f);
            bgrt.anchoredPosition = new Vector2(0f, -300f);
            bgrt.sizeDelta = new Vector2(900f, 88f);

            // 左槽：暂停 / 继续 互斥（同一位置，靠 SetActive 切换）
            CreatePanelButton(btnGroup.transform, "PauseBtn", "暂停", new Vector2(-160f, 0f), 240f, false, 80f, 32);
            CreatePanelButton(btnGroup.transform, "ResumeBtn", "继续", new Vector2(-160f, 0f), 240f, false, 80f, 32);
            // 右槽：重试
            CreatePanelButton(btnGroup.transform, "RetryBtn", "重试", new Vector2(160f, 0f), 240f, false, 80f, 32);

            TextMeshProUGUI failText = CreateText(panel.transform, "FailText", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(0f, -390f), new Vector2(1400f, 60f),
                TextAnchor.MiddleCenter, 26);
            failText.color = DangerRed;

            // 默认态：显示"暂停"，隐藏"继续""重试"与失败文案（与 HotUpdateView.Awake 的初值一致）
            SetNodeActive(panel.transform, "BtnGroup/ResumeBtn", false);
            SetNodeActive(panel.transform, "BtnGroup/RetryBtn", false);
            SetNodeActive(panel.transform, "FailText", false);

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, HotUpdatePath);
            Object.DestroyImmediate(root);
            report.Ok("HotUpdateView.prefab（HotTitle / PhaseText / ProgressBar(Track|Fill|Glow) / PercentText / SizeText / SpeedText / DetailText / BtnGroup(Pause|Resume|Retry) / FailText）");
        }

        /// <summary>
        /// 建一个纯 Image 节点（图标 / 色条 / 面板底衬）。
        ///
        /// 【为什么抽成 helper】顶部色条、Logo、图标、统计底衬这类节点在各界面重复出现，
        /// 每次都写 8 行 new GameObject + RectTransform + Image + ApplySlicedSkin 既啰嗦又容易写岔锚点。
        /// ⚠️ `check_ui_contract.py` **认识**这个 helper（与 CreateText/CreatePanelButton 同列）——
        ///   新增类似的"建节点 helper"时必须同步把它加进那个脚本的正则，否则
        ///   View 里引用这些节点会被误报为"生成器不产出"。
        /// </summary>
        private static Image CreateImageAt(Transform parent, string name, Vector2 anchor, Vector2 anchoredPos,
            Vector2 size, string spriteName, Color fallback, bool sliced = true)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.pivot = anchor;
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = size;

            Image img = go.AddComponent<Image>();
            if (!string.IsNullOrEmpty(spriteName))
            {
                ApplySlicedSkin(img, spriteName, fallback);
                if (!sliced)
                {
                    Sprite s = LoadUiSprite(spriteName);
                    if (s != null)
                    {
                        img.sprite = s;
                        img.type = Image.Type.Simple;
                        img.preserveAspect = true;
                        img.color = Color.white;
                    }
                }
            }
            else
            {
                img.color = fallback;
                img.raycastTarget = false;
            }
            return img;
        }

        // ==================================================================
        // UI 补全 P2/P3：主菜单 / 关卡详情 / 出售确认 / 通用确认
        // ==================================================================

        /// <summary>
        /// 坐标口径提醒：本工程 `CreateText` 的锚点即 pivot，`CreateImageAt` 同理。
        /// 传 (0.5,0.5) 时 anchoredPos 是**元素中心**相对画布中心的偏移；
        /// 传 (0,1) / (1,0) 时 anchoredPos 是**元素左上/右下角**相对该角的偏移。
        ///
        /// ★ 阅读效果图时的正确换算（踩过坑，别写反）：
        ///   1) 先 `Y_baseline = 540 − y_svg`（画布 1920×1080，y_svg 向下为正）；
        ///   2) 再 `Y_boxCenter = Y_baseline + 0.35 × fontSize`。
        ///   —— 因为 `CreateText` 是**盒子中心**定位，而 SVG 里的 y 是**文字基线**；
        ///   墨迹在基线**上方**，所以盒子中心要比基线**再高** 0.35 倍字号。
        ///   ⚠️ 写成 `− 0.35×字号` 会让整块文字下移约 0.7 倍字号 ——
        ///   实测表现为"标题和副标题叠在一起"（主菜单 88 号字下移了约 62px）。
        /// </summary>

        private static void BuildMainMenu(EditorUtil.Report report)
        {
            report.Head("生成主菜单 → " + MainMenuPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(MainMenuPath, MainMenuChildren, out extra))
            {
                report.Error("MainMenuView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(MainMenuPath);
            EditorUtil.EnsureFolderOfFile(MainMenuPath);

            GameObject panel;
            GameObject root = CreateDialogShell("MainMenuView", "", Vector2.zero, report, out panel, 0f);
            root.AddComponent<MainMenuView>();

            CreateImageAt(panel.transform, "Logo", new Vector2(0.5f, 0.5f), new Vector2(0f, 270f),
                new Vector2(380f, 380f), "UI_TowerIcon_Normal", new Color(0.208f, 0.878f, 1f, 0.12f), false);

            // 标题基线 y_svg 488 → Y=+52；88 号字的盒中心 ≈ +52−31 = +21
            TextMeshProUGUI title = CreateText(panel.transform, "GameTitle", "自由人塔防",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 83f), new Vector2(1000f, 130f),
                TextAnchor.MiddleCenter, 88);
            title.color = Cyan;

            // 副标题基线 y_svg 540 → Y=0；26 号 → 盒中心 ≈ −9
            TextMeshProUGUI sub = CreateText(panel.transform, "Subtitle", "FREEDOM TOWER · 单机塔防",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 9f), new Vector2(1000f, 44f),
                TextAnchor.MiddleCenter, 26);
            sub.color = TextSecondary;

            // 玩家总览（左上）：底衬先建，文字后建 → 文字压在底衬上
            CreateImageAt(panel.transform, "StatBg", new Vector2(0f, 1f), new Vector2(48f, -120f),
                new Vector2(416f, 112f), "UI_Panel_Cyan", new Color(0.12f, 0.16f, 0.24f, 0.85f));

            TextMeshProUGUI star = CreateText(panel.transform, "StarText", "0/0",
                new Vector2(0f, 1f), new Vector2(72f, -146f), new Vector2(368f, 40f),
                TextAnchor.MiddleLeft, 30);
            star.color = Gold;

            TextMeshProUGUI clear = CreateText(panel.transform, "ClearText", "已通关 0/0",
                new Vector2(0f, 1f), new Vector2(72f, -196f), new Vector2(368f, 40f),
                TextAnchor.MiddleLeft, 28);
            clear.color = TextSecondary;

            // 四颗入口按钮：中心 Y 依次 −66 / −184 / −302 / −420（对应 y_svg 606/724/842/960）
            CreatePanelButton(panel.transform, "StartBtn", "开始游戏", new Vector2(0f, -66f), 480f, true, 92f, 34);
            CreatePanelButton(panel.transform, "CodexBtn", "防御塔图鉴", new Vector2(0f, -184f), 480f, false, 92f, 32);
            CreatePanelButton(panel.transform, "SettingBtn", "设置", new Vector2(0f, -302f), 480f, false, 92f, 32);
            CreatePanelButton(panel.transform, "QuitBtn", "退出游戏", new Vector2(0f, -420f), 480f, false, 92f, 32);

            TextMeshProUGUI ver = CreateText(panel.transform, "Version", string.Empty,
                new Vector2(1f, 0f), new Vector2(-48f, 38f), new Vector2(240f, 32f),
                TextAnchor.MiddleRight, 22);
            ver.color = TextTertiary;

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, MainMenuPath);
            Object.DestroyImmediate(root);
            report.Ok("MainMenuView.prefab（Logo / GameTitle / Subtitle / StatBg+StarText+ClearText / Start+Codex+Setting+Quit / Version）");
        }

        private static void BuildLevelDetail(EditorUtil.Report report)
        {
            report.Head("生成本关关卡详情 → " + LevelDetailPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(LevelDetailPath, LevelDetailChildren, out extra))
            {
                report.Error("LevelDetailView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(LevelDetailPath);
            EditorUtil.EnsureFolderOfFile(LevelDetailPath);

            // 弹窗 1000×900（效果图 21：y_svg 90..990）
            GameObject panel;
            GameObject root = CreateDialogShell("LevelDetailView", "", new Vector2(1000f, 900f), report, out panel, -1f);
            root.AddComponent<LevelDetailView>();

            // 顶部色条 24px（效果图实测；§2.5 的"4px"是卡片细分隔线，两者不是一回事）
            CreateImageAt(panel.transform, "TopBar", new Vector2(0.5f, 1f), Vector2.zero,
                new Vector2(1000f, 24f), "UI_Chip_Gold", Gold);

            // 标题基线 y_svg 146 → 面板中心 y_svg 540 → Y=+394；48 号 → 盒中心 ≈ +377
            TextMeshProUGUI title = CreateText(panel.transform, "DetailTitle", "关卡",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 411f), new Vector2(940f, 64f),
                TextAnchor.MiddleCenter, 48);
            title.color = TextPrimary;

            // 关卡名基线 y_svg 196 → Y=+344；30 号 → 盒中心 ≈ +334
            TextMeshProUGUI name = CreateText(panel.transform, "LevelName", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(0f, 355f), new Vector2(940f, 48f),
                TextAnchor.MiddleCenter, 30);
            name.color = TextSecondary;

            // 星级行：y_svg 218..285 → 中心 251 → Y=+289；三颗星 x = −100 / 0 / +100
            CreateImageAt(panel.transform, "Star1", new Vector2(0.5f, 0.5f), new Vector2(-100f, 289f),
                new Vector2(62f, 62f), "UI_Star_On", new Color(1f, 0.788f, 0.302f, 1f), false);
            CreateImageAt(panel.transform, "Star2", new Vector2(0.5f, 0.5f), new Vector2(0f, 289f),
                new Vector2(62f, 62f), "UI_Star_On", new Color(1f, 0.788f, 0.302f, 1f), false);
            CreateImageAt(panel.transform, "Star3", new Vector2(0.5f, 0.5f), new Vector2(100f, 289f),
                new Vector2(62f, 62f), "UI_Star_On", new Color(1f, 0.788f, 0.302f, 1f), false);

            TextMeshProUGUI best = CreateText(panel.transform, "BestStarText", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(0f, 238f), new Vector2(600f, 36f),
                TextAnchor.MiddleCenter, 24);
            best.color = TextSecondary;

            // 信息格：2 列 × 3 行（回合数 / 波次 / 初始金币 / 初始生命 / 难度 / 最佳用时）
            // y_svg 322..496 → 中心 409 → Y=+131；单元 430×50、列距 450、行距 62
            // ⚠️ 刻意**逐个写开**而不是用循环：`check_ui_contract.py` 靠"字面量节点名"比对
            //   View 的 Find 路径，写成 `infoNames[i]` 会让这 6 个节点全部漏检。
            CreateText(panel.transform, "Info1", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(-225f, 131f), new Vector2(430f, 50f),
                TextAnchor.MiddleCenter, 28);
            CreateText(panel.transform, "Info2", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(225f, 131f), new Vector2(430f, 50f),
                TextAnchor.MiddleCenter, 28);
            CreateText(panel.transform, "Info3", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(-225f, 69f), new Vector2(430f, 50f),
                TextAnchor.MiddleCenter, 28);
            CreateText(panel.transform, "Info4", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(225f, 69f), new Vector2(430f, 50f),
                TextAnchor.MiddleCenter, 28);
            CreateText(panel.transform, "Info5", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(-225f, 7f), new Vector2(430f, 50f),
                TextAnchor.MiddleCenter, 28);
            CreateText(panel.transform, "Info6", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(225f, 7f), new Vector2(430f, 50f),
                TextAnchor.MiddleCenter, 28);

            // 本关怪物预览
            TextMeshProUGUI enemyLabel = CreateText(panel.transform, "EnemyLabel", "本关出现怪物",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -16f), new Vector2(880f, 32f),
                TextAnchor.MiddleCenter, 24);
            enemyLabel.color = TextSecondary;

            TextMeshProUGUI enemyRow = CreateText(panel.transform, "EnemyIcons", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(0f, -60f), new Vector2(880f, 64f),
                TextAnchor.MiddleCenter, 24);
            enemyRow.color = TextPrimary;

            CreatePanelButton(panel.transform, "PlayBtn", "开始挑战", new Vector2(0f, -194f), 560f, true, 88f, 34);
            CreatePanelButton(panel.transform, "ReplayBtn", "从头重打", new Vector2(-160f, -288f), 300f, false, 76f, 30);
            CreatePanelButton(panel.transform, "CloseBtn", "返回", new Vector2(160f, -288f), 300f, false, 76f, 30);

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, LevelDetailPath);
            Object.DestroyImmediate(root);
            report.Ok("LevelDetailView.prefab（TopBar / DetailTitle / LevelName / Star1-3 / BestStarText / Info1-6 / EnemyLabel+EnemyIcons / Play+Replay+Close）");
        }

        private static void BuildSellConfirm(EditorUtil.Report report)
        {
            report.Head("生成出售确认 → " + SellConfirmPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(SellConfirmPath, SellConfirmChildren, out extra))
            {
                report.Error("SellConfirmView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(SellConfirmPath);
            EditorUtil.EnsureFolderOfFile(SellConfirmPath);

            GameObject panel;
            GameObject root = CreateDialogShell("SellConfirmView", "", new Vector2(800f, 620f), report, out panel, -1f);
            root.AddComponent<SellConfirmView>();

            CreateImageAt(panel.transform, "TopBar", new Vector2(0.5f, 1f), Vector2.zero,
                new Vector2(800f, 24f), "UI_Chip_Gold", Fire);

            TextMeshProUGUI title = CreateText(panel.transform, "SellTitle", "确认出售？",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 241f), new Vector2(740f, 56f),
                TextAnchor.MiddleCenter, 48);
            title.color = TextPrimary;

            CreateImageAt(panel.transform, "TowerIcon", new Vector2(0.5f, 0.5f), new Vector2(0f, 158f),
                new Vector2(100f, 100f), "UI_TowerIcon_Normal", new Color(0.18f, 0.29f, 0.4f, 1f), false);

            TextMeshProUGUI name = CreateText(panel.transform, "TowerName", "塔",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 89f), new Vector2(740f, 44f),
                TextAnchor.MiddleCenter, 32);
            name.color = TextPrimary;

            TextMeshProUGUI warn = CreateText(panel.transform, "WarnText", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(0f, -5f), new Vector2(700f, 72f),
                TextAnchor.MiddleCenter, 27);
            warn.color = Fire;
            warn.enableWordWrapping = true;   // 两句警告文案要换行

            TextMeshProUGUI refundLabel = CreateText(panel.transform, "RefundLabel", "退回金币",
                new Vector2(0.5f, 0.5f), new Vector2(-100f, -80f), new Vector2(240f, 56f),
                TextAnchor.MiddleCenter, 30);
            refundLabel.color = TextSecondary;

            TextMeshProUGUI refundValue = CreateText(panel.transform, "RefundValue", "0",
                new Vector2(0.5f, 0.5f), new Vector2(80f, -78f), new Vector2(240f, 56f),
                TextAnchor.MiddleCenter, 34);
            refundValue.color = Gold;

            // 两按钮**并排同 y**（效果图 v2 修正：v1 竖排会越出面板底）
            CreatePanelButton(panel.transform, "ConfirmBtn", "确认出售", new Vector2(-260f, -210f), 240f, true, 88f, 32);
            CreatePanelButton(panel.transform, "CancelBtn", "取消", new Vector2(260f, -210f), 240f, false, 88f, 32);

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, SellConfirmPath);
            Object.DestroyImmediate(root);
            report.Ok("SellConfirmView.prefab（TopBar / SellTitle / TowerIcon / TowerName / WarnText / RefundLabel+RefundValue / Confirm+Cancel）");
        }

        private static void BuildConfirm(EditorUtil.Report report)
        {
            report.Head("生成通用确认弹窗 → " + ConfirmPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(ConfirmPath, ConfirmChildren, out extra))
            {
                report.Error("ConfirmView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            AssetDatabase.DeleteAsset(ConfirmPath);
            EditorUtil.EnsureFolderOfFile(ConfirmPath);

            GameObject panel;
            GameObject root = CreateDialogShell("ConfirmView", "", new Vector2(760f, 560f), report, out panel, -1f);
            root.AddComponent<ConfirmView>();

            CreateImageAt(panel.transform, "TopBar", new Vector2(0.5f, 1f), Vector2.zero,
                new Vector2(760f, 24f), "UI_Chip_Gold", Cyan);

            TextMeshProUGUI title = CreateText(panel.transform, "BodyTitle", "确认",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 201f), new Vector2(700f, 56f),
                TextAnchor.MiddleCenter, 48);
            title.color = TextPrimary;

            TextMeshProUGUI body = CreateText(panel.transform, "BodyText", string.Empty,
                new Vector2(0.5f, 0.5f), new Vector2(0f, 60f), new Vector2(660f, 120f),
                TextAnchor.MiddleCenter, 28);
            body.color = TextSecondary;
            body.enableWordWrapping = true;   // 正文必须能换行，否则长文案会横着穿出面板

            CreateImageAt(panel.transform, "DangerIcon", new Vector2(0.5f, 0.5f), new Vector2(0f, -16f),
                new Vector2(96f, 96f), "UI_Panel_Red", DangerRed);

            CreatePanelButton(panel.transform, "ConfirmBtn", "确定", new Vector2(-220f, -168f), 240f, true, 88f, 32);
            CreatePanelButton(panel.transform, "CancelBtn", "取消", new Vector2(220f, -168f), 240f, false, 88f, 32);

            EditorUtility.SetDirty(root);
            PrefabUtility.SaveAsPrefabAsset(root, ConfirmPath);
            Object.DestroyImmediate(root);
            report.Ok("ConfirmView.prefab（TopBar / BodyTitle / BodyText / DangerIcon / Confirm+Cancel）");
        }

        // ==================================================================
        // UI 补全 B2：防御塔图鉴（整页 + 横向画廊，与关卡选择同款几何）
        // ==================================================================

        private static void BuildTowerCodex(EditorUtil.Report report)
        {
            report.Head("生成防御塔图鉴 → " + TowerCodexPath);
            string extra;
            if (!EditorUtil.IsSafeToRebuild(TowerCodexPath, TowerCodexChildren, out extra))
            {
                report.Error("TowerCodexView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
                return;
            }

            // 卡片先建：下面的 LoopListView2 要引用这份 prefab 资产
            GameObject itemPrefab = BuildTowerCodexItemPrefab(report);
            if (itemPrefab == null)
            {
                report.Error("塔图鉴卡片生成失败，TowerCodexView 未重建（避免产出「列表里没有条目」的空壳）");
                return;
            }

            AssetDatabase.DeleteAsset(TowerCodexPath);
            EditorUtil.EnsureFolderOfFile(TowerCodexPath);

            GameObject panel;
            GameObject root = CreateDialogShell("TowerCodexView", "", Vector2.zero, report, out panel, 0f);
            root.AddComponent<TowerCodexView>();

            // 标题基线 y_svg 90（整页 64 号）→ 盒中心 ≈ 450 + 22 = +472
            TextMeshProUGUI title = CreateText(panel.transform, "CodexTitle", "防御塔图鉴",
                new Vector2(0.5f, 0.5f), new Vector2(0f, 472f), new Vector2(1400f, 92f),
                TextAnchor.MiddleCenter, 64);
            title.color = TextPrimary;

            // ---- 列表（结构必须与 SelectView 完全同款，否则吸附居中会失效）----
            GameObject list = new GameObject("List", typeof(RectTransform));
            list.transform.SetParent(panel.transform, false);
            RectTransform lrt = (RectTransform)list.transform;
            lrt.anchorMin = new Vector2(0.5f, 0.5f);
            lrt.anchorMax = new Vector2(0.5f, 0.5f);
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = new Vector2(0f, -10f);
            lrt.sizeDelta = new Vector2(CodexListW, CodexListH);

            Image trackImg = list.AddComponent<Image>();
            trackImg.color = new Color(0.04f, 0.06f, 0.10f, 0.6f);
            trackImg.raycastTarget = true;
            list.AddComponent<RectMask2D>();

            GameObject viewport = new GameObject("Viewport", typeof(RectTransform));
            viewport.transform.SetParent(list.transform, false);
            RectTransform vrt = (RectTransform)viewport.transform;
            // ⚠️ pivot.x 必须预置 0（LoopListView2 的 AdjustPivot 会强改），矩形用 offsetMin/Max 描述
            vrt.pivot = new Vector2(0f, 0.5f);
            vrt.anchorMin = new Vector2(0f, 0.5f);
            vrt.anchorMax = new Vector2(1f, 0.5f);
            vrt.offsetMin = new Vector2((CodexListW - CodexItemW) * 0.5f, -CodexListH * 0.5f);
            vrt.offsetMax = new Vector2(-(CodexListW - CodexItemW) * 0.5f, CodexListH * 0.5f);

            GameObject content = new GameObject("Content", typeof(RectTransform));
            content.transform.SetParent(viewport.transform, false);
            RectTransform crt = (RectTransform)content.transform;
            crt.anchorMin = new Vector2(0f, 0.5f);
            crt.anchorMax = new Vector2(0f, 0.5f);
            crt.pivot = new Vector2(0f, 0.5f);
            crt.anchoredPosition = Vector2.zero;
            crt.sizeDelta = new Vector2(CodexItemW, CodexListH);

            ScrollRect sr = list.AddComponent<ScrollRect>();
            sr.content = crt;
            sr.viewport = vrt;
            sr.horizontal = true;
            sr.vertical = false;
            sr.movementType = ScrollRect.MovementType.Elastic;
            sr.elasticity = 0.1f;
            sr.inertia = true;
            sr.decelerationRate = 0.135f;
            sr.scrollSensitivity = 40f;

            LoopListView2 lv = list.AddComponent<LoopListView2>();
            ConfigureLoopListView(lv, itemPrefab, CodexItemGap, 2);

            // 左右箭头（ASCII < >，与选关界面同一理由：中文 SDF 不保证有 ◀▶ 码位）
            CreatePanelButton(panel.transform, "LeftBtn", "<",
                new Vector2(-860f, -10f), SelectArrowW, false, SelectArrowH, CodexArrowFontSize);
            CreatePanelButton(panel.transform, "RightBtn", ">",
                new Vector2(860f, -10f), SelectArrowW, false, SelectArrowH, CodexArrowFontSize);

            CreateText(panel.transform, "PageText", "1 / 5",
                new Vector2(0.5f, 0.5f), new Vector2(0f, -330f), new Vector2(600f, 44f),
                TextAnchor.MiddleCenter, 28);

            CreatePanelButton(panel.transform, "CloseBtn", "返回", new Vector2(0f, -430f), 340f, true, 84f, 32);

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, TowerCodexPath);
            Object.DestroyImmediate(root);
            if (saved == null)
            {
                report.Error("保存失败：" + TowerCodexPath);
                return;
            }
            report.Ok("TowerCodexView.prefab（整页：Bg / Panel( CodexTitle / List(Viewport/Content) / LeftBtn / RightBtn / PageText / CloseBtn )）");
        }

        /// <summary>塔图鉴卡片（460×640）：图标 + 塔名 + 定位 + 四项数值 + 描述。</summary>
        private static GameObject BuildTowerCodexItemPrefab(EditorUtil.Report report)
        {
            AssetDatabase.DeleteAsset(TowerCodexItemPath);   // 幂等：先删后建
            EditorUtil.EnsureFolderOfFile(TowerCodexItemPath);

            GameObject go = new GameObject("TowerCodexItem", typeof(RectTransform));
            RectTransform rt = (RectTransform)go.transform;
            // 横向列表统一口径：锚点/轴心 = 左侧中点（与 SelectLevelItem 同款）
            rt.anchorMin = new Vector2(0f, 0.5f);
            rt.anchorMax = new Vector2(0f, 0.5f);
            rt.pivot = new Vector2(0f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(CodexItemW, CodexItemH);
            go.AddComponent<LoopListViewItem2>();
            go.AddComponent<TowerCodexItem>();

            GameObject body = new GameObject("Body", typeof(RectTransform));
            body.transform.SetParent(go.transform, false);
            RectTransform brt = (RectTransform)body.transform;
            brt.anchorMin = Vector2.zero;
            brt.anchorMax = Vector2.one;
            brt.pivot = new Vector2(0.5f, 0.5f);
            brt.anchoredPosition = Vector2.zero;
            brt.sizeDelta = Vector2.zero;
            // 卡片淡化作用在 Body 上（见 TowerCodexView.UpdateItemVisuals），所以这里补一个 CanvasGroup
            body.AddComponent<CanvasGroup>();
            CreateImageAt(body.transform, "CardBg", new Vector2(0.5f, 0.5f), Vector2.zero,
                new Vector2(CodexItemW, CodexItemH), "UI_Panel_Cyan", new Color(0.118f, 0.161f, 0.224f, 0.96f));
            CreateImageAt(body.transform, "TopBar", new Vector2(0.5f, 1f), Vector2.zero,
                new Vector2(CodexItemW, 4f), null, new Color(0.208f, 0.878f, 1f, 1f));
            CreateImageAt(body.transform, "Icon", new Vector2(0.5f, 0.5f), new Vector2(0f, 180f),
                new Vector2(240f, 240f), "UI_TowerIcon_Normal", new Color(0.18f, 0.29f, 0.4f, 1f), false);

            CreateText(body.transform, "TypeName", "塔", new Vector2(0.5f, 0.5f), new Vector2(0f, 10f),
                new Vector2(400f, 52f), TextAnchor.MiddleCenter, 40);
            CreateText(body.transform, "Role", string.Empty, new Vector2(0.5f, 0.5f), new Vector2(0f, -40f),
                new Vector2(400f, 40f), TextAnchor.MiddleCenter, 26);
            CreateImageAt(body.transform, "Divider", new Vector2(0.5f, 0.5f), new Vector2(0f, -70f),
                new Vector2(360f, 1f), null, new Color(0.227f, 0.290f, 0.388f, 0.3f));

            CreateText(body.transform, "DpsRow", string.Empty, new Vector2(0.5f, 0.5f), new Vector2(0f, -105f),
                new Vector2(380f, 36f), TextAnchor.MiddleCenter, 26);
            CreateText(body.transform, "RangeRow", string.Empty, new Vector2(0.5f, 0.5f), new Vector2(0f, -143f),
                new Vector2(380f, 36f), TextAnchor.MiddleCenter, 26);
            CreateText(body.transform, "SpeedRow", string.Empty, new Vector2(0.5f, 0.5f), new Vector2(0f, -181f),
                new Vector2(380f, 36f), TextAnchor.MiddleCenter, 26);
            CreateText(body.transform, "PriceRow", string.Empty, new Vector2(0.5f, 0.5f), new Vector2(0f, -219f),
                new Vector2(380f, 36f), TextAnchor.MiddleCenter, 26);
            CreateText(body.transform, "DescText", string.Empty, new Vector2(0.5f, 0.5f), new Vector2(0f, -272f),
                new Vector2(380f, 80f), TextAnchor.MiddleCenter, 24);

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(go, TowerCodexItemPath);
            Object.DestroyImmediate(go);
            if (saved == null)
            {
                report.Error("保存失败：" + TowerCodexItemPath);
                return null;
            }
            report.Ok("TowerCodexItem.prefab（Body: CardBg / TopBar / Icon / TypeName / Role / Divider / Dps|Range|Speed|Price / DescText）");
            return saved;
        }

        /// <summary>把生成出来的某个子节点置为初始隐藏（由 View 在运行期按状态切换）。</summary>
        private static void SetNodeActive(Transform root, string path, bool active)
        {
            Transform t = root.Find(path);
            if (t != null && t.gameObject.activeSelf != active)
            {
                t.gameObject.SetActive(active);
            }
        }

        // ------------------------------------------------------------------
        // 构件
        // ------------------------------------------------------------------

        private static TextMeshProUGUI CreateText(Transform parent, string name, string content,
            Vector2 anchor, Vector2 anchoredPos, Vector2 size, TextAnchor align, int fontSize)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);

            RectTransform rt = (RectTransform)go.transform;
            // 用左上/顶部为轴心的锚点，避免不同分辨率下位置漂移
            rt.anchorMin = anchor;
            rt.anchorMax = anchor;
            rt.pivot = new Vector2(anchor.x, anchor.y);
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = size;

            // 【为什么用 TextMeshProUGUI（UGUI 版 TMP）而不是 TextMeshPro】
            //   TextMeshProUGUI 才是 Canvas 下渲染的组件；TextMeshPro 是世界空间网格版。
            //   UI 层的所有文本都必须用 TextMeshProUGUI，否则不会出现在 Canvas 里。
            TextMeshProUGUI t = go.AddComponent<TextMeshProUGUI>();
            TMP_FontAsset font = EditorUtil.GetDefaultTmpFont();
            if (font != null)
            {
                t.font = font;
            }
            t.text = content;
            t.fontSize = fontSize;
            t.alignment = ToTmpAlignment(align);
            t.color = TextColor;
            t.raycastTarget = false;    // 文本不吃点击，避免挡住按钮

            // 描边：背景是浅色纸张纹理时纯白字会看不清。
            // 【TMP 不支持 UGUI 的 Outline 组件】UGUI 描边是靠复制顶点实现的组件；
            //   TMP 的描边是**材质属性**（_OutlineWidth / _OutlineColor），必须给文本
            //   指定一份开启了 outline 的材质预设。这里在生成期取/建该材质并赋上。
            //   取不到字体时不设置材质，退化为无描边（不影响功能）。
            Material outlineMat = GetOrCreateOutlineMaterial(font);
            if (outlineMat != null)
            {
                t.fontSharedMaterial = outlineMat;
            }

            // 不自动换行 + 溢出可见：与旧版 UGUI Text 默认行为一致，
            // 需要换行的少数节点（Tips / Stats / 关卡按钮）再单独打开 enableWordWrapping。
            t.enableWordWrapping = false;
            t.overflowMode = TextOverflowModes.Overflow;
            return t;
        }

        /// <summary>
        /// 取一份"开启描边"的 TMP 字体材质（预设资产）。
        ///
        /// 【为什么要落到资产文件】TMP 的材质是资产；若每个文本都 new 一份材质，
        ///   ① 会产生大量运行时材质实例、破坏合批 ② 存进 prefab 后会变成内嵌资产，
        ///   一堆重复。所以这里统一建一份共享材质资产，所有文本引用同一份。
        /// 首次调用时创建，之后直接复用（幂等）。
        /// </summary>
        private static Material GetOrCreateOutlineMaterial(TMP_FontAsset font)
        {
            if (font == null)
            {
                return null;
            }
            Material cached = AssetDatabase.LoadAssetAtPath<Material>(OutlineMaterialPath);
            if (cached != null)
            {
                return cached;
            }

            // 以字体自带的默认材质为模板复制一份，开启 outline
            Material mat = new Material(font.material);
            mat.name = "SiYuanSongTi SDF - Outline";
            mat.SetColor(ShaderUtilities.ID_OutlineColor, OutlineColor);
            mat.SetFloat(ShaderUtilities.ID_OutlineWidth, 0.12f);
            mat.EnableKeyword(ShaderUtilities.Keyword_Outline);

            EditorUtil.EnsureFolderOfFile(OutlineMaterialPath);
            AssetDatabase.CreateAsset(mat, OutlineMaterialPath);
            AssetDatabase.SaveAssets();

            // 描边材质被所有 UI 预制体共享引用（和字体一样是共享依赖）。
            // 【为什么在这里不直接设 AB 名】AB 名由 ResTable → ABNameSetter 统一写入
            //   （唯一权威来源）。ResTable 已登记 "Font_Outline_Mat" → bundle "font"，
            //   故此处只需保证资产存在，随后向导里的 ABNameSetter 步骤会赋名，避免重复逻辑。
            return mat;
        }

        /// <summary>统一的中文字体描边材质资产路径</summary>
        private const string OutlineMaterialPath = "Assets/Font/SiYuanSongTi SDF - Outline.mat";

        /// <summary>
        /// UGUI `TextAnchor` → TMP `TextAlignmentOptions` 的映射。
        ///
        /// 【为什么需要显式映射】TMP 用 (水平+垂直) 两位组合的枚举，UGUI 用九宫格 TextAnchor；
        ///   二者无隐式转换。这里逐项翻译，保持生成器接口签名不变（调用点二十多处）。
        /// </summary>
        private static TextAlignmentOptions ToTmpAlignment(TextAnchor a)
        {
            switch (a)
            {
                case TextAnchor.UpperLeft:    return TextAlignmentOptions.TopLeft;
                case TextAnchor.UpperCenter:  return TextAlignmentOptions.Top;
                case TextAnchor.UpperRight:   return TextAlignmentOptions.TopRight;
                case TextAnchor.MiddleLeft:   return TextAlignmentOptions.Left;
                case TextAnchor.MiddleCenter: return TextAlignmentOptions.Center;
                case TextAnchor.MiddleRight:  return TextAlignmentOptions.Right;
                case TextAnchor.LowerLeft:    return TextAlignmentOptions.BottomLeft;
                case TextAnchor.LowerCenter:  return TextAlignmentOptions.Bottom;
                case TextAnchor.LowerRight:   return TextAlignmentOptions.BottomRight;
                default:                      return TextAlignmentOptions.Center;
            }
        }

        private static void CreateButton(Transform parent, string name, string label, Vector2 anchoredPos,
            bool primary = false)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);

            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = new Vector2(0.5f, 0f);
            rt.anchorMax = new Vector2(0.5f, 0f);
            rt.pivot = new Vector2(0.5f, 0f);
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = new Vector2(220f, 72f);

            Image img = go.AddComponent<Image>();
            ApplySlicedSkin(img, primary ? "UI_Btn_Primary" : "UI_Btn_Secondary", ButtonColor);

            Button btn = go.AddComponent<Button>();
            btn.targetGraphic = img;    // ★ 必须显式指定，否则按钮没有按下反馈
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            TextMeshProUGUI t = CreateText(go.transform, "Label", label,
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(220f, 72f),
                TextAnchor.MiddleCenter, SmallFontSize);
            // Label 要铺满按钮，单独设一次
            RectTransform lrt = (RectTransform)t.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = Vector2.zero;
            lrt.sizeDelta = Vector2.zero;
        }

        /// <summary>
        /// 生成一颗塔按钮（128×128），带一个 Image 子节点用于承载塔图标（占位期留空）。
        /// 结构与手工版一致：Btn_Tower_* → Image(TowerIcon)，点击靠按钮自身，文字走 Label。
        /// </summary>
        private static void CreateTowerButton(Transform parent, TowerButtonSpec spec)
        {
            GameObject go = new GameObject(spec.NodeName, typeof(RectTransform));
            go.transform.SetParent(parent, false);

            RectTransform rt = (RectTransform)go.transform;
            // 【锚点必须是"屏幕中心"，不是左下角】spec.Pos 是按"画布中心为原点"量的
            //   （效果图：五颗按钮的中心 x = -548/-274/0/274/548，y = -427）。
            //   改成左下锚点会让整排按钮跑到画布外（表现为"塔建造栏整排消失、无法建塔"）——
            //   这是 prefab 重建时真实发生过的回归，改动前请对照 Docs/ui_mockups/02b 的坐标。
            rt.anchorMin = new Vector2(0.5f, 0.5f);
            rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = spec.Pos;
            rt.sizeDelta = new Vector2(128f, 128f);

            Image img = go.AddComponent<Image>();
            ApplySlicedSkin(img, "UI_TowerBtn_Frame", ButtonColor);

            Button btn = go.AddComponent<Button>();
            btn.targetGraphic = img;
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            // 图标子节点：占据按钮**上部**，底部留给价格签。
            // 【为什么不是铺满整格】铺满会与底部的价格芯片重叠，数字直接压在图标上。
            GameObject icon = new GameObject("Image", typeof(RectTransform));
            icon.transform.SetParent(go.transform, false);
            RectTransform irt = (RectTransform)icon.transform;
            irt.anchorMin = new Vector2(0.5f, 1f);
            irt.anchorMax = new Vector2(0.5f, 1f);
            irt.pivot = new Vector2(0.5f, 1f);
            irt.anchoredPosition = new Vector2(0f, -4f);
            irt.sizeDelta = new Vector2(84f, 84f);   // 128 - 4 - 84 = 40 > 价格签顶边 36，留 4px 缝
            Image iconImg = icon.AddComponent<Image>();
            iconImg.color = new Color(1f, 1f, 1f, 0.85f);
            iconImg.raycastTarget = false;  // 不吃点击，点击交给父级 Button
            Sprite sprite = LoadIcon(spec.TowerType);
            if (sprite != null)
            {
                iconImg.sprite = sprite;
                iconImg.color = Color.white;
            }

            // 价格签底（可选节点，HudView 视为可选）
            GameObject priceBg = new GameObject("PriceBg", typeof(RectTransform));
            priceBg.transform.SetParent(go.transform, false);
            RectTransform pbrt = (RectTransform)priceBg.transform;
            pbrt.anchorMin = new Vector2(0.5f, 0f);
            pbrt.anchorMax = new Vector2(0.5f, 0f);
            pbrt.pivot = new Vector2(0.5f, 0f);
            pbrt.anchoredPosition = new Vector2(0f, 2f);
            pbrt.sizeDelta = new Vector2(96f, 34f);
            Image priceBgImg = priceBg.AddComponent<Image>();
            priceBgImg.raycastTarget = false;
            ApplySlicedSkin(priceBgImg, "UI_Chip_Neutral", new Color(0.08f, 0.11f, 0.16f, 0.8f));

            // 【契约】塔按钮**不配 Label**（Docs/HudView_Sync_and_TowerUI_Plan.md §2）：
            // 需要显示价格时用 PriceText 子节点，不要复用 Label —— 否则"按钮上的文字"
            // 会同时承担"塔名"和"价格"两种语义，将来加角标或换图标栏时必然打架。
            // 本轮只建节点、文案留空，由 HudView 按当前配置表价格刷新。
            TextMeshProUGUI pt = CreateText(go.transform, "PriceText", string.Empty,
                new Vector2(0.5f, 0f), new Vector2(0f, 4f), new Vector2(128f, 36f),
                TextAnchor.LowerCenter, 24);   // 24 号才塞得进 96×34 的价格芯片（32 号会溢出）
            pt.raycastTarget = false;   // 不吃点击，点击交给父级 Button
        }

        /// <summary>
        /// 按塔型取建造栏图标。
        /// 【生成期只在编辑器里跑，直接走 AssetDatabase 读塔身贴图，不依赖运行时 ResLoader/AB】
        /// 资源未齐时返回 null → 按钮自动退化为纯色块，不影响逻辑联调。
        /// 【贴图名不统一】三塔美术文件名各异，逐塔指定（见 TowerPrefabConverter.Specs）
        /// </summary>
        private static Sprite LoadIcon(int towerType)
        {
            // ① 优先用程序生成的深色科幻塔图标（UISkinArtGenerator 产出）
            Sprite ui = LoadUiSprite(TowerIconSpriteName(towerType));
            if (ui != null)
            {
                return ui;
            }

            // ② 退化为塔身贴图
            string path;
            switch (towerType)
            {
                case 2: path = "Assets/_UIAssets/Tower/Power/tower_base.png"; break;
                case 3: path = "Assets/_UIAssets/Tower/retard/slowtower_base.png"; break;
                // 穿透塔 / 激光塔：专属美术未到位，暂时复用普通塔图标。
                // 【为什么不干脆留空退化成纯色块】纯色块在五连排里看不出是哪一种塔，
                // 联调"点对按钮了吗"反而更难判断；复用现有图标至少可区分"这是塔按钮"。
                case 4:
                case 5:
                default: path = "Assets/_UIAssets/Tower/Normal/turret_base_128.png"; break;
            }
            // 资源还没到 —— 不是错误，静默退化为纯色块
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }

        private static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = Vector2.zero;
            rt.localScale = Vector3.one;
        }
    }
}
