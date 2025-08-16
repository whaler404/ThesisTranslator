import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.markdown_generator import MarkdownGenerator

class TestMarkdownGenerator(unittest.TestCase):
    """Markdown生成器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = MarkdownGenerator()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.generator, MarkdownGenerator)
    
    def test_process_titles(self):
        """测试标题处理"""
        text = "Some text with titles"
        processed = self.generator.process_titles(text)
        # 在当前实现中，应该返回原始文本
        self.assertEqual(processed, text)
    
    def test_process_paragraphs(self):
        """测试段落处理"""
        text = "Some text with paragraphs"
        processed = self.generator.process_paragraphs(text)
        # 在当前实现中，应该返回原始文本
        self.assertEqual(processed, text)
    
    def test_generate_markdown(self):
        """测试Markdown生成"""
        chunks = ["# Title", "This is paragraph one.", "This is paragraph two."]
        markdown = self.generator.generate_markdown(chunks)
        self.assertIn("# Title", markdown)
        self.assertIn("This is paragraph one.", markdown)
        self.assertIn("This is paragraph two.", markdown)
    
    def test_generate_markdown_empty(self):
        """测试空Markdown生成"""
        chunks = []
        markdown = self.generator.generate_markdown(chunks)
        self.assertEqual(markdown, "")
    
    def test_add_metadata(self):
        """测试添加元数据"""
        content = "# Title\nContent"
        metadata = {"author": "Test Author", "date": "2023-01-01"}
        result = self.generator.add_metadata(content, metadata)
        self.assertIn("author: Test Author", result)
        self.assertIn("date: 2023-01-01", result)
        self.assertIn("# Title", result)
    
    def test_format_formulas(self):
        """测试公式格式化"""
        text = "E = mc^2"
        formatted = self.generator.format_formulas(text)
        # 在当前实现中，应该返回原始文本
        self.assertEqual(formatted, text)
    
    def test_create_table_of_contents(self):
        """测试创建目录"""
        content = "# Title\n## Section 1\n### Subsection\n## Section 2"
        result = self.generator.create_table_of_contents(content)
        self.assertIn("目录", result)
        self.assertIn("[Title]", result)
        self.assertIn("[Section 1]", result)
        self.assertIn("[Section 2]", result)
    
    def test_validate_markdown(self):
        """测试Markdown验证"""
        content = "# Title\n$$formula$$\nContent"
        result = self.generator.validate_markdown(content)
        self.assertIn("is_valid", result)
        self.assertIn("errors", result)
        self.assertIn("warnings", result)
        
        # 公式应该正确配对
        self.assertTrue(result["is_valid"])
        
        # 测试公式未配对的情况
        content_invalid = "# Title\n$$formula\nContent"
        result_invalid = self.generator.validate_markdown(content_invalid)
        self.assertFalse(result_invalid["is_valid"])

if __name__ == '__main__':
    unittest.main()