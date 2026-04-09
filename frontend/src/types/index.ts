/**
 * YOLO检测系统类型定义
 */

// 浓度数据类型
export interface ConcentrationData {
  id: string
  timestamp: Date
  value: number
  unit: string
  sensorId: string
  status: 'normal' | 'warning' | 'danger'
}

// 传感器信息
export interface Sensor {
  id: string
  name: string
  location: string
  type: string
  status: 'online' | 'offline' | 'maintenance'
  lastUpdate: Date
}

// 阈值配置
export interface ThresholdConfig {
  id: string
  sensorId: string
  minValue: number
  maxValue: number
  warningThreshold: number
  dangerThreshold: number
  unit: string
  createdAt: Date
  updatedAt: Date
}

// 历史数据查询参数
export interface HistoryQuery {
  sensorId?: string
  startTime: Date
  endTime: Date
  interval?: 'minute' | 'hour' | 'day'
}

// 历史数据响应
export interface HistoryData {
  data: ConcentrationData[]
  statistics: {
    avg: number
    max: number
    min: number
    count: number
  }
}

// 告警信息
export interface Alert {
  id: string
  sensorId: string
  sensorName: string
  type: 'warning' | 'danger'
  message: string
  value: number
  threshold: number
  timestamp: Date
  isRead: boolean
}

// 仪表盘统计数据
export interface DashboardStats {
  totalSensors: number
  onlineSensors: number
  alertCount: number
  avgConcentration: number
}

// API响应类型
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 分页参数
export interface PaginationParams {
  page: number
  pageSize: number
}

// 分页响应
export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}
