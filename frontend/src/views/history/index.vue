<template>
  <div class="history-page">
    <!-- 查询条件 -->
    <el-card class="query-card">
      <el-form :model="queryForm" inline>
        <el-form-item label="传感器">
          <el-select v-model="queryForm.sensorId" placeholder="选择传感器" style="width: 200px">
            <el-option
              v-for="sensor in sensors"
              :key="sensor.id"
              :label="sensor.name"
              :value="sensor.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="queryForm.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :shortcuts="shortcuts"
            style="width: 360px"
          />
        </el-form-item>
        
        <el-form-item label="时间间隔">
          <el-select v-model="queryForm.interval" style="width: 120px">
            <el-option label="分钟" value="minute" />
            <el-option label="小时" value="hour" />
            <el-option label="天" value="day" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计概览 -->
    <div class="stats-section" v-if="historyData.length > 0">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">数据点数</div>
            <div class="stat-value">{{ statistics.count }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">平均浓度</div>
            <div class="stat-value">{{ statistics.avg.toFixed(2) }} mg/L</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">最大浓度</div>
            <div class="stat-value max">{{ statistics.max.toFixed(2) }} mg/L</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">最小浓度</div>
            <div class="stat-value min">{{ statistics.min.toFixed(2) }} mg/L</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表展示 -->
    <el-card class="chart-card" v-if="historyData.length > 0">
      <template #header>
        <div class="card-header">
          <span>历史趋势图</span>
          <div class="header-actions">
            <el-radio-group v-model="chartType" size="small">
              <el-radio-button label="line">折线图</el-radio-button>
              <el-radio-button label="bar">柱状图</el-radio-button>
            </el-radio-group>
            <el-button type="primary" size="small" @click="exportChart">
              <el-icon><Download /></el-icon>
              导出图表
            </el-button>
          </div>
        </div>
      </template>
      <LineChart
        v-if="chartType === 'line'"
        :data="historyData"
        height="450px"
        :warning-threshold="60"
        :danger-threshold="80"
      />
      <BarChart
        v-else
        :data="historyData"
        height="450px"
      />
    </el-card>

    <!-- 空状态 -->
    <el-card v-else class="empty-card">
      <el-empty description="请选择查询条件并点击查询按钮">
        <el-button type="primary" @click="handleQuery">立即查询</el-button>
      </el-empty>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" v-if="historyData.length > 0">
      <template #header>
        <div class="card-header">
          <span>数据明细</span>
          <div class="header-actions">
            <el-button type="primary" size="small" @click="exportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="paginatedData"
        stripe
        max-height="400"
      >
        <el-table-column type="index" label="#" width="60" />
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column label="浓度值" width="140">
          <template #default="{ row }">
            <span :class="`status-${row.status}`">{{ row.value }} {{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sensorId" label="传感器ID" min-width="150" />
      </el-table>
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="historyData.length"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useConcentrationStore } from '@/stores'
import { concentrationApi } from '@/api'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import {
  Search,
  RefreshLeft,
  Download,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const store = useConcentrationStore()

// 查询表单
const queryForm = reactive({
  sensorId: '',
  timeRange: [] as Date[],
  interval: 'hour' as 'minute' | 'hour' | 'day',
})

// 快捷选项
const shortcuts = [
  {
    text: '最近1小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000)
      return [start, end]
    },
  },
  {
    text: '最近6小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 6)
      return [start, end]
    },
  },
  {
    text: '最近24小时',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24)
      return [start, end]
    },
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    },
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    },
  },
]

// 状态
const loading = ref(false)
const chartType = ref<'line' | 'bar'>('line')
const historyData = ref<any[]>([])
const statistics = ref({
  avg: 0,
  max: 0,
  min: 0,
  count: 0,
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 计算属性
const sensors = computed(() => store.sensors)

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return historyData.value.slice().reverse().slice(start, end)
})

// 方法
const formatTime = (date: Date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'danger': return 'danger'
    case 'warning': return 'warning'
    default: return 'success'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'danger': return '危险'
    case 'warning': return '警告'
    default: return '正常'
  }
}

const handleQuery = async () => {
  if (!queryForm.timeRange || queryForm.timeRange.length !== 2) {
    ElMessage.warning('请选择时间范围')
    return
  }
  
  loading.value = true
  try {
    const response = await concentrationApi.getHistoryData({
      sensorId: queryForm.sensorId || undefined,
      startTime: queryForm.timeRange[0],
      endTime: queryForm.timeRange[1],
      interval: queryForm.interval,
    })
    
    if (response.code === 200) {
      historyData.value = response.data.data
      statistics.value = response.data.statistics
      ElMessage.success(`查询成功，共 ${response.data.data.length} 条数据`)
    }
  } catch (error) {
    ElMessage.error('查询失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryForm.sensorId = ''
  queryForm.timeRange = []
  queryForm.interval = 'hour'
  historyData.value = []
  statistics.value = { avg: 0, max: 0, min: 0, count: 0 }
}

const exportChart = () => {
  ElMessage.success('图表导出功能开发中')
}

const exportData = () => {
  const csvContent = [
    ['时间', '浓度值', '单位', '状态', '传感器ID'],
    ...historyData.value.map(d => [
      formatTime(d.timestamp),
      d.value.toString(),
      d.unit,
      d.status,
      d.sensorId,
    ]),
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `history_data_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
  link.click()
  
  ElMessage.success('数据导出成功')
}

// 初始化
onMounted(async () => {
  await store.fetchSensors()
  
  // 默认查询最近24小时
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24)
  queryForm.timeRange = [start, end]
  
  // 自动查询
  handleQuery()
})
</script>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.query-card {
  margin-bottom: 0;
}

.stats-section {
  margin-top: 0;
}

.stat-item {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.stat-value.max { color: #f56c6c; }
.stat-value.min { color: #67c23a; }

.chart-card {
  margin-top: 0;
}

.empty-card {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.table-card {
  margin-top: 0;
}

.status-normal { color: #67c23a; }
.status-warning { color: #e6a23c; }
.status-danger { color: #f56c6c; }

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 响应式 */
@media (max-width: 768px) {
  .el-form--inline .el-form-item {
    display: block;
    margin-right: 0;
    margin-bottom: 16px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .stat-value {
    font-size: 20px;
  }
}
</style>
