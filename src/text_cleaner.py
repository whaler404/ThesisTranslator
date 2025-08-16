from typing import List, Optional
import logging
import re
import time
from openai import OpenAI

# 配置日志
logger = logging.getLogger(__name__)

class TextCleaningError(Exception):
    """文本清洗异常"""
    pass

class TextCleaner:
    """文本清洗处理器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.3,
                 max_tokens: int = 2000, timeout: int = 60, base_url: Optional[str] = None):
        """
        初始化文本清洗器
        
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
        self.total_cleanings = 0
        self.successful_cleanings = 0
        self.failed_cleanings = 0
        self.total_processing_time = 0.0
    
    def clean_text_chunk(self, text_chunk: str) -> str:
        """
        清洗单个文本块 - 使用LLM进行智能清洗
        
        Args:
            text_chunk (str): 输入文本块
            
        Returns:
            str: 清洗后的文本
        """
        if not text_chunk.strip():
            logger.warning("输入文本块为空")
            return ""
        
        start_time = time.time()
        self.total_cleanings += 1
        
        try:
            # 构建提示词
            prompt = f"""
你是一个专业的学术论文文本清洗助手。请对以下英文论文文本进行清洗和结构化：

清洗规则：
1. 识别数学公式，转换为LaTeX格式并用$$包裹，识别行内公式和行间公式，公式需要正确换行
2. 识别标题，用<Title></Title>包裹
3. 识别段落结束，用<End>标记
4. 移除无关内容：作者姓名、邮箱、参考文献编号、页码、注脚、页眉页脚、表格等
5. 保留图片和表格的标题

输入文本：
{text_chunk}

请输出清洗后的文本：
"""
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文文本清洗助手，专门处理PDF提取的文本内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # 提取清洗结果
            cleaned_text = response.choices[0].message.content.strip()
            
            self.successful_cleanings += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.debug(f"文本清洗完成，耗时: {processing_time:.2f}秒")
            return cleaned_text
            
        except Exception as e:
            self.failed_cleanings += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.error(f"文本清洗失败: {e}")
            
            # 失败时使用基本清洗作为后备方案
            logger.warning("使用基本清洗作为后备方案")
            return self._basic_clean(text_chunk)
    
    def _basic_clean(self, text_chunk: str) -> str:
        """
        基本清洗处理作为后备方案
        
        Args:
            text_chunk (str): 输入文本块
            
        Returns:
            str: 基本清洗后的文本
        """
        logger.debug(f"执行基本清洗，长度: {len(text_chunk)} 字符")
        
        # 基本清洗处理
        cleaned_text = text_chunk.strip()
        
        # 移除多余的空白字符
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # 移除常见的页码模式
        cleaned_text = re.sub(r'\b\d+\s*$', '', cleaned_text)
        cleaned_text = re.sub(r'^\s*\d+\b', '', cleaned_text)
        
        # 移除常见的参考文献模式
        cleaned_text = re.sub(r'\[\d+\]', '', cleaned_text)
        
        return cleaned_text.strip()
    
    def clean_text_chunks(self, text_chunks: List[str]) -> List[str]:
        """
        批量清洗文本块
        
        Args:
            text_chunks (List[str]): 输入文本块列表
            
        Returns:
            List[str]: 清洗后的文本块列表
        """
        if not text_chunks:
            logger.warning("输入文本块列表为空")
            return []
        
        cleaned_chunks = []
        for i, chunk in enumerate(text_chunks):
            try:
                logger.info(f"正在清洗第 {i+1}/{len(text_chunks)} 个文本块")
                # 使用带重试机制的清洗方法
                cleaned_chunk = self.clean_with_retry(chunk)
                cleaned_chunks.append(cleaned_chunk)
                logger.debug(f"清洗了第 {i+1}/{len(text_chunks)} 个文本块")
            except Exception as e:
                logger.error(f"清洗第 {i+1} 个文本块时出错: {e}")
                # 即使重试失败也要继续处理，使用基本清洗作为最后的备选方案
                cleaned_chunks.append(self._basic_clean(chunk))
        
        logger.info(f"批量清洗了 {len(cleaned_chunks)} 个文本块")
        return cleaned_chunks
    
    def clean_with_retry(self, text_chunk: str, max_retries: int = 3) -> str:
        """
        带重试机制的文本清洗
        
        Args:
            text_chunk (str): 输入文本块
            max_retries (int): 最大重试次数
            
        Returns:
            str: 清洗后的文本
        """
        for attempt in range(max_retries):
            try:
                return self.clean_text_chunk(text_chunk)
            except TextCleaningError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"文本清洗失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"文本清洗失败，已达到最大重试次数: {e}")
                    return self._basic_clean(text_chunk)
            except Exception as e:
                logger.error(f"文本清洗过程中发生未知错误: {e}")
                return self._basic_clean(text_chunk)
    
    def get_cleaning_statistics(self) -> dict:
        """
        获取清洗统计信息
        
        Returns:
            dict: 统计信息
        """
        success_rate = 0.0
        if self.total_cleanings > 0:
            success_rate = self.successful_cleanings / self.total_cleanings
        
        avg_processing_time = 0.0
        if self.total_cleanings > 0:
            avg_processing_time = self.total_processing_time / self.total_cleanings
        
        return {
            "total_cleanings": self.total_cleanings,
            "successful_cleanings": self.successful_cleanings,
            "failed_cleanings": self.failed_cleanings,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "total_processing_time": self.total_processing_time
        }
    
    def process_cleaned_output(self, cleaned_text: str) -> str:
        """
        处理清洗后的输出，转换标记
        
        Args:
            cleaned_text (str): 清洗后的文本
            
        Returns:
            str: 处理后的文本
        """
        if not cleaned_text:
            return ""
        
        # 处理标题标签
        processed_text = self.process_title_tags(cleaned_text)
        
        # 处理段落结束标签
        processed_text = self.process_end_tags(processed_text)
        
        return processed_text
    
    def process_title_tags(self, text: str) -> str:
        """
        处理标题标签，将<Title>标签转换为Markdown格式
        
        Args:
            text (str): 包含<Title></Title>标签的文本
            
        Returns:
            str: 转换后的文本
        """
        if not text:
            return ""
        
        # 将<Title>标题</Title>转换为\n## 标题\n
        # 这里简单处理，实际应该根据标题层级调整#的数量
        processed_text = re.sub(r'<Title>(.*?)</Title>', r'\n## \1\n', text)
        
        # 移除多余的空行
        processed_text = re.sub(r'\n\s*\n', '\n\n', processed_text)
        
        return processed_text.strip()
    
    def process_end_tags(self, text: str) -> str:
        """
        处理分段标签，将<End>标签转换为换行符
        
        Args:
            text (str): 包含<End>标签的文本
            
        Returns:
            str: 转换后的文本
        """
        if not text:
            return ""
        
        # 将<End>转换为换行符
        processed_text = text.replace('<End>', '\n')
        
        # 移除多余的空行
        processed_text = re.sub(r'\n\s*\n', '\n\n', processed_text)
        
        return processed_text