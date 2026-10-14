# -*- coding: utf-8 -*-
"""清除怪物动画控制器（.controller）中对两个"从未入库脚本"的 StateMachineBehaviour 引用。

背景：Assets/_UIAssets/Monsters 下 29 个 controller 引用 GUID 408e2275… / 57830dc1…
（素材包自带、从未随包导入）。运行时加载敌人资源会报
"The referenced script on this Behaviour (Game Object '<null>') is missing!"。
本脚本做"确定性清理"：
  1) 收集引用这两个 GUID 的 !u!114 对象块 id；
  2) 从 m_StateMachineBehaviours 数组中删除 `- {fileID: <id>}` 引用行；
  3) 删除整个坏块（从 "--- !u!114 &<id>" 到下一个 "--- " 之前）；
  4) 删除后若数组为空，把 "m_StateMachineBehaviours:" 归一为 "m_StateMachineBehaviours: []"。
幂等：对已清理过的文件再跑无变化。改动前请确保 git 工作区干净（可随时回滚）。

用法：
  python clean_animator_bad_refs.py          # dry-run：只统计，不写盘
  python clean_animator_bad_refs.py --apply  # 实际写盘
"""
import os
import re
import sys

ROOT = 'E:/MyTowerGame'
BAD_GUIDS = {
    '408e227577c5a194ba246d63582e3419',
    '57830dc1190df88479e9a6155ff52be7',
}


def find_bad_block_ids(txt):
    """返回引用坏 GUID 的 !u!114 块 id 集合。"""
    ids = set()
    pattern = re.compile(
        r'--- !u!114 &(-?\d+)\r?\n(?:(?!\r?\n--- )[\s\S])*?'
        r'm_Script: \{fileID: 11500000, guid: ([0-9a-fA-F]{32})')
    for m in pattern.finditer(txt):
        if m.group(2).lower() in BAD_GUIDS:
            ids.add(m.group(1))
    return ids


def clean_text(txt, bad_ids):
    """执行三步清理（行级处理，保守精确）。返回 (新文本, 删除引用行数, 删除块数)。"""
    lines = txt.split('\n')
    # ---- 1) 删除引用行（形如 "  - {fileID: <id>}"） ----
    removed_refs = 0
    id_set = set(bad_ids)
    step1 = []
    for line in lines:
        m = re.match(r'^\s*- \{fileID: (-?\d+)\}\s*$', line)
        if m and m.group(1) in id_set:
            removed_refs += 1
            continue
        step1.append(line)

    # ---- 2) 删除坏块 ----
    removed_blocks = 0
    step2 = []
    skip = False
    for line in step1:
        if line.startswith('--- '):
            skip = False
            m = re.match(r'^--- !u!114 &(-?\d+)\s*$', line)
            if m and m.group(1) in id_set:
                skip = True
                removed_blocks += 1
                continue
        if skip:
            continue
        step2.append(line)

    # ---- 3) 空数组归一 ----
    step3 = []
    for idx, line in enumerate(step2):
        if line.strip() == 'm_StateMachineBehaviours:':
            nxt = step2[idx + 1] if idx + 1 < len(step2) else ''
            if not nxt.strip().startswith('- '):
                step3.append(line.replace('m_StateMachineBehaviours:',
                                          'm_StateMachineBehaviours: []'))
                continue
        step3.append(line)

    return '\n'.join(step3), removed_refs, removed_blocks


def main():
    apply = '--apply' in sys.argv
    uia = os.path.join(ROOT, 'Assets/_UIAssets')
    files = []
    for dirpath, _dirnames, filenames in os.walk(uia):
        for fn in filenames:
            if fn.endswith('.controller'):
                files.append(os.path.join(dirpath, fn))

    total_files = 0
    total_refs = 0
    total_blocks = 0
    for p in sorted(files):
        with open(p, encoding='utf-8', errors='ignore') as f:
            txt = f.read()
        bad_ids = find_bad_block_ids(txt)
        if not bad_ids:
            continue
        new_txt, refs, blocks = clean_text(txt, bad_ids)
        changed = (new_txt != txt)
        total_files += 1
        total_refs += refs
        total_blocks += blocks
        rel = os.path.relpath(p, ROOT)
        tail = '' if not apply else ('  [已写盘]' if changed else '  [无变化]')
        print(f'{rel}: 坏块 {len(bad_ids)} 个 / 删引用行 {refs} / 删块 {blocks}{tail}')
        if apply and changed:
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new_txt)

    mode = 'APPLY' if apply else 'DRY-RUN'
    print(f'\n[{mode}] 涉及文件 {total_files} 个 / 引用行 {total_refs} / 对象块 {total_blocks}')
    if not apply:
        print('（未写盘；确认后加 --apply 执行）')


if __name__ == '__main__':
    main()
