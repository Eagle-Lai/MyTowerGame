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
    /// 【关于中文字体】这里用 Unity 内置动态字体（LegacyRuntime.ttf）。
    /// 在 Windows / macOS 编辑器与 PC 包中它能正常渲染中文；
    /// 但 Android / iOS 包内没有系统字体可回退，中文会显示成方块 ——
    /// 出移动包前需要换成自带中文字形的 TTF（见操作指南「字体」一节）。
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

        private static readonly string[] SelectChildren = { "Bg", "Panel" };
        private static readonly string[] PauseChildren = { "Bg", "Panel" };
        private static readonly string[] SettingChildren = { "Bg", "Panel" };

        // TowerInfoView 由本生成器管理的直接子节点集合（用于重建前的安全护栏）
        private static readonly string[] TowerInfoChildren = { "Bg", "Panel" };

        // HudView 由本生成器管理的直接子节点集合（用于重建前的安全护栏）
        private static readonly string[] HudChildren =
        {
            "GoldText", "HpText", "RoundText",
            "Btn_Tower_Normal", "Btn_Tower_Power", "Btn_Tower_Retard",
            "Btn_Tower_Pierce", "Btn_Tower_Laser",
            "StartButton",
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

        private static readonly Color TextColor = new Color(1f, 1f, 1f, 1f);
        private static readonly Color ButtonColor = new Color(0.18f, 0.24f, 0.34f, 0.92f);
        private static readonly Color OutlineColor = new Color(0f, 0f, 0f, 0.85f);

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

        /// <summary>供一键向导调用（不弹窗）。**全量重建**，会覆盖手工改过的 prefab。</summary>
        public static void BuildInternal(EditorUtil.Report report)
        {
            BuildHud(report);
            BuildTips(report);
            BuildTowerInfo(report);
            BuildSelect(report);
            BuildPause(report);
            BuildSetting(report);
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
        }

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
            else BuildSetting(report);
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

            // 底部：三颗塔按钮 + 开始
            for (int i = 0; i < TowerButtons.Length; i++)
            {
                CreateTowerButton(root.transform, TowerButtons[i]);
            }
            CreateButton(root.transform, "StartButton", "开始", new Vector2(140f, 60f));

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, HudPath);
            Object.DestroyImmediate(root);

            if (saved == null)
            {
                report.Error("保存失败：" + HudPath);
                return;
            }
            report.Ok("HudView.prefab（GoldText / HpText / RoundText / Btn_Tower_Normal·Power·Retard·Pierce·Laser / StartButton）");
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

            Text tip = CreateText(root.transform, "TipText", string.Empty,
                new Vector2(0.5f, 0.30f), Vector2.zero, new Vector2(1100f, 60f),
                TextAnchor.MiddleCenter, BigFontSize);
            tip.horizontalOverflow = HorizontalWrapMode.Wrap;
            tip.verticalOverflow = VerticalWrapMode.Overflow;

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
            panelImg.color = new Color(0.12f, 0.16f, 0.24f, 0.96f);

            // 标题 / 属性
            CreateText(panel.transform, "Title", "防御塔  Lv.1",
                new Vector2(0.5f, 1f), new Vector2(0f, -34f), new Vector2(500f, 52f),
                TextAnchor.MiddleCenter, BigFontSize);

            Text stats = CreateText(panel.transform, "Stats", "攻击 -   射程 -   攻速 -",
                new Vector2(0.5f, 1f), new Vector2(0f, -100f), new Vector2(500f, 44f),
                TextAnchor.MiddleCenter, SmallFontSize);
            stats.horizontalOverflow = HorizontalWrapMode.Wrap;

            // 三个按钮（竖排）
            CreatePanelButton(panel.transform, "UpgradeBtn", "升级", new Vector2(0f, -20f));
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
            Vector2 panelSize, EditorUtil.Report report, out GameObject panel)
        {
            GameObject root = new GameObject(rootName, typeof(RectTransform));
            Stretch((RectTransform)root.transform);

            GameObject bg = new GameObject("Bg", typeof(RectTransform));
            bg.transform.SetParent(root.transform, false);
            Stretch((RectTransform)bg.transform);
            Image bgImg = bg.AddComponent<Image>();
            bgImg.color = new Color(0f, 0f, 0f, 0.55f);
            Button bgBtn = bg.AddComponent<Button>();
            bgBtn.targetGraphic = bgImg;

            panel = new GameObject("Panel", typeof(RectTransform));
            panel.transform.SetParent(root.transform, false);
            RectTransform prt = (RectTransform)panel.transform;
            prt.anchorMin = new Vector2(0.5f, 0.5f);
            prt.anchorMax = new Vector2(0.5f, 0.5f);
            prt.pivot = new Vector2(0.5f, 0.5f);
            prt.anchoredPosition = Vector2.zero;
            prt.sizeDelta = panelSize;
            Image panelImg = panel.AddComponent<Image>();
            panelImg.color = new Color(0.12f, 0.16f, 0.24f, 0.96f);

            CreateText(panel.transform, "Title", title,
                new Vector2(0.5f, 1f), new Vector2(0f, -36f), new Vector2(panelSize.x - 60f, 56f),
                TextAnchor.MiddleCenter, BigFontSize);

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
            AssetDatabase.DeleteAsset(SelectPath);
            EditorUtil.EnsureFolderOfFile(SelectPath);

            GameObject panel;
            GameObject root = CreateDialogShell("SelectView", "选择关卡",
                new Vector2(1120f, 640f), report, out panel);
            root.AddComponent<SelectView>();

            CreateText(panel.transform, "Summary", "已通关 0/8　★ 0/24",
                new Vector2(0.5f, 1f), new Vector2(0f, -92f), new Vector2(1000f, 44f),
                TextAnchor.MiddleCenter, SmallFontSize);

            // 关卡按钮容器：模板按钮在里面，运行时被克隆成 N 份
            GameObject list = new GameObject("List", typeof(RectTransform));
            list.transform.SetParent(panel.transform, false);
            RectTransform lrt = (RectTransform)list.transform;
            lrt.anchorMin = new Vector2(0.5f, 1f);
            lrt.anchorMax = new Vector2(0.5f, 1f);
            lrt.pivot = new Vector2(0.5f, 1f);
            lrt.anchoredPosition = new Vector2(0f, -130f);
            lrt.sizeDelta = new Vector2(1040f, 400f);

            CreatePanelButton(list.transform, "LevelButtonTemplate", "关卡", Vector2.zero);
            Transform tpl = list.transform.Find("LevelButtonTemplate");
            if (tpl != null)
            {
                RectTransform trt = (RectTransform)tpl;
                // 锚点改左上：与 SelectView.CreateLevelButton 的排布口径一致（手排网格，不用 LayoutGroup）
                trt.anchorMin = new Vector2(0f, 1f);
                trt.anchorMax = new Vector2(0f, 1f);
                trt.pivot = new Vector2(0f, 1f);
                trt.sizeDelta = new Vector2(240f, 96f);
                trt.anchoredPosition = Vector2.zero;
                Text tl = tpl.GetComponentInChildren<Text>(true);
                if (tl != null)
                {
                    tl.alignment = TextAnchor.MiddleCenter;
                    tl.horizontalOverflow = HorizontalWrapMode.Wrap;
                    tl.verticalOverflow = VerticalWrapMode.Overflow;
                }
                tpl.gameObject.SetActive(false);
            }

            CreatePanelButton(panel.transform, "CloseBtn", "返回", new Vector2(0f, -270f));

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, SelectPath);
            Object.DestroyImmediate(root);
            if (saved == null)
            {
                report.Error("保存失败：" + SelectPath);
                return;
            }
            report.Ok("SelectView.prefab（Bg / Panel( Title / Summary / List(LevelButtonTemplate) / CloseBtn )）");
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

        /// <summary>面板内按钮：居中锚点、固定尺寸，带 Label 子节点</summary>
        private static void CreatePanelButton(Transform parent, string name, string label, Vector2 anchoredPos)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);

            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = new Vector2(0.5f, 0.5f);
            rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = anchoredPos;
            rt.sizeDelta = new Vector2(320f, 72f);

            Image img = go.AddComponent<Image>();
            img.color = ButtonColor;

            Button btn = go.AddComponent<Button>();
            btn.targetGraphic = img;
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            Text t = CreateText(go.transform, "Label", label,
                new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(320f, 72f),
                TextAnchor.MiddleCenter, SmallFontSize);
            RectTransform lrt = (RectTransform)t.transform;
            lrt.anchorMin = Vector2.zero;
            lrt.anchorMax = Vector2.one;
            lrt.pivot = new Vector2(0.5f, 0.5f);
            lrt.anchoredPosition = Vector2.zero;
            lrt.sizeDelta = Vector2.zero;
        }

        // ------------------------------------------------------------------
        // 构件
        // ------------------------------------------------------------------

        private static Text CreateText(Transform parent, string name, string content,
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

            Text t = go.AddComponent<Text>();
            t.font = EditorUtil.GetDefaultFont();
            t.text = content;
            t.fontSize = fontSize;
            t.alignment = align;
            t.color = TextColor;
            t.raycastTarget = false;    // 文本不吃点击，避免挡住按钮

            // 描边：背景是浅色纸张纹理时纯白字会看不清
            Outline o = go.AddComponent<Outline>();
            o.effectColor = OutlineColor;
            o.effectDistance = new Vector2(1.5f, -1.5f);
            return t;
        }

        private static void CreateButton(Transform parent, string name, string label, Vector2 anchoredPos)
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
            img.color = ButtonColor;    // sprite 为空时 Image 会画一个纯色矩形，够用

            Button btn = go.AddComponent<Button>();
            btn.targetGraphic = img;    // ★ 必须显式指定，否则按钮没有按下反馈
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            Text t = CreateText(go.transform, "Label", label,
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
            rt.anchorMin = new Vector2(0f, 0f);     // 左下锚点，与手工版坐标一致
            rt.anchorMax = new Vector2(0f, 0f);
            rt.pivot = new Vector2(0f, 0f);
            rt.anchoredPosition = spec.Pos;
            rt.sizeDelta = new Vector2(128f, 128f);

            Image img = go.AddComponent<Image>();
            img.color = ButtonColor;    // sprite 为空时画纯色矩形

            Button btn = go.AddComponent<Button>();
            btn.targetGraphic = img;
            ColorBlock cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color(1.15f, 1.15f, 1.15f, 1f);
            cb.pressedColor = new Color(0.8f, 0.8f, 0.8f, 1f);
            cb.disabledColor = new Color(0.5f, 0.5f, 0.5f, 0.6f);
            btn.colors = cb;

            // 图标占位子节点（美术资源到位后往这里塞 sprite）
            GameObject icon = new GameObject("Image", typeof(RectTransform));
            icon.transform.SetParent(go.transform, false);
            RectTransform irt = (RectTransform)icon.transform;
            irt.anchorMin = Vector2.zero;
            irt.anchorMax = Vector2.one;
            irt.pivot = new Vector2(0.5f, 0.5f);
            irt.anchoredPosition = Vector2.zero;
            irt.sizeDelta = Vector2.zero;
            Image iconImg = icon.AddComponent<Image>();
            iconImg.color = new Color(1f, 1f, 1f, 0.85f);
            iconImg.raycastTarget = false;  // 不吃点击，点击交给父级 Button
            Sprite sprite = LoadIcon(spec.TowerType);
            if (sprite != null)
            {
                iconImg.sprite = sprite;
                iconImg.color = Color.white;
            }

            // 【契约】塔按钮**不配 Label**（Docs/HudView_Sync_and_TowerUI_Plan.md §2）：
            // 需要显示价格时用 PriceText 子节点，不要复用 Label —— 否则"按钮上的文字"
            // 会同时承担"塔名"和"价格"两种语义，将来加角标或换图标栏时必然打架。
            // 本轮只建节点、文案留空，由 HudView 按当前配置表价格刷新。
            Text pt = CreateText(go.transform, "PriceText", string.Empty,
                new Vector2(0.5f, 0f), new Vector2(0f, 4f), new Vector2(128f, 36f),
                TextAnchor.LowerCenter, SmallFontSize);
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
