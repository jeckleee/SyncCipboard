# 📦 SyncClipboard 打包说明

本项目支持 Windows 和 macOS 平台的一键打包，使用 Nuitka 编译为原生可执行文件。

---

## 🎯 快速开始

### Windows 平台

```cmd
# 安装依赖
pip install -r requirements.txt
pip install nuitka zstandard ordered-set

# 一键打包
build_windows.bat
```

生成文件：`dist\SyncClipboard.exe`

### macOS 平台

```bash
# 安装依赖
source .venv/bin/activate
pip install -r requirements.txt
pip install nuitka zstandard ordered-set

# 一键打包
./build_macos.sh
```

生成文件：`client_gui.build/client_gui.app`

---

## 📚 详细文档

| 平台 | 快速指南 | 详细文档 |
|------|---------|---------|
| Windows | [BUILD_GUIDE.md](BUILD_GUIDE.md#-windows-平台打包) | [BUILD_WINDOWS.md](BUILD_WINDOWS.md) |
| macOS | [BUILD_GUIDE.md](BUILD_GUIDE.md#-macos-平台打包) | [BUILD_GUIDE.md](BUILD_GUIDE.md) |

---

## 🔑 核心特性

### ✅ 配置文件外置
- 配置文件 `config.ini` **不打包**到可执行文件中
- 运行时从 exe/app 所在目录读取配置
- 可随时修改配置无需重新打包

### ✅ 单文件分发
- Windows：单个 `SyncClipboard.exe` 文件（30-50 MB）
- macOS：单个 `client_gui.app` 应用包（60-80 MB）
- 包含完整的 Python 运行时和所有依赖

### ✅ 开箱即用
- 无需安装 Python 环境
- 无需安装任何依赖库
- 双击即可运行

---

## 📂 项目结构

```
SyncCipboard/
├── client_gui.py           # 客户端主程序
├── server.py               # 服务端主程序
├── config.ini              # 配置文件模板
├── requirements.txt        # Python 依赖
│
├── build_windows.bat       # Windows 打包脚本（批处理）
├── build_windows.ps1       # Windows 打包脚本（PowerShell）
├── build_macos.sh          # macOS 打包脚本
│
├── BUILD_GUIDE.md          # 快速构建指南
├── BUILD_WINDOWS.md        # Windows 详细打包文档
└── README_PACKAGING.md     # 本文件
```

---

## 🛠️ 打包脚本对比

### Windows

| 脚本 | 类型 | 推荐度 | 特点 |
|------|------|--------|------|
| `build_windows.bat` | 批处理 | ⭐⭐⭐⭐ | 兼容性好，所有系统可用 |
| `build_windows.ps1` | PowerShell | ⭐⭐⭐⭐⭐ | 功能强大，彩色输出 |

### macOS

| 脚本 | 类型 | 推荐度 | 特点 |
|------|------|--------|------|
| `build_macos.sh` | Shell | ⭐⭐⭐⭐⭐ | 一键打包为 .app 应用 |

---

## 📋 前置要求

### 所有平台

- Python 3.8+
- pip（Python 包管理器）

### Windows 额外要求

- Visual Studio（带 C++ 工具）或 MinGW64

### macOS 额外要求

- Xcode Command Line Tools

---

## 💡 使用提示

### 1. 配置文件位置

打包后，配置文件的查找顺序：
1. 可执行文件所在目录的 `config.ini`（推荐）
2. 当前工作目录的 `config.ini`
3. 脚本目录的 `config.ini`

### 2. 首次运行

```ini
# 编辑 config.ini
[client]
server_url = http://YOUR_SERVER_IP:8000  # 改为实际服务器地址
```

### 3. 调试模式

如需查看日志输出：

**Windows:**
```cmd
# 从命令行运行
SyncClipboard.exe
```

**macOS:**
```bash
# 从终端运行
./client_gui.app/Contents/MacOS/client_gui
```

---

## 🚀 分发指南

### Windows 分发清单
```
SyncClipboard-Windows/
├── SyncClipboard.exe
└── config.ini
```

### macOS 分发清单
```
SyncClipboard-macOS/
└── client_gui.app/
    └── Contents/
        └── MacOS/
            └── config.ini  （可选，也可以外置）
```

### 压缩打包

**Windows:**
```cmd
Compress-Archive -Path dist\* -DestinationPath SyncClipboard-Windows.zip
```

**macOS:**
```bash
cd client_gui.build
zip -r ../SyncClipboard-macOS.zip client_gui.app
```

---

## ⚠️ 常见问题

### Q: 打包时间过长？
A: 首次打包需要 3-5 分钟（下载依赖缓存），后续打包只需 1-2 分钟。

### Q: exe/app 文件很大？
A: 正常现象，包含了完整的 Python 运行时和所有依赖库。

### Q: 如何修改配置不重新打包？
A: 直接编辑 exe/app 同目录下的 `config.ini` 即可。

### Q: Windows Defender 报毒？
A: Nuitka 打包的程序可能被误判，添加到白名单即可。

### Q: macOS 提示"无法打开"？
A: 运行 `xattr -cr client_gui.app` 移除隔离属性。

---

## 📖 相关文档

- [BUILD_GUIDE.md](BUILD_GUIDE.md) - 快速构建指南（推荐新手）
- [BUILD_WINDOWS.md](BUILD_WINDOWS.md) - Windows 详细文档（包含高级选项）
- [Nuitka 官方文档](https://nuitka.net/) - 了解更多打包选项

---

## 🎉 开始打包

选择你的平台，运行对应的脚本：

**Windows:**
```cmd
build_windows.bat
```

**macOS:**
```bash
./build_macos.sh
```

**祝你打包顺利！**🚀

