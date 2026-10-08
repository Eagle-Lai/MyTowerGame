#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校验 SqliteNative.cs 里所有 DllImport 的 EntryPoint，在随包的 libsqlite3.so
里真的被导出；并同时校验每个 .so 的 .meta（平台 / ABI 设置是否正确）。

    [1] 符号检查：源码里 26 个入口点 → .dynsym 里必须全部导出
        （少了 → 真机 EntryPointNotFoundException，编译期完全看不出来）
    [2] meta 检查：Android=enabled、CPU 与所在 ABI 目录一致、Any/Editor=disabled
        （meta 缺失 → Unity 自动生成默认设置，插件可能进不了 APK）

【为什么需要这个检查】
  沙箱里没有 C# 编译器，也没有 Unity，P/Invoke 的名字写错、或者升级 SQLite 版本后
  某个符号被裁掉，都只有"真机上运行到那一行"才会炸：
      EntryPointNotFoundException / DllNotFoundException
  这类错误无法用其它静态脚本发现，只能拿"源码里的名字"去比对"二进制里导出的符号"。

【检查方式】
  不依赖 llvm-readelf：自己解析 ELF 的 .dynsym / .dynstr（只读节头表即可）。

用法：
    python .workbuddy/tools/check_native_symbols.py
退出码：0 = 全部命中，1 = 有缺失。
"""

import os
import re
import struct
import sys

ROOT = r"D:\FreedomTower_1"
SRC = os.path.join(ROOT, "Assets", "Scripts", "Data", "Persistence", "SqliteNative.cs")
SOS = [
    os.path.join(ROOT, "Assets", "Plugins", "Android", "libs", "arm64-v8a", "libsqlite3.so"),
    os.path.join(ROOT, "Assets", "Plugins", "Android", "libs", "armeabi-v7a", "libsqlite3.so"),
]


# ---------------------------------------------------------------- 源码侧
def entry_points(path):
    """从 C# 源码里取出 DllImport(EntryPoint="xxx") 的名字。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        text = f.read()
    names = re.findall(r'EntryPoint\s*=\s*"([^"]+)"', text)
    # 去重但保持顺序
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


# ---------------------------------------------------------------- ELF 侧
class Elf:
    """极简 ELF 动态符号解析器（32/64 位、小端）。"""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        if self.data[:4] != b"\x7fELF":
            raise ValueError("不是 ELF 文件")
        self.is64 = self.data[4] == 2
        self.endian = "<" if self.data[5] == 1 else ">"

    def _u(self, fmt, off):
        return struct.unpack_from(self.endian + fmt, self.data, off)[0]

    def info(self):
        """返回 (class, machine, type) —— machine: 0x28=ARM, 0xB7=AArch64"""
        e_type = self._u("H", 16)
        e_machine = self._u("H", 18)
        cls = "ELF64" if self.is64 else "ELF32"
        mach = {0x28: "ARM", 0xB7: "AArch64", 0x3E: "x86-64", 0x03: "x86"}.get(
            e_machine, hex(e_machine)
        )
        typ = {1: "REL", 2: "EXEC", 3: "DYN"}.get(e_type, str(e_type))
        return cls, mach, typ

    def _sections(self):
        if self.is64:
            e_shoff = self._u("Q", 0x28)
            e_shentsize = self._u("H", 0x3A)
            e_shnum = self._u("H", 0x3C)
            e_shstrndx = self._u("H", 0x3E)
        else:
            e_shoff = self._u("I", 0x20)
            e_shentsize = self._u("H", 0x2E)
            e_shnum = self._u("H", 0x30)
            e_shstrndx = self._u("H", 0x32)

        raw = []
        for i in range(e_shnum):
            off = e_shoff + i * e_shentsize
            if self.is64:
                name, typ, flags, addr, offset, size, link, info, align, entsize = struct.unpack_from(
                    self.endian + "IIQQQQIIQQ", self.data, off
                )
            else:
                name, typ, flags, addr, offset, size, link, info, align, entsize = struct.unpack_from(
                    self.endian + "IIIIIIIIII", self.data, off
                )
            raw.append(dict(name=name, type=typ, offset=offset, size=size,
                            link=link, entsize=entsize))

        # 节名表
        shstr = raw[e_shstrndx]
        base = shstr["offset"]
        for s in raw:
            end = self.data.index(b"\0", base + s["name"])
            s["sname"] = self.data[base + s["name"]:end].decode("ascii", "replace")
        return raw

    def dynamic_symbols(self):
        """返回 .dynsym 里所有"有名字"的符号（含 UNDEFINED，调用方自己筛）。"""
        secs = self._sections()
        dynsym = next((s for s in secs if s["sname"] == ".dynsym"), None)
        if dynsym is None:
            return []
        dynstr = secs[dynsym["link"]]
        strtab = dynstr["offset"]

        out = []
        count = dynsym["size"] // dynsym["entsize"] if dynsym["entsize"] else 0
        for i in range(count):
            off = dynsym["offset"] + i * dynsym["entsize"]
            if self.is64:
                st_name, st_info, st_other, st_shndx, st_value, st_size = struct.unpack_from(
                    self.endian + "IBBHQQ", self.data, off
                )
            else:
                st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
                    self.endian + "IIIBBH", self.data, off
                )
            if st_name == 0:
                continue
            end = self.data.index(b"\0", strtab + st_name)
            name = self.data[strtab + st_name:end].decode("ascii", "replace")
            out.append((name, st_shndx, (st_info >> 4) & 0xF))
        return out


# ---------------------------------------------------------------- meta 侧
# 目录名 → Unity Plugin Inspector 里该选的 CPU
EXPECTED_CPU = {"arm64-v8a": "ARM64", "armeabi-v7a": "ARMv7",
                "x86": "X86", "x86_64": "X86_64"}


def _parse_meta_regex(text):
    """不依赖 pyyaml 的兜底解析：把 platformData 里每个平台块的 enabled/settings 抠出来。"""
    plat = {}
    # 每个条目形如：
    #   - first:
    #       Android: Android
    #     second:
    #       enabled: 1
    #       settings:
    #         CPU: ARM64
    pat = re.compile(
        r"-\s*first:\s*\n\s*([A-Za-z ]+):[^\n]*\n\s*second:\s*\n"
        r"\s*enabled:\s*([01])\s*\n"
        r"(?:\s*settings:\s*(?:\{\}|(?:\n(?:\s+[A-Za-z_]+:[^\n]*\n?)*)))?"
    )
    for m in pat.finditer(text):
        name = m.group(1).strip()
        block = m.group(0)
        cpu = re.search(r"CPU:\s*([A-Za-z0-9_]+)", block)
        plat[name] = {"enabled": int(m.group(2)),
                      "settings": {"CPU": cpu.group(1)} if cpu else {}}
    return plat


def check_meta(so_path, verbose=True):
    """校验 .so.meta：存在、Android 启用、CPU 与 ABI 目录一致、Any/Editor 关闭。"""
    meta = so_path + ".meta"
    abi = os.path.basename(os.path.dirname(so_path))
    want = EXPECTED_CPU.get(abi)
    problems = []

    if want is None:
        return ["ABI 目录名 '%s' 不认识（可用的：%s）"
                % (abi, ", ".join(sorted(EXPECTED_CPU)))], {}

    if not os.path.isfile(meta):
        return ["缺少 %s —— Unity 会自行生成默认设置，插件可能进不了 APK"
                % os.path.basename(meta)], {}

    with open(meta, "r", encoding="utf-8-sig") as f:
        text = f.read()
    try:
        import yaml
        data = yaml.safe_load(text)
        plat = {}
        for e in data["PluginImporter"]["platformData"]:
            k = list(e["first"].keys())[0]
            plat[k] = e["second"] or {}
        info = {"guid": data.get("guid", "")}
    except Exception:
        plat = _parse_meta_regex(text)
        g = re.search(r"guid:\s*(\w{32})", text)
        info = {"guid": g.group(1) if g else ""}

    if len(info.get("guid", "")) != 32:
        problems.append("guid 不是 32 位十六进制")

    any_on = (plat.get("Any") or {}).get("enabled", 0) == 1
    ed_on = (plat.get("Editor") or {}).get("enabled", 0) == 1
    andr = plat.get("Android") or {}
    got_cpu = (andr.get("settings") or {}).get("CPU")

    if any_on:
        problems.append("Any 平台被启用（会把 Android .so 塞进所有平台）")
    if ed_on:
        problems.append("Editor 平台被启用（编辑器会尝试加载 Android .so 而失败）")
    if andr.get("enabled", 0) != 1:
        problems.append("Android 平台未启用（插件不会被打进 APK）")
    if got_cpu != want:
        problems.append("CPU 是 %r，但所在目录是 %s，应为 %r" % (got_cpu, abi, want))

    if verbose:
        print("    meta: Android=%s CPU=%s  Any=%s Editor=%s  guid=%s"
              % (andr.get("enabled", 0), got_cpu, int(any_on), int(ed_on),
                 info.get("guid", "?")))
    return problems, info


def main():
    if not os.path.isfile(SRC):
        print("找不到源码：" + SRC)
        return 1
    need = entry_points(SRC)
    print("SqliteNative.cs 中的 DllImport 入口点：%d 个" % len(need))
    for n in need:
        print("    " + n)
    missing_so = [p for p in SOS if not os.path.isfile(p)]
    if missing_so:
        print("\n缺少 .so 文件：")
        for p in missing_so:
            print("    " + p)
        return 1

    ok = True
    for path in SOS:
        print("\n--- " + os.path.relpath(path, ROOT))
        elf = Elf(path)
        cls, mach, typ = elf.info()
        print("    %s / %s / %s" % (cls, mach, typ))

        # ARMv7 浮点 ABI：BindDouble 传 double，hard-float 会让参数静默错位
        if mach == "ARM":
            e_flags = elf._u("I", 0x24)
            if e_flags & 0x400:
                ok = False
                print("    ✗ e_flags=0x%08X 是 hard-float，"
                      "Android armeabi-v7a 要求 softfp！" % e_flags)
            else:
                print("    ✓ softfp（EF_ARM_ABI_FLOAT_SOFT），符合 armeabi-v7a ABI")

        syms = elf.dynamic_symbols()
        exported = set(n for (n, shndx, bind) in syms if shndx != 0)  # 已定义 = 导出
        all_sqlite = sorted(n for n in exported if n.startswith("sqlite3_"))
        print("    导出 sqlite3_* 符号 %d 个" % len(all_sqlite))
        miss = [n for n in need if n not in exported]
        if miss:
            ok = False
            print("    ✗ 缺失 %d 个：" % len(miss))
            for n in miss:
                print("        " + n)
        else:
            print("    ✓ 所需 %d 个符号全部导出" % len(need))

        problems, _ = check_meta(path)
        for p in problems:
            ok = False
            print("    ✗ meta: " + p)

    print("\n" + ("PASS 原生库符号 / ABI / .meta 全部正确" if ok
                  else "FAIL 上面有问题需要修"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
