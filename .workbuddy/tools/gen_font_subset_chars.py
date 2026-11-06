# -*- coding: utf-8 -*-
"""生成字体子集用的字符清单（只读采集 + 写清单文件）。

字符来源（并集）：
  1. Assets/ConfigJson/*.json 全部字符串（含多语言表 tblocalization）
  2. Assets/**/*.prefab|*.unity 里 TMP / UGUI 文本字段
  3. Assets/**/*.cs 里的字符串字面量（品牌文案、格式串等）
  4. ASCII 可打印区 + 常用中英标点 / 全角符号（运行时拼接用）
  5. GB2312 一级字（3755）+ Big5 一级字（5401）作为未来文案的安全余量

用法：
  python gen_font_subset_chars.py                 # 打印统计
  python gen_font_subset_chars.py --out chars.txt # 写出清单
"""
import os
import re
import sys
import json
import glob
import argparse
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSETS = os.path.join(ROOT, "Assets")

# 常驻符号：ASCII + 中英标点 + 全角 + 少量排版符号
BASE_SYMBOLS = (
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "　、。〃々〈〉《》「」『』【】〔〕〖〗〝〞–—‘’“”„…‧﹏"
    + "！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠［＼］＾＿｀"
    + "｛｜｝～￥·×÷±≤≥≠∞°′″℃→←↑↓↔■□●○◆◇▲▼★☆✓"
)


def _cjk_ranges(text):
    for ch in text:
        o = ord(ch)
        if (0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF
                or 0xF900 <= o <= 0xFAFF or 0x3000 <= o <= 0x303F
                or 0xFF00 <= o <= 0xFFEF):
            yield ch


def collect_config(chars):
    n = 0
    for p in glob.glob(os.path.join(ASSETS, "ConfigJson", "*.json")):
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue

        def walk(o):
            nonlocal n
            if isinstance(o, str):
                for ch in o:
                    chars[ch] += 1
                    n += 1
            elif isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(data)
    return n


def collect_text_assets(chars):
    n = 0
    pat = re.compile(r"^\s*m_text:\s*(.*)$", re.M)
    for ext in ("*.prefab", "*.unity"):
        for p in glob.glob(os.path.join(ASSETS, "**", ext), recursive=True):
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in pat.finditer(t):
                for ch in m.group(1):
                    chars[ch] += 1
                    n += 1
    return n


def collect_code(chars):
    n = 0
    lit = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
    for p in glob.glob(os.path.join(ASSETS, "**", "*.cs"), recursive=True):
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in lit.finditer(t):
            s = m.group(1)
            if not any(_cjk_ranges(s)) and not any(ord(c) > 0x7F for c in s):
                continue
            for ch in s:
                chars[ch] += 1
                n += 1
    return n


def gb2312_level1():
    out = []
    for b1 in range(0xB0, 0xD8):
        for b2 in range(0xA1, 0xFF):
            try:
                out.append(bytes([b1, b2]).decode("gb2312"))
            except UnicodeDecodeError:
                pass
    return "".join(out)


def big5_level1():
    out = []
    for b1 in range(0xA4, 0xC7):
        for b2 in list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF)):
            try:
                out.append(bytes([b1, b2]).decode("big5"))
            except UnicodeDecodeError:
                pass
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    chars = collections.Counter()
    a = collect_config(chars)
    b = collect_text_assets(chars)
    c = collect_code(chars)
    real = set(chars)

    base = set(BASE_SYMBOLS)
    gb = set(gb2312_level1())
    b5 = set(big5_level1())
    final = real | base | gb | b5
    final = {ch for ch in final if ch >= " " and ch != "\x7f"}

    print("来源统计：配置 %d 字次 / 文本资产 %d 字次 / 代码字面量 %d 字次" % (a, b, c))
    print("实际文本唯一字符：%d（其中汉字 %d）" % (
        len(real), len([ch for ch in real if "\u4e00" <= ch <= "\u9fff"])))
    print("安全余量：ASCII+符号 %d / GB2312一级 %d / Big5一级 %d" % (len(base), len(gb), len(b5)))
    print("并集去重后：%d 字符" % len(final))

    missing_in_gb = sorted(ch for ch in real if ch not in final)
    if missing_in_gb:
        print("警告：有字符被过滤：", missing_in_gb[:20])

    if args.out:
        ordered = "".join(sorted(final))
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(ordered)
        print("已写出：%s（%d 字符）" % (args.out, len(ordered)))


if __name__ == "__main__":
    main()
