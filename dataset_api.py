"""
后端存储数据集的API
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
import base64
from werkzeug.utils import secure_filename
import sys

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

try:
    from https_server import run_https_server
    HAS_HTTPS_SUPPORT = True
except ImportError:
    HAS_HTTPS_SUPPORT = False

app = Flask(__name__)
CORS(app)

DATASETS_DIR = Path(__file__).parent / 'datasets'
DATASETS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'txt', 'yaml', 'yml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_filename(filepath):
    """从路径中提取文件名，去除路径部分"""
    return os.path.basename(filepath.replace('\\', '/'))

def check_has_yaml(dataset_dir: Path) -> bool:
    """检查是否存在 YAML 配置文件，支持 .yaml 和 .yml，大小写不敏感"""
    for filename in dataset_dir.iterdir():
        if filename.is_file():
            name_lower = filename.name.lower()
            if name_lower == 'data.yaml' or name_lower == 'data.yml':
                return True
    return False

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    try:
        datasets = []
        print(f"扫描目录: {DATASETS_DIR}")
        for dataset_dir in DATASETS_DIR.iterdir():
            if dataset_dir.is_dir():
                info_file = dataset_dir / 'info.json'
                if info_file.exists():
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    
                    if 'id' not in info:
                        info['id'] = dataset_dir.name
                    
                    train_image_count = 0
                    train_label_count = 0
                    valid_image_count = 0
                    valid_label_count = 0
                    test_image_count = 0
                    test_label_count = 0
                    
                    train_images_dir = dataset_dir / 'train' / 'images'
                    train_labels_dir = dataset_dir / 'train' / 'labels'
                    valid_images_dir = dataset_dir / 'valid' / 'images'
                    valid_labels_dir = dataset_dir / 'valid' / 'labels'
                    test_images_dir = dataset_dir / 'test' / 'images'
                    test_labels_dir = dataset_dir / 'test' / 'labels'
                    
                    if train_images_dir.exists():
                        train_image_count = len([f for f in train_images_dir.iterdir() if f.is_file()])
                    if train_labels_dir.exists():
                        train_label_count = len(list(train_labels_dir.glob('*.txt')))
                    if valid_images_dir.exists():
                        valid_image_count = len([f for f in valid_images_dir.iterdir() if f.is_file()])
                    if valid_labels_dir.exists():
                        valid_label_count = len(list(valid_labels_dir.glob('*.txt')))
                    if test_images_dir.exists():
                        test_image_count = len([f for f in test_images_dir.iterdir() if f.is_file()])
                    if test_labels_dir.exists():
                        test_label_count = len(list(test_labels_dir.glob('*.txt')))
                    
                    info['trainImageCount'] = train_image_count
                    info['trainLabelCount'] = train_label_count
                    info['validImageCount'] = valid_image_count
                    info['validLabelCount'] = valid_label_count
                    info['testImageCount'] = test_image_count
                    info['testLabelCount'] = test_label_count
                    info['imageCount'] = train_image_count + valid_image_count + test_image_count
                    info['labelCount'] = train_label_count + valid_label_count + test_label_count
                    info['hasYaml'] = check_has_yaml(dataset_dir)
                    
                    datasets.append(info)
        
        datasets.sort(key=lambda x: x.get('createTime', ''), reverse=True)
        return jsonify({'code': 200, 'data': datasets})
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets', methods=['POST'])
def create_dataset():
    try:
        data = request.json
        dataset_id = f"ds_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        dataset_dir = DATASETS_DIR / dataset_id
        dataset_dir.mkdir()
        
        (dataset_dir / 'train').mkdir()
        (dataset_dir / 'train' / 'images').mkdir()
        (dataset_dir / 'train' / 'labels').mkdir()
        (dataset_dir / 'valid').mkdir()
        (dataset_dir / 'valid' / 'images').mkdir()
        (dataset_dir / 'valid' / 'labels').mkdir()
        (dataset_dir / 'test').mkdir()
        (dataset_dir / 'test' / 'images').mkdir()
        (dataset_dir / 'test' / 'labels').mkdir()
        
        info = {
            'id': dataset_id,
            'name': data.get('name', '未命名数据集'),
            'description': data.get('description', ''),
            'createTime': datetime.now().isoformat()
        }
        
        with open(dataset_dir / 'info.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        return jsonify({'code': 200, 'data': info, 'message': '数据集创建成功'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

def find_yaml_file(dataset_dir: Path) -> Path | None:
    """查找 YAML 配置文件，支持 .yaml 和 .yml，大小写不敏感"""
    for filename in dataset_dir.iterdir():
        if filename.is_file():
            name_lower = filename.name.lower()
            if name_lower == 'data.yaml' or name_lower == 'data.yml':
                return filename
    return None

@app.route('/api/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            return jsonify({'code': 404, 'message': '数据集不存在'}), 404
        
        info_file = dataset_dir / 'info.json'
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
        else:
            info = {
                'id': dataset_id,
                'name': dataset_id,
                'description': '',
                'createTime': datetime.now().isoformat()
            }
        
        images = []
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.tif']
        
        for split in ['train', 'valid', 'test']:
            images_dir = dataset_dir / split / 'images'
            if images_dir.exists():
                for img_file in images_dir.iterdir():
                    if img_file.suffix.lower() in image_extensions:
                        images.append({
                            'id': img_file.stem,
                            'name': img_file.name,
                            'url': f'/api/datasets/{dataset_id}/images/{img_file.name}',
                            'size': img_file.stat().st_size,
                            'split': split
                        })
        
        top_images_dir = dataset_dir / 'images'
        if top_images_dir.exists():
            for img_file in top_images_dir.iterdir():
                if img_file.suffix.lower() in image_extensions:
                    images.append({
                        'id': img_file.stem,
                        'name': img_file.name,
                        'url': f'/api/datasets/{dataset_id}/images/{img_file.name}',
                        'size': img_file.stat().st_size,
                        'split': 'train'
                    })
        
        labels = []
        for split in ['train', 'valid', 'test']:
            labels_dir = dataset_dir / split / 'labels'
            if labels_dir.exists():
                for label_file in labels_dir.glob('*.txt'):
                    labels.append({
                        'id': label_file.stem,
                        'name': label_file.name,
                        'size': label_file.stat().st_size,
                        'split': split
                    })
        
        top_labels_dir = dataset_dir / 'labels'
        if top_labels_dir.exists():
            for label_file in top_labels_dir.glob('*.txt'):
                labels.append({
                    'id': label_file.stem,
                    'name': label_file.name,
                    'size': label_file.stat().st_size,
                    'split': 'train'
                })
        
        yaml_file = find_yaml_file(dataset_dir)
        yaml_data = None
        if yaml_file and yaml_file.exists():
            import yaml
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)
                classes = []
                if yaml_content.get('names'):
                    if isinstance(yaml_content['names'], list):
                        classes = yaml_content['names']
                    elif isinstance(yaml_content['names'], dict):
                        classes = list(yaml_content['names'].values())
                yaml_data = {
                    'fileName': yaml_file.name,
                    'classCount': len(classes),
                    'classes': classes,
                    'path': yaml_content.get('path', ''),
                    'train': yaml_content.get('train', ''),
                    'val': yaml_content.get('val', ''),
                    'test': yaml_content.get('test', '')
                }
        
        return jsonify({
            'code': 200,
            'data': {
                **info,
                'images': images,
                'labels': labels,
                'yamlData': yaml_data
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            return jsonify({'code': 404, 'message': '数据集不存在'}), 404
        
        shutil.rmtree(dataset_dir)
        return jsonify({'code': 200, 'message': '数据集已删除'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/images', methods=['POST'])
def upload_image(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            return jsonify({'code': 404, 'message': '数据集不存在'}), 404
        
        if 'file' not in request.files:
            data = request.json
            if data and 'base64' in data:
                filename = data.get('name', f'{uuid.uuid4().hex[:8]}.jpg')
                split = data.get('split', 'train')
                base64_data = data['base64']
                
                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]
                
                images_dir = dataset_dir / split / 'images'
                images_dir.mkdir(parents=True, exist_ok=True)
                
                filepath = images_dir / secure_filename(filename)
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                
                return jsonify({
                    'code': 200,
                    'data': {
                        'id': filepath.stem,
                        'name': filename,
                        'url': f'/api/datasets/{dataset_id}/images/{filename}',
                        'size': filepath.stat().st_size,
                        'split': split
                    }
                })
            return jsonify({'code': 400, 'message': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'message': '没有选择文件'}), 400
        
        split = request.form.get('split', 'train')
        filename = file.filename
        # 先提取文件名，去除路径部分，再进行安全处理
        filename = get_filename(filename)
        secure_name = secure_filename(filename)
        
        images_dir = dataset_dir / split / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = images_dir / secure_name
        file.save(filepath)
        
        return jsonify({
            'code': 200,
            'data': {
                'id': filepath.stem,
                'name': filename,
                'url': f'/api/datasets/{dataset_id}/images/{secure_name}',
                'size': filepath.stat().st_size,
                'split': split
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/images/<filename>', methods=['GET'])
def get_image(dataset_id, filename):
    try:
        # 首先尝试使用原始文件名
        for split in ['train', 'valid', 'test']:
            filepath = DATASETS_DIR / dataset_id / split / 'images' / filename
            if filepath.exists():
                return send_file(filepath)
        
        top_filepath = DATASETS_DIR / dataset_id / 'images' / filename
        if top_filepath.exists():
            return send_file(top_filepath)
        
        # 如果原始文件名不存在，尝试使用安全文件名
        secure_filename_try = secure_filename(filename)
        if secure_filename_try != filename:
            for split in ['train', 'valid', 'test']:
                filepath = DATASETS_DIR / dataset_id / split / 'images' / secure_filename_try
                if filepath.exists():
                    return send_file(filepath)
            
            top_filepath = DATASETS_DIR / dataset_id / 'images' / secure_filename_try
            if top_filepath.exists():
                return send_file(top_filepath)
        
        return jsonify({'code': 404, 'message': '图片不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/images/<filename>', methods=['DELETE'])
def delete_image(dataset_id, filename):
    try:
        # 首先尝试使用原始文件名
        for split in ['train', 'valid', 'test']:
            filepath = DATASETS_DIR / dataset_id / split / 'images' / filename
            if filepath.exists():
                filepath.unlink()
                label_file = filepath.parent.parent / 'labels' / (filepath.stem + '.txt')
                if label_file.exists():
                    label_file.unlink()
                return jsonify({'code': 200, 'message': '图片已删除'})
        
        top_filepath = DATASETS_DIR / dataset_id / 'images' / filename
        if top_filepath.exists():
            top_filepath.unlink()
            top_label_file = DATASETS_DIR / dataset_id / 'labels' / (top_filepath.stem + '.txt')
            if top_label_file.exists():
                top_label_file.unlink()
            return jsonify({'code': 200, 'message': '图片已删除'})
        
        # 如果原始文件名不存在，尝试使用安全文件名
        secure_filename_try = secure_filename(filename)
        if secure_filename_try != filename:
            for split in ['train', 'valid', 'test']:
                filepath = DATASETS_DIR / dataset_id / split / 'images' / secure_filename_try
                if filepath.exists():
                    filepath.unlink()
                    label_file = filepath.parent.parent / 'labels' / (filepath.stem + '.txt')
                    if label_file.exists():
                        label_file.unlink()
                    return jsonify({'code': 200, 'message': '图片已删除'})
            
            top_filepath = DATASETS_DIR / dataset_id / 'images' / secure_filename_try
            if top_filepath.exists():
                top_filepath.unlink()
                top_label_file = DATASETS_DIR / dataset_id / 'labels' / (top_filepath.stem + '.txt')
                if top_label_file.exists():
                    top_label_file.unlink()
                return jsonify({'code': 200, 'message': '图片已删除'})
        
        return jsonify({'code': 404, 'message': '图片不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/labels', methods=['POST'])
def upload_label(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            return jsonify({'code': 404, 'message': '数据集不存在'}), 404
        
        if 'file' not in request.files:
            data = request.json
            if data and 'content' in data:
                filename = data.get('name', f'{uuid.uuid4().hex[:8]}.txt')
                split = data.get('split', 'train')
                content = data['content']
                
                labels_dir = dataset_dir / split / 'labels'
                labels_dir.mkdir(parents=True, exist_ok=True)
                
                filepath = labels_dir / secure_filename(filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return jsonify({
                    'code': 200,
                    'data': {
                        'id': filepath.stem,
                        'name': filename,
                        'size': filepath.stat().st_size,
                        'split': split
                    }
                })
            return jsonify({'code': 400, 'message': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 400, 'message': '没有选择文件'}), 400
        
        split = request.form.get('split', 'train')
        filename = file.filename
        # 先提取文件名，去除路径部分，再进行安全处理
        filename = get_filename(filename)
        secure_name = secure_filename(filename)
        
        labels_dir = dataset_dir / split / 'labels'
        labels_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = labels_dir / secure_name
        file.save(filepath)
        
        return jsonify({
            'code': 200,
            'data': {
                'id': filepath.stem,
                'name': filename,
                'size': filepath.stat().st_size,
                'split': split
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/labels/<filename>', methods=['GET'])
def get_label(dataset_id, filename):
    try:
        # 首先尝试使用原始文件名
        for split in ['train', 'valid', 'test']:
            filepath = DATASETS_DIR / dataset_id / split / 'labels' / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return jsonify({'code': 200, 'data': {'content': f.read()}})
        
        # 如果原始文件名不存在，尝试使用安全文件名
        secure_filename_try = secure_filename(filename)
        if secure_filename_try != filename:
            for split in ['train', 'valid', 'test']:
                filepath = DATASETS_DIR / dataset_id / split / 'labels' / secure_filename_try
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        return jsonify({'code': 200, 'data': {'content': f.read()}})
        
        return jsonify({'code': 404, 'message': '标签文件不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/labels/<filename>', methods=['DELETE'])
def delete_label(dataset_id, filename):
    try:
        # 首先尝试使用原始文件名
        for split in ['train', 'valid', 'test']:
            filepath = DATASETS_DIR / dataset_id / split / 'labels' / filename
            if filepath.exists():
                filepath.unlink()
                return jsonify({'code': 200, 'message': '标签文件已删除'})
        
        # 如果原始文件名不存在，尝试使用安全文件名
        secure_filename_try = secure_filename(filename)
        if secure_filename_try != filename:
            for split in ['train', 'valid', 'test']:
                filepath = DATASETS_DIR / dataset_id / split / 'labels' / secure_filename_try
                if filepath.exists():
                    filepath.unlink()
                    return jsonify({'code': 200, 'message': '标签文件已删除'})
        
        return jsonify({'code': 404, 'message': '标签文件不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/yaml', methods=['POST'])
def upload_yaml(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            return jsonify({'code': 404, 'message': '数据集不存在'}), 404
        
        yaml_content = None
        
        if 'file' not in request.files:
            data = request.json
            if data and 'content' in data:
                content = data['content']
                
                import yaml
                yaml_content = yaml.safe_load(content)
            else:
                return jsonify({'code': 400, 'message': '没有文件'}), 400
        else:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'code': 400, 'message': '没有选择文件'}), 400
            
            import yaml
            yaml_content = yaml.safe_load(file.stream)
        
        if yaml_content is None:
            return jsonify({'code': 400, 'message': 'YAML内容无效'}), 400
        
        yaml_content['path'] = '.'
        yaml_content['train'] = 'train/images'
        yaml_content['val'] = 'valid/images'
        yaml_content['test'] = 'test/images'
        
        import yaml
        filepath = dataset_dir / 'data.yaml'
        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)
        
        classes = []
        if yaml_content.get('names'):
            if isinstance(yaml_content['names'], list):
                classes = yaml_content['names']
            elif isinstance(yaml_content['names'], dict):
                classes = list(yaml_content['names'].values())
        
        return jsonify({
            'code': 200,
            'data': {
                'fileName': 'data.yaml',
                'classCount': len(classes),
                'classes': classes,
                'path': yaml_content.get('path', ''),
                'train': yaml_content.get('train', ''),
                'val': yaml_content.get('val', ''),
                'test': yaml_content.get('test', '')
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/yaml', methods=['DELETE'])
def delete_yaml(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        yaml_file = find_yaml_file(dataset_dir)
        if yaml_file and yaml_file.exists():
            yaml_file.unlink()
            return jsonify({'code': 200, 'message': 'YAML文件已删除'})
        return jsonify({'code': 404, 'message': 'YAML文件不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/split', methods=['POST'])
def auto_split(dataset_id):
    try:
        dataset_dir = DATASETS_DIR / dataset_id
        if not dataset_dir.exists():
            return jsonify({'code': 404, 'message': '数据集不存在'}), 404
        
        data = request.json
        split_mode = data.get('mode', 'ratio')
        test_ratio = data.get('testRatio', 0.1)
        test_count = data.get('testCount', 10)
        valid_ratio = data.get('validRatio', 0.1)
        valid_count = data.get('validCount', 10)
        
        import random
        from collections import defaultdict
        
        all_images = []
        for split in ['train', 'valid', 'test']:
            images_dir = dataset_dir / split / 'images'
            if images_dir.exists():
                for img in images_dir.iterdir():
                    if img.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.tif']:
                        all_images.append((img, split))
        
        top_images_dir = dataset_dir / 'images'
        if top_images_dir.exists():
            for img in top_images_dir.iterdir():
                if img.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.tif']:
                    all_images.append((img, 'top'))
        
        def find_label_file(img_path, old_split):
            label_file = None
            if old_split == 'top':
                candidate_label = dataset_dir / 'labels' / (img_path.stem + '.txt')
                if candidate_label.exists():
                    label_file = candidate_label
            else:
                candidate_label = dataset_dir / old_split / 'labels' / (img_path.stem + '.txt')
                if candidate_label.exists():
                    label_file = candidate_label
            
            if not label_file:
                for split_dir in ['train', 'valid', 'test']:
                    candidate_label = dataset_dir / split_dir / 'labels' / (img_path.stem + '.txt')
                    if candidate_label.exists():
                        label_file = candidate_label
                        break
                if not label_file:
                    candidate_label = dataset_dir / 'labels' / (img_path.stem + '.txt')
                    if candidate_label.exists():
                        label_file = candidate_label
            return label_file
        
        def get_primary_class_id(label_file):
            if label_file and label_file.exists():
                try:
                    with open(label_file, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line:
                            parts = first_line.split()
                            if parts:
                                return int(parts[0])
                except:
                    pass
            return -1
        
        image_class_map = {}
        for img, old_split in all_images:
            label_file = find_label_file(img, old_split)
            class_id = get_primary_class_id(label_file)
            image_class_map[img] = {
                'old_split': old_split,
                'label_file': label_file,
                'class_id': class_id
            }
        
        class_to_images = defaultdict(list)
        for img, info in image_class_map.items():
            class_to_images[info['class_id']].append(img)
        
        for class_id, images in class_to_images.items():
            random.shuffle(images)
        
        total_count = len(all_images)
        
        if split_mode == 'count':
            num_valid_total = min(valid_count, total_count)
            num_test_total = min(test_count, total_count - num_valid_total)
        else:
            num_valid_total = int(total_count * valid_ratio)
            num_test_total = int(total_count * test_ratio)
        
        train_images = []
        valid_images = []
        test_images = []
        
        for class_id, images in class_to_images.items():
            n = len(images)
            if split_mode == 'count':
                class_valid = max(1, int(n * num_valid_total / total_count)) if n > 1 else 0
                class_test = max(1, int(n * num_test_total / total_count)) if n > 2 else 0
            else:
                class_valid = int(n * valid_ratio)
                class_test = int(n * test_ratio)
            
            class_valid = min(class_valid, n - 1) if n > 1 else 0
            class_test = min(class_test, n - class_valid - 1) if n > class_valid + 1 else 0
            
            valid_images.extend(images[:class_valid])
            test_images.extend(images[class_valid:class_valid + class_test])
            train_images.extend(images[class_valid + class_test:])
        
        def move_image_and_label(img, target_split):
            info = image_class_map[img]
            
            new_images_dir = dataset_dir / target_split / 'images'
            new_images_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(img), str(new_images_dir / img.name))
            
            if info['label_file']:
                new_labels_dir = dataset_dir / target_split / 'labels'
                new_labels_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(info['label_file']), str(new_labels_dir / info['label_file'].name))
        
        for img in train_images:
            move_image_and_label(img, 'train')
        
        for img in valid_images:
            move_image_and_label(img, 'valid')
        
        for img in test_images:
            move_image_and_label(img, 'test')
        
        train_count = len(list((dataset_dir / 'train' / 'images').glob('*'))) if (dataset_dir / 'train' / 'images').exists() else 0
        valid_count = len(list((dataset_dir / 'valid' / 'images').glob('*'))) if (dataset_dir / 'valid' / 'images').exists() else 0
        test_count = len(list((dataset_dir / 'test' / 'images').glob('*'))) if (dataset_dir / 'test' / 'images').exists() else 0
        
        class_distribution = {}
        for split in ['train', 'valid', 'test']:
            labels_dir = dataset_dir / split / 'labels'
            if labels_dir.exists():
                class_counts = defaultdict(int)
                for label_file in labels_dir.glob('*.txt'):
                    class_id = get_primary_class_id(label_file)
                    if class_id >= 0:
                        class_counts[class_id] += 1
                class_distribution[split] = dict(class_counts)
        
        return jsonify({
            'code': 200,
            'message': f'数据集划分完成！训练集 {train_count} 张，验证集 {valid_count} 张，测试集 {test_count} 张',
            'data': {
                'trainCount': train_count, 
                'validCount': valid_count, 
                'testCount': test_count,
                'classDistribution': class_distribution
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

if __name__ == '__main__':
    print("=" * 70)
    print("数据集存储服务器")
    print("=" * 70)
    print(f"数据集存储目录: {DATASETS_DIR}")
    print("=" * 70)
    
    if HAS_HTTPS_SUPPORT:
        run_https_server(app, host='0.0.0.0', port=5006, debug=False)
    else:
        app.run(host='0.0.0.0', port=5006, debug=False)
