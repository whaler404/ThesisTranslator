from typing import List, Dict, Any
from .pdf_parser import TextBlock
import logging

# 配置日志
logger = logging.getLogger(__name__)

class TextChunker:
    """文本分块处理器"""
    
    def __init__(self, chunk_size: int = 1000, overlap_size: int = 100):
        """
        初始化文本分块器
        
        Args:
            chunk_size (int): 每个块的最大字符数
            overlap_size (int): 块之间的重叠字符数
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        
    def create_chunks(self, text_blocks: List[TextBlock]) -> List[str]:
        """
        创建文本块
        
        Args:
            text_blocks (List[TextBlock]): 输入文本块列表
            
        Returns:
            List[str]: 分块后的文本字符串列表
        """
        if not text_blocks:
            logger.warning("输入文本块列表为空")
            return []
        
        # 将文本块合并为字符串，使用空格分隔
        merged_text = self.merge_blocks_to_string(text_blocks)
        
        # 分割成指定大小的块
        chunks = []
        start = 0
        
        while start < len(merged_text):
            end = min(start + self.chunk_size, len(merged_text))
            chunk = merged_text[start:end]
            chunks.append(chunk)
            
            # 移动起始位置，考虑重叠
            start = end - self.overlap_size
            if start >= end:  # 防止无限循环
                start = end
                
            # 如果剩余文本太短，直接添加并结束
            if len(merged_text) - start <= self.overlap_size:
                if start < len(merged_text):
                    chunks.append(merged_text[start:])
                break
        
        logger.info(f"创建了 {len(chunks)} 个文本块")
        return chunks
    
    def merge_blocks_to_string(self, blocks: List[TextBlock]) -> str:
        """
        将文本块合并为字符串
        
        Args:
            blocks (List[TextBlock]): 文本块列表
            
        Returns:
            str: 合并后的字符串
        """
        if not blocks:
            return ""
        
        # 使用空格连接所有文本块
        texts = [block.text for block in blocks if block.text.strip()]
        merged_text = " ".join(texts)
        
        logger.debug(f"合并了 {len(blocks)} 个文本块，总长度: {len(merged_text)} 字符")
        return merged_text
    
    def get_chunk_statistics(self) -> Dict[str, Any]:
        """
        获取分块统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        # 这个方法在当前实现中不适用，因为我们没有存储历史分块信息
        return {
            "chunk_size": self.chunk_size,
            "overlap_size": self.overlap_size
        }