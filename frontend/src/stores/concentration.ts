import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ConcentrationData, Sensor, ThresholdConfig, Alert, DashboardStats } from '@/types'
import { concentrationApi, sensorApi, thresholdApi, alertApi, dashboardApi } from '@/api'

export const useConcentrationStore = defineStore('concentration', () => {
  // 状态
  const realtimeData = ref<ConcentrationData[]>([])
  const sensors = ref<Sensor[]>([])
  const thresholds = ref<ThresholdConfig[]>([])
  const alerts = ref<Alert[]>([])
  const dashboardStats = ref<DashboardStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const onlineSensors = computed(() => sensors.value.filter(s => s.status === 'online'))
  const unreadAlerts = computed(() => alerts.value.filter(a => !a.isRead))
  const dangerAlerts = computed(() => alerts.value.filter(a => a.type === 'danger' && !a.isRead))

  // 获取实时数据
  const fetchRealtimeData = async (sensorId?: string) => {
    try {
      loading.value = true
      const response = await concentrationApi.getRealtimeData(sensorId)
      if (response.code === 200) {
        realtimeData.value = response.data
      }
    } catch (e) {
      error.value = '获取实时数据失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  // 获取传感器列表
  const fetchSensors = async () => {
    try {
      const response = await sensorApi.getSensors()
      if (response.code === 200) {
        sensors.value = response.data
      }
    } catch (e) {
      error.value = '获取传感器列表失败'
      console.error(e)
    }
  }

  // 获取阈值配置
  const fetchThresholds = async () => {
    try {
      const response = await thresholdApi.getThresholds()
      if (response.code === 200) {
        thresholds.value = response.data
      }
    } catch (e) {
      error.value = '获取阈值配置失败'
      console.error(e)
    }
  }

  // 更新阈值
  const updateThreshold = async (config: Partial<ThresholdConfig>) => {
    try {
      loading.value = true
      const response = await thresholdApi.updateThreshold(config)
      if (response.code === 200) {
        const index = thresholds.value.findIndex(t => t.id === config.id)
        if (index !== -1) {
          thresholds.value[index] = response.data
        }
        return true
      }
      return false
    } catch (e) {
      error.value = '更新阈值失败'
      console.error(e)
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取告警
  const fetchAlerts = async () => {
    try {
      const response = await alertApi.getAlerts()
      if (response.code === 200) {
        alerts.value = response.data
      }
    } catch (e) {
      error.value = '获取告警失败'
      console.error(e)
    }
  }

  // 标记告警已读
  const markAlertAsRead = async (alertId: string) => {
    try {
      const response = await alertApi.markAsRead(alertId)
      if (response.code === 200) {
        const alert = alerts.value.find(a => a.id === alertId)
        if (alert) {
          alert.isRead = true
        }
      }
    } catch (e) {
      console.error(e)
    }
  }

  // 清除所有告警
  const clearAllAlerts = async () => {
    try {
      const response = await alertApi.clearAllAlerts()
      if (response.code === 200) {
        alerts.value = []
      }
    } catch (e) {
      console.error(e)
    }
  }

  // 获取仪表盘统计
  const fetchDashboardStats = async () => {
    try {
      const response = await dashboardApi.getStats()
      if (response.code === 200) {
        dashboardStats.value = response.data
      }
    } catch (e) {
      error.value = '获取统计数据失败'
      console.error(e)
    }
  }

  return {
    // 状态
    realtimeData,
    sensors,
    thresholds,
    alerts,
    dashboardStats,
    loading,
    error,
    // 计算属性
    onlineSensors,
    unreadAlerts,
    dangerAlerts,
    // 方法
    fetchRealtimeData,
    fetchSensors,
    fetchThresholds,
    updateThreshold,
    fetchAlerts,
    markAlertAsRead,
    clearAllAlerts,
    fetchDashboardStats,
  }
})
