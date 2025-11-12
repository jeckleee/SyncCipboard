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

# 源代码文件名（固定）
SOURCE_FILE="client_gui"

# 从 config.ini 读取应用信息
if [ -f "$SCRIPT_DIR/config.ini" ]; then
    APP_DISPLAY_NAME=$(grep -E "^app_name\s*=" "$SCRIPT_DIR/config.ini" | cut -d'=' -f2 | xargs)
    APP_VERSION=$(grep -E "^app_version\s*=" "$SCRIPT_DIR/config.ini" | cut -d'=' -f2 | xargs)
    APP_ICON_PATH=$(grep -E "^app_icon\s*=" "$SCRIPT_DIR/config.ini" | cut -d'=' -f2 | sed 's/;.*//' | xargs)
else
    APP_DISPLAY_NAME="SyncClipboard"
    APP_VERSION="1.0.0"
    APP_ICON_PATH=""
fi

# 构建输出目录使用源文件名
BUILD_DIR="$SCRIPT_DIR/${SOURCE_FILE}.build"
# 最终应用名称使用配置的名称
APP_NAME="${APP_DISPLAY_NAME}"

echo "[info] Python: $(python3 -V)"
echo "[info] Python 路径: $(which python3)"
echo "[info] Nuitka: $(python3 -m nuitka --version || true)"
echo "[info] 应用名称: $APP_NAME"
echo "[info] 应用版本: $APP_VERSION"

# 如需安装 Command Line Tools（若未装），请先运行： xcode-select --install

echo "[step] 清理旧构建输出: $BUILD_DIR"
rm -rf "$BUILD_DIR"

echo "[step] 使用 Nuitka 构建 macOS .app（独立运行，打包 config.ini）"

# 构建 Nuitka 命令参数
NUITKA_ARGS=(
  --standalone
  --macos-create-app-bundle
  --enable-plugin=pyqt5
  --assume-yes-for-downloads
  --static-libpython=no
  --include-data-file="$SCRIPT_DIR/config.ini=config.ini"
  --clang
  --output-dir="$BUILD_DIR"
)

# 如果图标文件存在，将其作为运行时资源打包（用于托盘图标）
if [ -n "$APP_ICON_PATH" ] && [ -f "$SCRIPT_DIR/$APP_ICON_PATH" ]; then
  echo "[info] 打包托盘图标资源: $APP_ICON_PATH"
  NUITKA_ARGS+=(--include-data-file="$SCRIPT_DIR/$APP_ICON_PATH=$APP_ICON_PATH")
fi

# 如果配置了应用名称，添加参数
if [ -n "$APP_DISPLAY_NAME" ]; then
  NUITKA_ARGS+=(--macos-app-name="$APP_DISPLAY_NAME")
fi

# 如果配置了应用版本，添加参数
if [ -n "$APP_VERSION" ]; then
  NUITKA_ARGS+=(--macos-app-version="$APP_VERSION")
fi

# 如果配置了图标文件且存在，添加参数
if [ -n "$APP_ICON_PATH" ] && [ -f "$SCRIPT_DIR/$APP_ICON_PATH" ]; then
  echo "[info] 使用应用图标: $APP_ICON_PATH"
  NUITKA_ARGS+=(--macos-app-icon="$SCRIPT_DIR/$APP_ICON_PATH")
else
  echo "[warn] 未配置应用图标或图标文件不存在，使用默认图标"
fi

# 执行构建
python3 -m nuitka "${NUITKA_ARGS[@]}" "$SCRIPT_DIR/${SOURCE_FILE}.py"

# 构建完成后，重命名 .app 文件
TEMP_APP="$BUILD_DIR/${SOURCE_FILE}.app"
FINAL_APP="$BUILD_DIR/${APP_NAME}.app"

if [ -d "$TEMP_APP" ]; then
    if [ "$TEMP_APP" != "$FINAL_APP" ]; then
        echo "[step] 重命名应用: ${SOURCE_FILE}.app -> ${APP_NAME}.app"
        rm -rf "$FINAL_APP"  # 删除旧的（如果存在）
        mv "$TEMP_APP" "$FINAL_APP"
    fi
fi

echo "[done] 构建完成！"
echo "[info] 应用名称: $APP_NAME"
echo "[info] 应用版本: $APP_VERSION"
echo "[info] 产物目录: $BUILD_DIR"
echo "[info] 应用路径: $FINAL_APP"
echo "[hint] 运行命令: open \"$FINAL_APP\""

# 说明：
# - config.ini 已打包进应用（位于可执行文件同目录）。
# - 如需修改配置，需重新打包或在应用外部放置 config.ini 覆盖。
# - 如需自定义图标，可准备 icon.icns 并添加 --macos-app-icon=icon.icns 参数。


