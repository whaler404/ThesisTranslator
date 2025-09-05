import Link from 'next/link';
import MainLayout from '@/components/MainLayout';
import { Download, FileText, FolderOpen, ArrowRight } from 'lucide-react';

export default function HomePage() {
  const features = [
    {
      title: '下载论文',
      description: '支持文件上传和URL下载，自动去重',
      icon: Download,
      href: '/download',
      color: 'bg-blue-600 hover:bg-blue-700',
    },
    {
      title: '翻译论文',
      description: 'AI驱动的英文论文翻译，实时进度监控',
      icon: FileText,
      href: '/translate',
      color: 'bg-green-600 hover:bg-green-700',
    },
    {
      title: '文件管理',
      description: '文件预览、搜索、排序和管理功能',
      icon: FolderOpen,
      href: '/files',
      color: 'bg-purple-600 hover:bg-purple-700',
    },
  ];

  return (
    <MainLayout>
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          论文翻译器
        </h1>
        <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
          基于 AI 的英文论文翻译系统，支持 PDF 文件下载、翻译和管理
        </p>

        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Link key={index} href={feature.href}>
                <div className="card p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer group">
                  <div className={`w-12 h-12 ${feature.color} rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    {feature.description}
                  </p>
                  <div className="flex items-center text-primary-600 text-sm font-medium group-hover:translate-x-1 transition-transform">
                    开始使用
                    <ArrowRight className="h-4 w-4 ml-1" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-16 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-8">系统特性</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 mb-2">智能下载</h3>
              <p className="text-gray-600 text-sm">
                支持拖拽上传PDF文件和URL下载，自动检查重复文件，文件名智能处理
              </p>
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 mb-2">AI翻译</h3>
              <p className="text-gray-600 text-sm">
                基于大语言模型的智能翻译，支持多种模型选择，实时进度监控
              </p>
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 mb-2">文件预览</h3>
              <p className="text-gray-600 text-sm">
                支持PDF在线预览和Markdown渲染，双栏对比显示，多种预览模式
              </p>
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-gray-900 mb-2">文件管理</h3>
              <p className="text-gray-600 text-sm">
                强大的文件搜索和排序功能，支持批量操作，灵活的文件管理
              </p>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}