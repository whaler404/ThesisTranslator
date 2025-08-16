import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_chunker import TextChunker
from src.pdf_parser import TextBlock

class TestTextChunker(unittest.TestCase):
    """文本分块器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.chunker = TextChunker(chunk_size=50, overlap_size=10)
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.chunker.chunk_size, 50)
        self.assertEqual(self.chunker.overlap_size, 10)
    
    def test_merge_blocks_to_string(self):
        """测试文本块合并"""
        blocks = [
            TextBlock("Hello", (0, 0, 10, 10), 0, 0, {}, []),
            TextBlock("world", (10, 0, 20, 10), 0, 1, {}, []),
            TextBlock("!", (20, 0, 30, 10), 0, 2, {}, [])
        ]
        
        result = self.chunker.merge_blocks_to_string(blocks)
        self.assertEqual(result, "Hello world !")
    
    def test_merge_blocks_to_string_empty(self):
        """测试空文本块合并"""
        blocks = []
        result = self.chunker.merge_blocks_to_string(blocks)
        self.assertEqual(result, "")
    
    def test_create_chunks(self):
        """测试创建文本块"""
        blocks = [
            TextBlock("This is a test sentence for chunking.", (0, 0, 100, 10), 0, 0, {}, [])
        ]
        
        chunks = self.chunker.create_chunks(blocks)
        self.assertGreater(len(chunks), 0)
        # 检查每个块不超过chunk_size
        for chunk in chunks:
            self.assertLessEqual(len(chunk), self.chunker.chunk_size)
    
    def test_create_chunks_empty(self):
        """测试空文本块创建"""
        blocks = []
        chunks = self.chunker.create_chunks(blocks)
        self.assertEqual(chunks, [])
    
    def test_get_chunk_statistics(self):
        """测试获取分块统计信息"""
        stats = self.chunker.get_chunk_statistics()
        self.assertIn("chunk_size", stats)
        self.assertIn("overlap_size", stats)
        self.assertEqual(stats["chunk_size"], 50)
        self.assertEqual(stats["overlap_size"], 10)

if __name__ == '__main__':
    unittest.main()