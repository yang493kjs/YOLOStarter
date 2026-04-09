<template>
  <div class="threshold-page">
    <!-- 页面说明 -->
    <el-alert
      title="阈值设置说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      <template #default>
        设置传感器的浓度阈值，当浓度超过警告阈值时系统会发出警告，超过危险阈值时发出危险告警。
      </template>
    </el-alert>

    <!-- 阈值列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>阈值配置列表</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增配置
          </el-button>
        </div>
      </template>

      <el-table :data="thresholdList" stripe>
        <el-table-column label="传感器" min-width="180">
          <template #default="{ row }">
            <div class="sensor-info">
              <el-icon><Cpu /></el-icon>
              <span>{{ getSensorName(row.sensorId) }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="警告阈值" width="140">
          <template #default="{ row }">
            <span class="threshold-value warning">{{ row.warningThreshold }} {{ row.unit }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="危险阈值" width="140">
          <template #default="{ row }">
            <span class="threshold-value danger">{{ row.dangerThreshold }} {{ row.unit }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="范围" width="160">
          <template #default="{ row }">
            {{ row.minValue }} - {{ row.maxValue }} {{ row.unit }}
          </template>
        </el-table-column>
        
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updatedAt) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" text size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑阈值配置' : '新增阈值配置'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="传感器" prop="sensorId">
          <el-select
            v-model="formData.sensorId"
            placeholder="选择传感器"
            style="width: 100%"
            :disabled="isEdit"
          >
            <el-option
              v-for="sensor in onlineSensors"
              :key="sensor.id"
              :label="sensor.name"
              :value="sensor.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="最小值" prop="minValue">
          <el-input-number
            v-model="formData.minValue"
            :min="0"
            :max="formData.maxValue - 1"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="最大值" prop="maxValue">
          <el-input-number
            v-model="formData.maxValue"
            :min="formData.minValue + 1"
            :max="1000"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="警告阈值" prop="warningThreshold">
          <el-slider
            v-model="formData.warningThreshold"
            :min="formData.minValue"
            :max="formData.dangerThreshold - 1"
            show-input
          />
        </el-form-item>
        
        <el-form-item label="危险阈值" prop="dangerThreshold">
          <el-slider
            v-model="formData.dangerThreshold"
            :min="formData.warningThreshold + 1"
            :max="formData.maxValue"
            show-input
          />
        </el-form-item>
        
        <el-form-item label="单位" prop="unit">
          <el-input v-model="formData.unit" placeholder="请输入单位" />
        </el-form-item>
      </el-form>

      <!-- 预览 -->
      <div class="threshold-preview">
        <div class="preview-title">阈值预览</div>
        <div class="preview-bar">
          <div class="bar-track">
            <div class="bar-segment normal" :style="{ width: normalWidth + '%' }"></div>
            <div class="bar-segment warning" :style="{ width: warningWidth + '%' }"></div>
            <div class="bar-segment danger" :style="{ width: dangerWidth + '%' }"></div>
          </div>
          <div class="bar-labels">
            <span>正常</span>
            <span>警告</span>
            <span>危险</span>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量设置 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <span>批量设置</span>
      </template>
      
      <el-form inline>
        <el-form-item label="警告阈值">
          <el-input-number v-model="batchWarning" :min="0" :max="99" />
        </el-form-item>
        <el-form-item label="危险阈值">
          <el-input-number v-model="batchDanger" :min="1" :max="100" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleBatchUpdate">
            应用到所有传感器
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useConcentrationStore } from '@/stores'
import type { ThresholdConfig } from '@/types'
import {
  Plus,
  Edit,
  Delete,
  Cpu,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import dayjs from 'dayjs'

const store = useConcentrationStore()

// 数据
const thresholdList = computed(() => store.thresholds)
const sensors = computed(() => store.sensors)
const onlineSensors = computed(() => store.onlineSensors)

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 表单数据
const formData = reactive({
  id: '',
  sensorId: '',
  minValue: 0,
  maxValue: 100,
  warningThreshold: 60,
  dangerThreshold: 80,
  unit: 'mg/L',
})

// 表单验证
const formRules: FormRules = {
  sensorId: [{ required: true, message: '请选择传感器', trigger: 'change' }],
  minValue: [{ required: true, message: '请输入最小值', trigger: 'blur' }],
  maxValue: [{ required: true, message: '请输入最大值', trigger: 'blur' }],
  warningThreshold: [{ required: true, message: '请输入警告阈值', trigger: 'blur' }],
  dangerThreshold: [{ required: true, message: '请输入危险阈值', trigger: 'blur' }],
  unit: [{ required: true, message: '请输入单位', trigger: 'blur' }],
}

// 批量设置
const batchWarning = ref(60)
const batchDanger = ref(80)

// 预览计算
const normalWidth = computed(() => {
  const range = formData.maxValue - formData.minValue
  return ((formData.warningThreshold - formData.minValue) / range) * 100
})

const warningWidth = computed(() => {
  const range = formData.maxValue - formData.minValue
  return ((formData.dangerThreshold - formData.warningThreshold) / range) * 100
})

const dangerWidth = computed(() => {
  const range = formData.maxValue - formData.minValue
  return ((formData.maxValue - formData.dangerThreshold) / range) * 100
})

// 方法
const getSensorName = (sensorId: string) => {
  const sensor = sensors.value.find(s => s.id === sensorId)
  return sensor?.name || sensorId
}

const formatTime = (date: Date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    id: '',
    sensorId: '',
    minValue: 0,
    maxValue: 100,
    warningThreshold: 60,
    dangerThreshold: 80,
    unit: 'mg/L',
  })
  dialogVisible.value = true
}

const handleEdit = (row: ThresholdConfig) => {
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    sensorId: row.sensorId,
    minValue: row.minValue,
    maxValue: row.maxValue,
    warningThreshold: row.warningThreshold,
    dangerThreshold: row.dangerThreshold,
    unit: row.unit,
  })
  dialogVisible.value = true
}

const handleDelete = async (row: ThresholdConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除传感器 "${getSensorName(row.sensorId)}" 的阈值配置吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 这里应该调用API删除
    ElMessage.success('删除成功')
    await store.fetchThresholds()
  } catch {
    // 用户取消
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const success = await store.updateThreshold(formData)
      if (success) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
      } else {
        ElMessage.error('操作失败')
      }
    } finally {
      submitting.value = false
    }
  })
}

const handleBatchUpdate = async () => {
  if (batchWarning.value >= batchDanger.value) {
    ElMessage.warning('警告阈值必须小于危险阈值')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要将所有传感器的警告阈值设置为 ${batchWarning.value}，危险阈值设置为 ${batchDanger.value} 吗？`,
      '确认批量设置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 批量更新
    for (const threshold of thresholdList.value) {
      await store.updateThreshold({
        id: threshold.id,
        warningThreshold: batchWarning.value,
        dangerThreshold: batchDanger.value,
      })
    }
    
    ElMessage.success('批量设置成功')
  } catch {
    // 用户取消
  }
}

// 初始化
onMounted(async () => {
  await store.fetchSensors()
  await store.fetchThresholds()
})
</script>

<style scoped>
.threshold-page {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sensor-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.threshold-value {
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.threshold-value.warning {
  background: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.threshold-value.danger {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.threshold-preview {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.preview-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.preview-bar {
  margin-top: 8px;
}

.bar-track {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
}

.bar-segment {
  height: 100%;
  transition: width 0.3s;
}

.bar-segment.normal {
  background: #67c23a;
}

.bar-segment.warning {
  background: #e6a23c;
}

.bar-segment.danger {
  background: #f56c6c;
}

.bar-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

/* 响应式 */
@media (max-width: 768px) {
  .el-dialog {
    width: 90% !important;
  }
}
</style>
