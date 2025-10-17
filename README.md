### SyncCipboard - 跨设备剪贴板同步

一个轻量的跨设备剪贴板同步工具。
- 服务端: FastAPI + uvicorn
- 客户端: PyQt5 托盘程序 + pyperclip
- 通信: HTTP/JSON

适合在本地局域网或自建公网服务器同步不同设备的文本剪贴板。

---

### 功能特性
- 双向同步：监听本地剪贴板变化并上传；定时从服务端拉取最新内容
- 自发过滤：跳过本设备自己上传的内容，避免回环
- 托盘提示：上传/拉取成功提供托盘气泡与提示音
- 时区感知时间戳：服务端 `updated_at` 为 UTC ISO8601（timezone-aware）
- 简洁部署：无数据库依赖，内存存储

---

### 目录结构
```
/Users/lijian/Project/SyncCipboard/
  ├─ server.py        # FastAPI 服务端
  ├─ client_gui.py    # PyQt5 托盘客户端
  ├─ config.ini       # 配置文件（示例见下）
  └─ requirements.txt # 依赖清单
```

---

### 环境要求
- Python ≥ 3.8
- macOS / Windows / Linux（客户端依赖 PyQt5 与系统剪贴板）

---

### 安装依赖
建议使用虚拟环境：
```bash
pip install -r /Users/lijian/Project/SyncCipboard/requirements.txt
```

---

### 配置 `config.ini`
示例：
```ini
[server]
host = 0.0.0.0
port = 8000

[client]
server_url    = http://127.0.0.1:8000
sync_interval = 1.0
enable_sound  = true
enable_popup  = true
```
- host/port：服务端监听地址与端口
- server_url：客户端访问的服务端地址（可填内网 IP 或域名）
- sync_interval：客户端从服务端轮询的间隔（秒）
- enable_sound/enable_popup：是否启用提示音/托盘气泡

提示：若将应用打包为可执行文件，建议将 `config.ini` 外置保存，不随可执行文件一同打包，以便后续修改。

---

### 启动方式
1) 启动服务端：
```bash
python /Users/lijian/Project/SyncCipboard/server.py
```
默认监听 `http://0.0.0.0:8000`（可在 `config.ini` 中调整）。

2) 启动客户端托盘应用：
```bash
python /Users/lijian/Project/SyncCipboard/client_gui.py
```
启动后驻留系统托盘，自动监听剪贴板并与服务端同步。

---

### API 说明
- POST `/upload` 上传剪贴板内容
  - 请求体：
    ```json
    { "device_id": "string", "content": "text" }
    ```
  - 响应：
    ```json
    { "status": "ok", "updated_at": "UTC ISO8601" }
    ```

- GET `/fetch` 获取最新剪贴板
  - 响应：
    ```json
    {
      "content": "text",
      "updated_at": "UTC ISO8601",
      "device_id": "string"
    }
    ```

- GET `/status` 服务运行状况
  - 响应：
    ```json
    { "running": true, "clipboard": { /* 同 /fetch */ } }
    ```

示例（curl）：
```bash
# 上传
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"test","content":"hello"}' \
  http://127.0.0.1:8000/upload

# 拉取
curl http://127.0.0.1:8000/fetch
```

---

### 常见问题（FAQ）
- 日志显示前 30 个字符，会截断实际内容吗？
  - 不会。日志仅为预览，实际存储的是完整文本。
- DeprecationWarning：`datetime.datetime.utcnow()`？
  - 已改为 `datetime.now(timezone.utc)`，`updated_at` 为时区感知的 UTC ISO 字符串。
- 提示音在不同系统的行为？
  - macOS 使用 `afplay` 播放系统音效；Windows 使用 `winsound`；Linux 回退到 `QApplication.beep()`。
- 无法连接服务端？
  - 检查 `server_url`、端口、防火墙、是否跨网段访问，以及服务端是否启动。

---

### 安全与隐私
- 剪贴板可能包含敏感信息，请在可信网络环境使用。
- 服务端为内存存储，重启后不保留历史；如需持久化/鉴权，请按需扩展。

---

### 许可与贡献
- 许可：MIT（详见 `LICENSE` 文件）。
- 贡献：欢迎 PR/Issue（如增加持久化、鉴权、端到端加密、多格式支持等）。
