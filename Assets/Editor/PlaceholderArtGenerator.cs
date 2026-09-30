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

        // 配色（深色主题，与 Paper.png 背景同色系）
        private static readonly Color GroundFill = new Color(0.227f, 0.255f, 0.314f, 1f);
        private static readonly Color GroundBorder = new Color(1f, 1f, 1f, 0.10f);
        private static readonly Color BlockedFill = new Color(0.129f, 0.141f, 0.176f, 1f);
        private static readonly Color BlockedBorder = new Color(0f, 0f, 0f, 0.35f);
        private static readonly Color SpawnFill = new Color(0.180f, 0.353f, 0.204f, 1f);
        private static readonly Color SpawnBorder = new Color(0.36f, 0.85f, 0.42f, 0.85f);
        private static readonly Color EndFill = new Color(0.353f, 0.169f, 0.169f, 1f);
        private static readonly Color EndBorder = new Color(0.95f, 0.35f, 0.35f, 0.85f);

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
                Color white = new Color(1f, 1f, 1f, 0.95f);
                EditorUtil.FillTriangleUp(tex,
                    new Vector2(32f, 58f), new Vector2(14f, 9f), new Vector2(50f, 9f), white);
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
                EditorUtil.FillRing(tex, half, half, half - 2f, half - 8f, new Color(1f, 1f, 1f, 0.8f));
                EditorUtil.WriteSprite(Dir + "/Range_Ring.png", tex);
                report.Ok("Range_Ring.png (256×256 圆环，运行时按射程缩放)");
            }

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
    }
}
