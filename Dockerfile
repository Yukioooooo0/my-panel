# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 1. 安装后端依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. 复制后端代码
COPY backend/ .

# 3. 复制前端构建好的静态文件 (假设你在本地已经 npm run build 好了)
# 注意路径关系：Docker 构建上下文通常在项目根目录
COPY frontend/dist/ ../frontend/dist/

# 4. 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]