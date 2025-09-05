'use client';

import { useState, useEffect } from 'react';
import MainLayout from '@/components/MainLayout';
import { fileApi } from '@/utils/api';
import { sortFiles, searchFiles, isPdfFile, isMarkdownFile, getTranslationName, formatFileSize, formatDate } from '@/utils/fileUtils';
import { 
  FolderOpen, 
  Eye, 
  Download, 
  Trash2, 
  Edit3,
  Search,
  Filter,
  FileText,
  CheckCircle,
  Clock,
  Loader2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import InlineMath from 'react-latex-next';
import BlockMath from 'react-latex-next';

export default function FilesPage() {
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<any[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [sortBy, setSortBy] = useState<'name' | 'translated' | 'date'>('name');
  const [searchQuery, setSearchQuery] = useState('');
  const [previewMode, setPreviewMode] = useState<'pdf' | 'md' | 'both'>('both');
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [newName, setNewName] = useState('');
  const [renaming, setRenaming] = useState(false);

  useEffect(() => {
    loadFiles();
  }, []);

  useEffect(() => {
    let result = files;
    
    if (searchQuery) {
      result = searchFiles(result, searchQuery);
    }
    
    result = sortFiles(result, sortBy);
    setFilteredFiles(result);
  }, [files, searchQuery, sortBy]);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const fileList = await fileApi.getFiles();
      setFiles(fileList);
    } catch (error) {
      console.error('加载文件列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = (file: any) => {
    setSelectedFile(file);
  };

  const handleDelete = async (fileName: string, deleteTranslation = false) => {
    try {
      await fileApi.deleteFile(fileName);
      
      if (deleteTranslation && isPdfFile(fileName)) {
        const translationName = getTranslationName(fileName);
        try {
          await fileApi.deleteFile(translationName);
        } catch (error) {
          console.error('删除翻译文件失败:', error);
        }
      }
      
      loadFiles();
      if (selectedFile?.name === fileName) {
        setSelectedFile(null);
      }
    } catch (error) {
      console.error('删除错误:', error);
    }
  };

  const handleDownload = async (fileName: string) => {
    try {
      const blob = await fileApi.downloadFile(fileName);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载错误:', error);
    }
  };

  const handleRename = async () => {
    if (!selectedFile || !newName.trim()) return;
    
    setRenaming(true);
    try {
      const result = await fileApi.renameFile(selectedFile.name, newName);
      if (result.success) {
        // 更新文件列表
        await loadFiles();
        // 更新选中的文件信息
        const updatedFile = {
          ...selectedFile,
          name: result.new_name || newName
        };
        setSelectedFile(updatedFile);
        setRenameModalVisible(false);
        setNewName('');
      } else {
        alert('重命名失败: ' + (result.message || '未知错误'));
      }
    } catch (error) {
      console.error('重命名失败:', error);
      alert('重命名失败: ' + (error as Error).message);
    } finally {
      setRenaming(false);
    }
  };

  const showRenameModal = (file: any) => {
    setSelectedFile(file);
    // 显示文件名但不包括扩展名
    const displayName = file.name.replace(/\.[^/.]+$/, '');
    setNewName(displayName);
    setRenameModalVisible(true);
  };

  const getFileColor = (file: any) => {
    if (file.has_translation) return 'text-blue-600';
    return 'text-green-600';
  };

  const getFileTag = (file: any) => {
    if (file.has_translation) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <CheckCircle className="h-3 w-3 mr-1" />
          已翻译
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
        <Clock className="h-3 w-3 mr-1" />
        未翻译
      </span>
    );
  };

  const renderPDFPreview = () => {
    if (!selectedFile || !isPdfFile(selectedFile.name)) return null;

    const fileUrl = `/api/download/${selectedFile.name}`;

    return (
      <div className="file-preview-left">
        <h4 className="font-medium mb-4 flex items-center">
          <FileText className="h-4 w-4 mr-2" />
          PDF 预览
        </h4>
        <div className="h-[calc(100%-2rem)]">
          <iframe
            src={fileUrl}
            className="pdf-viewer"
            title={selectedFile.name}
            sandbox="allow-same-origin allow-scripts allow-forms"
          />
        </div>
      </div>
    );
  };

  const renderMarkdownPreview = () => {
    if (!selectedFile) return null;

    let markdownFileName = selectedFile.name;

    if (isPdfFile(selectedFile.name) && selectedFile.has_translation) {
      markdownFileName = getTranslationName(selectedFile.name);
    } else if (!isMarkdownFile(selectedFile.name)) {
      return null;
    }

    return (
      <div className="file-preview-right">
        <h4 className="font-medium mb-4 flex items-center">
          <FileText className="h-4 w-4 mr-2" />
          Markdown 预览
        </h4>
        <div className="h-[calc(100%-2rem)] overflow-auto">
          <MarkdownViewer fileName={markdownFileName} />
        </div>
      </div>
    );
  };

  return (
    <MainLayout>
      <div className="flex gap-6 h-[calc(100vh-8rem)]">
        {/* 文件列表 */}
        <div className="w-80">
          <div className="card p-4 h-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center">
                <FolderOpen className="h-5 w-5 mr-2" />
                文件列表
              </h3>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="name">按名称</option>
                <option value="translated">按翻译状态</option>
                <option value="date">按时间</option>
              </select>
            </div>
            
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索文件..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-10"
              />
            </div>
            
            <div className="space-y-2 max-h-[calc(100%-8rem)] overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary-600" />
                </div>
              ) : (
                filteredFiles.map((file) => (
                  <div
                    key={file.name}
                    className={`file-list-item p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                      selectedFile?.name === file.name
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleFileClick(file)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start flex-1 min-w-0">
                        <FolderOpen className={`h-4 w-4 mt-0.5 mr-2 flex-shrink-0 ${getFileColor(file)}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {file.name}
                          </p>
                          <div className="flex items-center mt-1 space-x-2">
                            {getFileTag(file)}
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatFileSize(file.size)}
                          </p>
                          <p className="text-xs text-gray-400">
                            {formatDate(file.last_modified)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
              
              {!loading && filteredFiles.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">未找到文件</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 文件预览 */}
        <div className="flex-1">
          <div className="card p-6 h-full">
            {selectedFile ? (
              <>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-semibold">{selectedFile.name}</h3>
                    {getFileTag(selectedFile)}
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDownload(selectedFile.name)}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="下载"
                    >
                      <Download className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => showRenameModal(selectedFile)}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="重命名"
                    >
                      <Edit3 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(selectedFile.name)}
                      className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="删除"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                    
                    {selectedFile.has_translation && (
                      <button
                        onClick={() => handleDelete(selectedFile.name, true)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="删除文件和翻译"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>

                {isPdfFile(selectedFile.name) && selectedFile.has_translation && (
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      预览模式
                    </label>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setPreviewMode('both')}
                        className={`px-3 py-1 rounded text-sm ${
                          previewMode === 'both'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        PDF + Markdown
                      </button>
                      <button
                        onClick={() => setPreviewMode('pdf')}
                        className={`px-3 py-1 rounded text-sm ${
                          previewMode === 'pdf'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        仅 PDF
                      </button>
                      <button
                        onClick={() => setPreviewMode('md')}
                        className={`px-3 py-1 rounded text-sm ${
                          previewMode === 'md'
                            ? 'bg-primary-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        仅 Markdown
                      </button>
                    </div>
                  </div>
                )}

                <div className="file-preview-container">
                  {(previewMode === 'both' || previewMode === 'pdf') && renderPDFPreview()}
                  {(previewMode === 'both' || previewMode === 'md') && renderMarkdownPreview()}
                </div>
              </>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">请选择一个文件进行预览</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 重命名模态框 */}
      {renameModalVisible && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">重命名文件</h3>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">当前文件: {selectedFile?.name}</p>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="input w-full"
                placeholder="新文件名（无需扩展名）"
                disabled={renaming}
              />
              <p className="text-xs text-gray-500 mt-1">
                系统会自动处理文件扩展名，重命名会同时处理PDF和对应的翻译文件
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleRename}
                disabled={renaming || !newName.trim()}
                className="btn btn-primary flex-1 flex items-center justify-center"
              >
                {renaming ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    重命名中...
                  </>
                ) : (
                  '确定'
                )}
              </button>
              <button
                onClick={() => {
                  setRenameModalVisible(false);
                  setNewName('');
                }}
                disabled={renaming}
                className="btn btn-secondary flex-1"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}

interface MarkdownViewerProps {
  fileName: string;
}

function MarkdownViewer({ fileName }: MarkdownViewerProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMarkdownContent();
  }, [fileName]);

  const loadMarkdownContent = async () => {
    try {
      const response = await fetch(`/api/download/${fileName}`);
      if (response.ok) {
        const text = await response.text();
        setContent(text);
      }
    } catch (error) {
      console.error('加载 Markdown 失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  // 处理 LaTeX 公式
  const processLatexFormulas = (text: string) => {
    // 处理行内公式 $formula$
    text = text.replace(/\$([^$]+)\$/g, (match, formula) => {
      try {
        return `<InlineMath math="${formula.replace(/"/g, '&quot;')}" />`;
      } catch (error) {
        return match;
      }
    });
    
    // 处理块级公式 $$formula$$
    text = text.replace(/\$\$([^$]+)\$\$/g, (match, formula) => {
      try {
        return `<BlockMath math="${formula.replace(/"/g, '&quot;')}" />`;
      } catch (error) {
        return match;
      }
    });
    
    return text;
  };

  const processedContent = processLatexFormulas(content);

  return (
    <div className="markdown-preview">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code(props: any) {
            const { inline, className, children, ...rest } = props;
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={tomorrow}
                language={match[1]}
                PreTag="div"
                {...rest}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className={className} {...rest}>
                {children}
              </code>
            );
          },
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}