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
import base64
import tempfile
from pathlib import Path
from io import BytesIO
from io import BytesIO
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

# 文件同步配置
max_file_size_str = config.get("client", "max_file_size", fallback="false").strip().lower()
if max_file_size_str == "false":
    MAX_FILE_SIZE = None  # 不同步文件
elif max_file_size_str == "0":
    MAX_FILE_SIZE = 0  # 无限制
else:
    try:
        MAX_FILE_SIZE = float(max_file_size_str) * 1024 * 1024  # 转换为字节
    except ValueError:
        MAX_FILE_SIZE = None
        print(f"⚠️  配置项 max_file_size 格式错误: {max_file_size_str}，将不同步文件")

DEVICE_ID = f"{platform.node()}-{uuid.uuid4().hex[:6]}"
last_clipboard_text = ""
last_clipboard_files = []  # 记录上次的文件列表
last_clipboard_hash = None  # 记录上次剪贴板内容的哈希值（统一用于文本/文件/图片）
last_received_hash = None  # 记录最后接收内容的哈希，避免重复上传
last_received_file = None  # 记录最后接收的文件路径（用于文件比较）
last_received_time = 0  # 记录接收时间
last_sync_time = None
stop_flag = False
is_setting_clipboard = False  # 标志：正在设置剪贴板（防止检测到自己的设置操作）

# 接收文件后的保护时间（秒）- 在此期间相同文件不会被上传
RECEIVED_FILE_PROTECTION_TIME = 3

# =======================
# 文件处理辅助函数
# =======================
def is_same_file(file1, file2):
    """检查两个文件是否相同（通过文件名和大小）"""
    if not file1 or not file2:
        return False
    
    # 如果是同一个路径，直接返回True
    if os.path.abspath(file1) == os.path.abspath(file2):
        return True
    
    # 比较文件名和大小
    try:
        name1 = os.path.basename(file1)
        name2 = os.path.basename(file2)
        
        if name1 == name2:
            size1 = os.path.getsize(file1) if os.path.exists(file1) else -1
            size2 = os.path.getsize(file2) if os.path.exists(file2) else -1
            
            if size1 == size2 and size1 > 0:
                return True
    except Exception as e:
        print(f"⚠️  文件比较错误: {e}")
    
    return False

def get_clipboard_files():
    """获取剪贴板中的文件列表（使用PyQt5）"""
    try:
        clipboard = QtWidgets.QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasUrls():
            files = []
            for url in mime_data.urls():
                # macOS可能返回file://格式的URL
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    
                    # macOS特殊处理：有时路径可能需要规范化
                    if platform.system() == "Darwin":
                        file_path = os.path.normpath(file_path)
                    
                    if os.path.isfile(file_path):
                        files.append(file_path)
            return files
    except Exception as e:
        print(f"❌ 获取剪贴板文件失败: {e}")
        import traceback
        if platform.system() == "Darwin":
            traceback.print_exc()
    return []

def file_to_base64(file_path):
    """将文件转换为Base64编码"""
    try:
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ 文件编码失败 {file_path}: {e}")
        return None

def base64_to_file(base64_data, file_name, target_dir=None):
    """将Base64数据保存为文件"""
    try:
        if target_dir is None:
            target_dir = tempfile.gettempdir()
        
        file_path = os.path.join(target_dir, file_name)
        
        # 如果文件已存在，添加序号
        if os.path.exists(file_path):
            name, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
                counter += 1
        
        file_data = base64.b64decode(base64_data)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path
    except Exception as e:
        print(f"❌ 文件解码失败: {e}")
        return None

def set_clipboard_file(file_path):
    """将文件设置到剪贴板（仅用于主线程直接调用）"""
    try:
        clipboard = QtWidgets.QApplication.clipboard()
        mime_data = QtCore.QMimeData()
        
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False
        
        file_path = os.path.abspath(file_path)
        url = QtCore.QUrl.fromLocalFile(file_path)
        mime_data.setUrls([url])
        clipboard.setMimeData(mime_data)
        
        print(f"✅ 文件已设置到剪贴板: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 设置文件到剪贴板失败: {e}")
        return False

# =======================
# 图片处理辅助函数
# =======================
def get_clipboard_image():
    """获取剪贴板中的图片"""
    try:
        clipboard = QtWidgets.QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                return image
    except Exception as e:
        print(f"❌ 获取剪贴板图片失败: {e}")
    return None

def image_to_base64(image):
    """将QImage转换为Base64编码的PNG"""
    try:
        buffer = BytesIO()
        # 转换为PNG格式
        byte_array = QtCore.QByteArray()
        buffer_qt = QtCore.QBuffer(byte_array)
        buffer_qt.open(QtCore.QIODevice.WriteOnly)
        image.save(buffer_qt, "PNG")
        buffer_qt.close()
        
        # Base64编码
        return base64.b64encode(byte_array.data()).decode('utf-8')
    except Exception as e:
        print(f"❌ 图片编码失败: {e}")
        return None

def base64_to_image(base64_data):
    """将Base64数据转换为QImage"""
    try:
        image_data = base64.b64decode(base64_data)
        image = QtGui.QImage()
        image.loadFromData(image_data)
        return image if not image.isNull() else None
    except Exception as e:
        print(f"❌ 图片解码失败: {e}")
        return None

def set_clipboard_image(image):
    """将图片设置到剪贴板（仅用于主线程）"""
    try:
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setImage(image)
        return True
    except Exception as e:
        print(f"❌ 设置图片到剪贴板失败: {e}")
        return False

def get_image_hash(image):
    """计算图片的哈希值（用于比较）"""
    try:
        # 使用图片尺寸和部分像素数据生成简单哈希
        width = image.width()
        height = image.height()
        
        # 获取图片数据
        byte_array = QtCore.QByteArray()
        buffer = QtCore.QBuffer(byte_array)
        buffer.open(QtCore.QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        
        # 计算哈希
        import hashlib
        return hashlib.md5(byte_array.data()).hexdigest()
    except Exception as e:
        print(f"⚠️  图片哈希计算失败: {e}")
        return None

def calculate_content_hash(content):
    """计算内容哈希（文本/文件数据/图片数据的统一哈希）"""
    try:
        import hashlib
        if isinstance(content, str):
            # 文本内容
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif isinstance(content, bytes):
            # 二进制数据（文件/图片）
            return hashlib.md5(content).hexdigest()
        else:
            return None
    except Exception as e:
        print(f"⚠️  哈希计算失败: {e}")
        return None

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
def upload_clipboard(tray_app, content_type="text", text="", file_path=None, image=None):
    
    """上传剪贴板内容到服务端"""
    try:
        if content_type == "image" and image:
            # 上传图片
            image_data = image_to_base64(image)
            if image_data is None:
                print(f"❌ 图片编码失败")
                return
            
            # 计算哈希
            content_hash = get_image_hash(image)
            
            image_size = len(image_data)
            width = image.width()
            height = image.height()
            
            requests.post(f"{SERVER_URL}/upload", json={
                "device_id": DEVICE_ID,
                "content_type": "image",
                "content_hash": content_hash,
                "image_data": image_data,
                "image_width": width,
                "image_height": height,
                "image_size": image_size
            }, timeout=15)
            
            if ENABLE_POPUP:
                tray_app.safe_notify(
                    "📤 图片同步",
                    f"已上传: {width}x{height} ({image_size/1024:.1f}KB)",
                    QtWidgets.QSystemTrayIcon.Information,
                    2000
                )
            play_sound()
            print(f"↑ 已上传图片: {width}x{height} ({image_size/1024:.1f}KB)")
            
        elif content_type == "file" and file_path:
            # 上传文件
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_data = file_to_base64(file_path)
            
            if file_data is None:
                print(f"❌ 文件编码失败: {file_path}")
                return
            
            # 计算文件哈希（基于文件名+大小+部分内容）
            content_hash = calculate_content_hash(f"{file_name}:{file_size}:{file_data[:100]}")
            
            requests.post(f"{SERVER_URL}/upload", json={
                "device_id": DEVICE_ID,
                "content_type": "file",
                "content_hash": content_hash,
                "file_name": file_name,
                "file_data": file_data,
                "file_size": file_size
            }, timeout=10)
            
            if ENABLE_POPUP:
                tray_app.safe_notify(
                    "📤 文件同步",
                    f"已上传: {file_name} ({file_size/1024:.1f}KB)",
                    QtWidgets.QSystemTrayIcon.Information,
                    2000
                )
            play_sound()
            print(f"↑ 已上传文件: {file_name} ({file_size/1024:.1f}KB)")
        else:
            # 上传文本
            content_hash = calculate_content_hash(text)
            
            requests.post(f"{SERVER_URL}/upload", json={
                "device_id": DEVICE_ID,
                "content_type": "text",
                "content_hash": content_hash,
                "content": text
            }, timeout=3)
            
            if ENABLE_POPUP:
                tray_app.safe_notify(
                    "📤 剪贴板同步",
                    "上传成功",
                    QtWidgets.QSystemTrayIcon.Information,
                    2000
                )
            play_sound()
            print(f"↑ 已上传文本: {text[:30]!r}")
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
    global last_clipboard_text, last_clipboard_files, last_clipboard_hash
    global last_received_file, last_received_hash, last_received_time
    global is_setting_clipboard
    
    # macOS调试模式
    macos_debug = platform.system() == "Darwin" and os.environ.get("SYNCCLIP_DEBUG") == "1"
    
    while not stop_flag:
        try:
            # 检查是否正在设置剪贴板（优先级最高）
            if is_setting_clipboard:
                time.sleep(0.3)
                continue
            
            # 检查是否在保护期内（接收内容后的3秒内不检测剪贴板变化）
            if last_received_time > 0:
                elapsed = time.time() - last_received_time
                if elapsed <= RECEIVED_FILE_PROTECTION_TIME:
                    # 保护期内，跳过剪贴板检测
                    if os.environ.get("SYNCCLIP_DEBUG") == "1":
                        print(f"🛡️  保护期中 ({elapsed:.1f}s / {RECEIVED_FILE_PROTECTION_TIME}s)")
                    time.sleep(0.3)
                    continue
                else:
                    # 保护期已过，清除记录
                    if last_received_hash:
                        print(f"🕐 接收内容保护期已过，恢复剪贴板检测")
                        last_received_hash = None
                        last_received_file = None
                        last_received_time = 0
            
            # 优先检查文件
            current_files = get_clipboard_files()
            
            if macos_debug and current_files:
                print(f"🔍 [macOS调试] 检测到文件: {current_files}")
            
            if current_files and current_files != last_clipboard_files:
                # 剪贴板有文件且发生变化
                file_path = current_files[0]
                last_clipboard_files = current_files
                
                # 检查是否启用文件同步
                if MAX_FILE_SIZE is None:
                    # 不同步文件（静默）
                    print(f"⏭️  检测到文件，但文件同步已禁用")
                else:
                    # 只同步第一个文件
                    file_size = os.path.getsize(file_path)
                    file_name = os.path.basename(file_path)
                    
                    # 检查文件大小限制
                    if MAX_FILE_SIZE == 0 or file_size <= MAX_FILE_SIZE:
                        # 可以同步
                        upload_clipboard(tray_app, content_type="file", file_path=file_path)
                    else:
                        # 文件超出限制
                        max_mb = MAX_FILE_SIZE / (1024 * 1024)
                        file_mb = file_size / (1024 * 1024)
                        print(f"⚠️  文件过大: {file_name} ({file_mb:.1f}MB > {max_mb:.1f}MB)")
                        if ENABLE_POPUP:
                            tray_app.safe_notify(
                                "⚠️  文件过大",
                                f"{file_name}\n大小 {file_mb:.1f}MB 超出限制 {max_mb:.1f}MB",
                                QtWidgets.QSystemTrayIcon.Warning,
                                3000
                            )
            elif not current_files:
                # 剪贴板中没有文件，检查图片
                current_image = get_clipboard_image()
                
                if current_image:
                    # 有图片数据
                    image_hash = get_image_hash(current_image)
                    
                    # 调试信息
                    if os.environ.get("SYNCCLIP_DEBUG") == "1":
                        print(f"🔍 [图片调试] 当前哈希: {image_hash[:8] if image_hash else 'None'}... 上次哈希: {last_clipboard_hash[:8] if last_clipboard_hash else 'None'}...")
                    
                    if image_hash and image_hash != last_clipboard_hash:
                        # 图片发生变化
                        last_clipboard_hash = image_hash
                        last_clipboard_files = []
                        
                        # 检查图片大小
                        image_data = image_to_base64(current_image)
                        if image_data:
                            image_size = len(image_data)
                            
                            # 使用文件大小限制（如果启用）
                            if MAX_FILE_SIZE is None:
                                print(f"⏭️  检测到图片，但文件同步已禁用")
                            elif MAX_FILE_SIZE == 0 or image_size <= MAX_FILE_SIZE:
                                # 可以同步
                                upload_clipboard(tray_app, content_type="image", image=current_image)
                            else:
                                # 图片过大
                                max_mb = MAX_FILE_SIZE / (1024 * 1024)
                                image_mb = image_size / (1024 * 1024)
                                print(f"⚠️  图片过大: {current_image.width()}x{current_image.height()} ({image_mb:.1f}MB > {max_mb:.1f}MB)")
                                if ENABLE_POPUP:
                                    tray_app.safe_notify(
                                        "⚠️  图片过大",
                                        f"{current_image.width()}x{current_image.height()}\n大小 {image_mb:.1f}MB 超出限制 {max_mb:.1f}MB",
                                        QtWidgets.QSystemTrayIcon.Warning,
                                        3000
                                    )
                else:
                    # 没有图片，检查文本
                    current_text = pyperclip.paste()
                    if current_text != last_clipboard_text:
                        last_clipboard_text = current_text
                        last_clipboard_files = []
                        last_clipboard_image_hash = None
                        upload_clipboard(tray_app, content_type="text", text=current_text)
        except Exception as e:
            print("❌ 剪贴板监听错误:", e)
        time.sleep(0.5)

def sync_from_server(tray_app):
    """定时从服务端拉取更新"""
    global last_sync_time, last_clipboard_text, last_clipboard_files, last_clipboard_image_hash
    global last_received_file, last_received_image_hash, last_received_time
    global last_sync_time, last_clipboard_text, last_clipboard_files, last_clipboard_image_hash
    global last_received_file, last_received_image_hash, last_received_time
    while not stop_flag:
        data = fetch_clipboard()
        if data and data.get("updated_at"):
            updated_at = data["updated_at"]
            if (not last_sync_time) or updated_at > last_sync_time:
                # 跳过自己上传的内容
                if data.get("device_id") != DEVICE_ID:
                    content_type = data.get("content_type", "text")
                    
                    if content_type == "image":
                        # 处理图片同步
                        image_data = data.get("image_data")
                        image_width = data.get("image_width", 0)
                        image_height = data.get("image_height", 0)
                        image_size = data.get("image_size", 0)
                        content_hash = data.get("content_hash")  # 直接使用服务器传来的哈希
                        
                        if image_data:
                            # 解码图片
                            image = base64_to_image(image_data)
                            if image:
                                # 必须在设置到剪贴板之前就更新所有状态
                                # 设置标志：正在设置剪贴板（让clipboard_watcher跳过检测）
                                is_setting_clipboard = True
                                last_received_hash = content_hash
                                last_clipboard_hash = content_hash
                                last_received_time = time.time()
                                last_clipboard_files = []
                                
                                # 使用线程安全的方法设置图片到剪贴板
                                tray_app.safe_set_image(image)
                                
                                # 调试信息
                                if os.environ.get("SYNCCLIP_DEBUG") == "1":
                                    print(f"🔍 [接收] 图片已设置，哈希: {content_hash[:8] if content_hash else 'None'}...")
                                
                                print(f"↓ 从服务端同步图片: {image_width}x{image_height} ({image_size/1024:.1f}KB)")
                                if ENABLE_POPUP:
                                    tray_app.safe_notify(
                                        "📥 图片同步",
                                        f"已接收: {image_width}x{image_height}\n💡 按 Ctrl+V 可直接粘贴",
                                        QtWidgets.QSystemTrayIcon.Information,
                                        4000
                                    )
                                play_sound()
                                
                    elif content_type == "file":
                        # 处理文件同步
                        file_name = data.get("file_name")
                        file_data = data.get("file_data")
                        file_size = data.get("file_size", 0)
                        content_hash = data.get("content_hash")  # 直接使用服务器传来的哈希
                        
                        if file_name and file_data:
                            # 保存文件到临时目录
                            saved_path = base64_to_file(file_data, file_name)
                            if saved_path:
                                # 必须在设置到剪贴板之前就更新状态
                                is_setting_clipboard = True
                                last_received_hash = content_hash
                                last_clipboard_hash = content_hash
                                last_received_file = saved_path
                                last_clipboard_files = [saved_path]
                                last_received_time = time.time()
                                
                                # 使用线程安全的方法设置文件到剪贴板
                                tray_app.safe_set_file(saved_path)
                                print(f"↓ 从服务端同步文件: {file_name} ({file_size/1024:.1f}KB)")
                                if ENABLE_POPUP:
                                    tray_app.safe_notify(
                                        "📥 文件同步",
                                        f"已接收: {file_name}\n💡 按 Ctrl+V 可直接粘贴",
                                        QtWidgets.QSystemTrayIcon.Information,
                                        4000
                                    )
                                play_sound()
                    else:
                        # 处理文本同步
                        new_text = data.get("content", "")
                        content_hash = data.get("content_hash")  # 直接使用服务器传来的哈希
                        
                        if new_text != last_clipboard_text:
                            # 在设置剪贴板之前更新状态
                            is_setting_clipboard = True
                            last_received_hash = content_hash
                            last_clipboard_hash = content_hash
                            last_received_time = time.time()
                            
                            pyperclip.copy(new_text)
                            last_clipboard_text = new_text
                            last_clipboard_files = []
                            is_setting_clipboard = False  # 文本设置是同步的，立即清除标志
                            print(f"↓ 从服务端同步文本: {new_text[:30]!r}")
                            if ENABLE_POPUP:
                                tray_app.safe_notify(
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
    # 定义自定义信号（必须在类级别定义）
    notify_signal = QtCore.pyqtSignal(str, str, int, int)  # title, message, icon, duration
    set_file_signal = QtCore.pyqtSignal(str)  # file_path - 在主线程设置文件到剪贴板
    set_image_signal = QtCore.pyqtSignal(object)  # QImage - 在主线程设置图片到剪贴板
    set_image_signal = QtCore.pyqtSignal(object)  # QImage - 在主线程设置图片到剪贴板
    
    def __init__(self, icon, parent=None):
        super(ClipboardTrayApp, self).__init__(icon, parent)
        
        # 关键：先显示托盘图标，Windows需要这样才能显示通知
        self.show()
        
        self.setToolTip(f"📋 {APP_NAME} v{APP_VERSION}")
        self.menu = QtWidgets.QMenu(parent)
        
        # 连接信号到槽函数
        self.notify_signal.connect(self._show_notification)
        self.set_file_signal.connect(self._set_file_to_clipboard)
        self.set_image_signal.connect(self._set_image_to_clipboard)
        self.set_image_signal.connect(self._set_image_to_clipboard)
        
        # Windows特定：设置AppUserModelID
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    f"{APP_NAME}.SyncClipboard.App.{APP_VERSION}"
                )
                print("✅ 已设置Windows AppUserModelID")
            except Exception as e:
                print(f"⚠️  设置AppUserModelID失败: {e}")

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

        # 延迟显示启动通知（Windows需要等托盘图标完全初始化）
        if ENABLE_POPUP:
            QtCore.QTimer.singleShot(500, self._show_startup_notification)
    
    def _show_startup_notification(self):
        """显示启动通知"""
        self.showMessage(
            f"📋 {APP_NAME}",
            f"v{APP_VERSION} 已启动（同步间隔 {SYNC_INTERVAL}s）",
            QtWidgets.QSystemTrayIcon.Information,
            2500
        )
        print(f"✅ 启动通知已显示")
    
    def _show_notification(self, title, message, icon, duration):
        """在主线程中显示通知（槽函数）"""
        # 确保托盘图标可见
        if not self.isVisible():
            self.show()
        
        print(f"📢 [通知] {title}: {message}")
        self.showMessage(title, message, icon, duration)
    
    def safe_notify(self, title, message, icon=QtWidgets.QSystemTrayIcon.Information, duration=2000):
        """线程安全的通知方法"""
        self.notify_signal.emit(title, message, icon, duration)
    
    def _set_file_to_clipboard(self, file_path):
        """在主线程中设置文件到剪贴板（槽函数）"""
        global is_setting_clipboard
        try:
            clipboard = QtWidgets.QApplication.clipboard()
            mime_data = QtCore.QMimeData()
            
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                is_setting_clipboard = False
                return
            
            # 使用绝对路径
            file_path = os.path.abspath(file_path)
            
            url = QtCore.QUrl.fromLocalFile(file_path)
            mime_data.setUrls([url])
            
            clipboard.setMimeData(mime_data)
            
            print(f"✅ 文件已设置到剪贴板: {file_path}")
            print(f"💡 现在可以按 Ctrl+V 粘贴文件")
            
        except Exception as e:
            print(f"❌ 设置文件到剪贴板失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清除标志，允许clipboard_watcher继续检测
            is_setting_clipboard = False
    
    def safe_set_file(self, file_path):
        """线程安全的文件设置方法"""
        self.set_file_signal.emit(file_path)
    
    def _set_image_to_clipboard(self, image):
        """在主线程中设置图片到剪贴板（槽函数）"""
        global is_setting_clipboard
        try:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setImage(image)
            
            print(f"✅ 图片已设置到剪贴板: {image.width()}x{image.height()}")
            print(f"💡 现在可以按 Ctrl+V 粘贴图片")
            
        except Exception as e:
            print(f"❌ 设置图片到剪贴板失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清除标志，允许clipboard_watcher继续检测（但仍有3秒保护期）
            is_setting_clipboard = False
    
    def safe_set_image(self, image):
        """线程安全的图片设置方法"""
        self.set_image_signal.emit(image)

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
                self.safe_notify("📋 手动同步", "已从服务端更新内容", QtWidgets.QSystemTrayIcon.Information, 2000)
            play_sound()
        else:
            if ENABLE_POPUP:
                self.safe_notify("📋 手动同步", "未获取到有效数据", QtWidgets.QSystemTrayIcon.Warning, 2000)

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
    
    # Windows特定设置
    if platform.system() == "Windows":
        app.setQuitOnLastWindowClosed(False)  # 防止没有窗口时退出
    
    # 加载应用图标
    if APP_ICON and os.path.exists(APP_ICON):
        icon = QtGui.QIcon(APP_ICON)
    else:
        icon = QtGui.QIcon.fromTheme("edit-paste")
        # 如果主题图标不可用，创建一个简单图标
        if icon.isNull():
            pixmap = QtGui.QPixmap(32, 32)
            pixmap.fill(QtGui.QColor(30, 144, 255))
            icon = QtGui.QIcon(pixmap)
    
    tray_app = ClipboardTrayApp(icon)
    
    # 诊断信息
    print(f"🧩 {APP_NAME} v{APP_VERSION} 已启动")
    print(f"📱 设备ID: {DEVICE_ID}")
    print(f"🔗 服务端地址: {SERVER_URL}")
    print(f"🖥️  操作系统: {platform.system()}")
    print(f"⚙️  系统托盘可用: {QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()}")
    print(f"⚙️  支持通知消息: {tray_app.supportsMessages()}")
    
    # 文件同步配置信息
    if MAX_FILE_SIZE is None:
        print(f"📁 文件同步: 已禁用")
    elif MAX_FILE_SIZE == 0:
        print(f"📁 文件同步: 已启用（无大小限制）")
    else:
        print(f"📁 文件同步: 已启用（限制 {MAX_FILE_SIZE/(1024*1024):.1f}MB）")
    
    if not tray_app.supportsMessages():
        print("⚠️  警告: 当前系统不支持托盘通知！")
        print("💡 请检查Windows通知设置:")
        print("   设置 -> 系统 -> 通知和操作")
        print("   确保'获取来自应用和其他发送者的通知'已开启")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
