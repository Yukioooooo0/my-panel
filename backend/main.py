# backend/main.py
import docker
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 允许跨域（虽然合并部署不需要，但开发时方便）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 连接到宿主机的 Docker（因为挂载了 socket）
try:
    client = docker.from_env()
except Exception as e:
    print("无法连接 Docker，请确保挂载了 /var/run/docker.sock")

# --- API 区域 ---

@app.get("/api/projects")
def list_projects():
    """列出所有容器"""
    containers = client.containers.list(all=True)
    return [{"id": c.short_id, "name": c.name, "status": c.status, "image": c.image.tags} for c in containers]

@app.post("/api/run_python")
def run_python_script(name: str, script_url: str):
    """
    极简部署演示：拉取一个 python 镜像，下载脚本并运行
    实际场景可以改为挂载本地目录
    """
    try:
        # 这是一个演示：启动一个 Python 容器，运行指定的命令
        container = client.containers.run(
            "python:3.9-slim",
            command=f"sh -c 'curl -s {script_url} | python3'", # 例子：从网络下载脚本运行
            name=name,
            detach=True,
            restart_policy={"Name": "always"}
        )
        return {"status": "success", "id": container.short_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{container_id}/stop")
def stop_project(container_id: str):
    container = client.containers.get(container_id)
    container.stop()
    return {"status": "stopped"}

# --- 静态文件区域 (关键) ---
# 将前端 build 好的 dist 目录挂载到根路径，这样访问 http://IP:8080 就是面板界面
# 注意：这行代码要放在最后，因为它会匹配所有剩余路由
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")