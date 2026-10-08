#!/usr/bin/env bash
# ==============================================================================
# 为 Android 交叉编译 libsqlite3.so，输出到 Assets/Plugins/Android/libs/<abi>/
#
# 【为什么要自带这份 .so】
#   Android 系统里确实有 /system/lib64/libsqlite3.so，但它属于**平台私有库**；
#   应用 targetSdk >= 24 时链接器会拒绝 dlopen 非公开 NDK 库 —— 是"加载失败"，
#   不是"版本旧"。所以必须随包带一份自己的。
#
# 【与工程配置的对应关系】
#   PlayerSettings → AndroidTargetArchitectures = ARMv7 | ARM64
#   → 只需要 arm64-v8a 与 armeabi-v7a 两个 ABI。
#   若将来加了 x86_64（模拟器常见），把 TARGETS 里补一行即可。
#
# 用法：
#   bash Tools/build_android_sqlite.sh
#
# 依赖：curl / unzip（Git Bash 自带）、python3 或 python（用于解压）。
# 已在 Windows + Git Bash 下实测通过。
# ==============================================================================
set -euo pipefail

SQLITE_VER="3500200"                 # SQLite 3.50.2
SQLITE_YEAR="2025"
NDK_VER="r25c"                       # 支持 minSdk 19+；本工程 AndroidMinSdkVersion=22
ANDROID_API=22                       # ★ 必须与 AndroidMinSdkVersion 一致

WORK="${TMPDIR:-/tmp}/ftsqlite-build"
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$PROJ/Assets/Plugins/Android/libs"

PY=""
for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || { echo "找不到 python，无法解压"; exit 1; }

mkdir -p "$WORK"; cd "$WORK"

# ---- 1) SQLite 官方 amalgamation -------------------------------------------
if [ ! -f "sqlite-amalgamation-$SQLITE_VER/sqlite3.c" ]; then
  echo "==> 下载 SQLite amalgamation $SQLITE_VER"
  curl -L --retry 5 -o sqlite.zip \
    "https://www.sqlite.org/$SQLITE_YEAR/sqlite-amalgamation-$SQLITE_VER.zip"
  "$PY" -c "import zipfile;zipfile.ZipFile('sqlite.zip').extractall('.')"
fi

# ---- 2) Android NDK --------------------------------------------------------
NDK_DIR="$WORK/android-ndk-$NDK_VER"
if [ ! -d "$NDK_DIR" ]; then
  echo "==> 下载 Android NDK $NDK_VER（约 445MB；国内可换腾讯云镜像）"
  NDK_URL="https://dl.google.com/android/repository/android-ndk-$NDK_VER-windows.zip"
  # 国内网络建议改用：https://mirrors.cloud.tencent.com/AndroidSDK/android-ndk-$NDK_VER-windows.zip
  curl -L --retry 5 -C - -o ndk.zip "$NDK_URL"
  "$PY" -c "import zipfile;zipfile.ZipFile('ndk.zip').extractall('.')"
fi

BIN="$NDK_DIR/toolchains/llvm/prebuilt/windows-x86_64/bin"
[ -d "$BIN" ] || BIN="$NDK_DIR/toolchains/llvm/prebuilt/linux-x86_64/bin"   # 非 Windows 主机

# ---- 3) 编译 ---------------------------------------------------------------
# SQLITE_OMIT_LOAD_EXTENSION : 不加载扩展 → 少一个 dlopen 依赖，体积更小
# SQLITE_DQS=0               : 禁止双引号当字符串（避免把标识符误写成字符串却不报错）
# HAVE_USLEEP=1              : 忙等退避，Android 上更省电
CFLAGS="-shared -O2 -fPIC -DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_DQS=0 -DHAVE_USLEEP=1 \
        -Wl,-soname,libsqlite3.so -s"

build_abi() {  # $1=abi 目录名  $2=clang 前缀
  echo "==> 编译 $1"
  mkdir -p "$OUT/$1"
  ( cd "sqlite-amalgamation-$SQLITE_VER" && \
    "$BIN/$2${ANDROID_API}-clang" $CFLAGS -o "$OUT/$1/libsqlite3.so" sqlite3.c )
  ls -l "$OUT/$1/libsqlite3.so"
}

build_abi arm64-v8a    aarch64-linux-android
build_abi armeabi-v7a  armv7a-linux-androideabi

# ---- 4) 校验：ELF 机器类型 + 我方 P/Invoke 所需符号 -------------------------
echo "==> 校验"
READELF="$BIN/llvm-readelf.exe"; [ -f "$READELF" ] || READELF="$BIN/llvm-readelf"
for abi in arm64-v8a armeabi-v7a; do
  echo "--- $abi"
  "$READELF" -h "$OUT/$abi/libsqlite3.so" | grep -E "Class|Machine|Type:"
  for s in sqlite3_open_v2 sqlite3_prepare_v2 sqlite3_step sqlite3_bind_text \
           sqlite3_column_bytes sqlite3_close_v2 sqlite3_libversion; do
    "$READELF" --dyn-syms "$OUT/$abi/libsqlite3.so" | grep -q "$s" \
      && echo "    ok  $s" || { echo "    缺失 $s"; exit 1; }
  done
done

echo
echo "完成。产物已就位："
echo "  $OUT/arm64-v8a/libsqlite3.so"
echo "  $OUT/armeabi-v7a/libsqlite3.so"
echo
echo "⚠️ 提醒：libsqlite3.so.meta 里的 Android CPU 设置需与 ABI 目录一致"
echo "   （arm64-v8a → CPU: ARM64，armeabi-v7a → CPU: ARMv7）。"
