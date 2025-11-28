<template>
  <div class="common-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="200px" class="aside">
        <div class="logo">⚡ Server Panel</div>
        <el-menu
          default-active="1"
          class="el-menu-vertical-demo"
          background-color="#1e293b"
          text-color="#fff"
          active-text-color="#409EFF"
        >
          <el-menu-item index="1">
            <el-icon><Monitor /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 头部 -->
        <el-header class="header">
          <span>控制台 / 仪表盘</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 新建项目
          </el-button>
        </el-header>

        <!-- 主内容区 -->
        <el-main>
          <!-- 状态卡片 -->
          <el-row :gutter="20" class="status-row">
            <el-col :span="8">
              <el-card shadow="hover">
                <template #header> CPU 使用率 </template>
                <el-progress type="dashboard" :percentage="systemStatus.cpu" :color="colors" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover">
                <template #header> 内存使用率 </template>
                <el-progress type="dashboard" :percentage="systemStatus.memory" :color="colors" />
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card shadow="hover" class="info-card">
                <template #header> 容器数量 </template>
                <div class="number-display">{{ projects.length }}</div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 项目表格 -->
          <el-card shadow="never" class="table-card">
            <template #header>
              <div class="card-header">
                <span>📦 项目列表</span>
                <el-button circle size="small" @click="fetchProjects"><el-icon><Refresh /></el-icon></el-button>
              </div>
            </template>
            
            <el-table :data="projects" style="width: 100%" v-loading="loading">
              <el-table-column prop="name" label="项目名称" width="180">
                <template #default="scope">
                  <strong>{{ scope.row.name }}</strong>
                </template>
              </el-table-column>
              
              <el-table-column prop="image" label="镜像" width="200">
                 <template #default="scope">
                   <el-tag size="small" type="info">{{ scope.row.image }}</el-tag>
                 </template>
              </el-table-column>

              <el-table-column prop="status" label="状态" width="120">
                <template #default="scope">
                  <el-tag :type="scope.row.status === 'running' ? 'success' : 'danger'">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="操作">
                <template #default="scope">
                  <el-button size="small" @click="handleLogs(scope.row)">日志</el-button>
                  
                  <!-- 停止按钮 -->
                  <el-button 
                    size="small" 
                    type="danger" 
                    plain
                    @click="handleStop(scope.row.id)"
                    v-if="scope.row.status === 'running'"
                  >停止</el-button>
                  
                  <!-- 启动按钮 -->
                  <el-button 
                    size="small" 
                    type="success" 
                    plain
                    @click="handleStart(scope.row.id)"
                    v-else
                  >启动</el-button>

                  <el-button 
                    size="small" 
                    type="info" 
                    link
                    @click="handleRemove(scope.row.id)"
                  >删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-main>
      </el-container>
    </el-container>

    <!-- 弹窗：新建项目 -->
    <el-dialog v-model="showCreateDialog" title="🚀 部署新项目" width="500px">
      <el-form :model="newItem" label-width="100px">
        <el-form-item label="项目名称">
          <el-input v-model="newItem.name" placeholder="例如: my-spider"></el-input>
        </el-form-item>
        <el-form-item label="镜像">
          <el-select v-model="newItem.image" placeholder="选择或输入镜像" allow-create filterable>
            <el-option label="Python 3.9" value="python:3.9-slim"></el-option>
            <el-option label="Nginx" value="nginx:latest"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="端口映射">
          <el-input v-model="newItem.host_port" placeholder="宿主机端口 (如 8080)" type="number"></el-input>
        </el-form-item>
        <el-form-item label="启动命令">
          <el-input v-model="newItem.command" placeholder="可选 (如 python app.py)"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createProject" :loading="creating">立即部署</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 弹窗：日志 -->
    <el-dialog v-model="showLogDialog" title="📜 日志查看" width="70%">
      <div class="log-viewer">
        <pre>{{ logContent || '正在连接日志...' }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Monitor, Plus, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

// --- 核心配置 ---
// 这里必须用相对路径，以便部署后自动使用服务器IP
const API_BASE = '/api'

// 状态
const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showLogDialog = ref(false)
const logContent = ref('')
const creating = ref(false)
const systemStatus = ref({ cpu: 0, memory: 0 })

// 颜色条
const colors = [
  { color: '#5cb87a', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#f56c6c', percentage: 80 },
]

// 新建模型
const newItem = ref({
  name: '',
  image: 'python:3.9-slim',
  host_port: '',
  command: ''
})

// --- API 方法 ---

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/projects`)
    projects.value = res.data
  } catch (error) {
    ElMessage.error('无法连接后端服务')
  } finally {
    loading.value = false
  }
}

const fetchStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/system/status`)
    systemStatus.value = res.data
  } catch (e) {}
}

const createProject = async () => {
  if (!newItem.value.name) return ElMessage.warning('请输入项目名称')
  creating.value = true
  try {
    const payload = {
      name: newItem.value.name,
      image: newItem.value.image,
      command: newItem.value.command || null,
      host_port: newItem.value.host_port ? parseInt(newItem.value.host_port) : null
    }
    await axios.post(`${API_BASE}/project/create`, payload)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    newItem.value.name = '' // 重置表单
    fetchProjects()
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

const handleStop = async (id) => {
  try {
    await axios.post(`${API_BASE}/project/stop`, { container_id: id })
    ElMessage.success('指令已发送')
    setTimeout(fetchProjects, 1000) // 延迟刷新
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleStart = async (id) => {
  try {
    await axios.post(`${API_BASE}/project/start`, { container_id: id })
    ElMessage.success('指令已发送')
    setTimeout(fetchProjects, 1000)
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleRemove = async (id) => {
  ElMessageBox.confirm('确定要删除这个容器吗？操作不可恢复。', '警告', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.post(`${API_BASE}/project/remove`, { container_id: id })
      ElMessage.success('已删除')
      fetchProjects()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  })
}

const handleLogs = (row) => {
  showLogDialog.value = true
  logContent.value = 'Connecting to WebSocket...'
  // WebSocket 连接
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const wsUrl = `${protocol}://${window.location.host}${API_BASE}/ws/logs/${row.id}`
  const ws = new WebSocket(wsUrl)
  
  ws.onmessage = (event) => {
    logContent.value = event.data // 简单覆盖，实际可改为累加
  }
  
  // 弹窗关闭时断开连接
  const unwatch = setInterval(() => {
    if (!showLogDialog.value) {
      ws.close()
      clearInterval(unwatch)
    }
  }, 500)
}

onMounted(() => {
  fetchProjects()
  fetchStatus()
  setInterval(fetchStatus, 5000) // 每5秒刷新状态
})
</script>

<style>
body { margin: 0; background-color: #f0f2f5; font-family: 'Helvetica Neue', Arial, sans-serif; }
.aside { background-color: #1e293b; min-height: 100vh; }
.logo { height: 60px; line-height: 60px; color: #fff; font-size: 18px; font-weight: bold; text-align: center; border-bottom: 1px solid #334155; }
.header { background-color: #fff; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: space-between; }
.status-row { margin-bottom: 20px; }
.number-display { font-size: 32px; font-weight: bold; color: #409EFF; text-align: center; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.log-viewer { background: #1e1e1e; color: #00ff00; padding: 15px; height: 400px; overflow-y: auto; font-family: monospace; white-space: pre-wrap; }
</style>