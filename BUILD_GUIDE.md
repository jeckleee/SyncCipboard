# 快速构建指南

## 🚀 一键构建 macOS 应用

### 1️⃣ 准备环境

确保已安装必要工具：

```bash
# 安装 Xcode Command Line Tools（必需）
xcode-select --install

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（如果还没有安装）
pip install -r requirements.txt
pip install nuitka zstandard ordered-set
```

### 2️⃣ 修改配置（可选）

在打包前修改 `config.ini`：

```ini
[client]
server_url = http://YOUR_SERVER_IP:8000  # 修改为实际服务器地址
sync_interval = 1
enable_sound = true
enable_popup = true
```

### 3️⃣ 执行构建

```bash
./build_macos.sh
```

构建过程大约需要 **1-2 分钟**，完成后会显示：

```
[done] 构建完成。产物目录: /path/to/client_gui.build
[hint] 应用路径: /path/to/client_gui.build/client_gui.app
[hint] 如需运行: open "/path/to/client_gui.build/client_gui.app"
```

### 4️⃣ 运行应用

```bash
open client_gui.build/client_gui.app
```

或双击 `client_gui.app` 启动。

## 📦 产物说明

- **应用位置**：`client_gui.build/client_gui.app`
- **应用大小**：约 60-80 MB（包含 Python 运行时和所有依赖）
- **配置文件**：已内置在 `Contents/MacOS/config.ini`
- **架构**：arm64 (Apple Silicon)

## 🔄 重新构建

修改代码或配置后，只需再次运行：

```bash
./build_macos.sh
```

脚本会自动清理旧的构建输出并重新编译。

## 📤 分发给其他用户

### 方法 1：直接分发 .app

```bash
# 压缩应用包
cd client_gui.build
zip -r ../SyncClipboard-macOS.zip client_gui.app

# 将 SyncClipboard-macOS.zip 发送给用户
```

用户下载后：
1. 解压得到 `client_gui.app`
2. 如遇到"无法打开"提示，运行：`xattr -cr client_gui.app`
3. 双击运行

### 方法 2：创建 DMG 安装包

```bash
# 安装 create-dmg 工具
brew install create-dmg

# 创建 DMG
create-dmg \
  --volname "剪贴板同步客户端" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --app-drop-link 450 150 \
  SyncClipboard-Installer.dmg \
  client_gui.build/client_gui.app
```

## 🛠️ 修改打包后的配置

如果需要修改已打包应用的配置：

```bash
# 直接编辑
vim client_gui.build/client_gui.app/Contents/MacOS/config.ini

# 或复制新配置覆盖
cp my_new_config.ini client_gui.build/client_gui.app/Contents/MacOS/config.ini
```

## ❓ 常见问题

### Q: "无法打开，因为来自身份不明的开发者"
**A:** 运行以下命令移除隔离属性：
```bash
xattr -cr client_gui.build/client_gui.app
```

### Q: 构建失败，提示找不到 libpython
**A:** 确保使用虚拟环境中的 Python，并且构建脚本已添加 `--static-libpython=no` 参数。

### Q: 应用启动后没有托盘图标
**A:** 这是正常的，因为未指定应用图标。可以准备 `icon.icns` 并在 `build_macos.sh` 中添加：
```bash
--macos-app-icon=icon.icns
```

### Q: 如何验证配置文件是否打包成功？
**A:** 检查应用内是否包含配置文件：
```bash
ls -lh client_gui.build/client_gui.app/Contents/MacOS/config.ini
```

### Q: 如何查看应用运行日志？
**A:** 从终端启动应用：
```bash
./client_gui.build/client_gui.app/Contents/MacOS/client_gui
```
日志会输出到终端。

## 📚 更多信息

详细的打包说明和高级用法，请参阅：[PACKAGING.md](PACKAGING.md)

