# 🎨 应用图标使用指南

本指南说明如何为 SyncClipboard 应用添加自定义图标。

---

## 📋 图标文件要求

### Windows 平台
- **文件名**: `icon.ico`
- **格式**: ICO 格式
- **推荐尺寸**: 256x256 像素（支持多尺寸内嵌）
- **位置**: 项目根目录

### macOS 平台
- **文件名**: `app.icns` 或在 `build_macos.sh` 中自定义
- **格式**: ICNS 格式
- **推荐尺寸**: 512x512 像素
- **位置**: 项目根目录

---

## 🛠️ 创建图标文件

### 方法一：在线转换工具（推荐）

#### Windows ICO 格式

1. **Convertio** - https://convertio.co/zh/png-ico/
   - 上传 PNG 图片
   - 选择转换为 ICO
   - 下载并重命名为 `icon.ico`

2. **ICO51** - https://www.ico51.cn/
   - 支持批量转换
   - 可自定义尺寸

3. **CloudConvert** - https://cloudconvert.com/png-to-ico
   - 支持多种格式
   - 高质量输出

#### macOS ICNS 格式

1. **CloudConvert** - https://cloudconvert.com/png-to-icns
2. **Online-Convert** - https://www.online-convert.com/convert-to-icns

### 方法二：命令行工具

#### Windows - 使用 ImageMagick

```powershell
# 安装 ImageMagick
choco install imagemagick

# 转换图片
magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

#### macOS - 使用 iconutil

```bash
# 1. 创建 iconset 目录
mkdir MyIcon.iconset

# 2. 准备不同尺寸的图片
sips -z 16 16     icon.png --out MyIcon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out MyIcon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out MyIcon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out MyIcon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out MyIcon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out MyIcon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out MyIcon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out MyIcon.iconset/icon_512x512@2x.png

# 3. 生成 icns 文件
iconutil -c icns MyIcon.iconset -o app.icns

# 4. 清理临时文件
rm -rf MyIcon.iconset
```

### 方法三：Photoshop / GIMP

1. 在 Photoshop 或 GIMP 中打开图片
2. 调整尺寸为 512x512 或 256x256
3. 使用插件导出为 ICO/ICNS 格式

---

## 📁 文件放置位置

```
SyncCipboard/
├── icon.ico           # Windows 图标
├── app.icns           # macOS 图标（已存在）
├── client_gui.py
├── build_windows.bat
└── build_macos.sh
```

---

## ✅ 使用步骤

### Windows

1. **准备图标文件**
   ```cmd
   # 确保文件存在
   dir icon.ico
   ```

2. **运行打包脚本**
   ```cmd
   build_windows.bat
   ```
   
3. **验证**
   - 脚本会自动检测 `icon.ico`
   - 如果存在，会显示：`检测到图标文件: icon.ico`
   - 如果不存在，会显示：`未找到 icon.ico，将使用默认图标`

### macOS

1. **准备图标文件**
   ```bash
   # 已存在 app.icns
   ls -lh app.icns
   ```

2. **确认 build_macos.sh 中的图标路径**
   ```bash
   # 编辑脚本，确认图标参数
   # --macos-app-icon=app.icns
   ```

3. **运行打包脚本**
   ```bash
   ./build_macos.sh
   ```

---

## 🎯 推荐图标设计

### 设计建议

1. **简洁明了**：使用简单的图形，避免过多细节
2. **高对比度**：确保在亮色和暗色背景下都清晰可见
3. **主题相关**：与剪贴板同步功能相关的图标设计
   - 📋 剪贴板图标
   - 🔄 同步箭头
   - 📱💻 设备互联

### 尺寸建议

| 平台 | 最小尺寸 | 推荐尺寸 | 最佳尺寸 |
|------|---------|---------|---------|
| Windows | 48x48 | 256x256 | 512x512 |
| macOS | 128x128 | 512x512 | 1024x1024 |

### 色彩建议

- 使用品牌色或主题色
- 避免过于鲜艳的颜色
- 考虑系统暗色模式的适配

---

## 🔍 当前项目状态

✅ **已存在**: `app.icns` (macOS 图标)  
❌ **缺失**: `icon.ico` (Windows 图标)

**建议**:
1. 使用在线工具将 `app.icns` 转换为 `icon.ico`
2. 或者从源图片同时生成两种格式

---

## 🚫 注意事项

1. **图标文件不是必需的**
   - 如果不提供图标，应用会使用系统默认图标
   - 不影响应用的正常运行

2. **文件大小**
   - ICO 文件通常在 10-100 KB 之间
   - ICNS 文件通常在 100-500 KB 之间
   - 过大的图标会增加应用体积

3. **透明背景**
   - 推荐使用 PNG 源图片（支持透明）
   - 转换时保留透明通道

4. **版权问题**
   - 确保使用的图标有合法授权
   - 可使用免费图标库：
     - [Flaticon](https://www.flaticon.com/)
     - [Icons8](https://icons8.com/)
     - [Iconify](https://iconify.design/)

---

## 🛠️ 测试图标

### Windows

```cmd
# 打包后查看图标
dist\SyncClipboard.exe

# 右键 -> 属性 -> 查看图标
```

### macOS

```bash
# 打包后查看图标
open client_gui.build/

# 在 Finder 中查看 client_gui.app 的图标
```

---

## 📚 相关资源

### 免费图标下载
- [Flaticon](https://www.flaticon.com/) - 海量免费图标
- [Icons8](https://icons8.com/) - 多风格图标
- [Iconify](https://iconify.design/) - 开源图标集

### 在线转换工具
- [Convertio](https://convertio.co/) - 支持多种格式
- [CloudConvert](https://cloudconvert.com/) - 高质量转换
- [OnlineConvertFree](https://onlineconvertfree.com/) - 免费无限制

### 图标设计工具
- [Figma](https://www.figma.com/) - 专业设计工具
- [Canva](https://www.canva.com/) - 简单易用
- [GIMP](https://www.gimp.org/) - 免费开源

---

## ❓ 常见问题

### Q: 我没有图标文件，能打包吗？
**A:** 可以！脚本会自动检测，如果没有图标文件会使用默认图标。

### Q: 如何修改已打包应用的图标？
**A:** 需要重新打包。建议准备好图标后再打包。

### Q: ICO 文件应该包含哪些尺寸？
**A:** 推荐包含：16x16, 32x32, 48x48, 64x64, 128x128, 256x256

### Q: 图标在 macOS 上显示模糊？
**A:** 确保 ICNS 文件包含高分辨率版本（@2x），建议使用 1024x1024 源图。

### Q: 可以使用 PNG 作为图标吗？
**A:** 不可以直接使用，需要先转换为 ICO（Windows）或 ICNS（macOS）格式。

---

## 💡 快速上手示例

假设你有一个 `my_icon.png` 文件：

### Windows

```cmd
# 1. 在线转换为 ICO
# 访问 https://convertio.co/zh/png-ico/
# 上传 my_icon.png，下载转换后的文件

# 2. 重命名为 icon.ico
ren downloaded_icon.ico icon.ico

# 3. 放到项目根目录
copy icon.ico D:\Project\SyncCipboard\

# 4. 运行打包脚本
build_windows.bat
```

### macOS

```bash
# 1. 在线转换为 ICNS
# 访问 https://cloudconvert.com/png-to-icns
# 上传 my_icon.png，下载转换后的文件

# 2. 重命名并放到项目目录
mv ~/Downloads/my_icon.icns ~/Project/SyncCipboard/app.icns

# 3. 运行打包脚本
./build_macos.sh
```

---

**🎨 享受自定义图标的乐趣！**

