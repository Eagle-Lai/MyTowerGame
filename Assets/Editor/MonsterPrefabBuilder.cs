using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 批量把 `Assets/_UIAssets/Monsters/**` 下的**全部**怪物转成战斗预制体。
    ///
    /// 源 prefab 是"美术包"形态：分部件 2D 骨骼式结构（Body/Head/腿/尾/Shadow + Anchor），
    /// 自带 Animator 与 SortingGroup，但**带着 CapsuleCollider2D**（v1.0 用来做 OnTriggerEnter）。
    /// 本工具把它转成"战斗形态"：
    ///   ① 去掉全部物理组件（需求 8：去物理化）
    ///   ② 挂 BaseEnemy
    ///   ③ 加 HpBar（Bg + Fill），位置与宽度**按实测渲染包围盒自适应**
    ///      —— 不同怪物体型差很多（猴子 vs 巨魔），写死坐标必然对不齐
    ///
    /// 产物：`Assets/Prefabs/Enemy/Enemy_<怪名>.prefab`（名字与打包规则见 MonsterCatalog）
    ///
    /// 动画不用管：源 prefab 的 Animator 已经引用了自己的 Controller
    ///（`_Common/Animations/<怪名>/Controller.controller`），克隆时会一并带过来。
    /// 所以配置表的 `animController` 可以留空，BaseEnemy 会沿用 prefab 自带的。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 9. 导入全部怪物（生成战斗预制体）
    /// </summary>
    public static class MonsterPrefabBuilder
    {
        public const string OutputDir = "Assets/Prefabs/Enemy";

        /// <summary>血条世界宽度 = 怪物世界宽度 × 此比例。
        /// 0.6 太宽（大怪的血条几乎横跨整个屏幕），0.5 是视觉上比较搭的值</summary>
        private const float BarWidthRatio = 0.5f;
        private const float BarMinWorldWidth = 0.35f;
        private const float BarMaxWorldWidth = 2.2f;
        /// <summary>血条世界高度（固定值，不随怪物宽度放大）。
        /// 之前让高度跟随宽度（宽的 1/5），大怪的血条高得像一块板，视觉上很突兀；
        /// 固定成一个薄条的厚度，所有怪物看起来才一致</summary>
        private const float BarWorldHeight = 0.11f;
        /// <summary>血条与头顶的间距 = 怪物世界高度 × 此比例（随体型缩放）</summary>
        private const float BarTopMarginRatio = 0.14f;
        private static readonly Color HpFillColor = new Color(0.35f, 0.90f, 0.35f, 1f);

        [MenuItem("Tools/塔防/9. 导入全部怪物（生成战斗预制体）", false, 108)]
        public static void BuildAllFromMenu()
        {
            if (!EditorUtility.DisplayDialog("导入全部怪物",
                    string.Format("将处理 {0} 个怪物，为每个生成：\n" +
                                  "  Assets/Prefabs/Enemy/Enemy_<怪名>.prefab\n\n" +
                                  "每个会：去掉物理组件、挂 BaseEnemy、按体型自适应添加血条。\n\n" +
                                  "数量较多，可能需要十几秒到一分钟。是否继续？",
                        MonsterCatalog.Count),
                    "开始导入", "取消"))
            {
                return;
            }

            EditorUtil.Report report = new EditorUtil.Report();
            BuildAllInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[怪物导入] 结果：\n" + report.Text);
            EditorUtility.DisplayDialog("导入全部怪物",
                string.Format("{0}\n\n错误 {1} · 警告 {2}\n\n详见 Console。",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成",
                    report.Errors, report.Warnings), "好");
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static void BuildAllInternal(EditorUtil.Report report)
        {
            report.Head(string.Format("导入全部怪物 → {0}/（共 {1} 个）",
                OutputDir, MonsterCatalog.Count));

            // 血条贴图是前置依赖，缺了就没必要逐个跑
            Sprite barBg = AssetDatabase.LoadAssetAtPath<Sprite>(
                EditorUtil.GeneratedArtDir + "/HP_Bar_Bg.png");
            Sprite barFill = AssetDatabase.LoadAssetAtPath<Sprite>(
                EditorUtil.GeneratedArtDir + "/HP_Bar_Fill.png");
            if (barBg == null || barFill == null)
            {
                report.Error("找不到血条贴图（HP_Bar_Bg / HP_Bar_Fill）。" +
                             "请先执行「1. 生成占位美术」");
                return;
            }

            EditorUtil.EnsureFolder(OutputDir);

            int built = 0;
            int noPhysics = 0;
            int failed = 0;
            int headOk = 0;
            int missingScripts = 0;
            float barMinY = float.MaxValue;
            float barMaxY = float.MinValue;
            float minW = float.MaxValue;
            float maxW = 0f;

            for (int i = 0; i < MonsterCatalog.Count; i++)
            {
                string src = MonsterCatalog.SourcePaths[i];
                string dst = MonsterCatalog.PrefabPath(i);
                GameObject source = AssetDatabase.LoadAssetAtPath<GameObject>(src);
                if (source == null)
                {
                    failed++;
                    report.Error(string.Format("源预制体不存在：{0}", src));
                    continue;
                }

                Bounds bounds;
                GameObject clone = Object.Instantiate(source);
                clone.name = System.IO.Path.GetFileNameWithoutExtension(dst);
                try
                {
                    int removed = PhysicsComponentCleaner.StripPhysics(clone);
                    if (removed == 0)
                    {
                        noPhysics++;
                    }

                    // 清掉"缺失脚本"：美术包原本带一个接收动画事件的脚本，
                    // 但它从来没进过这个项目 → 预制体上留着一条 Missing 引用，
                    // 每次实例化都会刷 "The referenced script (Unknown) on this Behaviour is missing!"
                    //（这正是我们补 MonsterAnimEventReceiver 的原因）
                    int missing = UnityEditor.GameObjectUtility.RemoveMonoBehavioursWithMissingScript(clone);
                    if (missing > 0)
                    {
                        missingScripts += missing;
                    }

                    if (clone.GetComponent<BaseEnemy>() == null)
                    {
                        clone.AddComponent<BaseEnemy>();
                    }

                    float barWorldY = AttachHpBar(clone, barBg, barFill);
                    if (barWorldY > -1000f)
                    {
                        if (barWorldY < barMinY) barMinY = barWorldY;
                        if (barWorldY > barMaxY) barMaxY = barWorldY;
                    }
                    if (AttachAnimEventReceiver(clone, MonsterCatalog.AtlasPaths[i]))
                    {
                        headOk++;
                    }
                    MeasureBodyBounds(clone, out bounds);

                    AssetDatabase.DeleteAsset(dst);
                    GameObject saved = PrefabUtility.SaveAsPrefabAsset(clone, dst);
                    if (saved == null)
                    {
                        failed++;
                        report.Error("保存失败：" + dst);
                        continue;
                    }
                    built++;

                    // 记录世界宽度，用于最后给出"要不要调 scale"的量化建议
                    Vector3 sc = clone.transform.localScale;
                    float w = bounds.size.x * Mathf.Abs(sc.x);
                    if (w > 0.0001f)
                    {
                        minW = Mathf.Min(minW, w);
                        maxW = Mathf.Max(maxW, w);
                    }
                }
                finally
                {
                    // 与 Instantiate 严格配对，避免预览场景泄漏对象
                    Object.DestroyImmediate(clone);
                }
            }

            report.Ok(string.Format("成功生成 {0} 个战斗预制体", built));
            if (failed > 0)
            {
                report.Error(string.Format("{0} 个失败（见上方明细）", failed));
            }
            if (noPhysics > 0)
            {
                report.Warn(string.Format("{0} 个源预制体上没有物理组件（若美术包更新后加回了 Collider，这里会提示）",
                    noPhysics));
            }
            if (built > 0 && maxW > 0f)
            {
            report.Ok(string.Format("实测显示宽度范围：{0:F2} ~ {1:F2} 世界单位（格子 1.0）",
                minW, maxW));
            if (barMaxY > float.MinValue)
            {
                report.Ok(string.Format(
                    "血条世界高度范围：{0:F2} ~ {1:F2}（应与各怪物的体型上限接近；\n" +
                    "  若某个怪的血条明显偏高/偏低，把怪名发我，我针对它的预制体结构单独看）",
                    barMinY, barMaxY));
            }
                report.Ok("体型差异来自美术（每个 prefab 自带缩放），所以相对大小不用手动调；" +
                          "若整体偏大/偏小，改 EnemyData.xlsx 的 scale 列");
            }
            report.Ok(string.Format(
                "{0}/{1} 个怪物的动画事件接收者已挂好并预填了头部贴图" +
                "（美术包的 Attack/Death 动画靠它切换 正常/愤怒/死亡 头，缺了会刷 " +
                "\"has no receiver\" 警告）", headOk, built));
            if (missingScripts > 0)
            {
                report.Ok(string.Format(
                    "已清除 {0} 个缺失脚本引用（美术包自带的动画事件脚本没进项目，\n" +
                    "  留着会每次实例化都刷 \"The referenced script (Unknown) is missing!\"）",
                    missingScripts));
            }
            report.Ok("下一步：执行「8a. 打 AssetBundle 标记」，让这些怪物按家族进入 enemy_<家族> 资源包");
        }

        // ------------------------------------------------------------------
        // 血条
        // ------------------------------------------------------------------

        /// <summary>
        /// 加血条。结构固定为 HpBar → Bg / Fill（BaseEnemy 按名字查找）。
        ///
        /// 位置与宽度按**实测渲染包围盒**推算，并用 InverseTransformPoint
        /// 把世界坐标换算回根节点本地（正确处理 66 个怪预制体根节点自带的位移、
        /// 以及全部 119 个的非均匀缩放）。
        /// 返回值：血条的世界 Y（用于报告里核对是否离谱）；失败返回 float.MinValue。
        /// </summary>
        private static float AttachHpBar(GameObject root, Sprite barBg, Sprite barFill)
        {
            Transform old = root.transform.Find("HpBar");
            if (old != null)
            {
                Object.DestroyImmediate(old.gameObject);
            }

            // 用"身体包围盒"而不是"全部渲染器包围盒"：
            // 部分美术预制体带未激活部件或远处的装饰节点，会把包围盒撑大，
            // 血条就被顶到离怪物很远的地方（这是实际反馈到的问题）
            Bounds b;
            bool hasBounds = MeasureBodyBounds(root, out b);
            Vector3 sc = root.transform.localScale;
            float sx = Mathf.Max(0.0001f, Mathf.Abs(sc.x));
            float sy = Mathf.Max(0.0001f, Mathf.Abs(sc.y));
            // 注意：sx/sy 只在没有包围盒时做兜底用；正常路径走 InverseTransformPoint

            // 【统一用世界尺寸思考，再换算回根节点本地】
            // 血条世界宽 = 怪物世界宽 × 比例；顶部 = 包围盒顶 + 怪物高 × 比例。
            //
            // 【换算必须用 InverseTransformPoint，不能"除以根缩放"】
            // 实测 119 个怪物预制体里：
            //   · 66 个的根节点 **localPosition 不为 0**（美术摆放时留了偏移）
            //   · 119 个全是 **非均匀缩放**（x/y 不相等）
            // 直接 `bounds.max.y / rootScaleY` 会**漏掉根节点自身的位移**，
            // 于是这 66 个怪的血条整体偏移一大截 —— 这正是
            // "大多数怪正常、少数怪（尤其某几个家族）偏得特别厉害"的原因。
            // InverseTransformPoint 会一次性正确处理 位移 + 缩放 + 旋转。
            Transform rt = root.transform;
            float worldW = hasBounds ? b.size.x : 1f;
            float worldH = hasBounds ? b.size.y : 1f;
            float barWorldW = Mathf.Clamp(worldW * BarWidthRatio, BarMinWorldWidth, BarMaxWorldWidth);
            float barWorldTop = (hasBounds ? b.max.y : 1f) + worldH * BarTopMarginRatio;

            // 位置：把"血条顶部"这个世界点换算到根节点本地空间
            // （必须用 InverseTransformPoint，理由见上）
            float topLocal = rt.InverseTransformPoint(
                new Vector3(b.center.x, barWorldTop, b.center.z)).y;

            // 尺寸：直接用根缩放把"期望的世界尺寸"换算成本地缩放
            //   渲染世界宽 = localScale.x × 根sx × 精灵原生宽(1.0)
            //   渲染世界高 = localScale.y × 根sy × 精灵原生高(0.2)
            // 宽度随怪物体型按比例；高度固定成一个薄条，所有怪物观感一致
            // （之前高度跟随宽度，大怪的血条高得像一块板，视觉上很突兀）
            float barLocalW = barWorldW / sx;
            float barLocalH = BarWorldHeight / (sy * 0.2f);

            GameObject bar = new GameObject("HpBar");
            bar.transform.SetParent(root.transform, false);
            bar.transform.localPosition = new Vector3(0f, topLocal, 0f);
            // 宽/高分开定标：宽度随怪物体型，高度固定为薄条
            // （Bg/Fill 保持在 1，这样 BaseEnemy 里的 _hpBarWidth 就是精灵原生宽度 1.0，
            //   左对齐计算最简单；血条的镜像补偿也只作用于 X）
            bar.transform.localScale = new Vector3(barLocalW, barLocalH, 1f);

            GameObject bgGo = new GameObject("Bg");
            bgGo.transform.SetParent(bar.transform, false);
            SpriteRenderer bgSr = bgGo.AddComponent<SpriteRenderer>();
            bgSr.sprite = barBg;
            bgSr.sortingOrder = BoardSorting.Overlay;
            bgSr.color = new Color(1f, 1f, 1f, 0.9f);

            GameObject fillGo = new GameObject("Fill");
            fillGo.transform.SetParent(bar.transform, false);
            SpriteRenderer fillSr = fillGo.AddComponent<SpriteRenderer>();
            fillSr.sprite = barFill;
            fillSr.sortingOrder = BoardSorting.Overlay + 1;
            fillSr.color = HpFillColor;

            // 返回血条的世界 Y，供调用方统计（报告里用来核对有没有离谱的偏移）
            return bar.transform.position.y;
        }

        /// <summary>
        /// 测"给血条定位用"的身体包围盒。
        ///
        /// 【为什么不能直接用全部 Renderer】实测发现部分怪物的血条位置明显偏高/偏斜，
        /// 原因是这些预制体里带**未激活**的部件（例如未启用的武器/特效），
        /// 或者位置很远的装饰节点；它们会把包围盒撑大。
        /// 所以只统计：**激活中**（includeInactive=false）+ **renderer.enabled** +
        /// 名字不像装饰（shadow/ground/fx/effect/glow/hit）的渲染器。
        /// </summary>
        private static bool MeasureBodyBounds(GameObject go, out Bounds bounds)
        {
            bounds = new Bounds(Vector3.zero, Vector3.zero);
            Renderer[] rs = go.GetComponentsInChildren<Renderer>(false);
            bool has = false;
            for (int i = 0; i < rs.Length; i++)
            {
                Renderer r = rs[i];
                if (r == null || !r.enabled)
                {
                    continue;
                }
                if (IsDecorativeRenderer(r.gameObject.name))
                {
                    continue;
                }
                if (!has)
                {
                    bounds = r.bounds;
                    has = true;
                }
                else
                {
                    bounds.Encapsulate(r.bounds);
                }
            }
            return has;
        }

        /// <summary>名字像装饰/特效/阴影的渲染器（不参与血条定位）</summary>
        private static bool IsDecorativeRenderer(string name)
        {
            if (string.IsNullOrEmpty(name))
            {
                return false;
            }
            string n = name.ToLowerInvariant();
            return n.Contains("shadow") || n.Contains("ground") || n.Contains("fx")
                || n.Contains("effect") || n.Contains("glow") || n.Contains("hit");
        }


        // ------------------------------------------------------------------
        // 动画事件接收者
        // ------------------------------------------------------------------

        /// <summary>
        /// 挂上动画事件接收者，并预填三个头部贴图。
        ///
        /// 【为什么必须挂】美术包的 Attack/Death 动画里内置了 `SetHead(int)` / `Event(string)`
        /// 的 AnimationEvent，但包里没有提供接收脚本，运行时 Console 会刷
        /// "AnimationEvent 'SetHead' … has no receiver!"。
        ///
        /// 【必须挂在 Animator 所在的 GameObject】Unity 把 AnimationEvent 发给
        /// 播放动画的那个 Animator 所属的 GameObject，挂错了收不到。
        /// </summary>
        private static bool AttachAnimEventReceiver(GameObject root, string atlasPath)
        {
            Animator anim = root.GetComponentInChildren<Animator>(true);
            GameObject host = anim != null ? anim.gameObject : root;

            MonsterAnimEventReceiver recv = host.GetComponent<MonsterAnimEventReceiver>();
            if (recv == null)
            {
                recv = host.AddComponent<MonsterAnimEventReceiver>();
            }

            recv.HeadRenderer = FindHeadRenderer(root);
            recv.HeadSprites = ResolveHeadSprites(atlasPath);
            return recv.HeadSprites != null && recv.HeadRenderer != null;
        }

        /// <summary>找名字含 "Head" 的渲染器（各家族节点名可能有差异，所以按名字模糊匹配）</summary>
        private static SpriteRenderer FindHeadRenderer(GameObject root)
        {
            SpriteRenderer[] rs = root.GetComponentsInChildren<SpriteRenderer>(true);
            for (int i = 0; i < rs.Length; i++)
            {
                if (rs[i] != null &&
                    rs[i].name.IndexOf("head", System.StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    return rs[i];
                }
            }
            return null;
        }

        /// <summary>
        /// 从图集里解析三个头部精灵。
        ///
        /// 【为什么必须在编辑期做】运行期拿到一个 Sprite 之后无法反查同一图集里的兄弟精灵
        ///（Sprite 不暴露这个信息），所以这里用 AssetDatabase 枚举图集全部子资产，
        /// 按名字取出来预填到组件上。
        ///
        /// 命名回退链覆盖实测到的几种美术包差异（118/120 图集有 Head 系命名）：
        ///   正常  HeadNormal → Head      → HeadAngry → HeadAttack
        ///   愤怒  HeadAngry  → HeadAttack→ HeadNormal→ Head
        ///   死亡  HeadDead   → HeadNormal→ Head
        /// </summary>
        private static Sprite[] ResolveHeadSprites(string atlasPath)
        {
            if (string.IsNullOrEmpty(atlasPath))
            {
                return null;
            }
            Object[] all = AssetDatabase.LoadAllAssetsAtPath(atlasPath);
            if (all == null || all.Length == 0)
            {
                return null;
            }

            System.Collections.Generic.Dictionary<string, Sprite> byName =
                new System.Collections.Generic.Dictionary<string, Sprite>(all.Length);
            for (int i = 0; i < all.Length; i++)
            {
                Sprite s = all[i] as Sprite;
                if (s != null && !byName.ContainsKey(s.name))
                {
                    byName[s.name] = s;
                }
            }
            if (byName.Count == 0)
            {
                return null;
            }

            string[][] chains =
            {
                new[] { "HeadNormal", "Head", "HeadAngry", "HeadAttack" },
                new[] { "HeadAngry", "HeadAttack", "HeadNormal", "Head" },
                new[] { "HeadDead", "HeadNormal", "Head" },
            };

            Sprite[] result = new Sprite[chains.Length];
            int found = 0;
            for (int i = 0; i < chains.Length; i++)
            {
                for (int k = 0; k < chains[i].Length; k++)
                {
                    Sprite s;
                    if (byName.TryGetValue(chains[i][k], out s))
                    {
                        result[i] = s;
                        found++;
                        break;
                    }
                }
            }
            return found > 0 ? result : null;
        }
    }
}
