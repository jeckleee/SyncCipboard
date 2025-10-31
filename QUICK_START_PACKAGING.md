# ⚡ 快速开始 - Windows 打包

3 步完成 Windows 应用打包！

---

## 📦 第一步：安装 Nuitka

```cmd
pip install nuitka zstandard ordered-set
```

如果还没有安装项目依赖：
```cmd
pip install -r requirements.txt
```

---

## 🔨 第二步：安装 C 编译器

下载并安装 **Visual Studio Community**（免费）：  
👉 https://visualstudio.microsoft.com/zh-hans/downloads/

安装时勾选：**"使用 C++ 的桌面开发"**

> ⏱️ 安装大约需要 10-15 分钟

---

## 🚀 第三步：运行打包脚本

双击运行：
```
build_windows.bat
```

或在命令行中执行：
```cmd
build_windows.bat
```

**PowerShell 用户**也可以使用：
```powershell
.\build_windows.ps1
```

---

## ✅ 完成！

打包完成后，在 `dist` 目录找到：
- ✅ `SyncClipboard.exe` - 可执行文件
- ✅ `config.ini` - 配置文件

### 使用方法

1. **编辑配置**
   ```cmd
   notepad dist\config.ini
   ```
   修改 `server_url` 为你的服务器地址。

2. **运行应用**
   ```cmd
   cd dist
   SyncClipboard.exe
   ```
   或直接双击 `SyncClipboard.exe`

3. **查看托盘图标**
   应用会在系统托盘显示图标 📋

---

## 🎁 可选：添加自定义图标

1. 准备一个 `icon.ico` 文件（推荐 256x256 像素）
2. 放到项目根目录
3. 重新运行打包脚本

不添加图标也可以正常使用！

详细说明：[ICON_GUIDE.md](ICON_GUIDE.md)

---

## 📤 分发给其他用户

压缩 `dist` 目录内的文件：
```powershell
Compress-Archive -Path dist\* -DestinationPath SyncClipboard-Windows.zip
```

把 `SyncClipboard-Windows.zip` 发给用户即可！

---

## ❓ 遇到问题？

### 编译失败
- ✅ 检查是否已安装 Visual Studio（带 C++ 工具）
- ✅ 检查是否已安装 Nuitka：`python -m nuitka --version`

### 运行时找不到配置文件
- ✅ 确保 `config.ini` 和 `SyncClipboard.exe` 在同一目录

### Windows Defender 报毒
- ✅ 添加到白名单（这是误报）

### 需要看到调试信息
- ✅ 从命令行运行 `SyncClipboard.exe`

---

## 📚 详细文档

- [BUILD_WINDOWS.md](BUILD_WINDOWS.md) - 完整打包指南
- [BUILD_GUIDE.md](BUILD_GUIDE.md) - 快速构建指南
- [README_PACKAGING.md](README_PACKAGING.md) - 打包说明总览

---

**🚀 开始打包吧！只需 3 步！**

```cmd
# 1. 安装 Nuitka
pip install nuitka zstandard ordered-set

# 2. 安装 Visual Studio (如果还没有)

# 3. 运行打包脚本
build_windows.bat
```

