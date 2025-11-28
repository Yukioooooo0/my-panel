import os
import time
import asyncio
import docker
import psutil
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

# --- 配置区域 ---
# 前端构建好的静态文件路径
FRONTEND_DIST_DIR = "../frontend/dist"
PORT = 8888

# --- 初始化 APP ---
app = FastAPI(title="Server Panel API")

# 1. 配置跨域 (CORS) - 允许开发环境访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 初始化 Docker 客户端
try:
    client = docker.from_env()
    print("✅ Docker 连接成功")
except Exception as e:
    print(f"❌ Docker 连接失败: {e}")
    print("   请确保 Docker 已安装且 /var/run/docker.sock 已挂载")
    client = None

# --- 数据模型 ---
class ProjectCreate(BaseModel):
    name: str
    image: str
    command: Optional[str] = None
    host_port: Optional[int] = None
    container_port: int = 80

# --- API 路由 ---

@app.get("/api/system/status")
def get_system_status():
    """获取服务器 CPU、内存"""
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

@app.get("/api/projects")
def list_projects():
    """列出所有容器"""
    if not client:
        return []
    
    try:
        containers = client.containers.list(all=True)
        results = []
        
        for c in containers:
            # 解析端口信息
            ports_info = c.attrs['NetworkSettings']['Ports']
            port_display = "No Port"
            url = ""
            type_ = "script"
            
            if ports_info:
                for k, v in ports_info.items():
                    if v:
                        host_port = v[0]['HostPort']
                        port_display = f":{host_port}"
                        # 简单生成访问地址，假设是本机
                        url = f"http://localhost:{host_port}"
                        type_ = "web"
                        break

            results.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status, # running, exited
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "ports": port_display,
                "type": type_,
                "url": url
            })
        return results
    except Exception as e:
        print(f"List Error: {e}")
        return []

@app.post("/api/project/create")
def create_project(project: ProjectCreate):
    """创建并运行新容器"""
    if not client:
        raise HTTPException(500, "Docker client not connected")

    try:
        kwargs = {
            "image": project.image,
            "name": project.name,
            "detach": True,
            "restart_policy": {"Name": "always"}
        }

        # 端口映射
        if project.host_port:
            kwargs['ports'] = {f"{project.container_port}/tcp": project.host_port}
        
        # 启动命令
        if project.command:
            kwargs['command'] = project.command
        else:
            # 防止容器跑完就退出的保活命令 (针对纯 Python 环境)
            if "python" in project.image:
                kwargs['command'] = "python -c 'import time; print(\"App Started\"); [time.sleep(60) for _ in range(100000)]'"

        # 拉取镜像
        try:
            client.images.get(project.image)
        except docker.errors.ImageNotFound:
            client.images.pull(project.image)

        container = client.containers.run(**kwargs)
        return {"status": "success", "id": container.short_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 核心：控制容器状态 (停止/启动) ---
@app.post("/api/project/{action}")
def manage_project(action: str, container_id: str = Body(..., embed=True)):
    """
    action: stop, start, restart, remove
    Body: {"container_id": "xxx"}
    """
    if not client:
        raise HTTPException(500, "Docker not connected")
    
    try:
        container = client.containers.get(container_id)
        if action == "stop":
            container.stop()
        elif action == "start":
            container.start()
        elif action == "restart":
            container.restart()
        elif action == "remove":
            container.remove(force=True)
        else:
            raise HTTPException(400, "Invalid action")
        
        return {"status": "success", "action": action}
    except Exception as e:
        print(f"Manage Error: {e}")
        raise HTTPException(500, detail=str(e))

# --- WebSocket 实时日志 ---
@app.websocket("/api/ws/logs/{container_id}")
async def websocket_endpoint(websocket: WebSocket, container_id: str):
    await websocket.accept()
    
    if not client:
        await websocket.close(reason="Docker not connected")
        return

    try:
        container = client.containers.get(container_id)
        
        # 1. 发送最近 50 行历史日志
        logs = container.logs(tail=50, stream=False)
        if logs:
            await websocket.send_text(logs.decode('utf-8', errors='ignore'))

        # 2. 模拟实时流 (简单轮询方式，兼容性最强)
        # 真正的高并发生产环境建议用 aiodocker，但这里用轮询足够个人使用
        while True:
            if websocket.client_state.name == "DISCONNECTED":
                break
            await asyncio.sleep(2)
            # 心跳或简单状态检查，实际日志靠刷新查看，防止阻塞
            # await websocket.send_text(".") 
            
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# --- 托管静态文件 (必须放在最后) ---
if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)