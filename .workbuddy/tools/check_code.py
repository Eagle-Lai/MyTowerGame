"""
M0 代码静态校验（本机没有可用的 C# 编译器，用脚本替代结构性与约定性检查）
检查项：
  1. 括号 / 字符串 / 注释 平衡
  2. 类 / 枚举 / 接口 重名（会导致 CS0101）
  3. MonoBehaviour 类名与文件名一致性（Unity 硬性要求；不一致且该文件没有同名
     MonoBehaviour 时判 FAIL，否则只判 WARN）
  4. EventName 常量：使用点 vs 定义点（未定义会 CS0117）
  5. ResTable 逻辑名：字面量调用 vs 登记项（防拼写错误）
"""
import io, os, re, sys, collections

ROOT = r'D:\FreedomTower\Assets'
DIRS = [os.path.join(ROOT, 'Scripts'), os.path.join(ROOT, 'Editor')]


def strip_code(src):
    """去掉注释与字符串字面量，只留结构字符"""
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
        if c == '@' and i + 1 < n and src[i + 1] == '"':
            i += 2
            while i < n:
                if src[i] == '"':
                    if i + 1 < n and src[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            continue
        if c == '"':
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if c == "'":
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def strip_comments_only(src):
    """只去注释，保留字符串字面量（用于扫描 EventName.X / ResTable 字面量）"""
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
        if c == '@' and i + 1 < n and src[i + 1] == '"':
            start = i
            i += 2
            while i < n:
                if src[i] == '"':
                    if i + 1 < n and src[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            out.append(src[start:i])
            continue
        if c == '"':
            start = i
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                i += 1
            out.append(src[start:i])
            continue
        out.append(c)
        i += 1
    return ''.join(out)


files = []
for d in DIRS:
    if not os.path.isdir(d):
        continue
    for dp, _, fns in os.walk(d):
        for fn in fns:
            if fn.endswith('.cs'):
                files.append(os.path.join(dp, fn))
files.sort()
print('扫描 %d 个 .cs 文件\n' % len(files))

balance_fail = []
type_defs = collections.defaultdict(list)
mono_fail, mono_warn = [], []

TYPE_RE = re.compile(
    r'\b(?:public|internal|private|protected)?\s*(?:sealed\s+|abstract\s+|static\s+|partial\s+)*'
    r'(class|struct|enum|interface)\s+([A-Za-z_]\w*)')
BASE_RE = re.compile(r'\bclass\s+([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)\b')

direct_mono, base_of = {}, {}
srcs = {}
for f in files:
    raw = io.open(f, encoding='utf-8-sig', errors='replace').read()
    srcs[f] = raw
    code = strip_code(raw)
    for m in BASE_RE.finditer(code):
        cls, base = m.group(1), m.group(2)
        base_of[cls] = base
        if base == 'MonoBehaviour':
            direct_mono[cls] = True


def is_mono(cls, depth=0):
    if depth > 12:
        return False
    if cls in direct_mono:
        return True
    b = base_of.get(cls)
    return is_mono(b, depth + 1) if b else False


for f in files:
    rel = os.path.relpath(f, ROOT)
    raw = srcs[f]
    code = strip_code(raw)

    # 1. 平衡
    probs = []
    for o, c, nm in [('{', '}', 'brace'), ('(', ')', 'paren'), ('[', ']', 'bracket')]:
        depth, mn = 0, 0
        for ch in code:
            if ch == o:
                depth += 1
            elif ch == c:
                depth -= 1
                mn = min(mn, depth)
        if depth != 0 or mn < 0:
            probs.append('%s final=%d min=%d' % (nm, depth, mn))
    if probs:
        balance_fail.append((rel, ', '.join(probs)))

    # 1b. 嵌套层级（防 CS0106：方法声明跑到类外）
    # 只查括号平衡不够：多一个 { 且末尾多一个 } 抵消后整体依然平衡，
    # 但方法声明会落到类外 —— 那要到编译期才报错。
    # 规则：namespace 深度1、class 深度2，类成员声明必须都在同一深度。
    decl_depths = []
    d2 = 0
    ln2 = 1
    buf = ""
    for ch in code:
        if ch == "\n":
            ln2 += 1; buf = ""
        elif ch == "{":
            d2 += 1; buf = ""
        elif ch == "}":
            d2 -= 1; buf = ""
        else:
            buf += ch
            if len(buf) > 300:
                buf = buf[-300:]
            m = re.search(r"((?:public|private|protected|internal)\s+[^\n{]*?\b(?:class|void|bool|int|float|string)\s+\w+\s*\()$", buf)
            if m and d2 >= 2:
                decl_depths.append((ln2, d2, m.group(1).strip()[:70]))

    if decl_depths:
        ds = set(x[1] for x in decl_depths)
        if len(ds) > 1:
            common = min(ds)
            for ln3, dv, t in decl_depths:
                if dv != common:
                    probs.append("嵌套层级异常 行%d 深度%d: %s（应与其他成员一致 depth=%d）"
                                 % (ln3, dv, t, common))

    # 2. 类型
    for m in TYPE_RE.finditer(code):
        type_defs[m.group(2)].append((rel, m.group(1)))

    # 3. MonoBehaviour 文件名
    fname = os.path.splitext(os.path.basename(f))[0]
    mono_in_file = set()
    for m in BASE_RE.finditer(code):
        if is_mono(m.group(1)):
            mono_in_file.add(m.group(1))
    for cls in sorted(mono_in_file):
        if cls == fname:
            continue
        if fname in mono_in_file:
            mono_warn.append((rel, cls, fname))
        else:
            mono_fail.append((rel, cls, fname))

print('=' * 78)
print('[1] 括号平衡')
if balance_fail:
    for rel, p in balance_fail:
        print('  FAIL  %-52s %s' % (rel, p))
else:
    print('  PASS  全部文件括号平衡')

print()
print('=' * 78)
print('[2] 类型重名（CS0101）')
dup = {k: v for k, v in type_defs.items() if len(v) > 1}
if dup:
    for k, v in sorted(dup.items()):
        print('  FAIL  %s' % k)
        for rel, kind in v:
            print('          %-10s %s' % (kind, rel))
else:
    print('  PASS  无重名类型')

print()
print('=' * 78)
print('[3] MonoBehaviour 类名 == 文件名')
if mono_fail:
    for rel, cls, fname in mono_fail:
        print('  FAIL  %-46s 类 %s / 文件 %s.cs' % (rel, cls, fname))
else:
    print('  PASS  无不一致（Unity 可正常序列化这些组件）')
for rel, cls, fname in mono_warn:
    print('  warn  %-46s 附带 MonoBehaviour %s（主类名匹配，可接受）' % (rel, cls))

# ---- 4. EventName 常量 ----
print()
print('=' * 78)
print('[4] EventName 常量：使用 vs 定义')
event_file = os.path.join(ROOT, 'Scripts', 'Core', 'Event', 'EventName.cs')
defined = set()
if os.path.exists(event_file):
    defined = set(re.findall(r'public\s+const\s+string\s+(\w+)\s*=',
                            io.open(event_file, encoding='utf-8-sig').read()))
used = collections.defaultdict(set)
for f in files:
    rel = os.path.relpath(f, ROOT)
    for m in re.finditer(r'\bEventName\.(\w+)', strip_comments_only(srcs[f])):
        used[m.group(1)].add(rel)
missing_ev = sorted(k for k in used if k not in defined)
unused_ev = sorted(k for k in defined if k not in used)
if missing_ev:
    for k in missing_ev:
        print('  FAIL  使用了未定义的事件名 EventName.%s  ← %s' % (k, ', '.join(sorted(used[k]))))
else:
    print('  PASS  %d 个被引用的事件名全部已定义' % len(used))
if unused_ev:
    print('  info  已定义但未被引用：%s' % ', '.join(unused_ev))

# ---- 5. ResTable 逻辑名 ----
print()
print('=' * 78)
print('[5] ResTable 逻辑名：代码字面量 vs 登记项')
table_file = os.path.join(ROOT, 'Scripts', 'Core', 'Res', 'ResTable.cs')
registered = set()
if os.path.exists(table_file):
    txt = io.open(table_file, encoding='utf-8-sig').read()
    registered = set(re.findall(r'\{\s*"(\w+)"\s*,\s*new\s+ResAddress', txt))
literal_calls = collections.defaultdict(set)
CALL_RE = re.compile(
    r'(?:Load<[^>]+>|Instantiate|LoadAsync<[^>]+>|ReleaseInstance)\s*\(\s*"(\w+)"')
for f in files:
    rel = os.path.relpath(f, ROOT)
    if rel.endswith('ResTable.cs'):
        continue
    for m in CALL_RE.finditer(strip_comments_only(srcs[f])):
        literal_calls[m.group(1)].add(rel)
missing_key = sorted(k for k in literal_calls if k not in registered)
if missing_key:
    for k in missing_key:
        print('  FAIL  使用了未登记的逻辑名「%s」 ← %s' % (k, ', '.join(sorted(literal_calls[k]))))
else:
    print('  PASS  %d 个字面量逻辑名全部已在 ResTable 登记' % len(literal_calls))
unreg = sorted(k for k in registered if k not in literal_calls)
if unreg:
    print('  info  已登记但代码未直接引用（可能由配置表 resName 间接引用）：%s' % ', '.join(unreg))

print()
print('=' * 78)
print('[汇总]')
print('  括号问题   : %d' % len(balance_fail))
print('  重名问题   : %d' % len(dup))
print('  文件名问题 : %d' % len(mono_fail))
print('  事件名问题 : %d' % len(missing_ev))
print('  逻辑名问题 : %d' % len(missing_key))

ok = not balance_fail and not dup and not mono_fail and not missing_ev and not missing_key
print()
print('RESULT:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
