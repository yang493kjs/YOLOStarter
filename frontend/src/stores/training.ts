import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

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

export interface GridSearchResult {
  best_params: Record<string, any>
  best_score: number
  all_results: Array<{
    params: Record<string, any>
    metrics: Record<string, number>
    fold_metrics?: Array<Record<string, number>>
  }>
}

export const useTrainingStore = defineStore('training', () => {
  const storedTab = localStorage.getItem('training_activeTab')
  const activeTab = ref(storedTab && storedTab !== 'ml' ? storedTab : 'yolo')

  const yoloTraining = ref(false)

  const yoloProgress = ref(0)
  const yoloProgressStatus = ref('')
  const yoloProgressText = ref('')

  const yoloTrainingLog = ref<string[]>([])

  const gridSearchRunning = ref(false)
  const gridSearchProgress = ref(0)
  const gridSearchProgressStatus = ref('')
  const gridSearchProgressText = ref('')
  const gridSearchLog = ref<string[]>([])
  const gridSearchResult = ref<GridSearchResult | null>(null)

  const gridSearchForm = reactive({
    datasetName: localStorage.getItem('gridSearchForm_datasetName') || '',
    dataYaml: localStorage.getItem('gridSearchForm_dataYaml') || '',
    baseModel: localStorage.getItem('gridSearchForm_baseModel') || 'yolov8n.pt',
    epochs: parseInt(localStorage.getItem('gridSearchForm_epochs') || '50'),
    batchSize: parseInt(localStorage.getItem('gridSearchForm_batchSize') || '16'),
    imgSize: parseInt(localStorage.getItem('gridSearchForm_imgSize') || '640'),
    device: localStorage.getItem('gridSearchForm_device') || '0',
    patience: parseInt(localStorage.getItem('gridSearchForm_patience') || '10'),
    savePeriod: parseInt(localStorage.getItem('gridSearchForm_savePeriod') || '-1'),
    name: localStorage.getItem('gridSearchForm_name') || 'grid_search',
    cvFolds: parseInt(localStorage.getItem('gridSearchForm_cvFolds') || '5'),
    paramGrid: JSON.parse(localStorage.getItem('gridSearchForm_paramGrid') || JSON.stringify({
      lr0: [0.001, 0.01, 0.1],
      lrf: [0.01, 0.1],
      momentum: [0.9, 0.937, 0.95],
      weight_decay: [0.0001, 0.0005, 0.001],
      warmup_epochs: [0.0, 1.0, 3.0],
      box: [7.5, 10.0],
      cls: [0.5, 1.0],
      dfl: [1.5, 3.0]
    }))
  })

  const yoloForm = reactive({
    datasetName: localStorage.getItem('yoloForm_datasetName') || '',
    dataYaml: localStorage.getItem('yoloForm_dataYaml') || '',
    baseModel: localStorage.getItem('yoloForm_baseModel') || 'yolov8n.pt',
    epochs: parseInt(localStorage.getItem('yoloForm_epochs') || '100'),
    batchSize: parseInt(localStorage.getItem('yoloForm_batchSize') || '16'),
    imgSize: parseInt(localStorage.getItem('yoloForm_imgSize') || '640'),
    device: localStorage.getItem('yoloForm_device') || '0',
    patience: parseInt(localStorage.getItem('yoloForm_patience') || '20'),
    savePeriod: parseInt(localStorage.getItem('yoloForm_savePeriod') || '-1'),
    project: localStorage.getItem('yoloForm_project') || '',
    name: localStorage.getItem('yoloForm_name') || 'train',
  })

  function updateYoloForm(name: string, yaml: string) {
    yoloForm.datasetName = name
    yoloForm.dataYaml = yaml
    saveYoloForm()
  }

  function setActiveTab(tab: string) {
    activeTab.value = tab
    localStorage.setItem('training_activeTab', tab)
  }

  function saveYoloForm() {
    localStorage.setItem('yoloForm_datasetName', yoloForm.datasetName)
    localStorage.setItem('yoloForm_dataYaml', yoloForm.dataYaml)
    localStorage.setItem('yoloForm_baseModel', yoloForm.baseModel)
    localStorage.setItem('yoloForm_epochs', String(yoloForm.epochs))
    localStorage.setItem('yoloForm_batchSize', String(yoloForm.batchSize))
    localStorage.setItem('yoloForm_imgSize', String(yoloForm.imgSize))
    localStorage.setItem('yoloForm_device', yoloForm.device)
    localStorage.setItem('yoloForm_patience', String(yoloForm.patience))
    localStorage.setItem('yoloForm_savePeriod', String(yoloForm.savePeriod))
    localStorage.setItem('yoloForm_project', yoloForm.project)
    localStorage.setItem('yoloForm_name', yoloForm.name)
  }

  function setYoloTrainingStatus(training: boolean, progress: number = 0, status: string = '', text: string = '') {
    yoloTraining.value = training
    yoloProgress.value = progress
    yoloProgressStatus.value = status
    yoloProgressText.value = text
  }

  function addYoloLog(message: string) {
    yoloTrainingLog.value.push(message)
    if (yoloTrainingLog.value.length > 500) {
      yoloTrainingLog.value = yoloTrainingLog.value.slice(-500)
    }
  }

  function clearYoloLog() {
    yoloTrainingLog.value = []
  }

  function saveGridSearchForm() {
    localStorage.setItem('gridSearchForm_datasetName', gridSearchForm.datasetName)
    localStorage.setItem('gridSearchForm_dataYaml', gridSearchForm.dataYaml)
    localStorage.setItem('gridSearchForm_baseModel', gridSearchForm.baseModel)
    localStorage.setItem('gridSearchForm_epochs', String(gridSearchForm.epochs))
    localStorage.setItem('gridSearchForm_batchSize', String(gridSearchForm.batchSize))
    localStorage.setItem('gridSearchForm_imgSize', String(gridSearchForm.imgSize))
    localStorage.setItem('gridSearchForm_device', gridSearchForm.device)
    localStorage.setItem('gridSearchForm_patience', String(gridSearchForm.patience))
    localStorage.setItem('gridSearchForm_savePeriod', String(gridSearchForm.savePeriod))
    localStorage.setItem('gridSearchForm_name', gridSearchForm.name)
    localStorage.setItem('gridSearchForm_cvFolds', String(gridSearchForm.cvFolds))
    localStorage.setItem('gridSearchForm_paramGrid', JSON.stringify(gridSearchForm.paramGrid))
  }

  function setGridSearchStatus(running: boolean, progress: number = 0, status: string = '', text: string = '') {
    gridSearchRunning.value = running
    gridSearchProgress.value = progress
    gridSearchProgressStatus.value = status
    gridSearchProgressText.value = text
  }

  function addGridSearchLog(message: string) {
    gridSearchLog.value.push(message)
    if (gridSearchLog.value.length > 500) {
      gridSearchLog.value = gridSearchLog.value.slice(-500)
    }
  }

  function clearGridSearchLog() {
    gridSearchLog.value = []
  }

  function setGridSearchResult(result: GridSearchResult | null) {
    gridSearchResult.value = result
  }

  return {
    activeTab,
    yoloTraining,
    yoloProgress,
    yoloProgressStatus,
    yoloProgressText,
    yoloTrainingLog,
    yoloForm,
    gridSearchRunning,
    gridSearchProgress,
    gridSearchProgressStatus,
    gridSearchProgressText,
    gridSearchLog,
    gridSearchResult,
    gridSearchForm,
    setActiveTab,
    saveYoloForm,
    setYoloTrainingStatus,
    addYoloLog,
    clearYoloLog,
    saveGridSearchForm,
    setGridSearchStatus,
    addGridSearchLog,
    clearGridSearchLog,
    setGridSearchResult,
    updateYoloForm,
  }
})
