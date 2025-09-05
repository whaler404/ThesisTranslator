'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/MainLayout';
import { fileApi, taskApi } from '@/utils/api';
import { getUntranslatedFiles } from '@/utils/fileUtils';
import { 
  Play, 
  Square, 
  Loader2, 
  FileText, 
  Settings,
  Activity,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import type { FileItem, Task, TranslationConfig } from '@/types/api';

export default function TranslatePage() {
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [taskInterval, setTaskInterval] = useState<NodeJS.Timeout | null>(null);

  // 配置状态
  const [config, setConfig] = useState<TranslationConfig>({
    model: 'qwen-flash',
    chunk_size: 1000,
    max_retries: 3,
    temperature: 0.3,
    timeout: 60,
    include_toc: true,
    include_metadata: true,
  });

  useEffect(() => {
    loadFiles();
    return () => {
      if (taskInterval) {
        clearInterval(taskInterval);
      }
    };
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const fileList = await fileApi.getFiles();
      setFiles(getUntranslatedFiles(fileList));
    } catch (error) {
      console.error('加载文件列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = (key: keyof TranslationConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const startTranslation = async () => {
    if (!selectedFile) {
      return;
    }

    setLoading(true);
    try {
      const result = await taskApi.startTranslation({
        object_name: selectedFile,
        config,
      });

      if (result.success && result.task_id) {
        setCurrentTask({
          id: result.task_id,
          filename: selectedFile,
          status: 'queued',
          stage: 'waiting',
          progress: 0,
          created_at: new Date().toISOString(),
          config,
        });
        startTaskMonitoring(result.task_id);
      }
    } catch (error) {
      console.error('翻译启动错误:', error);
    } finally {
      setLoading(false);
    }
  };

  const startTaskMonitoring = (taskId: string) => {
    if (taskInterval) {
      clearInterval(taskInterval);
    }

    const interval = setInterval(async () => {
      try {
        const taskResponse = await taskApi.getTaskStatus(taskId);
        if (taskResponse.success) {
          const task = taskResponse.task;
          setCurrentTask(task);
          
          if (task.status === 'completed' || task.status === 'failed') {
            clearInterval(interval);
            setTaskInterval(null);
            loadFiles();
          }
        }

        const logsResponse = await taskApi.getTaskLogs(taskId);
        if (logsResponse.success) {
          setLogs(logsResponse.logs);
        }
      } catch (error) {
        console.error('监控任务状态失败:', error);
      }
    }, 2000);

    setTaskInterval(interval);
  };

  const stopTask = () => {
    if (taskInterval) {
      clearInterval(taskInterval);
      setTaskInterval(null);
      setCurrentTask(null);
      setLogs([]);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'processing':
        return <Activity className="h-4 w-4 text-blue-600 animate-pulse" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case 'ERROR': return 'text-red-400';
      case 'WARNING': return 'text-yellow-400';
      case 'INFO': return 'text-green-400';
      default: return 'text-gray-300';
    }
  };

  return (
    <MainLayout>
      <div className="flex gap-6 h-[calc(100vh-8rem)]">
        {/* 文件选择 */}
        <div className="w-80">
          <div className="card p-4 h-full">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              选择文件
            </h3>
            
            <div className="space-y-2 max-h-[calc(100%-3rem)] overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                </div>
              ) : (
                files.map((file) => (
                  <div
                    key={file.name}
                    className={`file-list-item p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                      selectedFile === file.name
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedFile(file.name)}
                  >
                    <div className="flex items-start">
                      <FileText className="h-4 w-4 text-primary-600 mt-0.5 mr-2 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {!loading && files.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">暂无可翻译的文件</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 翻译配置和进度 */}
        <div className="flex-1">
          <div className="card p-6 h-full">
            <h3 className="text-lg font-semibold mb-6 flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              翻译配置
            </h3>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  模型
                </label>
                <select
                  value={config.model}
                  onChange={(e) => updateConfig('model', e.target.value)}
                  className="input"
                >
                  <option value="qwen-flash">Qwen Flash</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  块大小
                </label>
                <input
                  type="number"
                  min="100"
                  max="5000"
                  value={config.chunk_size}
                  onChange={(e) => updateConfig('chunk_size', parseInt(e.target.value))}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  最大重试次数
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={config.max_retries}
                  onChange={(e) => updateConfig('max_retries', parseInt(e.target.value))}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  温度
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => updateConfig('temperature', parseFloat(e.target.value))}
                  className="input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  超时时间(秒)
                </label>
                <input
                  type="number"
                  min="10"
                  max="300"
                  value={config.timeout}
                  onChange={(e) => updateConfig('timeout', parseInt(e.target.value))}
                  className="input"
                />
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.include_toc}
                    onChange={(e) => updateConfig('include_toc', e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">包含目录</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.include_metadata}
                    onChange={(e) => updateConfig('include_metadata', e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">包含元数据</span>
                </label>
              </div>
            </div>

            <div className="border-t pt-6">
              {currentTask ? (
                <div className="translation-progress">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-medium flex items-center">
                      {getStatusIcon(currentTask.status)}
                      <span className="ml-2">翻译进度</span>
                    </h4>
                    <span className="text-sm text-gray-600">
                      {currentTask.stage}
                    </span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                    <div
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${currentTask.progress}%` }}
                    />
                  </div>
                  
                  <div className="text-center">
                    <span className="text-2xl font-bold text-primary-600">
                      {currentTask.progress}%
                    </span>
                  </div>
                  
                  <button
                    onClick={stopTask}
                    className="btn btn-danger w-full mt-4 flex items-center justify-center"
                  >
                    <Square className="h-4 w-4 mr-2" />
                    停止任务
                  </button>
                </div>
              ) : (
                <button
                  onClick={startTranslation}
                  disabled={!selectedFile || loading}
                  className="btn btn-primary w-full flex items-center justify-center"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      准备中...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      开始翻译
                    </>
                  )}
                </button>
              )}
            </div>

            {logs.length > 0 && (
              <div className="log-container mt-6">
                <h4 className="text-sm font-medium text-gray-300 mb-2">翻译日志</h4>
                <div className="space-y-1">
                  {logs.slice(-20).map((log, index) => (
                    <div
                      key={index}
                      className={`log-entry text-xs ${getLogColor(log.level)}`}
                    >
                      [{log.timestamp}] {log.level}: {log.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}