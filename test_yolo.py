"""
YOLO模型测试API服务
提供模型上传和评估接口
支持流式输出评估过程
不保存任何文件到磁盘
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import tempfile
import shutil
import io
import sys
import json
import threading
import queue
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import numpy as np

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

try:
    from https_server import run_https_server
    HAS_HTTPS_SUPPORT = True
except ImportError:
    HAS_HTTPS_SUPPORT = False

app = Flask(__name__)
CORS(app)

DEFAULT_DATA_DIR = BASE_DIR / "data" / "test"

def find_test_dir(base_path: Path) -> Path | None:
    """查找测试目录，支持 test、val、vaild 目录名"""
    for dir_name in ['test', 'val', 'vaild']:
        test_dir = base_path / dir_name
        if test_dir.exists():
            images_dir = test_dir / 'images'
            labels_dir = test_dir / 'labels'
            if images_dir.exists() and labels_dir.exists():
                return test_dir
    return None

current_model = None
current_model_path = None


class StreamCapture:
    """捕获标准输出并转发到队列"""
    def __init__(self, output_queue):
        self.output_queue = output_queue
        self.original_stdout = sys.stdout
        self.buffer = ""
    
    def write(self, text):
        self.original_stdout.write(text)
        if text:
            self.output_queue.put(text)
    
    def flush(self):
        self.original_stdout.flush()
    
    def restore(self):
        sys.stdout = self.original_stdout


def evaluate_model_stream(model, test_dir: Path, conf: float = 0.25, iou: float = 0.5, device: str = "0", output_queue=None):
    """
    评估模型（带流式输出）
    返回评估指标
    """
    test_dir_name = test_dir.name
    
    # 使用模型的类别信息
    nc = len(model.names) if hasattr(model, 'names') else 1
    names = list(model.names.values()) if isinstance(model.names, dict) else (model.names if model.names else ['object'])
    
    data_yaml_content = f"""path: {test_dir.parent.as_posix()}
train: {test_dir_name}/images
val: {test_dir_name}/images
test: {test_dir_name}/images

nc: {nc}
names: {names}
"""
    yaml_path = Path(tempfile.mktemp(suffix=".yaml"))
    yaml_path.write_text(data_yaml_content, encoding='utf-8')
    
    stream_capture = None
    if output_queue:
        stream_capture = StreamCapture(output_queue)
        sys.stdout = stream_capture
    
    try:
        results = model.val(
            data=str(yaml_path),
            split="test",
            conf=conf,
            iou=iou,
            device=device,
            plots=False,
            save=False,
            verbose=True,
        )
        
        r2 = 0.0
        if hasattr(results.box, 'maps') and results.box.maps is not None:
            r2 = float(results.box.maps.mean()) if hasattr(results.box.maps, 'mean') else float(results.box.maps)
        
        precision = results.box.mp
        recall = results.box.mr
        
        error_rate = 0.0
        if precision > 0 and recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
            error_rate = 1 - f1
        
        predictions = []
        if hasattr(results, 'speed'):
            predictions.append({
                "preprocess_ms": round(results.speed.get('preprocess', 0), 2),
                "inference_ms": round(results.speed.get('inference', 0), 2),
                "postprocess_ms": round(results.speed.get('postprocess', 0), 2)
            })
        
        metrics = {
            "r2": round(r2, 4),
            "map50": round(float(results.box.map50), 4),
            "map50_95": round(float(results.box.map), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "error_rate": round(error_rate, 4),
            "predictions": predictions
        }
        
        if output_queue:
            output_queue.put(f"\n评估完成!\n")
            output_queue.put(f"R²: {metrics['r2']}\n")
            output_queue.put(f"mAP@50: {metrics['map50']}\n")
            output_queue.put(f"mAP@50-95: {metrics['map50_95']}\n")
            output_queue.put(f"Precision: {metrics['precision']}\n")
            output_queue.put(f"Recall: {metrics['recall']}\n")
            output_queue.put(f"Error Rate: {metrics['error_rate']}\n")
        
        return metrics
    finally:
        if stream_capture:
            stream_capture.restore()
        if yaml_path.exists():
            yaml_path.unlink()


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': current_model is not None,
        'model_path': str(current_model_path) if current_model_path else None
    })


@app.route('/api/model/load', methods=['POST'])
def load_model():
    """
    加载YOLO模型
    
    请求方式: POST
    Content-Type: multipart/form-data
    
    参数:
        file: YOLO模型文件
    
    返回:
        {
            "success": true,
            "message": "模型加载成功",
            "data": {
                "model_path": "best.pt",
                "num_classes": 1,
                "class_names": {"0": "tube"}
            }
        }
    """
    global current_model, current_model_path
    
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传模型文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择文件'
            }), 400
        
        if not file.filename.endswith('.pt'):
            return jsonify({
                'success': False,
                'message': '模型文件必须是 .pt 格式'
            }), 400
        
        model_bytes = file.read()
        temp_model_path = Path(tempfile.mktemp(suffix=".pt"))
        
        with open(temp_model_path, 'wb') as f:
            f.write(model_bytes)
        
        try:
            current_model = YOLO(str(temp_model_path))
            current_model_path = file.filename
            
            return jsonify({
                'success': True,
                'message': '模型加载成功',
                'data': {
                    'model_path': file.filename,
                    'num_classes': len(current_model.names),
                    'class_names': current_model.names
                }
            })
        finally:
            if temp_model_path.exists():
                temp_model_path.unlink()
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'模型加载失败: {str(e)}'
        }), 500


@app.route('/api/model/load-path', methods=['POST'])
def load_model_by_path():
    """
    通过路径加载YOLO模型
    
    请求方式: POST
    Content-Type: application/json
    
    请求体:
        {
            "model_path": "yolo_models/train4/weights/best.pt"
        }
    
    返回:
        {
            "success": true,
            "message": "模型加载成功",
            "data": {
                "model_path": "yolo_models/train4/weights/best.pt",
                "num_classes": 1,
                "class_names": {"0": "tube"}
            }
        }
    """
    global current_model, current_model_path
    
    try:
        data = request.get_json()
        
        if not data or 'model_path' not in data:
            return jsonify({
                'success': False,
                'message': '未提供模型路径'
            }), 400
        
        model_path = Path(data['model_path'])
        
        if not model_path.is_absolute():
            model_path = BASE_DIR / model_path
        
        if not model_path.exists():
            return jsonify({
                'success': False,
                'message': f'模型文件不存在: {model_path}'
            }), 400
        
        current_model = YOLO(str(model_path))
        current_model.to('cuda' if torch.cuda.is_available() else 'cpu')
        current_model_path = str(model_path)
        
        return jsonify({
            'success': True,
            'message': '模型加载成功',
            'data': {
                'model_path': str(model_path),
                'num_classes': len(current_model.names),
                'class_names': current_model.names
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'模型加载失败: {str(e)}'
        }), 500


@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """
    评估模型（非流式）
    
    请求方式: POST
    Content-Type: application/json
    
    请求体:
        {
            "data_dir": "data/test",
            "conf": 0.25,
            "iou": 0.5
        }
    
    返回:
        {
            "success": true,
            "data": {
                "r2": 0.9428,
                "map50": 0.995,
                "map50_95": 0.9428,
                "precision": 1.0,
                "recall": 1.0,
                "error_rate": 0.0,
                "predictions": [...]
            }
        }
    """
    global current_model
    
    try:
        if current_model is None:
            return jsonify({
                'success': False,
                'message': '请先加载模型'
            }), 400
        
        data = request.get_json() or {}
        
        data_dir = data.get('data_dir')
        if data_dir:
            test_dir = Path(data_dir)
            if not test_dir.is_absolute():
                test_dir = BASE_DIR / data_dir
        else:
            test_dir = DEFAULT_DATA_DIR
        
        if not test_dir.exists():
            return jsonify({
                'success': False,
                'message': f'测试数据目录不存在: {test_dir}'
            }), 400
        
        # 先尝试在传入目录下查找 test/val/vaild 子目录
        actual_test_dir = find_test_dir(test_dir)
        if actual_test_dir is None:
            # 如果传入的是 test/val/vaild 目录本身，则在父目录查找
            actual_test_dir = find_test_dir(test_dir.parent) if test_dir.name in ['test', 'val', 'vaild'] else None
        if actual_test_dir is None:
            if test_dir.name in ['images', 'labels']:
                actual_test_dir = test_dir.parent
            else:
                actual_test_dir = test_dir
        
        if not (actual_test_dir / 'images').exists():
            return jsonify({
                'success': False,
                'message': f'测试目录不存在 images 子目录: {actual_test_dir}'
            }), 400
        
        conf = data.get('conf', 0.25)
        iou = data.get('iou', 0.5)
        device = data.get('device', '0')
        
        metrics = evaluate_model_stream(current_model, actual_test_dir, conf, iou, device)
        
        return jsonify({
            'success': True,
            'data': metrics
        })
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'评估失败: {str(e)}'
        }), 500


@app.route('/api/evaluate/stream', methods=['POST'])
def evaluate_stream():
    """
    评估模型（流式输出）
    
    请求方式: POST
    Content-Type: application/json
    
    请求体:
        {
            "data_dir": "data/test",
            "conf": 0.25,
            "iou": 0.5,
            "device": "0"
        }
    
    返回: Server-Sent Events (SSE) 流
        data: {"type": "log", "message": "开始评估..."}
        data: {"type": "log", "message": "val: Scanning..."}
        data: {"type": "result", "data": {"r2": 0.9428, ...}}
    """
    global current_model
    
    if current_model is None:
        return jsonify({
            'success': False,
            'message': '请先加载模型'
        }), 400
    
    data = request.get_json() or {}
    
    data_dir = data.get('data_dir')
    if data_dir:
        test_dir = Path(data_dir)
        if not test_dir.is_absolute():
            test_dir = BASE_DIR / data_dir
    else:
        test_dir = DEFAULT_DATA_DIR
    
    if not test_dir.exists():
        return jsonify({
            'success': False,
            'message': f'测试数据目录不存在: {test_dir}'
        }), 400
    
    # 先尝试在传入目录下查找 test/val/vaild 子目录
    actual_test_dir = find_test_dir(test_dir)
    if actual_test_dir is None:
        # 如果传入的是 test/val/vaild 目录本身，则在父目录查找
        actual_test_dir = find_test_dir(test_dir.parent) if test_dir.name in ['test', 'val', 'vaild'] else None
    if actual_test_dir is None:
        if test_dir.name in ['images', 'labels']:
            actual_test_dir = test_dir.parent
        else:
            actual_test_dir = test_dir
    
    if not (actual_test_dir / 'images').exists():
        return jsonify({
            'success': False,
            'message': f'测试目录不存在 images 子目录: {actual_test_dir}'
        }), 400
    
    conf = data.get('conf', 0.25)
    iou = data.get('iou', 0.5)
    device = data.get('device', '0')
    
    def generate():
        output_queue = queue.Queue()
        result_container = {'metrics': None, 'error': None}
        
        def run_evaluation():
            try:
                metrics = evaluate_model_stream(
                    current_model, 
                    actual_test_dir, 
                    conf, iou, device, 
                    output_queue
                )
                result_container['metrics'] = metrics
            except Exception as e:
                result_container['error'] = str(e)
            finally:
                output_queue.put(None)
        
        thread = threading.Thread(target=run_evaluation)
        thread.start()
        
        yield f"data: {json.dumps({'type': 'start', 'message': '开始评估...'})}\n\n"
        
        while True:
            try:
                item = output_queue.get(timeout=60)
                if item is None:
                    break
                
                yield f"data: {json.dumps({'type': 'log', 'message': item})}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        
        thread.join()
        
        if result_container['error']:
            yield f"data: {json.dumps({'type': 'error', 'message': result_container['error']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'result', 'data': result_container['metrics']})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done', 'message': '评估完成'})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/evaluate/full', methods=['POST'])
def evaluate_full():
    """
    完整评估流程：加载模型 + 评估
    
    请求方式: POST
    Content-Type: multipart/form-data
    
    参数:
        model: YOLO模型文件
        data_dir: 测试数据目录路径 (可选)
        conf: 置信度阈值 (可选，默认0.25)
        iou: IOU阈值 (可选，默认0.5)
    
    返回:
        {
            "success": true,
            "data": {
                "model_info": {...},
                "metrics": {...}
            }
        }
    """
    global current_model, current_model_path
    
    try:
        if 'model' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传模型文件'
            }), 400
        
        model_file = request.files['model']
        
        if model_file.filename == '':
            return jsonify({
                'success': False,
                'message': '未选择模型文件'
            }), 400
        
        if not model_file.filename.endswith('.pt'):
            return jsonify({
                'success': False,
                'message': '模型文件必须是 .pt 格式'
            }), 400
        
        model_bytes = model_file.read()
        temp_model_path = Path(tempfile.mktemp(suffix=".pt"))
        
        with open(temp_model_path, 'wb') as f:
            f.write(model_bytes)
        
        try:
            current_model = YOLO(str(temp_model_path))
            current_model_path = model_file.filename
            
            data_dir = request.form.get('data_dir')
            if data_dir:
                test_dir = Path(data_dir)
                if not test_dir.is_absolute():
                    test_dir = BASE_DIR / data_dir
            else:
                test_dir = DEFAULT_DATA_DIR
            
            if not test_dir.exists():
                return jsonify({
                    'success': False,
                    'message': f'测试数据目录不存在: {test_dir}'
                }), 400
            
            conf = float(request.form.get('conf', 0.25))
            iou = float(request.form.get('iou', 0.5))
            device = request.form.get('device', '0')
            
            metrics = evaluate_model_stream(current_model, test_dir, conf, iou, device)
            
            return jsonify({
                'success': True,
                'data': {
                    'model_info': {
                        'num_classes': len(current_model.names),
                        'class_names': current_model.names
                    },
                    'metrics': metrics
                }
            })
            
        finally:
            if temp_model_path.exists():
                temp_model_path.unlink()
                
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'评估失败: {str(e)}'
        }), 500


@app.route('/api/evaluate/full/stream', methods=['POST'])
def evaluate_full_stream():
    """
    完整评估流程（流式输出）：加载模型 + 评估
    
    请求方式: POST
    Content-Type: multipart/form-data
    
    参数:
        model: YOLO模型文件
        data_dir: 测试数据目录路径 (可选)
        conf: 置信度阈值 (可选，默认0.25)
        iou: IOU阈值 (可选，默认0.5)
        device: 设备 (可选，默认0)
    
    返回: Server-Sent Events (SSE) 流
    """
    global current_model, current_model_path
    
    if 'model' not in request.files:
        return jsonify({
            'success': False,
            'message': '未上传模型文件'
        }), 400
    
    model_file = request.files['model']
    
    if model_file.filename == '' or not model_file.filename.endswith('.pt'):
        return jsonify({
            'success': False,
            'message': '请选择有效的 .pt 模型文件'
        }), 400
    
    model_bytes = model_file.read()
    temp_model_path = Path(tempfile.mktemp(suffix=".pt"))
    
    with open(temp_model_path, 'wb') as f:
        f.write(model_bytes)
    
    data_dir = request.form.get('data_dir')
    if data_dir:
        test_dir = Path(data_dir)
        if not test_dir.is_absolute():
            test_dir = BASE_DIR / data_dir
    else:
        test_dir = DEFAULT_DATA_DIR
    
    if not test_dir.exists():
        temp_model_path.unlink()
        return jsonify({
            'success': False,
            'message': f'测试数据目录不存在: {test_dir}'
        }), 400
    
    conf = float(request.form.get('conf', 0.25))
    iou = float(request.form.get('iou', 0.5))
    device = request.form.get('device', '0')
    
    def generate():
        output_queue = queue.Queue()
        result_container = {'metrics': None, 'error': None}
        
        def run_evaluation():
            try:
                current_model = YOLO(str(temp_model_path))
                output_queue.put(f"模型加载成功: {model_file.filename}\n")
                output_queue.put(f"类别数量: {len(current_model.names)}\n")
                output_queue.put(f"类别名称: {current_model.names}\n")
                
                metrics = evaluate_model_stream(
                    current_model, 
                    test_dir, 
                    conf, iou, device, 
                    output_queue
                )
                result_container['metrics'] = metrics
            except Exception as e:
                result_container['error'] = str(e)
            finally:
                output_queue.put(None)
        
        thread = threading.Thread(target=run_evaluation)
        thread.start()
        
        yield f"data: {json.dumps({'type': 'start', 'message': '开始评估...'})}\n\n"
        
        while True:
            try:
                item = output_queue.get(timeout=120)
                if item is None:
                    break
                
                yield f"data: {json.dumps({'type': 'log', 'message': item})}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        
        thread.join()
        
        if temp_model_path.exists():
            temp_model_path.unlink()
        
        if result_container['error']:
            yield f"data: {json.dumps({'type': 'error', 'message': result_container['error']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'result', 'data': result_container['metrics']})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done', 'message': '评估完成'})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


if __name__ == '__main__':
    print("=" * 70)
    print("YOLO模型测试API服务")
    print("=" * 70)
    print("API接口:")
    print("  GET  /api/health              - 健康检查")
    print("  POST /api/model/load          - 上传模型文件加载")
    print("  POST /api/model/load-path     - 通过路径加载模型")
    print("  POST /api/evaluate            - 评估已加载的模型")
    print("  POST /api/evaluate/stream     - 评估模型（流式输出）")
    print("  POST /api/evaluate/full       - 完整评估流程")
    print("  POST /api/evaluate/full/stream- 完整评估流程（流式输出）")
    print("=" * 70)
    
    if HAS_HTTPS_SUPPORT:
        run_https_server(app, host='0.0.0.0', port=5003, debug=False)
    else:
        print("服务器启动在 http://localhost:5003")
        print("=" * 70)
        app.run(host='0.0.0.0', port=5003, debug=False, threaded=True, use_reloader=False)
