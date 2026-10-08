"""
事件系统一致性校验。

背景（来自 EventController 的实现）：
  - AddEventListener<T..> 把回调以 Action<T..> 存进字典
  - TriggerEvent<T..> 用 `invocationList[i] as Action<T..>` 取回调
    → **arity 不匹配时 as 返回 null，日志只打一句 "something error here"，
       随后 action(...) 抛 NullReferenceException 又被 try/catch 吞掉**
    → 症状是"监听器静默不触发"，极难排查

因此必须保证：同一事件名上，Trigger 的 arity == Add 的 arity。

另检查编译期错误类：把带参数的方法组传给 AddEventListener(string, Action)
（无泛型）会报 CS1503 "cannot convert from 'method group' to 'Action'"。
"""
import io, os, re, sys, collections

# ★ ROOT 由脚本自身位置推导（旧版硬编码 'D:\FreedomTower\Assets' 少了 _1，
#   会导致扫 0 个文件却打印 PASS —— 见文件里的自检）
_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(os.path.dirname(_HERE)), 'Assets')
DIRS = [os.path.join(ROOT, 'Scripts'), os.path.join(ROOT, 'Editor')]


def strip_code(src):
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


files = []
for d in DIRS:
    for dp, _, fns in os.walk(d):
        for fn in fns:
            if fn.endswith('.cs'):
                files.append(os.path.join(dp, fn))
files.sort()

# ★ 自检：一个 .cs 都没扫到，说明 ROOT 写错了，必须 FAIL —— 不能沉默地报 PASS
if not files:
    print('目录下没扫到任何 .cs 文件，ROOT 很可能写错了：')
    for d in DIRS:
        print('    %s%s' % (d, '' if os.path.isdir(d) else '   <- 该目录不存在'))
    print('RESULT: FAIL (扫描到 0 个文件)')
    sys.exit(1)
print('扫描 %d 个 .cs 文件' % len(files))

# 方法签名表（同文件内解析）
METHOD_RE = re.compile(
    r'\b(?:private|public|protected|internal)\s+(?:static\s+)?(?:override\s+)?'
    r'(?:void|bool|int|float|string|double|[A-Z]\w*(?:<[^>]*>)?(?:\[\])?)\s+(\w+)\s*\(([^;{)]*)\)')


def count_params(param_text):
    t = param_text.strip()
    if not t:
        return 0
    depth = 0
    parts = []
    cur = ''
    for ch in t:
        if ch in '(<[':
            depth += 1
        elif ch in ')>]':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return len([p for p in parts if p.strip()])


# 匹配 EventDispatcher.XXX<...>(EventName.Y, Handler)  或  (EventName.Y, Handler)
CALL_RE = re.compile(
    r'EventDispatcher\.(AddEventListener|RemoveEventListener|TriggerEvent)'
    r'\s*(?:<\s*([^<>()]*?)\s*>)?\s*\(\s*EventName\.(\w+)\s*(?:,\s*(.+?))?\s*\)\s*;')

arity_problems = []           # 编译期错误类（handler 参数数 != 泛型 arity）
trigger_add = collections.defaultdict(lambda: {'trigger': set(), 'add': set()})
unresolved = []

for f in files:
    rel = os.path.relpath(f, ROOT)
    raw = io.open(f, encoding='utf-8-sig', errors='replace').read()
    code = strip_code(raw)

    methods = {}
    for m in METHOD_RE.finditer(code):
        methods[m.group(1)] = count_params(m.group(2))

    for line_no, line in enumerate(raw.split('\n'), 1):
        cm = CALL_RE.search(line)
        if not cm:
            continue
        kind, generics, evname, rest = cm.group(1), cm.group(2), cm.group(3), cm.group(4) or ''
        g = [x.strip() for x in generics.split(',')] if generics else []
        g = [x for x in g if x]
        declared_arity = len(g)

        if kind == 'TriggerEvent':
            trigger_add[evname]['trigger'].add(declared_arity)
            continue

        trigger_add[evname]['add'].add(declared_arity)

        # 解析 handler：可能是方法名、lambda、this.X
        handler = rest.strip()
        # 去掉可能的多余逗号/空白
        handler = handler.rstrip(',').strip()
        if not handler:
            continue

        if '=>' in handler:
            # lambda：统计 '=>' 左侧的参数个数
            left = handler.split('=>')[0].strip().strip('()')
            actual = count_params(left)
        elif '(' in handler:
            # 形如 OnXxx(...) 的调用 —— 不是方法组，跳过
            continue
        else:
            name = handler.split('.')[-1].strip()
            if name in methods:
                actual = methods[name]
            else:
                unresolved.append((rel, line_no, evname, name))
                continue

        if actual != declared_arity:
            arity_problems.append((rel, line_no, kind, evname, declared_arity, actual, handler))

print('=' * 78)
print('[1] 监听器参数个数 vs 泛型 arity（不匹配 → CS1503 或静默失效）')
if arity_problems:
    for rel, ln, kind, ev, dec, act, h in arity_problems:
        print('  FAIL  %s:%d' % (rel, ln))
        print('        %s(EventName.%s, %s)' % (kind, ev, h))
        print('        显式泛型 arity=%d，但方法参数个数=%d' % (dec, act))
else:
    print('  PASS  全部匹配')

print()
print('=' * 78)
print('[2] 同一事件名：Trigger 与 Add 的 arity 是否一致（不一致 → 静默不触发）')
mismatch = []
for ev, d in sorted(trigger_add.items()):
    if d['trigger'] and d['add'] and d['trigger'] != d['add']:
        mismatch.append((ev, sorted(d['trigger']), sorted(d['add'])))
if mismatch:
    for ev, t, a in mismatch:
        print('  FAIL  EventName.%-26s Trigger arity=%s  Add arity=%s' % (ev, t, a))
else:
    print('  PASS  已注册监听的事件名，Trigger/Add arity 全部一致')

print()
print('=' * 78)
print('[3] 事件使用概览')
for ev in sorted(trigger_add):
    d = trigger_add[ev]
    print('  %-28s trigger=%s  add=%s' % (ev, sorted(d['trigger']) or '-', sorted(d['add']) or '-'))

if unresolved:
    print()
    print('=' * 78)
    print('[info] 无法解析的 handler（可能是外部方法或表达式，需人工确认）')
    for rel, ln, ev, name in unresolved:
        print('  %s:%d  %s -> %s' % (rel, ln, ev, name))

print()
ok = not arity_problems and not mismatch
print('RESULT:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
