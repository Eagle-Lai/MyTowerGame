# -*- coding: utf-8 -*-
"""
生成 SelectView / PauseView / SettingView 三个 UI prefab（M3）。

【为什么要自己生成，而不是让用户在 Unity 里点一下】
  UIPrefabBuilder 已经能生成它们，但那需要一次编辑器交互。M3 的目标是"全部内容交付"，
  所以这里把同一套结构**离线产出**，让用户开 Unity 就能直接 Play。

【为什么是"克隆模板"而不是从零写 YAML】
  Unity 的 prefab 序列化有大量易错细节（CanvasRenderer 的字段、Text 的 m_FontData、
  Image 的 m_Type/m_PreserveAspect…）。少一个字段未必报错，但行为可能不对。
  这里的做法是：**全部节点都从 TowerInfoView.prefab 里已存在的、由 Unity 自己写出的
  文档克隆**，只改 id / 名字 / 坐标 / 文本 / 颜色。这样序列化格式一定是对的。

【与 UIPrefabBuilder 的关系】
  两者产出同一套结构（同一批节点名、同一套坐标）。UIPrefabBuilder 是"源"，
  本脚本是它在无 Unity 环境下的等价实现。节点名若有改动，两边都要改。
"""
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = "D:/FreedomTower_1"
UI = os.path.join(ROOT, "Assets/Prefabs/UI")
TEMPLATE = os.path.join(UI, "TowerInfoView.prefab")

# 各界面脚本的 guid（由同名 .cs.meta 提供）
SCRIPT_GUID = {
    "SelectView": "6552693babe951ea4b0a618f8ca9e553",
    "PauseView": "d354127551b5a7b6f0f3567c207974c2",
    "SettingView": "cdb3a5c081ce8530d14d9cea415e6b36",
}

ANCHOR_MID_CENTER = 4

with open(TEMPLATE, "r", encoding="utf-8") as f:
    RAW = f.read().replace("\r\n", "\n")
HEAD = RAW[:RAW.index("--- !u!1 ")]
DOCS = ["--- " + d for d in re.split(r"^--- ", RAW, flags=re.M)[1:]]


def doc_id(d):
    return re.match(r"--- !u!(\d+) &(\d+)", d).group(2)


def doc_cls(d):
    return re.match(r"--- !u!(\d+) &(\d+)", d).group(1)


def find_go(name):
    # 用正则按行匹配，而不是拼 "\nm_Name: X\n" 子串 ——
    # 后者会被"文档首尾是否带换行"这种分块细节影响，非常脆。
    pat = re.compile(r"^\s*m_Name: " + re.escape(name) + r"\s*$", re.M)
    for d in DOCS:
        if doc_cls(d) == "1" and pat.search(d):
            return d
    raise KeyError("找不到模板 GameObject: " + name)


def build_group(go_doc):
    gid = doc_id(go_doc)
    comps = re.findall(r"- component: \{fileID: (\d+)\}", go_doc)
    rt = None
    others = []
    for d in DOCS:
        if doc_id(d) in comps:
            if doc_cls(d) == "224":
                rt = d
            else:
                others.append(d)
    return {"go": go_doc, "rt": rt, "others": others}


USED = set(int(doc_id(d)) for d in DOCS)


def new_id():
    while True:
        v = random.randint(10 ** 16, 9 * 10 ** 18)
        if v not in USED:
            USED.add(v)
            return str(v)


def esc(s):
    """Unity 的 YAML 字符串转义：非 ASCII 一律写成 \\uXXXX（Unity 自己就是这么写的）。"""
    out = []
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif 32 <= o < 127:
            out.append(ch)
        else:
            out.append("\\u%04X" % o)
    return "".join(out)


def clone(group, name, active=True):
    mapping = {}
    for d in [group["go"], group["rt"]] + group["others"]:
        mapping[doc_id(d)] = new_id()
    out = {}
    for key, d in [("go", group["go"]), ("rt", group["rt"])] + [("c%d" % i, x) for i, x in enumerate(group["others"])]:
        body = d
        for old, nid in mapping.items():
            body = re.sub(r"&" + old + r"\b", "&" + nid, body)
            body = body.replace("{fileID: " + old + "}", "{fileID: " + nid + "}")
        out[key] = body
    out["_ids"] = mapping
    out["go"] = re.sub(r"m_Name: .*", "m_Name: " + name, out["go"], count=1)
    if not active:
        out["go"] = re.sub(r"m_IsActive: 1", "m_IsActive: 0", out["go"])
    return out


def set_rect(node, anchor=(0.5, 0.5), pos=(0, 0), size=(100, 100), pivot=None):
    if pivot is None:
        pivot = anchor
    rt = node["rt"]
    rt = re.sub(r"m_AnchorMin: \{[^}]*\}", "m_AnchorMin: {x: %s, y: %s}" % (anchor[0], anchor[1]), rt)
    rt = re.sub(r"m_AnchorMax: \{[^}]*\}", "m_AnchorMax: {x: %s, y: %s}" % (anchor[0], anchor[1]), rt)
    rt = re.sub(r"m_AnchoredPosition: \{[^}]*\}", "m_AnchoredPosition: {x: %s, y: %s}" % (pos[0], pos[1]), rt)
    rt = re.sub(r"m_SizeDelta: \{[^}]*\}", "m_SizeDelta: {x: %s, y: %s}" % (size[0], size[1]), rt)
    rt = re.sub(r"m_Pivot: \{[^}]*\}", "m_Pivot: {x: %s, y: %s}" % (pivot[0], pivot[1]), rt)
    node["rt"] = rt


def set_stretch(node):
    rt = node["rt"]
    rt = re.sub(r"m_AnchorMin: \{[^}]*\}", "m_AnchorMin: {x: 0, y: 0}", rt)
    rt = re.sub(r"m_AnchorMax: \{[^}]*\}", "m_AnchorMax: {x: 1, y: 1}", rt)
    rt = re.sub(r"m_AnchoredPosition: \{[^}]*\}", "m_AnchoredPosition: {x: 0, y: 0}", rt)
    rt = re.sub(r"m_SizeDelta: \{[^}]*\}", "m_SizeDelta: {x: 0, y: 0}", rt)
    rt = re.sub(r"m_Pivot: \{[^}]*\}", "m_Pivot: {x: 0.5, y: 0.5}", rt)
    node["rt"] = rt


def set_text(node, text, font_size=None, align=ANCHOR_MID_CENTER, wrap=True):
    for k in list(node.keys()):
        if not k.startswith("c"):
            continue
        b = node[k]
        if "m_FontData:" not in b:
            continue
        # 【必须用 lambda】替换串里含 \uXXXX（非 ASCII 的 YAML 转义），
        # 直接当替换串传进去会被 re 当成转义序列解析并报 "bad escape \u"。
        repl = 'm_Text: "%s"' % esc(text)
        b = re.sub(r"m_Text: .*", lambda m: repl, b, count=1)
        if font_size is not None:
            b = re.sub(r"m_FontSize: \d+", "m_FontSize: %d" % font_size, b, count=1)
        b = re.sub(r"m_Alignment: \d+", "m_Alignment: %d" % align, b, count=1)
        b = re.sub(r"m_HorizontalOverflow: \d+", "m_HorizontalOverflow: 0" if wrap else "m_HorizontalOverflow: 1", b, count=1)
        b = re.sub(r"m_VerticalOverflow: \d+", "m_VerticalOverflow: 1", b, count=1)
        node[k] = b


def set_image_color(node, color):
    for k in list(node.keys()):
        if not k.startswith("c"):
            continue
        b = node[k]
        if "m_Sprite:" in b and "m_Color:" in b:
            b = re.sub(r"m_Color: \{[^}]*\}",
                       "m_Color: {r: %s, g: %s, b: %s, a: %s}" % color, b, count=1)
            node[k] = b


def set_script(node, guid):
    for k in list(node.keys()):
        if not k.startswith("c"):
            continue
        b = node[k]
        if "m_Script:" in b:
            b = re.sub(r"m_Script: \{[^}]*\}",
                       "m_Script: {fileID: 11500000, guid: %s, type: 3}" % guid, b, count=1)
            node[k] = b


T_IMAGE = build_group(find_go("Panel"))
T_TEXT = build_group(find_go("Title"))
T_BUTTON = build_group(find_go("UpgradeBtn"))


def find_label_of(btn_rt_id):
    """按钮的 Label 是它的子节点（m_Father 指向按钮的 RectTransform）。"""
    for d in DOCS:
        if doc_cls(d) == "224" and ("m_Father: {fileID: %s}" % btn_rt_id) in d:
            gid = re.search(r"m_GameObject: \{fileID: (\d+)\}", d).group(1)
            for g in DOCS:
                if doc_cls(g) == "1" and doc_id(g) == gid:
                    return build_group(g)
    return None


LABEL_T = find_label_of(doc_id(T_BUTTON["rt"]))


def make_text(name, text, size, pos, font_size, anchor=(0.5, 0.5), align=ANCHOR_MID_CENTER, wrap=True):
    n = clone(T_TEXT, name)
    set_rect(n, anchor=anchor, pos=pos, size=size)
    set_text(n, text, font_size, align, wrap)
    return n


def make_button(name, label, size, pos, anchor=(0.5, 0.5)):
    b = clone(T_BUTTON, name)
    set_rect(b, anchor=anchor, pos=pos, size=size)
    l = clone(LABEL_T, "Label")
    set_rect(l, anchor=(0.5, 0.5), pos=(0, 0), size=size)
    set_text(l, label, 32)
    b["_children"] = [l]
    return b


def make_image(name, size, pos, anchor=(0.5, 0.5), stretch=False, color=None):
    n = clone(T_IMAGE, name)
    if stretch:
        set_stretch(n)
    else:
        set_rect(n, anchor=anchor, pos=pos, size=size)
    if color:
        set_image_color(n, color)
    return n


def make_container(name, size, pos, anchor=(0.5, 0.5)):
    """纯容器：只要 GameObject + RectTransform（不要 CanvasRenderer/Image）。"""
    n = clone(T_IMAGE, name)
    # 去掉除 go/rt 之外的所有组件，并同步 GameObject 的 m_Component
    ids_to_drop = [doc_id(n[k]) for k in list(n.keys()) if k.startswith("c")]
    for k in list(n.keys()):
        if k.startswith("c"):
            del n[k]
    for i in ids_to_drop:
        n["go"] = re.sub(r"\n  - component: \{fileID: " + i + r"\}", "", n["go"])
    set_rect(n, anchor=anchor, pos=pos, size=size)
    return n


def emit(prefab_name, script_guid, panel_size, build_children):
    root_go = find_go("TowerInfoView")
    root = clone(build_group(root_go), prefab_name)
    set_stretch(root)
    set_script(root, script_guid)

    bg = make_image("Bg", (0, 0), (0, 0), stretch=True, color=("0", "0", "0", "0.55"))
    panel = make_image("Panel", panel_size, (0, 0), color=("0.12", "0.16", "0.24", "0.96"))
    children = build_children(panel_size)
    panel["_children"] = children
    root["_children"] = [bg, panel]

    # 组装：先收集全部节点，再统一分配父子关系
    order = []
    def walk(n, parent_rt):
        n["_parent_rt"] = parent_rt
        order.append(n)
        for c in n.get("_children", []):
            walk(c, doc_id(n["rt"]))
    walk(root, "0")

    # 处理子孙的 m_Father 与父的 m_Children
    for n in order:
        rt = n["rt"]
        rt = re.sub(r"m_Father: \{fileID: \d+\}", "m_Father: {fileID: %s}" % n["_parent_rt"], rt)
        kids = n.get("_children", [])
        # 【两种写法都要处理】Unity 对空子节点写 "m_Children: []"（行内），
        # 非空则写成
        #     m_Children:
        #     - {fileID: 123}
        # 只匹配行内那种会把非空列表原样留下 —— 表现就是"引用了模板里的旧 id"。
        rt = rt.replace("m_Children: []", "m_Children:")
        if kids:
            repl = "".join("\n  - {fileID: %s}" % doc_id(c["rt"]) for c in kids)
        else:
            repl = " []"
        rt = re.sub(r"m_Children:(?:\n  - \{fileID: \d+\})*", lambda m: "m_Children:" + repl, rt, count=1)
        n["rt"] = rt

    body = HEAD
    for n in order:
        for k in ["go", "rt"] + sorted([x for x in n.keys() if x.startswith("c")]):
            body += n[k]
    if not body.endswith("\n"):
        body += "\n"

    path = os.path.join(UI, prefab_name + ".prefab")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    return path, body


def select_children(panel_size):
    pw = panel_size[0]
    lst = make_container("List", (1040, 400), (0, -130), anchor=(0.5, 1))
    tpl = make_button("LevelButtonTemplate", "关卡", (240, 96), (0, 0), anchor=(0, 1))
    tpl["go"] = re.sub(r"m_IsActive: 1", "m_IsActive: 0", tpl["go"])
    lst["_children"] = [tpl]
    return [
        make_text("Title", "选择关卡", (pw - 60, 56), (0, -36), 38, anchor=(0.5, 1)),
        make_text("Summary", "已通关 0/8　★ 0/24", (1000, 44), (0, -92), 32, anchor=(0.5, 1)),
        lst,
        make_button("CloseBtn", "返回", (320, 72), (0, -270)),
    ]


def pause_children(panel_size):
    return [
        make_text("Title", "暂停", (panel_size[0] - 60, 56), (0, -36), 38, anchor=(0.5, 1)),
        make_button("ResumeBtn", "继续", (320, 72), (0, 60)),
        make_button("RestartBtn", "重新开始本关", (320, 72), (0, -30)),
        make_button("SettingsBtn", "设置", (320, 72), (0, -120)),
        make_button("QuitBtn", "返回关卡选择", (320, 72), (0, -210)),
    ]


def setting_children(panel_size):
    return [
        make_text("Title", "设置", (panel_size[0] - 60, 56), (0, -36), 38, anchor=(0.5, 1)),
        make_text("VolumeText", "音量 80%", (520, 56), (0, 120), 38, wrap=False),
        make_button("VolDownBtn", "音量 −", (320, 72), (-170, 40)),
        make_button("VolUpBtn", "音量 ＋", (320, 72), (170, 40)),
        make_button("MuteBtn", "静音", (320, 72), (0, -50)),
        make_button("ResetBtn", "重置存档", (320, 72), (0, -140)),
        make_button("CloseBtn", "关闭", (320, 72), (0, -230)),
    ]


def validate(path, body):
    anchors = re.findall(r"^--- !u!\d+ &(\d+)", body, re.M)
    if len(anchors) != len(set(anchors)):
        return "存在重复锚点"
    aset = set(anchors)
    for line in body.split("\n"):
        if "guid:" in line:
            continue
        for ref in re.findall(r"fileID: (\d+)", line):
            if ref != "0" and ref not in aset:
                return "未解析的内部引用 %s   <- %s" % (ref, line.strip()[:70])
    ns = re.findall(r"m_Name: (\S+)", body)
    return None


if __name__ == "__main__":
    specs = [
        ("SelectView", SCRIPT_GUID["SelectView"], (1120, 640), select_children),
        ("PauseView", SCRIPT_GUID["PauseView"], (560, 520), pause_children),
        ("SettingView", SCRIPT_GUID["SettingView"], (620, 600), setting_children),
    ]
    bad = 0
    for name, guid, size, fn in specs:
        p, body = emit(name, guid, size, fn)
        err = validate(p, body)
        docs = len(re.findall(r"^--- !u!", body, re.M))
        print("%-14s -> %s  (%d 文档)  %s" % (name, os.path.basename(p), docs, "OK" if not err else "✘ " + err))
        if err:
            bad += 1
    if bad:
        raise SystemExit("有 %d 个 prefab 校验未通过" % bad)
    print("全部通过")
