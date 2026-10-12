#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时工具：解析 Unity prefab，输出 GameObject 树 + 组件清单。

用法:
    python _prefab_tree.py <prefab路径> [--tree] [--components]
"""
import io, os, re, sys

COMP_NAMES = {
    '114': 'MonoBehaviour', '222': 'CanvasRenderer', '223': 'Canvas',
    '224': 'RectTransform', '225': 'CanvasGroup', '1': 'GameObject',
    '4': 'Transform', '82': 'AudioSource', '95': 'Animator',
    '111': 'Animation', '198': 'ParticleSystem', '199': 'ParticleSystemRenderer',
    '11400000': 'Scriptable', '11500000': 'Script',
}


def read(path):
    with io.open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def parse(path):
    txt = read(path)
    # 拆成 "{class} &{fileID}\n{body}" 块
    blocks = {}
    # 匹配注释头 `--- !u!<class> &<id>` 或 `--- !u!<class> &<id> stripped`
    pat = re.compile(r'^--- !u!(\d+) &(\d+)(?:\s+stripped)?\s*$', re.M)
    marks = [(m.start(), int(m.group(1)), int(m.group(2))) for m in pat.finditer(txt)]
    for i, (pos, cls, fid) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(txt)
        body = txt[pos:end]
        blocks[fid] = (cls, body)
    return blocks


def get_scalar(body, key):
    m = re.search(r'^\s*%s:\s*(.*)$' % re.escape(key), body, re.M)
    return m.group(1).strip() if m else None


def go_name(body):
    return get_scalar(body, 'm_Name')


def go_components(body):
    out = []
    m = re.search(r'^\s*m_Component:\s*$', body, re.M)
    if not m:
        return out
    rest = body[m.end():]
    for mm in re.finditer(r'^\s*-\s*component:\s*\{fileID:\s*(\d+)\}', rest, re.M):
        out.append(int(mm.group(1)))
    return out


def rt_parent(body):
    return get_scalar(body, 'm_Father')


def rt_children(body):
    out = []
    m = re.search(r'^\s*m_Children:\s*$', body, re.M)
    if not m:
        m = re.search(r'^\s*m_Children:\s*\[\]\s*$', body, re.M)
        return out
    rest = body[m.end():]
    for mm in re.finditer(r'^\s*-\s*\{fileID:\s*(\d+)\}', rest, re.M):
        out.append(int(mm.group(1)))
    return out


def go_of_component(blocks, comp_fid):
    cls, body = blocks[comp_fid]
    go = get_scalar(body, 'm_GameObject')
    if go:
        m = re.search(r'fileID:\s*(\d+)', go)
        if m:
            return int(m.group(1))
    return None


def build(blocks):
    """返回 fid -> dict{name, comps:[(cls,body)], parent_go, children_go}"""
    rts = {}   # rt_fid -> (go_fid, body)
    gos = {}   # go_fid -> (name, comp_fids, body)
    for fid, (cls, body) in blocks.items():
        if cls == 1:
            gos[fid] = {'name': go_name(body), 'comps': go_components(body), 'body': body}
    # 补上没在 m_Component 列出的组件（按 m_GameObject 反查）
    for fid, (cls, body) in blocks.items():
        if cls == 1:
            continue
        go = go_of_component(blocks, fid)
        if go is not None and go in gos:
            if fid not in gos[go]['comps']:
                gos[go]['comps'].append(fid)
    # RectTransform / Transform 的父子
    tinfo = {}      # go_fid -> info (parent/children 用 go_fid 表示)
    rt2go = {}      # rt_fid -> go_fid
    raw = {}        # go_fid -> (parent_rt_fid, children_rt_fids)
    for fid, (cls, body) in blocks.items():
        if cls in (4, 224):
            go = go_of_component(blocks, fid)
            rt2go[fid] = go
            p = rt_parent(body)
            pv = None
            if p:
                m = re.search(r'fileID:\s*(\d+)', p)
                pv = int(m.group(1)) if m else None
                if pv == 0:
                    pv = None
            raw[go] = (pv, rt_children(body), cls, fid)
    for go, (p_rt, ch_rts, cls, fid) in raw.items():
        p_go = rt2go.get(p_rt) if p_rt else None
        ch_gos = [rt2go.get(c) for c in ch_rts if c in rt2go]
        tinfo[go] = {'t': fid, 'cls': cls, 'parent_go': p_go,
                     'children_go': ch_gos, 'body': blocks[fid][1]}
    return gos, tinfo


def dump_tree(blocks, gos, tinfo, root_go, indent=0):
    """按 RectTransform 父子关系打印树"""
    name = gos[root_go]['name']
    comps = describe_comps(blocks, gos[root_go]['comps'])
    print('%s%s  [%s]' % ('  ' * indent, name, ', '.join(comps)))
    t = tinfo.get(root_go)
    if not t:
        return
    for ch in t['children_go']:
        if ch in gos:
            dump_tree(blocks, gos, tinfo, ch, indent + 1)


def describe_comps(blocks, comp_fids):
    out = []
    for cf in comp_fids:
        if cf not in blocks:
            out.append('?%d' % cf)
            continue
        cls, body = blocks[cf]
        if cls == 114:
            script = get_scalar(body, 'm_Script') or ''
            m = re.search(r'guid:\s*([0-9a-f]+)', script)
            out.append('Mono(%s)' % (m.group(1)[:6] if m else '?'))
        elif cls == 223:
            out.append('Canvas')
        elif cls == 225:
            out.append('CanvasGroup')
        elif cls == 222:
            out.append('CanvasRenderer')
        elif cls == 95:
            out.append('Animator')
        elif cls == 114:
            out.append('Mono')
        elif cls == 1:
            continue
        else:
            out.append(COMP_NAMES.get(str(cls), 'cls%s' % cls))
    # 去重保序
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res


if __name__ == '__main__':
    p = sys.argv[1]
    blocks = parse(p)
    gos, tinfo = build(blocks)
    # 找根：没有 m_Father 或 father 为 0 的
    roots = []
    for go, t in tinfo.items():
        if t['parent_go'] is None:
            roots.append(go)
    print('== 节点总数: %d ==' % len(gos))
    for r in roots:
        dump_tree(blocks, gos, tinfo, r)
