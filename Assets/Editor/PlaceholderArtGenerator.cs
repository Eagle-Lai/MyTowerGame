using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 程序化生成棋盘与战斗的占位美术（P0-4）。
    ///
    /// 为什么要程序生成而不是找美术要图：
    ///   1. 这些是"功能验证用"的图（格子、箭头、血条、子弹点），美术风格定了还要换
    ///   2. 让程序生成可以随格子尺寸 / 配色随时重跑，不占用美术排期
    ///   3. 关掉"美术没到位"这个最常见的阻塞项 —— 符合需求 5「功能缺失不应阻塞实现」
    ///
    /// 全部按 PPU=100 生成，与现有美术（塔/怪物）保持一致。
    /// 输出目录：Assets/Art/Generated/　逻辑名见 ResTable（Cell_Ground / Path_Arrow / ...）
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 高级（单步重建）▸ 生成占位美术
    /// </summary>
    public static class PlaceholderArtGenerator
    {
        private const string Dir = EditorUtil.GeneratedArtDir;

        // 配色：深色科幻令牌（GameDesign §6）—— 战场 #10141D / 格线 #1C2532 / 青 #35E0FF / 红 #FF4D5E
        private static readonly Color GroundFill = new Color(0.102f, 0.133f, 0.188f, 1f);
        private static readonly Color GroundBorder = new Color(1f, 1f, 1f, 0.06f);
        private static readonly Color BlockedFill = new Color(0.051f, 0.067f, 0.098f, 1f);
        private static readonly Color BlockedBorder = new Color(0f, 0f, 0f, 0.45f);
        private static readonly Color SpawnFill = new Color(0.063f, 0.188f, 0.227f, 1f);
        private static readonly Color SpawnBorder = new Color(0.208f, 0.878f, 1f, 0.85f);
        private static readonly Color EndFill = new Color(0.227f, 0.086f, 0.125f, 1f);
        private static readonly Color EndBorder = new Color(1f, 0.302f, 0.369f, 0.85f);
        private static readonly Color PathArrowColor = new Color(0.208f, 0.878f, 1f, 0.95f);
        private static readonly Color RangeRingColor = new Color(0.208f, 0.878f, 1f, 0.80f);

        [MenuItem("Tools/塔防/高级（单步重建）/生成占位美术", false, 300)]
        public static void Generate()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            GenerateInternal(report);
            AssetDatabase.Refresh();

            Debug.Log("[M0] 占位美术生成完成：\n" + report.Text);
            EditorUtility.DisplayDialog("生成占位美术",
                string.Format("完成，共输出到 {0}\n\n{1}", Dir, report.Text), "好");
        }

        /// <summary>
        /// 无弹窗入口（供 Unity MCP / 批处理调用）。
        /// 【为什么单开一个】带 EditorUtility.DisplayDialog 的菜单会**阻塞编辑器**，
        /// 自动化调用会直接卡死；自动化一律走本入口，只往 Console 打日志。
        /// </summary>
        [MenuItem("Tools/塔防/自动化（无弹窗）/生成占位美术", false, 901)]
        public static void GenerateNoDialog()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            GenerateInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[M0] 占位美术生成完成：\n" + report.Text);
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static void GenerateInternal(EditorUtil.Report report)
        {
            report.Head("生成占位美术 → " + Dir);
            EditorUtil.EnsureFolder(Dir);

            // ---- 棋盘格子（128px，带 3px 内描边，便于目视看清格线）----
            WriteTile(report, "Cell_Ground", GroundFill, GroundBorder);
            WriteTile(report, "Cell_Blocked", BlockedFill, BlockedBorder);
            WriteTile(report, "Cell_Spawn", SpawnFill, SpawnBorder);
            WriteTile(report, "Cell_End", EndFill, EndBorder);

            // ---- 路径箭头（朝上，运行时按角度 -90° 旋转）----
            {
                Texture2D tex = EditorUtil.NewTexture(64, 64);
                EditorUtil.FillTriangleUp(tex,
                    new Vector2(32f, 58f), new Vector2(14f, 9f), new Vector2(50f, 9f), PathArrowColor);
                EditorUtil.WriteSprite(Dir + "/Path_Arrow.png", tex);
                report.Ok("Path_Arrow.png  (64×64 朝上三角)");
            }

            // ---- 子弹点 ----
            {
                Texture2D tex = EditorUtil.NewTexture(24, 24);
                EditorUtil.FillCircle(tex, 12f, 12f, 9f, Color.white);
                EditorUtil.WriteSprite(Dir + "/Bullet_Dot.png", tex);
                report.Ok("Bullet_Dot.png  (24×24 圆点)");
            }

            // ---- 血条 ----
            // 100×20 px → PPU100 下原生 1.0 × 0.2 世界单位，
            // 血条 prefab 里把 scale 设成 0.6 即得 0.6 × 0.12 的条
            {
                Texture2D bg = EditorUtil.NewTexture(100, 20);
                EditorUtil.FillRect(bg, 0, 0, 100, 20,
                    new Color(0.06f, 0.06f, 0.08f, 0.85f), new Color(0f, 0f, 0f, 0.9f), 2);
                EditorUtil.WriteSprite(Dir + "/HP_Bar_Bg.png", bg);
                report.Ok("HP_Bar_Bg.png   (100×20 深底)");

                // Fill 用纯白，颜色交给 prefab 的 SpriteRenderer.color 决定
                // （这样以后要做"低血变红"只需改颜色，不用重新出图）
                Texture2D fill = EditorUtil.NewTexture(100, 20);
                EditorUtil.FillRect(fill, 0, 0, 100, 20, Color.white, Color.white, 0);
                EditorUtil.WriteSprite(Dir + "/HP_Bar_Fill.png", fill);
                report.Ok("HP_Bar_Fill.png (100×20 纯白，运行时着色)");
            }

            // ---- 射程提示圈 ----
            // 256×256、环宽 6px → PPU100 下原生 2.56 世界单位。
            // 运行时按"目标直径 / 原生直径"折算 localScale（与 CellView.Setup 同一套做法），
            // 所以以后换分辨率或换美术都不用改代码。
            {
                const int size = 256;
                Texture2D tex = EditorUtil.NewTexture(size, size);
                float half = size * 0.5f;
                EditorUtil.FillRing(tex, half, half, half - 2f, half - 8f, RangeRingColor);
                EditorUtil.WriteSprite(Dir + "/Range_Ring.png", tex);
                report.Ok("Range_Ring.png (256×256 圆环，运行时按射程缩放)");
            }

            // ---- 世界层背景（就地覆盖 Paper.png，见 GenerateBackground 注释）----
            GenerateBackground(report);

            AssetDatabase.SaveAssets();
        }

        private static void WriteTile(EditorUtil.Report report, string name, Color fill, Color border)
        {
            const int size = 128;
            Texture2D tex = EditorUtil.NewTexture(size, size);
            EditorUtil.FillRect(tex, 0, 0, size, size, fill, border, 3);
            EditorUtil.WriteSprite(Dir + "/" + name + ".png", tex);
            report.Ok(name + ".png  (" + size + "×" + size + ")");
        }

        // ------------------------------------------------------------------
        // 世界层背景（★ 就地覆盖 Paper.png，不改任何场景/配置）
        // ------------------------------------------------------------------

        /// <summary>
        /// 背景贴图路径。**刻意沿用原文件名 Paper.png**：
        /// 它已经被 `ResTable["Background"]` 与主场景的 Background 物件引用，
        /// 就地覆盖内容即可让两边同时生效 —— 换文件名反而要动 ResTable + 场景 + AB 打标三处。
        /// </summary>
        private const string BackgroundPath = "Assets/_UIAssets/Backgrounds/Paper.png";

        /// <summary>
        /// 生成深色科幻背景（替换掉与整体风格不符的"米色纸张"占位图）。
        ///
        /// 【为什么值得单独做一张】背景占满整个屏幕，它的色相决定了整个游戏的第一印象：
        ///   原本的米黄色纸张把"深色科幻"直接拉成了"手账风"，选关/战斗/结算全部界面都受影响。
        ///
        /// 【尺寸为什么是 1950×1300】与原图一致 ⇒ PPU=100 下仍是 19.5×13 世界单位，
        ///   背景物件在场景里的缩放（1.6）与 BackgroundParallax 的视差算法都不用改。
        ///
        /// 【固定随机种子】星点位置每次生成都相同 ⇒ 便于 diff 与复现（不会一跑一个样）。
        /// </summary>
        private static void GenerateBackground(EditorUtil.Report report)
        {
            const int W = 1950;
            const int H = 1300;

            // 深色科幻令牌（GameDesign §6）
            Color baseCol = new Color(0.063f, 0.078f, 0.114f, 1f);   // #10141D 战场底
            Color edgeCol = new Color(0.043f, 0.055f, 0.078f, 1f);   // #0B0E14 暗角
            Color gridCol = new Color(0.110f, 0.145f, 0.196f, 1f);   // #1C2532 格线
            Color cyanCol = new Color(0.208f, 0.878f, 1f, 1f);       // #35E0FF
            Color starCol = new Color(0.910f, 0.941f, 0.980f, 1f);   // #E8F0FA

            Color[] buf = new Color[W * H];
            float cx = (W - 1) * 0.5f;
            float cy = (H - 1) * 0.5f;

            // ① 底 + 径向暗角（中心亮、四角压暗，与界面暗角同一套观感）
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float dx = (x - cx) / cx;
                    float dy = (y - cy) / cy;
                    float r = Mathf.Clamp01(Mathf.Sqrt(dx * dx + dy * dy) / 1.10f);
                    buf[y * W + x] = Color.Lerp(baseCol, edgeCol, r * r);
                }
            }

            // ② 淡格线（130px ≈ 1.3 世界单位，纯装饰性纵深）
            const int step = 130;
            for (int x = 0; x < W; x += step)
            {
                for (int y = 0; y < H; y++)
                {
                    buf[y * W + x] = Color.Lerp(buf[y * W + x], gridCol, 0.35f);
                }
            }
            for (int y = 0; y < H; y += step)
            {
                for (int x = 0; x < W; x++)
                {
                    buf[y * W + x] = Color.Lerp(buf[y * W + x], gridCol, 0.35f);
                }
            }

            // ③ 中段一条极淡的青色辉光带（把视线往棋盘中心引）
            int bandY = Mathf.RoundToInt(H * 0.52f);
            int bandH = Mathf.Max(1, Mathf.RoundToInt(H * 0.10f));
            for (int y = bandY - bandH; y <= bandY + bandH; y++)
            {
                if (y < 0 || y >= H)
                {
                    continue;
                }
                float t = 1f - Mathf.Abs(y - bandY) / (float)bandH;
                float a = t * t * 0.06f;
                for (int x = 0; x < W; x++)
                {
                    buf[y * W + x] = Color.Lerp(buf[y * W + x], cyanCol, a);
                }
            }

            // ④ 星点（固定种子 → 结果可复现）
            System.Random rnd = new System.Random(20261008);
            for (int i = 0; i < 900; i++)
            {
                int sx = rnd.Next(W);
                int sy = rnd.Next(H);
                bool isCyan = rnd.NextDouble() < 0.25;
                float a = 0.10f + (float)rnd.NextDouble() * 0.30f;
                float rad = rnd.NextDouble() < 0.15 ? 1.6f : 0.8f;
                Dot(buf, W, H, sx, sy, rad, isCyan ? cyanCol : starCol, a);
            }

            Texture2D tex = EditorUtil.NewTexture(W, H);
            tex.SetPixels(buf);
            EditorUtil.WriteSprite(BackgroundPath, tex);
            report.Ok("Paper.png  (" + W + "×" + H + " 深色科幻背景：暗角 + 星点 + 淡格线)");
        }

        /// <summary>在像素缓冲上画一个软边圆点（星点用）。越界自动裁剪。</summary>
        private static void Dot(Color[] buf, int w, int h, float px, float py, float radius, Color col, float alpha)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt(px - radius - 1f));
            int x1 = Mathf.Min(w - 1, Mathf.CeilToInt(px + radius + 1f));
            int y0 = Mathf.Max(0, Mathf.FloorToInt(py - radius - 1f));
            int y1 = Mathf.Min(h - 1, Mathf.CeilToInt(py + radius + 1f));
            for (int y = y0; y <= y1; y++)
            {
                for (int x = x0; x <= x1; x++)
                {
                    float dx = x - px;
                    float dy = y - py;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = Mathf.Clamp01((radius - d) / Mathf.Max(0.0001f, radius)) * alpha;
                    if (a <= 0f)
                    {
                        continue;
                    }
                    buf[y * w + x] = Color.Lerp(buf[y * w + x], col, a);
                }
            }
        }
    }
}
