<template>
  <div class="stat-card" :class="[`stat-card--${type}`, { 'is-clickable': clickable }]" @click="handleClick">
    <div class="stat-icon">
      <el-icon :size="32">
        <component :is="icon" />
      </el-icon>
    </div>
    <div class="stat-content">
      <div class="stat-value">
        <span class="value">{{ value }}</span>
        <span v-if="unit" class="unit">{{ unit }}</span>
      </div>
      <div class="stat-label">{{ label }}</div>
    </div>
    <div v-if="trend" class="stat-trend" :class="trend > 0 ? 'up' : 'down'">
      <el-icon>
        <CaretTop v-if="trend > 0" />
        <CaretBottom v-else />
      </el-icon>
      <span>{{ Math.abs(trend) }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CaretTop, CaretBottom } from '@element-plus/icons-vue'
import type { Component } from 'vue'

interface Props {
  value: string | number
  label: string
  icon: Component
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  unit?: string
  trend?: number
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'primary',
  clickable: false,
})

const emit = defineEmits<{
  click: []
}>()

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
}

.stat-card--primary::before {
  background: linear-gradient(180deg, #409eff, #79bbff);
}

.stat-card--success::before {
  background: linear-gradient(180deg, #67c23a, #95d475);
}

.stat-card--warning::before {
  background: linear-gradient(180deg, #e6a23c, #eebe77);
}

.stat-card--danger::before {
  background: linear-gradient(180deg, #f56c6c, #fab6b6);
}

.stat-card--info::before {
  background: linear-gradient(180deg, #909399, #b1b3b8);
}

.stat-card.is-clickable {
  cursor: pointer;
}

.stat-card.is-clickable:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card--primary .stat-icon {
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
}

.stat-card--success .stat-icon {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.stat-card--warning .stat-icon {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.stat-card--danger .stat-icon {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.stat-card--info .stat-icon {
  background: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.stat-content {
  flex: 1;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat-value .value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-value .unit {
  font-size: 14px;
  color: #909399;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.stat-trend.up {
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.stat-trend.down {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
  }
  
  .stat-icon :deep(.el-icon) {
    font-size: 24px !important;
  }
  
  .stat-value .value {
    font-size: 24px;
  }
}
</style>
