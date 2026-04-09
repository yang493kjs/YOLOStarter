<template>
  <div class="dataset-list-page">
    <div class="page-header">
      <h2>数据集管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建数据集
      </el-button>
    </div>
    
    <div class="dataset-grid" v-if="datasetList.length > 0">
      <el-card
        v-for="dataset in datasetList"
        :key="dataset.id"
        class="dataset-card"
        shadow="hover"
        @click="openDataset(dataset.id)"
      >
        <div class="card-content">
          <div class="card-icon">
            <el-icon :size="48"><FolderOpened /></el-icon>
          </div>
          <div class="card-info">
            <h3>{{ dataset.name }}</h3>
            <div class="card-meta">
              <span>
                <el-icon><Picture /></el-icon>
                {{ dataset.imageCount || 0 }} 张图片
              </span>
              <span>
                <el-icon><Document /></el-icon>
                {{ dataset.labelCount || 0 }} 个标签
              </span>
            </div>
            <div class="card-time">
              创建于 {{ formatDate(dataset.createTime) }}
            </div>
          </div>
          <el-button
            type="danger"
            size="small"
            circle
            class="delete-btn"
            @click.stop="deleteDataset(dataset.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>
    
    <el-empty v-else description="暂无数据集，点击上方按钮创建" />
    
    <el-dialog
      v-model="showCreateDialog"
      title="创建数据集"
      width="400px"
    >
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="数据集名称">
          <el-input
            v-model="createForm.name"
            placeholder="请输入数据集名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入描述（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createDataset" :disabled="!createForm.name.trim()">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  FolderOpened,
  Picture,
  Document,
  Delete,
} from '@element-plus/icons-vue'

import { datasetApi } from '@/api'

interface DatasetInfo {
  id: string
  name: string
  description?: string
  createTime: string
  imageCount: number
  labelCount: number
  hasYaml: boolean
}

const router = useRouter()

const datasetList = ref<DatasetInfo[]>([])
const showCreateDialog = ref(false)
const createForm = ref({
  name: '',
  description: ''
})

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const loadDatasetList = async () => {
  try {
    console.log('从后端加载数据集列表...')
    
    const result = await datasetApi.getDatasets()
    
    if (result.code === 200 && result.data) {
      datasetList.value = result.data
      console.log(`成功加载 ${datasetList.value.length} 个数据集`)
    } else {
      console.error('加载数据集列表失败:', result.message)
    }
  } catch (error) {
    console.error('加载数据集列表失败:', error)
  }
}

const createDataset = async () => {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入数据集名称')
    return
  }
  
  try {
    const result = await datasetApi.createDataset({
      name: createForm.value.name.trim(),
      description: createForm.value.description.trim()
    })
    
    if (result.code === 200) {
      datasetList.value.unshift(result.data)
      showCreateDialog.value = false
      createForm.value = { name: '', description: '' }
      ElMessage.success('数据集创建成功')
    } else {
      ElMessage.error(result.message || '创建失败')
    }
  } catch (error) {
    console.error('创建数据集失败:', error)
    ElMessage.error('创建数据集失败')
  }
}

const openDataset = (id: string) => {
  router.push(`/dataset/${id}`)
}

const deleteDataset = async (id: string) => {
  ElMessageBox.confirm('确定要删除此数据集吗？所有数据将被永久删除！', '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      const result = await datasetApi.deleteDataset(id)
      if (result.code === 200) {
        datasetList.value = datasetList.value.filter(item => item.id !== id)
        ElMessage.success('数据集已删除')
      } else {
        ElMessage.error(result.message || '删除失败')
      }
    } catch (error) {
      console.error('删除数据集失败:', error)
      ElMessage.error('删除数据集失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadDatasetList()
})
</script>

<style scoped>
.dataset-list-page {
  height: 100%;
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

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.dataset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.dataset-card {
  cursor: pointer;
  transition: all 0.3s;
}

.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.card-content {
  display: flex;
  align-items: center;
  position: relative;
}

.card-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
  margin-left: 16px;
  min-width: 0;
}

.card-info h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 6px;
}

.card-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #606266;
}

.card-time {
  font-size: 12px;
  color: #909399;
}

.delete-btn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.3s;
}

.dataset-card:hover .delete-btn{
  opacity: 1;
}

/* 响应式 - 平板 */
@media (max-width: 992px) {
  .dataset-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
}

/* 响应式 - 移动端 */
@media (max-width: 768px) {
  .dataset-list-page {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
  }
  
  .page-header h2 {
    font-size: 18px;
  }
  
  .page-header .el-button {
    width: 100%;
  }
  
  .dataset-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .dataset-card {
    margin-bottom: 0;
  }
  
  .dataset-card:hover {
    transform: none;
  }
  
  .card-content {
    padding: 12px;
  }
  
  .card-icon {
    width: 60px;
    height: 60px;
  }
  
  .card-icon :deep(.el-icon) {
    font-size: 28px;
  }
  
  .card-info {
    margin-left: 12px;
  }
  
  .card-info h3 {
    font-size: 16px;
    margin-bottom: 6px;
  }
  
  .card-meta {
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 4px;
  }
  
  .card-meta span {
    font-size: 13px;
  }
  
  .card-time {
    font-size: 11px;
  }
  
  .delete-btn {
    opacity: 1;
    right: 8px;
  }
}

/* 响应式 - 小屏幕手机 */
@media (max-width: 480px) {
  .dataset-list-page {
    padding: 8px;
  }
  
  .page-header {
    padding: 10px 12px;
    margin-bottom: 12px;
  }
  
  .page-header h2 {
    font-size: 16px;
  }
  
  .card-content {
    padding: 10px;
  }
  
  .card-icon {
    width: 48px;
    height: 48px;
  }
  
  .card-icon :deep(.el-icon) {
    font-size: 22px;
  }
  
  .card-info {
    margin-left: 10px;
  }
  
  .card-info h3 {
    font-size: 14px;
    margin-bottom: 4px;
  }
  
  .card-meta {
    gap: 8px;
  }
  
  .card-meta span {
    font-size: 12px;
  }
  
  .card-time {
    font-size: 10px;
  }
}
</style>
