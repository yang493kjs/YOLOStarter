<template>
  <div class="dataset-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>{{ datasetName }}</h2>
      </div>
      <div class="header-actions">
        <input
          ref="imageInputRef"
          type="file"
          accept="image/*"
          multiple
          style="display: none"
          @change="handleImageSelect"
        />
        <input
          ref="folderInputRef"
          type="file"
          webkitdirectory
          directory
          multiple
          style="display: none"
          @change="handleFolderSelect"
        />
        <input
          ref="labelInputRef"
          type="file"
          accept=".txt"
          multiple
          style="display: none"
          @change="handleLabelSelect"
        />
        <input
          ref="labelFolderInputRef"
          type="file"
          webkitdirectory
          directory
          multiple
          style="display: none"
          @change="handleLabelFolderSelect"
        />
        <input
          ref="yamlInputRef"
          type="file"
          accept=".yaml,.yml"
          style="display: none"
          @change="handleYamlSelect"
        />
        <el-dropdown @command="handleUploadCommand">
          <el-button type="primary">
            <el-icon><Upload /></el-icon>
            上传图片
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="files">
                <el-icon><Document /></el-icon>
                选择图片文件
              </el-dropdown-item>
              <el-dropdown-item command="folder">
                <el-icon><FolderOpened /></el-icon>
                选择文件夹
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-dropdown @command="handleLabelUploadCommand">
          <el-button type="success">
            <el-icon><Document /></el-icon>
            上传标签
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="files">
                <el-icon><Document /></el-icon>
                选择标签文件
              </el-dropdown-item>
              <el-dropdown-item command="folder">
                <el-icon><FolderOpened /></el-icon>
                选择文件夹
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="info" @click="showCreateYamlDialog = true">
          <el-icon><Edit /></el-icon>
          创建YAML
        </el-button>
        <el-button type="warning" @click="triggerYamlUpload">
          <el-icon><DocumentCopy /></el-icon>
          上传YAML
        </el-button>
        <el-button type="danger" @click="clearAllData">
          <el-icon><Delete /></el-icon>
          清空所有
        </el-button>
      </div>
    </div>
    
    <el-dialog
      v-model="showUploadProgress"
      title="正在上传图片"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="upload-progress-content">
        <el-progress 
          :percentage="uploadProgress" 
          :stroke-width="20"
          :text-inside="true"
          style="margin-bottom: 20px"
        />
        <div class="progress-text">
          正在上传: {{ uploadCurrent }} / {{ uploadTotal }} 张图片
        </div>
      </div>
    </el-dialog>
    
    <el-dialog
      v-model="showClearProgress"
      title="正在清空数据"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="upload-progress-content">
        <el-progress 
          :percentage="clearProgress" 
          :stroke-width="20"
          :text-inside="true"
          style="margin-bottom: 20px"
        />
        <div class="progress-text">
          {{ clearProgressText }}
        </div>
      </div>
    </el-dialog>
    
    <div class="content-container">
      <div class="left-section">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <el-icon><Picture /></el-icon>
              <span>图片文件 ({{ imageList.length }})</span>
              <div class="split-toggle">
                <el-radio-group v-model="currentSplit" size="small">
                  <el-radio-button label="train">训练集 ({{ trainImages.length }})</el-radio-button>
                  <el-radio-button label="valid">验证集 ({{ validImages.length }})</el-radio-button>
                  <el-radio-button label="test">测试集 ({{ testImages.length }})</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          
          <div class="file-list" v-loading="loadingImages">
            <div
              v-for="image in paginatedImages"
              :key="image.id"
              class="file-item"
              :class="{ 
                'train-item': currentSplit === 'train', 
                'valid-item': currentSplit === 'valid',
                'test-item': currentSplit === 'test' 
              }"
              @click="previewImage(image)"
            >
              <el-image
                :src="image.url"
                fit="cover"
                class="file-thumbnail"
                lazy
              />
              <div class="file-info">
                <div class="file-name">{{ image.name }}</div>
                <div class="file-size">{{ formatFileSize(image.size) }}</div>
              </div>
              <el-button
                type="danger"
                size="small"
                circle
                class="delete-btn"
                @click.stop="deleteImage(image)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            
            <el-empty v-if="currentDisplayImages.length === 0" :description="getEmptyText()" />
          </div>
          
          <div class="pagination-container" v-if="currentDisplayImages.length > pageSize">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="currentDisplayImages.length"
              layout="total, prev, pager, next"
              small
            />
          </div>
        </el-card>
      </div>
      
      <div class="right-section">
        <el-card class="section-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>标签文件 ({{ labelList.length }})</span>
              <div class="split-toggle">
                <el-radio-group v-model="currentSplit" size="small">
                  <el-radio-button label="train">训练集 ({{ trainLabels.length }})</el-radio-button>
                  <el-radio-button label="valid">验证集 ({{ validLabels.length }})</el-radio-button>
                  <el-radio-button label="test">测试集 ({{ testLabels.length }})</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          
          <div class="file-list" v-loading="loadingLabels">
            <div
              v-for="label in paginatedLabels"
              :key="label.id"
              class="file-item label-item"
              :class="{ 
                'train-item': currentSplit === 'train', 
                'valid-item': currentSplit === 'valid',
                'test-item': currentSplit === 'test' 
              }"
              @click="viewLabelContent(label)"
            >
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-info">
                <div class="file-name">{{ label.name }}</div>
                <div class="file-size">{{ formatFileSize(label.size) }}</div>
              </div>
              <el-button
                type="danger"
                size="small"
                circle
                class="delete-btn"
                @click.stop="deleteLabel(label.id)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            
            <el-empty v-if="currentDisplayLabels.length === 0" :description="getEmptyLabelText()" />
          </div>
          
          <div class="pagination-container" v-if="currentDisplayLabels.length > labelPageSize">
            <el-pagination
              v-model:current-page="labelCurrentPage"
              :page-size="labelPageSize"
              :total="currentDisplayLabels.length"
              layout="total, prev, pager, next"
            />
          </div>
        </el-card>
      </div>
    </div>
    
    <div class="split-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <el-icon><Operation /></el-icon>
            <span>自动划分数据集</span>
          </div>
        </template>
        
        <div class="auto-split-content">
          <div class="split-info">
            <el-tag type="primary">训练集 {{ trainImages.length }} 张</el-tag>
            <el-tag type="warning">验证集 {{ validImages.length }} 张</el-tag>
            <el-tag type="success">测试集 {{ testImages.length }} 张</el-tag>
          </div>
          
          <el-divider />
          
          <div class="split-options">
            <el-radio-group v-model="splitMode" size="large">
              <el-radio-button value="count">按数量划分</el-radio-button>
              <el-radio-button value="ratio">按比例划分</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="split-inputs">
            <template v-if="splitMode === 'count'">
              <div class="input-group">
                <span class="input-label">验证集数量：</span>
                <el-input-number 
                  v-model="validSetCount" 
                  :min="0" 
                  :max="imageList.length" 
                  :step="1"
                  size="large"
                  style="width: 150px"
                />
              </div>
              <div class="input-group">
                <span class="input-label">测试集数量：</span>
                <el-input-number 
                  v-model="testSetCount" 
                  :min="0" 
                  :max="imageList.length" 
                  :step="1"
                  size="large"
                  style="width: 150px"
                />
              </div>
            </template>
            <template v-else>
              <div class="input-group">
                <span class="input-label">验证集比例：</span>
                <el-slider 
                  v-model="validSetRatio" 
                  :min="0" 
                  :max="0.3" 
                  :step="0.05"
                  :format-tooltip="(val: number) => `${(val * 100).toFixed(0)}%`"
                  show-input
                  style="flex: 1; max-width: 250px"
                />
              </div>
              <div class="input-group">
                <span class="input-label">测试集比例：</span>
                <el-slider 
                  v-model="testSetRatio" 
                  :min="0" 
                  :max="0.3" 
                  :step="0.05"
                  :format-tooltip="(val: number) => `${(val * 100).toFixed(0)}%`"
                  show-input
                  style="flex: 1; max-width: 250px"
                />
              </div>
            </template>
          </div>
          
          <el-alert
            title="划分说明"
            type="info"
            :closable="false"
            style="margin-top: 12px"
          >
            <template #default>
              先将所有图片归入训练集，然后按顺序划分出验证集和测试集。验证集用于训练过程中调参，测试集用于最终评估。
            </template>
          </el-alert>
          
          <div class="split-actions">
            <el-button type="primary" @click="autoSplitDataset" size="large">
              <el-icon><Refresh /></el-icon>
              自动划分
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
    
    <div class="yaml-section">
      <el-card class="yaml-card">
        <template #header>
          <div class="card-header">
            <el-icon><DocumentCopy /></el-icon>
            <span>YAML文件信息</span>
          </div>
        </template>
        
        <el-alert
          type="warning"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <template #title>
            <strong>YAML配置文件说明</strong>
          </template>
          <div style="margin-top: 8px; line-height: 1.8;">
            <p style="margin: 4px 0;"><strong>path</strong>：必须使用绝对路径（如 D:/yuyan/Visual/datasets/your_dataset）</p>
            <p style="margin: 4px 0;"><strong>train/val/test</strong>：相对于path的图片目录路径</p>
            <p style="margin: 4px 0;"><strong>names</strong>：类别名称列表，支持中文</p>
            <p style="margin: 4px 0; color: #f56c6c;">⚠️ 路径配置错误会导致训练失败！</p>
          </div>
        </el-alert>
        
        <div class="yaml-info" v-if="yamlData">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="类别数量">
              <el-tag type="primary" size="large">{{ yamlData.classCount }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="类别列表">
              <div class="class-list">
                <el-tag
                  v-for="(className, index) in yamlData.classes"
                  :key="index"
                  style="margin: 4px"
                >
                  {{ className }}
                </el-tag>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="文件名">
              {{ yamlData.fileName }}
            </el-descriptions-item>
            <el-descriptions-item label="数据路径" v-if="yamlData.path">
              <el-tag type="info" size="small">{{ yamlData.path }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="训练集路径" v-if="yamlData.train">
              <el-tag type="success" size="small">{{ yamlData.train }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="验证集路径" v-if="yamlData.val">
              <el-tag type="warning" size="small">{{ yamlData.val }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="测试集路径" v-if="yamlData.test">
              <el-tag type="danger" size="small">{{ yamlData.test }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-button
            type="danger"
            size="small"
            style="margin-top: 16px"
            @click="clearYaml"
          >
            清除YAML文件
          </el-button>
        </div>
        
        <el-empty v-else description="暂无YAML文件" />
      </el-card>
    </div>
    
    <el-dialog
      v-model="previewDialogVisible"
      title="图片预览"
      width="800px"
    >
      <el-image
        :src="previewImageUrl"
        fit="contain"
        style="width: 100%; max-height: 600px"
      />
    </el-dialog>
    
    <el-dialog
      v-model="labelDialogVisible"
      title="标签文件内容"
      width="600px"
    >
      <pre class="label-content">{{ labelDialogContent }}</pre>
    </el-dialog>
    
    <el-dialog
      v-model="showCreateYamlDialog"
      title="创建YAML文件"
      width="500px"
    >
      <el-form :model="yamlForm" label-width="100px">
        <el-form-item label="类别数量">
          <el-input-number
            v-model="yamlForm.classCount"
            :min="1"
            :max="100"
            size="large"
            style="width: 100%"
            @change="updateClassInputs"
          />
        </el-form-item>
        <el-form-item label="类别名称">
          <div class="class-inputs">
            <el-input
              v-for="(className, index) in yamlForm.classes"
              :key="index"
              v-model="yamlForm.classes[index]"
              :placeholder="`类别 ${index + 1}`"
              style="margin-bottom: 8px"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateYamlDialog = false">取消</el-button>
        <el-button type="primary" @click="createYaml" :disabled="!validateYamlForm()">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload,
  Document,
  DocumentCopy,
  Delete,
  Picture,
  Close,
  ArrowLeft,
  Operation,
  Refresh,
  Edit,
  FolderOpened,
  ArrowDown,
} from '@element-plus/icons-vue'
import yaml from 'js-yaml'
import { datasetApi } from '@/api'

interface ImageItem {
  id: string
  name: string
  url: string
  size: number
  split: 'train' | 'test'
}

interface LabelItem {
  id: string
  name: string
  size: number
  split: 'train' | 'test'
}

interface YamlData {
  fileName: string
  classCount: number
  classes: string[]
  path: string
  train: string
  val: string
  test: string
}

const route = useRoute()
const router = useRouter()

const datasetId = computed(() => route.params.id as string)
const datasetName = ref('数据集详情')

const imageInputRef = ref<HTMLInputElement>()
const folderInputRef = ref<HTMLInputElement>()
const labelInputRef = ref<HTMLInputElement>()
const labelFolderInputRef = ref<HTMLInputElement>()
const yamlInputRef = ref<HTMLInputElement>()

const loadingImages = ref(false)
const loadingLabels = ref(false)

const uploadProgress = ref(0)
const uploadTotal = ref(0)
const uploadCurrent = ref(0)
const showUploadProgress = ref(false)

const imageList = ref<ImageItem[]>([])
const labelList = ref<LabelItem[]>([])
const yamlData = ref<YamlData | null>(null)

const currentSplit = ref<'train' | 'valid' | 'test'>('train')

const currentPage = ref(1)
const pageSize = ref(20)
const labelCurrentPage = ref(1)
const labelPageSize = ref(20)

watch(currentSplit, () => {
  currentPage.value = 1
  labelCurrentPage.value = 1
})

const splitMode = ref<'count' | 'ratio'>('ratio')
const validSetCount = ref(10)
const testSetCount = ref(10)
const validSetRatio = ref(0.1)
const testSetRatio = ref(0.1)

const previewDialogVisible = ref(false)
const previewImageUrl = ref('')

const labelDialogVisible = ref(false)
const labelDialogContent = ref('')

const showCreateYamlDialog = ref(false)
const yamlForm = ref({
  classCount: 1,
  classes: ['']
})

const trainImages = computed(() => {
  return imageList.value.filter(img => img.split === 'train')
})

const validImages = computed(() => {
  return imageList.value.filter(img => img.split === 'valid')
})

const testImages = computed(() => {
  return imageList.value.filter(img => img.split === 'test')
})

const trainLabels = computed(() => {
  return labelList.value.filter(label => label.split === 'train')
})

const validLabels = computed(() => {
  return labelList.value.filter(label => label.split === 'valid')
})

const testLabels = computed(() => {
  return labelList.value.filter(label => label.split === 'test')
})

const currentDisplayImages = computed(() => {
  let list = trainImages.value
  if (currentSplit.value === 'valid') {
    list = validImages.value
  } else if (currentSplit.value === 'test') {
    list = testImages.value
  }
  return [...list].sort((a, b) => a.name.localeCompare(b.name))
})

const currentDisplayLabels = computed(() => {
  let list = trainLabels.value
  if (currentSplit.value === 'valid') {
    list = validLabels.value
  } else if (currentSplit.value === 'test') {
    list = testLabels.value
  }
  return [...list].sort((a, b) => a.name.localeCompare(b.name))
})

const paginatedImages = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return currentDisplayImages.value.slice(start, end)
})

const paginatedLabels = computed(() => {
  const start = (labelCurrentPage.value - 1) * labelPageSize.value
  const end = start + labelPageSize.value
  return currentDisplayLabels.value.slice(start, end)
})

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const getEmptyText = () => {
  if (currentSplit.value === 'train') return '暂无训练集图片'
  if (currentSplit.value === 'valid') return '暂无验证集图片'
  return '暂无测试集图片'
}

const getEmptyLabelText = () => {
  if (currentSplit.value === 'train') return '暂无训练集标签'
  if (currentSplit.value === 'valid') return '暂无验证集标签'
  return '暂无测试集标签'
}

const goBack = () => {
  router.push('/dataset')
}

const handleUploadCommand = (command: string) => {
  if (command === 'files') {
    imageInputRef.value?.click()
  } else if (command === 'folder') {
    folderInputRef.value?.click()
  }
}

const triggerLabelUpload = () => {
  labelInputRef.value?.click()
}

const handleLabelUploadCommand = (command: string) => {
  if (command === 'files') {
    labelInputRef.value?.click()
  } else if (command === 'folder') {
    labelFolderInputRef.value?.click()
  }
}

const triggerYamlUpload = () => {
  yamlInputRef.value?.click()
}

// 提取文件名，去除路径部分
const getFileName = (filePath: string): string => {
  return filePath.split('/').pop() || filePath.split('\\').pop() || filePath
}

const isImageFile = (filename: string): boolean => {
  const ext = getFileName(filename).toLowerCase().split('.').pop()
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif'].includes(ext || '')
}

const isLabelFile = (filename: string): boolean => {
  const ext = getFileName(filename).toLowerCase().split('.').pop()
  return ext === 'txt'
}

const handleFolderSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files || files.length === 0) return
  
  const id = datasetId.value
  if (!id) {
    ElMessage.error('数据集ID不存在')
    return
  }
  
  const imageFiles = Array.from(files).filter(file => isImageFile(file.name))
  
  if (imageFiles.length === 0) {
    ElMessage.warning('所选文件夹中没有找到图片文件')
    target.value = ''
    return
  }
  
  const totalFiles = imageFiles.length
  uploadTotal.value = totalFiles
  uploadCurrent.value = 0
  uploadProgress.value = 0
  showUploadProgress.value = true
  loadingImages.value = true
  
  const batchSize = 5
  let successCount = 0
  
  try {
    for (let i = 0; i < imageFiles.length; i += batchSize) {
      const batch = imageFiles.slice(i, i + batchSize)
      
      const batchPromises = batch.map(async (file) => {
        try {
          // 创建一个新的File对象，使用提取的文件名
          const fileName = getFileName(file.name)
          const newFile = new File([file], fileName, { type: file.type })
          const result = await datasetApi.uploadImage(id, newFile, currentSplit.value)
          if (result.code === 200) {
            return result.data
          }
          return null
        } catch (error) {
          console.error('上传文件失败:', file.name, error)
          return null
        }
      })
      
      const batchResults = await Promise.all(batchPromises)
      const validResults = batchResults.filter(result => result !== null) as ImageItem[]
      
      for (const img of validResults) {
        img.url = datasetApi.getImageUrl(id, img.name)
      }
      
      imageList.value = [...imageList.value, ...validResults]
      successCount += validResults.length
      
      uploadCurrent.value = successCount
      uploadProgress.value = Math.round((successCount / totalFiles) * 100)
    }
    
    if (successCount === totalFiles) {
      ElMessage.success(`成功上传 ${totalFiles} 张图片`)
    } else if (successCount > 0) {
      ElMessage.warning(`成功上传 ${successCount} 张图片，${totalFiles - successCount} 张失败`)
    } else {
      ElMessage.error('所有图片上传失败')
    }
  } catch (error) {
    console.error('上传过程出错:', error)
    ElMessage.error('图片上传过程中发生错误')
  } finally {
    loadingImages.value = false
    showUploadProgress.value = false
    target.value = ''
  }
}

const handleImageSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files || files.length === 0) return
  
  const id = datasetId.value
  if (!id) {
    ElMessage.error('数据集ID不存在')
    return
  }
  
  const totalFiles = files.length
  uploadTotal.value = totalFiles
  uploadCurrent.value = 0
  uploadProgress.value = 0
  showUploadProgress.value = true
  loadingImages.value = true
  
  const batchSize = 5
  const fileArray = Array.from(files)
  let successCount = 0
  
  try {
    for (let i = 0; i < fileArray.length; i += batchSize) {
      const batch = fileArray.slice(i, i + batchSize)
      
      const batchPromises = batch.map(async (file) => {
        try {
          const result = await datasetApi.uploadImage(id, file, currentSplit.value)
          if (result.code === 200) {
            return result.data
          }
          return null
        } catch (error) {
          console.error('上传文件失败:', file.name, error)
          return null
        }
      })
      
      const batchResults = await Promise.all(batchPromises)
      const validResults = batchResults.filter(result => result !== null) as ImageItem[]
      
      for (const img of validResults) {
        img.url = datasetApi.getImageUrl(id, img.name)
      }
      
      imageList.value = [...imageList.value, ...validResults]
      successCount += validResults.length
      
      uploadCurrent.value = successCount
      uploadProgress.value = Math.round((successCount / totalFiles) * 100)
    }
    
    if (successCount === totalFiles) {
      ElMessage.success(`成功上传 ${totalFiles} 张图片`)
    } else if (successCount > 0) {
      ElMessage.warning(`成功上传 ${successCount} 张图片，${totalFiles - successCount} 张失败`)
    } else {
      ElMessage.error('所有图片上传失败')
    }
  } catch (error) {
    console.error('上传过程出错:', error)
    ElMessage.error('图片上传过程中发生错误')
  } finally {
    loadingImages.value = false
    showUploadProgress.value = false
    target.value = ''
  }
}

const handleLabelSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files || files.length === 0) return
  
  const id = datasetId.value
  if (!id) {
    ElMessage.error('数据集ID不存在')
    return
  }
  
  loadingLabels.value = true
  
  try {
    let successCount = 0
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      
      try {
        const result = await datasetApi.uploadLabel(id, file, currentSplit.value)
        if (result.code === 200) {
          labelList.value.push(result.data)
          successCount++
        }
      } catch (error) {
        console.error('上传标签文件失败:', file.name, error)
      }
    }
    
    if (successCount === files.length) {
      ElMessage.success(`成功上传 ${successCount} 个标签文件`)
    } else if (successCount > 0) {
      ElMessage.warning(`成功上传 ${successCount} 个标签文件，${files.length - successCount} 个失败`)
    } else {
      ElMessage.error('所有标签文件上传失败')
    }
  } catch (error) {
    console.error('上传过程出错:', error)
    ElMessage.error('标签文件上传过程中发生错误')
  } finally {
    loadingLabels.value = false
    target.value = ''
  }
}

const handleLabelFolderSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files || files.length === 0) return
  
  const id = datasetId.value
  if (!id) {
    ElMessage.error('数据集ID不存在')
    return
  }
  
  const labelFiles = Array.from(files).filter(file => isLabelFile(file.name))
  
  if (labelFiles.length === 0) {
    ElMessage.warning('所选文件夹中没有找到标签文件(.txt)')
    target.value = ''
    return
  }
  
  loadingLabels.value = true
  
  try {
    let successCount = 0
    
    for (let i = 0; i < labelFiles.length; i++) {
      const file = labelFiles[i]
      
      try {
        // 创建一个新的File对象，使用提取的文件名
        const fileName = getFileName(file.name)
        const newFile = new File([file], fileName, { type: file.type })
        const result = await datasetApi.uploadLabel(id, newFile, currentSplit.value)
        if (result.code === 200) {
          labelList.value.push(result.data)
          successCount++
        }
      } catch (error) {
        console.error('上传标签文件失败:', file.name, error)
      }
    }
    
    if (successCount === labelFiles.length) {
      ElMessage.success(`成功上传 ${successCount} 个标签文件`)
    } else if (successCount > 0) {
      ElMessage.warning(`成功上传 ${successCount} 个标签文件，${labelFiles.length - successCount} 个失败`)
    } else {
      ElMessage.error('所有标签文件上传失败')
    }
  } catch (error) {
    console.error('上传过程出错:', error)
    ElMessage.error('标签文件上传过程中发生错误')
  } finally {
    loadingLabels.value = false
    target.value = ''
  }
}

const handleYamlSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  const id = datasetId.value
  if (!id) {
    ElMessage.error('数据集ID不存在')
    return
  }
  
  try {
    const result = await datasetApi.uploadYaml(id, file)
    
    if (result.code === 200) {
      yamlData.value = result.data
      ElMessage.success('YAML文件解析成功')
    } else {
      ElMessage.error(result.message || 'YAML文件解析失败')
    }
  } catch (error) {
    console.error('YAML解析错误:', error)
    ElMessage.error('YAML文件解析失败')
  } finally {
    target.value = ''
  }
}

const previewImage = (image: ImageItem) => {
  previewImageUrl.value = image.url
  previewDialogVisible.value = true
}

const viewLabelContent = async (label: LabelItem) => {
  try {
    const result = await datasetApi.getLabelContent(datasetId.value, label.name)
    if (result.code === 200) {
      labelDialogContent.value = result.data.content
      labelDialogVisible.value = true
    }
  } catch (error) {
    console.error('获取标签内容失败:', error)
  }
}

const deleteImage = (image: ImageItem) => {
  ElMessageBox.confirm('确定要删除这张图片吗？', '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const result = await datasetApi.deleteImage(datasetId.value, image.name)
      if (result.code === 200) {
        imageList.value = imageList.value.filter(img => img.id !== image.id)
        ElMessage.success('删除成功')
      }
    } catch (error) {
      console.error('删除图片失败:', error)
    }
  }).catch(() => {})
}

const deleteLabel = (label: LabelItem) => {
  ElMessageBox.confirm('确定要删除这个标签文件吗？', '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const result = await datasetApi.deleteLabel(datasetId.value, label.name)
      if (result.code === 200) {
        labelList.value = labelList.value.filter(l => l.id !== label.id)
        ElMessage.success('删除成功')
      }
    } catch (error) {
      console.error('删除标签失败:', error)
    }
  }).catch(() => {})
}

const autoSplitDataset = async () => {
  if (imageList.value.length === 0) {
    ElMessage.warning('没有图片数据可划分')
    return
  }

  try {
    const result = await datasetApi.autoSplit(datasetId.value, {
      mode: splitMode.value,
      validRatio: validSetRatio.value,
      validCount: validSetCount.value,
      testRatio: testSetRatio.value,
      testCount: testSetCount.value
    })
    
    if (result.code === 200) {
      ElMessage.success(result.message)
      await loadDataset()
    } else {
      ElMessage.error(result.message || '划分失败')
    }
  } catch (error) {
    console.error('自动划分失败:', error)
    ElMessage.error('自动划分失败')
  }
}

const clearYaml = async () => {
  try {
    const result = await datasetApi.deleteYaml(datasetId.value)
    if (result.code === 200) {
      yamlData.value = null
      ElMessage.success('YAML文件已清除')
    }
  } catch (error) {
    console.error('清除YAML失败:', error)
  }
}

// 清空数据进度条
const showClearProgress = ref(false)
const clearProgress = ref(0)
const clearProgressText = ref('')

const clearAllData = () => {
  ElMessageBox.confirm('确定要清空所有数据吗？此操作不可恢复！', '确认清空', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      // 保存当前数据的副本
      const imagesToDelete = [...imageList.value]
      const labelsToDelete = [...labelList.value]
      const hasYaml = yamlData.value
      const totalItems = imagesToDelete.length + labelsToDelete.length + (hasYaml ? 1 : 0)
      
      if (totalItems > 0) {
        // 显示进度条
        showClearProgress.value = true
        clearProgress.value = 0
        clearProgressText.value = '准备开始清空数据...'
      }
      
      let completedItems = 0
      const updateProgress = (step = 1) => {
        completedItems += step
        clearProgress.value = Math.round((completedItems / totalItems) * 100)
        clearProgressText.value = `正在清空数据... ${completedItems}/${totalItems}`
      }
      
      // 清空前端状态
      imageList.value = []
      labelList.value = []
      yamlData.value = null
      
      // 并行删除图片
      const imagePromises = imagesToDelete.map(async (img) => {
        try {
          await datasetApi.deleteImage(datasetId.value, img.name)
          updateProgress()
        } catch (error) {
          console.error('删除图片失败:', img.name, error)
          updateProgress()
        }
      })
      
      // 并行删除标签
      const labelPromises = labelsToDelete.map(async (label) => {
        try {
          await datasetApi.deleteLabel(datasetId.value, label.name)
          updateProgress()
        } catch (error) {
          console.error('删除标签失败:', label.name, error)
          updateProgress()
        }
      })
      
      // 执行删除操作
      await Promise.all([...imagePromises, ...labelPromises])
      
      // 删除YAML文件
      if (hasYaml) {
        try {
          await datasetApi.deleteYaml(datasetId.value)
          updateProgress()
        } catch (error) {
          console.error('删除YAML失败:', error)
          updateProgress()
        }
      }
      
      // 关闭进度条
      showClearProgress.value = false
      ElMessage.success('所有数据已清空')
    } catch (error) {
      console.error('清空数据失败:', error)
      showClearProgress.value = false
      ElMessage.error('清空数据时发生错误')
      // 重新加载数据集以更新状态
      await loadDataset()
    }
  }).catch(() => {})
}

const loadDataset = async () => {
  const id = datasetId.value
  if (!id) return
  
  try {
    console.log('开始加载数据集:', id)
    const result = await datasetApi.getDataset(id)
    console.log('API响应:', result)
    
    if (result.code === 200) {
      const data = result.data
      datasetName.value = data.name
      
      if (data.images && Array.isArray(data.images)) {
        imageList.value = data.images.map((img: any) => ({
          ...img,
          url: datasetApi.getImageUrl(id, img.name)
        }))
      } else {
        imageList.value = []
        console.warn('数据集没有图片数据')
      }
      
      if (data.labels && Array.isArray(data.labels)) {
        labelList.value = data.labels
      } else {
        labelList.value = []
        console.warn('数据集没有标签数据')
      }
      
      yamlData.value = data.yamlData
      
      console.log(`数据集加载完成: ${data.name}`)
      console.log(`- 图片: ${imageList.value.length} 张`)
      console.log(`- 标签: ${labelList.value.length} 个`)
    } else {
      console.error('API返回错误:', result.message)
      ElMessage.error(`加载数据集失败: ${result.message || '未知错误'}`)
    }
  } catch (error) {
    console.error('加载数据集失败:', error)
    ElMessage.error('网络错误，请检查后端服务是否运行')
  }
}

const updateClassInputs = () => {
  const currentCount = yamlForm.value.classes.length
  const targetCount = yamlForm.value.classCount
  
  if (targetCount > currentCount) {
    for (let i = currentCount; i < targetCount; i++) {
      yamlForm.value.classes.push('')
    }
  } else if (targetCount < currentCount) {
    yamlForm.value.classes = yamlForm.value.classes.slice(0, targetCount)
  }
}

const validateYamlForm = () => {
  if (yamlForm.value.classCount < 1) return false
  return yamlForm.value.classes.every(className => className.trim() !== '')
}

const createYaml = async () => {
  if (!validateYamlForm()) {
    ElMessage.warning('请填写所有类别名称')
    return
  }
  
  const id = datasetId.value
  if (!id) {
    ElMessage.error('数据集ID不存在')
    return
  }
  
  try {
    const yamlContent = {
      path: '.',
      train: 'train/images',
      val: 'valid/images',
      test: 'test/images',
      nc: yamlForm.value.classCount,
      names: yamlForm.value.classes
    }
    
    const content = yaml.dump(yamlContent)
    
    const result = await datasetApi.uploadYamlContent(id, content)
    
    if (result.code === 200) {
      yamlData.value = result.data
      showCreateYamlDialog.value = false
      ElMessage.success('YAML文件创建成功')
    } else {
      ElMessage.error(result.message || 'YAML文件创建失败')
    }
  } catch (error) {
    console.error('YAML创建错误:', error)
    ElMessage.error('YAML文件创建失败')
  }
}

onMounted(() => {
  loadDataset()
})
</script>

<style scoped>
.dataset-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.back-btn {
  margin-right: 8px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.content-container {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 400px;
  max-height: 500px;
}

.left-section {
  flex: 1;
  min-width: 0;
}

.right-section {
  width: 400px;
}

.yaml-section {
  flex-shrink: 0;
  margin-top: 20px;
}

.yaml-card {
  width: 100%;
}

.section-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  max-height: 400px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 6px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.file-item:hover {
  background: #ecf5ff;
  transform: translateX(4px);
}

.file-thumbnail {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  flex-shrink: 0;
}

.file-icon {
  font-size: 36px;
  color: #409eff;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  margin-left: 10px;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.file-item:hover .delete-btn {
  opacity: 1;
}

.label-item {
  background: #fdf6ec;
}

.label-item:hover {
  background: #faecd8;
}

.yaml-info {
  padding: 8px;
}

.class-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.label-content {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.progress-text {
  text-align: center;
  color: #606266;
  font-size: 14px;
  margin-top: 10px;
}

.split-toggle {
  margin-left: auto;
}

.split-section {
  margin-top: 20px;
}

.auto-split-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.split-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.split-options {
  display: flex;
  justify-content: center;
}

.split-inputs {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
}

.split-actions {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.train-item {
  border-left: 3px solid #409eff;
}

.valid-item {
  border-left: 3px solid #e6a23c;
}

.test-item {
  border-left: 3px solid #67c23a;
}

.class-inputs {
  width: 100%;
}

/* 响应式 - 平板 */
@media (max-width: 992px) {
  .content-container {
    flex-direction: column;
    min-height: auto;
    max-height: none;
  }
  
  .left-section {
    width: 100%;
    min-height: 300px;
  }
  
  .right-section {
    width: 100%;
  }
}

/* 响应式 - 移动端 */
@media (max-width: 768px) {
  .dataset-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
  }
  
  .header-left {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .header-left h2 {
    font-size: 16px;
    word-break: break-word;
  }
  
  .back-btn {
    margin-right: 6px;
    padding: 6px 10px;
    font-size: 13px;
  }
  
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .header-actions .el-button {
    flex: 1 1 calc(50% - 4px);
    min-width: 0;
    padding: 8px 10px;
    font-size: 13px;
  }
  
  .content-container {
    flex-direction: column;
    min-height: auto;
    max-height: none;
    gap: 12px;
  }
  
  .left-section {
    width: 100%;
    min-height: 250px;
  }
  
  .right-section {
    width: 100%;
  }
  
  .section-card {
    margin-bottom: 0;
  }
  
  .card-header {
    flex-wrap: wrap;
    font-size: 14px;
    gap: 8px;
  }
  
  .split-toggle {
    width: 100%;
    margin-left: 0;
    margin-top: 8px;
  }
  
  .split-toggle :deep(.el-radio-button__inner) {
    padding: 6px 8px;
    font-size: 12px;
  }
  
  .file-list {
    padding: 6px;
    max-height: 250px;
  }
  
  .file-item {
    padding: 10px;
    margin-bottom: 6px;
  }
  
  .file-thumbnail {
    width: 48px;
    height: 48px;
  }
  
  .file-icon {
    font-size: 36px;
  }
  
  .file-info {
    margin-left: 10px;
  }
  
  .file-name {
    font-size: 13px;
  }
  
  .file-size {
    font-size: 11px;
  }
  
  .delete-btn {
    opacity: 1;
    right: 6px;
  }
  
  .pagination-container {
    margin-top: 10px;
  }
  
  .pagination-container :deep(.el-pagination) {
    justify-content: center;
  }
  
  .split-section {
    margin-top: 12px;
  }
  
  .auto-split-content {
    gap: 12px;
  }
  
  .split-info {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .split-options {
    width: 100%;
  }
  
  .split-options :deep(.el-radio-button__inner) {
    padding: 8px 12px;
    font-size: 13px;
  }
  
  .split-inputs {
    flex-direction: column;
    gap: 12px;
    padding: 8px 0;
  }
  
  .input-group {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .input-label {
    font-size: 13px;
  }
  
  .input-group :deep(.el-input-number) {
    width: 100% !important;
  }
  
  .input-group :deep(.el-slider) {
    width: 100% !important;
    max-width: 100% !important;
  }
  
  .split-actions {
    padding-top: 6px;
  }
  
  .split-actions .el-button {
    width: 100%;
  }
  
  .yaml-section {
    margin-top: 12px;
  }
  
  .yaml-info {
    padding: 6px;
  }
  
  .yaml-info :deep(.el-descriptions__label) {
    font-size: 13px;
  }
  
  .yaml-info :deep(.el-descriptions__content) {
    font-size: 13px;
  }
  
  .class-list {
    gap: 4px;
  }
  
  .class-list .el-tag {
    font-size: 12px;
    margin: 2px;
  }
  
  .label-content {
    padding: 12px;
    font-size: 12px;
    line-height: 1.5;
  }
  
  .progress-text {
    font-size: 13px;
  }
}

/* 响应式 - 小屏幕手机 */
@media (max-width: 480px) {
  .dataset-page {
    padding: 8px;
  }
  
  .page-header {
    padding: 10px 12px;
  }
  
  .header-left h2 {
    font-size: 14px;
  }
  
  .header-actions .el-button {
    flex: 1 1 100%;
    padding: 6px 8px;
    font-size: 12px;
  }
  
  .file-list {
    max-height: 200px;
    padding: 4px;
  }
  
  .file-item {
    padding: 8px;
  }
  
  .file-thumbnail {
    width: 40px;
    height: 40px;
  }
  
  .file-icon {
    font-size: 28px;
  }
  
  .file-name {
    font-size: 12px;
  }
  
  .card-header {
    font-size: 13px;
  }
  
  .split-toggle :deep(.el-radio-button__inner) {
    padding: 4px 6px;
    font-size: 11px;
  }
  
  .input-label {
    font-size: 12px;
  }
  
  .yaml-info :deep(.el-descriptions__label),
  .yaml-info :deep(.el-descriptions__content) {
    font-size: 12px;
  }
  
  .label-content {
    font-size: 11px;
    padding: 10px;
  }
}
</style>
