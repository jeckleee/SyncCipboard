# macOS 文件同步快速检查清单

## ✅ 快速验证

### 第一步：基础测试

```bash
# 1. 运行macOS专用测试脚本
python test_macos_clipboard.py
```

**预期结果**: 所有4个测试都应该通过 ✅

---

### 第二步：启动应用

```bash
# 2. 启动服务端（在一个终端）
python server.py

# 3. 启动客户端（在另一个终端，可选调试模式）
export SYNCCLIP_DEBUG=1
python client_gui.py
```

**检查输出**:
```
✅ 应该看到：
📁 文件同步: 已启用（限制 5.0MB）

❌ 如果看到：
📁 文件同步: 已禁用
→ 修改 config.ini 中的 max_file_size
```

---

### 第三步：测试文件复制

```bash
# 在Finder中：
1. 选择一个小文件（< 5MB）
2. 按 Cmd+C 复制
3. 观察终端输出
```

**预期输出**:
```
✅ 正常情况：
🔍 [macOS调试] 检测到文件: ['/Users/xxx/test.txt']
↑ 已上传文件: test.txt (1.2KB)

⚠️  如果文件过大：
⚠️  文件过大: large_file.mov (15.0MB > 5.0MB)

⏭️  如果禁用了文件同步：
⏭️  检测到文件，但文件同步已禁用
```

---

### 第四步：测试文件接收

```bash
# 在另一台设备上复制文件
# macOS设备应该：
1. 自动接收文件
2. 显示通知："📥 文件同步 - 已接收: xxx"
3. 可以按 Cmd+V 粘贴
```

**查找接收的文件**:
```bash
# 文件保存在临时目录
ls -lt $TMPDIR | head -5
```

---

## 🔍 问题排查

### 问题1: 测试脚本失败

```bash
# 检查PyQt5版本
pip show PyQt5

# 应该 >= 5.15.0
# 如果版本太旧，更新：
pip install --upgrade PyQt5
```

### 问题2: 复制文件后没有反应

**检查1: 配置是否启用**
```bash
grep max_file_size config.ini
# 应该是数字，不是 false
```

**检查2: 文件是否太大**
```bash
# 查看文件大小
ls -lh /path/to/file

# 比较配置限制
# 5MB = 5,242,880 字节
```

**检查3: 是否真的是文件**
```bash
# 确保复制的是文件，不是：
- 文件夹（不支持）
- 文本内容（会走文本同步）
- 多个文件（只会同步第一个）
```

### 问题3: 权限错误

```bash
# 授予Python辅助功能权限
系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能
→ 添加 Python 或 Terminal
```

### 问题4: pythonw vs python

```bash
# 使用pythonw（GUI应用推荐）
pythonw client_gui.py

# 而不是
python client_gui.py
```

---

## 📊 兼容性确认

### 代码兼容性：✅

- [x] 使用PyQt5标准API
- [x] macOS路径规范化
- [x] 剪贴板延迟处理
- [x] 详细错误日志
- [x] 调试模式支持

### 需要确认的：

- [ ] PyQt5版本 >= 5.15.0
- [ ] 应用有剪贴板访问权限
- [ ] config.ini中max_file_size != false
- [ ] 测试文件 < 配置的限制

---

## 🎯 期望行为

### 文件复制（本地 → 服务器）

```
Finder中Cmd+C → 检测到文件 → 检查大小 → 上传 → 通知
                    ↓
                如果禁用
                    ↓
                静默跳过
```

### 文件接收（服务器 → 本地）

```
轮询服务器 → 发现新文件 → 下载 → 保存到$TMPDIR → 放入剪贴板 → 通知
```

### 粘贴测试

```
接收到文件后 → 打开Finder → Cmd+V → 文件被粘贴到当前目录
```

---

## 💡 macOS特别说明

### 1. 临时目录位置

```bash
# macOS的临时目录是动态的
echo $TMPDIR
# 输出类似：/var/folders/zz/zyxvpxvq.../T/

# 接收的文件保存在这里
# 可以用 Cmd+Shift+G 在Finder中访问
```

### 2. 文件名处理

✅ 支持的文件名：
- 中文：`测试文件.txt`
- 空格：`my file.pdf`
- 特殊字符：`file (1).jpg`

### 3. 文件类型

✅ 支持所有文件类型：
- 文档：`.pages`, `.numbers`, `.pdf`, `.txt`
- 图片：`.jpg`, `.png`, `.heic`
- 压缩包：`.zip`, `.dmg`
- 任何其他文件

❌ 不支持：
- 文件夹（需要先压缩为.zip）
- 多文件同时复制（只同步第一个）

---

## 📞 仍然有问题？

### 收集诊断信息

```bash
# 1. 启用调试模式运行
export SYNCCLIP_DEBUG=1
python client_gui.py 2>&1 | tee macos_debug.log

# 2. 复制一个文件

# 3. 检查日志文件
cat macos_debug.log

# 4. 运行系统测试
python test_macos_clipboard.py > test_result.txt 2>&1
```

### 检查清单

- [ ] 运行了 `test_macos_clipboard.py`，结果如何？
- [ ] PyQt5版本是多少？`pip show PyQt5`
- [ ] 配置文件中 max_file_size 的值是？
- [ ] 控制台有什么错误信息？
- [ ] 是在用 python 还是 pythonw 启动？
- [ ] 测试文件大小是多少？

### 查看详细文档

如需更多信息，请查看：
- `MACOS_FILE_SYNC_GUIDE.md` - 完整的macOS指南
- `FILE_SYNC_GUIDE.md` - 通用文件同步指南
- `TROUBLESHOOTING.md` - 通用故障排查

---

**祝你在macOS上使用愉快！** 🍎✨

