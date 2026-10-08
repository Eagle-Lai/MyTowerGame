# -*- coding: utf-8 -*-
"""
扫描 Assets/Audio/ 生成 Assets/Scripts/Data/AudioCatalog.cs（M2-W6）。

【为什么用"生成代码"而不是运行时扫描】
  与 gen_monster_catalog.py 同一个理由：ResTable 是资源寻址的唯一数据源，
  它要在**运行时**就能枚举全部逻辑名（预加载、AB 打标、自检都依赖它）。
  运行时扫描目录在真机 AB 模式下根本做不到（文件都在包里）。

【幂等】重复执行结果一致；没有音频文件时生成空清单（工程当前就是这种状态）。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 【为什么按 __file__ 推导】见 apply_m2_audio_table.py 的同类说明：
# 硬编码绝对路径在换机器时会静默扫错目录。三级 dirname 回到工程根。
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIO_DIR = os.path.join(ROOT, "Assets/Audio")
OUT_FILE = os.path.join(ROOT, "Assets/Scripts/Data/AudioCatalog.cs")
EXTS = (".wav", ".ogg", ".mp3", ".aiff", ".aif")


def scan():
    found = []
    if not os.path.isdir(AUDIO_DIR):
        return found
    for dirpath, _dirnames, filenames in os.walk(AUDIO_DIR):
        for fn in filenames:
            if fn.startswith("."):
                continue
            name, ext = os.path.splitext(fn)
            if ext.lower() not in EXTS:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            found.append((name, rel))
    found.sort(key=lambda x: x[0].lower())
    return found


def wrap(items, indent="            ", per_line=4):
    if not items:
        return ""
    lines = []
    for i in range(0, len(items), per_line):
        chunk = items[i:i + per_line]
        lines.append(indent + " ".join(chunk))
    return "\n".join(lines)


def build(items):
    names = ['"%s",' % n for n, _ in items]
    paths = ['"%s",' % p for _, p in items]
    return '''// =============================================================================
// 本文件由工具自动生成，请勿手改。
//   生成脚本：.workbuddy/tools/gen_audio_catalog.py
//   运行方式：python .workbuddy/tools/gen_audio_catalog.py
//
// 数据来源：Assets/Audio/ 下的音频文件（.wav / .ogg / .mp3 / .aiff）
// 当前数量：%d
//
// 【为什么需要一个"生成的清单"】
//   ResTable 是资源寻址的唯一数据源，而它需要在**运行时**就能枚举逻辑名。
//   手写清单会跟实际文件分叉（加了音频忘了登记 → 静默无声），
//   所以与怪物一样改成扫描目录生成。
//
// 【放音频文件后要做什么】
//   把文件丢进 Assets/Audio/，跑一次本生成器即可 —— 代码一行都不用改。
// =============================================================================

namespace FTProject
{
    /// <summary>音频清单（生成代码）。逻辑名 = "Audio_" + 文件名（不含扩展名）。</summary>
    public static class AudioCatalog
    {
        /// <summary>文件名（不含扩展名），与 TBAudio.logicalName 一一对应</summary>
        public static readonly string[] Names =
        {
%s
        };

        /// <summary>资源路径（Assets/Audio/xxx.wav），下标与 Names 一一对应</summary>
        public static readonly string[] AssetPaths =
        {
%s
        };

        public static int Count { get { return Names.Length; } }

        /// <summary>逻辑名：Audio_&lt;文件名&gt;（与 TBAudio.logicalName 拼前缀后一致）</summary>
        public static string LogicalName(int i)
        {
            return "Audio_" + Names[i];
        }
    }
}
''' % (len(items), wrap(names), wrap(paths))


if __name__ == "__main__":
    items = scan()
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(build(items))
    print("扫描目录:", AUDIO_DIR)
    print("找到音频文件: %d" % len(items))
    for n, p in items[:10]:
        print("   ", n, "->", p)
    print("已写出:", OUT_FILE)
