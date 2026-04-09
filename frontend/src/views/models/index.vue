<template>
  <div class="model-manager">
    <div class="page-header">
      <h1 class="page-title">模型管理器</h1>
      <p class="page-description">管理和评估所有训练完成的模型</p>
      <el-button 
        type="primary" 
        :icon="Refresh" 
        @click="refreshModels"
        :loading="loading"
        circle
        class="refresh-button"
      />
    </div>

    <div class="content-container">
      <el-tabs v-model="activeTab" class="model-tabs">
        <el-tab-pane label="全部模型" name="all">
          <div class="tab-content">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="model in filteredModels" :key="model.id">
                <el-card class="model-card" :class="{ 'testing': model.testing, 'tested': model.tested, 'is-current': isCurrentModel(model) }">
                  <template #header>
                    <div class="card-header">
                      <el-icon class="model-icon"><Box /></el-icon>
                      <span class="model-name">{{ model.name }}</span>
                      <el-tag 
                        :type="model.type === 'YOLO' ? 'primary' : 'success'" 
                        size="small"
                      >
                        {{ model.type }}
                      </el-tag>
                      <el-tag v-if="isCurrentModel(model)" type="success" size="small" effect="dark">
                        当前使用
                      </el-tag>
                    </div>
                  </template>

                  <div class="model-info">
                    <div class="info-item">
                      <el-icon><Calendar /></el-icon>
                      <span>创建时间: {{ formatDate(model.createdAt) }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><DataLine /></el-icon>
                      <span>训练轮数: {{ model.epochs }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><FolderOpened /></el-icon>
                      <span>模型路径: {{ truncatePath(model.path) }}</span>
                    </div>
                  </div>

                  <div class="model-actions">
                    <el-button 
                      type="primary" 
                      @click="testModel(model)"
                      :loading="model.testing"
                      :disabled="model.testing"
                      size="small"
                    >
                      <el-icon><VideoPlay /></el-icon>
                      {{ model.testing ? '测试中...' : '开始测试' }}
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="setAsActiveModel(model)"
                      :disabled="model.testing"
                      size="small"
                      :class="{ 'is-active-model': isCurrentModel(model) }"
                    >
                      <el-icon><Check /></el-icon>
                      {{ isCurrentModel(model) ? '当前使用' : '设为测试模型' }}
                    </el-button>
                    <el-button 
                      type="danger" 
                      @click="deleteModel(model)"
                      :disabled="model.testing"
                      size="small"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </div>

                  <div v-if="model.tested && model.metrics" class="metrics-section">
                    <el-divider content-position="left">评估指标</el-divider>
                    <div class="metrics-grid">
                      <div class="metric-item">
                        <div class="metric-label">mAP@50</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.accuracy ?? model.metrics.map50 ?? 0)">
                          {{ ((model.metrics.accuracy ?? model.metrics.map50 ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">精确率</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.precision ?? 0)">
                          {{ ((model.metrics.precision ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">召回率</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.recall ?? 0)">
                          {{ ((model.metrics.recall ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">F1分数</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.f1Score ?? 0)">
                          {{ ((model.metrics.f1Score ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div v-if="model.metrics.map50_95" class="metric-item">
                        <div class="metric-label">mAP@50-95</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.map50_95 ?? 0)">
                          {{ ((model.metrics.map50_95 ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div v-if="model.metrics.errorRate !== undefined" class="metric-item">
                        <div class="metric-label">误差率</div>
                        <div class="metric-value" :class="model.metrics.errorRate < 0.1 ? 'metric-excellent' : model.metrics.errorRate < 0.2 ? 'metric-average' : 'metric-poor'">
                          {{ (model.metrics.errorRate * 100).toFixed(2) }}%
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="model.testing" class="testing-progress">
                    <el-progress :percentage="model.testProgress" :status="model.testStatus" />
                    <div class="progress-text">{{ model.testProgressText }}</div>
                    <div v-if="model.testSteps && model.testSteps.length > 0" class="test-steps">
                      <div class="steps-title">测试步骤</div>
                      <div class="steps-list">
                        <div 
                          v-for="(step, index) in model.testSteps" 
                          :key="index"
                          class="step-item"
                          :class="{ 'completed': step.completed, 'active': step.active, 'error': step.error }"
                        >
                          <el-icon v-if="step.completed" class="step-icon"><CircleCheck /></el-icon>
                          <el-icon v-else-if="step.active" class="step-icon loading"><Loading /></el-icon>
                          <el-icon v-else-if="step.error" class="step-icon error"><CircleClose /></el-icon>
                          <el-icon v-else class="step-icon pending"><Clock /></el-icon>
                          <span class="step-text">{{ step.text }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-empty v-if="filteredModels.length === 0" description="暂无模型，请先训练模型" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="YOLO模型" name="yolo">
          <div class="tab-content">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="model in filteredModels" :key="model.id">
                <el-card class="model-card" :class="{ 'testing': model.testing, 'tested': model.tested, 'is-current': isCurrentModel(model) }">
                  <template #header>
                    <div class="card-header">
                      <el-icon class="model-icon"><Box /></el-icon>
                      <span class="model-name">{{ model.name }}</span>
                      <el-tag type="primary" size="small">YOLO</el-tag>
                      <el-tag v-if="isCurrentModel(model)" type="success" size="small" effect="dark">
                        当前使用
                      </el-tag>
                    </div>
                  </template>

                  <div class="model-info">
                    <div class="info-item">
                      <el-icon><Calendar /></el-icon>
                      <span>创建时间: {{ formatDate(model.createdAt) }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><DataLine /></el-icon>
                      <span>训练轮数: {{ model.epochs }}</span>
                    </div>
                    <div class="info-item">
                      <el-icon><FolderOpened /></el-icon>
                      <span>模型路径: {{ truncatePath(model.path) }}</span>
                    </div>
                  </div>

                  <div class="model-actions">
                    <el-button 
                      type="primary" 
                      @click="testModel(model)"
                      :loading="model.testing"
                      :disabled="model.testing"
                      size="small"
                    >
                      <el-icon><VideoPlay /></el-icon>
                      {{ model.testing ? '测试中...' : '开始测试' }}
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="setAsActiveModel(model)"
                      :disabled="model.testing"
                      size="small"
                      :class="{ 'is-active-model': isCurrentModel(model) }"
                    >
                      <el-icon><Check /></el-icon>
                      {{ isCurrentModel(model) ? '当前使用' : '设为测试模型' }}
                    </el-button>
                    <el-button 
                      type="danger" 
                      @click="deleteModel(model)"
                      :disabled="model.testing"
                      size="small"
                    >
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </div>

                  <div v-if="model.tested && model.metrics" class="metrics-section">
                    <el-divider content-position="left">评估指标</el-divider>
                    <div class="metrics-grid">
                      <div class="metric-item">
                        <div class="metric-label">mAP@50</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.accuracy ?? model.metrics.map50 ?? 0)">
                          {{ ((model.metrics.accuracy ?? model.metrics.map50 ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">精确率</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.precision ?? 0)">
                          {{ ((model.metrics.precision ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">召回率</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.recall ?? 0)">
                          {{ ((model.metrics.recall ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">F1分数</div>
                        <div class="metric-value" :class="getMetricClass(model.metrics.f1Score ?? 0)">
                          {{ ((model.metrics.f1Score ?? 0) * 100).toFixed(2) }}%
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="model.testing" class="testing-progress">
                    <el-progress :percentage="model.testProgress" :status="model.testStatus" />
                    <div class="progress-text">{{ model.testProgressText }}</div>
                    <div v-if="model.testSteps && model.testSteps.length > 0" class="test-steps">
                      <div class="steps-title">测试步骤</div>
                      <div class="steps-list">
                        <div 
                          v-for="(step, index) in model.testSteps" 
                          :key="index"
                          class="step-item"
                          :class="{ 'completed': step.completed, 'active': step.active, 'error': step.error }"
                        >
                          <el-icon v-if="step.completed" class="step-icon"><CircleCheck /></el-icon>
                          <el-icon v-else-if="step.active" class="step-icon loading"><Loading /></el-icon>
                          <el-icon v-else-if="step.error" class="step-icon error"><CircleClose /></el-icon>
                          <el-icon v-else class="step-icon pending"><Clock /></el-icon>
                          <span class="step-text">{{ step.text }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-empty v-if="filteredModels.length === 0" description="暂无YOLO模型，请先训练YOLO模型" />
          </div>
        </el-tab-pane>

      </el-tabs>
    </div>

    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="400px"
    >
      <span>确定要删除模型 "{{ deletingModel?.name }}" 吗？此操作不可恢复。</span>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmDelete">确定删除</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="testsetSelectVisible"
      title="选择测试集"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="testsetTabActive">
        <el-tab-pane label="内部测试集" name="internal">
          <div class="testset-list" v-if="internalDatasets.length > 0">
            <el-alert
              title="提示"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            >
              <template #default>
                请选择包含测试集的内部数据集进行测试
              </template>
            </el-alert>
            <el-table :data="internalDatasets" style="width: 100%" @row-click="selectInternalTestset">
              <el-table-column prop="name" label="数据集名称" width="150" />
              <el-table-column label="训练集" width="80">
                <template #default="{ row }">
                  {{ row.train_images }}
                </template>
              </el-table-column>
              <el-table-column label="验证集" width="80">
                <template #default="{ row }">
                  {{ row.val_images || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="测试集" width="80">
                <template #default="{ row }">
                  {{ row.test_images || '-' }}
                </template>
              </el-table-column>
              <el-table-column label="YAML配置" width="90">
                <template #default="{ row }">
                  <el-tag :type="row.has_yaml ? 'success' : 'danger'" size="small">
                    {{ row.has_yaml ? '已配置' : '未配置' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="创建时间" width="160">
                <template #default="{ row }">
                  {{ new Date(row.created_at).toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="{ row }">
                  <el-button type="primary" size="small" @click.stop="selectInternalTestset(row)">
                    选择
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-else description="暂无内部数据集，请先在数据集管理页面创建并划分测试集" />
        </el-tab-pane>
        
        <el-tab-pane label="外部测试集" name="external">
          <div class="external-testset-section">
            <el-alert
              title="提示"
              type="info"
              :closable="false"
              style="margin-bottom: 20px"
            >
              <template #default>
                输入外部测试集目录的绝对路径，或点击按钮选择目录（目录结构应包含 images 和 labels 子目录）
              </template>
            </el-alert>
            <div class="select-external-section">
              <el-input 
                v-model="externalTestsetPath" 
                placeholder="请输入外部测试集目录的绝对路径，例如：D:\test_data"
                size="large"
                clearable
                style="flex: 1; margin-right: 10px"
              />
              <el-button type="primary" @click="selectExternalTestset" size="large">
                <el-icon><FolderOpened /></el-icon>
                选择目录
              </el-button>
            </div>
            <div style="margin-top: 15px">
              <el-button type="success" @click="confirmExternalTestset" size="large" :disabled="!externalTestsetPath">
                <el-icon><Check /></el-icon>
                确认选择
              </el-button>
            </div>
            <div v-if="selectedTestset && selectedTestset.type === 'external'" class="selected-info" style="margin-top: 15px">
              <el-tag type="success" size="large">
                已选择: {{ selectedTestset.path }}
              </el-tag>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      
      <template #footer>
        <el-button @click="testsetSelectVisible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Box, Calendar, DataLine, FolderOpened, VideoPlay, Delete, Refresh, CircleCheck, Loading, CircleClose, Clock, Check } from '@element-plus/icons-vue'
import { modelApi, yoloTestApi, type Model, type YoloEvaluateResponse, datasetApi } from '@/api'
import { useModelsStore } from '@/stores/models'

const modelsStore = useModelsStore()

const models = ref<Model[]>([])
const deleteDialogVisible = ref(false)
const deletingModel = ref<Model | null>(null)
const loading = ref(false)

const testsetSelectVisible = ref(false)
const testsetTabActive = ref('internal')

interface InternalDataset {
  name: string
  path: string
  train_images: number
  val_images: number
  test_images?: number
  has_yaml: boolean
  created_at: string
}

const internalDatasets = ref<InternalDataset[]>([])
const selectedTestset = ref<{ type: string; path: string; name?: string } | null>(null)
const externalTestsetPath = ref('')

const activeTab = computed({
  get: () => modelsStore.activeTab,
  set: (val) => modelsStore.setActiveTab(val)
})

const currentYoloModel = computed({
  get: () => modelsStore.currentYoloModel,
  set: (val) => modelsStore.setCurrentYoloModel(val)
})

const filteredModels = computed(() => {
  if (activeTab.value === 'all') {
    return models.value
  } else if (activeTab.value === 'yolo') {
    return models.value.filter(model => model.type === 'YOLO')
  }
  return models.value
})

const loadModels = async () => {
  loading.value = true
  try {
    const response = await modelApi.getModels()
    if (response.code === 200) {
      models.value = response.data
      await loadTestResults()
      await loadCurrentModels()
    } else {
      ElMessage.error(response.message || '加载模型列表失败')
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

const loadCurrentModels = async () => {
  try {
    const response = await modelApi.getCurrentModels()
    if (response.code === 200) {
      currentYoloModel.value = response.data.yolo_model
    }
  } catch (error) {
    console.error('获取当前模型失败:', error)
  }
}

const isCurrentModel = (model: Model): boolean => {
  if (model.type === 'YOLO') {
    const modelName = model.id.replace('yolo_', '')
    return currentYoloModel.value === modelName
  }
  return false
}

const setAsActiveModel = async (model: Model) => {
  try {
    const params: { yolo_model?: string } = {}

    if (model.type === 'YOLO') {
      const modelName = model.id.replace('yolo_', '')
      params.yolo_model = modelName
    }

    const response = await modelApi.switchModel(params)

    if (response.code === 200) {
      if (model.type === 'YOLO') {
        currentYoloModel.value = response.data.current_yolo_model || null
      }
      ElMessage.success(`已将 "${model.name}" 设置为当前使用的测试模型`)
    } else {
      ElMessage.error(response.message || '切换模型失败')
    }
  } catch (error) {
    console.error('切换模型失败:', error)
    ElMessage.error('切换模型失败')
  }
}

const loadTestResults = async () => {
  try {
    const response = await modelApi.getTestResults()
    if (response.code === 200) {
      const testResults = response.data
      models.value.forEach(model => {
        const result = testResults[model.id]
        if (result) {
          model.tested = true
          model.testProgress = 100
          model.testProgressText = '测试完成'
          model.testStatus = 'success'
          model.metrics = result.metrics
          model.testSteps = [
            { text: '初始化测试环境', completed: true, active: false, error: false },
            { text: '加载模型', completed: true, active: false, error: false },
            { text: '准备测试数据', completed: true, active: false, error: false },
            { text: '执行模型推理', completed: true, active: false, error: false },
            { text: '计算评估指标', completed: true, active: false, error: false },
            { text: '生成测试报告', completed: true, active: false, error: false }
          ]
        }
      })
    }
  } catch (error) {
    console.error('加载测试结果失败:', error)
  }
}

const refreshModels = async () => {
  try {
    const response = await modelApi.refreshModels()
    if (response.code === 200) {
      ElMessage.success(response.message)
      await loadModels()
    } else {
      ElMessage.error(response.message || '刷新模型列表失败')
    }
  } catch (error) {
    console.error('刷新模型列表失败:', error)
    ElMessage.error('刷新模型列表失败')
  }
}

const testYoloModel = async (model: Model, testPath: string) => {
  try {
    model.testProgress = 10
    model.testProgressText = '正在连接测试服务...'

    const isHealthy = await yoloTestApi.healthCheck()
    if (!isHealthy) {
      model.testing = false
      model.testStatus = 'exception'
      ElMessage.error('YOLO测试服务未启动，请先启动服务 (python test_yolo.py)')
      return
    }

    model.testProgress = 30
    model.testProgressText = '正在加载模型...'

    const loadResult = await yoloTestApi.loadModelByPath(model.path)
    if (loadResult.code !== 200) {
      model.testing = false
      model.testStatus = 'exception'
      ElMessage.error('加载模型失败')
      return
    }

    model.testProgress = 50
    model.testProgressText = '正在评估模型...'

    await yoloTestApi.evaluateStream(
      (message) => {
        model.testProgressText = message.trim()

        if (message.includes('images')) {
          model.testProgress = 70
        } else if (message.includes('mAP')) {
          model.testProgress = 90
        }
      },
      async (data: YoloEvaluateResponse) => {
        model.testProgress = 100
        model.testing = false
        model.tested = true
        model.testStatus = 'success'
        model.testProgressText = '测试完成'

        model.metrics = {
          accuracy: data.r2,
          precision: data.precision,
          recall: data.recall,
          f1Score: data.precision > 0 && data.recall > 0
            ? 2 * data.precision * data.recall / (data.precision + data.recall)
            : 0,
          r2: data.r2,
          map50: data.map50,
          map50_95: data.map50_95,
          errorRate: data.error_rate
        }

        model.testSteps = [
          { text: '连接测试服务', completed: true, active: false, error: false },
          { text: '加载模型', completed: true, active: false, error: false },
          { text: '评估模型', completed: true, active: false, error: false },
          { text: '计算指标', completed: true, active: false, error: false }
        ]

        await modelApi.saveTestResult(model.id, model.metrics)
        ElMessage.success(`模型 "${model.name}" 测试完成！`)
      },
      (error) => {
        model.testing = false
        model.testStatus = 'exception'
        model.testProgressText = '评估失败'
        ElMessage.error(error)
      },
      () => {
      },
      testPath
    )
  } catch (error) {
    console.error('YOLO模型测试失败:', error)
    model.testing = false
    model.testStatus = 'exception'
    ElMessage.error('YOLO模型测试失败')
  }
}

const deleteModel = (model: Model) => {
  deletingModel.value = model
  deleteDialogVisible.value = true
}

const confirmDelete = async () => {
  if (deletingModel.value) {
    try {
      const response = await modelApi.deleteModel(deletingModel.value.id)
      if (response.code === 200) {
        ElMessage.success(response.message)
        await loadModels()
      } else {
        ElMessage.error(response.message || '删除模型失败')
      }
    } catch (error) {
      console.error('删除模型失败:', error)
      ElMessage.error('删除模型失败')
    }
    deleteDialogVisible.value = false
    deletingModel.value = null
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const truncatePath = (path: string) => {
  if (path.length > 30) {
    return '...' + path.slice(-27)
  }
  return path
}

const currentTestingModel = ref<Model | null>(null)

const openTestsetSelectDialog = (model: Model) => {
  currentTestingModel.value = model
  testsetSelectVisible.value = true
  loadInternalDatasets()
}

const loadInternalDatasets = async () => {
  try {
    const result = await datasetApi.getDatasets()
    if (result.code === 200 && result.data) {
      internalDatasets.value = result.data
        .filter(d => d.testImageCount > 0)
        .map(d => ({
          name: d.name,
          path: `datasets/${d.id}`,
          train_images: d.trainImageCount || 0,
          val_images: d.validImageCount || 0,
          test_images: d.testImageCount || 0,
          has_yaml: d.hasYaml,
          created_at: d.createTime
        }))
    }
  } catch (e) {
    console.error('加载内部数据集失败:', e)
  }
}

const selectInternalTestset = async (dataset: InternalDataset) => {
  if (!currentTestingModel.value) return
  
  testsetSelectVisible.value = false
  
  const testPath = dataset.path
  selectedTestset.value = {
    type: 'internal',
    path: testPath,
    name: dataset.name
  }
  
  ElMessage.success(`已选择内部测试集: ${dataset.name}`)
  
  await startTesting(currentTestingModel.value, testPath)
}

const selectExternalTestset = () => {
  const input = document.createElement('input')
  input.type = 'file'
  ;(input as any).webkitdirectory = true
  input.style.display = 'none'
  
  input.onchange = async (event: Event) => {
    const target = event.target as HTMLInputElement
    if (target.files && target.files.length > 0) {
      const firstFile = target.files[0]
      const pathParts = firstFile.webkitRelativePath?.split('/')
      const folderName = pathParts && pathParts.length > 1 ? pathParts[0] : 'external'
      
      // 更新输入框中的路径为文件夹名称（相对路径）
      externalTestsetPath.value = folderName
      
      ElMessage.success(`已选择目录: ${folderName}，请点击"确认选择"按钮`)
    }
  }
  
  input.click()
}

const confirmExternalTestset = async () => {
  if (!currentTestingModel.value || !externalTestsetPath.value) return
  
  testsetSelectVisible.value = false
  
  selectedTestset.value = {
    type: 'external',
    path: externalTestsetPath.value,
    name: externalTestsetPath.value
  }
  
  ElMessage.success(`已选择外部测试集: ${externalTestsetPath.value}`)
  
  await startTesting(currentTestingModel.value!, externalTestsetPath.value)
}

const startTesting = async (model: Model, testPath: string) => {
  try {
    model.testing = true
    model.testProgress = 0
    model.testProgressText = '正在初始化测试环境...'
    model.testStatus = ''
    model.testSteps = []

    await testYoloModel(model, testPath)
  } catch (error) {
    console.error('测试模型失败:', error)
    model.testing = false
    model.testStatus = 'exception'
    ElMessage({
      message: '测试模型失败',
      type: 'error',
      duration: 3000
    })
  }
}

const testModel = (model: Model) => {
  openTestsetSelectDialog(model)
}

const safeMetricValue = (value: number | undefined, maxValue: number = 10000): number => {
  if (value === undefined || value === null || !isFinite(value) || value > maxValue) {
    return 0
  }
  return value
}

const getMetricClass = (value: number) => {
  if (value >= 0.95) return 'metric-excellent'
  if (value >= 0.9) return 'metric-good'
  if (value >= 0.8) return 'metric-average'
  return 'metric-poor'
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.model-manager {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
}

.page-title {
  font-size: 32px;
  font-weight: bold;
  margin: 0 0 10px 0;
  color: #409eff;
}

.page-description {
  font-size: 16px;
  margin: 0;
  color: #606266;
  position: relative;
}

.refresh-button {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
}

.model-tabs {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.tab-content {
  padding-top: 20px;
}

.model-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  background: white;
}

.model-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.2);
  border-color: #409eff;
}

.model-card.testing {
  border: 2px solid #409eff;
  background: #ecf5ff;
}

.model-card.tested {
  border: 1px solid #e4e7ed;
  background: white;
}

.model-card.is-current {
  border: 2px solid #67c23a;
  background: white;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-icon {
  font-size: 20px;
  color: #409eff;
}

.model-name {
  flex: 1;
  font-weight: bold;
  font-size: 16px;
}

.model-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.info-item .el-icon {
  color: #909399;
}

.model-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.model-actions .el-button {
  flex: 1;
  min-width: calc(50% - 4px);
}

.is-active-model {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%) !important;
  border-color: #67c23a !important;
  box-shadow: 0 2px 8px rgba(103, 194, 58, 0.4);
  font-weight: bold;
}

.is-active-model:hover {
  background: linear-gradient(135deg, #85ce61 0%, #67c23a 100%) !important;
  border-color: #85ce61 !important;
}

.metrics-section {
  margin-top: 15px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.metric-item {
  text-align: center;
  padding: 12px 8px;
  background: #f0f7ff;
  border-radius: 6px;
  border: 1px solid #d9ecff;
}

.metric-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.metric-excellent {
  color: #67c23a;
}

.metric-good {
  color: #409eff;
}

.metric-average {
  color: #e6a23c;
}

.metric-poor {
  color: #f56c6c;
}

.testing-progress {
  margin-top: 15px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.test-steps {
  margin-top: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.steps-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  background: white;
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.step-item.completed {
  background: #f0f9ff;
  border-color: #67c23a;
}

.step-item.active {
  background: #ecf5ff;
  border-color: #409eff;
  animation: pulse 1.5s infinite;
}

.step-item.error {
  background: #fef0f0;
  border-color: #f56c6c;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.step-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.step-icon.loading {
  color: #409eff;
  animation: spin 1s linear infinite;
}

.step-icon.error {
  color: #f56c6c;
}

.step-icon.pending {
  color: #909399;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.step-text {
  flex: 1;
  font-size: 13px;
  color: #606266;
}

.step-item.completed .step-text {
  color: #67c23a;
  font-weight: 500;
}

.step-item.error .step-text {
  color: #f56c6c;
}

/* 响应式 - 平板 */
@media (max-width: 992px) {
  .content-container :deep(.el-col) {
    margin-bottom: 16px;
  }
  
  .model-card {
    margin-bottom: 16px;
  }
}

/* 响应式 - 移动端 */
@media (max-width: 768px) {
  .model-manager {
    padding: 10px;
  }
  
  .page-header {
    margin-bottom: 20px;
    padding: 12px;
  }
  
  .page-title {
    font-size: 22px;
    line-height: 1.3;
  }
  
  .page-description {
    font-size: 13px;
  }
  
  .refresh-button {
    position: static;
    transform: none;
    margin-top: 12px;
  }
  
  .model-tabs {
    padding: 12px;
  }
  
  .tab-content {
    padding-top: 12px;
  }
  
  .model-card {
    margin-bottom: 12px;
  }
  
  .model-card:hover {
    transform: none;
  }
  
  .card-header {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .model-name {
    font-size: 14px;
    word-break: break-word;
  }
  
  .model-info {
    margin-bottom: 12px;
  }
  
  .info-item {
    font-size: 13px;
    margin-bottom: 6px;
    flex-wrap: wrap;
    word-break: break-word;
  }
  
  .model-actions {
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
  }
  
  .model-actions .el-button {
    width: 100%;
    min-width: auto;
    flex: none;
  }
  
  .metrics-section {
    margin-top: 12px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .metric-item {
    padding: 10px 6px;
  }
  
  .metric-label {
    font-size: 11px;
    margin-bottom: 4px;
  }
  
  .metric-value {
    font-size: 16px;
  }
  
  .testing-progress {
    margin-top: 12px;
  }
  
  .progress-text {
    font-size: 11px;
  }
  
  .test-steps {
    padding: 10px;
    margin-top: 12px;
  }
  
  .steps-title {
    font-size: 13px;
    margin-bottom: 10px;
  }
  
  .step-item {
    padding: 6px 10px;
    gap: 8px;
  }
  
  .step-text {
    font-size: 12px;
  }
  
  .step-icon {
    font-size: 14px;
  }
  
  .testset-list {
    max-height: 300px;
  }
  
  .external-testset-section {
    padding: 12px 0;
  }
  
  .select-external-section {
    padding: 20px 0;
    gap: 12px;
  }
}

/* 响应式 - 小屏幕手机 */
@media (max-width: 480px) {
  .model-manager {
    padding: 8px;
  }
  
  .page-header {
    padding: 10px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .page-description {
    font-size: 12px;
  }
  
  .model-tabs {
    padding: 10px;
  }
  
  .model-tabs :deep(.el-tabs__item) {
    font-size: 13px;
    padding: 0 8px;
  }
  
  .model-name {
    font-size: 13px;
  }
  
  .info-item {
    font-size: 12px;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
    gap: 6px;
  }
  
  .metric-item {
    padding: 8px 6px;
  }
  
  .metric-label {
    font-size: 10px;
  }
  
  .metric-value {
    font-size: 14px;
  }
  
  .step-text {
    font-size: 11px;
  }
}

.testset-list {
  max-height: 400px;
  overflow-y: auto;
}

.external-testset-section {
  padding: 20px 0;
}

.select-external-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 40px 0;
}

.selected-info {
  margin-top: 10px;
}
</style>
