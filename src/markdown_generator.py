from typing import List
import logging
import re

# 配置日志
logger = logging.getLogger(__name__)

class MarkdownGenerator:
    """Markdown文档生成器"""
    
    def __init__(self):
        """
        初始化Markdown生成器
        """
        pass
    
    def process_titles(self, text: str) -> str:
        """
        处理标题标记
        
        Args:
            text (str): 包含标题标记的文本
            
        Returns:
            str: 转换后的Markdown文本
        """
        if not text:
            return ""
        
        # 这个功能已经在text_cleaner中实现，这里保持接口一致性
        # 实际处理应该在text_cleaner中完成
        return text
    
    def process_paragraphs(self, text: str) -> str:
        """
        处理段落标记
        
        Args:
            text (str): 包含段落标记的文本
            
        Returns:
            str: 格式化后的文本
        """
        if not text:
            return ""
        
        # 这个功能已经在text_cleaner中实现，这里保持接口一致性
        # 实际处理应该在text_cleaner中完成
        return text
    
    def generate_markdown(self, translated_chunks: List[str]) -> str:
        """
        生成完整的Markdown文档
        
        Args:
            translated_chunks (List[str]): 翻译后的文本块列表
            
        Returns:
            str: 完整的Markdown文档
        """
        if not translated_chunks:
            logger.warning("输入翻译块列表为空")
            return ""
        
        # 合并所有翻译块
        markdown_content = "\n\n".join(translated_chunks)
        
        # 移除多余的空行
        markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
        
        # 添加文档标题（如果不存在）
        if not markdown_content.strip().startswith('#'):
            # 尝试从内容中提取标题
            lines = markdown_content.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                if first_line and not first_line.startswith('#'):
                    # 将第一行作为标题
                    markdown_content = f"# {first_line}\n\n" + '\n'.join(lines[1:])
        
        logger.info(f"生成Markdown文档，总长度: {len(markdown_content)} 字符")
        return markdown_content
    
    def add_metadata(self, content: str, metadata: dict = None) -> str:
        """
        添加文档元数据
        
        Args:
            content (str): 文档内容
            metadata (dict): 元数据信息
            
        Returns:
            str: 包含元数据的Markdown文档
        """
        if not content:
            return ""
        
        if not metadata:
            metadata = {}
        
        # 构建元数据部分
        metadata_lines = []
        if metadata:
            metadata_lines.append("---")
            for key, value in metadata.items():
                metadata_lines.append(f"{key}: {value}")
            metadata_lines.append("---")
            metadata_lines.append("")  # 空行分隔
        
        # 合并元数据和内容
        if metadata_lines:
            return "\n".join(metadata_lines) + content
        else:
            return content
    
    def format_formulas(self, text: str) -> str:
        """
        格式化数学公式
        
        Args:
            text (str): 包含公式的文本
            
        Returns:
            str: 格式化后的文本
        """
        # 在清洗阶段应该已经处理了公式格式，这里保持接口一致性
        return text
    
    def create_table_of_contents(self, content: str) -> str:
        """
        创建目录
        
        Args:
            content (str): Markdown内容
            
        Returns:
            str: 目录字符串
        """
        if not content:
            return ""
        
        # 提取标题
        titles = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)
        
        if not titles:
            return ""
        
        # 构建目录
        toc_lines = ["## 目录", ""]
        for level, title in titles:
            level_num = len(level)
            # 生成锚点链接
            anchor = re.sub(r'[^\w\u4e00-\u9fff\- ]', '', title).strip().lower().replace(' ', '-')
            toc_lines.append(f"{'  ' * (level_num - 1)}- [{title}](#{anchor})")
        
        toc_lines.append("")  # 空行分隔
        toc = "\n".join(toc_lines)
        
        # 将目录插入到文档开头（在第一个标题之前）
        lines = content.split('\n')
        new_lines = []
        toc_inserted = False
        
        for line in lines:
            if line.startswith('#') and not toc_inserted:
                new_lines.append(toc)
                toc_inserted = True
            new_lines.append(line)
        
        if not toc_inserted:
            # 如果没有找到标题，将目录放在开头
            new_lines.insert(0, toc)
        
        return "\n".join(new_lines)
    
    def validate_markdown(self, content: str) -> dict:
        """
        验证Markdown格式
        
        Args:
            content (str): Markdown内容
            
        Returns:
            dict: 验证结果
        """
        if not content:
            return {
                "is_valid": False,
                "errors": ["内容为空"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # 检查基本结构
        if len(content.strip()) < 10:
            warnings.append("内容过短")
        
        # 检查标题格式
        title_matches = re.findall(r'^#+\s+.*$', content, re.MULTILINE)
        if not title_matches:
            warnings.append("未找到标题")
        
        # 检查公式配对
        formula_count = content.count('$$')
        if formula_count % 2 != 0:
            errors.append("数学公式标记$$未正确配对")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }