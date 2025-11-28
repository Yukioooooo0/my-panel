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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    host_port: Optional[int] = None
    container_port: int = 80
    volume_host: Optional[str] = None
    volume_container: Optional[str] = None
    # ✅ 新增：端口备注字段
    port_remark: Optional[str] = None

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
                            ports_list.append(f"{item['HostPort']}→{internal_port}")
            
            ports_display = ", ".join(ports_list) if ports_list else "无"
            
            # 2. 解析挂载
            mounts = c.attrs.get('HostConfig', {}).get('Binds', [])
            mount_display = mounts[0].split(':')[0] if mounts else "无"

            # 3. ✅ 读取备注 (从 Labels 获取)
            # 我们约定 key 为 "panel.port_remark"
            remark = c.labels.get("panel.port_remark", "")

            results.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "ports": ports_display,
                "mounts": mount_display,
                "remark": remark, # 返回给前端
                "url": f"http://localhost:{ports_list[0].split('→')[0]}" if ports_list else ""
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
            "restart_policy": {"Name": "always"},
            # ✅ 新增：将备注写入 Labels
            "labels": {"panel.port_remark": project.port_remark or ""}
        }

        if project.host_port:
            kwargs['ports'] = {f"{project.container_port}/tcp": project.host_port}

        if project.volume_host and project.volume_container:
            kwargs['volumes'] = {project.volume_host: {'bind': project.volume_container, 'mode': 'rw'}}
            kwargs['working_dir'] = project.volume_container

        if project.command:
            kwargs['command'] = project.command
        else:
            if "python" in project.image.lower():
                kwargs['command'] = "python -c 'import time; print(\"Container Started\"); [time.sleep(60) for _ in range(100000)]'"

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
        logs = container.logs(tail=100, stream=False)
        if logs: await websocket.send_text(logs.decode('utf-8', errors='ignore'))
        while True:
            if websocket.client_state.name == "DISCONNECTED": break
            await asyncio.sleep(2)
    except: pass
    finally:
        try: await websocket.close()
        except: pass

if os.path.exists(FRONTEND_DIST_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)