#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import uuid
import threading
from datetime import datetime
from typing import Dict, Any
from flask import Flask, request, jsonify, render_template, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import ThesisTranslator

# 配置Flask应用
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'thesis-translator-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 配置CORS - 允许所有来源和方法
cors = CORS(app,
     origins="*",  # 允许所有来源
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 允许所有HTTP方法
     allow_headers=["*", "Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],  # 允许所有请求头
     supports_credentials=True,  # 支持凭证
     expose_headers=["*", "Content-Disposition", "Content-Type"],  # 暴露所有响应头
     max_age=3600  # 预检请求缓存1小时
)

# 添加全局响应头处理，解决跨域问题
@app.after_request
def after_request(response):
    """全局响应头处理，解决跨域问题"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Expose-Headers', '*')
    return response

# 添加OPTIONS预检请求处理
@app.before_request
def handle_preflight():
    """处理OPTIONS预检请求"""
    if request.method == "OPTIONS":
        response = jsonify({'success': True, 'message': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Expose-Headers', '*')
        response.headers.add('Access-Control-Max-Age', '3600')
        return response

# 配置上传和输出目录
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf'}

# 全局变量存储任务状态
tasks = {}
task_logs = {}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class TaskLogger(logging.Handler):
    """自定义日志处理器，用于收集任务日志"""
    
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id
        self.logs = []
    
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage()
        }
        self.logs.append(log_entry)
        
        # 保持最新100条日志
        if len(self.logs) > 100:
            self.logs.pop(0)
        
        # 存储到全局字典
        if self.task_id not in task_logs:
            task_logs[self.task_id] = []
        task_logs[self.task_id] = self.logs.copy()

def run_translation_task(task_id: str, pdf_path: str, output_path: str, config: Dict[str, Any]):
    """在后台运行翻译任务"""
    try:
        # 更新任务状态
        tasks[task_id]['status'] = 'processing'
        tasks[task_id]['stage'] = 'initializing'
        tasks[task_id]['progress'] = 0
        
        # 创建任务特定的日志处理器
        task_logger = TaskLogger(task_id)
        
        # 为根日志记录器添加我们的处理器，以捕获所有日志
        root_logger = logging.getLogger()
        root_logger.addHandler(task_logger)
        root_logger.setLevel(logging.INFO)
        
        # 同时为任务特定的日志记录器添加处理器
        task_logger_instance = logging.getLogger(f'task_{task_id}')
        task_logger_instance.addHandler(task_logger)
        task_logger_instance.setLevel(logging.INFO)
        
        logger = logging.getLogger(__name__)
        logger.info("开始翻译任务")
        
        # 创建翻译器实例
        translator = ThesisTranslator(**config)
        
        # 更新进度
        tasks[task_id]['stage'] = 'pdf_parsing'
        tasks[task_id]['progress'] = 10
        logger.info("正在解析PDF文件...")
        
        # 执行翻译
        success = translator.translate_pdf(pdf_path, output_path)
        
        if success:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            tasks[task_id]['output_file'] = output_path
            logger.info("翻译任务成功完成")
        else:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['error'] = "翻译过程失败"
            logger.error("翻译任务失败")
            
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        logger = logging.getLogger(__name__)
        logger.error(f"翻译任务异常: {e}")
    finally:
        # 清理：移除日志处理器
        root_logger = logging.getLogger()
        if task_logger in root_logger.handlers:
            root_logger.removeHandler(task_logger)
            
        task_logger_instance = logging.getLogger(f'task_{task_id}')
        if task_logger in task_logger_instance.handlers:
            task_logger_instance.removeHandler(task_logger)

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """文件上传接口"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '只支持PDF文件'}), 400
        
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存文件
        filename = secure_filename(file.filename)
        upload_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{filename}")
        file.save(upload_path)
        
        # 生成输出文件路径
        output_filename = f"{task_id}_{filename.rsplit('.', 1)[0]}.md"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # 获取配置参数
        config = {
            'model': request.form.get('model', 'qwen-flash'),
            'chunk_size': int(request.form.get('chunk_size', 1000)),
            'max_retries': int(request.form.get('max_retries', 3)),
            'temperature': float(request.form.get('temperature', 0.3)),
            'timeout': int(request.form.get('timeout', 60)),
            'include_toc': request.form.get('include_toc', 'true').lower() == 'true',
            'include_metadata': request.form.get('include_metadata', 'true').lower() == 'true'
        }
        
        # 创建任务记录
        tasks[task_id] = {
            'id': task_id,
            'filename': filename,
            'status': 'queued',
            'stage': 'waiting',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'upload_path': upload_path,
            'output_path': output_path,
            'config': config
        }
        
        # 在后台启动翻译任务
        thread = threading.Thread(
            target=run_translation_task,
            args=(task_id, upload_path, output_path, config)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '文件上传成功，翻译任务已开始'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in tasks:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    task = tasks[task_id].copy()
    
    # 添加日志信息
    if task_id in task_logs:
        task['logs'] = task_logs[task_id][-10:]  # 最近10条日志
    else:
        task['logs'] = []
    
    return jsonify({'success': True, 'task': task})

@app.route('/api/logs/<task_id>')
def get_task_logs(task_id):
    """获取任务完整日志"""
    if task_id not in tasks:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    logs = task_logs.get(task_id, [])
    return jsonify({'success': True, 'logs': logs})

@app.route('/api/download/<task_id>')
def download_file(task_id):
    """下载翻译结果"""
    if task_id not in tasks:
        abort(404)
    
    task = tasks[task_id]
    if task['status'] != 'completed':
        abort(400)
    
    output_path = task['output_path']
    if not os.path.exists(output_path):
        abort(404)
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"translated_{task['filename'].rsplit('.', 1)[0]}.md"
    )

@app.route('/api/tasks')
def get_all_tasks():
    """获取所有任务列表"""
    task_list = []
    for task_id, task in tasks.items():
        task_summary = {
            'id': task_id,
            'filename': task['filename'],
            'status': task['status'],
            'progress': task.get('progress', 0),
            'created_at': task['created_at']
        }
        task_list.append(task_summary)
    
    # 按创建时间倒序排列
    task_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({'success': True, 'tasks': task_list})

@app.route('/api/delete/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务和相关文件"""
    if task_id not in tasks:
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    task = tasks[task_id]
    
    try:
        # 删除上传的文件
        if os.path.exists(task['upload_path']):
            os.remove(task['upload_path'])
        
        # 删除输出文件
        if 'output_path' in task and os.path.exists(task['output_path']):
            os.remove(task['output_path'])
        
        # 删除任务记录
        del tasks[task_id]
        
        # 删除日志记录
        if task_id in task_logs:
            del task_logs[task_id]
        
        return jsonify({'success': True, 'message': '任务已删除'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    print("启动英文论文翻译器Web服务...")
    print("访问地址: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)