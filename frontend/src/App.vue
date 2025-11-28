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
          <el-menu-item index="2">
            <el-icon><Files /></el-icon>
            <span>文件管理 (Dev)</span>
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
          <!-- 1. 状态卡片区 -->
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
                <template #header> 运行中的容器 </template>
                <div class="number-display">{{ runningCount }}</div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 2. 项目列表表格 -->
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
              
              <el-table-column prop="image" label="镜像/环境" width="220">
                 <template #default="scope">
                   <el-tag size="small" type="info">{{ formatImage(scope.row.image) }}</el-tag>
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
                  <el-button 
                    size="small" 
                    type="danger" 
                    plain
                    @click="handleStop(scope.row.id)"
                    v-if="scope.row.status === 'running'"
                  >停止</el-button>
                  <el-button 
                    size="small" 
                    type="success" 
                    plain
                    @click="handleStart(scope.row.id)"
                    v-else
                  >启动</el-button>
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
        <el-form-item label="镜像选择">
          <el-select v-model="newItem.image" placeholder="选择环境">
            <el-option label="Python 3.9" value="python:3.9-slim"></el-option>
            <el-option label="Nginx Web" value="nginx:latest"></el-option>
            <el-option label="Node.js 18" value="node:18-alpine"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="启动命令">
          <el-input v-model="newItem.script_url" placeholder="脚本URL 或 命令 (示例用)"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="createProject" :loading="creating">立即运行</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 弹窗：日志查看 -->
    <el-dialog v-model="showLogDialog" title="📜 实时日志" width="70%" custom-class="log-dialog">
      <div class="log-viewer">
        <pre>{{ logContent || '暂无日志...' }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Monitor, Files, Plus, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// --- 状态变量 ---
const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showLogDialog = ref(false)
const logContent = ref('')
const creating = ref(false)

// 模拟系统状态 (真实数据需要后端提供API)
const systemStatus = ref({ cpu: 15, memory: 42 })

// 新建表单
const newItem = ref({
  name: '',
  image: 'python:3.9-slim',
  script_url: ''
})

// 进度条颜色
const colors = [
  { color: '#5cb87a', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#f56c6c', percentage: 80 },
]

// 计算运行中的容器数量
const runningCount = computed(() => {
  return projects.value.filter(p => p.status === 'running').length
})

// --- API 请求 ---
// 注意：本地开发时，如果后端在 8888 端口，你需要配置代理或者直接写全路径
const API_BASE = '/api'

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/projects`)
    projects.value = res.data
  } catch (error) {
    console.error(error)
    ElMessage.error('获取项目列表失败，请检查后端是否运行')
    // 演示用假数据，防止你看到空表格
    if (projects.value.length === 0) {
      projects.value = [
        { id: '123', name: 'demo-python-script', image: ['python:3.9'], status: 'running' },
        { id: '456', name: 'my-web-site', image: ['nginx:latest'], status: 'exited' }
      ]
    }
  } finally {
    loading.value = false
  }
}

const createProject = async () => {
  creating.value = true
  try {
    // 对应后端 main.py 的 /api/run_python 接口
    await axios.post(`${API_BASE}/run_python`, null, {
      params: {
        name: newItem.value.name,
        script_url: newItem.value.script_url
      }
    })
    ElMessage.success('容器创建成功！')
    showCreateDialog.value = false
    fetchProjects()
  } catch (error) {
    ElMessage.error('创建失败: ' + error.message)
  } finally {
    creating.value = false
  }
}

const handleStop = async (id) => {
  try {
    await axios.post(`${API_BASE}/projects/${id}/stop`)
    ElMessage.success('已停止')
    fetchProjects()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleStart = (id) => {
  ElMessage.info('启动功能需后端配合 restart API，此处仅演示')
}

const handleLogs = (row) => {
  logContent.value = `正在连接 ${row.name} 的日志...\n[INFO] Starting process...\n[INFO] Python 3.9 detected.\nChecking updates...\nDone.`
  showLogDialog.value = true
  // 真实场景这里应该调用 /api/logs/{id}
}

const formatImage = (tags) => {
  if (!tags) return 'Unknown'
  return typeof tags === 'string' ? tags : tags[0]
}

// 页面加载时拉取数据
onMounted(() => {
  fetchProjects()
  // 模拟动态效果
  setInterval(() => {
    systemStatus.value.cpu = Math.floor(Math.random() * 30) + 10
  }, 3000)
})
</script>

<style>
/* 全局重置 */
body { margin: 0; font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background-color: #f0f2f5; }

/* 布局样式 */
.aside { background-color: #1e293b; min-height: 100vh; }
.logo { height: 60px; line-height: 60px; color: #fff; font-size: 20px; font-weight: bold; text-align: center; border-bottom: 1px solid #334155; }
.header { background-color: #fff; border-bottom: 1px solid #dcdfe6; display: flex; align-items: center; justify-content: space-between; height: 60px; padding: 0 20px; }

/* 卡片样式 */
.status-row { margin-bottom: 20px; }
.number-display { font-size: 32px; font-weight: bold; color: #409EFF; text-align: center; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

/* 日志查看器样式 */
.log-viewer { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 4px; height: 300px; overflow-y: auto; font-family: 'Courier New', Courier, monospace; }
</style>