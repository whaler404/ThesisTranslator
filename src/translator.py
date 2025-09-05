from typing import List, Optional
import logging
from openai import OpenAI
import time

# 配置日志
logger = logging.getLogger(__name__)

class TranslationError(Exception):
    """翻译异常"""
    pass

class AITranslator:
    """AI翻译器"""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.3,
                 max_tokens: int = 2000, timeout: int = 60, base_url: Optional[str] = None):
        """
        初始化AI翻译器
        
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
        self.total_translations = 0
        self.successful_translations = 0
        self.failed_translations = 0
        self.total_processing_time = 0.0
        
    def translate_text(self, english_text: str) -> str:
        """
        翻译单个文本
        
        Args:
            english_text (str): 英文原文
            
        Returns:
            str: 中文翻译
        """
        if not english_text.strip():
            logger.warning("输入文本为空")
            return ""
        
        start_time = time.time()
        self.total_translations += 1
        
        try:
            # 构建提示词
            prompt = f"""
            你是一个专业的学术论文翻译专家。请将以下英文学术论文文本翻译成中文：

            要求：
            1. 保持学术性和准确性
            2. 保留LaTeX公式格式（用$$包裹的数学公式）
            3. 保持标题和段落结构
            4. 使用准确的学术术语
            5. 参考文献不需要翻译，保留参考文献英文文本

            英文原文：
            {english_text}

            请输出中文翻译：
            """
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的学术论文翻译专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # 提取翻译结果
            translated_text = response.choices[0].message.content.strip()
            
            self.successful_translations += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.debug(f"翻译完成，耗时: {processing_time:.2f}秒")
            return translated_text
            
        except Exception as e:
            self.failed_translations += 1
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            
            logger.error(f"翻译失败: {e}")
            raise TranslationError(f"翻译失败: {e}")
    
    def translate_chunks(self, text_chunks: List[str]) -> List[str]:
        """
        批量翻译文本块
        
        Args:
            text_chunks (List[str]): 文本块列表
            
        Returns:
            List[str]: 翻译结果列表
        """
        if not text_chunks:
            logger.warning("输入文本块列表为空")
            return []
        
        translated_chunks = []
        
        for i, chunk in enumerate(text_chunks):
            try:
                logger.info(f"正在翻译第 {i+1}/{len(text_chunks)} 个文本块")
                translated_chunk = self.translate_text(chunk)
                translated_chunks.append(translated_chunk)
            except TranslationError as e:
                logger.error(f"翻译第 {i+1} 个文本块时出错: {e}")
                # 出错时添加错误标记
                translated_chunks.append(f"[翻译错误: {str(e)}]")
            except Exception as e:
                logger.error(f"翻译第 {i+1} 个文本块时发生未知错误: {e}")
                translated_chunks.append(f"[未知错误: {str(e)}]")
        
        logger.info(f"批量翻译完成，成功: {len(translated_chunks)} 个文本块")
        return translated_chunks
    
    def translate_with_retry(self, text: str, max_retries: int = 3) -> str:
        """
        带重试机制的翻译
        
        Args:
            text (str): 待翻译文本
            max_retries (int): 最大重试次数
            
        Returns:
            str: 翻译结果
        """
        for attempt in range(max_retries):
            try:
                return self.translate_text(text)
            except TranslationError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"翻译失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"翻译失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                logger.error(f"翻译过程中发生未知错误: {e}")
                raise
    
    def get_translation_statistics(self) -> dict:
        """
        获取翻译统计信息
        
        Returns:
            dict: 统计信息
        """
        success_rate = 0.0
        if self.total_translations > 0:
            success_rate = self.successful_translations / self.total_translations
        
        avg_processing_time = 0.0
        if self.total_translations > 0:
            avg_processing_time = self.total_processing_time / self.total_translations
        
        return {
            "total_translations": self.total_translations,
            "successful_translations": self.successful_translations,
            "failed_translations": self.failed_translations,
            "success_rate": success_rate,
            "avg_processing_time": avg_processing_time,
            "total_processing_time": self.total_processing_time
        }