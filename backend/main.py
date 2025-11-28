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

# --- 配置 ---
FRONTEND_DIST_DIR = "../frontend/dist"
PORT = 8888

app = FastAPI(title="Server Panel API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker 初始化
try:
    client = docker.from_env()
    print("✅ Docker 连接成功")
except Exception as e:
    print(f"❌ Docker 连接失败: {e}")
    client = None

# --- 数据模型 ---
class ProjectCreate(BaseModel):
    name: str
    image: str
    command: Optional[str] = None
    # 端口配置
    host_port: Optional[int] = None      # 宿主机端口
    container_port: int = 80             # 容器端口 (默认80)
    # 目录挂载配置
    volume_host: Optional[str] = None    # 宿主机路径 (如 /root/code)
    volume_container: Optional[str] = None # 容器内路径 (如 /app)

# --- API ---

@app.get("/api/system/status")
def get_system_status():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent
    }

@app.get("/api/projects")
def list_projects():
    if not client: return []
    try:
        containers = client.containers.list(all=True)
        results = []
        for c in containers:
            # 1. 解析端口
            ports_list = []
            ports_data = c.attrs['NetworkSettings']['Ports'] or {}
            for internal_proto, external_list in ports_data.items():
                internal_port = internal_proto.split('/')[0]
                if external_list:
                    for item in external_list:
                        if item.get('HostPort'):
                            ports_list.append(f"{item['HostPort']}->{internal_port}")
            
            ports_display = ", ".join(ports_list) if ports_list else "无端口"
            
            # 2. 解析挂载 (只显示第一个挂载点，避免太长)
            mounts = c.attrs.get('HostConfig', {}).get('Binds', [])
            # Docker API 返回格式通常是 ["/host/path:/container/path:rw"]
            mount_display = mounts[0].split(':')[0] if mounts else "无挂载"

            results.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "ports": ports_display,
                "mounts": mount_display,
                "url": f"http://localhost:{ports_list[0].split('->')[0]}" if ports_list else ""
            })
        return results
    except Exception as e:
        print(f"List Error: {e}")
        return []

@app.post("/api/project/create")
def create_project(project: ProjectCreate):
    if not client: raise HTTPException(500, "Docker not connected")
    try:
        kwargs = {
            "image": project.image,
            "name": project.name,
            "detach": True,
            "restart_policy": {"Name": "always"}
        }

        # 1. 配置端口映射
        if project.host_port:
            kwargs['ports'] = {f"{project.container_port}/tcp": project.host_port}

        # 2. 配置目录挂载
        if project.volume_host and project.volume_container:
            # 格式: {'宿主机绝对路径': {'bind': '容器内路径', 'mode': 'rw'}}
            kwargs['volumes'] = {
                project.volume_host: {'bind': project.volume_container, 'mode': 'rw'}
            }
            # 关键：自动将容器的工作目录切换到挂载点，这样 python main.py 才能找到文件
            kwargs['working_dir'] = project.volume_container

        # 3. 配置启动命令
        if project.command:
            kwargs['command'] = project.command
        else:
            # 如果没填命令且是 Python 镜像，给个保活命令防止退出
            if "python" in project.image.lower():
                kwargs['command'] = "python -c 'import time; print(\"Container Started\"); [time.sleep(60) for _ in range(100000)]'"

        # 4. 拉取镜像
        try:
            client.images.get(project.image)
        except docker.errors.ImageNotFound:
            client.images.pull(project.image)

        container = client.containers.run(**kwargs)
        return {"status": "success", "id": container.short_id}

    except Exception as e:
        print(f"Create Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/project/{action}")
def manage_project(action: str, container_id: str = Body(..., embed=True)):
    if not client: raise HTTPException(500, "Docker not connected")
    try:
        container = client.containers.get(container_id)
        if action == "stop": container.stop()
        elif action == "start": container.start()
        elif action == "restart": container.restart()
        elif action == "remove": container.remove(force=True)
        return {"status": "success", "action": action}
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.websocket("/api/ws/logs/{container_id}")
async def websocket_endpoint(websocket: WebSocket, container_id: str):
    await websocket.accept()
    if not client: await websocket.close(); return
    try:
        container = client.containers.get(container_id)
        # 发送历史日志
        logs = container.logs(tail=100, stream=False)
        if logs: await websocket.send_text(logs.decode('utf-8', errors='ignore'))
        
        # 保持连接
        while True:
            if websocket.client_state.name == "DISCONNECTED": break
            await asyncio.sleep(2)
    except: pass
    finally:
        try: await websocket.close()
        except: pass

# 托管静态文件 (必须在最后)
if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)