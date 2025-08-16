import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_sorter import TextSorter

class TestTextSorter(unittest.TestCase):
    """文本排序器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.sorter = TextSorter()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.sorter, TextSorter)
    
    def test_sort_text_semantically(self):
        """测试语义排序"""
        text = "This is a test sentence."
        sorted_text = self.sorter.sort_text_semantically(text)
        # 在当前实现中，文本应该保持不变
        self.assertEqual(sorted_text, text)
    
    def test_sort_text_chunks(self):
        """测试批量文本块排序"""
        chunks = ["Sentence one.", "Sentence two.", ""]
        sorted_chunks = self.sorter.sort_text_chunks(chunks)
        self.assertEqual(len(sorted_chunks), 3)
        # 在当前实现中，文本应该保持不变
        self.assertEqual(sorted_chunks[0], "Sentence one.")
        self.assertEqual(sorted_chunks[1], "Sentence two.")
        self.assertEqual(sorted_chunks[2], "")
    
    def test_sort_text_chunks_empty(self):
        """测试空批量文本块排序"""
        chunks = []
        sorted_chunks = self.sorter.sort_text_chunks(chunks)
        self.assertEqual(sorted_chunks, [])

if __name__ == '__main__':
    unittest.main()