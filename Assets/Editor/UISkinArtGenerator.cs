using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 深色科幻 UI 皮肤的程序化生成器。
    ///
    /// 【为什么程序生成而不是等美术】效果图（Docs/ui_mockups/）定义了完整的视觉令牌
    ///   （45° 切角面板 / 霓虹发光 / 靛青-金-红主题色）。本工程是 **Built-in 渲染管线，
    ///   没有后处理**，所以"发光"**必须烘进贴图**（外扩模糊 + 描边），不能靠 Bloom。
    ///   程序生成让配色/切角/发光半径可随效果图随时重跑，且与既有 PlaceholderArtGenerator 同一范式。
    ///
    /// 【九宫格是硬约束】面板/按钮都是 45° 切角 + 外发光，若用普通 Sprite 拉伸，四角会被
    ///   拉成巨大的斜楔。因此这些图必须按九宫格导入（spriteBorder），消费端 `Image.type = Sliced`。
    ///   约定：**border ≥ 切角 + 发光半径**，否则四角在拉伸时变形（本文件的尺寸表已满足）。
    ///
    /// 输出目录：Assets/_UIAssets/UI/   菜单：Tools ▸ 塔防 ▸ 高级（单步重建）▸ 生成 UI 皮肤美术
    /// </summary>
    public static class UISkinArtGenerator
    {
        public const string UiArtDir = "Assets/_UIAssets/UI";

        // ------------------------------------------------------------------
        // 深色科幻视觉令牌（GameDesign §6）
        // ------------------------------------------------------------------
        private static readonly Color PanelTop = Hex("2A3444");
        private static readonly Color PanelMid = Hex("1B2330");
        private static readonly Color PanelBot = Hex("222C3B");
        private static readonly Color StrokeC = Hex("3A4A63");
        private static readonly Color Cyan = Hex("35E0FF");
        private static readonly Color Gold = Hex("FFC94D");
        private static readonly Color Red = Hex("FF4D5E");
        private static readonly Color Fire = Hex("FF7A29");
        private static readonly Color Ice = Hex("7DE8FF");
        private static readonly Color Purple = Hex("7C5CFF");
        private static readonly Color Steel = Hex("9FB3C8");
        private static readonly Color SteelDark = Hex("5E7396");
        private static readonly Color BaseBlue = Hex("2E4A66");
        private static readonly Color DotLight = Hex("C9D6E8");
        private static readonly Color BoxDark = Hex("2A3138");
        private static readonly Color BoxRib = Hex("55627A");
        private static readonly Color SlateDeep = Hex("1C2532");

        // ------------------------------------------------------------------
        // 菜单入口
        // ------------------------------------------------------------------

        [MenuItem("Tools/塔防/高级（单步重建）/生成 UI 皮肤美术", false, 306)]
        public static void GenerateFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            GenerateAll(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[UISkin] UI 皮肤美术生成结果：\n" + report.Text);
            EditorUtility.DisplayDialog("生成 UI 皮肤美术",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        /// <summary>
        /// 无弹窗入口（供 Unity MCP / 批处理调用）。
        /// 【为什么单开一个】带 EditorUtility.DisplayDialog 的菜单会**阻塞编辑器**，
        /// 自动化调用会直接卡死；自动化一律走本入口，只往 Console 打日志。
        /// </summary>
        [MenuItem("Tools/塔防/自动化（无弹窗）/生成 UI 皮肤美术", false, 900)]
        public static void GenerateNoDialog()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            GenerateAll(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[UISkin] UI 皮肤美术生成结果：\n" + report.Text);
        }

        /// <summary>供一键向导/自动化调用（不弹窗）</summary>
        public static void GenerateAll(EditorUtil.Report report)
        {
            report.Head("生成深色科幻 UI 皮肤 → " + UiArtDir);
            EditorUtil.EnsureFolder(UiArtDir);

            // ---- 九宫格面板（64×64，切角 14 + 发光 6 = 20 ≤ border 22）----
            WriteCutWidget("UI_Panel_Cyan", 64, 14f, 6f, Cyan, true, StrokeC, 2f, 1.2f, 22f, report, "面板（青）", 0.40f);
            WriteCutWidget("UI_Panel_Gold", 64, 14f, 6f, Gold, true, StrokeC, 2f, 1.2f, 22f, report, "面板（金·胜利）", 0.40f);
            WriteCutWidget("UI_Panel_Red", 64, 14f, 6f, Red, true, StrokeC, 2f, 1.2f, 22f, report, "面板（红·失败）", 0.40f);

            // ---- 九宫格按钮（48×48，切角 12 + 发光 5 = 17 ≤ border 17）----
            WriteCutWidget("UI_Btn_Primary", 48, 12f, 5f, Cyan, true, Cyan, 2f, 1.4f, 17f, report, "主按钮（青）", 0.90f);
            WriteCutWidget("UI_Btn_Secondary", 48, 12f, 3f, Cyan, true, StrokeC, 2f, 1.0f, 17f, report, "次按钮", 0.45f);

            // ---- 九宫格芯片（40×40，切角 8 + 发光 4 = 12 ≤ border 12）----
            WriteCutWidget("UI_Chip_Gold", 40, 8f, 4f, Gold, true, Gold, 1.5f, 1.1f, 12f, report, "金币芯片", 0.45f);
            WriteCutWidget("UI_Chip_HP", 40, 8f, 4f, Red, true, Red, 1.5f, 1.1f, 12f, report, "生命芯片", 0.45f);
            WriteCutWidget("UI_Chip_Neutral", 40, 8f, 4f, Cyan, true, StrokeC, 1.5f, 0.9f, 12f, report, "中性芯片", 0.40f);

            // ---- 提示条 / 塔按钮底板（48×48）----
            WriteCutWidget("UI_Tip_Bar", 48, 10f, 5f, Cyan, true, Cyan, 2f, 1.0f, 16f, report, "提示条", 0.60f);
            WriteCutWidget("UI_TowerBtn_Frame", 48, 10f, 3f, Cyan, true, StrokeC, 2f, 0.8f, 16f, report, "塔按钮底板", 0.35f);

            // ---- 非九宫格：塔图标 / 星 ----
            WriteTowerIcons(report);
            WriteStar("UI_Star_On", true, report);
            WriteStar("UI_Star_Off", false, report);

            AssetDatabase.SaveAssets();
        }

        // ------------------------------------------------------------------
        // 九宫格切角控件
        // ------------------------------------------------------------------

        /// <summary>
        /// 画一个"45° 切角 + 竖向渐变 + 外发光 + 内描边 + 顶边高光"的九宫格控件。
        /// inset 预留发光外扩空间；cut 是切角直角边长；border = inset + cut。
        /// </summary>
        private static void WriteCutWidget(string name, int size, float cut, float glowR,
            Color glowColor, bool gradient, Color stroke, float strokeW, float topHi, float border,
            EditorUtil.Report report, string desc, float glowStrength = 0.6f)
        {
            Texture2D tex = EditorUtil.NewTexture(size, size);
            float inset = Mathf.Max(1f, border - cut);
            float hw = size * 0.5f - inset;
            float hh = size * 0.5f - inset;

            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float dx = (x + 0.5f) - size * 0.5f;
                    float dy = (y + 0.5f) - size * 0.5f;
                    float sdf = CutRectSdf(dx, dy, hw, hh, cut);
                    float t = (y + 0.5f) / size;

                    // 1) 外发光（形状之外，向下衰减）
                    if (glowR > 0f && sdf > 0f && sdf <= glowR)
                    {
                        float g = 1f - sdf / glowR;
                        Color gc = glowColor;
                        gc.a *= g * g * glowStrength;
                        BlendAt(tex, x, y, gc);
                    }

                    // 2) 主体（渐变或纯色）+ 描边 + 顶边高光
                    float cov = Mathf.Clamp01(0.5f - sdf);
                    if (cov <= 0f)
                    {
                        continue;
                    }

                    Color fill = gradient ? PanelGradient(t) : PanelMid;
                    fill.a *= cov;
                    BlendAt(tex, x, y, fill);

                    if (strokeW > 0f)
                    {
                        float band = Mathf.Clamp01((sdf + strokeW) / strokeW);
                        if (band > 0f)
                        {
                            Color sc = stroke;
                            sc.a *= band * cov;
                            BlendAt(tex, x, y, sc);
                        }
                    }

                    if (topHi > 0f && t > 0.72f)
                    {
                        Color hc = Color.white;
                        hc.a = topHi * cov * ((t - 0.72f) / 0.28f);
                        BlendAt(tex, x, y, hc);
                    }
                }
            }

            EditorUtil.WriteSlicedSprite(UiArtDir + "/" + name + ".png", tex,
                new Vector4(border, border, border, border));
            report.Ok(name + ".png  (" + size + "×" + size + " 九宫格 border=" + border + ", " + desc + ")");
        }

        /// <summary>
        /// 45° 切角矩形（八边形）的有符号距离：<0 在内部，>0 在外部。
        /// 形状 = 四个半平面（矩形四边）+ 四个斜切半平面 |x|+|y| ≤ hw+hh-cut。斜向项除以 √2 得真实像素距离。
        /// </summary>
        private static float CutRectSdf(float dx, float dy, float hw, float hh, float cut)
        {
            float ax = Mathf.Abs(dx);
            float ay = Mathf.Abs(dy);
            float dAxis = Mathf.Max(ax - hw, ay - hh);
            float dDiag = (ax + ay - (hw + hh - cut)) * 0.70710678f;
            return Mathf.Max(dAxis, dDiag);
        }

        /// <summary>面板竖向渐变：底 #222C3B → 中 #1B2330 → 顶 #2A3444（t: 0=底, 1=顶）</summary>
        private static Color PanelGradient(float t)
        {
            if (t >= 0.5f)
            {
                return Color.Lerp(PanelMid, PanelTop, (t - 0.5f) * 2f);
            }
            return Color.Lerp(PanelBot, PanelMid, t * 2f);
        }

        // ------------------------------------------------------------------
        // 塔图标（96×96，非九宫格）
        // ------------------------------------------------------------------

        private static void WriteTowerIcons(EditorUtil.Report report)
        {
            WriteIcon("UI_TowerIcon_Normal", IconNormal, Cyan, report);
            WriteIcon("UI_TowerIcon_Power", IconPower, Fire, report);
            WriteIcon("UI_TowerIcon_Retard", IconRetard, Ice, report);
            WriteIcon("UI_TowerIcon_Pierce", IconPierce, Purple, report);
            WriteIcon("UI_TowerIcon_Laser", IconLaser, Purple, report);
        }

        private static void WriteIcon(string name, System.Action<Texture2D> draw, Color halo, EditorUtil.Report report)
        {
            const int S = 96;
            Texture2D tex = EditorUtil.NewTexture(S, S);
            // 统一底晕：让图标在深色按钮上"浮"起来
            SoftGlow(tex, S * 0.5f, S * 0.5f, S * 0.44f, halo, 0.16f);
            draw(tex);
            EditorUtil.WriteSprite(UiArtDir + "/" + name + ".png", tex);
            report.Ok(name + ".png  (" + S + "×" + S + " 塔图标)");
        }

        /// <summary>Normal：四联炮（圆形基座 + 十字炮管，炮管压在基座之上）</summary>
        private static void IconNormal(Texture2D tex)
        {
            const float cx = 48f, cy = 46f;
            FillDisc(tex, cx, cy, 26f, BaseBlue, SteelDark, 3f);
            FillRotRect(tex, cx, cy, 26f, 5.5f, 45f, Steel, StrokeC, 1.5f);
            FillRotRect(tex, cx, cy, 26f, 5.5f, 135f, Steel, StrokeC, 1.5f);
            FillDisc(tex, cx, cy, 8f, DotLight, DotLight, 0f);
        }

        /// <summary>Power：火焰发射箱（箱体 + 顶rib + 向下火苗）</summary>
        private static void IconPower(Texture2D tex)
        {
            SoftGlow(tex, 48f, 20f, 22f, Fire, 0.55f);
            FillConvexPoly(tex, new[]
            {
                new Vector2(34f, 38f), new Vector2(62f, 38f), new Vector2(48f, 10f)
            }, Fire, Fire, 0f);
            FillBoxRect(tex, 18f, 44f, 78f, 90f, BoxDark, SteelDark, 3f);
            FillBoxRect(tex, 40f, 90f, 50f, 100f, BoxRib, BoxRib, 0f);
            FillBoxRect(tex, 56f, 90f, 66f, 100f, BoxRib, BoxRib, 0f);
            for (int i = 0; i < 3; i++)
            {
                FillBoxRect(tex, 24f, 54f + i * 9f, 72f, 55f + i * 9f, BoxRib, BoxRib, 0f);
            }
        }

        /// <summary>Retard：水晶塔（梯形基座 + 菱形冰晶）</summary>
        private static void IconRetard(Texture2D tex)
        {
            FillEllipse(tex, 48f, 22f, 30f, 9f, new Color(Ice.r, Ice.g, Ice.b, 0.22f));
            FillConvexPoly(tex, new[]
            {
                new Vector2(34f, 34f), new Vector2(62f, 34f), new Vector2(52f, 8f), new Vector2(44f, 8f)
            }, SlateDeep, SteelDark, 3f);
            SoftGlow(tex, 48f, 62f, 30f, Ice, 0.5f);
            FillConvexPoly(tex, new[]
            {
                new Vector2(48f, 86f), new Vector2(62f, 60f), new Vector2(48f, 34f), new Vector2(34f, 60f)
            }, Ice, Color.white, 2f);
            DrawLine(tex, 48f, 36f, 48f, 84f, new Color(1f, 1f, 1f, 0.5f), 1.5f);
            DrawLine(tex, 36f, 60f, 60f, 60f, new Color(1f, 1f, 1f, 0.5f), 1.5f);
        }

        /// <summary>Pierce：钻头穿透（圆基座 + 竖直炮管 + 钻尖）</summary>
        private static void IconPierce(Texture2D tex)
        {
            FillDisc(tex, 48f, 24f, 24f, BaseBlue, SteelDark, 3f);
            FillBoxRect(tex, 42f, 40f, 54f, 66f, Steel, StrokeC, 1.5f);
            FillConvexPoly(tex, new[]
            {
                new Vector2(36f, 64f), new Vector2(60f, 64f), new Vector2(48f, 90f)
            }, Steel, Purple, 2f);
            DrawLine(tex, 36f, 72f, 60f, 72f, Purple, 2f);
            DrawLine(tex, 40f, 80f, 56f, 80f, Purple, 1.5f);
            FillDisc(tex, 48f, 24f, 7f, DotLight, DotLight, 0f);
        }

        /// <summary>Laser：透镜聚焦塔（梯形座 + 同心环）</summary>
        private static void IconLaser(Texture2D tex)
        {
            FillConvexPoly(tex, new[]
            {
                new Vector2(30f, 8f), new Vector2(66f, 8f), new Vector2(56f, 46f), new Vector2(40f, 46f)
            }, BoxDark, SteelDark, 3f);
            SoftGlow(tex, 48f, 66f, 26f, Purple, 0.55f);
            DrawRing(tex, 48f, 66f, 16f, 3f, Purple);
            DrawRing(tex, 48f, 66f, 9f, 2f, new Color(Purple.r, Purple.g, Purple.b, 0.7f));
            FillDisc(tex, 48f, 66f, 3.5f, Color.white, Color.white, 0f);
            DrawLine(tex, 40f, 46f, 30f, 32f, new Color(Purple.r, Purple.g, Purple.b, 0.6f), 2f);
            DrawLine(tex, 56f, 46f, 66f, 32f, new Color(Purple.r, Purple.g, Purple.b, 0.6f), 2f);
        }

        // ------------------------------------------------------------------
        // 星（48×48）
        // ------------------------------------------------------------------

        private static void WriteStar(string name, bool on, EditorUtil.Report report)
        {
            const int S = 48;
            Texture2D tex = EditorUtil.NewTexture(S, S);
            float cx = S * 0.5f, cy = S * 0.5f;
            float outer = 21f, inner = 8.5f;

            if (on)
            {
                SoftGlow(tex, cx, cy, 22f, Gold, 0.45f);
            }
            Color starStroke = on ? Hex("B96E1B") : StrokeC;
            for (int y = 0; y < S; y++)
            {
                for (int x = 0; x < S; x++)
                {
                    float dx = (x + 0.5f) - cx;
                    float dy = (y + 0.5f) - cy;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    float ang = Mathf.Atan2(dy, dx) * Mathf.Rad2Deg;
                    float rr = StarRadius(ang, outer, inner);
                    float sd = d - rr;
                    float cov = Mathf.Clamp01(0.5f - sd);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = on ? Gold : SlateDeep;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                    // 描边
                    float band = Mathf.Clamp01((sd + 2f) / 2f);
                    if (band > 0f)
                    {
                        Color sc = starStroke;
                        sc.a *= band * cov;
                        BlendAt(tex, x, y, sc);
                    }
                }
            }
            EditorUtil.WriteSprite(UiArtDir + "/" + name + ".png", tex);
            report.Ok(name + ".png  (" + S + "×" + S + (on ? " 亮星" : " 暗星") + ")");
        }

        /// <summary>五角星在角度 ang 处的半径（尖角朝上）</summary>
        private static float StarRadius(float angDeg, float outer, float inner)
        {
            float a = Mathf.Repeat(angDeg + 90f, 72f) / 72f;   // 0..1
            float tri = 1f - Mathf.Abs(2f * a - 1f);           // 0→1→0
            return inner + (outer - inner) * tri;
        }

        // ------------------------------------------------------------------
        // 基础绘制原语（全部作用在 Texture2D，坐标原点左下）
        // ------------------------------------------------------------------

        private static void BlendAt(Texture2D tex, int x, int y, Color src)
        {
            if (src.a <= 0f || x < 0 || y < 0 || x >= tex.width || y >= tex.height)
            {
                return;
            }
            Color dst = tex.GetPixel(x, y);
            float a = src.a + dst.a * (1f - src.a);
            if (a <= 0.0001f)
            {
                tex.SetPixel(x, y, new Color(0f, 0f, 0f, 0f));
                return;
            }
            Color r = new Color(
                (src.r * src.a + dst.r * dst.a * (1f - src.a)) / a,
                (src.g * src.a + dst.g * dst.a * (1f - src.a)) / a,
                (src.b * src.a + dst.b * dst.a * (1f - src.a)) / a,
                a);
            tex.SetPixel(x, y, r);
        }

        /// <summary>径向柔光（中心最亮，向外平方衰减）</summary>
        private static void SoftGlow(Texture2D tex, float cx, float cy, float radius, Color color, float strength)
        {
            int W = tex.width, H = tex.height;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float dx = x + 0.5f - cx;
                    float dy = y + 0.5f - cy;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    if (d >= radius)
                    {
                        continue;
                    }
                    float g = 1f - d / radius;
                    Color c = color;
                    c.a *= g * g * strength;
                    BlendAt(tex, x, y, c);
                }
            }
        }

        private static void FillDisc(Texture2D tex, float cx, float cy, float radius, Color fill, Color stroke, float strokeW)
        {
            int W = tex.width, H = tex.height;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float dx = x + 0.5f - cx;
                    float dy = y + 0.5f - cy;
                    float sd = Mathf.Sqrt(dx * dx + dy * dy) - radius;
                    float cov = Mathf.Clamp01(0.5f - sd);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = fill;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                    if (strokeW > 0f)
                    {
                        float band = Mathf.Clamp01((sd + strokeW) / strokeW);
                        if (band > 0f)
                        {
                            Color sc = stroke;
                            sc.a *= band * cov;
                            BlendAt(tex, x, y, sc);
                        }
                    }
                }
            }
        }

        private static void DrawRing(Texture2D tex, float cx, float cy, float radius, float width, Color color)
        {
            int W = tex.width, H = tex.height;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float dx = x + 0.5f - cx;
                    float dy = y + 0.5f - cy;
                    float sd = Mathf.Abs(Mathf.Sqrt(dx * dx + dy * dy) - radius) - width * 0.5f;
                    float cov = Mathf.Clamp01(0.5f - sd);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = color;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                }
            }
        }

        private static void FillEllipse(Texture2D tex, float cx, float cy, float rx, float ry, Color color)
        {
            int W = tex.width, H = tex.height;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float nx = (x + 0.5f - cx) / rx;
                    float ny = (y + 0.5f - cy) / ry;
                    float q = Mathf.Sqrt(nx * nx + ny * ny);
                    float cov = Mathf.Clamp01((1f - q) * Mathf.Min(rx, ry) + 0.5f);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = color;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                }
            }
        }

        /// <summary>轴对齐矩形（x0,y0)-(x1,y1)，含可选内描边</summary>
        private static void FillBoxRect(Texture2D tex, float x0, float y0, float x1, float y1,
            Color fill, Color stroke, float strokeW)
        {
            int W = tex.width, H = tex.height;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float px = x + 0.5f, py = y + 0.5f;
                    float sd = Mathf.Max(Mathf.Max(x0 - px, px - x1), Mathf.Max(y0 - py, py - y1));
                    float cov = Mathf.Clamp01(0.5f - sd);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = fill;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                    if (strokeW > 0f)
                    {
                        float band = Mathf.Clamp01((sd + strokeW) / strokeW);
                        if (band > 0f)
                        {
                            Color sc = stroke;
                            sc.a *= band * cov;
                            BlendAt(tex, x, y, sc);
                        }
                    }
                }
            }
        }

        /// <summary>绕中心旋转的矩形（用于炮管）</summary>
        private static void FillRotRect(Texture2D tex, float cx, float cy, float halfLen, float halfThick,
            float angleDeg, Color fill, Color stroke, float strokeW)
        {
            int W = tex.width, H = tex.height;
            float rad = angleDeg * Mathf.Deg2Rad;
            float cos = Mathf.Cos(rad), sin = Mathf.Sin(rad);
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float dx = x + 0.5f - cx;
                    float dy = y + 0.5f - cy;
                    // 逆旋转到矩形局部坐标
                    float lx = dx * cos + dy * sin;
                    float ly = -dx * sin + dy * cos;
                    float sd = Mathf.Max(Mathf.Abs(lx) - halfLen, Mathf.Abs(ly) - halfThick);
                    float cov = Mathf.Clamp01(0.5f - sd);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = fill;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                    if (strokeW > 0f)
                    {
                        float band = Mathf.Clamp01((sd + strokeW) / strokeW);
                        if (band > 0f)
                        {
                            Color sc = stroke;
                            sc.a *= band * cov;
                            BlendAt(tex, x, y, sc);
                        }
                    }
                }
            }
        }

        /// <summary>
        /// 凸多边形填充（顶点顺序任意）。逐边算"归一化到像素距离"的有向距离：
        /// 全部同号 = 在内部，取最接近 0 的一条作为深度；符号不一致 = 在外部。
        /// 【为什么不用 EditorUtil.FillTriangleUp】那个函数把 max(cross) 当作外测距离，
        /// 与内部点的正号约定相反，实测画不出三角形 —— 这里用自洽的写法。
        /// </summary>
        private static void FillConvexPoly(Texture2D tex, Vector2[] pts, Color fill, Color stroke, float strokeW)
        {
            int n = pts.Length;
            if (n < 3)
            {
                return;
            }
            int W = tex.width, H = tex.height;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float px = x + 0.5f, py = y + 0.5f;
                    float dmin = float.MaxValue, dmax = float.MinValue;
                    for (int i = 0; i < n; i++)
                    {
                        Vector2 a = pts[i];
                        Vector2 b = pts[(i + 1) % n];
                        float ex = b.x - a.x, ey = b.y - a.y;
                        float elen = Mathf.Max(0.0001f, Mathf.Sqrt(ex * ex + ey * ey));
                        float cross = (ex * (py - a.y) - ey * (px - a.x)) / elen;
                        dmin = Mathf.Min(dmin, cross);
                        dmax = Mathf.Max(dmax, cross);
                    }
                    float sd = Mathf.Max(dmin, -dmax);   // >=0 内部
                    float cov = Mathf.Clamp01(sd + 0.5f);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = fill;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                    if (strokeW > 0f)
                    {
                        // 距离边缘 strokeW 以内画描边
                        float band = Mathf.Clamp01((strokeW - sd) / strokeW);
                        if (band > 0f)
                        {
                            Color sc = stroke;
                            sc.a *= band * cov;
                            BlendAt(tex, x, y, sc);
                        }
                    }
                }
            }
        }

        /// <summary>抗锯齿线段（带宽）</summary>
        private static void DrawLine(Texture2D tex, float x0, float y0, float x1, float y1, Color color, float width)
        {
            int W = tex.width, H = tex.height;
            float ex = x1 - x0, ey = y1 - y0;
            float len2 = Mathf.Max(0.0001f, ex * ex + ey * ey);
            float half = width * 0.5f;
            for (int y = 0; y < H; y++)
            {
                for (int x = 0; x < W; x++)
                {
                    float px = x + 0.5f - x0, py = y + 0.5f - y0;
                    float t = Mathf.Clamp01((px * ex + py * ey) / len2);
                    float qx = px - ex * t, qy = py - ey * t;
                    float d = Mathf.Sqrt(qx * qx + qy * qy);
                    float cov = Mathf.Clamp01(half - d + 0.5f);
                    if (cov <= 0f)
                    {
                        continue;
                    }
                    Color c = color;
                    c.a *= cov;
                    BlendAt(tex, x, y, c);
                }
            }
        }

        private static Color Hex(string hex)
        {
            Color c;
            if (ColorUtility.TryParseHtmlString("#" + hex, out c))
            {
                return c;
            }
            return Color.magenta;
        }
    }
}
