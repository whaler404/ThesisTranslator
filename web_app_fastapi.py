#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import ThesisTranslator
from src.minio_client import create_minio_client_from_env
from src.minio_file_interface import create_minio_file_interface_from_env
from src.paper_downloader import create_paper_downloader_from_env

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic 模型
class TranslationConfig(BaseModel):
    model: str = "qwen-flash"
    chunk_size: int = 1000
    max_retries: int = 3
    temperature: float = 0.3
    timeout: int = 60
    include_toc: bool = True
    include_metadata: bool = True

class TaskResponse(BaseModel):
    success: bool
    task_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None

class TaskStatus(BaseModel):
    id: str
    filename: str
    status: str
    stage: str
    progress: int
    created_at: str
    config: Dict[str, Any]
    output_file: Optional[str] = None
    error: Optional[str] = None

class PaperDownloadRequest(BaseModel):
    url: str
    object_name: Optional[str] = None

class FileItem(BaseModel):
    name: str
    size: int
    last_modified: str
    has_translation: bool
    translation_name: Optional[str] = None

class FileListResponse(BaseModel):
    files: List[FileItem]

class TranslationRequest(BaseModel):
    object_name: str
    config: TranslationConfig = TranslationConfig()

# 配置FastAPI应用
app = FastAPI(
    title="Thesis Translator API",
    description="English thesis translation service with MinIO storage",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储任务状态
tasks: Dict[str, Dict[str, Any]] = {}
task_logs: Dict[str, List[Dict[str, Any]]] = {}

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

def run_translation_task(task_id: str, object_name: str, config: Dict[str, Any]):
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
        
        # 初始化MinIO组件
        minio_file_interface = create_minio_file_interface_from_env()
        
        # 检查是否已经翻译
        translation_name = object_name.rsplit('.', 1)[0] + '.md'
        if minio_file_interface.minio_client.file_exists(translation_name):
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['progress'] = 100
            tasks[task_id]['output_file'] = translation_name
            logger.info("文件已翻译，跳过翻译过程")
            return
        
        # 创建翻译器实例
        translator = ThesisTranslator(**config)
        
        # 更新进度
        tasks[task_id]['stage'] = 'downloading'
        tasks[task_id]['progress'] = 20
        logger.info("正在从MinIO下载文件...")
        
        # 从MinIO获取文件到临时路径
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            success = minio_file_interface.get_file_from_minio(object_name, temp_path)
            if not success:
                raise Exception("无法从MinIO获取文件")
            
            # 更新进度
            tasks[task_id]['stage'] = 'translating'
            tasks[task_id]['progress'] = 50
            logger.info("正在翻译文件...")
            
            # 执行翻译
            with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as output_temp:
                output_temp_path = output_temp.name
            
            success = translator.translate_pdf(temp_path, output_temp_path)
            
            if success:
                # 更新进度
                tasks[task_id]['stage'] = 'uploading'
                tasks[task_id]['progress'] = 90
                logger.info("正在上传翻译结果到MinIO...")
                
                # 上传翻译结果到MinIO
                minio_file_interface.minio_client.upload_file(output_temp_path, translation_name)
                
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['progress'] = 100
                tasks[task_id]['output_file'] = translation_name
                logger.info("翻译任务成功完成")
            else:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['error'] = "翻译过程失败"
                logger.error("翻译任务失败")
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if 'output_temp_path' in locals() and os.path.exists(output_temp_path):
                os.unlink(output_temp_path)
            
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        logger = logging.getLogger(__name__)
        logger.error(f"翻译任务异常: {e}")
    finally:
        # 清理：移除日志处理器
        root_logger = logging.getLogger()
        task_logger_instance = logging.getLogger(f'task_{task_id}')
        
        # 获取任务特定的日志处理器
        handlers_to_remove = []
        for handler in root_logger.handlers[:]:
            if isinstance(handler, TaskLogger) and handler.task_id == task_id:
                handlers_to_remove.append(handler)
        
        for handler in handlers_to_remove:
            root_logger.removeHandler(handler)
            task_logger_instance.removeHandler(handler)

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Thesis Translator API", "version": "1.0.0"}

@app.post("/api/upload", response_model=TaskResponse)
async def upload_file(
    custom_name: str,
    file: UploadFile = File(...), 
    config: TranslationConfig = Depends()
):
    """上传PDF文件到MinIO"""
    try:
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        if not custom_name or not custom_name.strip():
            raise HTTPException(status_code=400, detail="必须提供自定义文件名")
        
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            # 保存上传的文件
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # 初始化MinIO客户端
        minio_client = create_minio_client_from_env()
        
        # 处理文件名：使用自定义名称
        safe_filename = custom_name.replace(' ', '_')
        if not safe_filename.lower().endswith('.pdf'):
            safe_filename += '.pdf'
        
        # 检查文件名冲突并解决
        base_name = safe_filename[:-4]  # 移除.pdf扩展名
        object_name = safe_filename
        counter = 1
        
        while minio_client.file_exists(object_name):
            object_name = f"{base_name}_{counter}.pdf"
            counter += 1
        
        # 上传到MinIO
        success = minio_client.upload_file(temp_path, object_name)
        
        # 清理临时文件
        os.unlink(temp_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="文件上传到MinIO失败")
        
        # 创建任务记录
        tasks[task_id] = {
            'id': task_id,
            'filename': file.filename,
            'object_name': object_name,
            'status': 'queued',
            'stage': 'waiting',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'config': config.model_dump()
        }
        
        return TaskResponse(
            success=True,
            task_id=task_id,
            message="文件上传成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-paper", response_model=TaskResponse)
async def download_paper(request: PaperDownloadRequest, config: TranslationConfig = Depends()):
    """从URL下载论文到MinIO"""
    try:
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化论文下载器
        paper_downloader = create_paper_downloader_from_env()
        
        # 下载论文
        result = paper_downloader.download_paper(request.url, request.object_name)
        
        if not result:
            raise HTTPException(status_code=500, detail="论文下载失败")
        
        # 创建任务记录
        tasks[task_id] = {
            'id': task_id,
            'filename': result['object_name'],
            'object_name': result['object_name'],
            'status': 'queued',
            'stage': 'waiting',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'config': config.model_dump()
        }
        
        return TaskResponse(
            success=True,
            task_id=task_id,
            message="论文下载成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"论文下载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files", response_model=FileListResponse)
async def list_files():
    """获取MinIO中的文件列表"""
    try:
        # 初始化MinIO客户端
        minio_client = create_minio_client_from_env()
        
        # 获取文件列表
        files = minio_client.list_files()
        
        # 处理文件列表
        file_items = []
        pdf_files = [f for f in files if f['name'].lower().endswith('.pdf')]
        
        for pdf_file in pdf_files:
            # 检查是否有对应的翻译文件
            translation_name = pdf_file['name'].rsplit('.', 1)[0] + '.md'
            has_translation = any(f['name'] == translation_name for f in files)
            
            file_item = FileItem(
                name=pdf_file['name'],
                size=pdf_file['size'],
                last_modified=pdf_file['last_modified'].isoformat() if hasattr(pdf_file['last_modified'], 'isoformat') else str(pdf_file['last_modified']),
                has_translation=has_translation,
                translation_name=translation_name if has_translation else None
            )
            file_items.append(file_item)
        
        return FileListResponse(files=file_items)
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate", response_model=TaskResponse)
async def translate_file(request: TranslationRequest, background_tasks: BackgroundTasks):
    """翻译MinIO中的文件"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        tasks[task_id] = {
            'id': task_id,
            'filename': request.object_name,
            'object_name': request.object_name,
            'status': 'queued',
            'stage': 'waiting',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'config': request.config.model_dump()
        }
        
        # 在后台启动翻译任务
        background_tasks.add_task(run_translation_task, task_id, request.object_name, request.config.model_dump())
        
        return TaskResponse(
            success=True,
            task_id=task_id,
            message="翻译任务已开始"
        )
        
    except Exception as e:
        logger.error(f"启动翻译任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id].copy()
    
    # 添加日志信息
    if task_id in task_logs:
        task['logs'] = task_logs[task_id][-10:]  # 最近10条日志
    else:
        task['logs'] = []
    
    return {"success": True, "task": task}

@app.get("/api/logs/{task_id}")
async def get_task_logs(task_id: str):
    """获取任务完整日志"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    logs = task_logs.get(task_id, [])
    return {"success": True, "logs": logs}

@app.get("/api/download/{object_name}")
async def download_file(object_name: str):
    """从MinIO下载文件"""
    try:
        # 初始化MinIO文件接口
        minio_file_interface = create_minio_file_interface_from_env()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        # 从MinIO下载文件
        success = minio_file_interface.get_file_from_minio(object_name, temp_path)
        
        if not success:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 返回文件
        return FileResponse(
            temp_path,
            media_type='application/octet-stream',
            filename=object_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/files/{object_name}")
async def delete_file(object_name: str):
    """删除MinIO中的文件"""
    try:
        # 初始化MinIO客户端
        minio_client = create_minio_client_from_env()
        
        # 删除文件
        success = minio_client.delete_file(object_name)
        
        if not success:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 如果是PDF文件，同时删除对应的翻译文件
        if object_name.lower().endswith('.pdf'):
            translation_name = object_name.rsplit('.', 1)[0] + '.md'
            minio_client.delete_file(translation_name)
        
        return {"success": True, "message": "文件删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件删除失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RenameRequest(BaseModel):
    new_name: str

@app.put("/api/files/{object_name}/rename")
async def rename_file(object_name: str, request: RenameRequest):
    """重命名MinIO中的文件"""
    try:
        # 初始化MinIO客户端
        minio_client = create_minio_client_from_env()
        
        # 处理新文件名：替换空格为下划线，确保.pdf扩展名
        new_name = request.new_name.replace(' ', '_')
        if not new_name.lower().endswith('.pdf'):
            new_name += '.pdf'
        
        # 检查源文件是否存在
        if not minio_client.file_exists(object_name):
            raise HTTPException(status_code=404, detail="源文件不存在")
        
        # 检查目标文件是否已存在
        if minio_client.file_exists(new_name):
            raise HTTPException(status_code=400, detail="目标文件名已存在")
        
        # 重命名文件
        success = minio_client.rename_file(object_name, new_name)
        
        if not success:
            raise HTTPException(status_code=500, detail="文件重命名失败")
        
        # 如果是PDF文件，同时重命名对应的翻译文件
        if object_name.lower().endswith('.pdf'):
            old_translation_name = object_name.rsplit('.', 1)[0] + '.md'
            new_translation_name = new_name.rsplit('.', 1)[0] + '.md'
            
            if minio_client.file_exists(old_translation_name):
                minio_client.rename_file(old_translation_name, new_translation_name)
        
        return {"success": True, "message": "文件重命名成功", "new_name": new_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件重命名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks")
async def get_all_tasks():
    """获取所有任务列表"""
    task_list = []
    for task_id, task in tasks.items():
        task_summary = {
            'id': task_id,
            'filename': task.get('filename', task.get('object_name', '')),
            'status': task['status'],
            'progress': task.get('progress', 0),
            'created_at': task['created_at']
        }
        task_list.append(task_summary)
    
    # 按创建时间倒序排列
    task_list.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {"success": True, "tasks": task_list}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务记录"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 删除任务记录
    del tasks[task_id]
    
    # 删除日志记录
    if task_id in task_logs:
        del task_logs[task_id]
    
    return {"success": True, "message": "任务已删除"}

if __name__ == '__main__':
    print("启动英文论文翻译器FastAPI服务...")
    print("访问地址: http://localhost:8000")
    print("API文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "web_app_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )