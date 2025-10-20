#!/usr/bin/env bash

set -euo pipefail

# 进入脚本所在目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查并激活虚拟环境
VENV_DIR="$SCRIPT_DIR/.venv"
if [ -d "$VENV_DIR" ]; then
    echo "[info] 检测到虚拟环境: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "[info] 已激活虚拟环境"
else
    echo "[warn] 未找到虚拟环境 .venv，使用系统 Python"
fi

APP_NAME="client_gui"
OUTPUT_DIR="$SCRIPT_DIR/${APP_NAME}.build"

echo "[info] Python: $(python3 -V)"
echo "[info] Python 路径: $(which python3)"
echo "[info] Nuitka: $(python3 -m nuitka --version || true)"

# 如需安装 Command Line Tools（若未装），请先运行： xcode-select --install

echo "[step] 清理旧构建输出: $OUTPUT_DIR"
rm -rf "$OUTPUT_DIR"

echo "[step] 使用 Nuitka 构建 macOS .app（独立运行，打包 config.ini）"
python3 -m nuitka \
  --standalone \
  --macos-create-app-bundle \
  --enable-plugin=pyqt5 \
  --assume-yes-for-downloads \
  --static-libpython=no \
  --include-data-file="$SCRIPT_DIR/config.ini=config.ini" \
  --clang \
  --output-dir="$OUTPUT_DIR" \
  "$SCRIPT_DIR/${APP_NAME}.py"

echo "[done] 构建完成。产物目录: $OUTPUT_DIR"
echo "[hint] 应用路径: $OUTPUT_DIR/${APP_NAME}.app"
echo "[hint] 如需运行: open \"$OUTPUT_DIR/${APP_NAME}.app\""

# 说明：
# - config.ini 已打包进应用（位于可执行文件同目录）。
# - 如需修改配置，需重新打包或在应用外部放置 config.ini 覆盖。
# - 如需自定义图标，可准备 icon.icns 并添加 --macos-app-icon=icon.icns 参数。


