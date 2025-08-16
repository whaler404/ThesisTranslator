import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_cleaner import TextCleaner

class TestTextCleaner(unittest.TestCase):
    """文本清洗器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.cleaner = TextCleaner()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.cleaner, TextCleaner)
    
    def test_clean_text_chunk(self):
        """测试文本块清洗"""
        text = "  This is   a test   text.  "
        cleaned = self.cleaner.clean_text_chunk(text)
        # 基本清洗应该移除多余空格
        self.assertEqual(cleaned, "This is a test text.")
    
    def test_clean_text_chunk_empty(self):
        """测试空文本块清洗"""
        text = ""
        cleaned = self.cleaner.clean_text_chunk(text)
        self.assertEqual(cleaned, "")
    
    def test_clean_text_chunks(self):
        """测试批量文本块清洗"""
        chunks = ["  Hello  ", "  World  ", ""]
        cleaned_chunks = self.cleaner.clean_text_chunks(chunks)
        self.assertEqual(len(cleaned_chunks), 3)
        self.assertEqual(cleaned_chunks[0], "Hello")
        self.assertEqual(cleaned_chunks[1], "World")
        self.assertEqual(cleaned_chunks[2], "")
    
    def test_clean_text_chunks_empty(self):
        """测试空批量文本块清洗"""
        chunks = []
        cleaned_chunks = self.cleaner.clean_text_chunks(chunks)
        self.assertEqual(cleaned_chunks, [])
    
    def test_process_title_tags(self):
        """测试标题标签处理"""
        text = "Some text <Title>Introduction</Title> more text"
        processed = self.cleaner.process_title_tags(text)
        self.assertEqual(processed, "Some text\n## Introduction\nmore text")
    
    def test_process_end_tags(self):
        """测试结束标签处理"""
        text = "Paragraph one.<End>Paragraph two."
        processed = self.cleaner.process_end_tags(text)
        self.assertEqual(processed, "Paragraph one.\nParagraph two.")
    
    def test_process_cleaned_output(self):
        """测试清洗后输出处理"""
        text = "Text<Title>Title</Title>More<End>End"
        processed = self.cleaner.process_cleaned_output(text)
        # 应该处理标题和结束标签
        self.assertIn("## Title", processed)
        self.assertIn("\n", processed)

if __name__ == '__main__':
    unittest.main()