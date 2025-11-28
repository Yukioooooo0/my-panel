<template>
  <div class="app-layout">
    <!-- 手机端侧边栏 -->
    <el-drawer v-model="drawerVisible" direction="ltr" size="240px" :with-header="false" custom-class="sidebar-drawer">
      <div class="logo-area">Server Control</div>
      <el-menu default-active="1" class="sidebar-menu" background-color="#001529" text-color="#a6adb4" active-text-color="#fff">
        <el-menu-item index="1"><el-icon><Monitor /></el-icon>Dashboard</el-menu-item>
      </el-menu>
    </el-drawer>

    <el-container class="main-container">
      <!-- PC端侧边栏 (深色专业风) -->
      <el-aside width="220px" class="pc-aside hidden-xs-only">
        <div class="logo-area">
          <el-icon class="logo-icon"><Odometer /></el-icon> Server Panel
        </div>
        <el-menu default-active="1" class="sidebar-menu" background-color="#001529" text-color="#b0b0b0" active-text-color="#fff">
          <el-menu-item index="1">
            <el-icon><Monitor /></el-icon><span>容器列表</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 头部导航 -->
        <el-header class="app-header">
          <div class="header-left">
            <el-button class="hidden-sm-and-up hamburger" link @click="drawerVisible = true">
              <el-icon size="22"><Menu /></el-icon>
            </el-button>
            <el-breadcrumb separator="/" class="hidden-xs-only">
              <el-breadcrumb-item>首页</el-breadcrumb-item>
              <el-breadcrumb-item>容器管理</el-breadcrumb-item>
            </el-breadcrumb>
            <span class="mobile-title hidden-sm-and-up">容器管理</span>
          </div>
          <div class="header-right">
            <el-button type="primary" class="create-btn" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon> 新建实例
            </el-button>
          </div>
        </el-header>

        <el-main class="app-main">
          <!-- 1. 现代化仪表盘 -->
          <el-row :gutter="20" class="mb-24">
            <el-col :xs="24" :sm="6">
              <el-card shadow="hover" class="data-card">
                <div class="card-icon blue-bg"><el-icon><Cpu /></el-icon></div>
                <div class="card-info">
                  <div class="label">CPU 负载</div>
                  <div class="value">{{ systemStatus.cpu }}%</div>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="24" :sm="6">
              <el-card shadow="hover" class="data-card">
                <div class="card-icon purple-bg"><el-icon><Files /></el-icon></div>
                <div class="card-info">
                  <div class="label">内存使用</div>
                  <div class="value">{{ systemStatus.memory }}%</div>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="data-card">
                <div class="card-icon green-bg"><el-icon><VideoPlay /></el-icon></div>
                <div class="card-info">
                  <div class="label">运行中</div>
                  <div class="value success-text">{{ runningCount }}</div>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="data-card">
                <div class="card-icon gray-bg"><el-icon><Box /></el-icon></div>
                <div class="card-info">
                  <div class="label">总实例</div>
                  <div class="value">{{ projects.length }}</div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 2. 功能增强的表格区域 -->
          <el-card shadow="never" class="main-card">
            <div class="toolbar">
              <div class="toolbar-left">
                <!-- 🔍 搜索功能 -->
                <el-input 
                  v-model="searchQuery" 
                  placeholder="搜索容器名称..." 
                  prefix-icon="Search" 
                  clearable
                  class="search-input"
                />
              </div>
              <div class="toolbar-right">
                <el-button circle @click="fetchProjects"><el-icon><Refresh /></el-icon></el-button>
              </div>
            </div>

            <el-table :data="filteredProjects" style="width: 100%" v-loading="loading" size="large">
              <el-table-column prop="name" label="容器名称 / ID" min-width="180">
                <template #default="scope">
                  <div class="name-box">
                    <span class="status-badge" :class="scope.row.status"></span>
                    <div>
                      <div class="project-name">{{ scope.row.name }}</div>
                      <div class="project-id">ID: {{ scope.row.id }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column label="网络端口" min-width="200">
                <template #default="scope">
                  <div v-if="scope.row.ports" class="port-wrapper">
                    <el-tag effect="plain" class="port-tag">
                      {{ scope.row.ports }}
                      <!-- 📋 复制功能 -->
                      <el-icon class="copy-icon" @click="copyText(scope.row.ports)"><CopyDocument /></el-icon>
                    </el-tag>
                    <div v-if="scope.row.remark" class="remark-badge">{{ scope.row.remark }}</div>
                  </div>
                  <span v-else class="empty-text">-</span>
                </template>
              </el-table-column>

              <el-table-column prop="image" label="镜像" min-width="150" show-overflow-tooltip>
                 <template #default="scope">
                   <div class="image-text">{{ scope.row.image }}</div>
                 </template>
              </el-table-column>

              <el-table-column label="创建时间" min-width="160" class-name="hidden-xs-only">
                <template #default="scope">
                  <span class="time-text">{{ scope.row.created }}</span>
                </template>
              </el-table-column>

              <el-table-column label="操作" width="220" fixed="right" align="right">
                <template #default="scope">
                  <el-button-group>
                    <el-button type="primary" plain size="small" @click="handleLogs(scope.row)">日志</el-button>
                    <!-- 🔄 快捷重启按钮 -->
                    <el-button type="warning" plain size="small" @click="handleAction(scope.row.id, 'restart')">重启</el-button>
                    
                    <el-dropdown trigger="click" @command="(cmd) => handleAction(scope.row.id, cmd)">
                      <el-button type="info" plain size="small" class="more-btn">
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="stop" v-if="scope.row.status === 'running'" style="color: #F56C6C">停止运行</el-dropdown-item>
                          <el-dropdown-item command="start" v-else style="color: #67C23A">启动容器</el-dropdown-item>
                          <el-dropdown-item divided command="remove">删除容器</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-main>
      </el-container>
    </el-container>

    <!-- 新建弹窗 -->
    <el-dialog v-model="showCreateDialog" title="部署新实例" width="600px" destroy-on-close>
      <el-form :model="newItem" label-width="100px" class="create-form">
        <el-form-item label="名称" required>
          <el-input v-model="newItem.name" placeholder="例如: my-website"></el-input>
        </el-form-item>
        
        <el-form-item label="镜像" required>
          <el-select v-model="newItem.image" allow-create filterable style="width: 100%" placeholder="选择或输入">
            <el-option label="Python 3.9" value="python:3.9-slim"></el-option>
            <el-option label="Nginx" value="nginx:latest"></el-option>
            <el-option label="Node.js 18" value="node:18-alpine"></el-option>
            <el-option label="Redis" value="redis:alpine"></el-option>
          </el-select>
        </el-form-item>

        <div class="form-section-title">网络配置</div>
        <el-form-item label="端口映射">
          <el-row :gutter="10" style="width: 100%">
            <el-col :span="11"><el-input v-model="newItem.host_port" placeholder="主机端口 (如 8080)"></el-input></el-col>
            <el-col :span="2" align="center">:</el-col>
            <el-col :span="11"><el-input v-model="newItem.container_port" placeholder="容器端口 (默认 80)"></el-input></el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="端口备注">
          <el-input v-model="newItem.port_remark" placeholder="例如：博客前台"></el-input>
        </el-form-item>

        <div class="form-section-title">存储与命令</div>
        <el-form-item label="挂载目录">
          <el-input v-model="newItem.volume_host" placeholder="主机绝对路径">
             <template #append>主机</template>
          </el-input>
          <div style="height: 10px"></div>
          <el-input v-model="newItem.volume_container" placeholder="容器内路径 (如 /app)">
             <template #append>容器</template>
          </el-input>
        </el-form-item>

        <el-form-item label="启动命令">
          <el-input v-model="newItem.command" type="textarea" :rows="2" placeholder="可选"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createProject" :loading="creating">开始部署</el-button>
      </template>
    </el-dialog>

    <!-- 日志弹窗 (终端风格) -->
    <el-dialog v-model="showLogDialog" title="Terminal Output" width="80%" top="5vh" custom-class="terminal-dialog">
      <div class="terminal-window">
        <pre ref="logRef">{{ logContent || '> Connecting to container logs...' }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { Monitor, Plus, Refresh, Menu, Search, CopyDocument, MoreFilled, Odometer, Cpu, Files, VideoPlay, Box } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import 'element-plus/theme-chalk/display.css'

const API_BASE = '/api'
const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showLogDialog = ref(false)
const drawerVisible = ref(false)
const logContent = ref('')
const creating = ref(false)
const searchQuery = ref('') // 🔍 搜索词
const systemStatus = ref({ cpu: 0, memory: 0 })
const logRef = ref(null)

const defaultItem = { 
  name: '', image: 'python:3.9-slim', 
  volume_host: '', volume_container: '/app', 
  host_port: '', container_port: '', 
  port_remark: '', command: '' 
}
const newItem = ref({ ...defaultItem })

const runningCount = computed(() => projects.value.filter(p => p.status === 'running').length)

// 🔍 过滤逻辑
const filteredProjects = computed(() => {
  if (!searchQuery.value) return projects.value
  const query = searchQuery.value.toLowerCase()
  return projects.value.filter(p => 
    p.name.toLowerCase().includes(query) || 
    p.image.toLowerCase().includes(query) ||
    (p.remark && p.remark.toLowerCase().includes(query))
  )
})

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/projects`)
    projects.value = res.data
  } catch (error) { ElMessage.error('连接服务器失败') } finally { loading.value = false }
}

const fetchStatus = async () => { try { systemStatus.value = (await axios.get(`${API_BASE}/system/status`)).data } catch (e) {} }

const createProject = async () => {
  if (!newItem.value.name) return ElMessage.warning('请输入名称')
  creating.value = true
  try {
    const payload = {
      name: newItem.value.name,
      image: newItem.value.image,
      command: newItem.value.command || null,
      host_port: newItem.value.host_port ? parseInt(newItem.value.host_port) : null,
      container_port: newItem.value.container_port ? parseInt(newItem.value.container_port) : 80,
      volume_host: newItem.value.volume_host || null,
      volume_container: newItem.value.volume_container || null,
      port_remark: newItem.value.port_remark || null
    }
    await axios.post(`${API_BASE}/project/create`, payload)
    ElMessage.success('部署成功')
    showCreateDialog.value = false
    newItem.value = { ...defaultItem }
    fetchProjects()
  } catch (e) { ElMessage.error('失败: ' + e.message) } finally { creating.value = false }
}

const handleAction = async (id, action) => {
  if (action === 'remove') { try { await ElMessageBox.confirm('确认删除此容器?', '警告', {type:'warning'}) } catch { return } }
  try { await axios.post(`${API_BASE}/project/${action}`, { container_id: id }); ElMessage.success('执行成功'); setTimeout(fetchProjects, 1000) } catch (e) { ElMessage.error('执行失败') }
}

const handleLogs = (row) => {
  showLogDialog.value = true
  logContent.value = '> Connecting...'
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${window.location.host}${API_BASE}/ws/logs/${row.id}`)
  ws.onmessage = (e) => { 
    logContent.value = e.data 
    nextTick(() => { if(logRef.value) logRef.value.scrollTop = logRef.value.scrollHeight }) // 自动滚动
  }
  const unwatch = setInterval(() => { if (!showLogDialog.value) { ws.close(); clearInterval(unwatch) } }, 500)
}

// 📋 复制功能
const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text.split('->')[0]) // 只复制端口号
    ElMessage.success('端口号已复制')
  } catch (err) { ElMessage.error('复制失败') }
}

onMounted(() => { fetchProjects(); fetchStatus(); setInterval(fetchStatus, 3000) })
</script>

<style>
/* Reset & Base */
body { margin: 0; background-color: #f0f2f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #1f2937; }
.app-layout { height: 100vh; display: flex; }

/* Sidebar */
.pc-aside { background-color: #001529; color: #fff; border-right: none; box-shadow: 2px 0 6px rgba(0,21,41,.35); z-index: 10; }
.logo-area { height: 64px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 600; color: #fff; background: #002140; }
.logo-icon { margin-right: 8px; font-size: 20px; color: #1890ff; }
.sidebar-menu { border-right: none !important; }

/* Header */
.app-header { background: #fff; height: 64px; box-shadow: 0 1px 4px rgba(0,21,41,.08); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; z-index: 9; }
.header-left { display: flex; align-items: center; gap: 15px; }
.mobile-title { font-weight: 600; font-size: 16px; }

/* Main Content */
.app-main { padding: 24px; background-color: #f0f2f5; }
.mb-24 { margin-bottom: 24px; }

/* Dashboard Cards */
.data-card { border: none; border-radius: 8px; transition: all 0.3s; cursor: default; }
.data-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.data-card :deep(.el-card__body) { display: flex; align-items: center; padding: 20px; }
.card-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-right: 16px; color: #fff; }
.blue-bg { background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%); }
.purple-bg { background: linear-gradient(135deg, #722ed1 0%, #531dab 100%); }
.green-bg { background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%); }
.gray-bg { background: linear-gradient(135deg, #8c8c8c 0%, #595959 100%); }
.card-info .label { font-size: 14px; color: #8c8c8c; margin-bottom: 4px; }
.card-info .value { font-size: 24px; font-weight: 600; color: #262626; }
.success-text { color: #52c41a; }

/* Table Section */
.main-card { border: none; border-radius: 8px; }
.toolbar { display: flex; justify-content: space-between; margin-bottom: 20px; }
.search-input { width: 250px; }

.name-box { display: flex; align-items: center; gap: 10px; }
.status-badge { width: 10px; height: 10px; border-radius: 50%; display: block; background: #d9d9d9; }
.status-badge.running { background: #52c41a; box-shadow: 0 0 4px #52c41a; }
.project-name { font-weight: 600; font-size: 14px; color: #262626; }
.project-id { font-size: 12px; color: #8c8c8c; font-family: monospace; }

.port-wrapper { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; }
.port-tag { font-family: monospace; cursor: pointer; transition: all 0.2s; }
.port-tag:hover { border-color: #409EFF; color: #409EFF; }
.copy-icon { margin-left: 4px; font-size: 12px; vertical-align: middle; }
.remark-badge { font-size: 12px; color: #faad14; background: #fffbe6; padding: 0 4px; border-radius: 2px; border: 1px solid #ffe58f; }

.image-text { color: #1f2937; background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 12px; display: inline-block; }
.time-text { color: #6b7280; font-size: 13px; }
.more-btn { padding: 8px; }

/* Dialog Form */
.form-section-title { font-size: 14px; font-weight: 600; color: #1f2937; margin: 15px 0 10px; border-left: 3px solid #1890ff; padding-left: 8px; }

/* Terminal */
.terminal-window { background: #1e1e1e; padding: 16px; border-radius: 6px; height: 500px; overflow: hidden; }
.terminal-window pre { color: #4ade80; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 13px; height: 100%; overflow-y: auto; margin: 0; white-space: pre-wrap; }

/* Mobile Adapt */
@media (max-width: 768px) {
  .app-header { padding: 0 15px; }
  .create-btn span { display: none; }
  .create-btn .el-icon { margin: 0; }
  .toolbar { flex-direction: column; gap: 10px; }
  .search-input { width: 100%; }
}
</style>