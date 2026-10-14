# -*- coding: utf-8 -*-
"""扫描工程内所有 prefab/场景/asset 对脚本 GUID 的引用，找出"失联引用"：
   A. 引用的 GUID 在任何 .cs.meta 中都不存在（脚本文件被删除/移动且 meta 丢失）
   B. 引用的 GUID 属于"编辑器脚本"（路径含 /Editor/），但资源要在运行时加载（运行时无此程序集）
用法: python scan_missing_script_refs.py
输出: 控制台 + .workbuddy/logs/missing_script_scan.txt
"""
import os, re, sys

ROOT = 'E:/MyTowerGame'
ASSETS = os.path.join(ROOT, 'Assets')
OUT = os.path.join(ROOT, '.workbuddy/logs/missing_script_scan.txt')

guid_re = re.compile(r'm_Script:\s*\{fileID:\s*11500000,\s*guid:\s*([0-9a-fA-F]{32})')
scan_exts = ('.prefab', '.unity', '.asset', '.controller', '.playable')

# 1) 收集所有脚本 GUID -> 路径（Assets + Packages + PackageCache 包内脚本统一收集）
guid_to_path = {}
scan_roots = [
    ASSETS,
    os.path.join(ROOT, 'Packages'),
    os.path.join(ROOT, 'Library/PackageCache'),
]
for root in scan_roots:
    if not os.path.isdir(root):
        continue
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.cs.meta'):
                p = os.path.join(dirpath, fn)
                try:
                    with open(p, encoding='utf-8', errors='ignore') as f:
                        txt = f.read(400)
                    m = re.search(r'guid:\s*([0-9a-fA-F]{32})', txt)
                    if m:
                        guid_to_path[m.group(1).lower()] = os.path.join(dirpath, fn[:-5])
                except Exception:
                    pass

print(f'[scan] .cs.meta 总数: {len(guid_to_path)}')

def is_editor_script(path):
    p = path.replace('\\', '/')
    return '/Editor/' in p or p.endswith('.Editor')

# 2) 扫描所有资源文件
missing = []   # (file, guid, kind)
for dirpath, dirnames, filenames in os.walk(ASSETS):
    for fn in filenames:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in scan_exts:
            continue
        p = os.path.join(dirpath, fn)
        try:
            with open(p, encoding='utf-8', errors='ignore') as f:
                txt = f.read()
        except Exception:
            continue
        for m in guid_re.finditer(txt):
            g = m.group(1).lower()
            if g not in guid_to_path:
                missing.append((p, g, 'GUID不存在'))
            else:
                if is_editor_script(guid_to_path[g]):
                    missing.append((p, g, '编辑器脚本:' + guid_to_path[g]))

# 3) 汇总输出
lines = []
lines.append(f'== 失联脚本引用扫描 {len(missing)} 条 ==')
by_file = {}
for p, g, kind in missing:
    rel = os.path.relpath(p, ROOT)
    by_file.setdefault(rel, []).append((g, kind))
for rel, items in sorted(by_file.items()):
    lines.append(f'\n{rel}: {len(items)} 处')
    seen = set()
    for g, kind in items:
        key = (g, kind)
        if key in seen: continue
        seen.add(key)
        lines.append(f'  - guid={g} [{kind}]')

report = '\n'.join(lines)
print(report)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(report)
print(f'\n[scan] 报告已写入 {OUT}')
