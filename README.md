# SyncClipboard - 跨设备剪贴板同步工具

一个轻量、高效的跨设备剪贴板同步工具，支持**文本**、**图片**、**文件**三种内容类型的实时同步。

## ✨ 核心特性

### 多格式支持
- 📝 **文本同步**：支持任意长度的纯文本内容
- 🖼️ **图片同步**：支持剪贴板图片（PNG格式传输）
- 📁 **文件同步**：支持单个文件的跨设备传输

### 智能同步
- 🔄 **双向同步**：自动监听本地剪贴板变化并上传，定时从服务端拉取最新内容
- 🛡️ **防回环机制**：自动识别并跳过本设备上传的内容，避免重复同步
- ⏱️ **同步保护**：下载后2秒内不触发上传，防止误检测
- 📊 **增量拉取**：客户端记录最后同步时间，服务端仅在有新内容时返回数据

### 用户体验
- 🔔 **实时通知**：上传/下载成功后托盘气泡提醒，显示来源设备名称
- 🔊 **提示音效**：支持系统提示音（macOS/Windows/Linux）
- 🏷️ **设备识别**：支持自定义客户端名称，便于多设备管理
- 📏 **大小限制**：可配置文件/图片同步的体积上限

### 技术特点
- ⚡ **高性能**：HTTP Keep-Alive连接池，减少连接开销
- 🌐 **时区感知**：服务端使用UTC时区感知时间戳（ISO8601）
- 💾 **内存存储**：无数据库依赖，重启后不保留历史
- 🔒 **Base64传输**：文件和图片以Base64编码安全传输
- 🧹 **自动清理**：客户端退出时自动清理临时文件

---

## 📋 系统架构

```
┌─────────────┐          HTTP/JSON          ┌─────────────┐
│   客户端A    │ ◄────────────────────────► │  FastAPI    │
│  (PyQt5)    │                             │   服务端     │
└─────────────┘                             │  (内存存储)  │
                                            └─────────────┘
┌─────────────┐                                    ▲
│   客户端B    │                                    │
│  (PyQt5)    │ ───────────────────────────────────┘
└─────────────┘
```

**技术栈**：
- **服务端**：FastAPI + uvicorn
- **客户端**：PyQt5（托盘程序） + pyperclip（剪贴板操作）
- **通信协议**：HTTP/JSON（RESTful API）

---

## 📦 目录结构

```
SyncCipboard/
├── server.py              # FastAPI 服务端
├── client_gui.py          # PyQt5 托盘客户端
├── config.ini             # 配置文件
├── requirements.txt       # Python依赖清单
├── app.icns               # macOS应用图标
├── build_macos.sh         # macOS打包脚本
├── build_windows.bat      # Windows打包脚本
├── build_windows.ps1      # Windows PowerShell打包脚本
├── BUILD_GUIDE.md         # 构建指南
├── PACKAGING.md           # 打包详细文档
└── README.md              # 本文档
```

---

## 🚀 快速开始

### 环境要求

- **Python**：≥ 3.8
- **操作系统**：macOS / Windows / Linux
- **网络**：局域网或公网可达

### 安装依赖

建议使用虚拟环境：

```bash
# 克隆或下载项目
cd /Users/lijian/Project/SyncCipboard

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**依赖清单**（`requirements.txt`）：
```
fastapi
uvicorn[standard]
requests
pyperclip
PyQt5
```

---

## ⚙️ 配置说明

### 配置文件：`config.ini`

```ini
[global]
app_name = SyncClipboard
app_version = 1.0.0_20251103
# 应用图标路径（可留空使用系统默认）
app_icon = app.icns

[server]
# 服务端监听地址（0.0.0.0表示所有网卡）
host = 0.0.0.0
# 服务端监听端口
port = 8910

[client]
# 客户端显示名称（用于识别设备）
client_name = "我的电脑"
# 服务端地址（填局域网IP或公网域名）
server_url = http://127.0.0.1:8910
# 同步间隔时间（秒），建议1-3秒
sync_interval = 2
# 提示音文件路径（留空使用系统默认）
sound_file = 
# 是否启用提示音
enable_sound = true
# 是否启用托盘气泡通知
enable_popup = true
# 文件同步大小限制（单位：MB）
# - false: 不同步文件/图片
# - 0: 无限制
# - 数字: 最大MB数（如 5 表示5MB）
max_file_size = 5
```

### 配置项详解

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `client_name` | 客户端名称，显示在通知中 | `"公司电脑"`, `"家里Mac"` |
| `server_url` | 服务端地址（HTTP URL） | `http://192.168.1.100:8910` |
| `sync_interval` | 从服务端拉取间隔（秒） | `1.0` ~ `5.0` |
| `enable_sound` | 是否播放提示音 | `true` / `false` |
| `enable_popup` | 是否显示托盘通知 | `true` / `false` |
| `max_file_size` | 文件/图片大小限制（MB） | `false` / `0` / `5` / `10` |

**提示**：
- 局域网使用填内网IP（如 `192.168.1.100`）
- 公网使用填域名或公网IP（需开放端口）
- 打包后可将 `config.ini` 放在可执行文件同目录，便于修改

---

## 🎯 使用方式

### 1. 启动服务端

在一台设备上启动服务端（通常是固定IP的主机）：

```bash
python server.py
```

启动成功后会显示：
```
📡 服务端启动中... http://0.0.0.0:8910
```

**验证服务**：
```bash
curl http://127.0.0.1:8910/status
# 返回: {"running": true}
```

### 2. 启动客户端

在需要同步的设备上启动客户端：

```bash
python client_gui.py
```

启动后：
- ✅ 托盘出现图标
- ✅ 显示启动通知
- ✅ 后台自动监听剪贴板并同步

**诊断信息**：
```
📝 配置文件路径: /path/to/config.ini
🧩 SyncClipboard v1.0.0 已启动（后台模式）
🏷️  客户端名称: 我的电脑
📱 设备ID: hostname-abc123
🔗 服务端地址: http://192.168.1.100:8910
🔌 HTTP Keep-Alive: 已启用（连接池大小: 10-20）
🖥️  操作系统: Darwin
📁 文件同步: 已启用（限制 5.0MB）
```

### 3. 使用示例

#### 场景1：文本同步
1. 在设备A复制文本：`Ctrl+C` / `Cmd+C`
2. 客户端A自动上传到服务端
3. 设备B客户端自动拉取并写入剪贴板
4. 在设备B直接粘贴：`Ctrl+V` / `Cmd+V`

#### 场景2：图片同步
1. 在设备A截图或复制图片
2. 客户端A上传图片数据（PNG格式）
3. 设备B客户端下载并写入剪贴板
4. 在设备B的任意应用中粘贴图片

#### 场景3：文件同步
1. 在设备A复制文件（Finder/文件资源管理器）
2. 客户端A上传文件内容（Base64编码）
3. 设备B客户端下载到临时目录并写入剪贴板
4. 在设备B粘贴文件到目标位置

**注意**：
- 文件夹不支持同步（仅支持单个文件）
- 超过 `max_file_size` 限制的文件/图片会被跳过并提示
- 下载的文件保存在系统临时目录（退出时自动清理）

---

## 🔌 API接口文档

### POST `/upload` - 上传剪贴板内容

**请求体**（JSON）：

```json
{
  "device_id": "hostname-abc123",
  "client_name": "我的电脑",
  "content_type": "text",  // "text" | "file" | "image"
  
  // 当 content_type = "text" 时：
  "content": "Hello World",
  
  // 当 content_type = "file" 时：
  "file_name": "document.pdf",
  "file_data": "base64_encoded_string",
  "file_size": 1048576,  // 字节
  
  // 当 content_type = "image" 时：
  "image_data": "base64_encoded_png",
  "image_width": 1920,
  "image_height": 1080,
  "image_size": 524288  // 字节
}
```

**响应**（200 OK）：
```json
{
  "status": "ok",
  "updated_at": "2025-11-03T12:34:56.789012+00:00"
}
```

### GET `/fetch` - 拉取最新剪贴板

**查询参数**：
- `last_sync_time`（可选）：客户端最后同步时间（ISO8601格式）

**响应**（有新内容）：
```json
{
  "content_type": "text",
  "content": "Hello World",
  "updated_at": "2025-11-03T12:34:56.789012+00:00",
  "device_id": "hostname-abc123",
  "client_name": "我的电脑"
}
```

**响应**（无更新）：
```json
{
  "status": "no_update",
  "updated_at": "2025-11-03T12:34:56.789012+00:00"
}
```

### GET `/status` - 服务运行状态

**响应**：
```json
{
  "running": true
}
```

### cURL示例

```bash
# 上传文本
curl -X POST http://127.0.0.1:8910/upload \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device",
    "client_name": "测试客户端",
    "content_type": "text",
    "content": "Hello from curl!"
  }'

# 拉取内容
curl http://127.0.0.1:8910/fetch

# 增量拉取（带时间戳）
curl "http://127.0.0.1:8910/fetch?last_sync_time=2025-11-03T12:00:00.000000%2B00:00"

# 检查服务状态
curl http://127.0.0.1:8910/status
```

---

## 📱 应用打包

项目支持打包为独立可执行文件（无需Python环境）。

### macOS 打包

使用 Nuitka 打包为 `.app` 应用：

```bash
bash build_macos.sh
```

生成位置：`client_gui.build/SyncClipboard.app`

### Windows 打包

使用 Nuitka 打包为 `.exe` 可执行文件：

```cmd
build_windows.bat
```

生成位置：`client_gui.dist/client_gui.exe`

### 详细文档

- [BUILD_GUIDE.md](BUILD_GUIDE.md) - 完整构建指南
- [PACKAGING.md](PACKAGING.md) - 打包配置详解

---

## ❓ 常见问题（FAQ）

### Q1: 无法连接到服务端？
**解决方案**：
1. 检查服务端是否启动：`curl http://服务端IP:端口/status`
2. 检查 `config.ini` 中的 `server_url` 是否正确
3. 检查防火墙是否放行端口（如 `8910`）
4. 跨网段访问需确保路由可达

### Q2: 文件/图片无法同步？
**原因**：
- `max_file_size` 设置为 `false`（已禁用文件同步）
- 文件大小超过 `max_file_size` 限制

**解决方案**：
- 修改 `config.ini`：设置 `max_file_size = 0`（无限制）或增大数值（如 `10`）
- 检查托盘通知是否显示 "文件过大" 警告

### Q3: 为什么复制后立即粘贴没有同步？
**原因**：
- 同步有网络延迟（取决于 `sync_interval` 和网络状况）
- 首次上传需要等待下一次同步周期

**解决方案**：
- 减小 `sync_interval`（如改为 `1.0` 秒）
- 等待1-3秒后再粘贴

### Q4: 日志显示前30个字符，会截断实际内容吗？
**回答**：
- 不会。日志仅为预览，实际存储和传输的是完整内容。

### Q5: 支持哪些操作系统的提示音？
**回答**：
- **macOS**：使用 `afplay` 播放 `/System/Library/Sounds/Ping.aiff`
- **Windows**：使用 `winsound.MessageBeep()`
- **Linux**：回退到 `QApplication.beep()`

### Q6: 如何禁用通知和提示音？
**解决方案**：
修改 `config.ini`：
```ini
enable_sound = false
enable_popup = false
```

### Q7: 服务端重启后数据会丢失吗？
**回答**：
- 是的。服务端使用内存存储，重启后不保留历史剪贴板。
- 如需持久化，可扩展为使用 Redis/数据库存储。

### Q8: 临时文件保存在哪里？
**回答**：
- 下载的文件保存在系统临时目录（`tempfile.gettempdir()`）
- 客户端退出时自动清理最后一次下载的文件

### Q9: 如何在多台设备间使用？
**步骤**：
1. 在一台设备（如服务器）启动 `server.py`
2. 获取该设备的内网IP（如 `192.168.1.100`）或公网IP/域名
3. 在所有客户端设备的 `config.ini` 中填写 `server_url = http://192.168.1.100:8910`
4. 为每个客户端设置不同的 `client_name`（便于识别）
5. 启动所有客户端

---

## 🔒 安全与隐私

### ⚠️ 重要提示

- 剪贴板可能包含**敏感信息**（密码、私钥、个人数据）
- 请仅在**可信网络环境**使用（如家庭局域网、办公室内网）
- 服务端为**内存存储**，重启后不保留历史
- 数据传输为**明文HTTP**，公网使用建议配置HTTPS反向代理

### 安全建议

1. **内网部署**：优先在局域网内使用
2. **防火墙**：限制服务端端口仅允许特定IP访问
3. **HTTPS**：公网使用时配置Nginx/Caddy反向代理启用HTTPS
4. **鉴权扩展**：可自行添加API Token验证
5. **端到端加密**：可扩展为客户端加密后上传

---

## 🛠️ 技术细节

### 性能优化

- **HTTP Keep-Alive**：客户端使用 `requests.Session` 连接池，避免频繁建立TCP连接
- **增量拉取**：客户端记录 `last_sync_time`，服务端仅在有更新时返回完整数据
- **同步保护**：下载后2秒内不触发上传，避免误检测和回环
- **异步后台线程**：监听和同步在独立线程，不阻塞主界面

### 跨平台兼容性

| 功能 | macOS | Windows | Linux |
|------|-------|---------|-------|
| 文本同步 | ✅ | ✅ | ✅ |
| 图片同步 | ✅ | ✅ | ✅ |
| 文件同步 | ✅ | ✅ | ⚠️（未充分测试） |
| 托盘图标 | ✅ | ✅ | ✅ |
| 系统通知 | ✅ | ✅ | ✅ |
| 提示音 | ✅ | ✅ | ⚠️（降级为beep） |

### 已知限制

- 不支持文件夹同步（仅支持单个文件）
- 不支持富文本格式（如HTML剪贴板）
- 服务端仅存储最新一条剪贴板（不保留历史）
- Base64编码会增加约33%的传输体积

---

## 🤝 贡献与反馈

### 欢迎贡献

项目开源，欢迎提交 Pull Request 或 Issue：

- 🐛 **Bug修复**：修复已知问题
- ✨ **新功能**：如数据库持久化、鉴权、端到端加密
- 📝 **文档改进**：完善文档和示例
- 🌍 **国际化**：添加多语言支持

### 功能规划

- [ ] API Token鉴权
- [ ] 客户端历史记录面板
- [ ] 数据库持久化（SQLite/Redis）
- [ ] 端到端加密（AES）
- [ ] 富文本格式支持
- [ ] 多剪贴板管理（队列）
- [ ] WebSocket实时推送

---

## 📄 许可证

本项目采用 **MIT License** 开源。

详见 [LICENSE](LICENSE) 文件。

---

## 📮 联系方式

- **项目主页**：[GitHub Repository]
- **问题反馈**：[GitHub Issues]

---

**享受无缝的跨设备剪贴板体验！** 🚀
