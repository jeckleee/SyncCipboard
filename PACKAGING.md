# macOS 应用打包说明

## 📦 使用 Nuitka 打包为 macOS .app

### 前置要求

1. **Xcode Command Line Tools**（必需）
   ```bash
   xcode-select --install
   ```

2. **Python 虚拟环境**（推荐）
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install nuitka zstandard ordered-set
   ```

### 一键构建

项目提供了自动化构建脚本 `build_macos.sh`：

```bash
./build_macos.sh
```

该脚本会：
- 自动检测并激活虚拟环境（`.venv`）
- 清理旧的构建输出
- 使用 Nuitka 编译生成独立的 macOS 应用包
- 输出应用路径供后续使用

### 手动构建（可选）

如果需要自定义构建选项：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行 Nuitka 构建
python3 -m nuitka \
  --standalone \
  --macos-create-app-bundle \
  --enable-plugin=pyqt5 \
  --assume-yes-for-downloads \
  --static-libpython=no \
  --clang \
  --output-dir=client_gui.build \
  client_gui.py
```

### 构建产物

构建完成后，应用包位于：
```
client_gui.build/client_gui.app
```

应用结构：
```
client_gui.app/
├── Contents/
│   ├── MacOS/
│   │   ├── client_gui        # 主可执行文件 (~12MB)
│   │   ├── Python            # Python 运行时
│   │   ├── PyQt5/            # Qt 框架和插件
│   │   └── ...               # 其他依赖库
│   ├── Info.plist            # 应用元数据
│   └── _CodeSignature/       # 代码签名信息
```

## 🚀 运行应用

### 方法 1：双击运行
在 Finder 中找到 `client_gui.app`，双击即可启动。

### 方法 2：命令行运行
```bash
open client_gui.build/client_gui.app
```

### 方法 3：直接执行二进制
```bash
./client_gui.build/client_gui.app/Contents/MacOS/client_gui
```

## ⚙️ 配置文件说明

**重要**：`config.ini` 文件已**打包**进应用中（位于 `Contents/MacOS/config.ini`）。

### 配置文件读取优先级
应用会按以下优先级查找 `config.ini`：
1. **可执行文件所在目录**（打包后：`client_gui.app/Contents/MacOS/config.ini`）
2. **当前工作目录**（开发时：项目根目录的 `config.ini`）
3. **脚本所在目录**（开发时备用）

### 修改配置方式

#### 方法 1：修改打包前的配置（推荐）
在打包前修改项目根目录的 `config.ini`，然后重新运行 `./build_macos.sh`。

#### 方法 2：替换打包后的配置
```bash
# 直接修改应用内的配置文件
vim client_gui.build/client_gui.app/Contents/MacOS/config.ini

# 或复制新配置文件覆盖
cp my_config.ini client_gui.build/client_gui.app/Contents/MacOS/config.ini
```

### 默认配置内容
```ini
[server]
host = 0.0.0.0
port = 8000

[client]
server_url = http://127.0.0.1:8000
sync_interval = 1
enable_sound = true
enable_popup = true
```

### 分发建议
```
发布包/
├── client_gui.app          # 应用本体（已内置 config.ini）
└── README.txt              # 使用说明（含修改配置的方法）
```

## 📋 分发与部署

### 本地测试
```bash
# 复制应用到应用程序文件夹
cp -r client_gui.build/client_gui.app /Applications/

# 运行
open /Applications/client_gui.app
```

### 打包分发
```bash
# 创建分发包
mkdir -p dist_package
cp -r client_gui.build/client_gui.app dist_package/
cp config.ini dist_package/
cp README.md dist_package/README.txt

# 压缩
cd dist_package
zip -r ../SyncClipboard-macOS.zip .
```

### DMG 安装包（可选）
使用 `create-dmg` 工具创建专业的安装包：

```bash
# 安装工具
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

## 🔧 常见问题

### 1. "无法打开，因为来自身份不明的开发者"
```bash
# 允许运行未签名应用
xattr -cr client_gui.build/client_gui.app
```

或在系统偏好设置 → 安全性与隐私 → 点击"仍要打开"。

### 2. 托盘图标不显示
- 这是正常现象，因为未指定应用图标
- 可以准备 `icon.icns` 文件，并在构建时添加参数：
  ```bash
  --macos-app-icon=icon.icns
  ```

### 3. 需要修改服务器地址
- 打包前修改 `config.ini` 中的 `server_url`，然后重新打包
- 或者打包后修改 `client_gui.app/Contents/MacOS/config.ini`

### 4. PyQt5 警告信息
构建时可能出现 PyQt5 兼容性警告，这是正常的，不影响使用。

## 📝 构建参数说明

| 参数 | 说明 |
|------|------|
| `--standalone` | 生成独立可执行文件，包含所有依赖 |
| `--macos-create-app-bundle` | 创建 macOS 应用包（.app） |
| `--enable-plugin=pyqt5` | 启用 PyQt5 插件支持 |
| `--assume-yes-for-downloads` | 自动下载依赖，无需确认 |
| `--static-libpython=no` | 不使用静态 libpython（兼容 Homebrew Python） |
| `--include-data-file` | 打包数据文件（如 config.ini） |
| `--clang` | 使用 Clang 编译器 |
| `--output-dir` | 指定输出目录 |

### 可选参数
```bash
# 添加应用图标
--macos-app-icon=icon.icns

# 设置应用名称
--macos-app-name="剪贴板同步客户端"

# 设置应用版本
--macos-app-version=1.0.0

# 指定签名身份（需要开发者证书）
--macos-sign-identity="Developer ID Application: Your Name"

# 禁用控制台窗口（GUI 应用）
--disable-console
```

## 🎯 性能优化建议

### 减小应用体积
```bash
# 添加优化参数
--lto=yes                    # 链接时优化
--remove-output              # 构建完成后删除中间文件
```

### 加快构建速度
```bash
# 使用 ccache（缓存编译结果）
brew install ccache

# Nuitka 会自动检测并使用 ccache
```

## 📚 参考资源

- [Nuitka 官方文档](https://nuitka.net/doc/)
- [PyQt5 打包指南](https://nuitka.net/info/pyqt5.html)
- [macOS 应用签名](https://nuitka.net/doc/user-manual.html#macos-signing)

