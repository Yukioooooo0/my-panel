# my-panel

`my-panel` 是一个轻量级的服务器/桌面监控面板，采用前后端分离架构，并通过 Docker Compose 进行容器化部署。

## ✨ 主要功能

- **实时系统监控**: 实时展示 CPU、内存、磁盘等系统资源的使用情况。
- **Websocket 通信**: 前后端通过 Websocket 实现实时数据推送。
- **容器化部署**: 使用 Docker 和 Docker Compose，实现一键启动和环境隔离。

## 🛠️ 技术栈

- **后端**: 
  - **FastAPI**: 高性能的 Python Web 框架。
  - **Uvicorn**: ASGI 服务器，用于运行 FastAPI。
  - **Websockets**: 用于实现与前端的实时通信。
  - **Psutil**: 用于获取系统性能信息。
- **前端**:
  - **Vue.js**: 渐进式 JavaScript 框架。
  - **Vite**: 现代化的前端构建工具。
- **部署**:
  - **Docker**: 容器化平台。
  - **Docker Compose**: 用于定义和运行多容器 Docker 应用程序的工具。

## 🚀 如何运行

请确保您的系统中已经安装了 `Docker` 和 `Docker Compose`。

1. **克隆项目到本地**:
   ```bash
   git clone https://github.com/Yukioooooo0/my-panel.git
   cd my-panel
   ```

2. **使用 Docker Compose 启动**:
   在项目根目录下，执行以下命令来构建并启动所有服务：
   ```bash
   docker-compose up -d
   ```
   `-d` 参数表示在后台运行。

3. **访问应用**:
   - 前端应用将运行在 `http://localhost:5173`。
   - 后端 API 服务将运行在 `http://localhost:8000`。

4. **停止应用**:
   如果需要停止所有正在运行的容器，请执行：
   ```bash
   docker-compose down
