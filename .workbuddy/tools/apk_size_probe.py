# -*- coding: utf-8 -*-
"""只读：解析 APK 内置 YooAsset bundle 的内部构成，用于定位包体体积来源。
不做任何修改，仅输出统计。
"""
import os
import glob
import collections
import UnityPy

SA = r"E:\MyTowerGame\Assets\StreamingAssets\yoo\FreeTower"
OC = r"E:\MyTowerGame\Bundles\Android\FreeTower\OutputCache"


def name_map():
    m = {}
    for f in glob.glob(os.path.join(OC, "*.bundle")):
        m[os.path.getsize(f)] = os.path.basename(f)
    out = {}
    for f in glob.glob(os.path.join(SA, "*.bundle")):
        out[os.path.basename(f)] = m.get(os.path.getsize(f), os.path.basename(f))
    return out


def probe(path, logical):
    env = UnityPy.load(path)
    agg = collections.Counter()
    cnt = collections.Counter()
    fonts = []
    tex_bytes = 0
    tex_cnt = 0
    dims = collections.Counter()
    for o in env.objects:
        t = o.type.name
        try:
            raw = o.get_raw_data()
            n = len(raw) if raw else 0
        except Exception:
            n = 0
        agg[t] += n
        cnt[t] += 1
        if t == "Texture2D":
            tex_cnt += 1
            try:
                d = o.read()
                # 纹理像素数据量（m_CompleteImageSize），流式存储在 .resS 里
                cis = getattr(d, "m_CompleteImageSize", 0) or 0
                tex_bytes += cis
                dims[(getattr(d, "m_Width", 0), getattr(d, "m_Height", 0),
                      int(getattr(d, "m_TextureFormat", -1)))] += 1
            except Exception:
                pass
        if t in ("Font", "MonoBehaviour") and "TMP" in str(getattr(o.read(), "m_Name", "")):
            pass
        if t == "Font":
            try:
                d = o.read()
                fonts.append((len(d.m_FontData or b""), d.m_Name, n))
            except Exception:
                pass
    return {
        "logical": logical,
        "file_mb": os.path.getsize(path) / 1048576,
        "agg": agg,
        "cnt": cnt,
        "fonts": fonts,
        "tex_bytes": tex_bytes,
        "tex_cnt": tex_cnt,
        "dims": dims,
    }


def main():
    nm = name_map()
    rows = []
    for h, logical in sorted(nm.items()):
        rows.append(probe(os.path.join(SA, h), logical))

    total = sum(r["file_mb"] for r in rows)
    print("内置 bundle 合计 %.1f MB / %d 个\n" % (total, len(rows)))

    print("%-46s %7s %8s %8s  %s" % ("logical", "file MB", "tex MB", "anim MB", "top types"))
    for r in sorted(rows, key=lambda r: -r["file_mb"]):
        anim = r["agg"].get("AnimationClip", 0) / 1048576
        print("%-46s %7.1f %8.1f %8.1f  %s" % (
            r["logical"][:46], r["file_mb"], r["tex_bytes"] / 1048576, anim,
            ", ".join("%s%.1f" % (t, v / 1048576) for t, v in r["agg"].most_common(3)),
        ))

    print("\n=== Font 资产明细 ===")
    for r in rows:
        for size, name, raw in r["fonts"]:
            print("  %-46s font=%-28s 源字体数据 %.2f MB (对象 %.2f MB)" % (
                r["logical"], name, size / 1048576, raw / 1048576))

    print("\n=== 纹理尺寸分布（前 20 类） ===")
    alldims = collections.Counter()
    for r in rows:
        for k, v in r["dims"].items():
            alldims[k] += v
    for (w, h, fmt), c in alldims.most_common(20):
        print("  %5dx%-5d fmt=%-3d  %3d 张  RGBA32当量 %6.1f MB" % (
            w, h, fmt, c, w * h * 4 * c / 1048576))


if __name__ == "__main__":
    main()
