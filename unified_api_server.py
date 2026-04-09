"""
整合API服务器
提供模型管理和YOLO目标检测功能
"""

import os
import cv2
import json
import yaml
import threading
import time
import sys
import base64
import numpy as np
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO

try:
    from https_server import run_https_server
    HAS_HTTPS_SUPPORT = True
except ImportError:
    HAS_HTTPS_SUPPORT = False

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

try:
    from evaluation_exporter import export_yolo_evaluation
    HAS_EVALUATION_EXPORTER = True
except ImportError:
    HAS_EVALUATION_EXPORTER = False

app = Flask(__name__)
CORS(app)

YOLO_MODELS_DIR = BASE_DIR / 'yolo_models'
DATA_DIR = BASE_DIR / 'data（OAD）'

test_tasks = {}

test_results = {}

def check_has_yaml(dataset_dir: Path) -> bool:
    for filename in dataset_dir.iterdir():
        if filename.is_file():
            name_lower = filename.name.lower()
            if name_lower == 'data.yaml' or name_lower == 'data.yml':
                return True
    return False

TEST_RESULTS_FILE = BASE_DIR / 'test_results.json'
CURRENT_MODELS_FILE = BASE_DIR / 'current_models.json'

def load_test_results():
    global test_results
    if TEST_RESULTS_FILE.exists():
        try:
            with open(TEST_RESULTS_FILE, 'r', encoding='utf-8') as f:
                test_results = json.load(f)
        except Exception as e:
            print(f"加载测试结果失败: {e}")
            test_results = {}

def save_test_results():
    try:
        with open(TEST_RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存测试结果失败: {e}")

def load_current_models():
    global current_yolo_model_name
    if CURRENT_MODELS_FILE.exists():
        try:
            with open(CURRENT_MODELS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_yolo_model_name = data.get('yolo_model')
                print(f"加载当前模型状态: YOLO={current_yolo_model_name}")
        except Exception as e:
            print(f"加载当前模型状态失败: {e}")

def save_current_models():
    try:
        with open(CURRENT_MODELS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'yolo_model': current_yolo_model_name
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存当前模型状态失败: {e}")

load_test_results()
load_current_models()

yolo_model = None
current_yolo_model_name = None


def load_predict_models():
    global yolo_model, current_yolo_model_name

    if yolo_model is None:
        yolo_model_name = current_yolo_model_name or 'train4'
        yolo_model_path = YOLO_MODELS_DIR / yolo_model_name / 'weights' / 'best.pt'
        if yolo_model_path.exists():
            print(f"加载YOLO模型: {yolo_model_path}")
            yolo_model = YOLO(str(yolo_model_path))
            current_yolo_model_name = yolo_model_name
            print("YOLO模型加载完成")
        else:
            default_yolo_path = YOLO_MODELS_DIR / 'train4' / 'weights' / 'best.pt'
            if default_yolo_path.exists():
                print(f"加载默认YOLO模型: {default_yolo_path}")
                yolo_model = YOLO(str(default_yolo_path))
                current_yolo_model_name = 'train4'
                print("YOLO模型加载完成")


def get_yolo_models():
    models = []

    if not YOLO_MODELS_DIR.exists():
        return models

    for train_dir in YOLO_MODELS_DIR.iterdir():
        if not train_dir.is_dir():
            continue

        weights_dir = train_dir / 'weights'
        if not weights_dir.exists():
            continue

        best_model = weights_dir / 'best.pt'
        if not best_model.exists():
            continue

        args_file = train_dir / 'args.yaml'
        epochs = 100

        if args_file.exists():
            try:
                with open(args_file, 'r', encoding='utf-8') as f:
                    args = yaml.safe_load(f)
                    epochs = args.get('epochs', 100)
            except:
                pass

        created_time = datetime.fromtimestamp(train_dir.stat().st_mtime)

        model = {
            'id': f'yolo_{train_dir.name}',
            'name': f'YOLO检测模型-{train_dir.name}',
            'type': 'YOLO',
            'path': str(best_model.relative_to(BASE_DIR)),
            'createdAt': created_time.isoformat(),
            'epochs': epochs,
            'testing': False,
            'tested': False,
            'testProgress': 0,
            'testProgressText': '',
            'testStatus': '',
            'metrics': None
        }
        models.append(model)

    return sorted(models, key=lambda x: x['createdAt'], reverse=True)


def test_yolo_model_real(model_path: str, task_id: str):
    try:
        from ultralytics import YOLO
        import torch
        import tempfile
        import shutil

        model = YOLO(model_path)
        num_classes = len(model.names)

        test_images_dir = DATA_DIR / 'test' / 'images'
        test_labels_dir = DATA_DIR / 'test' / 'labels'

        if not test_images_dir.exists() or not test_labels_dir.exists():
            raise Exception("测试数据不存在")

        temp_dir = Path(tempfile.mkdtemp(prefix="yolo_test_"))
        try:
            temp_images = temp_dir / 'images'
            temp_labels = temp_dir / 'labels'
            temp_images.mkdir(parents=True, exist_ok=True)
            temp_labels.mkdir(parents=True, exist_ok=True)

            for img_file in test_images_dir.glob('*.jpg'):
                shutil.copy(img_file, temp_images / img_file.name)

            if num_classes == 1:
                for label_file in test_labels_dir.glob('*.txt'):
                    with open(label_file, 'r') as f:
                        lines = f.readlines()
                    new_lines = []
                    for line in lines:
                        parts = line.strip().split()
                        if parts:
                            parts[0] = '0'
                            new_lines.append(' '.join(parts) + '\n')
                    if new_lines:
                        with open(temp_labels / label_file.name, 'w') as f:
                            f.writelines(new_lines)

            data_yaml_content = f"""path: {temp_dir.as_posix()}
train: images
val: images
test: images

nc: {num_classes}
names: {list(model.names.values()) if num_classes > 1 else ['tube']}
"""
            yaml_path = temp_dir / 'data.yaml'
            yaml_path.write_text(data_yaml_content, encoding='utf-8')

            test_tasks[task_id]['progress'] = 20
            test_tasks[task_id]['status'] = 'running'
            test_tasks[task_id]['message'] = '正在执行模型推理...'

            device = '0' if torch.cuda.is_available() else 'cpu'
            results = model.val(
                data=str(yaml_path),
                split='test',
                conf=0.25,
                iou=0.5,
                device=device,
                plots=False,
                save=False,
                verbose=False,
            )

            test_tasks[task_id]['progress'] = 80
            test_tasks[task_id]['message'] = '正在计算评估指标...'

            metrics = {
                'accuracy': float(results.box.map50),
                'precision': float(results.box.mp),
                'recall': float(results.box.mr),
                'f1Score': float(results.box.map50),
            }

            if hasattr(results.box, 'maps') and results.box.maps is not None:
                metrics['r2'] = float(results.box.maps.mean()) if hasattr(results.box.maps, 'mean') else float(results.box.maps)

            test_tasks[task_id]['progress'] = 90
            test_tasks[task_id]['message'] = '正在导出评估结果...'

            model_path_obj = Path(model_path)
            model_name = model_path_obj.parent.parent.name

            if HAS_EVALUATION_EXPORTER:
                try:
                    export_result = export_yolo_evaluation(model_name, metrics)
                    if export_result.get('success'):
                        test_tasks[task_id]['export_info'] = export_result
                        test_tasks[task_id]['message'] = f'测试完成，结果已保存至: {export_result.get("folder_path")}'
                    else:
                        test_tasks[task_id]['message'] = f'测试完成，但导出失败: {export_result.get("error")}'
                except Exception as export_error:
                    print(f"导出评估结果失败: {export_error}")
                    test_tasks[task_id]['message'] = '测试完成'
            else:
                test_tasks[task_id]['message'] = '测试完成'

            test_tasks[task_id]['progress'] = 100
            test_tasks[task_id]['status'] = 'completed'
            test_tasks[task_id]['metrics'] = metrics

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    except Exception as e:
        test_tasks[task_id]['status'] = 'failed'
        test_tasks[task_id]['message'] = f'测试失败: {str(e)}'
        test_tasks[task_id]['error'] = str(e)


def detect_with_yolo(img):
    """使用YOLO模型直接检测图像，返回检测结果"""
    if yolo_model is None:
        return None, None, "YOLO模型未加载"

    results = yolo_model(img, verbose=False)

    if len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
        return None, None, "未检测到目标"

    boxes = results[0].boxes
    confidences = boxes.conf.cpu().numpy()
    max_idx = confidences.argmax()
    confidence = float(confidences[max_idx])

    bbox = boxes.xyxy[max_idx].cpu().numpy()
    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

    cls_id = int(boxes.cls[max_idx].item())
    class_name = yolo_model.names.get(cls_id, str(cls_id))

    detection_result = {
        'class_id': cls_id,
        'class_name': class_name,
        'confidence': confidence,
        'bbox': [x1, y1, x2, y2]
    }

    return detection_result, confidence, None


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': yolo_model is not None
    })


@app.route('/api/models', methods=['GET'])
def get_models():
    yolo_models = get_yolo_models()

    model_type = request.args.get('type')
    if model_type == 'yolo':
        return jsonify({
            'success': True,
            'data': yolo_models
        })
    else:
        return jsonify({
            'success': True,
            'data': yolo_models
        })


@app.route('/api/models/<model_id>/test', methods=['POST'])
def test_model(model_id):
    try:
        if model_id.startswith('yolo_'):
            train_dir_name = model_id.replace('yolo_', '')
            model_path = YOLO_MODELS_DIR / train_dir_name / 'weights' / 'best.pt'
        else:
            return jsonify({'success': False, 'message': '无效的模型ID'}), 400

        if not model_path.exists():
            return jsonify({'success': False, 'message': '模型文件不存在'}), 404

        task_id = f"{model_id}_{int(time.time())}"
        test_tasks[task_id] = {
            'model_id': model_id,
            'model_type': 'yolo',
            'model_path': str(model_path),
            'progress': 0,
            'status': 'pending',
            'message': '正在初始化测试环境...',
            'metrics': None,
            'error': None,
            'created_at': datetime.now().isoformat()
        }

        thread = threading.Thread(target=test_yolo_model_real, args=(str(model_path), task_id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': '测试任务已启动',
            'task_id': task_id
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'启动测试失败: {str(e)}'}), 500


@app.route('/api/models/test/<task_id>/progress', methods=['GET'])
def get_test_progress(task_id):
    if task_id not in test_tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404

    task = test_tasks[task_id]
    return jsonify({
        'success': True,
        'data': {
            'progress': task['progress'],
            'status': task['status'],
            'message': task['message'],
            'metrics': task['metrics'],
            'error': task['error']
        }
    })


@app.route('/api/models/<model_id>', methods=['DELETE'])
def delete_model(model_id):
    if model_id.startswith('yolo_'):
        train_dir_name = model_id.replace('yolo_', '')
        train_dir = YOLO_MODELS_DIR / train_dir_name
        if train_dir.exists():
            import shutil
            shutil.rmtree(train_dir)
            if model_id in test_results:
                del test_results[model_id]
                save_test_results()
            return jsonify({'success': True, 'message': f'YOLO模型 {model_id} 已删除'})

    return jsonify({'success': False, 'message': '模型不存在'}), 404


@app.route('/api/models/refresh', methods=['POST'])
def refresh_models():
    return jsonify({
        'success': True,
        'message': '模型列表已刷新'
    })


@app.route('/api/models/test-results', methods=['GET'])
def get_test_results():
    return jsonify({
        'success': True,
        'data': test_results
    })


@app.route('/api/models/test-results/<model_id>', methods=['POST'])
def save_test_result(model_id):
    try:
        data = request.get_json() or {}
        test_results[model_id] = {
            'metrics': data.get('metrics', {}),
            'timestamp': datetime.now().isoformat()
        }
        save_test_results()
        return jsonify({
            'success': True,
            'message': '测试结果已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存测试结果失败: {str(e)}'
        }), 500


@app.route('/api/models/test-results/<model_id>', methods=['DELETE'])
def delete_test_result(model_id):
    if model_id in test_results:
        del test_results[model_id]
        save_test_results()
        return jsonify({
            'success': True,
            'message': '测试结果已删除'
        })
    return jsonify({
        'success': False,
        'message': '测试结果不存在'
    }), 404


@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    global yolo_model, current_yolo_model_name

    try:
        data = request.get_json() or {}
        yolo_model_name = data.get('yolo_model')

        if yolo_model_name:
            yolo_model_path = YOLO_MODELS_DIR / yolo_model_name / 'weights' / 'best.pt'
            if not yolo_model_path.exists():
                return jsonify({
                    'success': False,
                    'message': f'YOLO模型不存在: {yolo_model_name}'
                }), 400

            yolo_model = YOLO(str(yolo_model_path))
            current_yolo_model_name = yolo_model_name
            print(f"已切换YOLO模型: {yolo_model_path}")

        save_current_models()

        return jsonify({
            'success': True,
            'message': '模型切换成功',
            'current_yolo_model': current_yolo_model_name
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'切换模型失败: {str(e)}'
        }), 500


@app.route('/api/models/current', methods=['GET'])
def get_current_models():
    return jsonify({
        'success': True,
        'data': {
            'yolo_model': current_yolo_model_name
        }
    })


@app.route('/api/predict', methods=['POST'])
def predict():
    """YOLO检测API - 上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传图片文件'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400

        allowed_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'message': f'不支持的文件格式，支持: {", ".join(allowed_extensions)}'
            }), 400

        file_bytes = file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({
                'success': False,
                'message': '无法解析图片'
            }), 400

        detection, confidence, error = detect_with_yolo(img)

        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400

        return jsonify({
            'success': True,
            'data': {
                'detection': detection,
                'confidence': round(confidence, 4),
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        }), 500


@app.route('/api/predict/base64', methods=['POST'])
def predict_base64():
    """YOLO检测API - Base64"""
    try:
        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'message': '未提供图片数据'
            }), 400

        image_data = data['image']

        if ',' in image_data:
            image_data = image_data.split(',')[1]

        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({
                'success': False,
                'message': '无法解析图片'
            }), 400

        detection, confidence, error = detect_with_yolo(img)

        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400

        return jsonify({
            'success': True,
            'data': {
                'detection': detection,
                'confidence': round(confidence, 4),
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        }), 500


@app.route('/api/predict/batch', methods=['POST'])
def predict_batch():
    """批量YOLO检测API"""
    try:
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传图片文件'
            }), 400

        files = request.files.getlist('files')

        if not files:
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400

        results = []
        successful = 0
        failed = 0

        for file in files:
            try:
                file_bytes = file.read()
                nparr = np.frombuffer(file_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if img is None:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'message': '无法解析图片'
                    })
                    failed += 1
                    continue

                detection, confidence, error = detect_with_yolo(img)

                if error:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'message': error
                    })
                    failed += 1
                else:
                    results.append({
                        'filename': file.filename,
                        'success': True,
                        'detection': detection,
                        'confidence': round(confidence, 4)
                    })
                    successful += 1

            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'message': str(e)
                })
                failed += 1

        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'total': len(files),
                'successful': successful,
                'failed': failed
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量检测失败: {str(e)}'
        }), 500


@app.route('/api/datasets/export', methods=['POST'])
def export_dataset():
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400

        dataset_name = data.get('name', f'dataset_{int(time.time())}')
        train_images = data.get('trainImages', [])
        train_labels = data.get('trainLabels', [])
        test_images = data.get('testImages', [])
        test_labels = data.get('testLabels', [])
        yaml_data = data.get('yaml')
        split_ratio = data.get('splitRatio', {'train': 0.8, 'val': 0.2})

        all_images = train_images + test_images
        if not all_images:
            return jsonify({
                'success': False,
                'message': '数据集没有图片'
            }), 400

        export_dir = BASE_DIR / 'exported_datasets' / dataset_name
        if export_dir.exists():
            import shutil
            shutil.rmtree(export_dir)

        train_images_dir = export_dir / 'train' / 'images'
        train_labels_dir = export_dir / 'train' / 'labels'
        val_images_dir = export_dir / 'valid' / 'images'
        val_labels_dir = export_dir / 'valid' / 'labels'
        test_images_dir = export_dir / 'test' / 'images'
        test_labels_dir = export_dir / 'test' / 'labels'

        train_images_dir.mkdir(parents=True, exist_ok=True)
        train_labels_dir.mkdir(parents=True, exist_ok=True)
        val_images_dir.mkdir(parents=True, exist_ok=True)
        val_labels_dir.mkdir(parents=True, exist_ok=True)
        test_images_dir.mkdir(parents=True, exist_ok=True)
        test_labels_dir.mkdir(parents=True, exist_ok=True)

        train_label_map = {}
        for label in train_labels:
            train_label_map[label['name']] = label['content']

        test_label_map = {}
        for label in test_labels:
            test_label_map[label['name']] = label['content']

        import random

        saved_train_images = 0
        saved_train_labels = 0
        saved_val_images = 0
        saved_val_labels = 0
        saved_test_images = 0
        saved_test_labels = 0

        if train_images:
            indices = list(range(len(train_images)))
            random.shuffle(indices)
            train_count = int(len(train_images) * split_ratio.get('train', 0.8))

            for i, idx in enumerate(indices):
                image = train_images[idx]
                image_name = image['name']
                image_data = image['data']

                if ',' in image_data:
                    image_data = image_data.split(',')[1]

                image_bytes = base64.b64decode(image_data)

                label_name = os.path.splitext(image_name)[0] + '.txt'
                label_content = train_label_map.get(label_name, '')

                if i < train_count:
                    image_path = train_images_dir / image_name
                    label_path = train_labels_dir / label_name
                    saved_train_images += 1
                    if label_content:
                        saved_train_labels += 1
                else:
                    image_path = val_images_dir / image_name
                    label_path = val_labels_dir / label_name
                    saved_val_images += 1
                    if label_content:
                        saved_val_labels += 1

                with open(image_path, 'wb') as f:
                    f.write(image_bytes)

                if label_content:
                    with open(label_path, 'w', encoding='utf-8') as f:
                        f.write(label_content)

        for image in test_images:
            image_name = image['name']
            image_data = image['data']

            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)

            label_name = os.path.splitext(image_name)[0] + '.txt'
            label_content = test_label_map.get(label_name, '')

            image_path = test_images_dir / image_name
            label_path = test_labels_dir / label_name

            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            saved_test_images += 1

            if label_content:
                with open(label_path, 'w', encoding='utf-8') as f:
                    f.write(label_content)
                saved_test_labels += 1

        if yaml_data:
            classes = yaml_data.get('classes', ['tube'])
            nc = len(classes)

            processed_classes = []
            for cls in classes:
                try:
                    if '.' in str(cls):
                        processed_classes.append(float(cls))
                    else:
                        processed_classes.append(int(cls))
                except (ValueError, TypeError):
                    processed_classes.append(cls)

            names_str = '[' + ', '.join(str(c) for c in processed_classes) + ']'

            yaml_content = f"""path: {export_dir.as_posix()}
train: train/images
val: valid/images
test: test/images

nc: {nc}
names: {names_str}
"""
            yaml_path = export_dir / 'data.yaml'
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

        return jsonify({
            'success': True,
            'message': f'数据集导出成功',
            'data': {
                'path': str(export_dir.relative_to(BASE_DIR)),
                'train_images': saved_train_images,
                'train_labels': saved_train_labels,
                'val_images': saved_val_images,
                'val_labels': saved_val_labels,
                'test_images': saved_test_images,
                'test_labels': saved_test_labels,
                'yaml_created': yaml_data is not None
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'导出数据集失败: {str(e)}'
        }), 500


@app.route('/api/datasets/list', methods=['GET'])
def list_datasets():
    try:
        datasets = []

        export_dir = BASE_DIR / 'exported_datasets'
        if export_dir.exists():
            for dataset_dir in export_dir.iterdir():
                if not dataset_dir.is_dir():
                    continue

                train_images = dataset_dir / 'train' / 'images'
                val_images = dataset_dir / 'vaild' / 'images'
                test_images = dataset_dir / 'test' / 'images'

                train_count = len(list(train_images.glob('*'))) if train_images.exists() else 0
                val_count = len(list(val_images.glob('*'))) if val_images.exists() else 0
                test_count = len(list(test_images.glob('*'))) if test_images.exists() else 0

                datasets.append({
                    'name': dataset_dir.name,
                    'path': str(dataset_dir.relative_to(BASE_DIR)),
                    'train_images': train_count,
                    'val_images': val_count,
                    'test_images': test_count,
                    'has_yaml': check_has_yaml(dataset_dir),
                    'created_at': datetime.fromtimestamp(dataset_dir.stat().st_mtime).isoformat()
                })

        datasets_dir = BASE_DIR / 'datasets'
        if datasets_dir.exists():
            for dataset_dir in datasets_dir.iterdir():
                if not dataset_dir.is_dir():
                    continue

                info_file = dataset_dir / 'info.json'
                if not info_file.exists():
                    continue

                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                except Exception:
                    continue

                train_images = dataset_dir / 'train' / 'images'
                val_images = dataset_dir / 'valid' / 'images'
                test_images = dataset_dir / 'test' / 'images'

                train_count = len(list(train_images.glob('*'))) if train_images.exists() else 0
                val_count = len(list(val_images.glob('*'))) if val_images.exists() else 0
                test_count = len(list(test_images.glob('*'))) if test_images.exists() else 0

                datasets.append({
                    'name': info.get('name', dataset_dir.name),
                    'path': str(dataset_dir.relative_to(BASE_DIR)),
                    'train_images': train_count,
                    'val_images': val_count,
                    'test_images': test_count,
                    'has_yaml': check_has_yaml(dataset_dir),
                    'created_at': info.get('createTime', datetime.fromtimestamp(dataset_dir.stat().st_mtime).isoformat())
                })

        datasets.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({
            'success': True,
            'data': datasets
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据集列表失败: {str(e)}'
        }), 500


@app.route('/api/datasets/<path:dataset_path>', methods=['DELETE'])
def delete_dataset(dataset_path):
    try:
        dataset_dir = BASE_DIR / dataset_path

        if not dataset_dir.exists():
            return jsonify({
                'success': False,
                'message': '数据集不存在'
            }), 404

        import shutil
        shutil.rmtree(dataset_dir)

        return jsonify({
            'success': True,
            'message': f'数据集 {dataset_path} 已删除'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除数据集失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 70)
    print("整合API服务器")
    print("=" * 70)
    print(f"YOLO模型目录: {YOLO_MODELS_DIR}")
    print("=" * 70)
    print("API接口:")
    print("  GET  /api/health              - 健康检查")
    print("  GET  /api/models              - 获取模型列表")
    print("  POST /api/models/<id>/test    - 测试模型")
    print("  GET  /api/models/test/<id>    - 获取测试进度")
    print("  DELETE /api/models/<id>       - 删除模型")
    print("  POST /api/models/refresh      - 刷新模型列表")
    print("  POST /api/predict             - 单张图片检测")
    print("  POST /api/predict/base64      - Base64图片检测")
    print("  POST /api/predict/batch       - 批量图片检测")
    print("  POST /api/datasets/export     - 导出前端数据集")
    print("  GET  /api/datasets/list       - 获取数据集列表")
    print("  DELETE /api/datasets/<path>   - 删除数据集")
    print("=" * 70)

    load_predict_models()

    if HAS_HTTPS_SUPPORT:
        run_https_server(app, host='0.0.0.0', port=5000, debug=False)
    else:
        print("服务器启动在 http://localhost:5000")
        print("=" * 70)
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
