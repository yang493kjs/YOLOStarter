<template>
  <div class="training-page">
    <el-tabs v-model="activeTab" class="training-tabs">
      <el-tab-pane label="YOLO训练" name="yolo">
        <div class="training-section">
          <el-card class="section-card">
            <template #header>
              <div class="card-header">
                <el-icon><Aim /></el-icon>
                <span>YOLO目标检测模型训练</span>
              </div>
            </template>
            
            <el-form :model="yoloForm" label-width="120px" class="training-form">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="数据集">
                    <el-input 
                      v-model="yoloForm.datasetName" 
                      placeholder="选择数据集" 
                      readonly
                      @click="openYoloDatasetSelectDialog"
                      style="cursor: pointer"
                    >
                      <template #append>
                        <el-button @click="openYoloDataYamlPicker" title="选择本地文件夹">
                          <el-icon><FolderOpened /></el-icon>
                        </el-button>
                      </template>
                    </el-input>
                    <input 
                      type="file" 
                      ref="yoloDataYamlInput"
                      webkitdirectory="true"
                      style="display: none" 
                      @change="handleYoloDataYamlSelect"
                    />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="基础模型">
                    <el-select v-model="yoloForm.baseModel" style="width: 100%">
                      <el-option label="YOLOv8n (最快)" value="yolov8n.pt" />
                      <el-option label="YOLOv8s (小)" value="yolov8s.pt" />
                      <el-option label="YOLOv8m (中)" value="yolov8m.pt" />
                      <el-option label="YOLOv8l (大)" value="yolov8l.pt" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :xs="24" :sm="8">
                  <el-form-item label="训练轮数">
                    <el-input-number v-model="yoloForm.epochs" :min="10" :max="500" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <el-form-item label="批次大小">
                    <el-input-number v-model="yoloForm.batchSize" :min="1" :max="64" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <el-form-item label="图像尺寸">
                    <el-input-number v-model="yoloForm.imgSize" :min="320" :max="1280" :step="32" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :xs="24" :sm="8">
                  <el-form-item label="设备选择">
                    <el-select v-model="yoloForm.device" style="width: 100%">
                      <el-option label="GPU (自动)" value="0" />
                      <el-option label="CPU" value="cpu" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <el-form-item label="早停耐心值">
                    <el-input-number v-model="yoloForm.patience" :min="5" :max="50" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <el-form-item label="保存周期">
                    <el-input-number v-model="yoloForm.savePeriod" :min="-1" :max="100" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="实验名称">
                    <el-input v-model="yoloForm.name" placeholder="实验名称" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-alert
                title="参数说明"
                type="info"
                :closable="false"
                style="margin-bottom: 20px">
                <template #default>
                  <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                    <li><strong>基础模型</strong>: 预训练模型，n最小最快，x最大最准</li>
                    <li><strong>训练轮数</strong>: 训练的迭代次数，越多越准确但耗时越长</li>
                    <li><strong>批次大小</strong>: 显存不足时可减小该值</li>
                    <li><strong>图像尺寸</strong>: 输入图像尺寸，可选 320/416/640/1280 等</li>
                    <li><strong>设备选择</strong>: GPU编号，"cpu"表示使用CPU</li>
                    <li><strong>早停耐心值</strong>: 多少轮无改善就停止训练</li>
                    <li><strong>保存周期</strong>: -1只保存最佳和最后模型，1表示每轮都保存</li>
                    <li><strong>模型保存目录</strong>: 模型保存的目录路径，留空使用默认</li>
                    <li><strong>实验名称</strong>: 当前训练实验的名称</li>
                  </ul>
                </template>
              </el-alert>
              
              <el-form-item class="form-actions">
                <div class="action-buttons">
                  <el-button type="primary" @click="startYoloTraining" :loading="yoloTraining">
                    <el-icon><VideoPlay /></el-icon>
                    开始训练
                  </el-button>
                  <el-button @click="stopYoloTraining" :disabled="!yoloTraining">
                    <el-icon><VideoPause /></el-icon>
                    停止训练
                  </el-button>
                  <el-button type="success" @click="saveYoloSettings" :disabled="yoloTraining">
                    <el-icon><FolderOpened /></el-icon>
                    保存参数
                  </el-button>
                  <el-button type="warning" @click="resetYoloToDefault" :disabled="yoloTraining">
                    <el-icon><RefreshLeft /></el-icon>
                    恢复默认
                  </el-button>
                </div>
                <span class="save-params-tip">请先保存参数后再训练</span>
              </el-form-item>
              
              <div v-if="yoloTraining" class="progress-section">
                <el-progress :percentage="yoloProgress" :status="yoloProgressStatus" />
                <div class="progress-text">{{ yoloProgressText }}</div>
              </div>
            </el-form>
          </el-card>
          
          <el-card class="section-card" v-if="yoloTrainingLog.length > 0">
            <template #header>
              <div class="card-header">
                <el-icon><Document /></el-icon>
                <span>训练日志</span>
              </div>
            </template>
            <div class="training-log">
              <div v-for="(log, index) in yoloTrainingLog" :key="index" class="log-item">
                {{ log }}
              </div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="datasetSelectVisible"
      title="选择数据集"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="dataset-list" v-if="localDatasets.length > 0">
        <el-table :data="localDatasets" style="width: 100%" @row-click="selectLocalDataset">
          <el-table-column prop="name" label="数据集名称" width="200" />
          <el-table-column label="图片数量" width="120">
            <template #default="{ row }">
              {{ row.imageCount }}
            </template>
          </el-table-column>
          <el-table-column label="标签数量" width="120">
            <template #default="{ row }">
              {{ row.labelCount }}
            </template>
          </el-table-column>
          <el-table-column label="YAML配置" width="100">
            <template #default="{ row }">
              <el-tag :type="row.hasYaml ? 'success' : 'danger'" size="small">
                {{ row.hasYaml ? '已配置' : '未配置' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" width="180">
            <template #default="{ row }">
              {{ new Date(row.createTime).toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click.stop="selectDatasetPath(row)">
                选择
              </el-button>
              <el-button type="danger" size="small" @click.stop="deleteDataset(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无数据集，请先在数据集管理页面创建数据集" />
      
      <template #footer>
        <el-button @click="datasetSelectVisible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Aim,
  VideoPlay,
  VideoPause,
  Document,
  FolderOpened,
  RefreshLeft,
} from '@element-plus/icons-vue'
import { yoloTrainApi, type YoloTrainParams, datasetApi, type LocalDataset } from '@/api'
import { useTrainingStore } from '@/stores/training'
import { storeToRefs } from 'pinia'

const trainingStore = useTrainingStore()

const { 
  yoloTraining, 
  yoloProgress,
  yoloProgressStatus,
  yoloProgressText,
  yoloTrainingLog,
} = storeToRefs(trainingStore)

const activeTab = computed({
  get: () => trainingStore.activeTab,
  set: (val) => trainingStore.setActiveTab(val)
})

const yoloForm = trainingStore.yoloForm
const _gridSearchForm = trainingStore.gridSearchForm

watch(yoloForm, () => {
  trainingStore.saveYoloForm()
}, { deep: true })

watch(_gridSearchForm, () => {
  trainingStore.saveGridSearchForm()
}, { deep: true })

const yoloDataYamlInput = ref<HTMLInputElement | null>(null)

const _lr0Input = ref('')
const _lrfInput = ref('')
const _momentumInput = ref('')
const _weightDecayInput = ref('')
const _warmupEpochsInput = ref('')
const _boxInput = ref('')
const _clsInput = ref('')
const _dflInput = ref('')

const datasetSelectVisible = ref(false)
const localDatasets = ref<LocalDataset[]>([])

function initParamGridInputs() {
  _lr0Input.value = _gridSearchForm.paramGrid.lr0.join(',')
  _lrfInput.value = _gridSearchForm.paramGrid.lrf.join(',')
  _momentumInput.value = _gridSearchForm.paramGrid.momentum.join(',')
  _weightDecayInput.value = _gridSearchForm.paramGrid.weight_decay.join(',')
  _warmupEpochsInput.value = _gridSearchForm.paramGrid.warmup_epochs.join(',')
  _boxInput.value = _gridSearchForm.paramGrid.box.join(',')
  _clsInput.value = _gridSearchForm.paramGrid.cls.join(',')
  _dflInput.value = _gridSearchForm.paramGrid.dfl.join(',')
}

onMounted(() => {
  checkTrainingStatus()
  initParamGridInputs()
})

let yoloStreamController: AbortController | null = null

async function checkTrainingStatus() {
  try {
    const yoloResult = await yoloTrainApi.getStatus()
    if (yoloResult.code === 200 && yoloResult.data) {
      const status = yoloResult.data
      
      if (status.is_training) {
        trainingStore.setYoloTrainingStatus(true, status.progress, '', status.message)
        trainingStore.clearYoloLog()
        
        if (status.current_task) {
          trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 恢复训练会话`)
          trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 数据配置文件: ${status.current_task.data_yaml}`)
          trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 基础模型: ${status.current_task.model_name}`)
          trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 训练轮数: ${status.current_task.epochs}`)
          trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 当前Epoch: ${status.epoch}/${status.total_epochs}`)
        }
        
        startYoloStream()
        
        ElMessage.info('检测到YOLO训练任务正在后台运行，已恢复训练状态')
      }
    }
  } catch (error) {
    console.error('检查训练状态失败:', error)
  }
}

function startYoloStream() {
  yoloStreamController = new AbortController()
  
  yoloTrainApi.trainStream(
    (message) => {
      if (message !== '[DONE]') {
        trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] ${message}`)
      }
    },
    (status) => {
      trainingStore.setYoloTrainingStatus(true, status.progress, '', status.message)
    },
    (error) => {
      trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 错误: ${error}`)
      ElMessage.error(error)
    },
    () => {
      trainingStore.setYoloTrainingStatus(false, 100, 'success', '训练完成！')
      trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 训练完成`)
      ElMessage.success('YOLO训练完成')
      yoloStreamController = null
    },
    yoloStreamController.signal
  )
}

function stopYoloStream() {
  if (yoloStreamController) {
    yoloStreamController.abort()
    yoloStreamController = null
  }
}

function saveYoloSettings() {
  trainingStore.saveYoloForm()
  ElMessage.success('YOLO参数已保存')
}

function resetYoloToDefault() {
  ElMessageBox.confirm(
    '确定要恢复默认参数吗？此操作将清除当前所有设置',
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    yoloForm.datasetName = ''
    yoloForm.dataYaml = ''
    yoloForm.baseModel = 'yolov8n.pt'
    yoloForm.epochs = 100
    yoloForm.batchSize = 16
    yoloForm.imgSize = 640
    yoloForm.device = '0'
    yoloForm.patience = 20
    yoloForm.savePeriod = -1
    yoloForm.project = ''
    yoloForm.name = 'train'
    ElMessage.success('YOLO参数已恢复为默认值')
  }).catch(() => {
    ElMessage.info('已取消恢复默认参数操作')
  })
}

const openYoloDataYamlPicker = () => {
  yoloDataYamlInput.value?.click()
}

const handleYoloDataYamlSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const files = Array.from(target.files)
    
    const firstFile = files[0]
    const firstPath = firstFile.webkitRelativePath || firstFile.name
    const pathParts = firstPath.split('/')
    const folderName = pathParts.length > 1 ? pathParts[0] : 'dataset'
    
    const yamlFile = files.find(file => {
      const fileName = file.name.toLowerCase()
      return fileName.endsWith('.yaml') || fileName.endsWith('.yml')
    })
    
    if (yamlFile) {
      const yamlPath = yamlFile.webkitRelativePath || yamlFile.name
      trainingStore.updateYoloForm(folderName, yamlPath)
      ElMessage.success(`已选择文件夹: ${folderName}, 找到配置文件: ${yamlFile.name}`)
    } else {
      ElMessage.warning(`已选择文件夹: ${folderName}，但未找到 YAML 配置文件`)
      trainingStore.updateYoloForm(folderName, '')
    }
  }
}

const openYoloDatasetSelectDialog = () => {
  datasetSelectVisible.value = true
  loadDatasets()
}

const loadDatasets = async () => {
  const result = await datasetApi.getDatasets()
  if (result.code === 200 && result.data) {
    localDatasets.value = result.data.map((ds: any) => ({
      id: ds.id,
      name: ds.name,
      description: ds.description || '',
      createTime: new Date(ds.createTime),
      imageCount: ds.imageCount,
      labelCount: ds.labelCount,
      hasYaml: ds.hasYaml
    }))
  }
}

const selectLocalDataset = (row: LocalDataset) => {
  selectDatasetPath(row)
}

const selectDatasetPath = (dataset: LocalDataset) => {
  if (dataset.imageCount === 0) {
    ElMessage.error('数据集没有图片，无法使用')
    return
  }
  
  if (!dataset.hasYaml) {
    ElMessage.warning('该数据集缺少YAML配置文件，训练可能会失败')
  }
  
  trainingStore.updateYoloForm(dataset.name, `datasets/${dataset.id}/data.yaml`)
  
  datasetSelectVisible.value = false
  ElMessage.success(`已选择数据集: ${dataset.name}`)
}

const deleteDataset = async (dataset: LocalDataset) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据集 "${dataset.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const result = await datasetApi.deleteDataset(dataset.id)
    if (result.code === 200) {
      ElMessage.success('数据集已删除')
      loadDatasets()
    } else {
      ElMessage.error(result.message || '删除数据集失败')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`删除数据集失败: ${error.message || '未知错误'}`)
    }
  }
}

const startYoloTraining = async () => {
  trainingStore.saveYoloForm()
  
  trainingStore.setYoloTrainingStatus(true, 0, '', '正在初始化训练环境...')
  trainingStore.clearYoloLog()
  
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 开始YOLO模型训练...`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 数据配置文件: ${yoloForm.dataYaml}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 基础模型: ${yoloForm.baseModel}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 训练轮数: ${yoloForm.epochs}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 批次大小: ${yoloForm.batchSize}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 图像尺寸: ${yoloForm.imgSize}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 设备: ${yoloForm.device === 'cpu' ? 'CPU' : 'GPU ' + yoloForm.device}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 早停耐心值: ${yoloForm.patience}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 保存周期: ${yoloForm.savePeriod === -1 ? '只保存最佳和最后' : yoloForm.savePeriod}`)
  trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 实验名称: ${yoloForm.name}`)
  
  const params: YoloTrainParams = {
    data_yaml: yoloForm.dataYaml,
    model_name: yoloForm.baseModel,
    epochs: yoloForm.epochs,
    batch: yoloForm.batchSize,
    imgsz: yoloForm.imgSize,
    device: yoloForm.device,
    name: yoloForm.name,
    patience: yoloForm.patience,
    save_period: yoloForm.savePeriod,
  }
  
  try {
    const startResult = await yoloTrainApi.startTraining(params)
    if (startResult.code !== 200) {
      ElMessage.error(startResult.message)
      trainingStore.setYoloTrainingStatus(false, 0, 'exception', '启动失败')
      return
    }
    
    ElMessage.success('YOLO训练任务已启动')
    trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 模型保存目录: ${startResult.data?.output_dir}`)
    
    startYoloStream()
  } catch (error: any) {
    ElMessage.error(`启动训练失败: ${error.message || '未知错误'}`)
    trainingStore.setYoloTrainingStatus(false, 0, 'exception', '启动失败')
  }
}

const stopYoloTraining = async () => {
  try {
    stopYoloStream()
    const result = await yoloTrainApi.stopTraining()
    if (result.code === 200) {
      trainingStore.setYoloTrainingStatus(false, trainingStore.yoloProgress, 'exception', '训练已停止')
      trainingStore.addYoloLog(`[${new Date().toLocaleTimeString()}] 训练已停止`)
      ElMessage.warning('YOLO训练已停止')
    } else {
      ElMessage.error(result.message)
    }
  } catch (error: any) {
    console.error('停止训练出错:', error)
    ElMessage.error(`停止训练失败: ${error.message || '未知错误'}`)
    stopYoloStream()
    trainingStore.setYoloTrainingStatus(false, trainingStore.yoloProgress, 'exception', '训练已停止')
  }
}
</script>

<style scoped>
.training-page {
  height: 100%;
}

.training-tabs {
  height: 100%;
}

.training-tabs :deep(.el-tabs__content) {
  height: calc(100% - 40px);
  overflow-y: auto;
}

.training-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.training-form {
  max-width: 100%;
}

.save-params-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #f78989;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.action-buttons .el-button {
  flex: 0 0 auto;
}

.form-actions :deep(.el-form-item__content) {
  flex-direction: column;
  align-items: flex-start;
}

.result-descriptions {
  width: 100%;
}

.result-descriptions :deep(.el-descriptions__label) {
  font-weight: 500;
  white-space: nowrap;
}

.result-descriptions :deep(.el-descriptions__content) {
  word-break: break-all;
}

.path-item :deep(.el-descriptions__content) {
  font-size: 12px;
  word-break: break-all;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table-wrapper :deep(.el-table) {
  min-width: 500px;
}

.progress-section {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-text {
  margin-top: 12px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.training-log {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 300px;
  overflow-y: auto;
}

.log-item {
  padding: 2px 0;
}

.log-item:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

@media (max-width: 992px) {
  .training-form :deep(.el-col) {
    margin-bottom: 12px;
  }
  
  .training-form :deep(.el-form-item__label) {
    font-size: 14px;
  }
}

@media (max-width: 768px) {
  .training-page {
    padding: 0;
  }
  
  .training-tabs :deep(.el-tabs__header) {
    margin-bottom: 12px;
  }
  
  .training-tabs :deep(.el-tabs__nav) {
    display: flex;
    width: 100%;
  }
  
  .training-tabs :deep(.el-tabs__item) {
    flex: 1;
    text-align: center;
    font-size: 14px;
    padding: 0 8px;
  }
  
  .training-tabs :deep(.el-tabs__content) {
    overflow-x: hidden;
  }
  
  .training-section {
    gap: 12px;
  }
  
  .section-card :deep(.el-card__header) {
    padding: 12px 16px;
  }
  
  .section-card :deep(.el-card__body) {
    padding: 12px;
  }
  
  .card-header {
    font-size: 15px;
    flex-wrap: wrap;
  }
  
  .training-form {
    padding: 0;
  }
  
  .training-form :deep(.el-row) {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .training-form :deep(.el-col) {
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-bottom: 0;
  }
  
  .training-form :deep(.el-form-item) {
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .training-form :deep(.el-form-item__label) {
    float: none;
    text-align: left;
    padding-bottom: 8px;
    line-height: 1.4;
    font-size: 13px;
    width: 100% !important;
    max-width: 100% !important;
  }
  
  .training-form :deep(.el-form-item__content) {
    margin-left: 0 !important;
    width: 100%;
  }
  
  .training-form :deep(.el-input-number) {
    width: 100% !important;
  }
  
  .training-form :deep(.el-input-number .el-input__wrapper) {
    padding-left: 8px;
    padding-right: 8px;
  }
  
  .training-form :deep(.el-input-number__decrease),
  .training-form :deep(.el-input-number__increase) {
    width: 28px;
  }
  
  .training-form :deep(.el-select) {
    width: 100% !important;
  }
  
  .training-form :deep(.el-slider) {
    width: 100% !important;
  }
  
  .training-form :deep(.el-slider__runway) {
    margin: 12px 0;
  }
  
  .training-form :deep(.el-slider__input) {
    width: 80px !important;
    min-width: 80px;
  }
  
  .training-form :deep(.el-switch) {
    height: 28px;
  }
  
  .training-form :deep(.el-switch__core) {
    min-width: 44px;
    height: 24px;
  }
  
  .training-form :deep(.el-alert) {
    padding: 10px 12px;
    margin: 12px 0;
  }
  
  .training-form :deep(.el-alert ul) {
    font-size: 12px;
    line-height: 1.8;
    padding-left: 16px;
    margin: 0;
  }
  
  .training-form :deep(.el-alert li) {
    margin-bottom: 4px;
  }
  
  .training-form :deep(.el-divider) {
    margin: 16px 0;
  }
  
  .training-form :deep(.el-divider__text) {
    font-size: 13px;
    font-weight: 600;
    color: #409eff;
  }
  
  .training-form :deep(.el-form-item:last-child) {
    margin-bottom: 0;
  }
  
  .training-form :deep(.el-button) {
    margin-bottom: 0;
    min-height: 40px;
    padding: 10px 16px;
  }
  
  .training-form :deep(.el-button + .el-button) {
    margin-left: 0;
  }
  
  .action-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    width: 100%;
  }
  
  .action-buttons .el-button {
    width: 100%;
    margin: 0;
  }
  
  .form-actions :deep(.el-form-item__content) {
    flex-direction: column;
    align-items: stretch;
  }
  
  .save-params-tip {
    display: block;
    margin-left: 0;
    margin-top: 8px;
    font-size: 11px;
  }
  
  .progress-section {
    padding: 12px;
  }
  
  .progress-text {
    font-size: 13px;
  }
  
  .training-log {
    padding: 12px;
    font-size: 12px;
    max-height: 200px;
  }
  
  .log-item {
    padding: 1px 0;
    font-size: 11px;
    word-break: break-all;
  }
  
  .result-descriptions :deep(.el-descriptions__label) {
    font-size: 12px;
    width: 120px !important;
    min-width: 120px;
  }
  
  .result-descriptions :deep(.el-descriptions__content) {
    font-size: 13px;
  }
  
  .table-wrapper {
    margin: 0 -12px;
    padding: 0 12px;
  }
  
  .table-wrapper :deep(.el-table__cell) {
    padding: 8px 4px;
    font-size: 12px;
  }
  
  .table-wrapper :deep(.el-button--small) {
    padding: 5px 8px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .training-tabs :deep(.el-tabs__item) {
    font-size: 12px;
    padding: 0 4px;
  }
  
  .card-header {
    font-size: 14px;
  }
  
  .section-card :deep(.el-card__header) {
    padding: 10px 12px;
  }
  
  .section-card :deep(.el-card__body) {
    padding: 10px;
  }
  
  .training-form :deep(.el-form-item__label) {
    font-size: 12px;
    padding-bottom: 6px;
  }
  
  .training-form :deep(.el-button) {
    padding: 8px 12px;
    font-size: 13px;
    min-height: 38px;
  }
  
  .action-buttons {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .action-buttons .el-button {
    width: 100%;
  }
  
  .training-form :deep(.el-alert ul) {
    font-size: 11px;
  }
  
  .training-form :deep(.el-divider__text) {
    font-size: 12px;
  }
  
  .training-form :deep(.el-slider__input) {
    width: 70px !important;
    min-width: 70px;
  }
  
  .training-log {
    font-size: 11px;
    padding: 10px;
  }
}
</style>
