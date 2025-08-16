import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.translator import AITranslator, TranslationError

class TestAITranslator(unittest.TestCase):
    """AI翻译器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.translator = AITranslator(api_key="test-key", model="gpt-test")
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.translator.model, "gpt-test")
        self.assertEqual(self.translator.temperature, 0.3)
        self.assertEqual(self.translator.max_tokens, 2000)
        self.assertEqual(self.translator.timeout, 60)
    
    @patch('src.translator.OpenAI')
    def test_translate_text(self, mock_openai):
        """测试文本翻译"""
        # 模拟OpenAI客户端和响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = "这是翻译结果"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        self.translator.client = mock_client
        
        result = self.translator.translate_text("This is a test.")
        self.assertEqual(result, "这是翻译结果")
        
        # 验证调用参数
        mock_client.chat.completions.create.assert_called_once()
    
    def test_translate_text_empty(self):
        """测试空文本翻译"""
        result = self.translator.translate_text("")
        self.assertEqual(result, "")
        
        result = self.translator.translate_text("   ")
        self.assertEqual(result, "")
    
    @patch('src.translator.OpenAI')
    def test_translate_chunks(self, mock_openai):
        """测试批量文本翻译"""
        # 模拟OpenAI客户端和响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = "翻译结果"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        self.translator.client = mock_client
        
        chunks = ["Text 1", "Text 2", ""]
        translated_chunks = self.translator.translate_chunks(chunks)
        
        self.assertEqual(len(translated_chunks), 3)
        self.assertEqual(translated_chunks[0], "翻译结果")
    
    def test_translate_chunks_empty(self):
        """测试空批量文本翻译"""
        chunks = []
        translated_chunks = self.translator.translate_chunks(chunks)
        self.assertEqual(translated_chunks, [])
    
    @patch('src.translator.OpenAI')
    def test_translate_with_retry_success(self, mock_openai):
        """测试带重试机制的翻译成功"""
        # 模拟OpenAI客户端和响应
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        
        mock_message.content = "翻译结果"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_response
        self.translator.client = mock_client
        
        result = self.translator.translate_with_retry("Test text", max_retries=3)
        self.assertEqual(result, "翻译结果")
    
    @patch('src.translator.OpenAI')
    def test_translate_with_retry_failure(self, mock_openai):
        """测试带重试机制的翻译失败"""
        # 模拟OpenAI客户端抛出异常
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        self.translator.client = mock_client
        
        with self.assertRaises(TranslationError):
            self.translator.translate_with_retry("Test text", max_retries=2)
    
    def test_get_translation_statistics(self):
        """测试获取翻译统计信息"""
        stats = self.translator.get_translation_statistics()
        self.assertIn("total_translations", stats)
        self.assertIn("successful_translations", stats)
        self.assertIn("failed_translations", stats)
        self.assertIn("success_rate", stats)
        self.assertIn("avg_processing_time", stats)
        self.assertIn("total_processing_time", stats)
        
        # 初始状态应该都是0
        self.assertEqual(stats["total_translations"], 0)
        self.assertEqual(stats["successful_translations"], 0)
        self.assertEqual(stats["failed_translations"], 0)
        self.assertEqual(stats["success_rate"], 0.0)
        self.assertEqual(stats["avg_processing_time"], 0.0)
        self.assertEqual(stats["total_processing_time"], 0.0)

if __name__ == '__main__':
    unittest.main()