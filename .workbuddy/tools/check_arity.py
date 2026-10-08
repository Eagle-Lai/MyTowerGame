"""
调用参数个数（arity）校验。

存在理由：本工程没有 C# 编译器（沙箱拦截 csc/MSBuild），
而"调用时参数个数写错"（如 Concat(a,b,c,d) 调一个只接受 3 个参数的方法）
只有编译期才会报 CS1501 —— 静态脚本此前完全查不出来，已经真实漏掉过一次。

做法（保守，只报高置信度的问题，避免误报淹没真问题）：
  1. 收集每个文件里"本类声明"的方法名 → 允许的参数个数集合（含 params 展开、默认值）；
  2. 扫描该文件（及同批文件）中 `Name(...)` 形式的调用；
  3. 若被调用的名字**只在这批文件里声明过**（外部库方法不参与判断），
     且实参个数不在允许集合里 → 报 FAIL。
"""
import io, os, re, sys, collections

# ★ 路径一律由脚本位置推导成绝对路径。
#   旧版用的是相对路径（'Assets/...'），一旦不从工程根目录运行就会静默少检文件，
#   仍然打印 PASS —— 和 check_code.py 那个"假通过"是同一类坑。
_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(_HERE))

DIRS = [
    os.path.join(PROJ, 'Assets', 'Scripts', 'Data', 'Persistence'),
    os.path.join(PROJ, 'Assets', 'Scripts', 'Core', 'Manager'),
    os.path.join(PROJ, 'Assets'),
]
ONLY_FILES = None  # 只检查本次改动涉及的文件

_PERSIST = os.path.join(PROJ, 'Assets', 'Scripts', 'Data', 'Persistence')
if not os.path.isdir(_PERSIST):
    print('找不到目录：' + _PERSIST)
    print('RESULT: FAIL')
    sys.exit(1)

TARGETS = [os.path.join(_PERSIST, f)
           for f in sorted(os.listdir(_PERSIST)) if f.endswith('.cs')]

# 本次（及近期）改动涉及的文件。
# 【为什么要显式列出】本脚本靠"方法名只在这批文件里声明过"来决定查不查，
#   范围圈小可以少误报；但**圈漏了文件 = 那部分代码根本没被检查**，
#   所以每次改完代码要顺手把新文件加进来。
_CHANGED = [
    'Assets/Scripts/Core/Manager/SaveManager.cs',
    'Assets/PopMain.cs',
    # —— 关卡结算弹窗（修"通关无弹窗"）——
    'Assets/Scripts/UI/LevelClearView.cs',
    'Assets/Scripts/UI/LevelClearInfo.cs',
    'Assets/Scripts/Game/GameFlowManager.cs',
    'Assets/Scripts/Core/Res/ResTable.cs',
    'Assets/Editor/UIPrefabBuilder.cs',
    # —— 关卡地图编辑器「一键写入」（写表 + Luban 重导 + 回读）——
    'Assets/Editor/LevelMapEditorWindow.cs',
    # —— 引入 YooAsset（适配器 + 实现选择）——
    'Assets/Scripts/Core/Res/YooAssetResLoader.cs',
    'Assets/Scripts/Core/Res/ResLoader.cs',
    # —— YooAsset 接入落地（分组包规则 + 宏开关 + 接入向导）——
    'Assets/Editor/YooAsset/FTBundlePackRule.cs',
    'Assets/Editor/YooAsset/FTYooAssetDefine.cs',
    'Assets/Editor/YooAsset/FTYooAssetSetupWizard.cs',
]
for _rel in _CHANGED:
    TARGETS.append(os.path.join(PROJ, *_rel.split('/')))

# 清单里的文件必须都在，否则"漏检文件"会伪装成 PASS
_MISSING = [t for t in TARGETS if not os.path.isfile(t)]
if _MISSING:
    print('以下待检文件不存在，检查清单已失效：')
    for m in _MISSING:
        print('    ' + m)
    print('RESULT: FAIL (检查清单失效)')
    sys.exit(1)

# 支持命令行指定文件（便于用"故意写错的样本"验证本脚本自身是否有效）
if len(sys.argv) > 1:
    TARGETS = sys.argv[1:]


def strip(src):
    """去注释与字符串/字符字面量，只留结构。
    ★ 关键：删除内容时必须**原样保留其中的换行**，否则后续报出的行号会整体漂移，
      排查时会指到完全无关的代码行上。"""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            continue                                  # 换行留给下一轮 append
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            nl = 0
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                if src[i] == '\n':
                    nl += 1
                i += 1
            i += 2
            out.append('\n' * nl)                     # 保留行数
            continue
        if c == '@' and i + 1 < n and src[i + 1] == '"':
            i += 2
            nl = 0
            while i < n:
                if src[i] == '"':
                    if i + 1 < n and src[i + 1] == '"':
                        i += 2
                        continue
                    i += 1
                    break
                if src[i] == '\n':
                    nl += 1
                i += 1
            out.append('""' + '\n' * nl)
            continue
        if c == '"':
            i += 1
            nl = 0
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                if src[i] == '\n':
                    nl += 1
                i += 1
            out.append('""' + '\n' * nl)
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
            out.append("''")
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def split_args(s):
    """按顶层逗号切分实参；空串表示 0 个参数。"""
    s = s.strip()
    if not s:
        return []
    args = []
    depth = 0
    cur = ''
    for ch in s:
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        elif ch == ',' and depth == 0:
            args.append(cur)
            cur = ''
            continue
        elif ch == '<':
            depth += 1
        elif ch == '>':
            depth -= 1
        cur += ch
    args.append(cur)
    return args


# ---- 1. 收集声明 ----
# 【BCL 继承成员白名单】这些名字在任何类型上都可能被调用成别的重载
# （例如本地重写了 `ToString()`，但 `x.ToString(provider)` 依然是合法的库重载），
# 因此只要出现就整名跳过，否则会产生大量误报。
BCL_COMMON = {
    'ToString', 'Equals', 'GetHashCode', 'CompareTo', 'Clone',
    'GetType', 'Finalize', 'MemberwiseClone', 'Invoke', 'GetEnumerator',
}

# 【关键字/语法噪声】避免把 if/for 等语句当成方法
NOISE = {'if', 'for', 'while', 'switch', 'catch', 'return', 'foreach', 'lock',
         'using', 'get', 'set', 'fixed', 'checked', 'unchecked', 'sizeof', 'typeof',
         'nameof', 'default', 'delegate', 'when'}

decl = collections.defaultdict(lambda: collections.defaultdict(set))  # file -> name -> arities
# 【必须按"名字"全局记录 params】不能按文件记：
# `IDatabase.Execute(string, params object[])` 声明在 IDatabase.cs，
# 而调用点在 SqliteSaveStorage.cs —— 按文件记就会让调用点判不出"可传任意个数"。
params_names = set()
for f in TARGETS:
    src = strip(io.open(f, encoding='utf-8-sig', errors='replace').read())
    code = src
    # 方法声明： 修饰符 返回类型 名字(参数列表)
    for m in re.finditer(
            r'\b(?:public|private|protected|internal)\s+(?:static\s+|virtual\s+|override\s+|sealed\s+|abstract\s+|new\s+|async\s+)*'
            r'(?:[\w\<\>\[\]\.,\?]+\s+)?([A-Za-z_]\w*)\s*\(([^;{)]*)\)\s*(?:\{|=>|;)', code):
        name, plist = m.group(1), m.group(2)
        if name in NOISE or name in BCL_COMMON:
            continue
        nparams = len(split_args(plist)) if plist.strip() else 0
        decl[f][name].add(nparams)
        if 'params ' in plist:
            params_names.add(name)
        if '=' in plist:
            # 有默认值 → 允许少传
            for k in range(nparams):
                decl[f][name].add(k)

# 只看"在这批文件中被声明过"的名字，避免把 Unity/BCL 的方法误判
known = {}
for f, d in decl.items():
    for name, ar in d.items():
        known.setdefault(name, set()).update(ar)

# ---- 1b. 接口成员也是"声明"，但**没有访问修饰符**，上面的正则抓不到 ----
# 盲区举例：`ISaveStorage.SetValue(string,string,bool)` 被写成传 2 个实参，
# 是编译错误，但若接口成员不被视为声明，校验就会漏掉。
for f in TARGETS:
    code = strip(io.open(f, encoding='utf-8-sig', errors='replace').read())
    for m in re.finditer(r'\binterface\s+\w+[^{]*\{', code):
        # 花括号配对取出接口体
        depth = 0
        i = m.end() - 1
        while i < len(code):
            if code[i] == '{':
                depth += 1
            elif code[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = code[m.end():i]
        for sig in re.finditer(r'[\w\<\>\[\]\.,\?]+\s+(\w+)\s*\(([^;)]*)\)\s*;', body):
            name, plist = sig.group(1), sig.group(2)
            if name in NOISE or name in BCL_COMMON:
                continue
            nparams = len(split_args(plist)) if plist.strip() else 0
            known.setdefault(name, set()).add(nparams)
            if 'params ' in plist:
                params_names.add(name)
            if '=' in plist:
                for k in range(nparams):
                    known[name].add(k)

# ---- 1c. 按"类型"收集成员 --------------------------------------------------
# 【为什么必须这么做】早期版本只按"方法名"把 arity 合并成一个全局集合，于是：
#     · GameFlowManager 里的 `boardView.Build(Map, cellSize, origin, boardRoot)`
#       被拿去和 UIPrefabBuilder.Build()（0 参）比对；
#     · `PerfProbe.Ensure()` 被拿去和 SaveSchema.Ensure(IDatabase)（1 参）比对。
#   两者都是**同名但属于不同类**的误报。会误报的检查器和永远 PASS 的一样不可信，
#   所以这里按类型分开记录：只有当接收者确实解析到某个已知类型时才做判断。
TYPE_DECL_RE = re.compile(r'\b(?:class|struct|interface)\s+([A-Za-z_]\w*)[^{;]*\{')
MEMBER_SIG_RE = re.compile(
    r'\b(?:public|private|protected|internal)\s+'
    r'(?:static\s+|virtual\s+|override\s+|sealed\s+|abstract\s+|new\s+|async\s+)*'
    r'(?:[\w\<\>\[\]\.,\?]+\s+)?([A-Za-z_]\w*)\s*\(([^;{)]*)\)\s*(?:\{|=>|;)')

type_members = collections.defaultdict(lambda: collections.defaultdict(set))  # 类型名 -> 成员名 -> arities
type_names = set()
for f in TARGETS:
    code = strip(io.open(f, encoding='utf-8-sig', errors='replace').read())
    for tm in TYPE_DECL_RE.finditer(code):
        tname = tm.group(1)
        type_names.add(tname)
        # 花括号配对取出类型体
        depth = 0
        i = tm.end() - 1
        while i < len(code):
            if code[i] == '{':
                depth += 1
            elif code[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = code[tm.end():i]
        for mm in MEMBER_SIG_RE.finditer(body):
            nm, plist = mm.group(1), mm.group(2)
            if nm in NOISE or nm in BCL_COMMON:
                continue
            npar = len(split_args(plist)) if plist.strip() else 0
            type_members[tname][nm].add(npar)
            if 'params ' in plist:
                params_names.add(nm)
            if '=' in plist:
                for k in range(npar):
                    type_members[tname][nm].add(k)
        # 接口成员没有访问修饰符，MEMBER_SIG_RE 抓不到，单独补一遍
        if re.search(r'\binterface\s+' + re.escape(tname) + r'\b', code):
            for sig in re.finditer(r'[\w\<\>\[\]\.,\?]+\s+(\w+)\s*\(([^;)]*)\)\s*;', body):
                nm, plist = sig.group(1), sig.group(2)
                if nm in NOISE or nm in BCL_COMMON:
                    continue
                npar = len(split_args(plist)) if plist.strip() else 0
                type_members[tname][nm].add(npar)
                if 'params ' in plist:
                    params_names.add(nm)
                if '=' in plist:
                    for k in range(npar):
                        type_members[tname][nm].add(k)

# ---- 2. 扫描调用 ----
# 判定规则（保守，只报高置信度问题）：
#   · 无接收者  `Foo(...)`   → 只与**同文件**的声明比对
#   · 有接收者  `X.Foo(...)` → 仅当 X 是本批文件里声明过的**类型名**时，
#                              与"该类型自己的成员"比对；否则跳过
#     （接收者是字段/局部变量时，不解析它的声明类型 —— 宁可漏检也不误报）
#   · `params` / 有默认值的方法整名放行
BCL_TYPES = {
    'Encoding', 'Convert', 'Marshal', 'Math', 'Mathf', 'Array', 'Buffer', 'Enum', 'Guid',
    'File', 'Directory', 'Path', 'FileInfo', 'DirectoryInfo', 'Environment', 'BitConverter',
    'Debug', 'Application', 'JsonUtility', 'PlayerPrefs', 'SystemInfo', 'Interlocked',
    'Type', 'Activator', 'Resources', 'Time', 'Random', 'DateTime', 'TimeSpan',
    'string', 'String', 'List', 'Dictionary', 'HashSet', 'Enumerable', 'EqualityComparer',
    'Comparer', 'Object', 'Task', 'Thread', 'GC', 'Console', 'CultureInfo', 'StringBuilder',
}

problems = []
for f in TARGETS:
    raw = io.open(f, encoding='utf-8-sig', errors='replace').read()
    code = strip(raw)
    for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(', code):
        name = m.group(1)
        if name not in known or name in params_names:
            continue
        # 跳过声明行：该行从行首到匹配点之间出现访问修饰符
        line_start = code.rfind('\n', 0, m.start()) + 1
        line_prefix = code[line_start:m.start()]
        if re.search(r'\b(?:public|private|protected|internal)\b', line_prefix):
            continue

        # 确定"允许的实参个数集合"
        recv = re.search(r'([A-Za-z_]\w*)\s*\.\s*$', code[max(0, m.start() - 120):m.start()])
        if recv:
            head = recv.group(1)
            if head in BCL_TYPES:
                continue                        # 库方法（Encoding.GetString…），与本地同名方法无关
            if head not in type_names:
                continue                        # 接收者是字段/局部变量，不解析其类型 → 宁可漏检不误报
            allowed = type_members[head].get(name)
            if allowed is None:
                continue                        # 该类型未声明此成员（继承自别处）→ 无法判定
        else:
            allowed = decl.get(f, {}).get(name)
            if allowed is None:
                continue                        # 无接收者且同文件未声明 → 属于别处，不判定

        start = m.end() - 1
        depth = 0
        i = start
        while i < len(code):
            if code[i] == '(':
                depth += 1
            elif code[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        inner = code[start + 1:i]
        n = len(split_args(inner))
        if n not in allowed:
            # ★ 行号必须基于 code 计算：m.start() 是 **code**（已去注释/字符串）里的偏移，
            #   而 strip() 会删掉注释与字面量内容 —— 拿 raw 去数换行会整体错位
            #   （曾因此把 205 行的调用报成 155 行，排查时被指到完全无关的代码上）。
            line = code[:m.start()].count('\n') + 1
            problems.append((f, line, name, n, sorted(allowed)))

print('=' * 78)
print('调用参数个数校验（CS1501 / CS1729）')
print('  参与检查的本地方法名：%d 个' % len(known))
if problems:
    for f, line, name, n, allowed in problems:
        print('  FAIL  %s:%d  调用 %s(%d 个实参)，但本地声明只接受 %s 个'
              % (f, line, name, n, allowed))
else:
    print('  PASS  未发现参数个数不匹配的调用')
print()
print('RESULT:', 'FAIL' if problems else 'PASS')
sys.exit(1 if problems else 0)
