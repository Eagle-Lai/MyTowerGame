using System.Collections.Generic;
using TMPro;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 把工程里所有 UI 预制体的**静态文案**节点批量挂上 <see cref="TextLocalizer"/>。
    ///
    /// 【为什么需要"批量挂"】
    ///   多语言组件是**挂在节点上的行为组件**，必须逐个组装进 prefab 才有意义。
    ///   手工一个个挂既慢又容易漏 —— 本工具让"代码改完"和"prefab 生效"一步到位。
    ///
    /// 【key 留空是刻意设计】
    ///   TextLocalizer 的 key 留空时会**自动拿节点上序列化的英文原文当 key**去查表
    ///   （表的主键就是英文原文本身）。所以挂上去即可用，无需在 Inspector 里再抄一遍 key，
    ///   也避免"key 抄岔 → 多语言静默失效"的老坑。
    ///
    /// 【幂等】已有 TextLocalizer 的节点跳过，不会重复挂。
    ///
        /// 【排除规则：运行时动态文本绝不挂】
        ///   这类节点的内容由 View 代码用 Localization.Get(key, args) / SetText 主动赋值，
        ///   挂了本地化组件反而会在切语言时把代码算好的内容冲掉。
        ///   判据 = 见 <see cref="DynamicNames"/>（按节点名，宁少挂不多挂）
        ///     + BindOne 里的两处结构性特判：TMP_Dropdown 内部文本（语言下拉框）、
        ///       MuteBtn/Label（"静音 / 取消静音"两态文本）。
    /// </summary>
    public static class LocalizationPrefabBinder
    {
        /// <summary>要处理的全部 UI 预制体（与 UIPrefabBuilder 的输出一一对应）。</summary>
        private static readonly string[] TargetPrefabs =
        {
            "Assets/Prefabs/UI/HudView.prefab",
            "Assets/Prefabs/UI/TipsView.prefab",
            "Assets/Prefabs/UI/TowerInfoView.prefab",
            "Assets/Prefabs/UI/SelectView.prefab",
            "Assets/Prefabs/UI/SelectLevelItem.prefab",
            "Assets/Prefabs/UI/PauseView.prefab",
            "Assets/Prefabs/UI/SettingView.prefab",
            "Assets/Prefabs/UI/LevelClearView.prefab",
            "Assets/Prefabs/UI/MainMenuView.prefab",
            "Assets/Prefabs/UI/LevelDetailView.prefab",
            "Assets/Prefabs/UI/SellConfirmView.prefab",
            "Assets/Prefabs/UI/ConfirmView.prefab",
            "Assets/Prefabs/UI/TowerCodexView.prefab",
            "Assets/Prefabs/UI/TowerCodexItem.prefab",
            // 游戏介绍弹窗（2026-10-14）：BackBtn/CloseBtn 的 Label 是静态文案
            "Assets/Prefabs/UI/GameIntroView.prefab",
            "Assets/HotUpdateUI/SplashView.prefab",
            "Assets/HotUpdateUI/LoadingView.prefab",
        };

        /// <summary>
        /// **运行时动态文本**节点名（View 代码会覆盖内容）→ 不挂本地化组件。
        ///
        /// 逐条依据（对照各 View 的代码）：
        ///   · GoldText / HpText / RoundText — HudView 每帧 SetText
        ///   · PriceText  — HudView 刷新塔价
        ///   · Title      — 除 MainMenu/Pause/Setting 的"页面标题"外，多数被 View SetText；
        ///                  这里统一排除（这些页面标题另有 CodexTitle/HotTitle/SellTitle 等直挂）
        ///   · Stats / StarDetail / RecordTip / LevelName / BestStarText — 结算/详情 View 带参查表
        ///   · Info1..6 / EnemyLabel / Summary / ClearText / StarText — 同上
        ///   · RefundValue / TowerName / WarnText / BodyText — 出售确认/通用确认 Setup 注入
        ///   · TypeName / Role / DescText / DpsRow / RangeRow / SpeedRow / PriceRow — 图鉴条目 Setup
        ///   · PageText — 图鉴页码
        ///   · StatusText / PercentText / TipText / PhaseText / SizeText / SpeedText /
        ///     DetailText / FailText / LoadingDots / VolumeText — 启动链与设置的运行时刷新
        ///   · Title(空串占位) — 骨架空标题
        /// </summary>
        private static readonly HashSet<string> DynamicNames = new HashSet<string>
        {
            "GoldText", "HpText", "RoundText", "PriceText",
            "Title",
            "Stats", "StarDetail", "RecordTip", "LevelName", "BestStarText",
            "Info1", "Info2", "Info3", "Info4", "Info5", "Info6",
            "EnemyLabel", "Summary", "ClearText", "StarText", "Stars",
            "RefundValue", "TowerName", "WarnText", "BodyText",
            "TypeName", "Role", "DescText", "DpsRow", "RangeRow", "SpeedRow", "PriceRow",
            "PageText",
            "StatusText", "PercentText", "TipText", "PhaseText", "SizeText", "SpeedText",
            "DetailText", "FailText", "LoadingDots", "VolumeText",
        };

        /// <summary>
        /// 这些节点名下的 TMP **是静态文案**，即便内容此刻为空也照样挂
        /// （挂上去后运行时按语言填；为空说明生成器给了空占位）。
        /// 主要是各页面的主标题，它们的名字与 View 的"动态 Title"区分开了。
        /// </summary>
        private static readonly HashSet<string> ForceStaticNames = new HashSet<string>
        {
            "CodexTitle", "HotTitle", "SellTitle", "GameTitle", "Subtitle",
        };

        [MenuItem("Tools/塔防/高级（单步重建）/批量挂多语言组件（TextLocalizer）", false, 308)]
        public static void BindFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            int files = BindAll(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log(report.Errors > 0
                ? string.Format("[多语言挂载] 有错误（处理 {0} 个预制体）：\n{1}", files, report.Text)
                : string.Format("[多语言挂载] 完成（处理 {0} 个预制体）：\n{1}", files, report.Text));
        }

        /// <summary>供向导调用（不弹窗）。返回处理的预制体数量。</summary>
        public static int BindAll(EditorUtil.Report report)
        {
            report.Head("批量挂 TextLocalizer（key 留空 → 用英文原文当 key）");
            int count = 0;
            for (int i = 0; i < TargetPrefabs.Length; i++)
            {
                if (BindOne(TargetPrefabs[i], report))
                {
                    count++;
                }
            }
            return count;
        }

        private static bool BindOne(string path, EditorUtil.Report report)
        {
            GameObject root = PrefabUtility.LoadPrefabContents(path);
            if (root == null)
            {
                report.Skip(System.IO.Path.GetFileName(path) + " 不存在，跳过");
                return false;
            }

            TextMeshProUGUI[] texts = root.GetComponentsInChildren<TextMeshProUGUI>(true);
            int added = 0;
            int skipped = 0;
            for (int i = 0; i < texts.Length; i++)
            {
                TextMeshProUGUI t = texts[i];
                if (t == null)
                {
                    continue;
                }
                string nm = t.gameObject.name;

                // SpeedButton/Label 是倍速显示（HudView.SetSpeedLabel 运行时覆盖），不本地化
                if (t.transform.parent != null && t.transform.parent.name == "SpeedButton")
                {
                    skipped++;
                    continue;
                }

                // MuteBtn/Label 是"静音 / 取消静音"两态文本（SettingView.Refresh 按存档状态写），
                // 挂了本地化组件会在切语言时被"按 prefab 原文 Mute"刷新、把 Unmute 状态冲掉。
                if (t.transform.parent != null && t.transform.parent.name == "MuteBtn")
                {
                    skipped++;
                    continue;
                }

                // Btn_Pause/Label 是"暂停 / 继续"两态文本（HudView.RefreshPauseLabel 按 GameClock.IsPaused 写），
                // 与 MuteBtn 同理：挂了本地化组件会在切语言时被"按 prefab 原文 Pause"刷回，
                // 把暂停态的 Continue 冲掉。该节点由 HudView 在语言切换时自己重算文案。
                if (t.transform.parent != null && t.transform.parent.name == "Btn_Pause")
                {
                    skipped++;
                    continue;
                }

                // TMP_Dropdown 内部的文本（设置界面的语言下拉框）一律跳过：
                //   · caption 与列表项由 TMP_Dropdown 运行时按当前语言自显名填充；
                //   · 挂了本地化组件后，切语言时会把它们按"占位原文"冲掉，表现为文案错乱。
                //   含未激活的 Template（弹出的列表模板）在内 —— includeInactive=true 覆盖。
                if (t.GetComponentInParent<TMP_Dropdown>(true) != null)
                {
                    skipped++;
                    continue;
                }

                // 纯符号文本（箭头 < > 等）：语言无关，不挂（挂了也会因表里没有而回退原文）
                if (IsSymbolOnly(t.text))
                {
                    skipped++;
                    continue;
                }

                if (DynamicNames.Contains(nm) && !ForceStaticNames.Contains(nm))
                {
                    skipped++;
                    continue;
                }
                if (t.GetComponent<TextLocalizer>() != null)
                {
                    continue;   // 幂等：已挂
                }
                bool force = ForceStaticNames.Contains(nm);
                if (!force && string.IsNullOrEmpty(t.text))
                {
                    continue;   // 空文本没 key 可查
                }
                t.gameObject.AddComponent<TextLocalizer>();
                added++;
            }

            if (added > 0)
            {
                PrefabUtility.SaveAsPrefabAsset(root, path);
            }
            PrefabUtility.UnloadPrefabContents(root);

            report.Ok(string.Format("{0}：新增 {1} 个 TextLocalizer（动态文本跳过 {2} 个）",
                System.IO.Path.GetFileName(path), added, skipped));
            return true;
        }

        /// <summary>
        /// 纯符号文本判定（箭头 `&lt;` `&gt;`、星号、乘号等）——语言无关，无需本地化。
        /// 只要**不含任何字母或汉字**就认为无需翻译。
        /// </summary>
        private static bool IsSymbolOnly(string s)
        {
            if (string.IsNullOrEmpty(s))
            {
                return true;
            }
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                if (char.IsLetter(c))
                {
                    return false;
                }
            }
            return true;
        }
    }
}
