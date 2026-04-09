# -*- coding: utf-8 -*-
"""
================================================================================
通用YOLO检测模型测试脚本
测试训练好的YOLO模型在测试集上的检测性能
自动保存评估结果到EDocument文件夹
================================================================================

使用说明:
--------
必选参数:
    --model-path    YOLO模型路径 (.pt文件)
    --test-dir      测试数据目录路径

可选参数:
    --conf-threshold    置信度阈值 (默认: 0.25)
    --iou-threshold     IoU阈值 (默认: 0.5)
    --save-visualizations  是否保存可视化结果 (默认: False)

自动保存功能:
--------
测试完成后会自动在 EDocument 文件夹下创建评估结果目录:
- 文件夹命名格式: [模型名称]_[YYYYMMDD_HHMMSS]
- 包含内容:
  * evaluation_metrics.png - 可视化评估指标图表
  * evaluation_results.xlsx - Excel格式评估文档
  * visualizations/ - 原始可视化结果（如启用）

示例:
--------
# 基本使用
python test_yolo_generic.py --model-path yolo_models/train/weights/best.pt --test-dir data/test

# 完整配置
python test_yolo_generic.py \
    --model-path yolo_models/train/weights/best.pt \
    --test-dir data/test \
    --conf-threshold 0.3 \
    --iou-threshold 0.5 \
    --save-visualizations
================================================================================
"""

import os
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import argparse
from datetime import datetime
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).parent


def calculate_iou(box1, box2):
    """计算两个边界框的IoU"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0
    
    return inter_area / union_area


def yolo_to_xyxy(yolo_box, img_width, img_height):
    """将YOLO格式转换为xyxy格式"""
    x_center, y_center, w, h = yolo_box
    x1 = (x_center - w / 2) * img_width
    y1 = (y_center - h / 2) * img_height
    x2 = (x_center + w / 2) * img_width
    y2 = (y_center + h / 2) * img_height
    return [x1, y1, x2, y2]


def test_yolo_model(model_path, test_dir, conf_threshold=0.25, iou_threshold=0.5, save_visualizations=False):
    """
    测试YOLO模型
    
    Args:
        model_path: 模型路径
        test_dir: 测试数据目录
        conf_threshold: 置信度阈值
        iou_threshold: IoU阈值
        save_visualizations: 是否保存可视化结果
    """
    print("=" * 70)
    print("YOLO检测模型测试")
    print("=" * 70)
    print(f"模型路径: {model_path}")
    print(f"测试数据: {test_dir}")
    print(f"置信度阈值: {conf_threshold}")
    print(f"IoU阈值: {iou_threshold}")
    print("=" * 70)
    
    model = YOLO(str(model_path))
    
    image_dir = test_dir / "images"
    label_dir = test_dir / "labels"
    
    if not image_dir.exists():
        print(f"错误: 图像目录不存在 - {image_dir}")
        return
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    image_files = sorted([f for f in os.listdir(image_dir) 
                         if f.lower().endswith(image_extensions)])
    
    print(f"\n发现 {len(image_files)} 个测试图片")
    
    all_predictions = []
    all_ground_truths = []
    results_list = []
    
    tp = 0
    fp = 0
    fn = 0
    
    vis_dir = BASE_DIR / "test_yolo_visualizations"
    if save_visualizations:
        vis_dir.mkdir(exist_ok=True)
    
    for i, img_name in enumerate(image_files):
        label_name = os.path.splitext(img_name)[0] + '.txt'
        label_path = label_dir / label_name
        
        img_path = image_dir / img_name
        img = cv2.imread(str(img_path))
        
        if img is None:
            continue
        
        img_height, img_width = img.shape[:2]
        
        ground_truths = []
        if label_path.exists():
            with open(label_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        yolo_box = [float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])]
                        xyxy = yolo_to_xyxy(yolo_box, img_width, img_height)
                        ground_truths.append({
                            'class_id': class_id,
                            'bbox': xyxy,
                            'matched': False
                        })
        
        results = model(img, verbose=False, conf=conf_threshold)
        
        predictions = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for j in range(len(boxes)):
                bbox = boxes.xyxy[j].cpu().numpy()
                conf = boxes.conf[j].cpu().numpy()
                cls = boxes.cls[j].cpu().numpy() if boxes.cls is not None else 0
                predictions.append({
                    'bbox': bbox,
                    'confidence': conf,
                    'class_id': int(cls),
                    'matched': False
                })
        
        for pred in predictions:
            best_iou = 0
            best_gt = None
            
            for gt in ground_truths:
                if gt['matched']:
                    continue
                
                iou = calculate_iou(pred['bbox'], gt['bbox'])
                if iou > best_iou:
                    best_iou = iou
                    best_gt = gt
            
            if best_iou >= iou_threshold and best_gt is not None:
                pred['matched'] = True
                best_gt['matched'] = True
                tp += 1
            else:
                fp += 1
        
        for gt in ground_truths:
            if not gt['matched']:
                fn += 1
        
        results_list.append({
            'image': img_name,
            'predictions': len(predictions),
            'ground_truths': len(ground_truths),
            'matched': sum(1 for p in predictions if p['matched'])
        })
        
        if save_visualizations and i < 20:
            vis_img = img.copy()
            vis_img = cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB)
            
            fig, ax = plt.subplots(1, figsize=(12, 8))
            ax.imshow(vis_img)
            
            for gt in ground_truths:
                x1, y1, x2, y2 = gt['bbox']
                rect = patches.Rectangle(
                    (x1, y1), x2 - x1, y2 - y1,
                    linewidth=2, edgecolor='green', facecolor='none',
                    label='Ground Truth' if gt == ground_truths[0] else ''
                )
                ax.add_patch(rect)
            
            for pred in predictions:
                x1, y1, x2, y2 = pred['bbox']
                color = 'red' if not pred['matched'] else 'blue'
                rect = patches.Rectangle(
                    (x1, y1), x2 - x1, y2 - y1,
                    linewidth=2, edgecolor=color, facecolor='none',
                    linestyle='--',
                    label=f'Pred ({pred["confidence"]:.2f})' if pred == predictions[0] else ''
                )
                ax.add_patch(rect)
                ax.text(x1, y1 - 5, f'{pred["confidence"]:.2f}', 
                       color=color, fontsize=10, fontweight='bold')
            
            ax.set_title(f'{img_name}\nGT: {len(ground_truths)}, Pred: {len(predictions)}, Matched: {sum(1 for p in predictions if p["matched"])}')
            ax.axis('off')
            
            plt.tight_layout()
            plt.savefig(vis_dir / f'{os.path.splitext(img_name)[0]}_result.png', dpi=100, bbox_inches='tight')
            plt.close()
        
        if (i + 1) % 50 == 0:
            print(f"已处理: {i + 1}/{len(image_files)}")
            current_precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            current_recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            current_f1 = 2 * current_precision * current_recall / (current_precision + current_recall) if (current_precision + current_recall) > 0 else 0
            print(f"  当前指标 - Precision: {current_precision:.4f}, Recall: {current_recall:.4f}, F1: {current_f1:.4f}")
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print("\n" + "=" * 70)
    print("测试结果")
    print("=" * 70)
    print(f"总图片数: {len(image_files)}")
    print(f"真阳性 (TP): {tp}")
    print(f"假阳性 (FP): {fp}")
    print(f"假阴性 (FN): {fn}")
    print(f"\n精确率 (Precision): {precision:.4f} ({precision*100:.2f}%)")
    print(f"召回率 (Recall): {recall:.4f} ({recall*100:.2f}%)")
    print(f"F1分数: {f1:.4f} ({f1*100:.2f}%)")
    
    print("\n" + "=" * 70)
    print("详细结果")
    print("=" * 70)
    print(f"\n{'图片名称':&lt;40} {'预测数':&lt;8} {'真实数':&lt;8} {'匹配数':&lt;8}")
    print("-" * 70)
    for r in results_list[:20]:
        print(f"{r['image']:&lt;40} {r['predictions']:&lt;8} {r['ground_truths']:&lt;8} {r['matched']:&lt;8}")
    if len(results_list) &gt; 20:
        print(f"... 还有 {len(results_list) - 20} 条结果")
    
    if save_visualizations:
        print(f"\n可视化结果已保存到: {vis_dir}")
    
    results_dict = {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'total_images': len(image_files),
        'results_list': results_list,
        'all_predictions': all_predictions,
        'all_ground_truths': all_ground_truths
    }
    
    save_yolo_evaluation_results(
        results_dict,
        model_path,
        image_files,
        vis_dir,
        save_visualizations
    )
    
    return results_dict


def save_yolo_evaluation_results(results, model_path, image_files, vis_dir, save_visualizations):
    """
    保存YOLO模型评估结果到文件夹
    
    Args:
        results: 评估结果字典
        model_path: 模型路径
        image_files: 图像文件列表
        vis_dir: 可视化目录
        save_visualizations: 是否保存可视化
    """
    try:
        BASE_DIR = Path(__file__).parent
        EDOCUMENT_DIR = BASE_DIR / "EDocument"
        EDOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
        
        model_name = Path(model_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_folder = EDOCUMENT_DIR / f"{model_name}_{timestamp}"
        result_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\n创建评估结果文件夹: {result_folder}")
        
        plot_yolo_metrics(results, result_folder)
        save_yolo_excel(results, result_folder)
        
        if save_visualizations and vis_dir.exists():
            import shutil
            vis_dest = result_folder / "visualizations"
            if vis_dest.exists():
                shutil.rmtree(vis_dest)
            shutil.copytree(vis_dir, vis_dest)
            print(f"可视化结果已复制到: {vis_dest}")
        
        print(f"评估结果已成功保存到: {result_folder}")
        
    except Exception as e:
        print(f"保存评估结果时出错: {e}")


def plot_yolo_metrics(results, output_dir):
    """
    绘制YOLO评估指标图表
    
    Args:
        results: 评估结果字典
        output_dir: 输出目录
    """
    try:
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        precision = results['precision']
        recall = results['recall']
        f1 = results['f1']
        tp = results['tp']
        fp = results['fp']
        fn = results['fn']
        
        metrics = ['精确率', '召回率', 'F1分数']
        values = [precision, recall, f1]
        colors = ['#3498db', '#2ecc71', '#e74c3c']
        axes[0, 0].bar(metrics, values, color=colors, alpha=0.7)
        axes[0, 0].set_ylim([0, 1])
        axes[0, 0].set_title('核心评估指标', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('数值', fontsize=12)
        for i, v in enumerate(values):
            axes[0, 0].text(i, v + 0.02, f'{v:.4f}', ha='center', fontsize=10, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3, axis='y')
        
        categories = ['真阳性 (TP)', '假阳性 (FP)', '假阴性 (FN)']
        counts = [tp, fp, fn]
        colors2 = ['#27ae60', '#e67e22', '#c0392b']
        axes[0, 1].bar(categories, counts, color=colors2, alpha=0.7)
        axes[0, 1].set_title('检测统计', fontsize=14, fontweight='bold')
        axes[0, 1].set_ylabel('数量', fontsize=12)
        for i, v in enumerate(counts):
            axes[0, 1].text(i, v + max(counts)*0.02, f'{v}', ha='center', fontsize=10, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        if results.get('results_list'):
            results_list = results['results_list']
            predictions_per_image = [r['predictions'] for r in results_list]
            gts_per_image = [r['ground_truths'] for r in results_list]
            matched_per_image = [r['matched'] for r in results_list]
            
            axes[1, 0].plot(predictions_per_image, label='预测数', alpha=0.7)
            axes[1, 0].plot(gts_per_image, label='真实数', alpha=0.7)
            axes[1, 0].plot(matched_per_image, label='匹配数', alpha=0.7)
            axes[1, 0].set_title('每图片检测统计', fontsize=14, fontweight='bold')
            axes[1, 0].set_xlabel('图片索引', fontsize=12)
            axes[1, 0].set_ylabel('数量', fontsize=12)
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            detection_counts = pd.DataFrame({
                '预测数': predictions_per_image,
                '真实数': gts_per_image,
                '匹配数': matched_per_image
            })
            axes[1, 1].boxplot([detection_counts['预测数'], detection_counts['真实数'], detection_counts['匹配数']], 
                               labels=['预测数', '真实数', '匹配数'])
            axes[1, 1].set_title('检测数量分布', fontsize=14, fontweight='bold')
            axes[1, 1].set_ylabel('数量', fontsize=12)
            axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'evaluation_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"评估指标图表已保存: {output_dir / 'evaluation_metrics.png'}")
        
    except Exception as e:
        print(f"绘制YOLO评估指标图表时出错: {e}")


def save_yolo_excel(results, output_dir):
    """
    保存YOLO评估结果到Excel文件
    
    Args:
        results: 评估结果字典
        output_dir: 输出目录
    """
    try:
        excel_path = output_dir / 'evaluation_results.xlsx'
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            summary_data = {
                '指标': ['总图片数', '真阳性 (TP)', '假阳性 (FP)', '假阴性 (FN)', 
                        '精确率 (Precision)', '召回率 (Recall)', 'F1分数'],
                '数值': [
                    results['total_images'],
                    results['tp'],
                    results['fp'],
                    results['fn'],
                    f"{results['precision']:.6f} ({results['precision']*100:.2f}%)",
                    f"{results['recall']:.6f} ({results['recall']*100:.2f}%)",
                    f"{results['f1']:.6f} ({results['f1']*100:.2f}%)"
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='评估摘要', index=False)
            
            if results.get('results_list'):
                df_details = pd.DataFrame(results['results_list'])
                df_details.to_excel(writer, sheet_name='详细结果', index=False)
        
        print(f"Excel评估文档已保存: {excel_path}")
        
    except Exception as e:
        print(f"保存YOLO Excel文件时出错: {e}")


def main():
    parser = argparse.ArgumentParser(description='通用YOLO检测模型测试')
    
    parser.add_argument('--model-path', type=str, required=True,
                        help='YOLO模型路径（必选）')
    parser.add_argument('--test-dir', type=str, required=True,
                        help='测试数据目录路径（必选）')
    parser.add_argument('--conf-threshold', type=float, default=0.25,
                        help='置信度阈值（默认: 0.25）')
    parser.add_argument('--iou-threshold', type=float, default=0.5,
                        help='IoU阈值（默认: 0.5）')
    parser.add_argument('--save-visualizations', action='store_true',
                        help='是否保存可视化结果（默认: False）')
    
    args = parser.parse_args()
    
    model_path = Path(args.model_path)
    if not model_path.is_absolute():
        model_path = BASE_DIR / model_path
    
    test_dir = Path(args.test_dir)
    if not test_dir.is_absolute():
        test_dir = BASE_DIR / test_dir
    
    if not model_path.exists():
        print(f"错误: 模型文件不存在 - {model_path}")
        print("请先训练YOLO模型或检查模型路径")
        return
    
    if not test_dir.exists():
        print(f"错误: 测试数据目录不存在 - {test_dir}")
        return
    
    results = test_yolo_model(
        model_path=model_path,
        test_dir=test_dir,
        conf_threshold=args.conf_threshold,
        iou_threshold=args.iou_threshold,
        save_visualizations=args.save_visualizations
    )
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
