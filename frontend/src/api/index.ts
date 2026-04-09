/**
 * 模拟后端API服务
 */

import type {
  ConcentrationData,
  Sensor,
  ThresholdConfig,
  HistoryQuery,
  HistoryData,
  Alert,
  DashboardStats,
  ApiResponse,
} from '@/types'
import dayjs from 'dayjs'
import axios from 'axios'

const getApiBaseUrl = (port: number = 5000) => {
  if (typeof window === 'undefined') {
    return `http://localhost:${port}/api`
  }
  const hostname = window.location.hostname
  return `http://${hostname}:${port}/api`
}

const API_BASE_URL = getApiBaseUrl(5000)

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// 模拟延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// 生成随机浓度数据
const generateRandomData = (
  sensorId: string,
  count: number,
  baseValue: number = 50,
  fluctuation: number = 20
): ConcentrationData[] => {
  const data: ConcentrationData[] = []
  const now = new Date()
  
  for (let i = count - 1; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 1000)
    const value = baseValue + (Math.random() - 0.5) * fluctuation * 2
    const clampedValue = Math.max(0, Math.min(100, value))
    
    let status: 'normal' | 'warning' | 'danger' = 'normal'
    if (clampedValue > 80) status = 'danger'
    else if (clampedValue > 60) status = 'warning'
    
    data.push({
      id: `${sensorId}-${timestamp.getTime()}`,
      timestamp,
      value: Number(clampedValue.toFixed(2)),
      unit: 'mg/L',
      sensorId,
      status,
    })
  }
  
  return data
}

// 模拟传感器列表
const mockSensors: Sensor[] = [
  {
    id: 'sensor-001',
    name: '主反应池传感器',
    location: 'A区-反应池1号',
    type: '光学浓度传感器',
    status: 'online',
    lastUpdate: new Date(),
  },
  {
    id: 'sensor-002',
    name: '储罐液位传感器',
    location: 'B区-储罐区',
    type: '超声波液位传感器',
    status: 'online',
    lastUpdate: new Date(),
  },
  {
    id: 'sensor-003',
    name: '管道浓度传感器',
    location: 'C区-主管道',
    type: '电导率传感器',
    status: 'online',
    lastUpdate: new Date(),
  },
  {
    id: 'sensor-004',
    name: '出口监测传感器',
    location: 'D区-出口处',
    type: '光学浓度传感器',
    status: 'offline',
    lastUpdate: new Date(Date.now() - 3600000),
  },
]

// 模拟阈值配置
const mockThresholds: ThresholdConfig[] = [
  {
    id: 'threshold-001',
    sensorId: 'sensor-001',
    minValue: 0,
    maxValue: 100,
    warningThreshold: 60,
    dangerThreshold: 80,
    unit: 'mg/L',
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date(),
  },
  {
    id: 'threshold-002',
    sensorId: 'sensor-002',
    minValue: 0,
    maxValue: 100,
    warningThreshold: 55,
    dangerThreshold: 75,
    unit: 'mg/L',
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date(),
  },
  {
    id: 'threshold-003',
    sensorId: 'sensor-003',
    minValue: 0,
    maxValue: 100,
    warningThreshold: 65,
    dangerThreshold: 85,
    unit: 'mg/L',
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date(),
  },
]

// 模拟告警数据
const mockAlerts: Alert[] = [
  {
    id: 'alert-001',
    sensorId: 'sensor-001',
    sensorName: '主反应池传感器',
    type: 'warning',
    message: '浓度接近警告阈值',
    value: 62.5,
    threshold: 60,
    timestamp: new Date(Date.now() - 1800000),
    isRead: false,
  },
  {
    id: 'alert-002',
    sensorId: 'sensor-003',
    sensorName: '管道浓度传感器',
    type: 'danger',
    message: '浓度超过危险阈值',
    value: 85.2,
    threshold: 85,
    timestamp: new Date(Date.now() - 900000),
    isRead: false,
  },
]

// API方法
export const concentrationApi = {
  // 获取实时浓度数据
  async getRealtimeData(sensorId?: string): Promise<ApiResponse<ConcentrationData[]>> {
    await delay(300)
    const sensors = sensorId ? [sensorId] : mockSensors.filter(s => s.status === 'online').map(s => s.id)
    const data = sensors.flatMap(id => generateRandomData(id, 10))
    return { code: 200, message: 'success', data }
  },

  // 获取单个传感器最新数据
  async getLatestData(sensorId: string): Promise<ApiResponse<ConcentrationData>> {
    await delay(200)
    const data = generateRandomData(sensorId, 1)[0]
    return { code: 200, message: 'success', data }
  },

  // 获取历史数据
  async getHistoryData(query: HistoryQuery): Promise<ApiResponse<HistoryData>> {
    await delay(500)
    const sensorId = query.sensorId || 'sensor-001'
    const hours = dayjs(query.endTime).diff(dayjs(query.startTime), 'hour')
    const count = Math.min(hours * 60, 1000) // 每分钟一个数据点，最多1000个
    
    const data = generateRandomData(sensorId, count, 50, 25)
    const values = data.map(d => d.value)
    
    return {
      code: 200,
      message: 'success',
      data: {
        data,
        statistics: {
          avg: Number((values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)),
          max: Math.max(...values),
          min: Math.min(...values),
          count: values.length,
        },
      },
    }
  },
}

export const sensorApi = {
  // 获取所有传感器
  async getSensors(): Promise<ApiResponse<Sensor[]>> {
    await delay(300)
    return { code: 200, message: 'success', data: mockSensors }
  },

  // 获取单个传感器
  async getSensor(id: string): Promise<ApiResponse<Sensor>> {
    await delay(200)
    const sensor = mockSensors.find(s => s.id === id)
    if (!sensor) {
      return { code: 404, message: 'Sensor not found', data: null as any }
    }
    return { code: 200, message: 'success', data: sensor }
  },
}

export const thresholdApi = {
  // 获取所有阈值配置
  async getThresholds(): Promise<ApiResponse<ThresholdConfig[]>> {
    await delay(300)
    return { code: 200, message: 'success', data: mockThresholds }
  },

  // 获取单个传感器阈值
  async getThreshold(sensorId: string): Promise<ApiResponse<ThresholdConfig>> {
    await delay(200)
    const threshold = mockThresholds.find(t => t.sensorId === sensorId)
    if (!threshold) {
      return { code: 404, message: 'Threshold not found', data: null as any }
    }
    return { code: 200, message: 'success', data: threshold }
  },

  // 更新阈值配置
  async updateThreshold(config: Partial<ThresholdConfig>): Promise<ApiResponse<ThresholdConfig>> {
    await delay(400)
    const index = mockThresholds.findIndex(t => t.id === config.id)
    if (index === -1) {
      return { code: 404, message: 'Threshold not found', data: null as any }
    }
    mockThresholds[index] = {
      ...mockThresholds[index],
      ...config,
      updatedAt: new Date(),
    }
    return { code: 200, message: 'success', data: mockThresholds[index] }
  },
}

export const alertApi = {
  // 获取告警列表
  async getAlerts(): Promise<ApiResponse<Alert[]>> {
    await delay(300)
    return { code: 200, message: 'success', data: mockAlerts }
  },

  // 标记告警已读
  async markAsRead(alertId: string): Promise<ApiResponse<boolean>> {
    await delay(200)
    const alert = mockAlerts.find(a => a.id === alertId)
    if (alert) {
      alert.isRead = true
    }
    return { code: 200, message: 'success', data: true }
  },

  // 清除所有告警
  async clearAllAlerts(): Promise<ApiResponse<boolean>> {
    await delay(300)
    mockAlerts.length = 0
    return { code: 200, message: 'success', data: true }
  },
}

export const dashboardApi = {
  // 获取仪表盘统计数据
  async getStats(): Promise<ApiResponse<DashboardStats>> {
    await delay(300)
    return {
      code: 200,
      message: 'success',
      data: {
        totalSensors: mockSensors.length,
        onlineSensors: mockSensors.filter(s => s.status === 'online').length,
        alertCount: mockAlerts.filter(a => !a.isRead).length,
        avgConcentration: 52.35,
      },
    }
  },
}

export interface ModelMetrics {
  accuracy?: number
  precision?: number
  recall?: number
  f1Score?: number
  mae?: number
  r2?: number
  rmse?: number
  map50?: number
  map50_95?: number
  errorRate?: number
  within5Percent?: number
  within10Percent?: number
  totalSamples?: number
  success?: number
  failed?: number
}

export interface YoloEvaluateResponse {
  r2: number
  map50: number
  map50_95: number
  precision: number
  recall: number
  error_rate: number
  predictions?: Array<{
    preprocess_ms: number
    inference_ms: number
    postprocess_ms: number
  }>
}



const YOLO_API_BASE_URL = getApiBaseUrl(5003)

const yoloApiClient = axios.create({
  baseURL: YOLO_API_BASE_URL,
  timeout: 120000,
})

export interface Model {
  id: string
  name: string
  type: 'YOLO'
  path: string
  createdAt: string
  epochs: number
  testing: boolean
  tested: boolean
  testProgress: number
  testProgressText: string
  testStatus: '' | 'success' | 'exception' | 'warning'
  testSteps?: Array<{
    text: string
    completed: boolean
    active: boolean
    error: boolean
  }>
  metrics?: ModelMetrics
}

export const modelApi = {
  // 获取所有模型
  async getModels(type?: 'yolo'): Promise<ApiResponse<Model[]>> {
    try {
      const params = type ? { type } : {}
      const response = await apiClient.get<{ success: boolean; data: Model[] }>('/models', { params })
      if (response.data.success) {
        return { code: 200, message: 'success', data: response.data.data }
      }
      return { code: 500, message: '获取模型列表失败', data: [] }
    } catch (error) {
      console.error('获取模型列表失败:', error)
      return { code: 500, message: '获取模型列表失败', data: [] }
    }
  },

  // 测试模型
  async testModel(modelId: string): Promise<ApiResponse<{ taskId: string }>> {
    try {
      const response = await apiClient.post<{ taskId: string }>(`/models/${modelId}/test`)
      return { code: 200, message: '测试任务已启动', data: response.data }
    } catch (error) {
      console.error('测试模型失败:', error)
      return { code: 500, message: '测试模型失败', data: { taskId: '' } }
    }
  },

  // 获取测试进度
  async getTestProgress(taskId: string): Promise<ApiResponse<{
    progress: number
    status: string
    message: string
    metrics?: ModelMetrics
    error?: string
  }>> {
    try {
      const response = await apiClient.get<{
        progress: number
        status: string
        message: string
        metrics?: ModelMetrics
        error?: string
      }>(`/models/test/${taskId}/progress`)
      return { code: 200, message: 'success', data: response.data }
    } catch (error) {
      console.error('获取测试进度失败:', error)
      return { code: 500, message: '获取测试进度失败', data: {} as any }
    }
  },

  // 删除模型
  async deleteModel(modelId: string): Promise<ApiResponse<boolean>> {
    try {
      const response = await apiClient.delete(`/models/${modelId}`)
      return { code: 200, message: response.data.message, data: true }
    } catch (error) {
      console.error('删除模型失败:', error)
      return { code: 500, message: '删除模型失败', data: false }
    }
  },

  // 刷新模型列表
  async refreshModels(): Promise<ApiResponse<boolean>> {
    try {
      const response = await apiClient.post('/models/refresh')
      return { code: 200, message: response.data.message, data: true }
    } catch (error) {
      console.error('刷新模型列表失败:', error)
      return { code: 500, message: '刷新模型列表失败', data: false }
    }
  },

  // 获取所有测试结果
  async getTestResults(): Promise<ApiResponse<Record<string, { metrics: ModelMetrics, timestamp: string }>>> {
    try {
      const response = await apiClient.get('/models/test-results')
      if (response.data.success) {
        return { code: 200, message: 'success', data: response.data.data }
      }
      return { code: 500, message: '获取测试结果失败', data: {} }
    } catch (error) {
      console.error('获取测试结果失败:', error)
      return { code: 500, message: '获取测试结果失败', data: {} }
    }
  },

  // 保存测试结果
  async saveTestResult(modelId: string, metrics: ModelMetrics): Promise<ApiResponse<boolean>> {
    try {
      const response = await apiClient.post(`/models/test-results/${modelId}`, { metrics })
      if (response.data.success) {
        return { code: 200, message: response.data.message, data: true }
      }
      return { code: 500, message: response.data.message || '保存测试结果失败', data: false }
    } catch (error) {
      console.error('保存测试结果失败:', error)
      return { code: 500, message: '保存测试结果失败', data: false }
    }
  },

  // 删除测试结果
  async deleteTestResult(modelId: string): Promise<ApiResponse<boolean>> {
    try {
      const response = await apiClient.delete(`/models/test-results/${modelId}`)
      if (response.data.success) {
        return { code: 200, message: response.data.message, data: true }
      }
      return { code: 500, message: response.data.message || '删除测试结果失败', data: false }
    } catch (error) {
      console.error('删除测试结果失败:', error)
      return { code: 500, message: '删除测试结果失败', data: false }
    }
  },

  // 切换模型
  async switchModel(params: { yolo_model?: string }): Promise<ApiResponse<{
    current_yolo_model?: string
  }>> {
    try {
      const response = await apiClient.post('/models/switch', params)
      return { code: 200, message: response.data.message, data: response.data }
    } catch (error) {
      console.error('切换模型失败:', error)
      return { code: 500, message: '切换模型失败', data: {} }
    }
  },

  // 获取当前使用的模型
  async getCurrentModels(): Promise<ApiResponse<{
    yolo_model: string | null
  }>> {
    try {
      const response = await apiClient.get('/models/current')
      return { code: 200, message: 'success', data: response.data.data }
    } catch (error) {
      console.error('获取当前模型失败:', error)
      return { code: 500, message: '获取当前模型失败', data: { yolo_model: null } }
    }
  },
}

export const yoloTestApi = {
  async healthCheck(): Promise<boolean> {
    try {
      const response = await yoloApiClient.get('/health')
      return response.data?.status === 'ok'
    } catch (error) {
      console.error('YOLO API健康检查失败:', error)
      return false
    }
  },

  async loadModelByPath(modelPath: string): Promise<ApiResponse<{ num_classes: number, class_names: Record<string, string> }>> {
    try {
      const response = await yoloApiClient.post('/model/load-path', { model_path: modelPath })
      if (response.data.success) {
        return { code: 200, message: '模型加载成功', data: response.data.data }
      }
      return { code: 500, message: response.data.message || '加载模型失败', data: {} as any }
    } catch (error) {
      console.error('加载模型失败:', error)
      return { code: 500, message: '加载模型失败', data: {} as any }
    }
  },

  async evaluate(): Promise<ApiResponse<YoloEvaluateResponse>> {
    try {
      const response = await yoloApiClient.post('/evaluate', {})
      if (response.data.success) {
        return { code: 200, message: '评估成功', data: response.data.data }
      }
      return { code: 500, message: response.data.message || '评估失败', data: {} as YoloEvaluateResponse }
    } catch (error) {
      console.error('评估模型失败:', error)
      return { code: 500, message: '评估模型失败', data: {} as YoloEvaluateResponse }
    }
  },

  async evaluateStream(
    onLog: (message: string) => void,
    onResult: (data: YoloEvaluateResponse) => void,
    onError: (error: string) => void,
    onDone: () => void,
    testPath?: string
  ): Promise<void> {
    try {
      const response = await fetch(`${YOLO_API_BASE_URL}/evaluate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ data_dir: testPath })
      })

      if (!response.ok) {
        onError(`HTTP错误: ${response.status}`)
        onDone()
        return
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        onError('无法读取响应流')
        onDone()
        return
      }

      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.substring(6).trim()
              if (!jsonStr) continue
              
              const data = JSON.parse(jsonStr)

              if (data.type === 'start') {
                onLog(data.message)
              } else if (data.type === 'log') {
                onLog(data.message)
              } else if (data.type === 'result') {
                onResult(data.data)
              } else if (data.type === 'error') {
                onError(data.message)
              } else if (data.type === 'done') {
                onLog(data.message)
              }
            } catch (e) {
              console.error('解析流数据失败:', e, line)
            }
          }
        }
      }
      
      onDone()
    } catch (error) {
      console.error('流式评估失败:', error)
      onError('流式评估失败')
      onDone()
    }
  },

  async evaluateFull(modelPath: string): Promise<ApiResponse<YoloEvaluateResponse>> {
    try {
      const response = await yoloApiClient.post('/evaluate/full', { model_path: modelPath })
      if (response.data.success) {
        return { code: 200, message: '评估成功', data: response.data.data }
      }
      return { code: 500, message: response.data.message || '评估失败', data: {} as YoloEvaluateResponse }
    } catch (error) {
      console.error('完整评估失败:', error)
      return { code: 500, message: '完整评估失败', data: {} as YoloEvaluateResponse }
    }
  },
}

export interface YoloTrainParams {
  data_yaml: string
  model_name: string
  epochs: number
  batch: number
  imgsz: number
  device: string
  name: string
  patience: number
  save_period: number
}

export interface YoloTrainStatus {
  is_training: boolean
  current_task: YoloTrainParams | null
  progress: number
  message: string
  start_time: string | null
  end_time: string | null
  error: string | null
  epoch: number
  total_epochs: number
  metrics: Record<string, number | null>
  is_grid_search: boolean
  current_fold: number
  total_folds: number
}

export interface YoloParamGrid {
  lr0: number[]
  lrf: number[]
  momentum: number[]
  weight_decay: number[]
  warmup_epochs: number[]
  box: number[]
  cls: number[]
  dfl: number[]
}

export interface GridSearchParams {
  data_yaml: string
  model_name: string
  epochs: number
  batch: number
  imgsz: number
  device: string
  name: string
  patience: number
  save_period: number
  cv_folds: number
  param_grid: YoloParamGrid
}

export interface GridSearchResult {
  best_params: Record<string, any>
  best_score: number
  all_results: Array<{
    params: Record<string, any>
    metrics: Record<string, number>
    fold_metrics?: Array<Record<string, number>>
  }>
}

const YOLO_TRAIN_API_URL = getApiBaseUrl(5004)

export const yoloTrainApi = {
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/train/health`)
      const data = await response.json()
      return data?.status === 'ok'
    } catch (error) {
      console.error('YOLO训练API健康检查失败:', error)
      return false
    }
  },

  async getStatus(): Promise<ApiResponse<YoloTrainStatus>> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/train/status`)
      const data = await response.json()
      if (data.success) {
        return { code: 200, message: 'success', data: data.data }
      }
      return { code: 500, message: '获取状态失败', data: {} as YoloTrainStatus }
    } catch (error) {
      console.error('获取训练状态失败:', error)
      return { code: 500, message: '获取训练状态失败', data: {} as YoloTrainStatus }
    }
  },

  async startTraining(params: YoloTrainParams): Promise<ApiResponse<{ output_dir: string, parameters: YoloTrainParams }>> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/train/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      })
      const data = await response.json()
      if (data.success) {
        return { code: 200, message: data.message, data: data.data }
      }
      return { code: 500, message: data.message || '启动训练失败', data: {} as any }
    } catch (error) {
      console.error('启动训练失败:', error)
      return { code: 500, message: '启动训练失败', data: {} as any }
    }
  },

  async stopTraining(): Promise<ApiResponse<boolean>> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/train/stop`, {
        method: 'POST',
      })
      const data = await response.json()
      if (data.success) {
        return { code: 200, message: data.message, data: true }
      }
      return { code: 500, message: data.message || '停止训练失败', data: false }
    } catch (error) {
      console.error('停止训练失败:', error)
      return { code: 500, message: '停止训练失败', data: false }
    }
  },

  async trainStream(
    onLog: (message: string) => void,
    _onProgress: (data: YoloTrainStatus) => void,
    onError: (error: string) => void,
    onDone: () => void,
    signal?: AbortSignal
  ): Promise<void> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/train/stream`, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
        },
        signal,
      })

      if (!response.ok) {
        onError(`HTTP错误: ${response.status}`)
        onDone()
        return
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        onError('无法读取响应流')
        onDone()
        return
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.substring(6).trim()
              if (!jsonStr) continue

              const data = JSON.parse(jsonStr)

              if (data.message === '[DONE]') {
                onDone()
                return
              }

              onLog(data.message)
            } catch (e) {
              console.error('解析流数据失败:', e, line)
            }
          }
        }
      }

      onDone()
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('训练流已被用户中止')
        return
      }
      console.error('训练流式输出失败:', error)
      onError('训练流式输出失败')
      onDone()
    }
  },

  async getGridSearchParams(): Promise<ApiResponse<YoloParamGrid>> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/grid-search/params`)
      const data = await response.json()
      if (data.success) {
        return { code: 200, message: 'success', data: data.data }
      }
      return { code: 500, message: data.message || '获取参数网格失败', data: {} as YoloParamGrid }
    } catch (error) {
      console.error('获取参数网格失败:', error)
      return { code: 500, message: '获取参数网格失败', data: {} as YoloParamGrid }
    }
  },

  async startGridSearch(params: GridSearchParams): Promise<ApiResponse<{ output_dir: string, parameters: GridSearchParams }>> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/grid-search/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      })
      const data = await response.json()
      if (data.success) {
        return { code: 200, message: data.message, data: data.data }
      }
      return { code: 500, message: data.message || '启动网格搜索失败', data: {} as any }
    } catch (error) {
      console.error('启动网格搜索失败:', error)
      return { code: 500, message: '启动网格搜索失败', data: {} as any }
    }
  },

  async getGridSearchResults(): Promise<ApiResponse<GridSearchResult>> {
    try {
      const response = await fetch(`${YOLO_TRAIN_API_URL}/grid-search/results`)
      const data = await response.json()
      if (data.success) {
        return { code: 200, message: 'success', data: data.data }
      }
      return { code: 500, message: data.message || '获取网格搜索结果失败', data: {} as GridSearchResult }
    } catch (error) {
      console.error('获取网格搜索结果失败:', error)
      return { code: 500, message: '获取网格搜索结果失败', data: {} as GridSearchResult }
    }
  },
}



export interface DatasetExportParams {
  name: string
  images: Array<{ name: string; data: string }>
  labels: Array<{ name: string; content: string }>
  yaml?: {
    classCount: number
    classes: string[]
    rawData: any
  } | null
  splitRatio: { train: number; val: number }
}

export interface Dataset {
  id: string
  name: string
  description?: string
  createTime: string
  imageCount: number
  labelCount: number
  trainImageCount: number
  trainLabelCount: number
  validImageCount: number
  validLabelCount: number
  testImageCount: number
  testLabelCount: number
  hasYaml: boolean
}

export interface LocalDataset {
  id: string
  name: string
  description?: string
  createTime: Date
  imageCount: number
  labelCount: number
  hasYaml: boolean
}

export const localDatasetStorage = {
  getDatasetList(): LocalDataset[] {
    try {
      const data = localStorage.getItem('dataset_list')
      if (!data) return []
      const parsed = JSON.parse(data)
      return parsed.map((item: any) => ({
        ...item,
        createTime: new Date(item.createTime),
        imageCount: 0,
        labelCount: 0,
        hasYaml: false
      }))
    } catch (error) {
      console.error('获取本地数据集列表失败:', error)
      return []
    }
  },

  getDatasetImages(datasetId: string): Array<{ id: string; name: string; url: string; size: number; uploadTime: Date }> {
    try {
      const data = localStorage.getItem(`dataset_${datasetId}_images`)
      if (!data) return []
      return JSON.parse(data)
    } catch (error) {
      console.error('获取数据集图片失败:', error)
      return []
    }
  },

  getDatasetLabels(datasetId: string): Array<{ id: string; name: string; content: string; size: number; uploadTime: Date }> {
    try {
      const data = localStorage.getItem(`dataset_${datasetId}_labels`)
      if (!data) return []
      return JSON.parse(data)
    } catch (error) {
      console.error('获取数据集标签失败:', error)
      return []
    }
  },

  getDatasetYaml(datasetId: string): { fileName: string; classCount: number; classes: string[]; rawData: any } | null {
    try {
      const data = localStorage.getItem(`dataset_${datasetId}_yaml`)
      if (!data) return null
      return JSON.parse(data)
    } catch (error) {
      console.error('获取数据集YAML失败:', error)
      return null
    }
  },

  getDatasetStats(datasetId: string): { imageCount: number; labelCount: number; hasYaml: boolean } {
    try {
      const images = this.getDatasetImages(datasetId)
      const labels = this.getDatasetLabels(datasetId)
      const yaml = this.getDatasetYaml(datasetId)
      return {
        imageCount: images.length,
        labelCount: labels.length,
        hasYaml: yaml !== null
      }
    } catch (error) {
      return { imageCount: 0, labelCount: 0, hasYaml: false }
    }
  }
}

// 本地存储工具
export const modelStorage = {
  // 保存模型测试结果
  saveTestResult(modelId: string, metrics: ModelMetrics): void {
    try {
      const testResults = this.getTestResults()
      testResults[modelId] = {
        metrics,
        timestamp: new Date().toISOString()
      }
      localStorage.setItem('model_test_results', JSON.stringify(testResults))
    } catch (error) {
      console.error('保存测试结果失败:', error)
    }
  },

  // 获取所有测试结果
  getTestResults(): Record<string, { metrics: ModelMetrics, timestamp: string }> {
    try {
      const data = localStorage.getItem('model_test_results')
      return data ? JSON.parse(data) : {}
    } catch (error) {
      console.error('获取测试结果失败:', error)
      return {}
    }
  },

  // 获取指定模型的测试结果
  getModelTestResult(modelId: string): { metrics: ModelMetrics, timestamp: string } | null {
    const results = this.getTestResults()
    return results[modelId] || null
  },

  clearTestResults(): void {
    try {
      localStorage.removeItem('model_test_results')
    } catch (error) {
      console.error('清除测试结果失败:', error)
    }
  },
}

const getDatasetApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    return 'http://localhost:5006/api'
  }
  const hostname = window.location.hostname
  return `http://${hostname}:5006/api`
}

const DATASET_API_URL = getDatasetApiBaseUrl()

const datasetApiClient = axios.create({
  baseURL: DATASET_API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const datasetApi = {
  async getDatasets(): Promise<{ code: number; message?: string; data?: Dataset[] }> {
    const response = await datasetApiClient.get('/datasets')
    return response.data
  },

  async createDataset(data: { name: string; description?: string }) {
    const response = await datasetApiClient.post('/datasets', data)
    return response.data
  },

  async getDataset(id: string) {
    const response = await datasetApiClient.get(`/datasets/${id}`)
    return response.data
  },

  async deleteDataset(id: string) {
    const response = await datasetApiClient.delete(`/datasets/${id}`)
    return response.data
  },

  async uploadImage(datasetId: string, file: File, split: 'train' | 'test' = 'train') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('split', split)
    const response = await datasetApiClient.post(`/datasets/${datasetId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async uploadImageBase64(datasetId: string, name: string, base64: string, split: 'train' | 'test' = 'train') {
    const response = await datasetApiClient.post(`/datasets/${datasetId}/images`, {
      name,
      base64,
      split
    })
    return response.data
  },

  getImageUrl(datasetId: string, filename: string) {
    return `${DATASET_API_URL}/datasets/${datasetId}/images/${filename}`
  },

  async deleteImage(datasetId: string, filename: string) {
    const response = await datasetApiClient.delete(`/datasets/${datasetId}/images/${filename}`)
    return response.data
  },

  async uploadLabel(datasetId: string, file: File, split: 'train' | 'test' = 'train') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('split', split)
    const response = await axios.post(`${DATASET_API_URL}/datasets/${datasetId}/labels`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async uploadLabelContent(datasetId: string, name: string, content: string, split: 'train' | 'test' = 'train') {
    const response = await axios.post(`${DATASET_API_URL}/datasets/${datasetId}/labels`, {
      name,
      content,
      split
    })
    return response.data
  },

  async getLabelContent(datasetId: string, filename: string) {
    const response = await axios.get(`${DATASET_API_URL}/datasets/${datasetId}/labels/${filename}`)
    return response.data
  },

  async deleteLabel(datasetId: string, filename: string) {
    const response = await axios.delete(`${DATASET_API_URL}/datasets/${datasetId}/labels/${filename}`)
    return response.data
  },

  async uploadYaml(datasetId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await axios.post(`${DATASET_API_URL}/datasets/${datasetId}/yaml`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async uploadYamlContent(datasetId: string, content: string) {
    const response = await axios.post(`${DATASET_API_URL}/datasets/${datasetId}/yaml`, { content })
    return response.data
  },

  async deleteYaml(datasetId: string) {
    const response = await axios.delete(`${DATASET_API_URL}/datasets/${datasetId}/yaml`)
    return response.data
  },

  async autoSplit(datasetId: string, options: { mode: 'ratio' | 'count'; testRatio?: number; testCount?: number }) {
    const response = await axios.post(`${DATASET_API_URL}/datasets/${datasetId}/split`, options)
    return response.data
  },
}
