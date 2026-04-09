<template>
  <div class="sensor-card" :class="{ 'is-offline': sensor.status === 'offline' }">
    <div class="sensor-header">
      <div class="sensor-name">
        <el-icon><Cpu /></el-icon>
        <span>{{ sensor.name }}</span>
      </div>
      <el-tag :type="statusType" size="small">
        {{ statusText }}
      </el-tag>
    </div>
    
    <div class="sensor-info">
      <div class="info-item">
        <el-icon><Location /></el-icon>
        <span>{{ sensor.location }}</span>
      </div>
      <div class="info-item">
        <el-icon><Document /></el-icon>
        <span>{{ sensor.type }}</span>
      </div>
    </div>

    <div v-if="latestData" class="sensor-data">
      <div class="data-value" :class="`status-${latestData.status}`">
        <span class="value">{{ latestData.value }}</span>
        <span class="unit">{{ latestData.unit }}</span>
      </div>
      <div class="data-time">
        更新于 {{ formatTime(latestData.timestamp) }}
      </div>
    </div>
    <div v-else class="sensor-data no-data">
      <span>暂无数据</span>
    </div>

    <div class="sensor-actions">
      <el-button type="primary" size="small" @click="handleViewDetails">
        查看详情
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Cpu, Location, Document } from '@element-plus/icons-vue'
import type { Sensor, ConcentrationData } from '@/types'
import dayjs from 'dayjs'

interface Props {
  sensor: Sensor
  latestData?: ConcentrationData | null
}

const props = withDefaults(defineProps<Props>(), {
  latestData: null,
})

const emit = defineEmits<{
  viewDetails: [sensorId: string]
}>()

// 状态类型
const statusType = computed(() => {
  switch (props.sensor.status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'danger'
    case 'maintenance':
      return 'warning'
    default:
      return 'info'
  }
})

// 状态文本
const statusText = computed(() => {
  switch (props.sensor.status) {
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    case 'maintenance':
      return '维护中'
    default:
      return '未知'
  }
})

// 格式化时间
const formatTime = (date: Date) => {
  return dayjs(date).format('HH:mm:ss')
}

// 查看详情
const handleViewDetails = () => {
  emit('viewDetails', props.sensor.id)
}
</script>

<style scoped>
.sensor-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.3s;
}

.sensor-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.sensor-card.is-offline {
  opacity: 0.7;
}

.sensor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.sensor-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.sensor-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #909399;
}

.sensor-data {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  text-align: center;
}

.data-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-bottom: 8px;
}

.data-value .value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.data-value .unit {
  font-size: 14px;
  color: #909399;
}

.data-value.status-normal .value {
  color: #67c23a;
}

.data-value.status-warning .value {
  color: #e6a23c;
}

.data-value.status-danger .value {
  color: #f56c6c;
}

.data-time {
  font-size: 12px;
  color: #909399;
}

.no-data {
  color: #c0c4cc;
  font-size: 14px;
}

.sensor-actions {
  display: flex;
  justify-content: flex-end;
}

/* 响应式 */
@media (max-width: 768px) {
  .sensor-card {
    padding: 16px;
  }
  
  .data-value .value {
    font-size: 28px;
  }
}
</style>
