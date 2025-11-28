<template>
  <div class="app-wrapper">
    <!-- 手机端：侧边栏抽屉 -->
    <el-drawer v-model="drawerVisible" direction="ltr" size="250px" :with-header="false" custom-class="glass-drawer">
      <div class="logo-area">⚡ CYBER PANEL</div>
      <el-menu default-active="1" class="glass-menu" text-color="#eee" active-text-color="#00f2ea">
        <el-menu-item index="1"><el-icon><Monitor /></el-icon>控制台</el-menu-item>
      </el-menu>
    </el-drawer>

    <el-container class="main-layout">
      <!-- PC端：侧边栏 -->
      <el-aside width="240px" class="glass-aside hidden-xs-only">
        <div class="logo-area">⚡ CYBER PANEL</div>
        <el-menu default-active="1" class="glass-menu" text-color="#a0a0a0" active-text-color="#00f2ea">
          <el-menu-item index="1">
            <el-icon><Monitor /></el-icon><span>容器管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <!-- 头部 -->
        <el-header class="glass-header">
          <div class="header-left">
            <!-- 手机端菜单按钮 -->
            <el-button class="hidden-sm-and-up menu-btn" link @click="drawerVisible = true">
              <el-icon size="24"><Menu /></el-icon>
            </el-button>
            <span class="page-title">DASHBOARD</span>
          </div>
          <el-button type="primary" round class="neon-btn" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> <span class="hidden-xs-only">新建项目</span>
          </el-button>
        </el-header>

        <el-main>
          <!-- 响应式状态卡片 -->
          <el-row :gutter="20" class="status-row">
            <el-col :xs="24" :sm="12" :md="6" class="mb-20">
              <div class="glass-card stat-card">
                <div class="stat-icon cpu"><el-icon><Cpu /></el-icon></div>
                <div class="stat-info">
                  <div class="label">CPU Load</div>
                  <div class="value">{{ systemStatus.cpu }}%</div>
                  <el-progress :percentage="systemStatus.cpu" :show-text="false" :color="colors" stroke-width="4" />
                </div>
              </div>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6" class="mb-20">
              <div class="glass-card stat-card">
                <div class="stat-icon mem"><el-icon><Files /></el-icon></div>
                <div class="stat-info">
                  <div class="label">Memory</div>
                  <div class="value">{{ systemStatus.memory }}%</div>
                  <el-progress :percentage="systemStatus.memory" :show-text="false" :color="colors" stroke-width="4" />
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="12" :md="6" class="mb-20">
              <div class="glass-card stat-card center">
                <div class="label">Running</div>
                <div class="value green-glow">{{ runningCount }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="12" :md="6" class="mb-20">
              <div class="glass-card stat-card center">
                <div class="label">Total</div>
                <div class="value">{{ projects.length }}</div>
              </div>
            </el-col>
          </el-row>

          <!-- 容器列表 -->
          <div class="glass-card table-wrapper">
            <div class="card-header">
              <span class="title">Active Containers</span>
              <el-button circle class="refresh-btn" @click="fetchProjects"><el-icon><Refresh /></el-icon></el-button>
            </div>
            
            <el-table :data="projects" style="width: 100%" v-loading="loading" class="glass-table">
              <el-table-column prop="name" label="Name" min-width="140">
                <template #default="scope">
                  <div class="name-cell">
                    <span class="status-dot" :class="scope.row.status"></span>
                    <b>{{ scope.row.name }}</b>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column prop="image" label="Image" min-width="150" show-overflow-tooltip>
                 <template #default="scope"><span class="mono-text">{{ scope.row.image }}</span></template>
              </el-table-column>
              
              <el-table-column label="Port / Remark" min-width="180">
                <template #default="scope">
                  <div class="port-cell">
                    <el-tag v-if="scope.row.ports !== '无'" size="small" effect="dark" class="port-tag">{{ scope.row.ports }}</el-tag>
                    <span v-else class="text-muted">-</span>
                    <!-- ✅ 显示备注 -->
                    <div v-if="scope.row.remark" class="remark-text">{{ scope.row.remark }}</div>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="Mount" min-width="150" class-name="hidden-xs-only">
                <template #default="scope">
                  <span class="mono-text sm">{{ scope.row.mounts }}</span>
                </template>
              </el-table-column>

              <el-table-column label="Action" width="180" fixed="right">
                <template #default="scope">
                  <el-button link size="small" @click="handleLogs(scope.row)" class="action-btn">Log</el-button>
                  <el-button link size="small" type="danger" v-if="scope.row.status === 'running'" @click="handleAction(scope.row.id, 'stop')" class="action-btn">Stop</el-button>
                  <el-button link size="small" type="success" v-else @click="handleAction(scope.row.id, 'start')" class="action-btn">Start</el-button>
                  <el-button link size="small" type="info" @click="handleAction(scope.row.id, 'remove')" class="action-btn">Del</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-main>
      </el-container>
    </el-container>

    <!-- 新建弹窗 (深色模式) -->
    <el-dialog v-model="showCreateDialog" title="Deploy New Container" width="90%" style="max-width: 600px" custom-class="glass-dialog">
      <el-form :model="newItem" label-position="top">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Name">
              <el-input v-model="newItem.name" placeholder="my-app"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Image">
              <el-select v-model="newItem.image" allow-create filterable style="width: 100%" placeholder="Select Image">
                <el-option label="Python 3.9" value="python:3.9-slim"></el-option>
                <el-option label="Nginx" value="nginx:latest"></el-option>
                <el-option label="Node.js 18" value="node:18-alpine"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <div class="section-title">Networking & Remark</div>
        <el-row :gutter="10">
          <el-col :span="8"><el-input v-model="newItem.host_port" placeholder="Host Port"></el-input></el-col>
          <el-col :span="2" style="text-align: center; line-height: 32px">→</el-col>
          <el-col :span="8"><el-input v-model="newItem.container_port" placeholder="80"></el-input></el-col>
        </el-row>
        <!-- ✅ 新增：备注输入框 -->
        <el-form-item label="Port Remark" style="margin-top: 10px;">
          <el-input v-model="newItem.port_remark" placeholder="e.g. Web Admin Interface"></el-input>
        </el-form-item>

        <div class="section-title">Mount Volume</div>
        <el-form-item>
          <el-input v-model="newItem.volume_host" placeholder="Host Path (e.g. /root/code)">
             <template #prepend>Host</template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="newItem.volume_container" placeholder="Container Path (e.g. /app)">
             <template #prepend>Cont</template>
          </el-input>
        </el-form-item>

        <el-form-item label="Command">
          <el-input v-model="newItem.command" placeholder="python -u main.py"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false" class="glass-btn">Cancel</el-button>
        <el-button type="primary" @click="createProject" :loading="creating" class="neon-btn">Deploy</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showLogDialog" title="Terminal Output" width="90%" custom-class="glass-dialog">
      <div class="log-viewer"><pre>{{ logContent || 'Connecting to socket...' }}</pre></div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Monitor, Plus, Refresh, Menu, Cpu, Files } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import 'element-plus/theme-chalk/display.css' // 引入 Element 的响应式类名

const API_BASE = '/api'
const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showLogDialog = ref(false)
const drawerVisible = ref(false)
const logContent = ref('')
const creating = ref(false)
const systemStatus = ref({ cpu: 0, memory: 0 })

const defaultItem = { 
  name: '', image: 'python:3.9-slim', 
  volume_host: '', volume_container: '/app', 
  host_port: '', container_port: '', 
  port_remark: '', // ✅ 默认值
  command: '' 
}
const newItem = ref({ ...defaultItem })
const colors = '#00f2ea'

const runningCount = computed(() => projects.value.filter(p => p.status === 'running').length)

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/projects`)
    projects.value = res.data
  } catch (error) { ElMessage.error('Connect Error') } finally { loading.value = false }
}

const fetchStatus = async () => { try { systemStatus.value = (await axios.get(`${API_BASE}/system/status`)).data } catch (e) {} }

const createProject = async () => {
  if (!newItem.value.name) return ElMessage.warning('Name Required')
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
      port_remark: newItem.value.port_remark || null // ✅ 传参
    }
    await axios.post(`${API_BASE}/project/create`, payload)
    ElMessage.success('Deployed!')
    showCreateDialog.value = false
    newItem.value = { ...defaultItem }
    fetchProjects()
  } catch (e) { ElMessage.error('Fail: ' + e.message) } finally { creating.value = false }
}

const handleAction = async (id, action) => {
  if (action === 'remove') { try { await ElMessageBox.confirm('Delete this container?', 'Warning', {type:'warning'}) } catch { return } }
  try { await axios.post(`${API_BASE}/project/${action}`, { container_id: id }); ElMessage.success('Done'); setTimeout(fetchProjects, 1000) } catch (e) { ElMessage.error('Error') }
}

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
/* --- 全局前卫设计 (Global Avant-garde Styles) --- */
:root {
  --bg-dark: #0f172a;
  --bg-card: rgba(30, 41, 59, 0.7);
  --neon-blue: #00f2ea;
  --neon-pink: #ff0050;
  --text-main: #e2e8f0;
  --text-muted: #94a3b8;
}

body {
  margin: 0;
  background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
  color: var(--text-main);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, monospace;
  min-height: 100vh;
}

/* 玻璃拟态卡片 */
.glass-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
  transition: transform 0.2s;
}
.glass-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.1); }

/* 侧边栏 & 头部 */
.glass-aside, .glass-drawer {
  background: rgba(15, 23, 42, 0.95) !important;
  border-right: 1px solid rgba(255,255,255,0.05);
}
.glass-header {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255,255,255,0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo-area {
  height: 60px; line-height: 60px; text-align: center;
  font-weight: 900; font-size: 18px; letter-spacing: 1px;
  background: -webkit-linear-gradient(45deg, var(--neon-blue), #fff);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* 统计卡片 */
.stat-card { display: flex; align-items: center; height: 80px; }
.stat-card.center { flex-direction: column; justify-content: center; }
.stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 15px; }
.stat-icon.cpu { background: rgba(0, 242, 234, 0.1); color: var(--neon-blue); }
.stat-icon.mem { background: rgba(255, 0, 80, 0.1); color: var(--neon-pink); }
.stat-info { flex: 1; }
.stat-info .label, .center .label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
.stat-info .value, .center .value { font-size: 24px; font-weight: bold; margin: 2px 0 5px; }
.green-glow { color: var(--neon-blue); text-shadow: 0 0 10px rgba(0, 242, 234, 0.4); }

/* 表格样式 */
.table-wrapper { padding: 0; overflow: hidden; }
.glass-table {
  background: transparent !important;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(0,0,0,0.2);
  --el-table-text-color: var(--text-main);
  --el-table-border-color: rgba(255,255,255,0.05);
  --el-table-row-hover-bg-color: rgba(255,255,255,0.05) !important;
}
.glass-table th { color: var(--text-muted); font-weight: normal; }
.name-cell { display: flex; align-items: center; gap: 10px; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #555; box-shadow: 0 0 5px #555; }
.status-dot.running { background: var(--neon-blue); box-shadow: 0 0 8px var(--neon-blue); }
.status-dot.exited { background: var(--neon-pink); }
.mono-text { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #a5b4fc; }
.sm { font-size: 11px; opacity: 0.7; }
.remark-text { font-size: 11px; color: #fbbf24; margin-top: 2px; }

/* 按钮与表单 */
.neon-btn {
  background: var(--neon-blue) !important;
  border: none !important;
  color: #000 !important;
  font-weight: bold;
  box-shadow: 0 0 15px rgba(0, 242, 234, 0.3);
}
.neon-btn:hover { box-shadow: 0 0 25px rgba(0, 242, 234, 0.5); transform: scale(1.05); }
.action-btn { color: var(--text-muted) !important; }
.action-btn:hover { color: #fff !important; }

/* 弹窗与覆盖 Element 样式 */
.el-dialog.glass-dialog {
  background: rgba(15, 23, 42, 0.95) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
}
.el-dialog__title { color: #fff !important; }
.el-form-item__label { color: var(--text-muted) !important; }
.el-input__wrapper {
  background: rgba(255,255,255,0.05) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
}
.el-input__inner { color: #fff !important; }

/* 响应式调整 */
.mb-20 { margin-bottom: 20px; }
.card-header { padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); }
.title { font-weight: bold; font-size: 16px; }
.log-viewer { background: #000; padding: 15px; border-radius: 8px; font-family: monospace; color: #4ade80; height: 400px; overflow: auto; }

/* Element Menu */
.glass-menu { border-right: none !important; background: transparent !important; }
.glass-menu .el-menu-item:hover, .glass-menu .el-menu-item.is-active { background: rgba(0, 242, 234, 0.1) !important; }

@media (max-width: 768px) {
  .glass-header { padding: 0 15px; }
  .page-title { font-size: 16px; }
  .table-wrapper { border-radius: 0; border-left: none; border-right: none; }
}
</style>