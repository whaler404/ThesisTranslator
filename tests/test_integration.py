import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import ThesisTranslator
from src.pdf_parser import TextBlock

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.pdf_path = os.path.join(self.test_dir, "test.pdf")
        self.output_path = os.path.join(self.test_dir, "output.md")
        
        # 创建一个简单的测试PDF内容（模拟）
        self.mock_text_blocks = [
            TextBlock(
                text="This is a test paper title",
                bbox=(100, 100, 200, 120),
                page_num=0,
                block_num=0,
                font_info={"Helvetica": 12},
                line_info=[{"text": "This is a test paper title", "bbox": (100, 100, 200, 120)}]
            ),
            TextBlock(
                text="This is the introduction section.",
                bbox=(50, 150, 300, 170),
                page_num=0,
                block_num=1,
                font_info={"Times": 11},
                line_info=[{"text": "This is the introduction section.", "bbox": (50, 150, 300, 170)}]
            ),
            TextBlock(
                text="Here is a mathematical formula: E = mc^2",
                bbox=(50, 200, 300, 220),
                page_num=0,
                block_num=2,
                font_info={"Times": 11},
                line_info=[{"text": "Here is a mathematical formula: E = mc^2", "bbox": (50, 200, 300, 220)}]
            )
        ]
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)
    
    @patch('src.main.PDFTextExtractor')
    @patch('src.main.AITranslator')
    def test_translate_pdf_success(self, mock_translator, mock_pdf_extractor):
        """测试PDF翻译成功流程"""
        # 模拟PDF提取器
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.get_reading_order.return_value = self.mock_text_blocks
        mock_pdf_extractor.return_value.__enter__.return_value = mock_extractor_instance
        
        # 模拟翻译器
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate_chunks.return_value = [
            "这是一个测试论文标题",
            "这是介绍部分。",
            "这里有一个数学公式：E = mc^2"
        ]
        mock_translator.return_value = mock_translator_instance
        
        # 创建翻译器实例
        translator = ThesisTranslator(openai_api_key="test-key")
        
        # 执行翻译
        success = translator.translate_pdf(self.pdf_path, self.output_path)
        
        # 验证结果
        self.assertTrue(success)
        mock_pdf_extractor.assert_called_once_with(self.pdf_path)
        mock_translator_instance.translate_chunks.assert_called_once()
        
        # 验证输出文件是否存在
        self.assertTrue(os.path.exists(self.output_path))
    
    @patch('src.main.PDFTextExtractor')
    def test_translate_pdf_empty_content(self, mock_pdf_extractor):
        """测试PDF内容为空的情况"""
        # 模拟PDF提取器返回空内容
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.get_reading_order.return_value = []
        mock_pdf_extractor.return_value.__enter__.return_value = mock_extractor_instance
        
        # 创建翻译器实例
        translator = ThesisTranslator(openai_api_key="test-key")
        
        # 执行翻译
        success = translator.translate_pdf(self.pdf_path, self.output_path)
        
        # 验证结果
        self.assertFalse(success)
    
    def test_process_with_error_handling(self):
        """测试带错误处理的处理流程"""
        # 创建翻译器实例
        translator = ThesisTranslator(openai_api_key="test-key")
        
        # 使用不存在的PDF文件进行测试
        result = translator.process_with_error_handling("nonexistent.pdf", self.output_path)
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertEqual(result["error_count"], 1)
        self.assertGreater(result["processing_time"], 0)

if __name__ == '__main__':
    unittest.main()