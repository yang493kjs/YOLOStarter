import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface TestStep {
  text: string
  completed: boolean
  active: boolean
  error: boolean
}

export interface TestingTask {
  progress: number
  status: string
  message: string
  steps: TestStep[]
}

export interface ModelMetrics {
  r2?: number
  mae?: number
  rmse?: number
  errorRate?: number
  precision?: number
  recall?: number
  f1Score?: number
  accuracy?: number
  map50?: number
  map50_95?: number
  totalSamples?: number
  success?: number
  failed?: number
}

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
  testStatus: string
  metrics: ModelMetrics | null
  testSteps?: TestStep[]
}

export const useModelsStore = defineStore('models', () => {
  const activeTab = ref(localStorage.getItem('models_activeTab') || 'all')
  const testingTasks = ref<Record<string, TestingTask>>({})
  const currentYoloModel = ref<string | null>(localStorage.getItem('models_currentYoloModel'))

  function setActiveTab(tab: string) {
    activeTab.value = tab
    localStorage.setItem('models_activeTab', tab)
  }

  function setCurrentYoloModel(model: string | null) {
    currentYoloModel.value = model
    if (model) {
      localStorage.setItem('models_currentYoloModel', model)
    } else {
      localStorage.removeItem('models_currentYoloModel')
    }
  }

  function setTestingTask(modelId: string, task: TestingTask) {
    testingTasks.value[modelId] = task
    localStorage.setItem('models_testingTask_' + modelId, JSON.stringify(task))
  }

  function getTestingTask(modelId: string): TestingTask | null {
    const stored = localStorage.getItem('models_testingTask_' + modelId)
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  }

  function removeTestingTask(modelId: string) {
    delete testingTasks.value[modelId]
    localStorage.removeItem('models_testingTask_' + modelId)
  }

  function clearTestingTasks() {
    testingTasks.value = {}
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith('models_testingTask_')) {
        localStorage.removeItem(key)
      }
    })
  }

  function loadTestingTasksFromStorage() {
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith('models_testingTask_')) {
        try {
          const task = JSON.parse(localStorage.getItem(key) || '{}')
          const modelId = key.replace('models_testingTask_', '')
          if (task.status === 'running') {
            task.status = 'interrupted'
            task.message = '测试被中断'
          }
          testingTasks.value[modelId] = task
        } catch {
        }
      }
    })
  }

  return {
    activeTab,
    testingTasks,
    currentYoloModel,
    setActiveTab,
    setCurrentYoloModel,
    setTestingTask,
    getTestingTask,
    removeTestingTask,
    clearTestingTasks,
    loadTestingTasksFromStorage,
  }
})
