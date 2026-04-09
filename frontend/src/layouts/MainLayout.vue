<template>
  <el-container class="main-layout">
    <!-- 移动端遮罩层 -->
    <div 
      v-if="isMobile && !isCollapse" 
      class="sidebar-overlay"
      @click="closeSidebar"
    ></div>
    
    <!-- 侧边栏 -->
    <el-aside 
      :width="isCollapse ? '64px' : '220px'" 
      class="sidebar"
      :class="{ 'sidebar--mobile-open': isMobile && !isCollapse }"
    >
      <div class="logo">
        <el-icon :size="28"><Odometer /></el-icon>
        <span v-show="!isCollapse" class="logo-text">YOLO检测系统</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse && !isMobile"
        :collapse-transition="false"
        router
        class="sidebar-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/realtime">
          <el-icon><Monitor /></el-icon>
          <template #title>实时预测</template>
        </el-menu-item>
        
        <el-menu-item index="/history">
          <el-icon><Box /></el-icon>
          <template #title>模型管理器</template>
        </el-menu-item>
        
        <el-menu-item index="/training">
          <el-icon><SetUp /></el-icon>
          <template #title>训练数据</template>
        </el-menu-item>
        
        <el-menu-item index="/dataset">
          <el-icon><FolderOpened /></el-icon>
          <template #title>数据集</template>
        </el-menu-item>
        
        <el-menu-item index="/guide">
          <el-icon><QuestionFilled /></el-icon>
          <template #title>使用指南</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <!-- 移动端汉堡菜单按钮 -->
          <el-icon 
            v-if="isMobile"
            class="hamburger-btn" 
            @click="toggleSidebar"
          >
            <Close v-if="!isCollapse" />
            <Menu v-else />
          </el-icon>
          <!-- 桌面端折叠按钮 -->
          <el-icon 
            v-else
            class="collapse-btn" 
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useConcentrationStore } from '@/stores'
import {
  Odometer,
  Monitor,
  Box,
  SetUp,
  FolderOpened,
  Fold,
  Expand,
  Menu,
  Close,
  QuestionFilled,
} from '@element-plus/icons-vue'

const route = useRoute()
const store = useConcentrationStore()

const isCollapse = ref(false)
const isMobile = ref(false)
const MOBILE_BREAKPOINT = 768

const checkMobile = () => {
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT
  if (isMobile.value) {
    isCollapse.value = true
  }
}

const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

const closeSidebar = () => {
  isCollapse.value = true
}

const handleMenuSelect = () => {
  if (isMobile.value) {
    closeSidebar()
  }
}

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/dataset')) {
    return '/dataset'
  }
  return path
})

const currentTitle = computed(() => route.meta.title as string || '')

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  await Promise.all([
    store.fetchSensors(),
    store.fetchThresholds(),
  ])
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar-overlay {
  display: none;
}

.sidebar {
  background: linear-gradient(180deg, #1a1f3c 0%, #2d3561 100%);
  transition: width 0.3s, transform 0.3s;
  overflow: hidden;
  flex-shrink: 0;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-text {
  white-space: nowrap;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.7);
  height: 50px;
  line-height: 50px;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #409eff 0%, transparent 100%);
  color: #fff;
}

.main-container {
  background: #f0f2f5;
  overflow: hidden;
  flex: 1;
  min-width: 0;
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
  height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn,
.hamburger-btn {
  font-size: 22px;
  cursor: pointer;
  color: #606266;
  transition: all 0.3s;
  padding: 8px;
  border-radius: 8px;
}

.collapse-btn:hover,
.hamburger-btn:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.collapse-btn:active,
.hamburger-btn:active {
  transform: scale(0.95);
}

.hamburger-btn {
  display: none;
}

.breadcrumb {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.main-content {
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 告警样式 */
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
}

.alert-item.is-read {
  opacity: 0.6;
}

.alert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.alert-time {
  font-size: 12px;
  color: #909399;
}

.alert-content {
  margin-bottom: 8px;
}

.alert-sensor {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.alert-message {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.alert-value {
  font-size: 12px;
  color: #909399;
}

.alert-value .value {
  color: #f56c6c;
  font-weight: 600;
}

.alert-actions {
  text-align: right;
}

.no-alert {
  padding: 40px 0;
}

/* 响应式 - 平板 */
@media (max-width: 992px) {
  .main-content {
    padding: 16px;
  }
}

/* 响应式 - 移动端 */
@media (max-width: 768px) {
  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
    animation: fadeIn 0.3s ease;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 100;
    width: 220px !important;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.sidebar--mobile-open {
    transform: translateX(0);
  }
  
  .hamburger-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    font-size: 26px;
    padding: 0;
    background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
    color: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  }
  
  .hamburger-btn:hover {
    background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
    color: #fff;
    transform: scale(1.05);
  }
  
  .hamburger-btn:active {
    transform: scale(0.95);
  }
  
  .collapse-btn {
    display: none;
  }
  
  .header {
    padding: 0 12px;
    height: 56px;
  }
  
  .header-left {
    gap: 8px;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .username {
    display: none;
  }
  
  .main-content {
    padding: 12px;
  }
  
  .logo {
    height: 56px;
    font-size: 16px;
  }
  
  .sidebar-menu :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    font-size: 15px;
  }
}

/* 响应式 - 小屏幕手机 */
@media (max-width: 480px) {
  .header {
    padding: 0 10px;
  }
  
  .main-content {
    padding: 10px;
  }
  
  .hamburger-btn {
    width: 44px;
    height: 44px;
    font-size: 24px;
    border-radius: 10px;
  }
}
</style>
