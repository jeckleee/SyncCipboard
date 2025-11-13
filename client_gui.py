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
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore

# =======================
# 读取配置文件
# =======================
SINGLE_INSTANCE_MUTEX = None

def ensure_single_instance_windows(app_name: str) -> bool:
    """Windows: 通过命名互斥量确保单实例运行"""
    if platform.system() != "Windows":
        return True
    try:
        import ctypes
        import ctypes.wintypes as wintypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = f"Global\\{app_name}_SingleInstance_Mutex"
        # CreateMutexW(lpMutexAttributes, bInitialOwner, lpName)
        handle = kernel32.CreateMutexW(None, False, wintypes.LPCWSTR(mutex_name))
        # GetLastError == 183 (ERROR_ALREADY_EXISTS) 表示已存在
        last_error = kernel32.GetLastError()
        if last_error == 183 or handle == 0:
            return False
        # 保存句柄，防止被 GC 回收
        global SINGLE_INSTANCE_MUTEX
        SINGLE_INSTANCE_MUTEX = handle
        return True
    except Exception:
        # 出现异常时不阻止运行（降级）
        return True
def ensure_qt_plugin_paths():
    """确保 Qt 插件路径包含 imageformats/iconengines，避免 ICO/ICNS 无法解码"""
    try:
        candidates = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.extend([
            os.path.join(base_dir, "qt-plugins"),
            os.path.join(base_dir, "PyQt5", "qt-plugins"),
            os.path.join(base_dir, "PyQt5", "Qt", "plugins"),
        ])
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            candidates.extend([
                os.path.join(exe_dir, "qt-plugins"),
                os.path.join(exe_dir, "PyQt5", "qt-plugins"),
                os.path.join(exe_dir, "PyQt5", "Qt", "plugins"),
            ])
        for p in list(candidates):
            candidates.append(os.path.join(p, "imageformats"))
            candidates.append(os.path.join(p, "iconengines"))
        seen = set()
        for p in candidates:
            if not p or p in seen:
                continue
            seen.add(p)
            if os.path.isdir(p) and p not in QtCore.QCoreApplication.libraryPaths():
                QtCore.QCoreApplication.addLibraryPath(p)
    except Exception:
        pass


def load_icon_with_reader(file_path):
    """使用 QImageReader 读取图像并构造 QIcon（作为 QIcon 失败时的回退）"""
    try:
        reader = QtGui.QImageReader(file_path)
        image = reader.read()
        if image and not image.isNull():
            pixmap = QtGui.QPixmap.fromImage(image)
            if not pixmap.isNull():
                icon = QtGui.QIcon()
                # 提供多个常见尺寸，提升托盘显示适配性
                for size in (16, 20, 22, 24, 32, 40, 48, 64):
                    icon.addPixmap(pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                return icon
    except Exception as _e:
        pass
    return None

def resolve_app_icon():
    """根据平台和配置解析应用图标，保持现有逻辑不变（Windows 优先 ico，失败回退 icns）。"""
    if not APP_ICON:
        return None
    try:
        if platform.system() == "Windows":
            # 先尝试 ico（优先 icon.ico，再尝试与 APP_ICON 同名的 .ico）
            if APP_ICON.endswith(".icns"):
                candidate_names = [
                    "icon.ico",
                    os.path.basename(APP_ICON).replace(".icns", ".ico"),
                ]
                for candidate in candidate_names:
                    icon_path = get_resource_path(candidate)
                    if icon_path and os.path.exists(icon_path):
                        icon_try = QtGui.QIcon(icon_path)
                        if icon_try.isNull():
                            icon_try = load_icon_with_reader(icon_path)
                        if icon_try and not icon_try.isNull():
                            return icon_try
                # 回退：尝试直接加载 icns
                fallback_icon_path = get_resource_path(APP_ICON)
                if fallback_icon_path and os.path.exists(fallback_icon_path):
                    icon_try = QtGui.QIcon(fallback_icon_path)
                    if icon_try.isNull():
                        icon_try = load_icon_with_reader(fallback_icon_path)
                    if icon_try and not icon_try.isNull():
                        return icon_try
                return None
            else:
                # APP_ICON 非 icns，按路径直接加载
                icon_path = get_resource_path(APP_ICON)
                if icon_path and os.path.exists(icon_path):
                    icon_try = QtGui.QIcon(icon_path)
                    return icon_try if not icon_try.isNull() else None
                return None
        else:
            # macOS/Linux
            icon_path = get_resource_path(APP_ICON)
            if icon_path and os.path.exists(icon_path):
                if platform.system() == "Darwin" and icon_path.endswith(".icns"):
                    icon_try = QtGui.QIcon(icon_path)
                    if not icon_try.isNull():
                        pixmap = icon_try.pixmap(44, 44)
                        return QtGui.QIcon(pixmap)
                    return None
                icon_try = QtGui.QIcon(icon_path)
                return icon_try if not icon_try.isNull() else None
            return None
    except Exception:
        return None

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

def get_resource_path(relative_path):
    """获取资源文件路径（兼容打包后的应用）"""
    if not relative_path:
        return ""
    
    # 优先级1: Nuitka 单文件打包后的临时解压目录
    if getattr(sys, 'frozen', False):
        # Nuitka onefile 模式：资源文件被解压到脚本所在的临时目录
        # __file__ 指向临时解压目录中的脚本位置
        try:
            bundle_dir = os.path.dirname(os.path.abspath(__file__))
            resource_path = os.path.join(bundle_dir, relative_path)
            if os.path.exists(resource_path):
                return os.path.abspath(resource_path)
        except Exception:
            pass
        
        # 备选方案：exe 所在目录（用于外部资源文件）
        exe_dir = os.path.dirname(sys.executable)
        resource_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(resource_path):
            return os.path.abspath(resource_path)
    
    # 优先级2: 当前工作目录
    if os.path.exists(relative_path):
        return os.path.abspath(relative_path)
    
    # 优先级3: 脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    resource_path = os.path.join(script_dir, relative_path)
    if os.path.exists(resource_path):
        return os.path.abspath(resource_path)
    
    # 未找到资源文件
    return ""

config = configparser.ConfigParser()
config_file_path = get_config_path()
config.read(config_file_path, encoding="utf-8")
print(f"📝 配置文件路径: {config_file_path}")

# 全局配置
APP_NAME = config.get("global", "app_name", fallback="SyncClipboard")
APP_VERSION = config.get("global", "app_version", fallback="1.0.0")
APP_ICON = config.get("global", "app_icon", fallback="")

# 客户端配置
CLIENT_NAME = config.get("client", "client_name", fallback=platform.node()).strip('"\'')
URL_PREFIX = config.get("server", "url_prefix", fallback="")
SERVER_URL = f"{config.get('client', 'server_url', fallback='http://127.0.0.1:8000')}{URL_PREFIX}"
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
last_sync_time = None  # 最后一次从服务器同步的时间（服务器的updated_at）
last_sync_download_time = 0  # 最后一次实际下载内容的本地时间戳（用于保护期）
last_downloaded_file = None  # 最后一次下载的文件路径（用于清理）
stop_flag = False
is_setting_clipboard = False  # 标志：正在设置剪贴板（防止检测到自己的设置操作）
SYNC_PROTECTION_SECONDS = 2  # 同步保护时间（秒）

# 上传下载开关
allow_upload = True  # 允许上传数据
allow_download = True  # 允许下载数据

# =======================
# HTTP Session 配置（启用 Keep-Alive）
# =======================
http_session = requests.Session()
# 配置连接池：最大连接数和keep-alive
adapter = requests.adapters.HTTPAdapter(
    pool_connections=10,  # 连接池大小
    pool_maxsize=20,      # 最大连接数
    max_retries=0,        # 不自动重试（避免重复上传）
    pool_block=False
)
http_session.mount('http://', adapter)
http_session.mount('https://', adapter)
# 设置默认请求头，明确启用 keep-alive
http_session.headers.update({
    'Connection': 'keep-alive',
    'Keep-Alive': 'timeout=30, max=100'
})

# =======================
# 辅助函数
# =======================
def get_timestamp():
    """获取当前时间戳字符串（精确到毫秒）"""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

# =======================
# 文件处理辅助函数
# =======================
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
                return
            
            image_size = len(image_data)
            width = image.width()
            height = image.height()
            
            response = http_session.post(f"{SERVER_URL}/upload", json={
                "device_id": DEVICE_ID,
                "client_name": CLIENT_NAME,
                "content_type": "image",
                "image_data": image_data,
                "image_width": width,
                "image_height": height,
                "image_size": image_size
            }, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ 上传图片成功: {width}x{height} ({image_size/1024:.1f}KB) | {get_timestamp()}")
                
                if ENABLE_POPUP:
                    tray_app.safe_notify(
                        "📤 图片同步",
                        f"已上传: {width}x{height} ({image_size/1024:.1f}KB)",
                        QtWidgets.QSystemTrayIcon.Information,
                        2000
                    )
                play_sound()
            
        elif content_type == "file" and file_path:
            # 上传文件
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_data = file_to_base64(file_path)
            
            if file_data is None:
                return
            
            response = http_session.post(f"{SERVER_URL}/upload", json={
                "device_id": DEVICE_ID,
                "client_name": CLIENT_NAME,
                "content_type": "file",
                "file_name": file_name,
                "file_data": file_data,
                "file_size": file_size
            }, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ 上传文件成功: {file_name} ({file_size/1024:.1f}KB) | {get_timestamp()}")
                
                if ENABLE_POPUP:
                    tray_app.safe_notify(
                        "📤 文件同步",
                        f"已上传: {file_name} ({file_size/1024:.1f}KB)",
                        QtWidgets.QSystemTrayIcon.Information,
                        2000
                    )
                play_sound()
        else:
            # 上传文本
            text_preview = text[:30] if len(text) <= 30 else text[:30] + "..."
            
            response = http_session.post(f"{SERVER_URL}/upload", json={
                "device_id": DEVICE_ID,
                "client_name": CLIENT_NAME,
                "content_type": "text",
                "content": text
            }, timeout=3)
            
            if response.status_code == 200:
                print(f"✅ 上传文本成功: {text_preview!r} | {get_timestamp()}")
                
                if ENABLE_POPUP:
                    tray_app.safe_notify(
                        "📤 剪贴板同步",
                        "上传成功",
                        QtWidgets.QSystemTrayIcon.Information,
                        2000
                    )
                play_sound()
    except Exception as e:
        pass

def fetch_clipboard(last_sync_time=None):
    """从服务端拉取最新内容"""
    try:
        params = {}
        if last_sync_time:
            params["last_sync_time"] = last_sync_time
        
        r = http_session.get(f"{SERVER_URL}/fetch", params=params, timeout=3)
        return r.json()
    except Exception as e:
        print("❌ 拉取失败:", e)
        return None

def clipboard_watcher(tray_app):
    """监听剪贴板变化并上传（带3秒保护期）"""
    global is_setting_clipboard, last_sync_download_time, allow_upload
    
    # 用于检测是否真正发生变化的缓存
    last_text = ""
    last_files = []
    last_image_data = None

    def skip_recent_download_guard() -> bool:
        """距离上次下载过短则跳过上传，并按原样打印提示与等待。"""
        if last_sync_download_time > 0:
            elapsed = time.time() - last_sync_download_time
            if elapsed < SYNC_PROTECTION_SECONDS:
                print(f"🛡️ 距离上次下载 {elapsed:.1f}s < {SYNC_PROTECTION_SECONDS}s，跳过上传")
                time.sleep(0.5)
                return True
        return False

    while not stop_flag:
        try:
            # 优先级0：检查是否允许上传
            if not allow_upload:
                time.sleep(0.5)
                continue
            
            # 优先级1：正在设置剪贴板，跳过
            if is_setting_clipboard:
                time.sleep(0.3)
                continue

            # 开始检测剪贴板内容
            # 优先级1：文件
            current_files = get_clipboard_files()
            if current_files and current_files != last_files:
                last_files = current_files
                last_text = ""
                last_image_data = None
                
                if skip_recent_download_guard():
                    continue
                
                file_path = current_files[0]
                has_directory = any(os.path.isdir(path) for path in current_files)

                if has_directory:
                    if ENABLE_POPUP:
                        tray_app.safe_notify(
                            "⛔️ 不支持的剪贴板类型",
                            "当前版本暂不支持同步文件夹内容",
                            QtWidgets.QSystemTrayIcon.Warning,
                            3000
                        )
                    time.sleep(0.5)
                    continue

                if MAX_FILE_SIZE is not None:
                    file_size = os.path.getsize(file_path)
                    file_name = os.path.basename(file_path)

                    if MAX_FILE_SIZE == 0 or file_size <= MAX_FILE_SIZE:
                        upload_clipboard(tray_app, content_type="file", file_path=file_path)
                    else:
                        max_mb = MAX_FILE_SIZE / (1024 * 1024)
                        file_mb = file_size / (1024 * 1024)
                        if ENABLE_POPUP:
                            tray_app.safe_notify(
                                "⚠️  文件过大",
                                f"{file_name}\n大小 {file_mb:.1f}MB 超出限制 {max_mb:.1f}MB",
                                QtWidgets.QSystemTrayIcon.Warning,
                                3000
                            )
            
            # 优先级2：图片（如果没有文件）
            elif not current_files:
                current_image = get_clipboard_image()
                if current_image:
                    # 简单比较：将图片转为base64字符串
                    image_data = image_to_base64(current_image)
                    if image_data and image_data != last_image_data:
                        last_image_data = image_data
                        last_text = ""
                        last_files = []
                        
                        if skip_recent_download_guard():
                            continue
                        
                        image_size = len(image_data)
                        if MAX_FILE_SIZE and (MAX_FILE_SIZE == 0 or image_size <= MAX_FILE_SIZE):
                            upload_clipboard(tray_app, content_type="image", image=current_image)
                        elif MAX_FILE_SIZE:
                            max_mb = MAX_FILE_SIZE / (1024 * 1024)
                            image_mb = image_size / (1024 * 1024)
                            if ENABLE_POPUP:
                                tray_app.safe_notify(
                                    "⚠️  图片过大",
                                    f"{current_image.width()}x{current_image.height()}\n大小 {image_mb:.1f}MB 超出限制 {max_mb:.1f}MB",
                                    QtWidgets.QSystemTrayIcon.Warning,
                                    3000
                                )
                
                # 优先级3：文本（如果既没有文件也没有图片）
                else:
                    current_text = pyperclip.paste()
                    if current_text != last_text:
                        last_text = current_text
                        last_files = []
                        last_image_data = None
                        
                        if skip_recent_download_guard():
                            continue
                        
                        upload_clipboard(tray_app, content_type="text", text=current_text)
        
        except Exception as e:
            print("❌ 剪贴板监听错误:", e)
        
        time.sleep(0.5)

def sync_from_server(tray_app):
    """定时从服务端拉取更新并写入剪贴板"""
    global last_sync_time, is_setting_clipboard, last_sync_download_time, last_downloaded_file, allow_download
    
    while not stop_flag:
        # 检查是否允许下载
        if not allow_download:
            time.sleep(SYNC_INTERVAL)
            continue
        
        # 传入last_sync_time，让服务端判断是否需要返回数据
        data = fetch_clipboard(last_sync_time)
        
        if data:
            # 如果服务端返回 no_update，说明没有新内容，跳过处理
            if data.get("status") == "no_update":
                time.sleep(SYNC_INTERVAL)
                continue
            
            # 有新内容，处理更新
            updated_at = data.get("updated_at")
            if updated_at:
                # 检查是否是自己上传的内容
                if data.get("device_id") == DEVICE_ID:
                    # 是自己上传的，直接更新时间戳，不处理
                    last_sync_time = updated_at
                else:
                    content_type = data.get("content_type", "text")
                    client_name = data.get("client_name", "未知设备")
                    
                    if content_type == "image":
                        # 处理图片同步
                        image_data = data.get("image_data")
                        image_width = data.get("image_width", 0)
                        image_height = data.get("image_height", 0)
                        image_size = data.get("image_size", 0)
                        
                        if image_data:
                            image = base64_to_image(image_data)
                            if image:
                                # 记录下载时间（写入剪贴板之前），用于保护期判断
                                last_sync_download_time = time.time()
                                
                                is_setting_clipboard = True
                                tray_app.safe_set_image(image)
                                
                                print(f"✅ 下载图片成功: {image_width}x{image_height} ({image_size/1024:.1f}KB) | {get_timestamp()}")
                                if ENABLE_POPUP:
                                    tray_app.safe_notify(
                                        "📥 图片同步",
                                        f"已接收到来自[{client_name}]的图片内容\n{image_width}x{image_height}\n💡 按 Ctrl+V 可直接粘贴",
                                        QtWidgets.QSystemTrayIcon.Information,
                                        4000
                                    )
                                play_sound()
                                
                    elif content_type == "file":
                        # 处理文件同步
                        file_name = data.get("file_name")
                        file_data = data.get("file_data")
                        file_size = data.get("file_size", 0)
                        
                        if file_name and file_data:
                            # 删除上一次下载的文件
                            if last_downloaded_file and os.path.exists(last_downloaded_file):
                                try:
                                    os.remove(last_downloaded_file)
                                    print(f"🗑️  已清理上一次的文件: {os.path.basename(last_downloaded_file)}")
                                except Exception as e:
                                    print(f"⚠️  清理文件失败: {e}")
                            
                            saved_path = base64_to_file(file_data, file_name)
                            if saved_path:
                                # 记录本次下载的文件路径
                                last_downloaded_file = saved_path
                                
                                # 记录下载时间（写入剪贴板之前），用于保护期判断
                                last_sync_download_time = time.time()
                                
                                is_setting_clipboard = True
                                tray_app.safe_set_file(saved_path)
                                
                                print(f"✅ 下载文件成功: {file_name} ({file_size/1024:.1f}KB) | {get_timestamp()}")
                                if ENABLE_POPUP:
                                    tray_app.safe_notify(
                                        "📥 文件同步",
                                        f"已接收到来自[{client_name}]的文件内容\n{file_name}\n💡 按 Ctrl+V 可直接粘贴",
                                        QtWidgets.QSystemTrayIcon.Information,
                                        4000
                                    )
                                play_sound()
                    
                    else:
                        # 处理文本同步
                        new_text = data.get("content", "")
                        text_preview = new_text[:30] if len(new_text) <= 30 else new_text[:30] + "..."
                        
                        # 记录下载时间（写入剪贴板之前），用于保护期判断
                        last_sync_download_time = time.time()
                        
                        is_setting_clipboard = True
                        pyperclip.copy(new_text)
                        is_setting_clipboard = False  # 文本设置是同步的，立即清除标志
                        
                        print(f"✅ 下载文本成功: {text_preview!r} | {get_timestamp()}")
                        if ENABLE_POPUP:
                            tray_app.safe_notify(
                                "📥 剪贴板同步",
                                f"已接收到来自[{client_name}]的文本内容",
                                QtWidgets.QSystemTrayIcon.Information,
                                3000
                            )
                        play_sound()
                    
                    # 处理完成，更新时间戳
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
    
    def __init__(self, icon, parent=None):
        super(ClipboardTrayApp, self).__init__(icon, parent)
        
        # 创建托盘图标右键菜单
        self.menu = QtWidgets.QMenu()
        
        # 添加客户端名称（不可点击）
        client_name_action = self.menu.addAction(f"🏷️  {CLIENT_NAME}")
        client_name_action.setEnabled(False)  # 设置为禁用状态，不可点击
        
        # 添加分隔线
        self.menu.addSeparator()
        
        # 添加上传开关
        self.upload_action = self.menu.addAction("📤 允许上传数据")
        self.upload_action.setCheckable(True)
        self.upload_action.setChecked(allow_upload)
        self.upload_action.triggered.connect(self.toggle_upload)
        
        # 添加下载开关
        self.download_action = self.menu.addAction("📥 允许下载数据")
        self.download_action.setCheckable(True)
        self.download_action.setChecked(allow_download)
        self.download_action.triggered.connect(self.toggle_download)
        
        # 添加分隔线
        self.menu.addSeparator()
        
        # 添加退出菜单项
        exit_action = self.menu.addAction("退出")
        exit_action.triggered.connect(self.quit_application)
        
        # 将菜单关联到托盘图标
        self.setContextMenu(self.menu)
        
        # 设置鼠标悬停提示（显示应用名称和版本）
        self.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        
        # 显示托盘图标（确保可以看到图标和右键菜单）
        self.show()
        
        # 连接信号到槽函数
        self.notify_signal.connect(self._show_notification)
        self.set_file_signal.connect(self._set_file_to_clipboard)
        self.set_image_signal.connect(self._set_image_to_clipboard)
        
        # Windows特定：设置AppUserModelID（用于通知）
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    f"{APP_NAME}.SyncClipboard.App.{APP_VERSION}"
                )
                print("✅ 已设置Windows AppUserModelID")
            except Exception as e:
                print(f"⚠️  设置AppUserModelID失败: {e}")

        # 启动后台线程
        threading.Thread(target=clipboard_watcher, args=(self,), daemon=True).start()
        threading.Thread(target=sync_from_server, args=(self,), daemon=True).start()

        # 显示启动通知
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
    
    def _show_notification(self, title, message, icon, duration):
        """在主线程中显示通知（槽函数）"""
        # 确保托盘图标可见
        if not self.isVisible():
            self.show()
        
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
                return
            
            # 使用绝对路径
            file_path = os.path.abspath(file_path)
            url = QtCore.QUrl.fromLocalFile(file_path)
            mime_data.setUrls([url])
            clipboard.setMimeData(mime_data)
            
        except Exception as e:
            pass
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
            
        except Exception as e:
            pass
        finally:
            # 清除标志，允许clipboard_watcher继续检测（但仍有3秒保护期）
            is_setting_clipboard = False
    
    def safe_set_image(self, image):
        """线程安全的图片设置方法"""
        self.set_image_signal.emit(image)
    
    def toggle_upload(self):
        """切换上传开关"""
        global allow_upload
        allow_upload = self.upload_action.isChecked()
        status = "已启用" if allow_upload else "已禁用"
        print(f"📤 上传功能 {status}")
        
        if ENABLE_POPUP:
            self.safe_notify(
                "📤 上传设置",
                f"上传功能{status}",
                QtWidgets.QSystemTrayIcon.Information,
                2000
            )
    
    def toggle_download(self):
        """切换下载开关"""
        global allow_download
        allow_download = self.download_action.isChecked()
        status = "已启用" if allow_download else "已禁用"
        print(f"📥 下载功能 {status}")
        
        if ENABLE_POPUP:
            self.safe_notify(
                "📥 下载设置",
                f"下载功能{status}",
                QtWidgets.QSystemTrayIcon.Information,
                2000
            )
    
    def quit_application(self):
        """退出应用程序"""
        global stop_flag, last_downloaded_file
        print("👋 正在退出应用...")
        
        # 停止后台线程
        stop_flag = True
        
        # 清理最后一次下载的临时文件
        if last_downloaded_file and os.path.exists(last_downloaded_file):
            try:
                os.remove(last_downloaded_file)
                print(f"🗑️  已清理临时文件: {os.path.basename(last_downloaded_file)}")
            except Exception as e:
                print(f"⚠️  清理文件失败: {e}")
        
        # 隐藏托盘图标
        self.hide()
        
        # 退出应用程序
        QtWidgets.QApplication.quit()

# =======================
# 主入口
# =======================
def main():
    # Windows 单实例保护（尽早执行，避免多开）
    if not ensure_single_instance_windows(APP_NAME):
        # 已有实例在运行，直接退出
        return 0

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # 确保 Qt 插件路径就绪（onefile 场景尤为重要）
    ensure_qt_plugin_paths()

    # Windows特定设置
    if platform.system() == "Windows":
        app.setQuitOnLastWindowClosed(False)  # 防止没有窗口时退出
    
    # 加载应用图标
    icon = resolve_app_icon()
    
    # 如果图标加载失败，使用备用方案
    if icon is None or icon.isNull():
        print("⚠️  使用默认图标")
        if platform.system() == "Darwin":
            # macOS：创建一个简单的彩色圆形图标（22x22）
            pixmap = QtGui.QPixmap(44, 44)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(QtGui.QColor(30, 144, 255))
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(2, 2, 18, 18)
            painter.end()
            icon = QtGui.QIcon(pixmap)
        else:
            # Windows/Linux：尝试主题图标或创建方形图标
            icon = QtGui.QIcon.fromTheme("edit-paste")
            if icon.isNull():
                pixmap = QtGui.QPixmap(32, 32)
                pixmap.fill(QtGui.QColor(30, 144, 255))
                icon = QtGui.QIcon(pixmap)

    # 设置应用图标到 QApplication（在某些 Windows 环境可提升托盘图标稳定性）
    try:
        if icon and not icon.isNull():
            app.setWindowIcon(icon)
        else:
            pass
    except Exception as _e:
        pass
    
    # 启动前清空剪贴板，避免脏数据触发同步
    global is_setting_clipboard, last_sync_download_time, last_downloaded_file

    clipboard = QtWidgets.QApplication.clipboard()
    clipboard.clear()
    pyperclip.copy("")

    is_setting_clipboard = False
    last_sync_download_time = 0
    last_downloaded_file = None

    print("🧹 启动时已清空剪贴板")

    tray_app = ClipboardTrayApp(icon)
    try:
        if icon and not icon.isNull():
            tray_app.setIcon(icon)  # 再次显式设置一遍，增强稳定性
    except Exception as _e:
        pass
    
    # 诊断信息
    print(f"🧩 {APP_NAME} v{APP_VERSION} 已启动（后台模式）")
    print(f"🏷️  客户端名称: {CLIENT_NAME}")
    print(f"📱 设备ID: {DEVICE_ID}")
    print(f"🔗 服务端地址: {SERVER_URL}")
    print(f"🔌 HTTP Keep-Alive: 已启用（连接池大小: 10-20）")
    print(f"🖥️  操作系统: {platform.system()}")
    
    # 文件同步配置信息
    if MAX_FILE_SIZE is None:
        print(f"📁 文件同步: 已禁用")
    elif MAX_FILE_SIZE == 0:
        print(f"📁 文件同步: 已启用（无大小限制）")
    else:
        print(f"📁 文件同步: 已启用（限制 {MAX_FILE_SIZE/(1024*1024):.1f}MB）")
    
    print(f"💡 提示: 使用 Ctrl+C 或任务管理器退出程序")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

