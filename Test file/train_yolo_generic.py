"""
================================================================================
通用YOLO目标检测模型训练脚本
================================================================================

使用说明:
--------
必选参数:
    --data-yaml    数据配置YAML文件路径

可选参数:
    --model-name    预训练模型名称 (默认: yolov8n.pt)
    --epochs        训练轮数 (默认: 100)
    --batch         批次大小 (默认: 16)
    --imgsz         输入图像大小 (默认: 640)
    --device        设备 (0, 1, 2... 或 cpu, 默认: 0)
    --project       项目保存目录 (默认: yolo_models)
    --name          实验名称 (默认: train)
    --patience      早停耐心值 (默认: 20)
    --save-period   模型保存周期 (-1表示只保存最佳和最后, 默认: -1)

示例:
--------
# 基本使用
python train_yolo_generic.py --data-yaml data/bread.yaml

# 完整配置
python train_yolo_generic.py \
    --data-yaml data/bread.yaml \
    --model-name yolov8s.pt \
    --epochs 200 \
    --batch 32 \
    --imgsz 640 \
    --device 0 \
    --project yolo_models \
    --name tube_detect \
    --patience 30 \
    --save-period 10
================================================================================
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import argparse


def train_yolo(
    data_yaml: str,
    model_name: str = "yolov8n.pt",
    epochs: int = 100,
    batch: int = 16,
    imgsz: int = 640,
    device: str = "0",
    project: str = None,
    name: str = "train",
    patience: int = 20,
    save_period: int = -1,
):
    """
    训练YOLO模型
    
    Args:
        data_yaml: 数据配置文件路径
        model_name: 预训练模型名称
        epochs: 训练轮数
        batch: 批次大小
        imgsz: 输入图像大小
        device: 设备 (0, 1, 2... 或 cpu)
        project: 项目保存目录
        name: 实验名称
        patience: 早停耐心值
        save_period: 模型保存周期 (-1表示只保存最佳和最后)
    """
    print("=" * 60)
    print("YOLO模型训练")
    print("=" * 60)
    print(f"数据配置: {data_yaml}")
    print(f"基础模型: {model_name}")
    print(f"训练轮数: {epochs}")
    print(f"批次大小: {batch}")
    print(f"图像大小: {imgsz}")
    print(f"设备: {device}")
    print("=" * 60)
    
    if torch.cuda.is_available():
        print(f"GPU可用: {torch.cuda.get_device_name(0)}")
        print(f"GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("GPU不可用，使用CPU训练")
    
    model = YOLO(model_name)
    
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=project,
        name=name,
        patience=patience,
        save_period=save_period,
        verbose=True,
        exist_ok=True,
    )
    
    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='通用YOLO目标检测模型训练')
    
    parser.add_argument('--data-yaml', type=str, required=True,
                        help='数据配置YAML文件路径（必选）')
    parser.add_argument('--model-name', type=str, default="yolov8n.pt",
                        help='预训练模型名称（默认: yolov8n.pt）')
    parser.add_argument('--epochs', type=int, default=100,
                        help='训练轮数（默认: 100）')
    parser.add_argument('--batch', type=int, default=16,
                        help='批次大小（默认: 16）')
    parser.add_argument('--imgsz', type=int, default=640,
                        help='输入图像大小（默认: 640）')
    parser.add_argument('--device', type=str, default="0",
                        help='设备（0, 1, 2... 或 cpu, 默认: 0）')
    parser.add_argument('--project', type=str, default="yolo_models",
                        help='项目保存目录（默认: yolo_models）')
    parser.add_argument('--name', type=str, default="train",
                        help='实验名称（默认: train）')
    parser.add_argument('--patience', type=int, default=20,
                        help='早停耐心值（默认: 20）')
    parser.add_argument('--save-period', type=int, default=-1,
                        help='模型保存周期（-1表示只保存最佳和最后, 默认: -1）')
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    
    data_yaml_path = Path(args.data_yaml)
    if not data_yaml_path.is_absolute():
        data_yaml_path = base_dir / data_yaml_path
    
    project_path = Path(args.project)
    if not project_path.is_absolute():
        project_path = base_dir / project_path
    
    results = train_yolo(
        data_yaml=str(data_yaml_path),
        model_name=args.model_name,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        project=str(project_path),
        name=args.name,
        patience=args.patience,
        save_period=args.save_period,
    )
    
    print("\n模型保存位置:", project_path / args.name / "weights")


if __name__ == "__main__":
    main()
