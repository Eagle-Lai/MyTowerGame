using System.Collections.Generic;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Editor 工具共用方法。
    /// 集中放这里的原因：几个脚本都要"确保目录存在""取默认字体""设 Sprite 导入参数"，
    /// 复制多份迟早会分叉（尤其是 Sprite 导入参数，分叉会导致图集批次不一致）。
    /// </summary>
    public static class EditorUtil
    {
        /// <summary>所有程序生成的占位美术都放这里</summary>
        public const string GeneratedArtDir = "Assets/Art/Generated";

        /// <summary>M0 统一使用的每单位像素数（与现有美术一致）</summary>
        public const float DefaultPPU = 100f;

        // ------------------------------------------------------------------
        // 目录
        // ------------------------------------------------------------------

        /// <summary>确保资源目录存在（会递归创建父级）</summary>
        public static void EnsureFolder(string assetFolder)
        {
            if (string.IsNullOrEmpty(assetFolder) || AssetDatabase.IsValidFolder(assetFolder))
            {
                return;
            }
            string[] parts = assetFolder.Split('/');
            string cur = parts[0];   // "Assets"
            for (int i = 1; i < parts.Length; i++)
            {
                string next = cur + "/" + parts[i];
                if (!AssetDatabase.IsValidFolder(next))
                {
                    AssetDatabase.CreateFolder(cur, parts[i]);
                }
                cur = next;
            }
        }

        /// <summary>确保某个文件所在的目录存在</summary>
        public static void EnsureFolderOfFile(string assetFilePath)
        {
            int idx = assetFilePath.LastIndexOf('/');
            if (idx > 0)
            {
                EnsureFolder(assetFilePath.Substring(0, idx));
            }
        }

        // ------------------------------------------------------------------
        // 生成器安全护栏（★ 重要）
        // ------------------------------------------------------------------

        /// <summary>
        /// 生成器的"可安全重建"判定。
        ///
        /// 【为什么需要它】本工程的 Editor 生成器一律是「DeleteAsset + 重建」，
        /// 与"人在编辑器里手工调 prefab"天然互斥 —— 跑一次向导就抹掉手工成果
        /// （真实案例：HudView 手工加的三颗塔按钮被生成器删掉）。
        ///
        /// 约定：**只允许生成器管理"它自己产出的那套节点"**。
        /// 若在 prefab 里发现生成器预期之外的一级子节点，说明有人手工加过东西，
        /// 此时**必须中止并报错**，而不是静默删除。
        /// </summary>
        /// <param name="prefabPath">预制体路径</param>
        /// <param name="expectedChildren">生成器预期会产出的直接子节点名集合</param>
        /// <param name="extra">发现的"额外节点"（逗号分隔）；无额外节点时为 null</param>
        /// <returns>true = 结构纯净，可安全重建；false = 有手工痕迹，应中止</returns>
        public static bool IsSafeToRebuild(string prefabPath, string[] expectedChildren, out string extra)
        {
            extra = null;
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                return true;    // 不存在 → 首次生成，安全
            }

            List<string> extras = new List<string>();
            Transform root = prefab.transform;
            for (int i = 0; i < root.childCount; i++)
            {
                string childName = root.GetChild(i).name;
                bool known = false;
                for (int j = 0; j < expectedChildren.Length; j++)
                {
                    if (childName == expectedChildren[j])
                    {
                        known = true;
                        break;
                    }
                }
                if (!known)
                {
                    extras.Add(childName);
                }
            }

            if (extras.Count > 0)
            {
                extra = string.Join("、", extras.ToArray());
                return false;
            }
            return true;
        }

        // ------------------------------------------------------------------
        // 字体（UGUI Text 必须要字体，2022 起 Arial.ttf 已不再是内置名）
        // ------------------------------------------------------------------

        private static Font _cachedFont;

        /// <summary>
        /// 取一个可用的内置字体。
        /// 【坑】Unity 2022 之前内置字体叫 "Arial.ttf"，2022 起改名为 "LegacyRuntime.ttf"，
        /// 用错名字会得到 null，UGUI Text 就不显示任何字。
        /// </summary>
        public static Font GetDefaultFont()
        {
            if (_cachedFont != null)
            {
                return _cachedFont;
            }
            _cachedFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (_cachedFont == null)
            {
                _cachedFont = Resources.GetBuiltinResource<Font>("Arial.ttf");
            }
            if (_cachedFont == null)
            {
                Debug.LogWarning("[EditorUtil] 找不到内置字体，UGUI 文本可能不显示。" +
                                 "请在场景里手动给 Text 组件指定字体。");
            }
            return _cachedFont;
        }

        // ------------------------------------------------------------------
        // 贴图生成
        // ------------------------------------------------------------------

        /// <summary>
        /// 把一张 Texture2D 写成 PNG 并设为 Sprite。
        /// 已存在则覆盖，保证工具可重复执行（幂等）。
        /// </summary>
        public static void WriteSprite(string assetPath, Texture2D tex, float ppu = DefaultPPU)
        {
            EnsureFolderOfFile(assetPath);
            byte[] png = tex.EncodeToPNG();
            Object.DestroyImmediate(tex);
            System.IO.File.WriteAllBytes(assetPath, png);
            AssetDatabase.ImportAsset(assetPath, ImportAssetOptions.ForceUpdate);
            ApplySpriteSettings(assetPath, ppu);
        }

        /// <summary>把一张贴图设为 Sprite（Single 模式、无压缩、不生成 mipmap）</summary>
        public static void ApplySpriteSettings(string assetPath, float ppu)
        {
            TextureImporter ti = AssetImporter.GetAtPath(assetPath) as TextureImporter;
            if (ti == null)
            {
                return;
            }
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.spritePixelsPerUnit = ppu;
            ti.filterMode = FilterMode.Bilinear;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.wrapMode = TextureWrapMode.Clamp;
            // 占位图是纯色/简单形状，压缩只会引入色块，直接不压缩
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            ti.SaveAndReimport();
        }

        /// <summary>新建一张全透明的贴图</summary>
        public static Texture2D NewTexture(int w, int h)
        {
            Texture2D tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            Color32[] px = new Color32[w * h];
            Color32 clear = new Color32(0, 0, 0, 0);
            for (int i = 0; i < px.Length; i++)
            {
                px[i] = clear;
            }
            tex.SetPixels32(px);
            return tex;
        }

        /// <summary>画一个带内描边的实心矩形（像素坐标，原点左下）</summary>
        public static void FillRect(Texture2D tex, int x, int y, int w, int h, Color fill, Color border, int borderWidth)
        {
            int texW = tex.width;
            int texH = tex.height;
            for (int iy = y; iy < y + h; iy++)
            {
                if (iy < 0 || iy >= texH)
                {
                    continue;
                }
                for (int ix = x; ix < x + w; ix++)
                {
                    if (ix < 0 || ix >= texW)
                    {
                        continue;
                    }
                    bool onBorder = borderWidth > 0 &&
                                    (ix < x + borderWidth || ix >= x + w - borderWidth ||
                                     iy < y + borderWidth || iy >= y + h - borderWidth);
                    tex.SetPixel(ix, iy, onBorder ? border : fill);
                }
            }
        }

        /// <summary>画一个抗锯齿的实心圆</summary>
        public static void FillCircle(Texture2D tex, float cx, float cy, float radius, Color color)
        {
            int texW = tex.width;
            int texH = tex.height;
            float aa = 1f;   // 1 像素的抗锯齿过渡带
            for (int iy = 0; iy < texH; iy++)
            {
                for (int ix = 0; ix < texW; ix++)
                {
                    float d = Mathf.Sqrt((ix + 0.5f - cx) * (ix + 0.5f - cx) + (iy + 0.5f - cy) * (iy + 0.5f - cy));
                    float a = Mathf.Clamp01((radius - d) / aa + 0.5f);
                    if (a <= 0f)
                    {
                        continue;
                    }
                    Color c = color;
                    c.a *= a;
                    tex.SetPixel(ix, iy, Blend(tex.GetPixel(ix, iy), c));
                }
            }
        }

        /// <summary>画一个朝上的抗锯齿实心三角形（用于路径箭头）</summary>
        public static void FillTriangleUp(Texture2D tex, Vector2 a, Vector2 b, Vector2 c, Color color)
        {
            int texW = tex.width;
            int texH = tex.height;
            float aa = 1f;
            for (int iy = 0; iy < texH; iy++)
            {
                for (int ix = 0; ix < texW; ix++)
                {
                    Vector2 p = new Vector2(ix + 0.5f, iy + 0.5f);
                    float d = EdgeDistance(p, a, b, c);
                    float alpha = Mathf.Clamp01(0.5f - d / aa);
                    if (alpha <= 0f)
                    {
                        continue;
                    }
                    Color col = color;
                    col.a *= alpha;
                    tex.SetPixel(ix, iy, Blend(tex.GetPixel(ix, iy), col));
                }
            }
        }

        /// <summary>点到三角形三条边的最小有向距离（负值表示在内部）</summary>
        private static float EdgeDistance(Vector2 p, Vector2 a, Vector2 b, Vector2 c)
        {
            float d1 = Cross(p, a, b);
            float d2 = Cross(p, b, c);
            float d3 = Cross(p, c, a);
            float max = Mathf.Max(d1, Mathf.Max(d2, d3));
            // 归一化到"像素距离"
            float scale = 1f / Mathf.Max(0.0001f, Mathf.Max(new float[]
            {
                (b - a).magnitude, (c - b).magnitude, (a - c).magnitude
            }));
            return max * scale;
        }

        private static float Cross(Vector2 p, Vector2 a, Vector2 b)
        {
            return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
        }

        private static Color Blend(Color dst, Color src)
        {
            float a = src.a + dst.a * (1f - src.a);
            if (a <= 0.0001f)
            {
                return new Color(0f, 0f, 0f, 0f);
            }
            Color r;
            r.r = (src.r * src.a + dst.r * dst.a * (1f - src.a)) / a;
            r.g = (src.g * src.a + dst.g * dst.a * (1f - src.a)) / a;
            r.b = (src.b * src.a + dst.b * dst.a * (1f - src.a)) / a;
            r.a = a;
            return r;
        }

        // ------------------------------------------------------------------
        // 结果收集（让向导脚本能汇总一份报告给用户看）
        // ------------------------------------------------------------------

        public class Report
        {
            private readonly StringBuilder _sb = new StringBuilder();
            public int Errors { get; private set; }
            public int Warnings { get; private set; }

            public void Head(string title)
            {
                _sb.AppendLine("── " + title + " ──");
            }

            public void Ok(string msg)
            {
                _sb.AppendLine("  ✔ " + msg);
            }

            public void Warn(string msg)
            {
                _sb.AppendLine("  ! " + msg);
                Warnings++;
            }

            public void Error(string msg)
            {
                _sb.AppendLine("  ✘ " + msg);
                Errors++;
            }

            public string Text { get { return _sb.ToString(); } }
        }

        /// <summary>取一组预制体在原点实例化后的渲染包围盒（用于核对怪物/塔的实际显示尺寸）</summary>
        public static bool TryMeasureBounds(GameObject prefab, out Bounds bounds)
        {
            bounds = new Bounds(Vector3.zero, Vector3.zero);
            if (prefab == null)
            {
                return false;
            }
            GameObject inst = Object.Instantiate(prefab);
            inst.transform.position = Vector3.zero;
            Renderer[] rs = inst.GetComponentsInChildren<Renderer>(true);
            bool has = false;
            for (int i = 0; i < rs.Length; i++)
            {
                if (rs[i] == null)
                {
                    continue;
                }
                if (!has)
                {
                    bounds = rs[i].bounds;
                    has = true;
                }
                else
                {
                    bounds.Encapsulate(rs[i].bounds);
                }
            }
            Object.DestroyImmediate(inst);
            return has;
        }
    }
}
