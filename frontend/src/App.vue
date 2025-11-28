<template>
  <div class="common-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="220px" class="aside">
        <div class="logo">
          <el-icon style="margin-right: 8px"><ElementPlus /></el-icon>
          Server Panel
        </div>
        <el-menu default-active="1" class="el-menu-vertical-demo" background-color="#1e293b" text-color="#94a3b8" active-text-color="#fff">
          <el-menu-item index="1">
            <el-icon><Monitor /></el-icon><span>容器管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 头部 -->
        <el-header class="header">
          <div class="header-title">仪表盘 / 容器列表</div>
          <el-button type="primary" @click="showCreateDialog = true" size="large">
            <el-icon style="margin-right: 5px"><Plus /></el-icon> 新建容器
          </el-button>
        </el-header>

        <el-main>
          <!-- 顶部卡片 -->
          <el-row :gutter="20" class="status-row">
            <el-col :span="6"><el-card shadow="hover" class="stat-card"><template #header>CPU</template><el-progress type="dashboard" :percentage="systemStatus.cpu" :color="colors" :width="100" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover" class="stat-card"><template #header>内存</template><el-progress type="dashboard" :percentage="systemStatus.memory" :color="colors" :width="100" /></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover" class="stat-card"><template #header>运行中</template><div class="number-display">{{ runningCount }}</div></el-card></el-col>
            <el-col :span="6"><el-card shadow="hover" class="stat-card"><template #header>总数</template><div class="number-display" style="color: #909399">{{ projects.length }}</div></el-card></el-col>
          </el-row>

          <!-- 容器列表 -->
          <el-card shadow="never" class="table-card">
            <template #header>
              <div class="card-header"><span style="font-weight: bold">📦 容器实例</span><el-button circle @click="fetchProjects"><el-icon><Refresh /></el-icon></el-button></div>
            </template>
            
            <el-table :data="projects" style="width: 100%" v-loading="loading" stripe>
              <el-table-column prop="name" label="名称" width="160"><template #default="scope"><b>{{ scope.row.name }}</b></template></el-table-column>
              
              <el-table-column prop="image" label="镜像" width="180"><template #default="scope"><el-tag size="small" type="info">{{ scope.row.image }}</el-tag></template></el-table-column>
              
              <!-- 端口映射列 -->
              <el-table-column label="端口映射" width="180">
                <template #default="scope">
                  <el-tag v-if="scope.row.ports !== '无端口'" size="small" effect="dark">{{ scope.row.ports }}</el-tag>
                  <span v-else style="color:#ccc">-</span>
                </template>
              </el-table-column>

              <!-- 挂载信息列 -->
              <el-table-column label="挂载目录" width="220" show-overflow-tooltip>
                <template #default="scope">
                  <span v-if="scope.row.mounts !== '无挂载'" style="font-size: 12px; color: #666">{{ scope.row.mounts }}</span>
                  <span v-else style="color:#ccc">-</span>
                </template>
              </el-table-column>

              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'running'" type="success" effect="dark">运行</el-tag>
                  <el-tag v-else type="danger" effect="dark">停止</el-tag>
                </template>
              </el-table-column>

              <el-table-column label="操作" min-width="200">
                <template #default="scope">
                  <el-button size="small" @click="handleLogs(scope.row)">日志</el-button>
                  <el-button size="small" type="danger" plain v-if="scope.row.status === 'running'" @click="handleAction(scope.row.id, 'stop')">停止</el-button>
                  <el-button size="small" type="success" plain v-else @click="handleAction(scope.row.id, 'start')">启动</el-button>
                  <el-button size="small" type="info" link @click="handleAction(scope.row.id, 'remove')">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-main>
      </el-container>
    </el-container>

    <!-- 新建容器弹窗 -->
    <el-dialog v-model="showCreateDialog" title="部署新容器" width="600px">
      <el-form :model="newItem" label-width="110px">
        
        <el-form-item label="容器名称" required>
          <el-input v-model="newItem.name" placeholder="例如: my-spider"></el-input>
        </el-form-item>
        
        <el-form-item label="镜像" required>
          <el-select v-model="newItem.image" allow-create filterable style="width: 100%" placeholder="选择或输入镜像">
            <el-option label="Python 3.9 (Slim)" value="python:3.9-slim"></el-option>
            <el-option label="Nginx (Web)" value="nginx:latest"></el-option>
            <el-option label="Node.js 18" value="node:18-alpine"></el-option>
          </el-select>
        </el-form-item>

        <!-- 目录挂载 -->
        <el-divider content-position="left">目录挂载 (代码路径)</el-divider>
        <el-form-item label="宿主机目录">
          <el-input v-model="newItem.volume_host" placeholder="服务器上的代码路径 (如 /root/my_code)">
            <template #prefix>📂</template>
          </el-input>
        </el-form-item>
        <el-form-item label="容器目录">
          <el-input v-model="newItem.volume_container" placeholder="映射到容器内的路径 (默认 /app)">
            <template #prefix>📦</template>
          </el-input>
        </el-form-item>

        <!-- 端口映射 -->
        <el-divider content-position="left">网络与启动</el-divider>
        <el-form-item label="端口映射">
          <el-row :gutter="10">
            <el-col :span="11"><el-input v-model="newItem.host_port" placeholder="宿主机端口 (如 8000)" type="number"></el-input></el-col>
            <el-col :span="2" style="text-align: center;">→</el-col>
            <el-col :span="11"><el-input v-model="newItem.container_port" placeholder="容器端口 (默认 80)" type="number"></el-input></el-col>
          </el-row>
        </el-form-item>

        <el-form-item label="启动命令">
          <el-input v-model="newItem.command" placeholder="例如: python -u main.py"></el-input>
        </el-form-item>

      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createProject" :loading="creating">部署</el-button>
      </template>
    </el-dialog>

    <!-- 日志弹窗 -->
    <el-dialog v-model="showLogDialog" title="实时日志" width="70%">
      <div class="log-viewer"><pre>{{ logContent || 'Connecting...' }}</pre></div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Monitor, Plus, Refresh, ElementPlus } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const API_BASE = '/api'
const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showLogDialog = ref(false)
const logContent = ref('')
const creating = ref(false)
const systemStatus = ref({ cpu: 0, memory: 0 })

// 默认值
const defaultItem = { 
  name: '', 
  image: 'python:3.9-slim', 
  volume_host: '',        // 宿主机路径
  volume_container: '/app', // 容器路径 (默认 /app)
  host_port: '', 
  container_port: '', 
  command: '' 
}
const newItem = ref({ ...defaultItem })

const colors = [{ color: '#5cb87a', percentage: 20 }, { color: '#e6a23c', percentage: 40 }, { color: '#f56c6c', percentage: 80 }]
const runningCount = computed(() => projects.value.filter(p => p.status === 'running').length)

// 1. 获取列表
const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/projects`)
    projects.value = res.data
  } catch (error) { ElMessage.error('获取列表失败') } finally { loading.value = false }
}

// 2. 获取状态
const fetchStatus = async () => { try { systemStatus.value = (await axios.get(`${API_BASE}/system/status`)).data } catch (e) {} }

// 3. 创建容器 (整合了端口和挂载)
const createProject = async () => {
  if (!newItem.value.name || !newItem.value.image) return ElMessage.warning('请填写名称和镜像')
  creating.value = true
  try {
    const payload = {
      name: newItem.value.name,
      image: newItem.value.image,
      command: newItem.value.command || null,
      host_port: newItem.value.host_port ? parseInt(newItem.value.host_port) : null,
      container_port: newItem.value.container_port ? parseInt(newItem.value.container_port) : 80,
      volume_host: newItem.value.volume_host || null,
      volume_container: newItem.value.volume_container || null
    }
    await axios.post(`${API_BASE}/project/create`, payload)
    ElMessage.success('部署成功！')
    showCreateDialog.value = false
    newItem.value = { ...defaultItem }
    fetchProjects()
  } catch (e) { ElMessage.error('部署失败: ' + (e.response?.data?.detail || e.message)) } finally { creating.value = false }
}

// 4. 管理操作
const handleAction = async (id, action) => {
  if (action === 'remove') { try { await ElMessageBox.confirm('确定删除吗？', '警告', {type:'warning'}) } catch { return } }
  try { await axios.post(`${API_BASE}/project/${action}`, { container_id: id }); ElMessage.success('操作成功'); setTimeout(fetchProjects, 1000) } catch (e) { ElMessage.error('失败') }
}

// 5. 日志 WebSocket
const handleLogs = (row) => {
  showLogDialog.value = true
  logContent.value = 'Connecting...'
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${window.location.host}${API_BASE}/ws/logs/${row.id}`)
  ws.onmessage = (e) => { logContent.value = e.data }
  const unwatch = setInterval(() => { if (!showLogDialog.value) { ws.close(); clearInterval(unwatch) } }, 500)
}

onMounted(() => { fetchProjects(); fetchStatus(); setInterval(fetchStatus, 3000) })
</script>

<style>
body { margin: 0; background-color: #f1f5f9; font-family: sans-serif; }
.aside { background-color: #0f172a; min-height: 100vh; color: #fff; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; border-bottom: 1px solid #1e293b; }
.header { background-color: #fff; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; }
.stat-card { text-align: center; }
.number-display { font-size: 30px; font-weight: 700; color: #0f172a; margin-top: 5px; }
.status-row { margin-bottom: 20px; }
.log-viewer { background: #1a1a1a; color: #4ade80; padding: 15px; height: 450px; overflow-y: auto; font-family: monospace; white-space: pre-wrap; }
.el-menu { border-right: none !important; }
</style>