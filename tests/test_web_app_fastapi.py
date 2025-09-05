#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import json

# 导入FastAPI应用
from web_app_fastapi import app

class TestFastAPIWebApp:
    """FastAPI Web应用测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Thesis Translator API"
    
    def test_upload_no_file(self):
        """测试没有文件的上传"""
        response = self.client.post("/api/upload")
        assert response.status_code == 422  # FastAPI验证错误
    
    def test_get_tasks_empty(self):
        """测试获取空任务列表"""
        response = self.client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["tasks"] == []
    
    def test_get_nonexistent_task_status(self):
        """测试获取不存在的任务状态"""
        response = self.client.get("/api/status/nonexistent-task")
        assert response.status_code == 404
    
    def test_get_nonexistent_task_logs(self):
        """测试获取不存在的任务日志"""
        response = self.client.get("/api/logs/nonexistent-task")
        assert response.status_code == 404
    
    def test_delete_nonexistent_task(self):
        """测试删除不存在的任务"""
        response = self.client.delete("/api/tasks/nonexistent-task")
        assert response.status_code == 404
    
    @patch('web_app_fastapi.create_minio_client_from_env')
    def test_list_files_minio_error(self, mock_create_client):
        """测试MinIO错误时的文件列表获取"""
        mock_create_client.side_effect = Exception("MinIO连接失败")
        
        response = self.client.get("/api/files")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    @patch('web_app_fastapi.create_minio_client_from_env')
    def test_list_files_success(self, mock_create_client):
        """测试成功获取文件列表"""
        # 模拟MinIO客户端
        mock_client = Mock()
        mock_client.list_files.return_value = [
            {'name': 'test.pdf', 'size': 1024, 'last_modified': '2024-01-01T00:00:00Z'},
            {'name': 'test.md', 'size': 512, 'last_modified': '2024-01-01T00:00:00Z'}
        ]
        mock_create_client.return_value = mock_client
        
        response = self.client.get("/api/files")
        assert response.status_code == 200
        data = response.json()
        assert data["files"][0]["name"] == "test.pdf"
        assert data["files"][0]["has_translation"] == True
    
    @patch('web_app_fastapi.create_paper_downloader_from_env')
    def test_download_paper_success(self, mock_create_downloader):
        """测试成功下载论文"""
        # 模拟论文下载器
        mock_downloader = Mock()
        mock_downloader.download_paper.return_value = {
            'object_name': 'test.pdf',
            'url': 'https://example.com/test.pdf',
            'size': 1024
        }
        mock_create_downloader.return_value = mock_downloader
        
        payload = {
            "url": "https://example.com/test.pdf",
            "object_name": "test.pdf"
        }
        
        response = self.client.post("/api/download-paper", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "task_id" in data
    
    @patch('web_app_fastapi.create_paper_downloader_from_env')
    def test_download_paper_failure(self, mock_create_downloader):
        """测试论文下载失败"""
        # 模拟论文下载器
        mock_downloader = Mock()
        mock_downloader.download_paper.return_value = None
        mock_create_downloader.return_value = mock_downloader
        
        payload = {
            "url": "https://example.com/test.pdf",
            "object_name": "test.pdf"
        }
        
        response = self.client.post("/api/download-paper", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    def test_translate_file_invalid_config(self):
        """测试无效配置的翻译请求"""
        payload = {
            "object_name": "test.pdf",
            "config": {
                "chunk_size": "invalid"  # 应该是整数
            }
        }
        
        response = self.client.post("/api/translate", json=payload)
        assert response.status_code == 422  # FastAPI验证错误
    
    def test_translate_file_valid_config(self):
        """测试有效配置的翻译请求"""
        payload = {
            "object_name": "test.pdf",
            "config": {
                "model": "gpt-3.5-turbo",
                "chunk_size": 1000,
                "temperature": 0.3
            }
        }
        
        response = self.client.post("/api/translate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "task_id" in data
    
    @patch('web_app_fastapi.create_minio_client_from_env')
    def test_delete_file_success(self, mock_create_client):
        """测试成功删除文件"""
        # 模拟MinIO客户端
        mock_client = Mock()
        mock_client.delete_file.return_value = True
        mock_create_client.return_value = mock_client
        
        response = self.client.delete("/api/files/test.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    @patch('web_app_fastapi.create_minio_client_from_env')
    def test_delete_file_failure(self, mock_create_client):
        """测试删除文件失败"""
        # 模拟MinIO客户端
        mock_client = Mock()
        mock_client.delete_file.return_value = False
        mock_create_client.return_value = mock_client
        
        response = self.client.delete("/api/files/test.pdf")
        assert response.status_code == 404

if __name__ == '__main__':
    pytest.main([__file__, '-v'])