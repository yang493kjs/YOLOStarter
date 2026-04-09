"""
YOLO模型训练API服务
提供模型训练的REST API接口
"""

import os
import sys
import threading
import queue
from pathlib import Path
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime
from ultralytics import YOLO
import torch
import json

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

try:
    from https_server import run_https_server
    HAS_HTTPS_SUPPORT = True
except ImportError:
    HAS_HTTPS_SUPPORT = False

app = Flask(__name__)
CORS(app)

training_status = {
    'is_training': False,
    'is_grid_search': False,
    'current_task': None,
    'progress': 0,
    'message': '',
    'start_time': None,
    'end_time': None,
    'error': None,
    'epoch': 0,
    'total_epochs': 0,
    'metrics': {},
    'grid_search': {
        'current_param': 0,
        'total_params': 0,
        'current_params': {},
        'best_params': {},
        'best_score': None,
        'all_results': [],
        'cv_folds': 1,
        'current_fold': 0,
        'total_folds': 1
    }
}

YOLO_PARAM_GRID = {
    'lr0': [0.001, 0.01, 0.1],
    'lrf': [0.01, 0.1],
    'momentum': [0.9, 0.937, 0.95],
    'weight_decay': [0.0001, 0.0005, 0.001],
    'warmup_epochs': [0.0, 1.0, 3.0],
    'box': [7.5, 10.0],
    'cls': [0.5, 1.0],
    'dfl': [1.5, 3.0]
}

log_queue = queue.Queue()
stop_event = threading.Event()


def generate_param_combinations(param_grid: dict) -> list:
    """生成参数组合"""
    import itertools
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = []
    for combo in itertools.product(*values):
        combinations.append(dict(zip(keys, combo)))
    return combinations


def log_message(msg: str):
    """记录日志消息到队列"""
    log_queue.put(msg)
    print(msg)

def train_yolo_task(
    data_yaml: str,
    model_name: str,
    epochs: int,
    batch: int,
    imgsz: int,
    device: str,
    name: str,
    patience: int,
    save_period: int,
):
    """训练YOLO模型的后台任务"""
    global training_status
    
    try:
        training_status['is_training'] = True
        training_status['progress'] = 0
        training_status['message'] = '初始化训练...'
        training_status['start_time'] = datetime.now().isoformat()
        training_status['error'] = None
        training_status['total_epochs'] = epochs
        training_status['epoch'] = 0
        stop_event.clear()
        
        log_message('=' * 60)
        log_message('YOLO模型训练')
        log_message('=' * 60)
        log_message(f'数据配置: {data_yaml}')
        log_message(f'基础模型: {model_name}')
        log_message(f'训练轮数: {epochs}')
        log_message(f'批次大小: {batch}')
        log_message(f'图像大小: {imgsz}')
        log_message(f'设备: {device}')
        log_message('=' * 60)
        
        output_dir = BASE_DIR / 'yolo_models'
        output_dir.mkdir(exist_ok=True)
        
        training_status['message'] = f'加载基础模型: {model_name}'
        training_status['progress'] = 10
        log_message(f'加载基础模型: {model_name}')
        
        model = YOLO(model_name)
        
        if torch.cuda.is_available():
            log_message(f'GPU可用: {torch.cuda.get_device_name(0)}')
            log_message(f'GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
        else:
            log_message('GPU不可用，使用CPU训练')
        
        training_status['message'] = '开始训练...'
        training_status['progress'] = 20
        log_message('开始训练...')
        
        def on_train_epoch_end(trainer):
            if stop_event.is_set():
                raise KeyboardInterrupt("训练被用户停止")
            current_epoch = trainer.epoch + 1
            training_status['epoch'] = current_epoch
            training_status['progress'] = 20 + int((current_epoch / epochs) * 70)
            training_status['message'] = f'训练中... Epoch {current_epoch}/{epochs}'
            
            if hasattr(trainer, 'metrics') and trainer.metrics:
                training_status['metrics'] = {
                    'box_loss': getattr(trainer.metrics, 'box_loss', None),
                    'cls_loss': getattr(trainer.metrics, 'cls_loss', None),
                    'dfl_loss': getattr(trainer.metrics, 'dfl_loss', None),
                }
            
            log_message(f'Epoch {current_epoch}/{epochs} - Progress: {training_status["progress"]}%')
        
        model.add_callback('on_train_epoch_end', on_train_epoch_end)
        
        results = model.train(
            data=data_yaml,
            epochs=epochs,
            batch=batch,
            imgsz=imgsz,
            device=device,
            project=str(output_dir),
            name=name,
            patience=patience,
            save_period=save_period,
            verbose=True,
            exist_ok=True,
        )
        
        training_status['progress'] = 100
        training_status['message'] = '训练完成!'
        training_status['end_time'] = datetime.now().isoformat()
        log_message('=' * 60)
        log_message('训练完成!')
        log_message(f'模型保存位置: {output_dir / name / "weights"}')
        log_message('=' * 60)
        
    except KeyboardInterrupt:
        training_status['message'] = '训练已停止'
        training_status['end_time'] = datetime.now().isoformat()
        log_message('训练已停止')
        
    except Exception as e:
        training_status['error'] = str(e)
        training_status['message'] = f'训练失败: {str(e)}'
        log_message(f'训练失败: {str(e)}')
        
    finally:
        training_status['is_training'] = False


@app.route('/api/train/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/train/stream', methods=['GET'])
def training_stream():
    """训练日志流式输出 (Server-Sent Events)"""
    def generate():
        wait_count = 0
        while True:
            try:
                msg = log_queue.get(timeout=1)
                yield f"data: {json.dumps({'message': msg, 'timestamp': datetime.now().isoformat()})}\n\n"
            except queue.Empty:
                if not training_status['is_training']:
                    if training_status['end_time'] is not None or training_status['error'] is not None:
                        yield f"data: {json.dumps({'message': '[DONE]', 'timestamp': datetime.now().isoformat()})}\n\n"
                        break
                    wait_count += 1
                    if wait_count > 30:
                        yield f"data: {json.dumps({'message': '[DONE]', 'timestamp': datetime.now().isoformat()})}\n\n"
                        break
                yield f": heartbeat\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/train/status', methods=['GET'])
def get_training_status():
    """获取训练状态"""
    return jsonify({
        'success': True,
        'data': training_status
    })


@app.route('/api/train/start', methods=['POST'])
def start_training():
    """开始训练
    
    请求方式: POST
    Content-Type: application/json
    
    请求体:
        {
            "data_yaml": "data/bread.yaml",
            "model_name": "yolov8n.pt",
            "epochs": 100,
            "batch": 16,
            "imgsz": 640,
            "device": "0",
            "name": "train",
            "patience": 20,
            "save_period": -1
        }
    """
    global training_status
    
    try:
        if training_status['is_training']:
            return jsonify({
                'success': False,
                'message': '已有训练任务正在运行'
            }), 400
        
        data = request.get_json()
        
        data_yaml = data.get('data_yaml')
        if not data_yaml:
            return jsonify({
                'success': False,
                'message': '数据配置文件路径不能为空'
            }), 400
        
        # 智能路径处理：尝试多种可能的路径
        yaml_file = Path(data_yaml)
        possible_paths = []
        
        if yaml_file.is_absolute():
            possible_paths.append(yaml_file)
        else:
            # 1. 直接相对于 BASE_DIR 的路径
            possible_paths.append(BASE_DIR / data_yaml)
            # 2. 如果路径不以 datasets/ 开头，尝试加上 datasets/ 前缀
            if not str(data_yaml).startswith('datasets/'):
                possible_paths.append(BASE_DIR / 'datasets' / data_yaml)
        
        # 尝试所有可能的路径
        data_yaml_path = None
        for path in possible_paths:
            if path.exists():
                data_yaml_path = path
                log_message(f'找到 YAML 文件: {path}')
                break
        
        if data_yaml_path is None:
            return jsonify({
                'success': False,
                'message': f'数据配置文件不存在，尝试过的路径: {possible_paths}'
            }), 400
        
        model_name = data.get('model_name', 'yolov8n.pt')
        epochs = data.get('epochs', 100)
        batch = data.get('batch', 16)
        imgsz = data.get('imgsz', 640)
        device = data.get('device', '0')
        name = data.get('name', 'train')
        patience = data.get('patience', 20)
        save_period = data.get('save_period', -1)
        
        training_status['current_task'] = {
            'data_yaml': data_yaml,
            'model_name': model_name,
            'epochs': epochs,
            'batch': batch,
            'imgsz': imgsz,
            'device': device,
            'name': name,
            'patience': patience,
            'save_period': save_period
        }
        
        thread = threading.Thread(
            target=train_yolo_task,
            kwargs={
                'data_yaml': str(data_yaml_path),
                'model_name': model_name,
                'epochs': epochs,
                'batch': batch,
                'imgsz': imgsz,
                'device': device,
                'name': name,
                'patience': patience,
                'save_period': save_period,
            }
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '训练任务已启动',
            'data': {
                'output_dir': str(BASE_DIR / 'yolo_models' / name),
                'parameters': training_status['current_task']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动训练失败: {str(e)}'
        }), 500


@app.route('/api/train/stop', methods=['POST'])
def stop_training():
    """停止训练"""
    global training_status
    
    if not training_status['is_training']:
        return jsonify({
            'success': False,
            'message': '没有正在运行的训练任务'
        }), 400
    
    stop_event.set()
    training_status['message'] = '正在停止训练...'
    log_message('用户请求停止训练...')
    
    return jsonify({
        'success': True,
        'message': '停止训练请求已发送'
    })


def grid_search_yolo_task(
    data_yaml: str,
    model_name: str,
    epochs: int,
    batch: int,
    imgsz: int,
    device: str,
    name: str,
    patience: int,
    save_period: int,
    param_grid: dict,
    cv_folds: int = 1,
):
    """YOLO网格搜索任务"""
    global training_status
    
    try:
        training_status['is_training'] = True
        training_status['is_grid_search'] = True
        training_status['progress'] = 0
        training_status['message'] = '初始化网格搜索...'
        training_status['start_time'] = datetime.now().isoformat()
        training_status['error'] = None
        training_status['total_epochs'] = epochs
        training_status['epoch'] = 0
        stop_event.clear()
        
        training_status['grid_search']['current_param'] = 0
        training_status['grid_search']['total_params'] = 0
        training_status['grid_search']['current_params'] = {}
        training_status['grid_search']['best_params'] = {}
        training_status['grid_search']['best_score'] = None
        training_status['grid_search']['all_results'] = []
        training_status['grid_search']['cv_folds'] = cv_folds
        training_status['grid_search']['current_fold'] = 0
        training_status['grid_search']['total_folds'] = cv_folds
        
        log_message('=' * 60)
        log_message('YOLO模型网格搜索')
        log_message('=' * 60)
        log_message(f'数据配置: {data_yaml}')
        log_message(f'基础模型: {model_name}')
        log_message(f'训练轮数: {epochs}')
        log_message(f'批次大小: {batch}')
        log_message(f'图像大小: {imgsz}')
        log_message(f'设备: {device}')
        log_message(f'交叉验证: {cv_folds}折')
        log_message('=' * 60)
        
        output_dir = BASE_DIR / 'yolo_models'
        output_dir.mkdir(exist_ok=True)
        
        training_status['message'] = '生成参数组合...'
        training_status['progress'] = 5
        log_message('生成参数组合...')
        
        param_combinations = generate_param_combinations(param_grid)
        total_params = len(param_combinations)
        training_status['grid_search']['total_params'] = total_params
        
        log_message(f'共生成 {total_params} 个参数组合')
        log_message('=' * 60)
        
        for idx, params in enumerate(param_combinations):
            if stop_event.is_set():
                raise KeyboardInterrupt("网格搜索被用户停止")
            
            training_status['grid_search']['current_param'] = idx + 1
            training_status['grid_search']['current_params'] = params
            
            param_str = ', '.join([f'{k}={v}' for k, v in params.items()])
            log_message(f'\n参数组合 {idx + 1}/{total_params}: {param_str}')
            
            training_status['message'] = f'训练参数组合 {idx + 1}/{total_params}'
            
            fold_scores = []
            
            for fold in range(cv_folds):
                training_status['grid_search']['current_fold'] = fold + 1
                
                if cv_folds > 1:
                    log_message(f'\n  折 {fold + 1}/{cv_folds}')
                
                current_name = f'{name}_gs_{idx + 1}'
                if cv_folds > 1:
                    current_name = f'{current_name}_fold{fold + 1}'
                
                training_status['message'] = f'加载基础模型: {model_name}'
                log_message(f'  加载基础模型: {model_name}')
                model = YOLO(model_name)
                
                if torch.cuda.is_available():
                    log_message(f'  GPU可用: {torch.cuda.get_device_name(0)}')
                else:
                    log_message('  GPU不可用，使用CPU训练')
                
                training_status['message'] = f'开始训练参数组合 {idx + 1}/{total_params} - 折 {fold + 1}/{cv_folds}'
                log_message('  开始训练...')
                
                def on_train_epoch_end(trainer):
                    if stop_event.is_set():
                        raise KeyboardInterrupt("训练被用户停止")
                    current_epoch = trainer.epoch + 1
                    training_status['epoch'] = current_epoch
                    fold_progress = (current_epoch / epochs)
                    total_progress = 5 + int(((idx + (fold + fold_progress) / cv_folds) / total_params) * 90)
                    training_status['progress'] = total_progress
                    training_status['message'] = f'参数组合 {idx + 1}/{total_params} - 折 {fold + 1}/{cv_folds} - Epoch {current_epoch}/{epochs}'
                    
                    if hasattr(trainer, 'metrics') and trainer.metrics:
                        training_status['metrics'] = {
                            'box_loss': getattr(trainer.metrics, 'box_loss', None),
                            'cls_loss': getattr(trainer.metrics, 'cls_loss', None),
                            'dfl_loss': getattr(trainer.metrics, 'dfl_loss', None),
                        }
                    
                    log_message(f'  参数组合 {idx + 1}/{total_params} - 折 {fold + 1}/{cv_folds} - Epoch {current_epoch}/{epochs}')
                
                model.add_callback('on_train_epoch_end', on_train_epoch_end)
                
                results = model.train(
                    data=data_yaml,
                    epochs=epochs,
                    batch=batch,
                    imgsz=imgsz,
                    device=device,
                    project=str(output_dir),
                    name=current_name,
                    patience=patience,
                    save_period=save_period,
                    verbose=True,
                    exist_ok=True,
                    **params
                )
                
                val_results = model.val()
                if hasattr(val_results, 'box'):
                    map50 = val_results.box.map50
                else:
                    map50 = 0.0
                
                fold_scores.append(float(map50))
                log_message(f'  折 {fold + 1}/{cv_folds} 完成 - mAP50: {map50:.4f}')
            
            mean_map50 = float(np.mean(fold_scores))
            std_map50 = float(np.std(fold_scores))
            
            result_entry = {
                'param_idx': idx + 1,
                'params': params,
                'map50': mean_map50,
                'map50_std': std_map50,
                'fold_scores': fold_scores,
                'name': f'{name}_gs_{idx + 1}'
            }
            training_status['grid_search']['all_results'].append(result_entry)
            
            log_message(f'\n参数组合 {idx + 1} 完成 - 平均mAP50: {mean_map50:.4f} (±{std_map50:.4f})')
            
            if (training_status['grid_search']['best_score'] is None or 
                mean_map50 > training_status['grid_search']['best_score']):
                training_status['grid_search']['best_score'] = mean_map50
                training_status['grid_search']['best_params'] = params
                log_message(f'新的最佳参数! 平均mAP50: {mean_map50:.4f}')
        
        training_status['progress'] = 100
        training_status['message'] = '网格搜索完成!'
        training_status['end_time'] = datetime.now().isoformat()
        
        log_message('=' * 60)
        log_message('网格搜索完成!')
        log_message('=' * 60)
        log_message(f'最佳参数: {training_status["grid_search"]["best_params"]}')
        log_message(f'最佳平均mAP50: {training_status["grid_search"]["best_score"]:.4f}')
        log_message(f'交叉验证: {cv_folds}折')
        log_message('=' * 60)
        
    except KeyboardInterrupt:
        training_status['message'] = '网格搜索已停止'
        training_status['end_time'] = datetime.now().isoformat()
        log_message('网格搜索已停止')
        
    except Exception as e:
        training_status['error'] = str(e)
        training_status['message'] = f'网格搜索失败: {str(e)}'
        log_message(f'网格搜索失败: {str(e)}')
        
    finally:
        training_status['is_training'] = False
        training_status['is_grid_search'] = False


@app.route('/api/grid-search/start', methods=['POST'])
def start_grid_search():
    """开始网格搜索
    
    请求方式: POST
    Content-Type: application/json
    
    请求体:
        {
            "data_yaml": "data/bread.yaml",
            "model_name": "yolov8n.pt",
            "epochs": 50,
            "batch": 16,
            "imgsz": 640,
            "device": "0",
            "name": "grid_search",
            "patience": 10,
            "save_period": -1,
            "cv_folds": 5,
            "param_grid": {
                "lr0": [0.001, 0.01],
                "momentum": [0.9, 0.937]
            }
        }
    """
    global training_status
    
    try:
        if training_status['is_training']:
            return jsonify({
                'success': False,
                'message': '已有训练任务正在运行'
            }), 400
        
        data = request.get_json()
        
        data_yaml = data.get('data_yaml')
        if not data_yaml:
            return jsonify({
                'success': False,
                'message': '数据配置文件路径不能为空'
            }), 400
        
        # 智能路径处理：尝试多种可能的路径
        yaml_file = Path(data_yaml)
        possible_paths = []
        
        if yaml_file.is_absolute():
            possible_paths.append(yaml_file)
        else:
            # 1. 直接相对于 BASE_DIR 的路径
            possible_paths.append(BASE_DIR / data_yaml)
            # 2. 如果路径不以 datasets/ 开头，尝试加上 datasets/ 前缀
            if not str(data_yaml).startswith('datasets/'):
                possible_paths.append(BASE_DIR / 'datasets' / data_yaml)
        
        # 尝试所有可能的路径
        data_yaml_path = None
        for path in possible_paths:
            if path.exists():
                data_yaml_path = path
                log_message(f'找到 YAML 文件: {path}')
                break
        
        if data_yaml_path is None:
            return jsonify({
                'success': False,
                'message': f'数据配置文件不存在，尝试过的路径: {possible_paths}'
            }), 400
        
        model_name = data.get('model_name', 'yolov8n.pt')
        epochs = data.get('epochs', 50)
        batch = data.get('batch', 16)
        imgsz = data.get('imgsz', 640)
        device = data.get('device', '0')
        name = data.get('name', 'grid_search')
        patience = data.get('patience', 10)
        save_period = data.get('save_period', -1)
        cv_folds = data.get('cv_folds', 1)
        param_grid = data.get('param_grid', YOLO_PARAM_GRID)
        
        training_status['current_task'] = {
            'data_yaml': data_yaml,
            'model_name': model_name,
            'epochs': epochs,
            'batch': batch,
            'imgsz': imgsz,
            'device': device,
            'name': name,
            'patience': patience,
            'save_period': save_period,
            'cv_folds': cv_folds,
            'param_grid': param_grid
        }
        
        thread = threading.Thread(
            target=grid_search_yolo_task,
            kwargs={
                'data_yaml': str(data_yaml_path),
                'model_name': model_name,
                'epochs': epochs,
                'batch': batch,
                'imgsz': imgsz,
                'device': device,
                'name': name,
                'patience': patience,
                'save_period': save_period,
                'cv_folds': cv_folds,
                'param_grid': param_grid,
            }
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '网格搜索任务已启动',
            'data': {
                'output_dir': str(BASE_DIR / 'yolo_models'),
                'parameters': training_status['current_task'],
                'total_param_combinations': len(generate_param_combinations(param_grid)),
                'cv_folds': cv_folds
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动网格搜索失败: {str(e)}'
        }), 500


@app.route('/api/grid-search/results', methods=['GET'])
def get_grid_search_results():
    """获取网格搜索结果"""
    return jsonify({
        'success': True,
        'data': {
            'is_grid_search': training_status['is_grid_search'],
            'grid_search': training_status['grid_search']
        }
    })


@app.route('/api/grid-search/params', methods=['GET'])
def get_default_param_grid():
    """获取默认参数网格"""
    return jsonify({
        'success': True,
        'data': YOLO_PARAM_GRID
    })


if __name__ == "__main__":
    print("=" * 70)
    print("YOLO模型训练API服务")
    print("=" * 70)
    print("API接口:")
    print("  GET  /api/train/health            - 健康检查")
    print("  GET  /api/train/status            - 获取训练状态")
    print("  GET  /api/train/stream            - 训练日志流式输出 (SSE)")
    print("  POST /api/train/start             - 开始训练")
    print("  POST /api/train/stop              - 停止训练")
    print("  GET  /api/grid-search/params      - 获取默认参数网格")
    print("  POST /api/grid-search/start       - 开始网格搜索")
    print("  GET  /api/grid-search/results     - 获取网格搜索结果")
    print("=" * 70)
    print(f"模型保存目录: {BASE_DIR / 'yolo_models'}")
    print("=" * 70)
    
    if HAS_HTTPS_SUPPORT:
        run_https_server(app, host='0.0.0.0', port=5004, debug=False)
    else:
        print("服务器启动在 http://localhost:5004")
        print("=" * 70)
        app.run(host='0.0.0.0', port=5004, debug=False, threaded=True)
