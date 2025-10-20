# 常见问题排查指南

## 应用无法启动的解决方案

### 问题：双击应用无法启动

#### 原因 1：macOS 安全限制（最常见）

**症状**：双击后没有反应，或提示"无法打开，因为来自身份不明的开发者"

**解决方案**：

##### 方法 1：移除隔离属性（推荐）
```bash
xattr -cr /path/to/SyncClipboard.app
```

或针对本项目：
```bash
cd /Users/lijian/Project/SyncCipboard
xattr -cr client_gui.build/SyncClipboard.app
```

##### 方法 2：从终端启动
```bash
open client_gui.build/SyncClipboard.app
```

##### 方法 3：通过系统偏好设置允许
1. 尝试双击打开应用
2. 打开"系统偏好设置" → "隐私与安全性"
3. 在底部找到被阻止的应用，点击"仍要打开"

#### 原因 2：应用未签名

**症状**：macOS Sequoia (15.0+) 可能拒绝运行未签名的应用

**解决方案**：

##### 临时解决（开发阶段）
```bash
# 允许运行本地构建的应用
sudo spctl --master-disable

# 使用完后记得重新启用
sudo spctl --master-enable
```

##### 永久解决（分发阶段）
使用 Apple 开发者账号签名应用：

```bash
# 查看可用的签名身份
security find-identity -v -p codesigning

# 签名应用（需要开发者证书）
codesign --deep --force --sign "Developer ID Application: Your Name" \
  client_gui.build/SyncClipboard.app

# 验证签名
codesign -dv client_gui.build/SyncClipboard.app
```

#### 原因 3：应用权限问题

**症状**：应用启动后立即闪退

**解决方案**：

```bash
# 检查可执行文件权限
ls -l client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui

# 如果没有执行权限，添加
chmod +x client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui
```

#### 原因 4：Python 依赖缺失

**症状**：终端启动时报错找不到库文件

**解决方案**：

```bash
# 从终端运行查看详细错误
./client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui

# 如果缺少 Python 模块，重新打包
./build_macos.sh
```

#### 原因 5：配置文件问题

**症状**：应用启动后无响应或立即退出

**解决方案**：

```bash
# 检查配置文件是否存在
ls -l client_gui.build/SyncClipboard.app/Contents/MacOS/config.ini

# 查看应用日志（从终端启动）
./client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui 2>&1 | tee app.log
```

---

## 验证应用状态

### 检查代码签名
```bash
codesign -dv client_gui.build/SyncClipboard.app
```

**正常输出应包含**：
```
Executable=/path/to/SyncClipboard.app/Contents/MacOS/client_gui
Identifier=SyncClipboard
Format=app bundle with Mach-O thin (arm64)
Signature=adhoc
```

### 检查应用信息
```bash
cat client_gui.build/SyncClipboard.app/Contents/Info.plist | grep -A 1 "CFBundleName"
```

### 检查可执行文件
```bash
file client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui
```

应该显示：`Mach-O 64-bit executable arm64`

### 查看应用是否运行
```bash
ps aux | grep SyncClipboard | grep -v grep
```

---

## 分发给其他用户

### 如果其他用户无法打开应用

#### 方案 1：提供安装说明

在 README 中包含以下说明：

```markdown
### 安装步骤

1. 下载 SyncClipboard.app
2. 解压到应用程序文件夹
3. **重要**：首次运行前执行以下命令：
   ```bash
   xattr -cr /Applications/SyncClipboard.app
   ```
4. 或者：右键点击应用 → 选择"打开" → 在弹出窗口点击"打开"
```

#### 方案 2：代码签名（推荐，需要开发者账号）

**需要**：
- Apple Developer 账号（$99/年）
- 开发者证书

**步骤**：
```bash
# 1. 获取开发者证书（在 Apple Developer 网站）

# 2. 签名应用
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  client_gui.build/SyncClipboard.app

# 3. 公证应用（macOS 10.15+）
xcrun notarytool submit SyncClipboard.zip \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password" \
  --wait

# 4. 装订公证票据
xcrun stapler staple client_gui.build/SyncClipboard.app

# 5. 验证
spctl -a -vvv -t install client_gui.build/SyncClipboard.app
```

#### 方案 3：创建 DMG 安装包

```bash
# 安装 create-dmg
brew install create-dmg

# 创建 DMG
create-dmg \
  --volname "SyncClipboard 安装器" \
  --volicon "app.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "SyncClipboard.app" 200 190 \
  --hide-extension "SyncClipboard.app" \
  --app-drop-link 600 185 \
  "SyncClipboard-Installer.dmg" \
  "client_gui.build/SyncClipboard.app"
```

---

## 调试技巧

### 查看应用日志
```bash
# 从终端启动并查看输出
./client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui

# 或使用 Console.app 查看系统日志
open /Applications/Utilities/Console.app
```

### 查看崩溃报告
```bash
# macOS 崩溃报告位置
open ~/Library/Logs/DiagnosticReports/
```

### 测试应用元数据
```bash
# 查看应用信息
plutil -p client_gui.build/SyncClipboard.app/Contents/Info.plist

# 查看应用图标
qlmanage -p client_gui.build/SyncClipboard.app/Contents/Resources/app.icns
```

### 重置 LaunchServices 数据库
```bash
# 如果应用图标不显示或双击行为异常
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user

# 重启 Dock
killall Dock
```

---

## 常见错误信息

### "app is damaged and can't be opened"
**原因**：macOS 隔离属性或 Gatekeeper 阻止  
**解决**：`xattr -cr SyncClipboard.app`

### "code signature invalid"
**原因**：签名损坏或被修改  
**解决**：重新构建或重新签名

### "LSOpenURLsWithRole() failed with error -10810"
**原因**：应用包结构不完整  
**解决**：重新构建应用

### Python 相关错误
**原因**：依赖缺失或路径问题  
**解决**：检查虚拟环境，重新打包

---

## 快速检查清单

构建完成后，使用此清单验证应用：

- [ ] 应用文件存在：`ls client_gui.build/SyncClipboard.app`
- [ ] 可执行文件有效：`file client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui`
- [ ] 配置文件存在：`ls client_gui.build/SyncClipboard.app/Contents/MacOS/config.ini`
- [ ] 图标文件存在：`ls client_gui.build/SyncClipboard.app/Contents/Resources/app.icns`
- [ ] 从终端可启动：`open client_gui.build/SyncClipboard.app`
- [ ] 应用进程运行：`ps aux | grep SyncClipboard`
- [ ] 托盘图标显示：检查菜单栏
- [ ] 配置正确读取：查看终端输出

---

## 获取帮助

如果以上方法都无效：

1. 从终端运行并保存日志：
   ```bash
   ./client_gui.build/SyncClipboard.app/Contents/MacOS/client_gui 2>&1 | tee debug.log
   ```

2. 检查系统信息：
   ```bash
   sw_vers
   system_profiler SPSoftwareDataType
   ```

3. 提供以下信息以便排查：
   - macOS 版本
   - 芯片架构（Intel/Apple Silicon）
   - 完整错误日志
   - 构建命令和输出

