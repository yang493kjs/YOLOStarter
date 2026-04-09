<template>
  <div class="guide-page">
    <el-card class="guide-card">
      <template #header>
        <div class="card-header">
          <el-icon><QuestionFilled /></el-icon>
          <span>YOLO检测系统使用指南</span>
        </div>
      </template>

      <el-collapse v-model="activeNames" accordion>
        <el-collapse-item title="1. 系统概述" name="1">
          <div class="guide-content">
            <p>本系统是一个基于YOLO目标检测模型的图像检测平台，主要功能包括：</p>
            <ul>
              <li><strong>实时预测</strong>：通过摄像头或上传图片进行实时目标检测</li>
              <li><strong>模型管理</strong>：管理和测试已训练的YOLO模型</li>
              <li><strong>模型训练</strong>：使用自定义数据集训练YOLO模型</li>
              <li><strong>数据集管理</strong>：创建和管理训练数据集</li>
              <li><strong>使用指南</strong>：查看系统使用说明和常见问题解答</li>
            </ul>
          </div>
        </el-collapse-item>

        <el-collapse-item title="2. 侧边栏菜单说明" name="2">
          <div class="guide-content">
            <p>系统左侧导航栏包含以下功能模块：</p>
            <el-table :data="menuData" border style="width: 100%">
              <el-table-column prop="name" label="菜单名称" width="120" />
              <el-table-column prop="icon" label="图标" width="80" />
              <el-table-column prop="desc" label="功能说明" />
            </el-table>
          </div>
        </el-collapse-item>

        <el-collapse-item title="3. 实时预测使用方法" name="3">
          <div class="guide-content">
            <h4>3.1 使用摄像头检测</h4>
            <ol>
              <li>进入"实时预测"页面</li>
              <li>点击"开启摄像头"按钮</li>
              <li>选择要使用的摄像头设备</li>
              <li>摄像头开启后，点击"拍照"按钮进行检测</li>
              <li>检测结果将显示在右侧面板中</li>
            </ol>

            <h4>3.2 上传图片检测</h4>
            <ol>
              <li>点击"导入图片"按钮或拖拽图片到预览区域</li>
              <li>支持批量上传多张图片</li>
              <li>系统将自动进行目标检测</li>
              <li>检测结果可导出为Excel报告</li>
            </ol>
          </div>
        </el-collapse-item>

        <el-collapse-item title="4. 模型管理使用方法" name="4">
          <div class="guide-content">
            <h4>4.1 查看模型列表</h4>
            <p>进入"模型管理器"页面，可以查看所有已训练的YOLO模型，包括模型名称、创建时间、训练轮数等信息。</p>

            <h4>4.2 测试模型</h4>
            <ol>
              <li>点击模型卡片上的"开始测试"按钮</li>
              <li>系统将自动使用测试数据集评估模型性能</li>
              <li>测试完成后显示评估指标：mAP@50、精确率、召回率、F1分数等</li>
            </ol>

            <h4>4.3 切换当前模型</h4>
            <p>点击"设为测试模型"按钮，将该模型设置为实时预测使用的模型。</p>

            <h4>4.4 删除模型</h4>
            <p>点击"删除"按钮可以删除不需要的模型文件。</p>
          </div>
        </el-collapse-item>

        <el-collapse-item title="5. 模型训练使用方法" name="5">
          <div class="guide-content">
            <h4>5.1 准备数据集</h4>
            <p>首先需要在"数据集"页面创建训练数据集，数据集需要包含：</p>
            <ul>
              <li>训练图片（train/images）</li>
              <li>训练标签（train/labels）</li>
              <li>验证图片（valid/images）</li>
              <li>验证标签（valid/labels）</li>
              <li>配置文件（data.yaml）</li>
            </ul>

            <h4>5.2 配置训练参数</h4>
            <ol>
              <li><strong>数据集</strong>：选择已创建的数据集</li>
              <li><strong>基础模型</strong>：选择预训练模型（YOLOv8n/s/m/l）</li>
              <li><strong>训练轮数</strong>：设置训练迭代次数（建议100-300）</li>
              <li><strong>批次大小</strong>：根据显存大小调整（显存不足时减小）</li>
              <li><strong>图像尺寸</strong>：输入图像尺寸（默认640）</li>
              <li><strong>设备选择</strong>：选择GPU或CPU训练</li>
            </ol>

            <h4>5.3 开始训练</h4>
            <ol>
              <li>点击"保存参数"保存当前配置</li>
              <li>点击"开始训练"启动训练任务</li>
              <li>训练过程中可以查看实时日志</li>
              <li>训练完成后模型自动保存到模型列表</li>
            </ol>
          </div>
        </el-collapse-item>

        <el-collapse-item title="6. 数据集管理使用方法" name="6">
          <div class="guide-content">
            <h4>6.1 创建数据集</h4>
            <ol>
              <li>进入"数据集"页面</li>
              <li>点击"创建数据集"按钮</li>
              <li>上传训练图片和标签文件</li>
              <li>配置类别名称</li>
              <li>保存数据集</li>
            </ol>

            <h4>6.2 数据集格式要求</h4>
            <p>标签文件格式（YOLO格式）：</p>
            <pre>class_id center_x center_y width height
0 0.5 0.5 0.3 0.4
1 0.2 0.3 0.1 0.2</pre>
            <p>其中坐标值为归一化值（0-1之间）。</p>
          </div>
        </el-collapse-item>

        <el-collapse-item title="7. YAML配置文件说明" name="7">
          <div class="guide-content">
            <el-alert type="warning" :closable="false" style="margin-bottom: 16px;">
              <template #title>
                <strong>重要提示</strong>
              </template>
              YAML配置文件（data.yaml）是训练的核心配置，路径配置错误会导致训练失败！
            </el-alert>

            <h4>7.1 YAML文件结构</h4>
            <pre>names:
- tube
- class2
nc: 2
path: D:/yuyan/Visual/datasets/your_dataset
train: train/images
val: valid/images
test: test/images</pre>

            <h4>7.2 字段说明</h4>
            <el-table :data="yamlFields" border style="width: 100%">
              <el-table-column prop="field" label="字段名" width="100" />
              <el-table-column prop="required" label="是否必需" width="100" />
              <el-table-column prop="desc" label="说明" />
            </el-table>

            <h4>7.3 常见错误</h4>
            <el-alert type="error" :closable="false" style="margin-bottom: 12px;">
              <template #title>错误示例：使用相对路径</template>
              <pre>path: .  # 错误！可能导致找不到文件</pre>
            </el-alert>
            <el-alert type="success" :closable="false">
              <template #title>正确示例：使用绝对路径</template>
              <pre>path: D:/yuyan/Visual/datasets/your_dataset  # 正确</pre>
            </el-alert>

            <h4>7.4 数据集目录结构</h4>
            <pre>datasets/
└── your_dataset/
    ├── data.yaml          # 配置文件
    ├── train/
    │   ├── images/        # 训练图片
    │   └── labels/        # 训练标签
    ├── valid/
    │   ├── images/        # 验证图片
    │   └── labels/        # 验证标签
    └── test/
        ├── images/        # 测试图片
        └── labels/        # 测试标签</pre>
          </div>
        </el-collapse-item>

        <el-collapse-item title="8. 常见问题" name="8">
          <div class="guide-content">
            <h4>Q1: 训练时显存不足怎么办？</h4>
            <p>可以尝试以下方法：</p>
            <ul>
              <li>减小批次大小（batch_size）</li>
              <li>减小图像尺寸（img_size）</li>
              <li>使用更小的模型（如YOLOv8n）</li>
            </ul>

            <h4>Q2: 如何提高检测精度？</h4>
            <ul>
              <li>增加训练数据量</li>
              <li>使用数据增强</li>
              <li>增加训练轮数</li>
              <li>使用更大的模型（如YOLOv8m/l）</li>
              <li>调整学习率等超参数</li>
            </ul>

            <h4>Q3: 摄像头无法开启？</h4>
            <ul>
              <li>检查浏览器是否授予摄像头权限</li>
              <li>确保摄像头未被其他程序占用</li>
              <li>尝试刷新页面后重新开启</li>
            </ul>

            <h4>Q4: 支持哪些图片格式？</h4>
            <p>支持常见图片格式：JPG、JPEG、PNG、BMP</p>

            <h4>Q5: 训练报错 "images not found"？</h4>
            <p>这是YAML配置文件路径问题，请检查：</p>
            <ul>
              <li><code>path</code> 字段是否使用绝对路径</li>
              <li>数据集目录下是否存在对应的 images 和 labels 文件夹</li>
              <li>路径中的斜杠方向（建议使用正斜杠 /）</li>
            </ul>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'

const activeNames = ref('1')

const menuData = [
  { name: '实时预测', icon: '显示器', desc: '通过摄像头或上传图片进行实时目标检测，支持批量检测和结果导出' },
  { name: '模型管理器', icon: '盒子', desc: '查看、测试、切换和删除已训练的YOLO模型' },
  { name: '训练数据', icon: '设置', desc: '配置训练参数，启动YOLO模型训练任务' },
  { name: '数据集', icon: '文件夹', desc: '创建、管理和删除训练数据集' },
  { name: '使用指南', icon: '问号', desc: '查看系统使用说明和常见问题解答' },
]

const yamlFields = [
  { field: 'names', required: '是', desc: '类别名称列表，支持中文名称' },
  { field: 'nc', required: '是', desc: '类别数量，必须与names列表长度一致' },
  { field: 'path', required: '是', desc: '数据集根目录的绝对路径（推荐使用正斜杠/）' },
  { field: 'train', required: '是', desc: '训练集图片目录（相对于path）' },
  { field: 'val', required: '是', desc: '验证集图片目录（相对于path），如无单独验证集可指向train' },
  { field: 'test', required: '否', desc: '测试集图片目录（相对于path）' },
]
</script>

<style scoped>
.guide-page {
  height: 100%;
  overflow-y: auto;
}

.guide-card {
  max-width: 900px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.guide-content {
  padding: 10px 0;
  line-height: 1.8;
}

.guide-content h4 {
  margin: 16px 0 8px;
  color: #409eff;
  font-size: 15px;
}

.guide-content h4:first-child {
  margin-top: 0;
}

.guide-content p {
  margin: 8px 0;
  color: #606266;
}

.guide-content ul,
.guide-content ol {
  margin: 8px 0;
  padding-left: 24px;
}

.guide-content li {
  margin: 6px 0;
  color: #606266;
}

.guide-content pre {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 6px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  overflow-x: auto;
  margin: 10px 0;
}

.guide-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #e6a23c;
}

:deep(.el-collapse-item__header) {
  font-size: 15px;
  font-weight: 500;
  height: 50px;
}

:deep(.el-collapse-item__content) {
  padding-bottom: 10px;
}

:deep(.el-alert pre) {
  margin: 8px 0 0;
  padding: 8px 12px;
  font-size: 12px;
}
</style>
