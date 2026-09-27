"""
Unity API 成员名校验。

背景：`BuildAssetBundleOptions.Deterministic` 报 CS0117（该枚举里根本没这个成员，
      正确名是 `DeterministicAssetBundle`，2022.2+ 推荐 `UseContentHash`）。
      这类"类型存在但成员名不对"的错误，靠"类型存在性"检查抓不到。

做法：Unity 安装目录里每个托管程序集旁边都有一份官方 API 文档 XML
      （`UnityEditor.xml` / `UnityEngine.xml` / `UnityEngine/*.xml`），
      里面逐条列出 `F:`/`M:`/`P:`/`T:` 成员签名 —— 这就是权威的成员名单。
      用它校验源码里所有的 `UnityType.Member` 静态/枚举访问。

说明：XML 不含继承信息，所以采用两级判定：
  ① 成员在该类型自己的名单里 → OK
  ② 不在，但该成员名在**任何** Unity 类型上都存在 → 视为继承成员，OK（避免误报）
  ③ 全都不存在 → FAIL（确定的名字错误）

用法：python check_unity_api.py
"""
import io, os, re, sys, collections

MANAGED = r'C:\Program Files\Unity 2022.3.62f3c1\Editor\Data\Managed'
ROOT = r'D:\FreedomTower\Assets'
DIRS = [os.path.join(ROOT, 'Scripts'), os.path.join(ROOT, 'Editor')]

xml_files = []
for p in (os.path.join(MANAGED, 'UnityEditor.xml'), os.path.join(MANAGED, 'UnityEngine.xml')):
    if os.path.exists(p):
        xml_files.append(p)
mod_dir = os.path.join(MANAGED, 'UnityEngine')
if os.path.isdir(mod_dir):
    for fn in sorted(os.listdir(mod_dir)):
        if fn.endswith('.xml'):
            xml_files.append(os.path.join(mod_dir, fn))

MEMBER_RE = re.compile(r'name="([TFMPE]):([A-Za-z0-9_\.`]+)(?:\([^"]*)?\)?"')

type_members = collections.defaultdict(set)
all_members = set()
type_names = set()
member_count = 0

for xf in xml_files:
    try:
        s = io.open(xf, encoding='utf-8-sig', errors='replace').read()
    except Exception:
        continue
    for kind, full in MEMBER_RE.findall(s):
        # 去掉泛型反引号部分：AddComponent``1 -> AddComponent
        parts = full.split('.')
        if kind == 'T':
            type_names.add(parts[-1].split('`')[0])
            continue
        if len(parts) < 2:
            continue
        member = parts[-1].split('`')[0]
        tname = parts[-2].split('`')[0]
        type_members[tname].add(member)
        all_members.add(member)
        member_count += 1

print('解析 %d 份 API 文档，%d 个类型 / %d 条成员签名' % (
    len(xml_files), len(type_members), member_count))
print()

files = []
for d in DIRS:
    for dp, _, fns in os.walk(d):
        for fn in fns:
            if fn.endswith('.cs'):
                files.append(os.path.join(dp, fn))
files.sort()


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


ACCESS_RE = re.compile(r'(?<![\w\.])([A-Z][A-Za-z0-9_]*)\.([A-Za-z_]\w*)')

# BCL 类型：Unity 安装目录的 XML 只文档化 Unity 自己的 API，不含 BCL，
# 所以 System.IO.File 这类无法用本工具校验（它们是标准库 API，存在性无悬念）。
BCL_TYPES = {
    'File', 'Directory', 'Path', 'String', 'Convert', 'Environment', 'Activator',
    'Console', 'Enum', 'Array', 'Math', 'GC', 'Nullable', 'BitConverter',
}

# Unity 官方 XML 文档并不覆盖全部公开 API。下面这些成员已用"直接对程序集做
# 字符串确证"或"泛型签名写法差异"确认存在，但 XML 里查不到，故显式放行。
KNOWN_OK = {
    ('Resources', 'GetBuiltinResource'),      # 泛型方法，XML 写作 GetBuiltinResource``1
    ('GameObject', 'FindGameObjectWithTag'),  # 已在 UnityEngine.CoreModule.dll 中确证
}

# 命名空间前缀：`System.IO` 这种形式不是"类型.成员"，要跳过
NS_PREFIXES = {
    'System', 'System.Collections', 'System.Collections.Generic', 'System.IO',
    'System.Text', 'System.Diagnostics', 'System.Linq', 'System.Threading',
    'UnityEngine', 'UnityEditor', 'UnityEngine.UI', 'UnityEngine.EventSystems',
    'UnityEngine.SceneManagement', 'UnityEditor.SceneManagement', 'UnityEngine.Networking',
    'UnityEngine.Rendering', 'UnityEngine.Profiling', 'SimpleJSON', 'FTProject',
    'FTProject.EditorTools', 'AStar', 'cfg', 'cfg.item',
}

fails = []
inherited = []
for f in files:
    rel = os.path.relpath(f, ROOT)
    code = strip_comments(io.open(f, encoding='utf-8-sig', errors='replace').read())

    # 本文件声明的字段/属性/方法名。像 `Grid.QueryCircle` 里的 Grid 是我方属性名，
    # 不是 UnityEngine.Grid 这个类型，必须先排除，否则误报。
    own_members = set(re.findall(r'\b([A-Za-z_]\w*)\s*(?:;|\{|\()', code))
    seen = set()
    for m in ACCESS_RE.finditer(code):
        t, mem = m.group(1), m.group(2)
        if (t, mem) in seen:
            continue
        seen.add((t, mem))
        if (t + '.' + mem) in NS_PREFIXES:
            continue                      # 命名空间路径（System.IO 之类），不是成员访问
        if t in ('System', 'UnityEngine', 'UnityEditor'):
            continue                      # 裸命名空间前缀（如 [System.Serializable]）
        if t in own_members:
            continue                      # 本文件声明的字段/属性名（如 Grid.QueryCircle 的 Grid）
        if t in BCL_TYPES:
            continue                      # BCL 类型，不在 Unity XML 的覆盖范围内
        if (t, mem) in KNOWN_OK:
            continue                      # 已用其它手段确认存在的 Unity API（文档未收录）
        if t not in type_members:
            continue                      # 不是 Unity 类型（自有类型/命名空间）
        if mem in type_members[t]:
            continue                      # ① 该类型自己的成员
        if mem in all_members or mem in type_names:
            inherited.append((rel, t, mem))
            continue                      # ② 继承/嵌套成员
        fails.append((rel, t, mem))       # ③ 哪里都找不到

print('=' * 78)
print('[FAIL] 成员名在任何 Unity 类型上都不存在（确定是 CS0117/CS1061）')
if fails:
    for rel, t, m in fails:
        print('  ✘ %-44s %s.%s' % (rel, t, m))
else:
    print('  PASS  未发现不存在的成员名')

print()
print('=' * 78)
print('[info] 不在该类型自身名单、但存在于其它 Unity 类型（判为继承成员，共 %d 条）' % len(inherited))
shown = collections.defaultdict(set)
for rel, t, m in inherited:
    shown[t].add(m)
for t in sorted(shown):
    print('  %-32s %s' % (t, ', '.join(sorted(shown[t]))))

print()
print('RESULT:', 'FAIL' if fails else 'PASS')
sys.exit(1 if fails else 0)
