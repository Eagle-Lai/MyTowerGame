#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UI prefab 结构缓存：把 Assets/Prefabs/UI 下所有 prefab 的节点树、
组件清单、RectTransform 关键值 dump 成一份 JSON。

【它是什么 / 不是什么】
  - 它是**结构快照缓存**（.workbuddy/cache/ui_prefabs.json），不是权威源。
  - 权威源永远是 .prefab 文件本身。
  - 用途：① 快速 diff（不必再逐字节比 YAML）② 代码生成/契约校验的比对底稿
            ③ 换机器后一眼看出 prefab 结构与代码定义是否已同步。

【与 UIPrefabBuilder.cs 的关系】
  生成器是"代码定义"，本缓存是"磁盘现实"。
  两者若不一致 = 有人手工改了 prefab 但没同步生成器 → `check_ui_contract.py` 应能报出来。
  本脚本不做判断，只负责"如实记录磁盘现实"。

用法:
    python gen_ui_prefab_cache.py            # 写入 .workbuddy/cache/ui_prefabs.json
    python gen_ui_prefab_cache.py --check    # 只校验缓存是否与磁盘一致（不写）
退出码：0 = 一致（或已写入），1 = --check 时发现不一致。
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
CACHE_DIR = os.path.join(PROJ, '.workbuddy', 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'ui_prefabs.json')

sys.path.insert(0, _HERE)
from _prefab_tree import parse, build, describe_comps  # noqa: E402

# 参与缓存的 prefab 名单（= Assets/Prefabs/UI 下本工程自有的 UI prefab）
PREFAB_NAMES = [
    'ConfirmView', 'GameIntroView', 'HudView', 'LevelClearView', 'LevelDetailView', 'MainMenuView',
    'PauseView', 'SelectLevelItem', 'SelectView', 'SellConfirmView', 'SettingView',
    'TipsView', 'TowerCodexItem', 'TowerCodexView', 'TowerInfoView',
]


def _scalar(body, key):
    m = re.search(r'^\s*%s:\s*(.*)$' % re.escape(key), body, re.M)
    return m.group(1).strip() if m else None


def dump_prefab(path):
    blocks = parse(path)
    gos, tinfo = build(blocks)
    roots = [g for g, t in tinfo.items() if t['parent_go'] is None]

    # ★ 只记"工程根相对路径"（不写盘符）：本工程有家用D盘 / 公司E盘两份副本，
    #   写死绝对路径会让缓存一换机器就"假性不一致"。
    rel = os.path.relpath(path, PROJ).replace(os.sep, '/')

    def node(go, prefix):
        name = gos[go]['name']
        p = prefix + '/' + name
        t = tinfo.get(go)
        rec = {'path': p, 'name': name,
               'components': describe_comps(blocks, gos[go]['comps'])}
        gom = gos[go]['body']
        rec['active'] = _scalar(gom, 'm_IsActive') == '1'
        if t:
            b = t['body']
            rec['anchorMin'] = _scalar(b, 'm_AnchorMin')
            rec['anchorMax'] = _scalar(b, 'm_AnchorMax')
            rec['anchoredPosition'] = _scalar(b, 'm_AnchoredPosition')
            rec['sizeDelta'] = _scalar(b, 'm_SizeDelta')
            rec['pivot'] = _scalar(b, 'm_Pivot')
            rec['children'] = [node(c, p) for c in t['children_go'] if c in gos]
        else:
            rec['children'] = []
        return rec

    return {
        'asset': rel,
        'nodeCount': len(gos),
        'roots': [node(r, '') for r in roots],
    }


def build_cache():
    data = {'version': 1, 'source': 'Assets/Prefabs/UI', 'prefabs': {}}
    for name in PREFAB_NAMES:
        p = os.path.join(UI_DIR, name + '.prefab')
        if not os.path.isfile(p):
            data['prefabs'][name] = {
                'asset': os.path.relpath(p, PROJ).replace(os.sep, '/'),
                'missing': True}
            continue
        data['prefabs'][name] = dump_prefab(p)
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='只比对，不写盘')
    args = ap.parse_args()

    fresh = build_cache()
    if args.check:
        if not os.path.isfile(CACHE_FILE):
            print('缓存不存在：%s' % CACHE_FILE)
            return 1
        old = json.loads(io.open(CACHE_FILE, encoding='utf-8').read())
        if old == fresh:
            print('OK  缓存与磁盘一致：%s' % CACHE_FILE)
            return 0
        print('DIFF  缓存与磁盘不一致：')
        for name in PREFAB_NAMES:
            a = old.get('prefabs', {}).get(name)
            b = fresh['prefabs'].get(name)
            if a != b:
                print('   - %s' % name)
        print('（重新生成请运行：python .workbuddy/tools/gen_ui_prefab_cache.py）')
        return 1

    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    with io.open(CACHE_FILE, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=2))
    total = sum(v.get('nodeCount', 0) for v in fresh['prefabs'].values())
    print('已写入缓存：%s' % CACHE_FILE)
    print('  预制体 %d 个，节点合计 %d 个' % (len(PREFAB_NAMES), total))
    for name in PREFAB_NAMES:
        v = fresh['prefabs'][name]
        print('    %-18s %s 个节点' % (name, v.get('nodeCount', '缺失')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
