# macOS 文件同步指南

## 📋 概述

本文档专门针对macOS系统上的文件同步功能，解释可能遇到的问题和解决方案。

## ✅ 兼容性分析

### 代码兼容性

经过检查，`client_gui.py`中的文件同步代码**理论上完全兼容macOS**：

1. **使用PyQt5标准API**
   - `QMimeData.hasUrls()` - 跨平台支持
   - `QUrl.fromLocalFile()` - macOS原生支持
   - `QUrl.toLocalFile()` - 正确处理file://协议

2. **macOS特殊优化**
   - 路径规范化：`os.path.normpath()` 和 `os.path.abspath()`
   - 剪贴板延迟：设置后等待50ms确保生效
   - 详细错误追踪：macOS上自动打印完整错误堆栈

## 🔍 潜在问题

虽然代码兼容，但macOS上可能遇到以下问题：

### 1. 应用权限问题

**问题**: macOS的安全机制可能阻止访问剪贴板

**解决方案**:
```bash
# 1. 在系统偏好设置中授予权限
系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能
将 Python 或 Terminal 添加到允许列表

# 2. 或者使用管理员权限运行（不推荐）
sudo python client_gui.py
```

### 2. PyQt5版本问题

**问题**: 旧版PyQt5可能不支持某些macOS特性

**检查版本**:
```bash
pip show PyQt5
```

**推荐版本**: PyQt5 >= 5.15.0

**更新**:
```bash
pip install --upgrade PyQt5
```

### 3. Python.app vs python命令行

**问题**: macOS的剪贴板访问在GUI应用和命令行工具中行为不同

**解决方案**:
```bash
# 方式1: 使用pythonw（推荐）
pythonw client_gui.py

# 方式2: 创建.app包（最佳）
# 参考 BUILD_GUIDE.md

# 方式3: 使用虚拟环境中的python
source venv/bin/activate
python client_gui.py
```

### 4. 文件路径问题

**问题**: macOS的文件路径可能包含特殊字符或空格

**已优化**: 代码中已添加路径规范化
```python
if platform.system() == "Darwin":
    file_path = os.path.normpath(file_path)
    file_path = os.path.abspath(file_path)
```

### 5. 临时文件位置

**macOS临时目录**: 
- 位置: `/var/folders/xx/xxxxx/T/`
- 使用 `tempfile.gettempdir()` 自动获取
- 系统会定期清理

## 🧪 测试步骤

### 1. 运行测试脚本

```bash
# 测试PyQt5剪贴板功能
python test_macos_clipboard.py
```

这个脚本会：
- ✅ 测试读取Finder中复制的文件
- ✅ 测试将文件设置到剪贴板
- ✅ 测试不同的URL格式
- ✅ 显示所有MIME格式

### 2. 手动测试文件复制

**测试上传**:
```
1. 启动服务端: python server.py
2. 启动客户端: python client_gui.py
3. 在Finder中选择一个文件
4. 按 Cmd+C 复制
5. 观察终端输出
```

**预期输出**:
```
🔍 [macOS调试] 检测到文件: ['/Users/xxx/test.txt']
↑ 已上传文件: test.txt (1.2KB)
```

**测试下载**:
```
1. 在另一台设备上复制文件
2. macOS设备会自动接收
3. 文件保存到 /var/folders/xx/.../T/
4. 按 Cmd+V 可以粘贴文件
```

### 3. 启用调试模式

```bash
# 启用macOS详细调试信息
export SYNCCLIP_DEBUG=1
python client_gui.py
```

这会显示：
- 每次检测到文件时的详细信息
- 完整的错误堆栈
- 文件路径和大小

## 🔧 macOS特定配置

### 配置示例

```ini
[client]
server_url = http://192.168.1.100:8910
sync_interval = 1
max_file_size = 5

# macOS用户可能需要更大的限制（Retina截图）
# max_file_size = 10
```

### 推荐设置

| 场景 | max_file_size | 说明 |
|------|---------------|------|
| 文档为主 | 5 | 适合.pages, .numbers, .pdf |
| 含截图 | 10 | Retina截图可能较大 |
| 设计稿 | 20 | .sketch, .psd文件 |
| 代码项目 | false | 只同步文本，不同步文件 |

## 📱 macOS特性支持

### 支持的操作

✅ **完全支持**:
- Finder中 Cmd+C 复制文件
- 接收后 Cmd+V 粘贴文件
- 拖拽到Finder、Desktop
- 支持所有文件类型

✅ **已测试**:
- .txt, .pdf, .jpg, .png
- .zip, .dmg
- 包含空格和中文的文件名
- 路径中包含~的文件

⚠️  **注意事项**:
- 不支持同时复制多个文件（只同步第一个）
- 不支持复制文件夹（需要压缩为.zip）
- iCloud Drive文件需要先下载到本地

### macOS剪贴板格式

macOS剪贴板使用的MIME类型：
```
public.file-url          # macOS标准文件URL
public.url               # 通用URL格式
text/uri-list            # URI列表（跨平台）
```

PyQt5会自动处理这些格式转换。

## 🐛 常见问题

### Q1: 复制文件后没有同步

**诊断步骤**:

1. 检查控制台输出
```bash
# 应该看到以下输出之一：
⏭️  检测到文件，但文件同步已禁用
↑ 已上传文件: xxx.txt
⚠️  文件过大: xxx.txt
```

2. 启用调试模式
```bash
export SYNCCLIP_DEBUG=1
python client_gui.py
```

3. 运行测试脚本
```bash
python test_macos_clipboard.py
```

**可能原因**:
- [ ] `max_file_size = false`（禁用了文件同步）
- [ ] 文件大小超出限制
- [ ] PyQt5版本太旧
- [ ] 应用没有权限访问剪贴板
- [ ] 复制的是文件夹而不是文件

### Q2: 接收文件后找不到

**文件位置**:
```bash
# macOS临时目录（示例）
/var/folders/zz/zyxvpxvq6csfxvn_n0000000000000/T/

# 查看临时目录
echo $TMPDIR

# 查找最近下载的文件
ls -lt $TMPDIR | head -20
```

**快速访问**:
1. 文件已在剪贴板中，直接 Cmd+V 粘贴
2. 或打开Finder，按 Cmd+Shift+G，输入 $TMPDIR

### Q3: 文件同步后无法打开

**检查文件完整性**:
```bash
# 比对文件大小
# 原始文件
ls -lh /path/to/original

# 接收的文件
ls -lh $TMPDIR/filename
```

**可能原因**:
- Base64编码/解码错误
- 网络传输不完整
- 文件权限问题

**解决方案**:
```bash
# 1. 检查文件权限
chmod 644 $TMPDIR/filename

# 2. 查看文件类型
file $TMPDIR/filename

# 3. 重新复制文件
```

### Q4: 提示音不工作

macOS提示音使用：
```python
subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])
```

**检查**:
```bash
# 测试系统提示音
afplay /System/Library/Sounds/Ping.aiff

# 如果不工作，检查音量设置
```

### Q5: 打包后的.app无法同步文件

**可能原因**:
- 应用签名问题
- 沙盒限制
- 权限不足

**解决方案**:
```bash
# 1. 打包时禁用沙盒
# 参考 BUILD_GUIDE.md

# 2. 首次运行后在系统偏好设置中授权

# 3. 使用开发者ID签名（正式发布）
```

## 💡 最佳实践

### 1. 开发环境

```bash
# 使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 测试
python client_gui.py
```

### 2. 生产环境

```bash
# 打包为.app
nuitka3 --standalone \
  --macos-create-app-bundle \
  --macos-app-icon=app.icns \
  --enable-plugin=pyqt5 \
  client_gui.py

# 双击运行
open client_gui.app
```

### 3. 调试技巧

```bash
# 1. 查看剪贴板内容（原生工具）
pbpaste

# 2. 查看剪贴板文件
osascript -e 'the clipboard as «class furl»'

# 3. 监控临时目录
watch -n 1 "ls -lt $TMPDIR | head -10"

# 4. 启用详细日志
export SYNCCLIP_DEBUG=1
python client_gui.py 2>&1 | tee debug.log
```

## 📊 性能考虑

### macOS特点

- **Retina屏幕截图**: 可能达到5-10MB
- **HEIC图片格式**: 比JPEG更小
- **系统临时目录**: SSD速度快，但空间有限

### 推荐配置

```ini
# Retina MacBook用户
max_file_size = 10

# 经常传输设计稿
max_file_size = 20

# 只传输文档
max_file_size = 5
```

## 🎯 结论

### 兼容性总结

| 项目 | 状态 | 说明 |
|------|------|------|
| 文件检测 | ✅ | 支持Finder复制 |
| 文件上传 | ✅ | Base64编码 |
| 文件下载 | ✅ | 保存到临时目录 |
| 剪贴板设置 | ✅ | 支持Cmd+V粘贴 |
| 路径处理 | ✅ | 自动规范化 |
| 权限管理 | ⚠️  | 可能需要手动授权 |
| 提示音 | ✅ | 使用afplay |
| 通知 | ✅ | 系统原生通知 |

### 确认兼容

**代码层面**: ✅ 完全兼容macOS
- 使用标准PyQt5 API
- 添加了macOS特殊处理
- 路径规范化
- 剪贴板延迟

**系统层面**: ⚠️  可能需要配置
- 应用权限
- PyQt5版本
- Python运行方式

### 测试建议

1. 先运行 `python test_macos_clipboard.py` 确认基础功能
2. 再运行完整客户端测试文件同步
3. 启用调试模式排查问题
4. 查看本文档的常见问题部分

---

## 📞 获取帮助

如果遇到问题：

1. **运行测试脚本**: `python test_macos_clipboard.py`
2. **启用调试模式**: `export SYNCCLIP_DEBUG=1`
3. **查看控制台输出**: 检查错误信息
4. **参考本文档**: 查找类似问题的解决方案

**macOS文件同步功能已准备就绪！** 🍎✨

