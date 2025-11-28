# ---------- 第一阶段：构建前端 ----------
# 使用 Node.js 镜像
FROM node:20-alpine as frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 先只复制 package.json 安装依赖 (为了缓存，提高构建速度)
COPY frontend/package*.json ./
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端所有源码并打包
COPY frontend/ .
RUN npm run build

# ---------- 第二阶段：构建后端并运行 ----------
# 使用 Python 镜像
FROM python:3.9-slim

# 设置工作目录到 backend
WORKDIR /app/backend

# 安装 Python 依赖
COPY backend/requirements.txt .
# 换源安装以防卡顿
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端代码
COPY backend/ .

# 【关键步骤】把第一阶段打包好的前端文件 (dist) 复制到 Python 能找到的位置
# 对应 main.py 里的 "../frontend/dist"
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 暴露端口
EXPOSE 8888

# 启动命令
CMD ["python", "main.py"]