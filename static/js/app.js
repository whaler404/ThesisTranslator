// 全局变量
let currentTaskId = null;
let statusUpdateInterval = null;
let logsVisible = false;

// DOM元素
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const submitBtn = document.getElementById('submitBtn');
const statusSection = document.getElementById('statusSection');
const logsSection = document.getElementById('logsSection');
const taskFileName = document.getElementById('taskFileName');
const taskStatus = document.getElementById('taskStatus');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const taskStage = document.getElementById('taskStage');
const downloadSection = document.getElementById('downloadSection');
const downloadBtn = document.getElementById('downloadBtn');
const logsList = document.getElementById('logsList');
const toggleLogs = document.getElementById('toggleLogs');
const historyList = document.getElementById('historyList');
const refreshHistory = document.getElementById('refreshHistory');
const notification = document.getElementById('notification');
const loadingOverlay = document.getElementById('loadingOverlay');

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    loadHistory();
});

// 初始化事件监听器
function initializeEventListeners() {
    // 文件上传相关
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // 表单提交
    uploadForm.addEventListener('submit', handleFormSubmit);
    
    // 日志切换
    toggleLogs.addEventListener('click', toggleLogsVisibility);
    
    // 下载按钮
    downloadBtn.addEventListener('click', downloadFile);
    
    // 刷新历史
    refreshHistory.addEventListener('click', loadHistory);
}

// 拖拽处理
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files: files } });
    }
}

// 文件选择处理
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    if (file.type !== 'application/pdf') {
        showNotification('请选择PDF文件', 'error');
        return;
    }
    
    // 验证文件大小 (100MB)
    if (file.size > 100 * 1024 * 1024) {
        showNotification('文件大小不能超过100MB', 'error');
        return;
    }
    
    // 显示文件信息
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileInfo.style.display = 'block';
    submitBtn.disabled = false;
    
    // 更新上传区域样式
    uploadArea.style.borderColor = '#059669';
    uploadArea.style.backgroundColor = '#ecfdf5';
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 表单提交处理
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!fileInput.files[0]) {
        showNotification('请先选择PDF文件', 'error');
        return;
    }
    
    // 显示加载状态
    showLoading(true);
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData(uploadForm);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentTaskId = result.task_id;
            showNotification(result.message, 'success');
            
            // 显示状态区域
            statusSection.style.display = 'block';
            logsSection.style.display = 'block';
            
            // 开始监控任务状态
            startStatusUpdate();
            
            // 滚动到状态区域
            statusSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('上传失败: ' + error.message, 'error');
    } finally {
        showLoading(false);
        submitBtn.disabled = false;
    }
}

// 开始状态更新
function startStatusUpdate() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    
    statusUpdateInterval = setInterval(updateTaskStatus, 2000);
    updateTaskStatus(); // 立即更新一次
}

// 更新任务状态
async function updateTaskStatus() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/status/${currentTaskId}`);
        const result = await response.json();
        
        if (result.success) {
            const task = result.task;
            updateStatusDisplay(task);
            updateLogsDisplay(task.logs || []);
            
            // 如果任务完成或失败，停止更新
            if (task.status === 'completed' || task.status === 'failed') {
                clearInterval(statusUpdateInterval);
                statusUpdateInterval = null;
                
                if (task.status === 'completed') {
                    downloadSection.style.display = 'block';
                    showNotification('翻译完成！', 'success');
                } else {
                    showNotification('翻译失败: ' + (task.error || '未知错误'), 'error');
                }
                
                // 刷新历史记录
                loadHistory();
            }
        }
    } catch (error) {
        console.error('Status update error:', error);
    }
}

// 更新状态显示
function updateStatusDisplay(task) {
    taskFileName.textContent = task.filename;
    
    // 更新状态标签
    taskStatus.textContent = getStatusText(task.status);
    taskStatus.className = `task-status status-${task.status}`;
    
    // 更新进度条
    const progress = task.progress || 0;
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    
    // 更新阶段信息
    taskStage.textContent = getStageText(task.stage);
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'queued': '排队中',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || status;
}

// 获取阶段文本
function getStageText(stage) {
    const stageMap = {
        'waiting': '等待中...',
        'initializing': '初始化...',
        'pdf_parsing': '解析PDF文件...',
        'text_chunking': '文本分块...',
        'text_cleaning': '文本清洗...',
        'text_sorting': '文本排序...',
        'translating': 'AI翻译中...',
        'generating_markdown': '生成Markdown...',
        'completed': '翻译完成'
    };
    return stageMap[stage] || stage;
}

// 更新日志显示
function updateLogsDisplay(logs) {
    if (!logs || logs.length === 0) return;
    
    logsList.innerHTML = '';
    
    logs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // 使用与后端一致的日志格式：时间 - 模块名 - 级别 - 消息
        logEntry.innerHTML = `
            <span class="log-timestamp">${log.timestamp}</span>
            <span class="log-name">${log.name || 'unknown'}</span>
            <span class="log-level ${log.level}">${log.level}</span>
            <span class="log-message">${escapeHtml(log.message)}</span>
        `;
        
        logsList.appendChild(logEntry);
    });
    
    // 滚动到底部
    logsList.scrollTop = logsList.scrollHeight;
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 切换日志显示
function toggleLogsVisibility() {
    logsVisible = !logsVisible;
    
    if (logsVisible) {
        toggleLogs.innerHTML = '<i class="fas fa-eye-slash"></i> 隐藏详细日志';
        // 加载完整日志
        loadFullLogs();
    } else {
        toggleLogs.innerHTML = '<i class="fas fa-eye"></i> 显示详细日志';
    }
}

// 加载完整日志
async function loadFullLogs() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/logs/${currentTaskId}`);
        const result = await response.json();
        
        if (result.success) {
            updateLogsDisplay(result.logs);
        }
    } catch (error) {
        console.error('Load logs error:', error);
    }
}

// 下载文件
async function downloadFile() {
    if (!currentTaskId) return;
    
    try {
        const response = await fetch(`/api/download/${currentTaskId}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `translated_${fileName.textContent.replace('.pdf', '.md')}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('文件下载成功', 'success');
        } else {
            throw new Error('下载失败');
        }
    } catch (error) {
        console.error('Download error:', error);
        showNotification('下载失败: ' + error.message, 'error');
    }
}

// 加载历史记录
async function loadHistory() {
    try {
        const response = await fetch('/api/tasks');
        const result = await response.json();
        
        if (result.success) {
            displayHistory(result.tasks);
        }
    } catch (error) {
        console.error('Load history error:', error);
    }
}

// 显示历史记录
function displayHistory(tasks) {
    if (!tasks || tasks.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>暂无历史任务</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = '';
    
    tasks.forEach(task => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const createdAt = new Date(task.created_at).toLocaleString('zh-CN');
        
        historyItem.innerHTML = `
            <div class="history-info">
                <h4>${escapeHtml(task.filename)}</h4>
                <div class="history-meta">
                    创建时间: ${createdAt} | 
                    状态: <span class="status-${task.status}">${getStatusText(task.status)}</span> |
                    进度: ${task.progress}%
                </div>
            </div>
            <div class="history-actions">
                ${task.status === 'completed' ? 
                    `<button class="btn btn-success btn-sm" onclick="downloadHistoryFile('${task.id}')">
                        <i class="fas fa-download"></i> 下载
                    </button>` : ''}
                <button class="btn btn-secondary btn-sm" onclick="deleteHistoryTask('${task.id}')">
                    <i class="fas fa-trash"></i> 删除
                </button>
            </div>
        `;
        
        historyList.appendChild(historyItem);
    });
}

// 下载历史文件
async function downloadHistoryFile(taskId) {
    try {
        const response = await fetch(`/api/download/${taskId}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `translated_${taskId}.md`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showNotification('文件下载成功', 'success');
        } else {
            throw new Error('下载失败');
        }
    } catch (error) {
        console.error('Download error:', error);
        showNotification('下载失败: ' + error.message, 'error');
    }
}

// 删除历史任务
async function deleteHistoryTask(taskId) {
    if (!confirm('确定要删除这个任务吗？这将删除所有相关文件。')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/delete/${taskId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('任务已删除', 'success');
            loadHistory();
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('删除失败: ' + error.message, 'error');
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// 显示/隐藏加载遮罩
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
});

// 工具函数：重置表单
function resetForm() {
    uploadForm.reset();
    fileInfo.style.display = 'none';
    submitBtn.disabled = true;
    uploadArea.style.borderColor = '#e5e7eb';
    uploadArea.style.backgroundColor = '#f8fafc';
    
    statusSection.style.display = 'none';
    logsSection.style.display = 'none';
    downloadSection.style.display = 'none';
    
    currentTaskId = null;
    
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
        statusUpdateInterval = null;
    }
}

// 导出全局函数（供HTML调用）
window.downloadHistoryFile = downloadHistoryFile;
window.deleteHistoryTask = deleteHistoryTask;