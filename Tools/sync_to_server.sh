#!/usr/bin/env bash
# ==============================================================================
# 把 Unity 构建出的热更产物同步到本机资源服务器目录 ServerRoot/
#
# 【为什么要这个脚本】Unity 的构建产物在 Bundles/ 下，服务器要读的是 ServerRoot/。
#   手工拷贝容易漏（尤其是新增 bundle、或版本号变了之后），所以固化成一个脚本。
#
# 【用法】
#   bash Tools/sync_to_server.sh                     # 同步默认版本（1.0.0）
#   bash Tools/sync_to_server.sh Android 1.0.1       # 指定平台与版本
#
# 【它会做三件事】
#   ① 把 Bundles/<平台>/FreeTower/<版本>/ 整个拷到 ServerRoot/<平台>/FreeTower/<版本>/
#   ② 把 Assets/StreamingAssets/HybridCLR/*.dll 拷到 ServerRoot/<平台>/HybridCLR/
#   ③ 打印清单，并提示哪些地址可以拿来验证
#
# ⚠️ 版本号必须与 Unity 构建时填的「资源包版本」一致，否则手机请求的目录不存在（404）。
#
# 【安全说明】本脚本**不做任何删除**，只做覆盖式拷贝（`cp -r .../.` + `cp -f`）。
#   之所以不用 `rm -f *` 清空目标目录：一旦 cd 失败，裸通配符会落到当前工作目录（工程根），
#   后果不可控。覆盖式拷贝的语义完全够用 —— 同名文件被最新产物覆盖，旧的多余文件留着无害
#   （手机只按新清单里的哈希去取，取不到的多余文件不会被请求）。
# ==============================================================================
set -euo pipefail

PLATFORM="${1:-Android}"
VERSION="${2:-1.0.0}"
PACKAGE="FreeTower"

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
SRC_AB="$PROJ/Bundles/$PLATFORM/$PACKAGE/$VERSION"
SRC_DLL="$PROJ/Assets/StreamingAssets/HybridCLR"
DST_AB="$PROJ/ServerRoot/$PLATFORM/$PACKAGE/$VERSION"
DST_DLL="$PROJ/ServerRoot/$PLATFORM/HybridCLR"

echo "==> 工程根目录 : $PROJ"
echo "==> 平台 / 版本: $PLATFORM / $VERSION"
echo

# ---- 前置检查（缺哪样就直接说清楚，别让它拷一半）-------------------------------
if [ ! -d "$SRC_AB" ]; then
  echo "[错误] 找不到资源包构建产物："
  echo "        $SRC_AB"
  echo "        请先在 Unity 里跑："
  echo "        Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 接入向导 ▸ ③ 构建真实资源包"
  echo "       （或在官方构建窗口里构建），并把「资源包版本」填成 $VERSION"
  exit 1
fi

if [ ! -d "$SRC_DLL" ]; then
  echo "[错误] 找不到热更 dll 目录：$SRC_DLL"
  echo "        请先在 Unity 里跑："
  echo "        Tools ▸ 塔防 ▸ HybridCLR ▸ 1. 拷贝热更 dll 到 StreamingAssets"
  exit 1
fi

# ---- ① 同步 AB 资源包（覆盖式，不删除）--------------------------------------
echo "==> ① 同步资源包（AB）"
mkdir -p "$DST_AB"
cp -r "$SRC_AB"/. "$DST_AB"/
echo "     目标：$DST_AB"
echo "     现有 $(ls -1 "$DST_AB" | wc -l) 个文件（源 $SRC_AB 有 $(ls -1 "$SRC_AB" | wc -l) 个）"

# ---- ② 同步热更 dll（覆盖式）------------------------------------------------
echo "==> ② 同步热更 dll"
mkdir -p "$DST_DLL"
cp -f "$SRC_DLL"/*.dll "$DST_DLL"/
echo "     目标：$DST_DLL  （$(ls -1 "$DST_DLL"/*.dll | wc -l) 个 dll）"

# ---- ③ 打印验证地址 ---------------------------------------------------------
echo
echo "==> 完成。服务器根目录 = $PROJ/ServerRoot"
echo
echo "    可用来验证的地址（启动资源服务器后，手机浏览器直接打开）："
echo "      http://<本机IP>:8000/$PLATFORM/$PACKAGE/$VERSION/FreeTower.version   ← 应显示 $VERSION"
echo "      http://<本机IP>:8000/$PLATFORM/$PACKAGE/$VERSION/                    ← 应列出所有 .bundle"
echo
echo "    当前 ServerRoot 目录结构："
find "$PROJ/ServerRoot" -maxdepth 3 -type d | sed 's|^|      |'
