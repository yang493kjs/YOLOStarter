import { ElMessage } from 'element-plus'

interface YoloTrainingParams {
  dataYaml: string
  baseModel: string
  epochs: number
  batchSize: number
  imgSize: number
  device: string
  patience: number
  savePeriod: number
  project: string
  name: string
}

interface StorageData {
  yoloParams: YoloTrainingParams
  lastUpdated: string
}

const STORAGE_KEY = 'densevis_training_params'

const defaultYoloParams: YoloTrainingParams = {
  dataYaml: 'data/bread.yaml',
  baseModel: 'yolov8n.pt',
  epochs: 100,
  batchSize: 16,
  imgSize: 640,
  device: '0',
  patience: 20,
  savePeriod: -1,
  project: '',
  name: 'train',
}

function validateYoloParams(params: any): params is YoloTrainingParams {
  return (
    typeof params === 'object' &&
    typeof params.dataYaml === 'string' &&
    typeof params.baseModel === 'string' &&
    typeof params.epochs === 'number' &&
    params.epochs >= 10 && params.epochs <= 500 &&
    typeof params.batchSize === 'number' &&
    params.batchSize >= 1 && params.batchSize <= 64 &&
    typeof params.imgSize === 'number' &&
    params.imgSize >= 320 && params.imgSize <= 1280 &&
    typeof params.device === 'string' &&
    typeof params.patience === 'number' &&
    params.patience >= 5 && params.patience <= 50 &&
    typeof params.savePeriod === 'number' &&
    params.savePeriod >= -1 && params.savePeriod <= 100 &&
    typeof params.project === 'string' &&
    typeof params.name === 'string'
  )
}

function validateStorageData(data: any): data is StorageData {
  return (
    typeof data === 'object' &&
    validateYoloParams(data.yoloParams) &&
    typeof data.lastUpdated === 'string'
  )
}

export function saveYoloParams(params: YoloTrainingParams): boolean {
  try {
    const newData: StorageData = {
      yoloParams: params,
      lastUpdated: new Date().toISOString(),
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(newData))
    ElMessage.success('YOLO训练参数保存成功')
    return true
  } catch (error) {
    console.error('保存YOLO参数失败:', error)
    ElMessage.error('保存YOLO训练参数失败，请重试')
    return false
  }
}

function loadStorageData(): StorageData | null {
  try {
    const dataStr = localStorage.getItem(STORAGE_KEY)
    if (!dataStr) {
      return null
    }

    const data = JSON.parse(dataStr)

    if (!validateStorageData(data)) {
      console.warn('本地存储数据格式无效，将使用默认值')
      return null
    }

    return data
  } catch (error) {
    console.error('读取本地存储失败:', error)
    return null
  }
}

export function loadYoloParams(): YoloTrainingParams {
  const data = loadStorageData()
  if (data && validateYoloParams(data.yoloParams)) {
    return data.yoloParams
  }
  return { ...defaultYoloParams }
}

export function getLastUpdateTime(): string | null {
  const data = loadStorageData()
  return data?.lastUpdated || null
}

export function clearStorage(): boolean {
  try {
    localStorage.removeItem(STORAGE_KEY)
    ElMessage.success('已清除本地存储的训练参数')
    return true
  } catch (error) {
    console.error('清除本地存储失败:', error)
    ElMessage.error('清除本地存储失败，请重试')
    return false
  }
}

export function hasStoredData(): boolean {
  return loadStorageData() !== null
}

export { defaultYoloParams }
