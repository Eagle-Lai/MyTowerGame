#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_native_symbols.py 的「守卫有效性」回归测试。

【为什么必须有这个文件】
  本工程刚吃过一次亏：`check_code.py` 因为 ROOT 指向了旧路径，
  实际扫描 0 个文件，却每次都打印 PASS —— 一个"永远通过"的检查等于没有检查。
  所以任何新建的静态守卫，都必须用「故意注入故障」的方式证明它真的会 FAIL。

本测试对 check_meta() 注入 6 种故障，逐一确认能被报出来；
外加 1 个正常对照组，确认它不会无脑报错。

用法：
    python .workbuddy/tools/test_native_symbols_guard.py
退出码：0 = 守卫有效，1 = 有漏报（守卫不可信）。
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))

import check_native_symbols as C  # noqa: E402

GOOD_META = os.path.join(
    ROOT, "Assets", "Plugins", "Android", "libs", "arm64-v8a", "libsqlite3.so.meta"
)


def load_good():
    with open(GOOD_META, "r", encoding="utf-8") as f:
        return f.read()


def mutate(text, old, new, label):
    """替换必须真的发生，否则用例本身失效（而不是守卫通过）。"""
    if old not in text:
        raise AssertionError("用例「%s」的注入锚点没匹配上，用例无效：%r" % (label, old))
    out = text.replace(old, new, 1)
    assert out != text, "用例「%s」替换后内容未变化" % label
    return out


def run():
    good = load_good()

    # Android 段与 Editor 段的锚点
    A_OLD = "      Android: Android\n    second:\n      enabled: 1"
    A_NEW_OFF = "      Android: Android\n    second:\n      enabled: 0"
    E_OLD = "      Editor: Editor\n    second:\n      enabled: 0"
    E_NEW_ON = "      Editor: Editor\n    second:\n      enabled: 1"
    ANY_OLD = "      Any: \n    second:\n      enabled: 0"
    ANY_NEW_ON = "      Any: \n    second:\n      enabled: 1"

    cases = [
        ("① 正常 meta（对照组，应无问题）",
         good, "arm64-v8a", []),
        ("② CPU 与目录不符",
         mutate(good, "CPU: ARM64", "CPU: ARMv7", "CPU 写错"),
         "arm64-v8a", ["CPU"]),
        ("③ Android 平台被关掉",
         mutate(good, A_OLD, A_NEW_OFF, "关掉 Android"),
         "arm64-v8a", ["Android 平台未启用"]),
        ("④ Any 平台被打开",
         mutate(good, ANY_OLD, ANY_NEW_ON, "打开 Any"),
         "arm64-v8a", ["Any 平台被启用"]),
        ("⑤ Editor 平台被打开",
         mutate(good, E_OLD, E_NEW_ON, "打开 Editor"),
         "arm64-v8a", ["Editor 平台被启用"]),
        ("⑥ ABI 目录名不认识",
         good, "riscv64", ["ABI 目录名"]),
        ("⑦ meta 文件整个缺失",
         None, "arm64-v8a", ["缺少"]),
    ]

    base = tempfile.mkdtemp(prefix="ftguard_")
    fails = []
    try:
        for i, (name, content, abi, expect) in enumerate(cases):
            d = os.path.join(base, "case%d" % i, abi)
            os.makedirs(d, exist_ok=True)
            so = os.path.join(d, "libsqlite3.so")
            if content is not None:
                with open(so + ".meta", "w", encoding="utf-8", newline="") as f:
                    f.write(content)

            problems, _ = C.check_meta(so, verbose=False)

            if expect:
                hit = all(any(e in p for p in problems) for e in expect)
            else:
                hit = len(problems) == 0
            print(("  [OK] " if hit else "  [!!] ") + name)
            print("        -> " + ("、".join(problems) if problems else "无问题"))
            if not hit:
                fails.append(name)
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print()
    if fails:
        print("守卫无效！以下 %d 个故障未被报出：" % len(fails))
        for f in fails:
            print("    " + f)
        return 1
    print("守卫有效：%d 个用例全部符合预期（对照组不误报，故障组能报出）" % len(cases))
    return 0


if __name__ == "__main__":
    sys.exit(run())
