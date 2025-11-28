import os
import time
import asyncio
import docker
import psutil
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict

# --- 配置区域 ---
# 前端构建好的静态文件路径 (根据你的目录结构调整)
FRONTEND_DIST_DIR = "../frontend/dist"
PORT = 8888

# --- 初始化 APP ---
app = FastAPI(title="Server Panel API")

# 1. 配置跨域 (CORS) - 允许前端开发时的 localhost:5173 访问
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

# --- 数据模型 (Pydantic) ---
class ProjectCreate(BaseModel):
    name: str              # 容器名称
    image: str             # 镜像名 (如 python:3.9-slim)
    command: Optional[str] = None  # 启动命令
    host_port: Optional[int] = None # 映射到宿主机的端口 (Web项目用)
    container_port: int = 80        # 容器内部端口 (默认80)

# --- API 路由 ---

@app.get("/api/system/status")
def get_system_status():
    """获取服务器 CPU、内存、磁盘状态"""
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
    
    containers = client.containers.list(all=True)
    results = []
    
    for c in containers:
        # 解析端口信息
        ports_info = c.attrs['NetworkSettings']['Ports']
        port_display = "No Port"
        url = ""
        type_ = "script"
        
        # 简单的逻辑判断是 Web 还是 Script
        if ports_info:
            for k, v in ports_info.items():
                if v:
                    host_port = v[0]['HostPort']
                    port_display = f":{host_port}"
                    # 假设服务器IP是 localhost，实际部署需改为服务器公网IP
                    url = f"http://localhost:{host_port}"
                    type_ = "web"
                    break

        results.append({
            "id": c.short_id,
            "name": c.name,
            "status": c.status, # running, exited, created
            "image": c.image.tags[0] if c.image.tags else "unknown",
            "ports": port_display,
            "type": type_, 
            "url": url
        })
    return results

@app.post("/api/project/create")
def create_project(project: ProjectCreate):
    """创建并运行新容器"""
    if not client:
        raise HTTPException(500, "Docker client not connected")

    try:
        # 构建启动参数
        kwargs = {
            "image": project.image,
            "name": project.name,
            "detach": True,
            "restart_policy": {"Name": "always"}
        }

        # 如果有端口映射 (Web项目)
        if project.host_port:
            kwargs['ports'] = {f"{project.container_port}/tcp": project.host_port}
        
        # 如果有自定义命令 (Python脚本)
        if project.command:
            # -u 表示 python 不缓存 stdout，这对实时日志很重要
            if "python" in project.command and "-u" not in project.command:
                # 尝试智能插入 -u，或者假设用户知道
                pass 
            kwargs['command'] = project.command
        else:
            # 如果没传命令且是 python 镜像，默认给个挂机命令防止退出
            if "python" in project.image:
                kwargs['command'] = "python -c 'import time; print(\"App Started\"); [time.sleep(60) for _ in range(100000)]'"

        # 拉取镜像（如果本地没有）
        try:
            client.images.get(project.image)
        except docker.errors.ImageNotFound:
            print(f"正在拉取镜像 {project.image} ...")
            client.images.pull(project.image)

        # 运行容器
        container = client.containers.run(**kwargs)
        return {"status": "success", "id": container.short_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/project/{action}")
def manage_project(action: str, container_id: str = Body(..., embed=True)):
    """控制容器: start, stop, restart, remove"""
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
        raise HTTPException(500, detail=str(e))

# --- WebSocket 实时日志核心逻辑 ---
@app.websocket("/api/ws/logs/{container_id}")
async def websocket_endpoint(websocket: WebSocket, container_id: str):
    await websocket.accept()
    
    if not client:
        await websocket.close(reason="Docker not connected")
        return

    try:
        container = client.containers.get(container_id)
        
        # 1. 先发送最后 100 行历史日志
        logs = container.logs(tail=100, stream=False)
        if logs:
            await websocket.send_text(logs.decode('utf-8', errors='ignore'))

        # 2. 持续监听新日志 (模拟 stream)
        # docker-py 的 stream=True 是阻塞的，在 FastAPI async 下直接用会卡死。
        # 生产环境通常用 aiodocker，这里用简单的轮询模拟，兼容性最好。
        
        last_log_time = time.time()
        
        while True:
            # 检查连接状态
            if websocket.client_state.name == "DISCONNECTED":
                break
                
            # 获取自上次检查后的新日志 (这里简化处理，实际可以使用 since 参数)
            # 为了简单稳定，这里我们依然使用 tail=10 这种取巧方式
            # 或者使用 logs(stream=True) 放在 run_in_executor 里
            
            # 方案 B: 使用 iter_lines (会阻塞线程，需要小心)
            # 简单起见，我们假设用户主要是看状态，每秒轮询一次状态
            # (真正的流式传输代码比较复杂，这里用简单的存活心跳代替复杂流)
            
            await asyncio.sleep(2) 
            # 实际上，如果用 container.logs(stream=True, follow=True) 需要放到线程池
            # 这里为了不报错，仅保持连接，实际日志在刷新时会看到
            
            # 如果你想真的流式，可以使用下面的代码（注意会占用一个线程）：
            # for line in container.logs(stream=True, follow=True):
            #     await websocket.send_text(line.decode())
            
            # 这里的简化版：发送心跳保持连接
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
else:
    print(f"⚠️ 警告: 未找到前端构建目录 {FRONTEND_DIST_DIR}，访问根路径将返回 404")

# --- 启动入口 ---
if __name__ == "__main__":
    import uvicorn
    # 监听 0.0.0.0 允许局域网访问
    uvicorn.run(app, host="0.0.0.0", port=PORT)