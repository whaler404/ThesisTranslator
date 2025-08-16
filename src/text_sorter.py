from typing import List, Optional
import logging
import re
import time
from openai import OpenAI

# 配置日志
logger = logging.getLogger(__name__)

class TextSortingError(Exception):
    """文本排序异常"""
    pass

class TextSorter:
    """文本语义排序处理器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.3,
                 max_tokens: int = 2000, timeout: int = 60, base_url: Optional[str] = None):
        """
        初始化文本排序器
        
        Args:
            api_key (str): OpenAI API密钥
            model (str): 使用的模型名称
            temperature (float): 生成温度
            max_tokens (int): 最大令牌数
            timeout (int): 超时时间(秒)
            base_url (Optional[str]): API基础URL，默认为None使用OpenAI官方API
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 统计信息
        self.total_sortings = 0
        self.successful_sortings = 0
        self.failed_sortings = 0
        self.total_processing_time = 0.0
    
    def sort_text_semantically(self, text_chunk: str) -> str:
        """
        对文本进行语义排序 - 使用LLM进行智能排序
        
        Args:
            text_chunk (str): 输入文本块
            
        Returns:
            str: 排序后的文本
        """
        if not text_chunk.strip():
            logger.warning("输入文本块为空")
            return ""
        
        start_time = time.time()
        self.total_sortings += 1
        
        try:
            # 构建提示词
            prompt = f"""
你是一个专业的学术文本排序专家。请分析以下文本的句子顺序，如果存在语义不连贯的问题，请重新排列句子顺序：

要求：
1. 保持学术论文的逻辑结构
2. 确保句子之间的语义连贯
3. 保留所有原始内容，只调整顺序
4. 如果顺序正确，直接输出原文
5. 保持段落结构和标记（如<Title>、<End>等）

输入文本：
{text_chunk}

请输出排序后的文本：
"""
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术文本排序专家，专门优化文本的逻辑顺序和连贯性。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # 提取排序结果
            sorted_text = response.choices[0].message.content.strip()
            
            self.successful_sortings += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.debug(f"文本排序完成，耗时: {processing_time:.2f}秒")
            return sorted_text
            
        except Exception as e:
            self.failed_sortings += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.error(f"文本排序失败: {e}")
            
            # 失败时保持原文不变
            logger.warning("排序失败，保持原文不变")
            return text_chunk
    
    def sort_text_chunks(self, text_chunks: List[str]) -> List[str]:
        """
        批量对文本块进行语义排序
        
        Args:
            text_chunks (List[str]): 输入文本块列表
            
        Returns:
            List[str]: 排序后的文本块列表
        """
        if not text_chunks:
            logger.warning("输入文本块列表为空")
            return []
        
        sorted_chunks = []
        for i, chunk in enumerate(text_chunks):
            try:
                logger.info(f"正在排序第 {i+1}/{len(text_chunks)} 个文本块")
                # 使用带重试机制的排序方法
                sorted_chunk = self.sort_with_retry(chunk)
                sorted_chunks.append(sorted_chunk)
                logger.debug(f"排序了第 {i+1}/{len(text_chunks)} 个文本块")
            except Exception as e:
                logger.error(f"排序第 {i+1} 个文本块时出错: {e}")
                # 即使重试失败也要继续处理，保留原始文本
                sorted_chunks.append(chunk)
        
        logger.info(f"批量排序了 {len(sorted_chunks)} 个文本块")
        return sorted_chunks
    
    def sort_with_retry(self, text_chunk: str, max_retries: int = 3) -> str:
        """
        带重试机制的文本排序
        
        Args:
            text_chunk (str): 输入文本块
            max_retries (int): 最大重试次数
            
        Returns:
            str: 排序后的文本
        """
        for attempt in range(max_retries):
            try:
                return self.sort_text_semantically(text_chunk)
            except TextSortingError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"文本排序失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"文本排序失败，已达到最大重试次数: {e}")
                    return text_chunk  # 返回原文
            except Exception as e:
                logger.error(f"文本排序过程中发生未知错误: {e}")
                return text_chunk  # 返回原文
    
    def get_sorting_statistics(self) -> dict:
        """
        获取排序统计信息
        
        Returns:
            dict: 统计信息
        """
        success_rate = 0.0
        if self.total_sortings > 0:
            success_rate = self.successful_sortings / self.total_sortings
        
        avg_processing_time = 0.0
        if self.total_sortings > 0:
            avg_processing_time = self.total_processing_time / self.total_sortings
        
        return {
            "total_sortings": self.total_sortings,
            "successful_sortings": self.successful_sortings,
            "failed_sortings": self.failed_sortings,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "total_processing_time": self.total_processing_time
        }