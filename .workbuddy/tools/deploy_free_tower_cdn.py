#!/usr/bin/env python3
"""把某个版本的 FreeTower 资源包部署到热更服务器根目录（YooAsset HostPlayMode 布局）。

【为什么是"平铺在服务器根"，而不是 Android/FreeTower/版本/ 目录式】
  这是 2026-10-14 从 YooAsset 3.0.6 源码 + 模拟器实测双重确认的**实际请求路径**：
    版本文件  {ServerUrl}/FreeTower.version                （平铺，内容=版本号字符串）
    清单哈希  {ServerUrl}/FreeTower_{版本}.hash             （平铺）
    清单本体  {ServerUrl}/FreeTower_{版本}.bytes            （平铺）
    bundle    {ServerUrl}/{哈希}.bundle                     （构建用 EFileNameStyle.HashName
                                                             → 裸文件名，平铺根）
  其中 ServerUrl = ResServerConfig.ServerUrl（当前 = http://10.0.2.2:8000，
  指向 HotUpdateServer/ 这个真目录）。
  因此部署 = 把构建输出 Bundles/Android/FreeTower/{版本}/ 里的
    FreeTower.version、FreeTower_{版本}.hash、FreeTower_{版本}.bytes、*.bundle
    **以及无后缀的 32 位哈希文件**（YooAsset 内置特殊包 unitymonos / unityshaders
      的文件名就是裸哈希、不带 .bundle 后缀）全部拷到 HotUpdateServer/ 根。
  ★ 2026-10-16 实测教训：漏掉无后缀特殊包 → 跨版本热更时客户端请求
    {ServerUrl}/{哈希} 得到 404 → **main 场景加载失败**（unitymonos 是脚本资源包，
      凡组件类型集合有变化（如新增 TMP_Dropdown 引用）它的哈希就会变、必须重下）。

⚠️ 与此无关的旧结构：HotUpdateServer/Android/FreeTower（junction 到构建输出）只是
   "把构建目录挂出来看看"用的，HostPlayMode 运行时不请求它；dll 的
   Android/HybridCLR 链路（BootLoader 独立 HTTP）同样与本脚本无关。
   部署后可直接 curl 自检：{ServerUrl}/FreeTower.version 应返回版本号。

用法:
  python deploy_free_tower_cdn.py            # 自动取 Bundles 下最大版本
  python deploy_free_tower_cdn.py 1.0.13     # 指定版本
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # 工程根（.workbuddy/tools/xxx.py → 上三级）
BUILD_ROOT = ROOT / "Bundles" / "Android" / "FreeTower"
SERVER_ROOT = ROOT / "HotUpdateServer"


def pick_latest_version() -> str:
    versions = []
    for d in BUILD_ROOT.iterdir():
        if not d.is_dir():
            continue
        parts = d.name.split(".")
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            versions.append((tuple(int(p) for p in parts), d.name))
    if not versions:
        raise SystemExit("构建输出目录下没有任何 x.y.z 版本目录：" + str(BUILD_ROOT))
    return max(versions)[1]


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else pick_latest_version()
    src = BUILD_ROOT / version
    if not src.is_dir():
        raise SystemExit("版本目录不存在：" + str(src))

    copied = 0
    # 1) 版本号文件（客户端"请求最新版本"入口）
    (SERVER_ROOT / "FreeTower.version").write_text(version, encoding="ascii")
    copied += 1

    # 2) 清单 hash + 清单本体 + 全量 bundle（平铺；哈希命名天然不冲突，重复覆盖即可）
    for pattern in (f"FreeTower_{version}.hash", f"FreeTower_{version}.bytes", "*.bundle"):
        for f in sorted(src.glob(pattern)):
            shutil.copy2(f, SERVER_ROOT / f.name)
            copied += 1

    # 2b) 无后缀特殊包（unitymonos / unityshaders：文件名 = 裸 32 位小写哈希）。
    #     ★ 必须拷 —— 漏掉时跨版本热更会在加载场景时 404（2026-10-16 实测）。
    for f in sorted(src.iterdir()):
        if f.is_file() and re.fullmatch(r"[0-9a-f]{32}", f.name):
            shutil.copy2(f, SERVER_ROOT / f.name)
            copied += 1

    print(f"[deploy] 版本 {version} 部署完成：{copied} 个文件（版本号 + 清单 + 全量 bundle）")
    print(f"[deploy] 服务器根：{SERVER_ROOT}")
    print(f"[deploy] 自检：curl {SERVER_ROOT} 所在 http 服务的 /FreeTower.version（应返回 {version}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
