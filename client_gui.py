import sys
import os
import time
import threading
import uuid
import platform
import subprocess
import requests
import pyperclip
import configparser
from PyQt5 import QtWidgets, QtGui, QtCore

# =======================
# 读取配置文件
# =======================
def get_config_path():
    """获取配置文件路径（兼容打包后的应用）"""
    # 优先级1: 可执行文件所在目录（打包后）
    if getattr(sys, 'frozen', False):
        # Nuitka 打包后
        exe_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(exe_dir, "config.ini")
        if os.path.exists(config_path):
            return config_path
    
    # 优先级2: 当前工作目录
    if os.path.exists("config.ini"):
        return "config.ini"
    
    # 优先级3: 脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.ini")
    if os.path.exists(config_path):
        return config_path
    
    # 未找到配置文件，返回默认路径
    return "config.ini"

config = configparser.ConfigParser()
config_file_path = get_config_path()
config.read(config_file_path, encoding="utf-8")
print(f"📝 配置文件路径: {config_file_path}")

# 全局配置
APP_NAME = config.get("global", "app_name", fallback="SyncClipboard")
APP_VERSION = config.get("global", "app_version", fallback="1.0.0")
APP_ICON = config.get("global", "app_icon", fallback="")

# 客户端配置
SERVER_URL = config.get("client", "server_url", fallback="http://127.0.0.1:8000")
SYNC_INTERVAL = config.getfloat("client", "sync_interval", fallback=1.0)
ENABLE_SOUND = config.getboolean("client", "enable_sound", fallback=True)
ENABLE_POPUP = config.getboolean("client", "enable_popup", fallback=True)

DEVICE_ID = f"{platform.node()}-{uuid.uuid4().hex[:6]}"
last_clipboard_text = ""
last_sync_time = None
stop_flag = False

# =======================
# 系统提示音
# =======================
def play_sound():
    if not ENABLE_SOUND:
        return
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"])
        elif system == "Windows":
            import winsound
            winsound.MessageBeep()
        else:
            QtWidgets.QApplication.beep()
    except Exception as e:
        print("⚠️ 提示音播放失败:", e)

# =======================
# 剪贴板同步逻辑
# =======================
def upload_clipboard(tray_app, text):
    """上传剪贴板内容到服务端"""
    try:
        requests.post(f"{SERVER_URL}/upload", json={
            "device_id": DEVICE_ID,
            "content": text
        }, timeout=3)
        if ENABLE_POPUP:
            tray_app.showMessage(
                "📤 剪贴板同步",
                "上传成功",
                QtWidgets.QSystemTrayIcon.Information,
                2000
            )
        play_sound()
        print(f"↑ 已上传: {text[:30]!r}")
    except Exception as e:
        print("❌ 上传失败:", e)

def fetch_clipboard():
    """从服务端拉取最新内容"""
    try:
        r = requests.get(f"{SERVER_URL}/fetch", timeout=3)
        return r.json()
    except Exception as e:
        print("❌ 拉取失败:", e)
        return None

def clipboard_watcher(tray_app):
    """监听剪贴板变化"""
    global last_clipboard_text
    while not stop_flag:
        try:
            current_text = pyperclip.paste()
            if current_text != last_clipboard_text:
                last_clipboard_text = current_text
                upload_clipboard(tray_app, current_text)
        except Exception as e:
            print("❌ 剪贴板监听错误:", e)
        time.sleep(0.5)

def sync_from_server(tray_app):
    """定时从服务端拉取更新"""
    global last_sync_time, last_clipboard_text
    while not stop_flag:
        data = fetch_clipboard()
        if data and data.get("updated_at"):
            updated_at = data["updated_at"]
            if (not last_sync_time) or updated_at > last_sync_time:
                # 跳过自己上传的内容
                if data.get("device_id") != DEVICE_ID:
                    new_text = data["content"]
                    if new_text != last_clipboard_text:
                        pyperclip.copy(new_text)
                        last_clipboard_text = new_text
                        print(f"↓ 从服务端同步: {new_text[:30]!r}")
                        if ENABLE_POPUP:
                            tray_app.showMessage(
                                "📥 剪贴板同步",
                                "已接收到来自其他设备的新内容",
                                QtWidgets.QSystemTrayIcon.Information,
                                3000
                            )
                        play_sound()
                last_sync_time = updated_at
        time.sleep(SYNC_INTERVAL)

# =======================
# 托盘应用部分
# =======================
class ClipboardTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(ClipboardTrayApp, self).__init__(icon, parent)
        self.setToolTip(f"📋 {APP_NAME} v{APP_VERSION}")
        self.menu = QtWidgets.QMenu(parent)

        # 查看当前剪贴板
        show_action = self.menu.addAction("查看当前剪贴板")
        show_action.triggered.connect(self.show_clipboard_content)

        # 手动同步
        sync_action = self.menu.addAction("手动同步")
        sync_action.triggered.connect(self.manual_sync)

        self.menu.addSeparator()

        # 退出
        exit_action = self.menu.addAction("退出")
        exit_action.triggered.connect(self.exit_app)

        self.setContextMenu(self.menu)

        # 启动后台线程
        threading.Thread(target=clipboard_watcher, args=(self,), daemon=True).start()
        threading.Thread(target=sync_from_server, args=(self,), daemon=True).start()

        self.show()
        if ENABLE_POPUP:
            self.showMessage(
                f"📋 {APP_NAME}",
                f"v{APP_VERSION} 已启动（同步间隔 {SYNC_INTERVAL}s）",
                QtWidgets.QSystemTrayIcon.Information,
                2500
            )

    def show_clipboard_content(self):
        content = pyperclip.paste()
        msg = content if len(content) < 300 else content[:300] + "..."
        QtWidgets.QMessageBox.information(None, "当前剪贴板内容", msg)

    def manual_sync(self):
        """手动从服务端拉取更新"""
        data = fetch_clipboard()
        if data and data.get("content"):
            pyperclip.copy(data["content"])
            if ENABLE_POPUP:
                self.showMessage("📋 手动同步", "已从服务端更新内容", QtWidgets.QSystemTrayIcon.Information, 2000)
            play_sound()
        else:
            if ENABLE_POPUP:
                self.showMessage("📋 手动同步", "未获取到有效数据", QtWidgets.QSystemTrayIcon.Warning, 2000)

    def exit_app(self):
        global stop_flag
        stop_flag = True
        QtWidgets.QApplication.quit()

# =======================
# 主入口
# =======================
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # 加载应用图标
    if APP_ICON and os.path.exists(APP_ICON):
        icon = QtGui.QIcon(APP_ICON)
    else:
        icon = QtGui.QIcon.fromTheme("edit-paste")
    
    tray_app = ClipboardTrayApp(icon)
    print(f"🧩 {APP_NAME} v{APP_VERSION} 已启动")
    print(f"📱 设备ID: {DEVICE_ID}")
    print(f"🔗 服务端地址: {SERVER_URL}")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
