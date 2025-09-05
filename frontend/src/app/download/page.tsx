'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/MainLayout';
import { fileApi } from '@/utils/api';
import { sanitizeFileName } from '@/utils/fileUtils';
import { Upload, Link, AlertCircle, CheckCircle, Loader2, Download as DownloadIcon } from 'lucide-react';

export default function DownloadPage() {
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [existingFiles, setExistingFiles] = useState<string[]>([]);
  const [url, setUrl] = useState('');
  const [objectName, setObjectName] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'warning'; text: string } | null>(null);

  useEffect(() => {
    loadExistingFiles();
  }, []);

  const loadExistingFiles = async () => {
    try {
      const files = await fileApi.getFiles();
      setExistingFiles(files.map(f => f.name));
    } catch (error) {
      console.error('加载文件列表失败:', error);
    }
  };

  const checkFileExists = (fileName: string): boolean => {
    return existingFiles.includes(fileName);
  };

  const showMessage = (type: 'success' | 'error' | 'warning', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleFileUpload = async (file: File) => {
    const fileName = sanitizeFileName(file.name);
    
    if (checkFileExists(fileName)) {
      showMessage('warning', `文件 "${fileName}" 已存在，无需重复上传`);
      return false;
    }

    setUploading(true);
    try {
      const result = await fileApi.uploadFile(file);
      if (result.success) {
        showMessage('success', '文件上传成功');
        loadExistingFiles();
      } else {
        showMessage('error', result.error || '上传失败');
      }
    } catch (error) {
      showMessage('error', '上传失败');
      console.error('上传错误:', error);
    } finally {
      setUploading(false);
    }
    return false;
  };

  const handleUrlDownload = async () => {
    if (!url.trim()) {
      showMessage('error', '请输入论文链接');
      return;
    }

    const fileName = sanitizeFileName(objectName || url.split('/').pop() || 'unknown.pdf');
    
    if (checkFileExists(fileName)) {
      showMessage('warning', `文件 "${fileName}" 已存在，无需重复下载`);
      return;
    }

    setDownloading(true);
    try {
      const result = await fileApi.downloadPaper({ url, object_name: fileName });
      if (result.success) {
        showMessage('success', '论文下载成功');
        loadExistingFiles();
        setUrl('');
        setObjectName('');
      } else {
        showMessage('error', result.error || '下载失败');
      }
    } catch (error) {
      showMessage('error', '下载失败');
      console.error('下载错误:', error);
    } finally {
      setDownloading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="card p-6">
          <h2 className="text-2xl font-bold mb-6">下载论文到 MinIO</h2>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
              <p className="text-blue-800 text-sm">
                系统会自动检查文件是否已存在，避免重复下载。文件名中的空格会自动替换为下划线。
              </p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* 文件上传 */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Upload className="h-5 w-5 mr-2" />
                上传 PDF 文件
              </h3>
              
              <div
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition-colors duration-200"
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onDragEnter={(e) => e.preventDefault()}
              >
                {uploading ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="h-12 w-12 animate-spin text-primary-600 mb-4" />
                    <p className="text-gray-600">上传中...</p>
                  </div>
                ) : (
                  <>
                    <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-lg font-medium text-gray-700 mb-2">
                      拖拽文件到此处或点击选择
                    </p>
                    <p className="text-sm text-gray-500 mb-4">
                      仅支持 PDF 文件
                    </p>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="file-upload"
                    />
                    <label
                      htmlFor="file-upload"
                      className="btn btn-primary cursor-pointer"
                    >
                      选择文件
                    </label>
                  </>
                )}
              </div>
            </div>

            {/* URL 下载 */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Link className="h-5 w-5 mr-2" />
                提供论文链接
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                    论文链接 *
                  </label>
                  <input
                    type="url"
                    id="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://arxiv.org/pdf/xxxx.pdf"
                    className="input"
                    disabled={downloading}
                  />
                </div>
                
                <div>
                  <label htmlFor="object_name" className="block text-sm font-medium text-gray-700 mb-2">
                    文件名（可选）
                  </label>
                  <input
                    type="text"
                    id="object_name"
                    value={objectName}
                    onChange={(e) => setObjectName(e.target.value)}
                    placeholder="论文文件名.pdf"
                    className="input"
                    disabled={downloading}
                  />
                </div>
                
                <button
                  onClick={handleUrlDownload}
                  disabled={downloading || !url.trim()}
                  className="btn btn-primary w-full flex items-center justify-center"
                >
                  {downloading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      下载中...
                    </>
                  ) : (
                    <>
                      <DownloadIcon className="h-4 w-4 mr-2" />
                      下载论文
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 消息提示 */}
        {message && (
          <div className={`fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
            message.type === 'success' ? 'bg-green-100 border border-green-400 text-green-700' :
            message.type === 'error' ? 'bg-red-100 border border-red-400 text-red-700' :
            'bg-yellow-100 border border-yellow-400 text-yellow-700'
          }`}>
            <div className="flex items-center">
              {message.type === 'success' && <CheckCircle className="h-5 w-5 mr-2" />}
              {message.type === 'error' && <AlertCircle className="h-5 w-5 mr-2" />}
              {message.type === 'warning' && <AlertCircle className="h-5 w-5 mr-2" />}
              {message.text}
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}