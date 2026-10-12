#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对比 UI prefab 的"当前结构"与"基准结构"，列出节点路径级增删。

用途：用户手工改了 Assets/Prefabs/UI/*.prefab 后，
      用本脚本精确算出「哪些节点路径被新增 / 删除 / 移动」，
      再据此同步 UIPrefabBuilder.cs 与各 View 脚本。

用法:
    python diff_ui_prefabs.py --base <基准目录>            # 基准 prefab 放这里（同名）
    python diff_ui_prefabs.py --base <基准目录> --json out.json

基准目录一般用 `git show HEAD:...` 导出（见 README 说明）。
退出码：0 = 无结构差异，1 = 有差异（便于 CI/钩子用）。
"""
import argparse
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(_HERE))
UI_DIR = os.path.join(PROJ, 'Assets', 'Prefabs', 'UI')

sys.path.insert(0, _HERE)
from _prefab_tree import parse, build, describe_comps  # noqa: E402

# 参与比对的 prefab（与目录下实际文件一致；新增/删除 prefab 时同步改这里）
PREFABS = [
    'ConfirmView', 'HudView', 'LevelClearView', 'LevelDetailView', 'MainMenuView',
    'PauseView', 'SelectLevelItem', 'SelectView', 'SellConfirmView', 'TipsView',
    'TowerInfoView', 'SettingView', 'TowerCodexItem', 'TowerCodexView',
]


def collect_paths(blocks, gos, tinfo):
    """返回 {节点路径: [组件名列表]}（允许多个同名路径，聚合为一条）"""
    roots = [g for g, t in tinfo.items() if t['parent_go'] is None]
    out = {}

    def walk(go, prefix):
        name = gos[go]['name']
        p = prefix + '/' + name
        comps = sorted(set(c for c in describe_comps(blocks, gos[go]['comps'])
                           if c != 'CanvasRenderer'))
        out.setdefault(p, []).append(comps)
        t = tinfo.get(go)
        if t:
            for ch in t['children_go']:
                if ch in gos:
                    walk(ch, p)

    for r in roots:
        walk(r, '')
    return out


def _scalar(body, key):
    m = re.search(r'^\s*%s:\s*(.*)$' % re.escape(key), body, re.M)
    return m.group(1).strip() if m else None


def collect_geometry(blocks, gos, tinfo):
    """返回 {节点路径: {anchorMin/anchorMax/anchoredPosition/sizeDelta/active}}。

    ★ 为什么必须比几何：`collect_paths` 只比"有哪些节点、挂什么组件"，
      对**纯数值改动**（尺寸/位置/激活态）无感 —— 而手工重排 UI 恰恰常是这类改动。
      只比路径会让 "生成器把手工调过的坐标又算回旧值" 这种回归悄悄溜过去。
    """
    roots = [g for g, t in tinfo.items() if t['parent_go'] is None]
    out = {}

    def walk(go, prefix):
        name = gos[go]['name']
        p = prefix + '/' + name
        rec = {'active': _scalar(gos[go]['body'], 'm_IsActive') == '1'}
        t = tinfo.get(go)
        if t:
            b = t['body']
            rec['anchorMin'] = _scalar(b, 'm_AnchorMin')
            rec['anchorMax'] = _scalar(b, 'm_AnchorMax')
            rec['anchoredPosition'] = _scalar(b, 'm_AnchoredPosition')
            rec['sizeDelta'] = _scalar(b, 'm_SizeDelta')
        out[p] = rec
        if t:
            for ch in t['children_go']:
                if ch in gos:
                    walk(ch, p)

    for r in roots:
        walk(r, '')
    return out


def diff_one(cur_path, base_path):
    cb = parse(cur_path)
    cg, ct = build(cb)
    cpaths = collect_paths(cb, cg, ct)
    cgeo = collect_geometry(cb, cg, ct)

    ob = parse(base_path)
    og, ot = build(ob)
    opaths = collect_paths(ob, og, ot)
    ogeo = collect_geometry(ob, og, ot)

    added = sorted(p for p in cpaths if p not in opaths)
    removed = sorted(p for p in opaths if p not in cpaths)
    common = sorted(p for p in cpaths if p in opaths)
    comp_changed = []
    geom_changed = []
    for p in common:
        a = sorted(sum(cpaths[p], []))
        b = sorted(sum(opaths[p], []))
        if a != b:
            comp_changed.append({'path': p, 'old': b, 'new': a})
        if cgeo.get(p) != ogeo.get(p):
            o = ogeo.get(p, {})
            n = cgeo.get(p, {})
            fields = {}
            for k in ('anchorMin', 'anchorMax', 'anchoredPosition', 'sizeDelta', 'active'):
                if o.get(k) != n.get(k):
                    fields[k] = {'old': o.get(k), 'new': n.get(k)}
            geom_changed.append({'path': p, 'fields': fields})
    return {
        'added': [{'path': p, 'comps': cpaths[p][0]} for p in added],
        'removed': [{'path': p, 'comps': opaths[p][0]} for p in removed],
        'componentsChanged': comp_changed,
        'geometryChanged': geom_changed,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True, help='基准 prefab 目录（同名文件）')
    ap.add_argument('--json', default=None, help='把结果也写一份 JSON 到这里')
    args = ap.parse_args()

    any_diff = False
    all_res = {}
    print('=' * 78)
    print('UI prefab 结构差异（当前 vs 基准）')
    print('  当前: %s' % UI_DIR)
    print('  基准: %s' % args.base)
    print('=' * 78)
    for name in PREFABS:
        cur = os.path.join(UI_DIR, name + '.prefab')
        base = os.path.join(args.base, name + '.prefab')
        if not os.path.isfile(cur):
            print('### %s  【当前缺失，跳过】' % name)
            continue
        if not os.path.isfile(base):
            print('### %s  【基准缺失 → 视为全新文件】' % name)
            any_diff = True
            continue
        d = diff_one(cur, base)
        if not (d['added'] or d['removed'] or d['componentsChanged'] or d['geometryChanged']):
            print('  OK   %s  （结构与几何一致）' % name)
            continue
        any_diff = True
        all_res[name] = d
        print('### %s' % name)
        for it in d['added']:
            print('   + %-52s %s' % (it['path'], ','.join(it['comps'])))
        for it in d['removed']:
            print('   - %-52s %s' % (it['path'], ','.join(it['comps'])))
        for it in d['componentsChanged']:
            print('   ~ %-52s %s → %s' % (it['path'], ','.join(it['old']), ','.join(it['new'])))
        for it in d['geometryChanged']:
            for k, v in it['fields'].items():
                print('   = %-52s %-16s %s → %s' % (it['path'], k, v['old'], v['new']))
    print('=' * 78)
    print('RESULT: %s' % ('DIFF' if any_diff else 'SAME'))
    if args.json:
        with io.open(args.json, 'w', encoding='utf-8') as f:
            f.write(json.dumps(all_res, ensure_ascii=False, indent=2))
        print('已写 JSON: %s' % args.json)
    return 1 if any_diff else 0


if __name__ == '__main__':
    sys.exit(main())
