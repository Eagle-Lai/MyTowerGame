# -*- coding: utf-8 -*-
"""fix_svg_comments.py — 修正 SVG 中非法的 XML 注释
XML 规则：注释体不能含连续 `--`，也不能以 `-` 结尾。
把注释体里的 `--` 折成 `-`，去掉结尾的 `-`，并统一 `===== xxx =====` → `xxx`。
"""
import os
import re
import sys

SVG_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "Docs", "ui_mockups"))


def clean(body):
    b = body
    # 去掉纯装饰的 ==== / ---- 分隔
    b = re.sub(r"^\s*=+\s*", "", b)
    b = re.sub(r"\s*=+\s*$", "", b)
    b = re.sub(r"^\s*-+\s*", "", b)
    b = re.sub(r"\s*-+\s*$", "", b)
    # 注释体内部任何 `--` 折成一个 `-`
    while "--" in b:
        b = b.replace("--", "-")
    while b.endswith("-"):
        b = b[:-1]
    return b


def process(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    changed = [0]

    def repl(m):
        body = m.group(1)
        nb = clean(body)
        if nb != body:
            changed[0] += 1
        # 保留换行结构：按行清洗
        lines = body.split("\n")
        out = []
        for i, ln in enumerate(lines):
            c = ln
            if i == 0:
                c = re.sub(r"^\s*=+\s*", "", c)
            if i == len(lines) - 1:
                c = re.sub(r"\s*-+\s*$", "", c)
                c = re.sub(r"\s*=+\s*$", "", c)
            while "--" in c:
                c = c.replace("--", "-")
            out.append(c.rstrip())
        res = "\n".join(out)
        while res.endswith("-"):
            res = res[:-1]
        return "<!--" + res + " -->"

    new = re.sub(r"<!--(.*?)-->", repl, src, flags=re.S)
    if new != src:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        return changed[0]
    return 0


def main():
    args = sys.argv[1:]
    files = sorted(f for f in os.listdir(SVG_DIR) if f.endswith(".svg"))
    if args:
        files = [f for f in files if any(a in f for a in args)]
    n = 0
    for f in files:
        c = process(os.path.join(SVG_DIR, f))
        if c:
            print("fixed %-34s %d 处注释" % (f, c))
            n += c
    print("共修正 %d 处" % n)


if __name__ == "__main__":
    main()
