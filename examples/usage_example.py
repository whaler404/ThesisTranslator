#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ThesisTranslator 使用示例
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import ThesisTranslator

def basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建翻译器实例
    translator = ThesisTranslator(
        openai_api_key="your-openai-api-key",  # 请替换为实际的API密钥
        model="gpt-4",
        chunk_size=1000,
        max_retries=3
    )
    
    # 执行翻译（需要实际的PDF文件）
    # success = translator.translate_pdf("input.pdf", "output.md")
    # print(f"翻译结果: {'成功' if success else '失败'}")

def custom_api_usage():
    """自定义API端点使用示例"""
    print("\n=== 自定义API端点示例 ===")
    
    # 使用自定义API端点（例如：Azure OpenAI、其他兼容的API服务）
    translator = ThesisTranslator(
        openai_api_key="your-api-key",
        base_url="https://your-custom-api-endpoint.com/v1",  # 自定义API端点
        model="gpt-4",
        chunk_size=1000,
        max_retries=3
    )
    
    print("已配置自定义API端点")
    print("支持Azure OpenAI、本地部署的模型等兼容的API服务")

def advanced_usage():
    """高级使用示例"""
    print("\n=== 高级使用示例 ===")
    
    # 自定义配置
    config = {
        "model": "gpt-4",
        "base_url": "https://api.openai.com/v1",  # 可以自定义API端点
        "chunk_size": 800,
        "temperature": 0.2,
        "include_toc": True,
        "include_metadata": True
    }
    
    # 创建翻译器并设置配置
    translator = ThesisTranslator(openai_api_key="your-openai-api-key")
    translator.set_configuration(config)
    
    print("配置已更新:")
    for key, value in config.items():
        print(f"  {key}: {value}")

def error_handling_usage():
    """错误处理使用示例"""
    print("\n=== 错误处理示例 ===")
    
    translator = ThesisTranslator(openai_api_key="your-openai-api-key")
    
    # 使用错误处理机制
    result = translator.process_with_error_handling("nonexistent.pdf", "output.md")
    
    print("处理结果:")
    print(f"  成功: {result['success']}")
    print(f"  错误数: {result['error_count']}")
    print(f"  处理时间: {result['processing_time']:.2f}秒")

def main():
    """主函数"""
    print("ThesisTranslator 使用示例")
    print("=" * 30)
    
    # 基本使用
    basic_usage()
    
    # 自定义API端点
    custom_api_usage()
    
    # 高级使用
    advanced_usage()
    
    # 错误处理
    error_handling_usage()
    
    print("\n注意: 这些示例需要:")
    print("1. 实际的PDF文件")
    print("2. 有效的OpenAI API密钥")
    print("3. 安装所有依赖包")
    print("4. 如使用自定义API端点，请确保端点兼容OpenAI API格式")

if __name__ == "__main__":
    main()