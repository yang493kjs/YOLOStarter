<template>
  <div class="detection-page">
    <div class="page-header">
      <h1 class="page-title">YOLO目标检测</h1>
      <p class="page-description">通过YOLO模型实时检测图像中的目标</p>
      <div class="current-models">
        <el-tag v-if="currentYoloModel" type="primary" size="small">
          YOLO模型: {{ currentYoloModel }}
        </el-tag>
      </div>
    </div>

    <div class="content-container">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="14">
          <el-card class="main-card">
            <template #header>
              <div class="card-header">
                <span>图像输入</span>
                <div class="header-actions">
                  <el-dropdown v-if="cameras.length > 1" trigger="click">
                    <el-button type="primary" size="small">
                      <el-icon><Camera /></el-icon>
                      选择摄像头
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item 
                          v-for="(camera, index) in cameras" 
                          :key="index"
                          @click="selectCamera(index)"
                        >
                          {{ camera.label || `摄像头 ${index + 1}` }}
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                  <el-button v-else type="primary" size="small" @click="startCamera">
                    <el-icon><Camera /></el-icon>
                    开启摄像头
                  </el-button>
                  <el-button 
                    v-if="cameraActive" 
                    type="success" 
                    size="small" 
                    @click="capturePhoto"
                  >
                    <el-icon><CameraFilled /></el-icon>
                    拍照 (Enter)
                  </el-button>
                  <el-button 
                    v-if="cameraActive" 
                    type="danger" 
                    size="small" 
                    @click="stopCamera"
                  >
                    <el-icon><SwitchButton /></el-icon>
                    关闭摄像头
                  </el-button>
                  <el-button 
                    v-if="!cameraActive && images.length > 0" 
                    type="success" 
                    size="small" 
                    @click="predict"
                    :loading="detecting"
                  >
                    <el-icon><DataAnalysis /></el-icon>
                    开始预测
                  </el-button>
                  <el-upload
                    ref="uploadRef"
                    :auto-upload="false"
                    :show-file-list="false"
                    accept="image/*"
                    multiple
                    webkitdirectory
                    :on-change="handleFileChange"
                  >
                    <el-button type="info" size="small">
                      <el-icon><FolderOpened /></el-icon>
                      导入文件夹
                    </el-button>
                  </el-upload>
                </div>
              </div>
            </template>

            <div class="image-section">
              <canvas ref="canvasRef" style="display: none;"></canvas>
              
              <div class="camera-container" v-if="cameraActive">
                <video 
                  ref="videoRef" 
                  autoplay
                  playsinline
                  muted
                  class="camera-video"
                  :class="{ 'video-ready': videoReady }"
                  @loadedmetadata="onVideoLoaded"
                  @play="onVideoPlay"
                  @error="onVideoError"
                  @canplay="onVideoCanPlay"
                  @waiting="onVideoWaiting"
                ></video>
                <div class="camera-overlay" v-if="!videoReady">
                  <el-icon class="loading-icon"><Loading /></el-icon>
                  <div class="status-text">正在加载摄像头画面...</div>
                </div>
              </div>

              <div class="image-preview" v-else-if="selectedImage">
                <img :src="selectedImage" alt="预览图像" />
              </div>

              <div class="empty-state" v-else>
                <el-icon class="empty-icon"><Picture /></el-icon>
                <div class="empty-text">请导入图片或开启摄像头</div>
              </div>
            </div>

            <div class="image-list" v-if="images.length > 0">
              <div class="list-header">
                <span>已导入图片 ({{ images.length }})</span>
                <div class="list-actions">
                  <span v-if="isProcessingFiles" class="processing-hint">
                    <el-icon class="loading-icon-small"><Loading /></el-icon>
                    处理中...
                  </span>
                  <el-button type="danger" size="small" text @click="clearImages">
                    <el-icon><Delete /></el-icon>
                    清空
                  </el-button>
                </div>
              </div>
              
              <div 
                ref="thumbnailContainerRef" 
                class="image-thumbnails"
              >
                <div 
                  v-for="(image, index) in displayedImages" 
                  :key="(currentPage - 1) * pageSize + index"
                  class="thumbnail"
                  :class="{ 'selected': selectedImageIndex === (currentPage - 1) * pageSize + index }"
                  @click="selectImage((currentPage - 1) * pageSize + index)"
                >
                  <img :src="image.thumbnail" :alt="`图片 ${(currentPage - 1) * pageSize + index + 1}`" loading="lazy" />
                  <div class="thumbnail-index">{{ (currentPage - 1) * pageSize + index + 1 }}</div>
                </div>
              </div>
              
              <div class="pagination-container" v-if="totalPages > 1">
                <el-pagination
                  v-model:current-page="currentPage"
                  :page-size="pageSize"
                  :total="images.length"
                  layout="prev, pager, next"
                  small
                  @current-change="onPageChange"
                />
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="10">
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>检测结果</span>
                <el-tag v-if="detecting" type="warning">检测中</el-tag>
                <el-tag v-else-if="result" type="success">完成</el-tag>
                <el-tag v-else type="info">等待检测</el-tag>
              </div>
            </template>

              <div class="result-content">
              <div v-if="detecting" class="loading-section">
                <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
                <div class="loading-text">正在分析图像...</div>
                <el-progress :percentage="detectionProgress" :status="detectionStatus" />
              </div>

              <div v-else-if="result" class="result-section">
                <div class="result-value">
                  <div class="result-label">检测结果</div>
                  <div class="result-number">{{ result.className }}</div>
                  <div class="result-unit">目标类别</div>
                </div>

                <div class="result-details">
                  <div class="detail-item">
                    <span class="detail-label">置信度</span>
                    <span class="detail-value">{{ (result.confidence * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">检测时间</span>
                    <span class="detail-value">{{ result.detectionTime }}ms</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">图像尺寸</span>
                    <span class="detail-value">{{ result.imageSize }}</span>
                  </div>
                  <div class="detail-item" v-if="result.bbox">
                    <span class="detail-label">检测框</span>
                    <span class="detail-value">[{{ result.bbox.join(', ') }}]</span>
                  </div>
                </div>

                <div class="result-actions">
                  <el-button type="primary" @click="predict" :disabled="!selectedImage && !cameraActive">
                    <el-icon><Refresh /></el-icon>
                    重新检测
                  </el-button>
                  <el-button type="success" @click="exportResult">
                    <el-icon><Download /></el-icon>
                    导出结果
                  </el-button>
                  <el-button v-if="batchResults.length > 1" type="info" @click="showBatchResults = true">
                    <el-icon><DataAnalysis /></el-icon>
                    查看批量结果
                  </el-button>
                </div>
              </div>

              <div v-else class="empty-result">
                <el-icon class="empty-icon"><DataAnalysis /></el-icon>
                <div class="empty-text">等待图像输入</div>
                <div class="empty-sub">请导入图片或使用摄像头进行检测</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog
      v-model="exportDialogVisible"
      title="导出检测结果"
      width="500px"
    >
      <div class="export-content">
        <div class="export-item">
          <span class="export-label">检测结果:</span>
          <span class="export-value">{{ result?.className }}</span>
        </div>
        <div class="export-item">
          <span class="export-label">置信度:</span>
          <span class="export-value">{{ result ? (result.confidence * 100).toFixed(1) : 0 }}%</span>
        </div>
        <div class="export-item">
          <span class="export-label">检测时间:</span>
          <span class="export-value">{{ result?.detectionTime }}ms</span>
        </div>
        <div class="export-item">
          <span class="export-label">检测时间戳:</span>
          <span class="export-value">{{ new Date().toLocaleString() }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="exportDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadResult">下载报告</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showBatchResults"
      title="批量预测结果"
      width="800px"
    >
      <div class="batch-results-content">
        <div class="batch-summary">
          <el-tag type="success">成功: {{ batchResults.filter(r => r.success).length }}</el-tag>
          <el-tag type="danger">失败: {{ batchResults.filter(r => !r.success).length }}</el-tag>
          <el-tag type="info">总计: {{ batchResults.length }}</el-tag>
        </div>
        <el-table :data="batchResults" style="width: 100%; margin-top: 20px;" max-height="400">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="filename" label="文件名" min-width="200" />
          <el-table-column label="状态" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.success ? 'success' : 'danger'" size="small">
                {{ scope.row.success ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="检测结果" width="120">
            <template #default="scope">
              <span v-if="scope.row.success">{{ scope.row.detection?.class_name || '-' }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="置信度" width="100">
            <template #default="scope">
              <span v-if="scope.row.success">{{ (scope.row.confidence! * 100).toFixed(1) }}%</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="错误信息" min-width="200">
            <template #default="scope">
              <span v-if="!scope.row.success" style="color: #f56c6c;">{{ scope.row.message }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showBatchResults = false">关闭</el-button>
        <el-button type="primary" @click="exportBatchResults">导出结果</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { Camera, CameraFilled, FolderOpened, Picture, Delete, Loading, Refresh, Download, DataAnalysis, SwitchButton } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
import { useRealtimeStore } from '@/stores/realtime'
import { modelApi } from '@/api'

interface DetectionResult {
  className: string
  confidence: number
  detectionTime: number
  imageSize: string
  bbox?: number[]
}

interface BatchPredictionResult {
  filename: string
  success: boolean
  detection?: {
    class_id: number
    class_name: string
    confidence: number
    bbox: number[]
  }
  confidence?: number
  message?: string
}

const store = useRealtimeStore()
const {
  images,
  pendingFiles,
  isProcessingFiles,
  selectedImageIndex,
  currentPage,
  pageSize,
  totalPages,
  displayedImages,
  skippedFiles
} = storeToRefs(store)

const selectedImage = computed(() => {
  if (selectedImageIndex.value >= 0 && selectedImageIndex.value < images.value.length) {
    return images.value[selectedImageIndex.value].url
  }
  return ''
})

const cameras = ref<MediaDeviceInfo[]>([])
const currentCameraIndex = ref(0)
const cameraActive = ref(false)
const videoReady = ref(false)
const detecting = ref(false)
const detectionProgress = ref(0)
const detectionStatus = ref('')
const result = ref<DetectionResult | null>(null)
const exportDialogVisible = ref(false)
const importInProgress = ref(false)
const batchResults = ref<BatchPredictionResult[]>([])
const showBatchResults = ref(false)

const currentYoloModel = ref<string | null>(null)

const THUMBNAIL_SIZE = 80
const BATCH_LOAD_SIZE = 20

const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const loadCurrentModels = async () => {
  try {
    const response = await modelApi.getCurrentModels()
    if (response.code === 200) {
      currentYoloModel.value = response.data.yolo_model
    }
  } catch (error) {
    console.error('加载当前模型失败:', error)
  }
}

const loadCameras = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    cameras.value = devices.filter(device => device.kind === 'videoinput')
    if (cameras.value.length === 0) {
      ElMessage.warning('未检测到摄像头设备')
    } else {
      console.log(`检测到 ${cameras.value.length} 个摄像头设备`)
    }
  } catch (error) {
    console.error('获取摄像头设备失败:', error)
    ElMessage.error('无法访问摄像头设备，请确保已授予摄像头权限')
  }
}

const createThumbnail = (file: File, maxSize: number = THUMBNAIL_SIZE): Promise<string> => {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    
    img.onload = () => {
      URL.revokeObjectURL(url)
      
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      
      if (!ctx) {
        resolve(url)
        return
      }
      
      let width = img.width
      let height = img.height
      
      if (width > height) {
        if (width > maxSize) {
          height = (height * maxSize) / width
          width = maxSize
        }
      } else {
        if (height > maxSize) {
          width = (width * maxSize) / height
          height = maxSize
        }
      }
      
      canvas.width = width
      canvas.height = height
      ctx.drawImage(img, 0, 0, width, height)
      
      resolve(canvas.toDataURL('image/jpeg', 0.7))
    }
    
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to load image'))
    }
    
    img.src = url
  })
}

const processFileQueue = async () => {
  if (isProcessingFiles.value || pendingFiles.value.length === 0) return
  
  store.setProcessingFiles(true)
  
  const batch: File[] = []
  for (let i = 0; i < BATCH_LOAD_SIZE && pendingFiles.value.length > 0; i++) {
    const file = store.removePendingFile()
    if (file) batch.push(file)
  }
  
  for (const file of batch) {
    try {
      const thumbnail = await createThumbnail(file)
      const url = URL.createObjectURL(file)
      
      store.addImage({
        url,
        thumbnail,
        file,
        loaded: true
      })
    } catch (error) {
      console.error('处理图片失败:', error)
    }
    
    await new Promise(resolve => setTimeout(resolve, 10))
  }
  
  store.setProcessingFiles(false)
  
  if (pendingFiles.value.length > 0) {
    requestIdleCallback(() => processFileQueue(), { timeout: 100 })
  }
}

const selectCamera = async (index: number) => {
  stopCamera()
  currentCameraIndex.value = index
  await startCamera()
}

const startCamera = async () => {
  try {
    const hostname = window.location.hostname
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      ElMessage.warning('使用 IP 地址访问时摄像头功能不可用，请使用 localhost 访问以使用摄像头功能')
      return
    }
    
    if (cameras.value.length === 0) {
      await loadCameras()
      if (cameras.value.length === 0) {
        ElMessage.error('未检测到摄像头，请检查设备连接和权限设置')
        return
      }
    }

    const constraints = {
      video: {
        deviceId: cameras.value[currentCameraIndex.value]?.deviceId,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      }
    }

    console.log('请求摄像头权限，约束条件:', constraints)
    const stream = await navigator.mediaDevices.getUserMedia(constraints)

    console.log('获取到视频流:', stream)
    console.log('视频流轨道:', stream.getTracks())

    cameraActive.value = true
    console.log('设置cameraActive为true')
    
    await nextTick()
    
    if (!videoRef.value) {
      console.error('videoRef不存在，等待DOM更新')
      await new Promise(resolve => setTimeout(resolve, 200))
    }

    if (videoRef.value) {
      console.log('videoRef存在，设置视频源')
      videoRef.value.srcObject = stream
      
      videoRef.value!.onloadedmetadata = () => {
        console.log('视频元数据已加载')
        console.log('视频尺寸:', videoRef.value!.videoWidth, 'x', videoRef.value!.videoHeight)
        
        if (videoRef.value!.videoWidth > 0 && videoRef.value!.videoHeight > 0) {
          console.log('视频尺寸有效')
          videoReady.value = true
          ElMessage.success('摄像头已开启')
        } else {
          console.error('视频尺寸无效:', videoRef.value!.videoWidth, videoRef.value!.videoHeight)
          ElMessage.error('摄像头初始化失败，视频尺寸无效')
          stopCamera()
        }
      }
      
      videoRef.value!.onerror = (error) => {
        console.error('视频加载错误:', error)
        ElMessage.error('摄像头加载失败，请重试')
        stopCamera()
      }
    } else {
      console.error('videoRef仍然不存在')
      ElMessage.error('视频元素初始化失败，请刷新页面重试')
      cameraActive.value = false
      stream.getTracks().forEach(track => track.stop())
    }
  } catch (error: any) {
    console.error('开启摄像头失败:', error)
    
    if (error.name === 'NotAllowedError') {
      ElMessage.error('摄像头权限被拒绝，请在浏览器设置中允许访问摄像头')
    } else if (error.name === 'NotFoundError') {
      ElMessage.error('未找到摄像头设备，请检查设备连接')
    } else if (error.name === 'NotReadableError') {
      ElMessage.error('摄像头被其他应用占用，请关闭其他应用后重试')
    } else {
      ElMessage.error(`无法开启摄像头: ${error.message || '未知错误'}`)
    }
  }
}

const stopCamera = () => {
  console.log('停止摄像头')
  if (videoRef.value && videoRef.value.srcObject) {
    const stream = videoRef.value.srcObject as MediaStream
    stream.getTracks().forEach(track => {
      console.log('停止视频轨道:', track)
      track.stop()
    })
    videoRef.value.srcObject = null
    cameraActive.value = false
    videoReady.value = false
    console.log('摄像头已停止，cameraActive:', cameraActive.value)
  }
}

const capturePhoto = () => {
  console.log('尝试拍照，cameraActive:', cameraActive.value)
  console.log('videoRef:', videoRef.value)
  console.log('canvasRef:', canvasRef.value)
  
  if (!videoRef.value || !canvasRef.value) {
    console.error('视频或画布元素不存在')
    ElMessage.error('无法拍照，请确保摄像头正常工作')
    return
  }

  const video = videoRef.value
  const canvas = canvasRef.value
  const context = canvas.getContext('2d')

  if (!context) {
    console.error('无法获取画布上下文')
    ElMessage.error('无法拍照，画布初始化失败')
    return
  }

  console.log('视频尺寸:', video.videoWidth, 'x', video.videoHeight)
  
  if (video.videoWidth === 0 || video.videoHeight === 0) {
    console.error('视频尺寸无效')
    ElMessage.error('摄像头未准备好，请稍后重试')
    return
  }

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  context.drawImage(video, 0, 0)

  const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9)
  const blob = dataURLtoBlob(imageDataUrl)

  if (blob) {
    const file = new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' })
    addImage(file, imageDataUrl)
    ElMessage.success('拍照成功')
  } else {
    console.error('无法创建图像blob')
    ElMessage.error('拍照失败，请重试')
  }
}

const handleFileChange = (file: any) => {
  if (file.raw) {
    if (!isValidImageFile(file.raw)) {
      store.incrementSkippedFiles()
      return
    }
    
    store.addPendingFile(file.raw)
    importInProgress.value = true
    
    if (!isProcessingFiles.value) {
      processFileQueue()
    }
  }
}

const isValidImageFile = (file: File): boolean => {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
  const validExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
  
  const fileType = file.type.toLowerCase()
  const fileName = file.name.toLowerCase()
  
  const isValidType = validTypes.includes(fileType)
  const isValidExtension = validExtensions.some(ext => fileName.endsWith(ext))
  
  return isValidType || isValidExtension
}

const addImage = async (file: File, url: string) => {
  try {
    const thumbnail = await createThumbnail(file)
    store.addImage({ url, thumbnail, file, loaded: true })
  } catch (error) {
    console.error('添加图片失败:', error)
  }
  importInProgress.value = true
}

const selectImage = (index: number) => {
  store.selectImage(index)
  result.value = null
}

const onPageChange = (page: number) => {
  store.setPage(page)
  result.value = null
}

const clearImages = () => {
  store.clearImages()
  result.value = null
  ElMessage.info('已清空所有图片')
}

const predict = async () => {
  if (images.value.length === 0) {
    ElMessage.warning('请先导入图片或使用摄像头拍照')
    return
  }

  detecting.value = true
  detectionProgress.value = 0
  detectionStatus.value = ''
  result.value = null
  batchResults.value = []
  showBatchResults.value = false

  try {
    const formData = new FormData()
    images.value.forEach((image) => {
      formData.append('files', image.file)
    })

    detectionProgress.value = 30

    const getApiBaseUrl = () => {
      const hostname = window.location.hostname
      return `http://${hostname}:5000/api`
    }

    const response = await fetch(`${getApiBaseUrl()}/predict/batch`, {
      method: 'POST',
      body: formData
    })

    detectionProgress.value = 70

    if (!response.ok) {
      throw new Error('预测请求失败')
    }

    const data = await response.json()

    if (data.success) {
      batchResults.value = data.data.results
      showBatchResults.value = true
      
      const successfulCount = data.data.successful
      const failedCount = data.data.failed

      if (failedCount > 0) {
        ElMessage.warning(`预测完成！成功 ${successfulCount} 张，失败 ${failedCount} 张`)
      } else {
        ElMessage.success(`预测完成！成功预测 ${successfulCount} 张图片`)
      }

      if (successfulCount > 0) {
        const firstSuccessful = batchResults.value.find(r => r.success)
        if (firstSuccessful && firstSuccessful.detection) {
          result.value = {
            className: firstSuccessful.detection.class_name,
            confidence: firstSuccessful.detection.confidence || 0,
            detectionTime: 150,
            imageSize: '1280x720',
            bbox: firstSuccessful.detection.bbox
          }
        }
      }
    } else {
      throw new Error(data.message || '预测失败')
    }

    detectionProgress.value = 100
    detectionStatus.value = 'success'

  } catch (error: any) {
    console.error('预测失败:', error)
    ElMessage.error(`预测失败: ${error.message || '未知错误'}`)
    detectionStatus.value = 'exception'
  } finally {
    detecting.value = false
  }
}

const exportResult = () => {
  if (result.value) {
    exportDialogVisible.value = true
  }
}

const downloadResult = () => {
  if (!result.value) return

  const workbook = XLSX.utils.book_new()
  
  const summaryData = [
    ['YOLO目标检测报告'],
    [''],
    ['检测项目', '数值'],
    ['检测结果', result.value.className],
    ['置信度 (%)', (result.value.confidence * 100).toFixed(1)],
    ['检测时间 (ms)', result.value.detectionTime],
    ['图像尺寸', result.value.imageSize],
    ['检测时间戳', new Date().toLocaleString()]
  ]
  
  const summarySheet = XLSX.utils.aoa_to_sheet(summaryData)
  
  summarySheet['!cols'] = [
    { wch: 20 },
    { wch: 25 }
  ]
  
  XLSX.utils.book_append_sheet(workbook, summarySheet, '检测结果')
  
  const fileName = `detection_result_${Date.now()}.xlsx`
  XLSX.writeFile(workbook, fileName)

  exportDialogVisible.value = false
  ElMessage.success('报告已下载')
}

const exportBatchResults = () => {
  if (batchResults.value.length === 0) return

  const workbook = XLSX.utils.book_new()
  
  const summaryData = [
    ['批量检测结果报告'],
    [''],
    ['导出时间', new Date().toLocaleString()],
    ['总计', batchResults.value.length],
    ['成功', batchResults.value.filter(r => r.success).length],
    ['失败', batchResults.value.filter(r => !r.success).length]
  ]
  
  const summarySheet = XLSX.utils.aoa_to_sheet(summaryData)
  summarySheet['!cols'] = [
    { wch: 20 },
    { wch: 15 }
  ]
  XLSX.utils.book_append_sheet(workbook, summarySheet, '汇总信息')
  
  const detailData = [
    ['序号', '文件名', '状态', '检测结果', '置信度 (%)', '错误信息']
  ]
  
  batchResults.value.forEach((result, index) => {
    detailData.push([
      String(index + 1),
      result.filename,
      result.success ? '成功' : '失败',
      result.success ? (result.detection?.class_name || '-') : '-',
      result.success ? ((result.confidence ?? 0) * 100).toFixed(1) : '-',
      result.success ? '-' : (result.message || '')
    ])
  })
  
  const detailSheet = XLSX.utils.aoa_to_sheet(detailData)
  detailSheet['!cols'] = [
    { wch: 8 },
    { wch: 30 },
    { wch: 10 },
    { wch: 15 },
    { wch: 12 },
    { wch: 40 }
  ]
  
  XLSX.utils.book_append_sheet(workbook, detailSheet, '详细结果')
  
  const fileName = `batch_prediction_results_${Date.now()}.xlsx`
  XLSX.writeFile(workbook, fileName)

  showBatchResults.value = false
  ElMessage.success('批量结果已导出')
}

const onVideoLoaded = () => {
  console.log('视频元数据已加载')
  console.log('视频尺寸:', videoRef.value?.videoWidth, 'x', videoRef.value?.videoHeight)
  console.log('视频元素:', videoRef.value)
  console.log('视频源:', videoRef.value?.srcObject)
  
  if (videoRef.value && videoRef.value.videoWidth > 0 && videoRef.value.videoHeight > 0) {
    console.log('视频尺寸有效，显示视频元素')
    videoRef.value.style.display = 'block'
  } else {
    console.log('视频尺寸无效，保持隐藏状态')
  }
}

const onVideoPlay = () => {
  console.log('视频开始播放')
  console.log('cameraActive状态:', cameraActive.value)
  console.log('视频当前时间:', videoRef.value?.currentTime)
  console.log('视频播放状态:', videoRef.value?.paused ? '暂停' : '播放中')
  videoReady.value = true
}

const onVideoCanPlay = () => {
  console.log('视频可以播放')
  videoReady.value = true
}

const onVideoWaiting = () => {
  console.log('视频正在缓冲')
}

const onVideoError = (error: Event) => {
  console.error('视频播放错误:', error)
  ElMessage.error('摄像头播放出错，请重试')
  cameraActive.value = false
  videoReady.value = false
  if (videoRef.value) {
    videoRef.value.style.display = 'none'
  }
}

const dataURLtoBlob = (dataURL: string): Blob | null => {
  const arr = dataURL.split(',')
  const mime = arr[0].match(/:(.*?);/)?.[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  return new Blob([u8arr], { type: mime })
}

watch(importInProgress, async (newValue, oldValue) => {
  if (newValue && !oldValue) {
    await nextTick()
    setTimeout(() => {
      importInProgress.value = false
      if (skippedFiles.value > 0) {
        ElMessage.warning(`导入完成！成功导入 ${images.value.length} 张图片，跳过 ${skippedFiles.value} 个非图片文件`)
      } else {
        ElMessage.success(`导入完成！成功导入 ${images.value.length} 张图片`)
      }
      store.resetSkippedFiles()
    }, 500)
  }
})

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && cameraActive.value && videoReady.value) {
    event.preventDefault()
    console.log('Enter键按下，快速拍照')
    capturePhoto()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyPress)
  loadCameras()
  loadCurrentModels()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyPress)
  if (cameraActive.value) {
    stopCamera()
  }
})
</script>

<style scoped>
.detection-page {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 10px 0;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0 0 15px 0;
}

.current-models {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
}

.main-card, .result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.image-section {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
  aspect-ratio: 16 / 9;
}

.camera-container {
  width: 100%;
  height: auto;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  pointer-events: none;
  aspect-ratio: 16 / 9;
}

.camera-video {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: auto;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.camera-video.video-ready {
  opacity: 1;
}

.camera-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  z-index: 10;
  pointer-events: none;
}

.camera-overlay .loading-icon {
  font-size: 48px;
  color: #409eff;
  animation: rotate 2s linear infinite;
}

.camera-overlay .status-text {
  margin-top: 15px;
  font-size: 16px;
  color: white;
  font-weight: 500;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.image-preview {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.empty-state {
  text-align: center;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 15px;
  color: #c0c4cc;
}

.empty-text {
  font-size: 16px;
  margin: 0;
}

.image-list {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.list-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.processing-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #409eff;
  font-size: 13px;
}

.loading-icon-small {
  font-size: 14px;
  animation: rotate 2s linear infinite;
}

.image-thumbnails {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.thumbnail {
  position: relative;
  aspect-ratio: 1;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s ease;
}

.thumbnail:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.thumbnail.selected {
  border-color: #409eff;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-index {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 2px;
}

.pagination-container {
  margin-top: 15px;
  display: flex;
  justify-content: center;
}

.result-content {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-section {
  text-align: center;
  padding: 40px 20px;
}

.loading-icon {
  color: #409eff;
  margin-bottom: 20px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 20px;
}

.result-section {
  width: 100%;
  padding: 20px;
}

.result-value {
  text-align: center;
  margin-bottom: 30px;
  padding: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.result-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 10px;
}

.result-number {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 5px;
}

.result-unit {
  font-size: 20px;
  font-weight: 500;
  opacity: 0.8;
}

.result-details {
  margin-bottom: 20px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 14px;
  color: #909399;
}

.detail-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.result-actions .el-button {
  flex: 1;
}

.empty-result {
  text-align: center;
  color: #909399;
}

.empty-result .empty-icon {
  color: #c0c4cc;
}

.empty-result .empty-text {
  font-size: 16px;
  margin-bottom: 5px;
}

.empty-result .empty-sub {
  font-size: 14px;
  color: #c0c4cc;
  opacity: 0.7;
}

.export-content {
  padding: 10px 0;
}

.export-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.export-item:last-child {
  border-bottom: none;
}

.export-label {
  font-size: 14px;
  color: #909399;
}

.export-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.batch-results-content {
  padding: 10px 0;
}

.batch-summary {
  display: flex;
  gap: 10px;
  justify-content: center;
  padding: 15px 0;
  background: #f5f7fa;
  border-radius: 4px;
}

/* 响应式 - 平板 */
@media (max-width: 992px) {
  .content-container :deep(.el-col) {
    margin-bottom: 16px;
  }
}

/* 响应式 - 移动端 */
@media (max-width: 768px) {
  .detection-page {
    padding: 10px;
  }
  
  .page-header {
    margin-bottom: 16px;
  }
  
  .page-title {
    font-size: 22px;
    line-height: 1.3;
  }
  
  .page-description {
    font-size: 13px;
  }
  
  .current-models {
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .header-actions .el-button {
    flex: 0 0 auto;
    min-width: auto;
    padding: 8px 12px;
    font-size: 13px;
  }
  
  .image-section {
    min-height: 200px;
    aspect-ratio: 4 / 3;
  }
  
  .camera-container {
    min-height: 200px;
  }
  
  .empty-icon {
    font-size: 48px;
  }
  
  .empty-text {
    font-size: 14px;
  }
  
  .image-list {
    margin-top: 16px;
    padding-top: 16px;
  }
  
  .list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .list-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .image-thumbnails {
    grid-template-columns: repeat(auto-fill, minmax(60px, 1fr));
    gap: 8px;
    max-height: 200px;
  }
  
  .thumbnail-index {
    font-size: 10px;
    padding: 1px 4px;
  }
  
  .result-content {
    min-height: 300px;
  }
  
  .result-section {
    padding: 12px;
  }
  
  .result-value {
    padding: 20px 16px;
    margin-bottom: 20px;
  }
  
  .result-label {
    font-size: 13px;
  }
  
  .result-number {
    font-size: 36px;
  }
  
  .result-unit {
    font-size: 16px;
  }
  
  .detail-item {
    padding: 10px 0;
  }
  
  .detail-label,
  .detail-value {
    font-size: 13px;
  }
  
  .result-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .result-actions .el-button {
    width: 100%;
  }
  
  .empty-result .empty-text {
    font-size: 14px;
  }
  
  .empty-result .empty-sub {
    font-size: 12px;
  }
  
  .batch-summary {
    flex-wrap: wrap;
    gap: 8px;
  }
}

/* 响应式 - 小屏幕手机 */
@media (max-width: 480px) {
  .detection-page {
    padding: 8px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .page-description {
    font-size: 12px;
  }
  
  .header-actions .el-button {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .image-section {
    min-height: 180px;
  }
  
  .camera-container {
    min-height: 180px;
  }
  
  .image-thumbnails {
    grid-template-columns: repeat(auto-fill, minmax(50px, 1fr));
    gap: 6px;
  }
  
  .result-number {
    font-size: 28px;
  }
  
  .result-unit {
    font-size: 14px;
  }
}
</style>
