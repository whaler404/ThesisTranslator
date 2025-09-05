import axios from 'axios';
import { FileItem, Task, TaskResponse, PaperDownloadRequest, TranslationRequest, TranslationConfig, LogEntry } from '@/types/api';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const fileApi = {
  // 获取文件列表
  getFiles: async (): Promise<FileItem[]> => {
    const response = await api.get('/files');
    return response.data.files;
  },

  // 上传文件
  uploadFile: async (file: File, customName: string, config?: TranslationConfig): Promise<TaskResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/upload?custom_name=${encodeURIComponent(customName)}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: config,
    });
    return response.data;
  },

  // 下载论文
  downloadPaper: async (request: PaperDownloadRequest, config?: TranslationConfig): Promise<TaskResponse> => {
    const response = await api.post('/download-paper', request, {
      params: config,
    });
    return response.data;
  },

  // 重命名文件
  renameFile: async (objectName: string, newName: string): Promise<{ success: boolean; message: string; new_name?: string }> => {
    const response = await api.put(`/files/${objectName}/rename`, { new_name: newName });
    return response.data;
  },

  // 删除文件
  deleteFile: async (objectName: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/files/${objectName}`);
    return response.data;
  },

  // 下载文件
  downloadFile: async (objectName: string): Promise<Blob> => {
    const response = await api.get(`/download/${objectName}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export const taskApi = {
  // 获取所有任务
  getTasks: async (): Promise<{ success: boolean; tasks: Task[] }> => {
    const response = await api.get('/tasks');
    return response.data;
  },

  // 获取任务状态
  getTaskStatus: async (taskId: string): Promise<{ success: boolean; task: Task }> => {
    const response = await api.get(`/status/${taskId}`);
    return response.data;
  },

  // 获取任务日志
  getTaskLogs: async (taskId: string): Promise<{ success: boolean; logs: LogEntry[] }> => {
    const response = await api.get(`/logs/${taskId}`);
    return response.data;
  },

  // 开始翻译
  startTranslation: async (request: TranslationRequest): Promise<TaskResponse> => {
    const response = await api.post('/translate', request);
    return response.data;
  },

  // 删除任务
  deleteTask: async (taskId: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/tasks/${taskId}`);
    return response.data;
  },
};

export default api;