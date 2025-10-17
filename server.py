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
    "updated_at": None,
    "device_id": None
}

@app.post("/upload")
async def upload_clipboard(request: Request):
    data = await request.json()
    clipboard_store["content"] = data.get("content", "")
    print(f"↑ 已上传({len(clipboard_store['content'])}字): {clipboard_store['content'][:30]!r}")
    clipboard_store["updated_at"] = datetime.now(timezone.utc).isoformat()
    clipboard_store["device_id"] = data.get("device_id")
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
