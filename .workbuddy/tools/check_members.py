"""
跨程序集成员引用校验。

背景：Editor 脚本（Assembly-CSharp-Editor）会引用运行时类型（Assembly-CSharp）的成员，
      例如 ResPathUtil.BuildOutputRoot、GameFlowManager.startLevelId、ResBundle.All。
      拼错一个成员名就是 CS0117 / CS1061，且这类错误不会被"名字存在性"检查捕获。

做法：
  1. 从运行时源码里建立 类型 -> {成员名} 索引（含继承链合并）
  2. 扫描所有源码里的 `Type.Member` 访问，若 Type 是已知类型，则校验 Member 存在
"""
import io, os, re, sys, collections

ROOT = r'D:\FreedomTower\Assets'
DIRS = [os.path.join(ROOT, 'Scripts'), os.path.join(ROOT, 'Editor')]


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

srcs = {f: io.open(f, encoding='utf-8-sig', errors='replace').read() for f in files}

# ---- 1. 建立类型索引 ----
CLASS_RE = re.compile(r'\b(?:class|struct|enum|interface)\s+([A-Za-z_]\w*)')
BASE_RE = re.compile(r'\bclass\s+([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)')

type_members = collections.defaultdict(set)
type_base = {}
type_files = collections.defaultdict(set)

MEMBER_PATTERNS = [
    re.compile(r'\b(?:public|private|protected|internal)\s+(?:static\s+|readonly\s+|const\s+|override\s+|virtual\s+|abstract\s+|sealed\s+)*'
               r'[\w\<\>\[\]\.,\s]+?\s+([A-Za-z_]\w*)\s*(?:[;=]|\{|\()'),
]

for f in files:
    code = strip_comments(srcs[f])
    rel = os.path.relpath(f, ROOT)
    for cm in CLASS_RE.finditer(code):
        t = cm.group(1)
        type_files[t].add(f)
    for bm in BASE_RE.finditer(code):
        type_base[bm.group(1)] = bm.group(2)

# 按类型名界定成员范围（简化：同文件内所有公开成员都算这个类型的）
for t, fs in type_files.items():
    for f in fs:
        code = strip_comments(srcs[f])
        for pat in MEMBER_PATTERNS:
            for m in pat.finditer(code):
                type_members[t].add(m.group(1))
        # 枚举值 / const
        for m in re.finditer(r'\b([A-Z][A-Za-z0-9_]*)\s*=\s*[-\d"\']', code):
            type_members[t].add(m.group(1))


def members_of(t, depth=0):
    if depth > 10:
        return set()
    s = set(type_members.get(t, ()))
    b = type_base.get(t)
    if b:
        s |= members_of(b, depth + 1)
    return s


# 已知类型（运行时 + 编辑器）——只校验这些
KNOWN = set(type_files.keys())

# ---- 2. 扫描 Type.Member 访问 ----
ACCESS_RE = re.compile(r'(?<![\w\.])([A-Z][A-Za-z0-9_]*)\s*\.\s*([A-Za-z_]\w*)')

problems = []
for f in files:
    rel = os.path.relpath(f, ROOT)
    code = strip_comments(srcs[f])
    seen = set()
    for m in ACCESS_RE.finditer(code):
        t, mem = m.group(1), m.group(2)
        if t not in KNOWN:
            continue
        if t in ('System', 'UnityEngine', 'UnityEditor', 'FTProject', 'AStar', 'cfg', 'SimpleJSON'):
            continue
        if (t, mem) in seen:
            continue
        seen.add((t, mem))
        if mem not in members_of(t):
            problems.append((rel, t, mem))

# 过滤：同文件内定义的成员也可能因正则漏掉，做一次全局兜底
filtered = []
for rel, t, mem in problems:
    # 若该成员名在声明它的文件里能找到任何形式的声明，就放过
    ok = False
    for df in type_files.get(t, ()):
        dc = strip_comments(srcs[df])
        if re.search(r'\b' + re.escape(mem) + r'\b', dc) and re.search(
                r'\b' + re.escape(t) + r'\b', dc):
            ok = True
            break
    if not ok:
        filtered.append((rel, t, mem))

print('=' * 78)
print('跨程序集成员引用校验（%d 个已知类型）' % len(KNOWN))
if filtered:
    for rel, t, mem in filtered:
        print('  FAIL  %-46s %s.%s' % (rel, t, mem))
else:
    print('  PASS  所有 Type.Member 引用都能在对应类型中找到')

print()
print('RESULT:', 'FAIL' if filtered else 'PASS')
sys.exit(1 if filtered else 0)
