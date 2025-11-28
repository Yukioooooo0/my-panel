<template>
  <div class="display-container">
    <!-- 顶部控制栏 -->
    <div class="control-bar">
      <span class="title">📺 {{ project.name }} ({{ project.type }})</span>
      <div class="actions">
        <el-tag v-if="project.status === 'running'" type="success" effect="dark">RUNNING</el-tag>
        <el-tag v-else type="danger" effect="dark">STOPPED</el-tag>
      </div>
    </div>

    <!-- 核心展示区 -->
    <div class="screen-area">
      
      <!-- 模式 A: Web 项目 (Iframe 嵌入) -->
      <div v-if="project.type === 'web'" class="iframe-wrapper">
        <div v-if="project.status !== 'running'" class="placeholder">
          <el-empty description="服务未启动，无法访问网页" />
        </div>
        <!-- 注意：实际部署时 iframe src 需要是服务器 IP + 端口 -->
        <iframe 
          v-else
          :src="project.url" 
          frameborder="0" 
          class="web-frame"
        ></iframe>
      </div>

      <!-- 模式 B: 脚本项目 (Xterm 终端) -->
      <div v-else class="terminal-wrapper">
        <div ref="terminalContainer" class="xterm-container"></div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'

// 接收父组件传来的项目信息
const props = defineProps({
  project: {
    type: Object, // 包含 { name, type: 'web'|'script', url, id, status }
    required: true
  }
})

// 终端相关变量
const terminalContainer = ref(null)
let term = null
let socket = null
let fitAddon = null

// 初始化终端
const initTerminal = () => {
  if (term) return // 避免重复初始化

  term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: '"Menlo", "Consolas", monospace',
    theme: {
      background: '#1e1e1e',
      foreground: '#00ff00'
    }
  })
  
  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(terminalContainer.value)
  fitAddon.fit()

  term.writeln(`\x1b[1;34m[SYSTEM]\x1b[0m Connecting to container ${props.project.name}...`)
  
  connectWebSocket()
}

// 连接 WebSocket 获取实时日志
const connectWebSocket = () => {
  // 连接到后端 WebSocket 接口
  // 假设后端地址是 localhost:8888
  const wsUrl = `ws://localhost:8888/api/ws/logs/${props.project.id}`
  socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    term.writeln(`\x1b[1;32m[CONNECTED]\x1b[0m Live logs attached.`)
  }

  socket.onmessage = (event) => {
    // 写入终端
    term.write(event.data) 
  }

  socket.onclose = () => {
    term.writeln(`\n\x1b[1;31m[DISCONNECTED]\x1b[0m Connection closed.`)
  }
}

// 监听项目变化，如果是脚本且正在运行，就加载终端
watch(() => props.project, (newVal) => {
  if (newVal.type === 'script' && newVal.status === 'running') {
    nextTick(() => {
      initTerminal()
    })
  } else if (newVal.type === 'web') {
    if (socket) socket.close()
  }
}, { deep: true, immediate: true })

// 销毁时清理
onBeforeUnmount(() => {
  if (socket) socket.close()
  if (term) term.dispose()
})
</script>

<style scoped>
.display-container { display: flex; flex-direction: column; height: 100%; background: #000; }
.control-bar { height: 40px; background: #333; color: #fff; display: flex; align-items: center; padding: 0 15px; justify-content: space-between; }
.screen-area { flex: 1; position: relative; overflow: hidden; }

/* Iframe 样式 */
.iframe-wrapper { width: 100%; height: 100%; background: #fff; }
.web-frame { width: 100%; height: 100%; }
.placeholder { display: flex; justify-content: center; align-items: center; height: 100%; }

/* 终端样式 */
.terminal-wrapper { height: 100%; width: 100%; padding: 10px; box-sizing: border-box; background: #1e1e1e; }
.xterm-container { height: 100%; width: 100%; }
</style>