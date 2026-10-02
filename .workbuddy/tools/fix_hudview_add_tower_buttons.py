# -*- coding: utf-8 -*-
"""
一次性修复：给 Assets/Prefabs/UI/HudView.prefab 补上 Btn_Tower_Pierce / Btn_Tower_Laser。

【为什么要手改 prefab，而不是跑「生成 UI 预制体（全量重建）」】
  实测：手工版的三颗按钮把**塔身贴图直接挂在按钮自身的 Image 上**
  （Btn_Tower_Normal → turret_base_128，子节点再叠一张 turret_barrel_128，
   合起来就是完整的一座塔），而 UIPrefabBuilder.CreateTowerButton 的产法是
  "纯色底 + 图标子节点"，两者外观不同。
  跑全量重建会**改掉手工调好的观感**；而本次只想"补上缺的两颗"。
  所以：克隆 Btn_Tower_Normal 的整块结构（穿透/激光当前本就复用普通塔外观），
  只换名字、坐标与 fileID。

【顺带把 5 颗按钮重排成等距】HudView 建造栏的规范坐标是
  -548 / -274 / 0 / +274 / +548（间距 274，在 1920 参考宽度下居中），
  与 UIPrefabBuilder.TowerButtons 保持一致 —— 这样将来真要全量重建，
  位置也不会跳。原手工版是 3 颗时代的 -633/-359/-123。

【安全性】脚本自带三重校验：
  ① 所有 fileID 引用都能解析到已定义的锚点；
  ② 没有重复锚点；
  ③ 根节点的 m_Children 恰好包含 9 个子节点。
  任一条不过就不写文件。
"""
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

PREFAB = r"D:/FreedomTower_1/Assets/Prefabs/UI/HudView.prefab"

ROOT_RT = "4952505089378875455"           # HudView 根 RectTransform
NORMAL_GO = "3982924297004534815"         # Btn_Tower_Normal 的 GameObject（克隆模板）
GOLDTEXT_GO = "5598065035970295796"       # 模板块的结束边界

# 现有三颗按钮的 RectTransform → 新的 x
RESIZE = {
    "4961646577516388187": (-633, -548),   # Normal
    "1782706572363652907": (-359, -274),   # Power
    "4354259897685611015": (-123, 0),      # Retard
}

# 新增两颗：(节点名, x)
ADD = [("Btn_Tower_Pierce", 274), ("Btn_Tower_Laser", 548)]


def new_fid(used):
    while True:
        v = random.randint(10 ** 17, 9 * 10 ** 18)
        if v not in used:
            used.add(v)
            return str(v)


def main():
    with open(PREFAB, "r", encoding="utf-8", newline="") as f:
        raw = f.read()

    eol = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")

    # ---- 切出模板块（Btn_Tower_Normal 的 9 个文档）----
    a = text.index("--- !u!1 &" + NORMAL_GO)
    b = text.index("--- !u!1 &" + GOLDTEXT_GO)
    template = text[a:b]
    print("模板块长度: %d 字符, 文档数: %d"
          % (len(template), len(re.findall(r"^--- !u!", template, re.M))))

    # 模板里出现的全部 fileID（锚点）
    tpl_ids = re.findall(r"^--- !u!\d+ &(\d+)", template, re.M)
    print("模板锚点:", tpl_ids)

    used = set(int(x) for x in re.findall(r"^--- !u!\d+ &(\d+)", text, re.M))

    new_blocks = []
    new_root_children = []
    for name, x in ADD:
        mapping = {old: new_fid(used) for old in tpl_ids}
        blk = template
        for old, new in mapping.items():
            blk = blk.replace("&" + old, "&" + new)
            blk = blk.replace("{fileID: " + old + "}", "{fileID: " + new + "}")
        blk = blk.replace("m_Name: Btn_Tower_Normal", "m_Name: " + name)
        # 按钮 RectTransform 的 anchoredPosition（子节点那张是 0,0，靠 sizeDelta 区分不了，
        # 所以只在"m_Father 指向根节点"的那张上改）
        blk = blk.replace(
            "  m_Father: {fileID: %s}\n  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}\n"
            "  m_AnchorMin: {x: 0.5, y: 0.5}\n  m_AnchorMax: {x: 0.5, y: 0.5}\n"
            "  m_AnchoredPosition: {x: -633, y: -427}" % ROOT_RT,
            "  m_Father: {fileID: %s}\n  m_LocalEulerAnglesHint: {x: 0, y: 0, z: 0}\n"
            "  m_AnchorMin: {x: 0.5, y: 0.5}\n  m_AnchorMax: {x: 0.5, y: 0.5}\n"
            "  m_AnchoredPosition: {x: %d, y: -427}" % (ROOT_RT, x))
        new_blocks.append(blk)
        new_root_children.append("  - {fileID: %s}" % mapping[tpl_ids[1]])   # 索引 1 = RectTransform
        print("  %s → x=%d, 新锚点 %s" % (name, x, mapping[tpl_ids[1]]))

    # ---- 现有三颗按钮重排 ----
    for rt, (old_x, new_x) in RESIZE.items():
        pat = re.compile(
            r"(--- !u!224 &" + rt + r"\n(?:.*?\n)*?  m_AnchoredPosition: \{x: )"
            + str(old_x) + r"(, y: -427\})")
        text, n = pat.subn(lambda m: m.group(1) + str(new_x) + m.group(2), text, count=1)
        print("  重排 %s: %d → %d  (命中 %d 处)" % (rt, old_x, new_x, n))
        if n != 1:
            raise SystemExit("重排失败，已中止")

    # ---- 插入新块 + 更新根节点子列表 ----
    insert_at = text.index("--- !u!1 &" + GOLDTEXT_GO)
    text = text[:insert_at] + "".join(new_blocks) + text[insert_at:]

    m = re.search(r"(--- !u!224 &" + ROOT_RT + r"\n(?:.*?\n)*?  m_Children:\n)((?:  - \{fileID: \d+\}\n)+)", text)
    if not m:
        raise SystemExit("找不到根节点的 m_Children")
    text = text[:m.end(2)] + "".join(c + "\n" for c in new_root_children) + text[m.end(2):]

    # ---- 校验 ① ② ③ ----
    anchors = re.findall(r"^--- !u!\d+ &(\d+)", text, re.M)
    if len(anchors) != len(set(anchors)):
        raise SystemExit("校验失败：存在重复锚点")
    aset = set(anchors)
    missing = []
    for line in text.split("\n"):
        # 【要点】带 guid 的 fileID 指向**别的资源**（如 m_Script: 11500000、
        # m_Sprite: 21300000、内置默认材质 10102），本来就不该在本文件里有锚点。
        # 只校验"不带 guid 的裸 fileID 引用"，那才是必须解析到本文件锚点的内部引用。
        if "guid:" in line:
            continue
        for ref in re.findall(r"fileID: (\d+)", line):
            if ref != "0" and ref not in aset:
                missing.append((ref, line.strip()[:80]))
    if missing:
        for ref, line in missing[:10]:
            print("  未解析: %s   <- %s" % (ref, line))
        raise SystemExit("校验失败：存在未解析的内部引用")

    m2 = re.search(r"--- !u!224 &" + ROOT_RT + r"\n(?:.*?\n)*?  m_Children:\n((?:  - \{fileID: \d+\}\n)+)", text)
    kids = re.findall(r"fileID: (\d+)", m2.group(1))
    print("\n根节点子节点数: %d (期望 9)" % len(kids))
    if len(kids) != 9:
        raise SystemExit("校验失败：根节点子节点数不是 9")

    names = re.findall(r"m_Name: (Btn_Tower_\w+)", text)
    print("塔按钮节点:", sorted(set(names)))
    if len(set(names)) != 5:
        raise SystemExit("校验失败：塔按钮不是 5 个")

    with open(PREFAB, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace("\n", eol))
    print("\n已写出:", PREFAB)


if __name__ == "__main__":
    main()
