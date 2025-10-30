# Windows 托盘通知问题排查指南

## 问题描述
在 Windows 系统上，程序功能正常但没有弹出托盘通知提示。

## 解决方案

### 1. 代码层面的修复（已完成）

已对 `client_gui.py` 进行以下优化：

#### ✅ 使用 PyQt5 信号-槽机制
- 后台线程通过信号发射通知请求
- 主线程的槽函数负责显示通知
- 确保所有 GUI 操作在主线程执行

#### ✅ Windows 特定优化
- **提前显示托盘图标**: 在构造函数中立即调用 `self.show()`
- **设置 AppUserModelID**: Windows 10+ 需要此 ID 才能正确显示通知
- **延迟启动通知**: 使用 `QTimer.singleShot()` 延迟 500ms 显示启动通知
- **确保图标可见性**: 在显示通知前检查并确保托盘图标可见

#### ✅ 诊断信息
程序启动时会输出：
- 系统托盘是否可用
- 是否支持通知消息
- 操作系统信息

### 2. Windows 系统设置检查

即使代码正确，Windows 系统设置也可能阻止通知显示。

#### 🔍 检查步骤

**步骤 1: 检查全局通知设置**
1. 打开 **设置** → **系统** → **通知和操作**
2. 确认 **"获取来自应用和其他发送者的通知"** 已开启
3. 检查 **"专注助手"** 设置（见下文）

**步骤 2: 检查应用通知权限**
1. 在 **通知和操作** 页面向下滚动
2. 找到 **Python** 或 **SyncClipboard** (取决于运行方式)
3. 确保该应用的通知开关已打开
4. 检查通知样式设置（建议选择 "显示横幅和操作中心中的通知"）

**步骤 3: 检查专注助手**
1. **设置** → **系统** → **专注助手**
2. 如果启用了专注助手，需要将应用添加到 **"优先级列表"**
3. 或者临时关闭专注助手进行测试

**步骤 4: 检查操作中心设置**
1. 点击任务栏右下角的通知图标
2. 查看是否有通知被收集在操作中心
3. 有些通知可能不弹出但会显示在这里

### 3. 测试工具

#### 运行简单测试
使用提供的测试脚本验证通知功能：

```bash
python test_notification.py
```

该脚本会：
- 检测系统托盘支持情况
- 测试主线程通知
- 测试跨线程通知
- 提供详细的诊断信息

#### 运行增强测试
```bash
python fix_windows_notification.py
```

该脚本包含：
- Windows 特定的优化
- AppUserModelID 设置
- 多种通知测试方式
- 详细的设置检查指南

### 4. 常见问题

#### Q1: 程序运行正常但从不显示通知
**A:** 
- 检查 `config.ini` 中的 `enable_popup = true`
- 查看控制台输出 `⚙️  支持通知消息: True/False`
- 如果显示 `False`，说明系统不支持或被禁用

#### Q2: 启动通知可以显示，但同步通知不显示
**A:**
- 这是线程安全问题，已通过信号-槽机制修复
- 确保使用的是修复后的代码版本

#### Q3: macOS 正常，Windows 不正常
**A:**
- macOS 对线程要求宽松，Windows 严格要求 GUI 操作在主线程
- Windows 需要 AppUserModelID
- Windows 托盘图标必须先显示才能发送通知

#### Q4: 通知显示但立即消失
**A:**
- 检查 `duration` 参数（单位：毫秒）
- Windows 10+ 可能会自动收集通知到操作中心
- 检查是否启用了 "安静时间" 功能

#### Q5: 打包后的 .exe 没有通知
**A:**
- 确保 AppUserModelID 设置正确
- Windows 可能需要首次运行时授予权限
- 检查 Windows Defender 或防火墙设置

### 5. 代码关键点说明

#### 信号-槽机制
```python
class ClipboardTrayApp(QtWidgets.QSystemTrayIcon):
    # 定义信号（类级别）
    notify_signal = QtCore.pyqtSignal(str, str, int, int)
    
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        # 连接信号到槽
        self.notify_signal.connect(self._show_notification)
    
    def _show_notification(self, title, message, icon, duration):
        """槽函数：在主线程中执行"""
        self.showMessage(title, message, icon, duration)
    
    def safe_notify(self, title, message, icon, duration):
        """从任何线程安全调用"""
        self.notify_signal.emit(title, message, icon, duration)
```

#### Windows AppUserModelID
```python
if platform.system() == "Windows":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "SyncClipboard.App.1.0.0"
    )
```

#### 延迟显示通知
```python
# 不要在 __init__ 中立即显示通知
# 使用 QTimer 延迟
QtCore.QTimer.singleShot(500, self._show_startup_notification)
```

### 6. 调试技巧

#### 启用详细日志
程序已经包含了详细的 print 输出：
- `↑ 已上传` - 上传成功
- `↓ 从服务端同步` - 接收到同步
- `📢 [通知]` - 准备显示通知

#### 检查控制台输出
```
✅ 已设置Windows AppUserModelID
✅ 启动通知已显示
⚙️  系统托盘可用: True
⚙️  支持通知消息: True
📢 [通知] 📥 剪贴板同步: 已接收到来自其他设备的新内容
```

如果看到 `📢 [通知]` 输出但没有弹窗，问题在系统设置层面。

### 7. 终极测试方法

1. **重启程序**: 有时 Windows 需要重启应用才能识别新的通知设置
2. **重启系统**: 系统级别的通知服务可能需要重启
3. **使用管理员权限运行**: 测试是否是权限问题
4. **临时关闭所有安全软件**: 测试是否被拦截
5. **检查事件查看器**: `Windows日志 → 应用程序` 查看是否有错误

### 8. 替代方案

如果托盘通知始终无法工作，可以考虑：

1. **使用 Windows 原生通知 API**
   ```python
   from win10toast import ToastNotifier
   toaster = ToastNotifier()
   toaster.show_toast("标题", "消息", duration=3)
   ```

2. **使用第三方库 `plyer`**
   ```python
   from plyer import notification
   notification.notify(title="标题", message="消息", timeout=3)
   ```

3. **使用 `winotify` (Windows 10+)**
   ```python
   from winotify import Notification
   toast = Notification(app_id="SyncClipboard", title="标题", msg="消息")
   toast.show()
   ```

### 9. 相关资源

- [PyQt5 QSystemTrayIcon 文档](https://doc.qt.io/qt-5/qsystemtrayicon.html)
- [Windows 通知设置官方文档](https://support.microsoft.com/zh-cn/windows/windows-10-notifications)
- [AppUserModelID 说明](https://learn.microsoft.com/en-us/windows/win32/shell/appids)

---

## 快速自检清单

- [ ] 运行 `python client_gui.py` 查看控制台输出
- [ ] 确认输出中显示 `⚙️  支持通知消息: True`
- [ ] 查看是否有 `📢 [通知]` 输出
- [ ] 检查 Windows 设置 → 系统 → 通知和操作
- [ ] 确认 Python 应用通知权限已开启
- [ ] 检查专注助手是否阻止了通知
- [ ] 查看操作中心是否有通知堆积
- [ ] 尝试运行测试脚本 `test_notification.py`
- [ ] 重启程序和/或系统

如果以上全部检查完毕仍无法显示通知，请提供：
1. 控制台完整输出
2. Windows 版本 (`winver` 命令)
3. PyQt5 版本 (`pip show PyQt5`)

