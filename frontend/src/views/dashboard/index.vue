<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <StatCard
        :value="dashboardStats?.totalSensors || 0"
        label="传感器总数"
        :icon="Cpu"
        type="primary"
      />
      <StatCard
        :value="dashboardStats?.onlineSensors || 0"
        label="在线传感器"
        :icon="Connection"
        type="success"
        :trend="5.2"
      />
      <StatCard
        :value="dashboardStats?.alertCount || 0"
        label="未处理告警"
        :icon="Bell"
        type="danger"
        clickable
        @click="handleAlertClick"
      />
      <StatCard
        :value="dashboardStats?.avgConcentration || 0"
        label="平均浓度"
        :icon="Odometer"
        type="warning"
        unit="mg/L"
      />
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="16">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>实时浓度趋势</span>
                <el-button type="primary" text @click="refreshData">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>
            <LineChart
              :data="realtimeData"
              title=""
              height="350px"
              :warning-threshold="60"
              :danger-threshold="80"
            />
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="8">
          <el-card class="chart-card">
            <template #header>
              <span>浓度分布</span>
            </template>
            <BarChart
              :data="realtimeData.slice(-20)"
              title=""
              height="350px"
            />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 传感器状态 -->
    <div class="sensors-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>传感器状态</span>
            <el-button type="primary" text @click="goToRealtime">
              查看全部
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </template>
        <div class="sensors-grid">
          <SensorCard
            v-for="sensor in sensors.slice(0, 4)"
            :key="sensor.id"
            :sensor="sensor"
            :latest-data="getSensorLatestData(sensor.id)"
            @view-details="handleViewDetails"
          />
        </div>
      </el-card>
    </div>

    <!-- 最近告警 -->
    <div class="alerts-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>最近告警</span>
            <el-button type="primary" text @click="goToAlerts">
              查看全部
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </template>
        <el-table :data="alerts.slice(0, 5)" stripe>
          <el-table-column prop="sensorName" label="传感器" min-width="150" />
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'danger' ? 'danger' : 'warning'" size="small">
                {{ row.type === 'danger' ? '危险' : '警告' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="200" />
          <el-table-column label="数值" width="120">
            <template #default="{ row }">
              <span class="alert-value">{{ row.value }} mg/L</span>
            </template>
          </el-table-column>
          <el-table-column label="时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.isRead ? 'info' : 'warning'" size="small">
                {{ row.isRead ? '已读' : '未读' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConcentrationStore } from '@/stores'
import StatCard from '@/components/common/StatCard.vue'
import SensorCard from '@/components/common/SensorCard.vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import {
  Cpu,
  Connection,
  Bell,
  Odometer,
  Refresh,
  ArrowRight,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()
const store = useConcentrationStore()

// 数据
const dashboardStats = computed(() => store.dashboardStats)
const realtimeData = computed(() => store.realtimeData)
const sensors = computed(() => store.sensors)
const alerts = computed(() => store.alerts)

// 获取传感器最新数据
const getSensorLatestData = (sensorId: string) => {
  const data = realtimeData.value.filter(d => d.sensorId === sensorId)
  return data.length > 0 ? data[data.length - 1] : null
}

// 格式化时间
const formatTime = (date: Date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

// 刷新数据
const refreshData = async () => {
  await store.fetchRealtimeData()
}

// 查看传感器详情
const handleViewDetails = (sensorId: string) => {
  router.push({
    path: '/realtime',
    query: { sensorId },
  })
}

// 跳转到实时数据页
const goToRealtime = () => {
  router.push('/realtime')
}

// 跳转到告警
const goToAlerts = () => {
  // 打开告警抽屉
}

// 点击告警卡片
const handleAlertClick = () => {
  // 打开告警抽屉
}

// 定时刷新
let refreshTimer: number | null = null

onMounted(async () => {
  await Promise.all([
    store.fetchDashboardStats(),
    store.fetchRealtimeData(),
    store.fetchSensors(),
    store.fetchAlerts(),
  ])
  
  // 每5秒刷新实时数据
  refreshTimer = window.setInterval(() => {
    store.fetchRealtimeData()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.charts-section {
  margin-top: 0;
}

.chart-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.sensors-section {
  margin-top: 0;
}

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.alerts-section {
  margin-top: 0;
}

.alert-value {
  color: #f56c6c;
  font-weight: 600;
}

/* 响应式 - 大屏 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .sensors-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

/* 响应式 - 平板 */
@media (max-width: 992px) {
  .dashboard-page {
    gap: 16px;
  }
  
  .stats-grid {
    gap: 12px;
  }
  
  .sensors-grid {
    gap: 10px;
  }
  
  .charts-section :deep(.el-col) {
    margin-bottom: 12px;
  }
}

/* 响应式 - 移动端 */
@media (max-width: 768px) {
  .dashboard-page {
    gap: 12px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .sensors-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .card-header {
    font-size: 14px;
  }
  
  .card-header .el-button {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .chart-card :deep(.el-card__body) {
    padding: 12px;
  }
  
  .alerts-section :deep(.el-table) {
    font-size: 13px;
  }
  
  .alerts-section :deep(.el-table__cell) {
    padding: 8px 6px;
  }
  
  .alerts-section :deep(.el-tag) {
    font-size: 11px;
  }
}

/* 响应式 - 小屏幕手机 */
@media (max-width: 480px) {
  .dashboard-page {
    gap: 10px;
  }
  
  .stats-grid {
    gap: 8px;
  }
  
  .sensors-grid {
    gap: 8px;
  }
  
  .card-header {
    font-size: 13px;
  }
  
  .card-header .el-button {
    padding: 4px 8px;
    font-size: 11px;
  }
  
  .chart-card :deep(.el-card__body) {
    padding: 10px;
  }
  
  .alerts-section :deep(.el-table) {
    font-size: 12px;
  }
  
  .alerts-section :deep(.el-table__cell) {
    padding: 6px 4px;
  }
}
</style>
