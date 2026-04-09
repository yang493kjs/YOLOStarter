# YOLOStarter - YOLO目标检测可视化平台

## 项目简介

**YOLOStarter** 是一个专为代码小白和对视觉模型感兴趣的新手设计的 **YOLO目标检测可视化平台**。无需编写复杂代码，通过友好的图形界面即可完成从数据集准备、模型训练到实时预测的完整机器学习工作流。

---

## 为什么创建这个项目？

对于想要入门计算机视觉的新手来说，YOLO模型的学习曲线往往比较陡峭：

- 环境配置繁琐，容易出错
- 命令行操作对新手不友好
- 训练参数复杂，不知如何调整
- 缺乏可视化的训练过程和结果展示

**YOLOStarter** 的诞生就是为了解决这些痛点，让每个人都能轻松体验目标检测的魅力。

---

## 核心功能

### 1. 实时预测
- 支持摄像头实时检测
- 支持图片上传批量检测
- 检测结果可视化展示
- 支持导出Excel检测报告

### 2. 模型训练
- 可视化配置训练参数
- 支持YOLOv8n/s/m/l多种模型规格
- 实时查看训练日志和进度
- 自动保存训练结果

### 3. 模型管理
- 一键查看所有训练好的模型
- 模型性能测试与评估
- 快速切换当前使用的模型
- 模型文件管理（删除、导出）

### 4. 数据集管理
- 可视化创建和管理数据集
- 支持图片和标签文件上传
- 自动生成YOLO格式配置文件
- 数据集格式验证

### 5. 使用指南
- 内置详细的使用教程
- 常见问题解答
- 参数调优建议

---

## 技术架构

```
YOLOStarter/
├── frontend/                 # Vue 3 前端应用
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 公共组件
│   │   ├── stores/          # 状态管理
│   │   └── api/             # API接口
│   └── package.json
├── unified_api_server.py     # 后端API服务 (端口 5000)
├── yolo_train_api.py         # 训练API服务 (端口 5004)
├── dataset_api.py            # 数据集API服务 (端口 5006)
├── test_yolo.py              # 测试API服务 (端口 5003)
├── start-frontend.bat        # 一键启动脚本
├── Test file/                # 训练/测试脚本
│   ├── train_yolo_generic.py
│   └── test_yolo_generic.py
├── yolo_models/              # 模型存储目录
└── datasets/                 # 数据集存储目录
```

### 技术栈

**前端**
- Vue 3 + TypeScript
- Element Plus UI组件库
- ECharts 数据可视化
- Pinia 状态管理
- Vite 构建工具

**后端**
- Python Flask API服务
- Ultralytics YOLO
- OpenCV 图像处理
- PyTorch 深度学习框架

---

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- CUDA（可选，用于GPU加速）

### 安装步骤

#### 第一步：安装 PyTorch（重要！）

PyTorch 需要根据您的系统配置选择合适的版本安装。

**1. 检查您的CUDA版本（如果有NVIDIA显卡）**

打开命令行执行：
```bash
nvidia-smi
```
在输出中找到 `CUDA Version` 一行，记下版本号。

**2. 选择对应的安装命令**

| 您的配置 | 安装命令 |
|---------|---------|
| **无显卡 / 仅CPU** | `pip install torch torchvision torchaudio` |
| **CUDA 11.8** | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118` |
| **CUDA 12.1** | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121` |
| **CUDA 12.4** | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124` |

**3. 验证安装**

```bash
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
```

> **提示**：如果您不确定自己的CUDA版本，建议先安装CPU版本，后续需要GPU加速时再重新安装对应版本。

**4. 官方安装指南**

更多版本请访问 PyTorch 官网：https://pytorch.org/get-started/locally/

---

#### 第二步：安装其他Python依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install ultralytics flask flask-cors opencv-python numpy matplotlib pyyaml
```

---

#### 第三步：安装前端依赖

```bash
cd frontend
npm install
```

---

#### 第四步：启动服务

**方式一：一键启动（推荐）**

双击运行 `start-frontend.bat`，将自动启动所有服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| Unified API Server | 5000 | 主API服务 |
| YOLO Test API | 5003 | 模型测试服务 |
| YOLO Train API | 5004 | 模型训练服务 |
| Dataset API | 5006 | 数据集管理服务 |
| Frontend Dev Server | 5173 | 前端开发服务器 |

**方式二：手动启动**

如需单独启动某个服务：

```bash
# 启动主API服务
python unified_api_server.py

# 启动训练服务
python yolo_train_api.py

# 启动数据集服务
python dataset_api.py

# 启动前端（新终端）
cd frontend
npm run dev
```

---

#### 第五步：访问应用

打开浏览器访问 `http://localhost:5173`

---

## 使用流程

```
准备数据集 → 配置训练参数 → 开始训练 → 测试模型 → 实时预测
     ↓            ↓            ↓          ↓          ↓
  上传图片     选择模型      查看日志   评估指标   摄像头/上传
  标注数据     设置轮数      监控进度   切换模型   导出报告
```

---

## 适合人群

- 零编程基础，想体验AI目标检测的爱好者
- 计算机视觉方向的学生和研究者
- 需要快速验证想法的开发者
- 想要学习YOLO模型的新手

---

## 项目特色

- **零代码操作**：全程图形化界面，无需编写代码
- **一键启动**：双击批处理文件即可启动所有服务
- **一键训练**：预设最佳参数，点击即可开始训练
- **实时反馈**：训练进度、日志实时展示
- **中文界面**：全中文界面，降低学习门槛
- **详细教程**：内置使用指南，手把手教学

---

## 许可证

Apache License 2.0

详见 [LICENSE](LICENSE) 文件。
