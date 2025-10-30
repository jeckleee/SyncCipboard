from datetime import datetime, timezone
from fastapi import FastAPI, Request
import uvicorn
import configparser

# 读取配置文件
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")
HOST = config.get("server", "host", fallback="0.0.0.0")
PORT = config.getint("server", "port", fallback=8000)

app = FastAPI()

# 用内存保存剪贴板内容
clipboard_store = {
    "content": "",
    "content_type": "text",  # text, file 或 image
    "file_name": None,       # 文件名（当content_type=file时）
    "file_data": None,       # 文件数据（Base64编码）
    "file_size": 0,          # 文件大小（字节）
    "image_data": None,      # 图片数据（Base64编码的PNG）
    "image_width": 0,        # 图片宽度
    "image_height": 0,       # 图片高度
    "image_size": 0,         # 图片大小（字节）
    "updated_at": None,
    "device_id": None
}

@app.post("/upload")
async def upload_clipboard(request: Request):
    data = await request.json()
    content_type = data.get("content_type", "text")
    
    clipboard_store["content_type"] = content_type
    clipboard_store["device_id"] = data.get("device_id")
    clipboard_store["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if content_type == "image":
        # 图片数据
        clipboard_store["content"] = ""
        clipboard_store["file_name"] = None
        clipboard_store["file_data"] = None
        clipboard_store["file_size"] = 0
        clipboard_store["image_data"] = data.get("image_data")
        clipboard_store["image_width"] = data.get("image_width", 0)
        clipboard_store["image_height"] = data.get("image_height", 0)
        clipboard_store["image_size"] = data.get("image_size", 0)
        print(f"↑ 已上传图片: {clipboard_store['image_width']}x{clipboard_store['image_height']} ({clipboard_store['image_size']/1024:.1f}KB)")
    elif content_type == "file":
        # 文件数据
        clipboard_store["content"] = ""
        clipboard_store["file_name"] = data.get("file_name")
        clipboard_store["file_data"] = data.get("file_data")
        clipboard_store["file_size"] = data.get("file_size", 0)
        clipboard_store["image_data"] = None
        clipboard_store["image_width"] = 0
        clipboard_store["image_height"] = 0
        clipboard_store["image_size"] = 0
        print(f"↑ 已上传文件: {clipboard_store['file_name']} ({clipboard_store['file_size']/1024:.1f}KB)")
    else:
        # 文本数据
        clipboard_store["content"] = data.get("content", "")
        clipboard_store["file_name"] = None
        clipboard_store["file_data"] = None
        clipboard_store["file_size"] = 0
        clipboard_store["image_data"] = None
        clipboard_store["image_width"] = 0
        clipboard_store["image_height"] = 0
        clipboard_store["image_size"] = 0
        print(f"↑ 已上传文本({len(clipboard_store['content'])}字): {clipboard_store['content'][:30]!r}")
    
    return {"status": "ok", "updated_at": clipboard_store["updated_at"]}

@app.get("/fetch")
async def fetch_clipboard():
    return clipboard_store

@app.get("/status")
async def status():
    return {"running": True, "clipboard": clipboard_store}

def start_server():
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    print(f"📡 服务端启动中... http://{HOST}:{PORT}")
    start_server()
