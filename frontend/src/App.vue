<template>
  <div class="app-layout">
    <!-- 手机端侧边栏 (已修复颜色不一致问题) -->
    <el-drawer 
      v-model="drawerVisible" 
      direction="ltr" 
      size="240px" 
      :with-header="false" 
      class="sidebar-drawer" 
      :modal-class="'sidebar-modal'"
    >
      <div class="logo-area mobile-logo">Server Control</div>
      <el-menu default-active="1" class="sidebar-menu" background-color="#001529" text-color="#a6adb4" active-text-color="#fff">
        <el-menu-item index="1"><el-icon><Monitor /></el-icon>Dashboard</el-menu-item>
      </el-menu>
    </el-drawer>

    <el-container class="main-container">
      <!-- PC端侧边栏 -->
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
            <span class="mobile-title hidden-sm-and-up">控制台</span>
          </div>
          <div class="header-right">
            <el-button type="primary" class="create-btn" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon> <span class="hidden-xs-only">新建实例</span>
            </el-button>
          </div>
        </el-header>

        <el-main class="app-main">
          <!-- 1. 优化后的仪表盘 (手机端双列显示，更紧凑) -->
          <el-row :gutter="15" class="mb-15">
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="data-card">
                <div class="card-icon blue-bg"><el-icon><Cpu /></el-icon></div>
                <div class="card-info">
                  <div class="label">CPU</div>
                  <div class="value">{{ systemStatus.cpu }}%</div>
                </div>
              </el-card>
            </el-col>
            <el-col :xs="12" :sm="6">
              <el-card shadow="hover" class="data-card">
                <div class="card-icon purple-bg"><el-icon><Files /></el-icon></div>
                <div class="card-info">
                  <div class="label">内存</div>
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
                  <div class="label">总数</div>
                  <div class="value">{{ projects.length }}</div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 2. 表格区域 -->
          <el-card shadow="never" class="main-card">
            <div class="toolbar">
              <el-input 
                v-model="searchQuery" 
                placeholder="搜索名称 / 镜像 / 备注" 
                prefix-icon="Search" 
                clearable
                class="search-input"
              />
              <el-button circle @click="fetchProjects"><el-icon><Refresh /></el-icon></el-button>
            </div>

            <el-table :data="filteredProjects" style="width: 100%" v-loading="loading" size="large">
              <el-table-column prop="name" label="容器信息" min-width="160">
                <template #default="scope">
                  <div class="name-box">
                    <span class="status-badge" :class="scope.row.status"></span>
                    <div>
                      <div class="project-name">{{ scope.row.name }}</div>
                      <div class="project-id text-gray">{{ scope.row.image }}</div>
                    </div>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column label="端口/备注" min-width="180">
                <template #default="scope">
                  <div v-if="scope.row.ports" class="port-wrapper">
                    <div class="port-row">
                      <el-tag effect="plain" size="small" class="port-tag">
                        {{ scope.row.ports.split(',')[0] }}
                      </el-tag>
                      <el-icon class="copy-icon" @click="copyText(scope.row.ports)"><CopyDocument /></el-icon>
                    </div>
                    <div v-if="scope.row.remark" class="remark-badge">{{ scope.row.remark }}</div>
                  </div>
                  <span v-else class="empty-text">-</span>
                </template>
              </el-table-column>

              <!-- 手机端隐藏这一列 -->
              <el-table-column label="创建时间" min-width="120" class-name="hidden-xs-only">
                <template #default="scope">
                  <span class="time-text">{{ scope.row.created }}</span>
                </template>
              </el-table-column>

              <!-- 修复：操作列使用 Flex 布局，防止换行 -->
              <el-table-column label="操作" width="160" fixed="right" align="right">
                <template #default="scope">
                  <div class="action-box">
                    <!-- 核心按钮1: 日志 -->
                    <el-button link type="primary" @click="handleLogs(scope.row)">
                      日志
                    </el-button>
                    
                    <!-- 核心按钮2: 启/停 -->
                    <el-button 
                      link 
                      :type="scope.row.status === 'running' ? 'danger' : 'success'" 
                      @click="handleAction(scope.row.id, scope.row.status === 'running' ? 'stop' : 'start')"
                    >
                      {{ scope.row.status === 'running' ? '停止' : '启动' }}
                    </el-button>

                    <!-- 更多菜单 (删除/重启) -->
                    <el-dropdown trigger="click" @command="(cmd) => handleAction(scope.row.id, cmd)">
                      <el-button link type="info" class="more-btn">
                        <el-icon><MoreFilled /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="restart">🔄 重启容器</el-dropdown-item>
                          <el-dropdown-item divided command="remove" style="color: #F56C6C">🗑️ 删除容器</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-main>
      </el-container>
    </el-container>

    <!-- 新建弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建实例" width="600px" destroy-on-close>
      <el-form :model="newItem" label-width="90px" class="create-form">
        <el-form-item label="名称" required>
          <el-input v-model="newItem.name" placeholder="例如: my-web"></el-input>
        </el-form-item>
        
        <el-form-item label="镜像" required>
          <el-select v-model="newItem.image" allow-create filterable style="width: 100%" placeholder="选择或输入">
            <el-option label="Python 3.9" value="python:3.9-slim"></el-option>
            <el-option label="Nginx" value="nginx:latest"></el-option>
            <el-option label="Node.js 18" value="node:18-alpine"></el-option>
            <el-option label="Redis" value="redis:alpine"></el-option>
          </el-select>
        </el-form-item>

        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="主机端口">
              <el-input v-model="newItem.host_port" placeholder="如 8080"></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="容器端口">
              <el-input v-model="newItem.container_port" placeholder="默认 80"></el-input>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="端口备注">
          <el-input v-model="newItem.port_remark" placeholder="例如：API接口"></el-input>
        </el-form-item>

        <el-form-item label="挂载主机">
          <el-input v-model="newItem.volume_host" placeholder="主机代码路径">
             <template #prefix>📂</template>
          </el-input>
        </el-form-item>
        <el-form-item label="挂载容器">
          <el-input v-model="newItem.volume_container" placeholder="容器内路径 (如 /app)">
             <template #prefix>📦</template>
          </el-input>
        </el-form-item>

        <el-form-item label="命令">
          <el-input v-model="newItem.command" placeholder="可选"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createProject" :loading="creating">部署</el-button>
      </template>
    </el-dialog>

    <!-- 日志弹窗 -->
    <el-dialog v-model="showLogDialog" title="实时日志" width="85%" top="5vh" custom-class="terminal-dialog">
      <div class="terminal-window">
        <pre ref="logRef">{{ logContent || '> Connecting...' }}</pre>
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
const searchQuery = ref('')
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
  } catch (error) { ElMessage.error('连接失败') } finally { loading.value = false }
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
    ElMessage.success('成功')
    showCreateDialog.value = false
    newItem.value = { ...defaultItem }
    fetchProjects()
  } catch (e) { ElMessage.error('失败: ' + e.message) } finally { creating.value = false }
}

const handleAction = async (id, action) => {
  if (action === 'remove') { try { await ElMessageBox.confirm('删除此容器?', '警告', {type:'warning'}) } catch { return } }
  try { await axios.post(`${API_BASE}/project/${action}`, { container_id: id }); ElMessage.success('操作成功'); setTimeout(fetchProjects, 1000) } catch (e) { ElMessage.error('失败') }
}

const handleLogs = (row) => {
  showLogDialog.value = true
  logContent.value = '> Connecting...'
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${window.location.host}${API_BASE}/ws/logs/${row.id}`)
  ws.onmessage = (e) => { 
    logContent.value = e.data 
    nextTick(() => { if(logRef.value) logRef.value.scrollTop = logRef.value.scrollHeight })
  }
  const unwatch = setInterval(() => { if (!showLogDialog.value) { ws.close(); clearInterval(unwatch) } }, 500)
}

const copyText = async (text) => {
  try { await navigator.clipboard.writeText(text.split('->')[0]); ElMessage.success('已复制') } catch (err) {}
}

onMounted(() => { fetchProjects(); fetchStatus(); setInterval(fetchStatus, 3000) })
</script>

<style>
/* CSS 修复与优化 */

/* 1. 全局重置 */
body { margin: 0; background-color: #f0f2f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
.app-layout { height: 100vh; display: flex; }

/* 2. 侧边栏修复 */
.pc-aside { background-color: #001529; color: #fff; box-shadow: 2px 0 6px rgba(0,21,41,.35); z-index: 10; }
/* 关键修复：强制 Drawer 内部背景色一致 */
.sidebar-drawer .el-drawer__body { background-color: #001529 !important; padding: 0 !important; }
.sidebar-menu { border-right: none !important; }
.logo-area { height: 64px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 600; color: #fff; background: #002140; }
.mobile-logo { color: #fff; font-size: 18px; font-weight: bold; text-align: center; line-height: 60px; background: #002140; }

/* 3. 头部 */
.app-header { background: #fff; height: 64px; box-shadow: 0 1px 4px rgba(0,21,41,.08); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; }
.header-left { display: flex; align-items: center; gap: 15px; }

/* 4. 内容区 */
.app-main { padding: 20px; background-color: #f0f2f5; }
.mb-15 { margin-bottom: 15px; }

/* 5. 卡片优化 (移动端双列更紧凑) */
.data-card { border: none; border-radius: 8px; margin-bottom: 10px; }
.data-card :deep(.el-card__body) { display: flex; align-items: center; padding: 15px; }
.card-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; margin-right: 12px; color: #fff; }
.blue-bg { background: #1890ff; }
.purple-bg { background: #722ed1; }
.green-bg { background: #52c41a; }
.gray-bg { background: #8c8c8c; }
.card-info .label { font-size: 12px; color: #8c8c8c; }
.card-info .value { font-size: 20px; font-weight: 600; color: #262626; }

/* 6. 表格与按钮修复 */
.main-card { border: none; border-radius: 8px; }
.toolbar { display: flex; justify-content: space-between; margin-bottom: 15px; }
.search-input { width: 100%; max-width: 300px; }

.name-box { display: flex; align-items: center; gap: 8px; }
.status-badge { width: 8px; height: 8px; border-radius: 50%; background: #d9d9d9; flex-shrink: 0; }
.status-badge.running { background: #52c41a; box-shadow: 0 0 3px #52c41a; }
.project-name { font-weight: 600; font-size: 14px; color: #262626; }
.text-gray { color: #8c8c8c; font-size: 12px; }

.port-row { display: flex; align-items: center; gap: 4px; }
.copy-icon { cursor: pointer; color: #409EFF; font-size: 12px; }
.remark-badge { font-size: 11px; color: #faad14; background: #fffbe6; padding: 0 4px; border-radius: 2px; border: 1px solid #ffe58f; margin-top: 2px; display: inline-block; }

/* 关键修复：操作按钮强制一行不换行 */
.action-box {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0px; /* 紧凑排列 */
  white-space: nowrap;
}
/* 调整按钮内边距，适应小屏幕 */
.action-box .el-button { padding: 0 5px; margin: 0; }
.more-btn { padding: 0 5px; }

/* 7. 终端与弹窗 */
.terminal-window { background: #1e1e1e; padding: 15px; border-radius: 6px; height: 450px; overflow: hidden; }
.terminal-window pre { color: #4ade80; font-family: monospace; font-size: 12px; height: 100%; overflow-y: auto; margin: 0; white-space: pre-wrap; }

/* 8. 移动端适配细节 */
@media (max-width: 768px) {
  .app-header { padding: 0 15px; }
  .create-btn { padding: 8px 12px; }
  /* 隐藏不重要的列 */
  .hidden-xs-only { display: none !important; }
  /* 确保表格横向滚动 */
  .el-table { overflow-x: auto; }
}
</style>