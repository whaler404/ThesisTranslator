#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
英文论文翻译器Web界面启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = ['flask', 'flask_cors']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少依赖包:", ', '.join(missing_packages))
        print("📦 正在安装依赖...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements_web.txt'])
            print("✅ 依赖安装完成")
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败，请手动运行: pip install -r requirements_web.txt")
            return False
    
    return True

def check_openai_key():
    """检查OpenAI API密钥"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  警告: 未设置OPENAI_API_KEY环境变量")
        print("请设置OpenAI API密钥:")
        print("  Linux/Mac: export OPENAI_API_KEY='your-api-key'")
        print("  Windows: set OPENAI_API_KEY=your-api-key")
        return False
    return True

def create_directories():
    """创建必要的目录"""
    directories = ['uploads', 'downloads', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("📁 目录结构检查完成")

def main():
    """主函数"""
    print("🚀 启动英文论文翻译器Web界面...")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查API密钥
    check_openai_key()
    
    # 创建目录
    create_directories()
    
    print("✅ 环境检查完成")
    print("🌐 启动Web服务器...")
    print("📍 访问地址: http://localhost:5000")
    print("=" * 50)
    
    # 启动Flask应用
    try:
        import web_app
        web_app.app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    main()