# Thesis Translator Frontend

基于 Next.js + React + Ant Design 的论文翻译系统前端。

## 功能特性

### 1. 下载页面 (/download)
- **文件上传**: 支持拖拽上传 PDF 文件到 MinIO
- **URL 下载**: 输入论文链接自动下载到 MinIO
- **重复检查**: 自动检查文件是否已存在，避免重复下载
- **文件名处理**: 自动将文件名中的空格替换为下划线

### 2. 翻译页面 (/translate)
- **文件选择**: 左侧列出所有未翻译的 PDF 文件
- **翻译配置**: 支持模型选择、块大小、温度等参数配置
- **实时监控**: 显示翻译进度、状态和日志
- **任务管理**: 支持启动、停止翻译任务

### 3. 文件管理页面 (/files)
- **文件列表**: 显示所有文件，用颜色区分翻译状态
- **排序搜索**: 支持按名称、翻译状态、时间排序和模糊搜索
- **文件预览**: 
  - PDF 在线预览
  - Markdown 渲染预览
  - 双栏对比显示
- **文件操作**: 下载、重命名、删除（支持批量删除）
- **预览模式**: 可选择仅 PDF、仅 Markdown 或双栏显示

## 技术栈

- **框架**: Next.js 14 + React 18
- **UI 库**: Ant Design 5
- **状态管理**: React Hooks
- **HTTP 客户端**: Axios
- **Markdown 渲染**: React Markdown + Remark GFM
- **代码高亮**: React Syntax Highlighter
- **PDF 预览**: React PDF
- **开发语言**: TypeScript

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 公共组件
│   │   └── MainLayout.tsx   # 主布局组件
│   ├── pages/              # 页面组件
│   │   ├── index.tsx       # 首页
│   │   ├── download.tsx    # 下载页面
│   │   ├── translate.tsx   # 翻译页面
│   │   └── files.tsx       # 文件管理页面
│   ├── types/              # TypeScript 类型定义
│   │   └── api.ts          # API 接口类型
│   ├── utils/              # 工具函数
│   │   ├── api.ts          # API 封装
│   │   └── fileUtils.ts    # 文件处理工具
│   └── styles/             # 样式文件
│       └── globals.css     # 全局样式
├── public/                 # 静态资源
├── package.json           # 依赖配置
├── next.config.js         # Next.js 配置
├── tsconfig.json          # TypeScript 配置
└── README.md              # 项目说明
```

## 安装和运行

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

3. 构建生产版本：
```bash
npm run build
npm start
```

## API 集成

前端通过 API 代理与后端 FastAPI 服务通信：

- 下载页面: `/api/upload`, `/api/download-paper`, `/api/files`
- 翻译页面: `/api/files`, `/api/translate`, `/api/status/{task_id}`, `/api/logs/{task_id}`
- 文件管理: `/api/files`, `/api/download/{object_name}`, `/api/files/{object_name}`

## 特性亮点

1. **响应式设计**: 适配不同屏幕尺寸
2. **实时更新**: 翻译进度和日志实时刷新
3. **文件预览**: 支持 PDF 和 Markdown 在线预览
4. **状态管理**: 清晰的翻译状态指示
5. **错误处理**: 完善的错误提示和处理机制
6. **用户体验**: 流畅的交互和视觉反馈