# -*- coding: utf-8 -*-
"""校验子集字体：字形覆盖、字体名、关键度量是否与原件一致。

用法：python verify_font_subset.py <原字体> <子集字体> <字符清单>
"""
import sys
from fontTools.ttLib import TTFont


def face_info(path):
    f = TTFont(path, lazy=True)
    head = f["head"]
    hhea = f["hhea"]
    os2 = f["OS/2"] if "OS/2" in f else None
    name = f["name"]
    fam = ""
    ps = ""
    for rec in name.names:
        try:
            s = rec.toUnicode()
        except Exception:
            continue
        if rec.nameID == 1 and not fam:
            fam = s
        if rec.nameID == 6 and not ps:
            ps = s
    return {
        "unitsPerEm": head.unitsPerEm,
        "ascent": hhea.ascent,
        "descent": hhea.descent,
        "family": fam,
        "postscript": ps,
        "typoAscender": getattr(os2, "sTypoAscender", None) if os2 else None,
        "capHeight": getattr(os2, "sCapHeight", None) if os2 else None,
        "numGlyphs": f["maxp"].numGlyphs,
    }


def main():
    src, sub, chars_path = sys.argv[1], sys.argv[2], sys.argv[3]
    text = open(chars_path, encoding="utf-8").read()

    a = face_info(src)
    b = face_info(sub)
    print("原件 %s" % src)
    for k, v in a.items():
        print("   %-14s %s" % (k, v))
    print("子集 %s" % sub)
    for k, v in b.items():
        print("   %-14s %s" % (k, v))

    inv = TTFont(sub, lazy=True)
    cmap = inv.getBestCmap()
    missing = sorted(set(ch for ch in text if ch.strip() and ord(ch) not in cmap))
    print("\n清单字符 %d，子集覆盖 %d，缺失 %d" % (
        len(set(text)), len(set(text) & set(chr(c) for c in cmap)), len(missing)))
    if missing:
        print("缺失字符：", "".join(missing[:80]))
        sys.exit(1)

    same = (a["unitsPerEm"] == b["unitsPerEm"] and a["ascent"] == b["ascent"]
            and a["descent"] == b["descent"])
    print("关键度量一致：", same)
    if a["family"] != b["family"]:
        print("注意：family 名变化 %r -> %r" % (a["family"], b["family"]))


if __name__ == "__main__":
    main()
