import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import logging

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class TextBlock:
    """文本块数据结构"""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    page_num: int
    block_num: int
    font_info: Dict[str, Any]
    line_info: List[Dict]

class PDFProcessingError(Exception):
    """PDF处理异常"""
    pass

class PDFTextExtractor:
    """PDF文本提取器"""
    
    def __init__(self, pdf_path: str):
        """
        初始化PDF文本提取器
        
        Args:
            pdf_path (str): PDF文件路径
        """
        self.pdf_path = pdf_path
        self.doc = None
        
    def __enter__(self):
        """上下文管理器入口"""
        try:
            self.doc = fitz.open(self.pdf_path)
            logger.info(f"成功打开PDF文件: {self.pdf_path}")
            return self
        except Exception as e:
            logger.error(f"打开PDF文件失败: {e}")
            raise PDFProcessingError(f"无法打开PDF文件: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.doc:
            self.doc.close()
            logger.info("PDF文件已关闭")
    
    def extract_text_blocks(self) -> List[TextBlock]:
        """
        提取所有文本块
        
        Returns:
            List[TextBlock]: 文本块列表
        """
        if not self.doc:
            raise PDFProcessingError("PDF文档未打开")
            
        text_blocks = []
        
        try:
            for page_num in range(len(self.doc)):
                page = self.doc.load_page(page_num)
                # 使用dict模式提取详细文本信息
                text_dict = page.get_text("dict")
                
                # 遍历文本块
                for block_num, block in enumerate(text_dict.get("blocks", [])):
                    if "lines" not in block:
                        continue
                        
                    # 提取块中文本
                    block_text = ""
                    line_info = []
                    font_info = {}
                    
                    # 遍历行
                    for line in block["lines"]:
                        line_text = ""
                        # 遍历span
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                            # 收集字体信息
                            font_name = span.get("font", "")
                            font_size = span.get("size", 0)
                            if font_name and font_size:
                                font_info[font_name] = font_size
                        
                        block_text += line_text + " "
                        line_info.append({
                            "text": line_text,
                            "bbox": line.get("bbox", (0, 0, 0, 0))
                        })
                    
                    # 创建TextBlock对象
                    if block_text.strip():
                        text_block = TextBlock(
                            text=block_text.strip(),
                            bbox=block.get("bbox", (0, 0, 0, 0)),
                            page_num=page_num,
                            block_num=block_num,
                            font_info=font_info,
                            line_info=line_info
                        )
                        text_blocks.append(text_block)
            
            logger.info(f"成功提取 {len(text_blocks)} 个文本块")
            return text_blocks
            
        except Exception as e:
            logger.error(f"提取文本块时出错: {e}")
            raise PDFProcessingError(f"提取文本块失败: {e}")
    
    def get_reading_order(self) -> List[TextBlock]:
        """
        获取按阅读顺序排列的文本块
        
        Returns:
            List[TextBlock]: 按阅读顺序排列的文本块
        """
        text_blocks = self.extract_text_blocks()
        
        # 按页面和垂直位置排序
        text_blocks.sort(key=lambda block: (block.page_num, block.bbox[1], block.bbox[0]))
        
        logger.info(f"按阅读顺序排列 {len(text_blocks)} 个文本块")
        return text_blocks
    
    def get_page_info(self, page_num: int) -> Dict[str, Any]:
        """
        获取指定页面信息
        
        Args:
            page_num (int): 页面编号(从0开始)
            
        Returns:
            Dict[str, Any]: 页面信息
        """
        if not self.doc:
            raise PDFProcessingError("PDF文档未打开")
            
        if page_num >= len(self.doc):
            raise PDFProcessingError(f"页面编号超出范围: {page_num}")
            
        page = self.doc.load_page(page_num)
        rect = page.rect
        
        # 计算文本块数量
        text_dict = page.get_text("dict")
        blocks_count = len(text_dict.get("blocks", []))
        
        return {
            "width": rect.width,
            "height": rect.height,
            "rotation": page.rotation,
            "blocks_count": blocks_count
        }
    
    def extract_fonts(self) -> Dict[str, Dict]:
        """
        提取文档中使用的字体信息
        
        Returns:
            Dict[str, Dict]: 字体信息字典
        """
        if not self.doc:
            raise PDFProcessingError("PDF文档未打开")
            
        fonts = {}
        
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_name = span.get("font", "")
                        font_size = span.get("size", 0)
                        if font_name and font_size:
                            if font_name not in fonts:
                                fonts[font_name] = {
                                    "sizes": set(),
                                    "pages": set()
                                }
                            fonts[font_name]["sizes"].add(font_size)
                            fonts[font_name]["pages"].add(page_num)
        
        # 转换sets为lists以便序列化
        for font_name in fonts:
            fonts[font_name]["sizes"] = list(fonts[font_name]["sizes"])
            fonts[font_name]["pages"] = list(fonts[font_name]["pages"])
            
        return fonts