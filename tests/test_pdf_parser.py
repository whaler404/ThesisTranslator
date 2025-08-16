import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_parser import PDFTextExtractor, TextBlock, PDFProcessingError

class TestPDFTextExtractor(unittest.TestCase):
    """PDF文本提取器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.pdf_path = "test.pdf"
    
    def test_init(self):
        """测试初始化"""
        extractor = PDFTextExtractor(self.pdf_path)
        self.assertEqual(extractor.pdf_path, self.pdf_path)
        self.assertIsNone(extractor.doc)
    
    @patch('src.pdf_parser.fitz.open')
    def test_enter_exit(self, mock_fitz_open):
        """测试上下文管理器"""
        mock_doc = MagicMock()
        mock_fitz_open.return_value = mock_doc
        
        with PDFTextExtractor(self.pdf_path) as extractor:
            self.assertEqual(extractor.doc, mock_doc)
        
        mock_doc.close.assert_called_once()
    
    @patch('src.pdf_parser.fitz.open')
    def test_extract_text_blocks(self, mock_fitz_open):
        """测试文本块提取"""
        # 模拟PDF文档结构
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        
        mock_text_dict = {
            "blocks": [
                {
                    "bbox": (0, 0, 100, 100),
                    "lines": [
                        {
                            "bbox": (0, 0, 100, 50),
                            "spans": [
                                {
                                    "text": "Test text",
                                    "font": "Helvetica",
                                    "size": 12
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_page.get_text.return_value = mock_text_dict
        mock_fitz_open.return_value = mock_doc
        
        with PDFTextExtractor(self.pdf_path) as extractor:
            blocks = extractor.extract_text_blocks()
            
            self.assertEqual(len(blocks), 1)
            self.assertIsInstance(blocks[0], TextBlock)
            self.assertEqual(blocks[0].text, "Test text")
            self.assertEqual(blocks[0].page_num, 0)
    
    @patch('src.pdf_parser.fitz.open')
    def test_extract_text_blocks_empty(self, mock_fitz_open):
        """测试空文本块提取"""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.load_page.return_value = mock_page
        
        mock_text_dict = {"blocks": []}
        mock_page.get_text.return_value = mock_text_dict
        mock_fitz_open.return_value = mock_doc
        
        with PDFTextExtractor(self.pdf_path) as extractor:
            blocks = extractor.extract_text_blocks()
            self.assertEqual(len(blocks), 0)
    
    def test_extract_text_blocks_no_doc(self):
        """测试未打开文档时的文本块提取"""
        extractor = PDFTextExtractor(self.pdf_path)
        with self.assertRaises(PDFProcessingError):
            extractor.extract_text_blocks()

if __name__ == '__main__':
    unittest.main()