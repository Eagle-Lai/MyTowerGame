#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 节点契约校验：View 脚本里 `transform.Find("路径")` 引用的节点，
必须真的存在于 UIPrefabBuilder 生成的那棵 prefab 树里。

【为什么必须有这个检查】
  本工程的 UI 取值一律走 `transform.Find("Panel/Title")` 这种字符串路径，
  两边（.cs 与生成器）都写死了同一套名字，**中间没有任何映射层**。
  一旦名字写岔，运行时不会报错崩溃，只会打一句
  「[XXX] 缺少文本节点「Panel/Title」」然后整块 UI 空白 ——
  这种"能跑但看不见"的问题最难在联调时发现。

【做法】
  1. 从 UIPrefabBuilder.cs 里解析每个 Build<View> 方法：
     按父子关系还原出节点路径集合（CreateDialogShell 固定产 Bg / Panel / Panel/Title；
     CreatePanelButton 额外产 <Btn>/Label）。
  2. 从各 View 脚本里收集所有 Find("...") 字符串。
  3. 两边求差：View 引用了但生成器不产 → FAIL。

用法：
    python .workbuddy/tools/check_ui_contract.py
退出码：0 = 一致，1 = 有对不上的节点。
"""

import io
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(_HERE))
BUILDER = os.path.join(PROJ, 'Assets', 'Editor', 'UIPrefabBuilder.cs')
UI_DIR = os.path.join(PROJ, 'Assets', 'Scripts', 'UI')

# 只看这些视图（HudView 的塔按钮等已由 UIPrefabBuilder 自己的名单维护）
VIEWS = [
    'HudView', 'TipsView', 'TowerInfoView', 'SelectView',
    'PauseView', 'SettingView', 'LevelClearView',
]

# 生成器里"容器变量名 -> 路径前缀"（CreateDialogShell 的产出）
SHELL_VARS = {'root': '', 'panel': 'Panel', 'bg': 'Bg'}


def read(path):
    with io.open(path, encoding='utf-8-sig', errors='replace') as f:
        return f.read()


def strip_comments(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def builder_nodes(section, has_shell):
    """
    按**代码顺序**还原 Build<View> 方法产出的节点路径集合。

    支持三种建节点方式（生成器里都用到了）：
      1. CreateDialogShell(...)      → 固定产 Bg / Panel / Panel/Title（out panel）
      2. new GameObject("X") + X.transform.SetParent(Y.transform, false) → Y路径/X
      3. CreateText/CreateButton/CreatePanelButton(<容器>.transform, "X", ...)
         —— CreatePanelButton 额外产 X/Label
    没被 SetParent 过的那一个就是 prefab 根，路径为空。
    """
    nodes = set()
    varpath = {}
    if has_shell:
        # CreateDialogShell 的固定产出
        nodes.update(['Bg', 'Panel', 'Panel/Title'])
        varpath['root'] = ''
        varpath['panel'] = 'Panel'
        varpath['bg'] = 'Bg'

    events = []
    for m in re.finditer(r'([A-Za-z_]\w*)\s*=\s*new\s+GameObject\(\s*"([^"]+)"', section):
        events.append((m.start(), 0, ('decl', m.group(1), m.group(2))))
    for m in re.finditer(
            r'([A-Za-z_]\w*)\s*\.\s*transform\s*\.\s*SetParent\(\s*([A-Za-z_]\w*)\s*\.\s*transform\s*,',
            section):
        events.append((m.start(), 1, ('parent', m.group(1), m.group(2))))
    for m in re.finditer(
            r'(CreatePanelButton|CreateText|CreateButton)\(\s*([A-Za-z_]\w*)\s*\.\s*transform\s*,\s*"([^"]+)"',
            section):
        events.append((m.start(), 2, ('create', m.group(1), m.group(2), m.group(3))))
    events.sort(key=lambda x: (x[0], x[1]))

    # 先扫一遍：谁被 SetParent 过、谁没被 —— 没被 SetParent 的就是 prefab 根
    names = {}
    child_vars = set()
    for _, _, ev in events:
        if ev[0] == 'decl':
            names[ev[1]] = ev[2]
        elif ev[0] == 'parent':
            child_vars.add(ev[1])
    for var in names:
        if var not in child_vars:
            varpath[var] = ''          # ★ 必须在处理 create 事件**之前**定好，
                                       #   否则 CreateText(root.transform, ...) 取到 None 被整批跳过
                                       #   （HudView / TipsView 就因此被误报为"一个节点都不产"）

    for _, _, ev in events:
        if ev[0] == 'decl':
            continue
        if ev[0] == 'parent':
            child, parent = ev[1], ev[2]
            p = varpath.get(parent)
            n = names.get(child)
            if n is None:
                continue
            path = (p + '/' + n) if p else n
            varpath[child] = path
            nodes.add(path)            # 容器本身也是节点（如 Panel / Panel/List）
        else:
            _, fn, var, name = ev
            p = varpath.get(var)
            if p is None:
                continue               # 容器来自别处（运行期克隆），本工具不判定
            path = (p + '/' + name) if p else name
            nodes.add(path)
            if fn == 'CreatePanelButton':
                nodes.add(path + '/Label')

    return nodes, varpath


def view_paths(path):
    """收集 View 脚本里所有 transform.Find("...") 的字符串。"""
    src = strip_comments(read(path))
    found = set()
    for m in re.finditer(r'Find(?:Text|Button|Rect)?\(\s*"([^"]+)"', src):
        found.add(m.group(1))
    for m in re.finditer(r'\.\s*Find\(\s*"([^"]+)"', src):
        found.add(m.group(1))
    return found


def main():
    if not os.path.isfile(BUILDER):
        print('找不到生成器：' + BUILDER)
        return 1
    src = strip_comments(read(BUILDER))

    problems = []
    checked = 0
    for view in VIEWS:
        # 切出 Build<View> 方法体：从 'private static void BuildX(' 到下一个同级方法
        marker = 'Build' + view.replace('View', '') if view != 'HudView' else 'BuildHud'
        # 生成器里的方法名与视图名并不总是一一对应，这里按"方法体里是否出现该视图类"来定位
        m = re.search(r'private static void (Build[A-Za-z]*)\s*\([^)]*\)\s*\{', src)
        bodies = []
        for mm in re.finditer(r'private static void (Build[A-Za-z]*)\s*\([^)]*\)\s*\{', src):
            depth = 0
            i = mm.end() - 1
            while i < len(src):
                if src[i] == '{':
                    depth += 1
                elif src[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            bodies.append((mm.group(1), src[mm.end():i]))

        # 该视图对应的生成方法：方法体里出现 `AddComponent<<View>>()` 或 root 名字就是 <View>
        body = None
        for name, b in bodies:
            if ('AddComponent<' + view + '>()') in b or ('"' + view + '"') in b:
                body = b
                break
        if body is None:
            continue

        nodes, _vars = builder_nodes(body, 'CreateDialogShell' in body)
        vp = os.path.join(UI_DIR, view + '.cs')
        if not os.path.isfile(vp):
            continue
        refs = view_paths(vp)
        # 运行期动态生成的节点名（例如 "Panel/List/LevelButtonTemplate"）也应在 nodes 里
        missing = sorted(r for r in refs if r not in nodes)
        checked += 1
        if missing:
            problems.append((view, missing, sorted(nodes)))

    print('=' * 78)
    print('UI 节点契约校验（View 的 Find 路径 vs 生成器产出的节点）')
    print('  已比对视图：%d 个' % checked)
    for view, missing, nodes in problems:
        print('  [FAIL] %s 引用了生成器不产出的节点：' % view)
        for x in missing:
            print('           %s' % x)
        print('         生成器实际产出：%s' % ', '.join(nodes))
    if not problems:
        print('  PASS  所有视图引用的节点都能在生成器里找到')
    print()
    print('RESULT:', 'FAIL' if problems else 'PASS')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
