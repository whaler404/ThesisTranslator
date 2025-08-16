# 英文论文翻译器 - 测试计划文档

## 测试概述

本文档详细描述了英文论文翻译器项目的测试策略、测试用例和验收标准。测试分为单元测试、集成测试和端到端测试三个层级。

## 测试环境配置

### 测试框架
- **单元测试**: pytest
- **覆盖率测试**: pytest-cov
- **模拟测试**: unittest.mock
- **性能测试**: pytest-benchmark

### 测试数据
```
tests/data/
├── sample_papers/
│   ├── simple_paper.pdf      # 简单结构论文
│   ├── complex_paper.pdf     # 复杂结构论文
│   ├── math_heavy_paper.pdf  # 数学公式密集论文
│   └── multi_column.pdf      # 多栏布局论文
├── expected_outputs/
│   ├── simple_paper.md
│   ├── complex_paper.md
│   └── math_heavy_paper.md
└── mock_responses/
    ├── openai_responses.json
    └── error_scenarios.json
```

## 单元测试计划

### 1. PDF文本解析模块测试 (`test_pdf_parser.py`)

#### 测试类: `TestPDFTextExtractor`

**测试用例1: 基本文本提取**
```python
def test_extract_basic_text():
    """测试从简单PDF中提取文本"""
    # 给定: 包含基本文本的PDF文件
    # 当: 调用extract_text_blocks()
    # 则: 应返回正确的TextBlock列表
    pass

def test_extract_text_with_formatting():
    """测试提取包含格式的文本"""
    # 给定: 包含粗体、斜体等格式的PDF
    # 当: 提取文本块
    # 则: 应保留字体信息
    pass

def test_extract_mathematical_formulas():
    """测试数学公式文本提取"""
    # 给定: 包含数学公式的PDF
    # 当: 提取文本
    # 则: 应正确识别公式文本
    pass

def test_reading_order_extraction():
    """测试阅读顺序提取"""
    # 给定: 多栏布局的PDF
    # 当: 获取阅读顺序
    # 则: 应按正确的逻辑顺序排列
    pass

def test_bbox_coordinates():
    """测试边界框坐标准确性"""
    # 给定: 已知位置的文本
    # 当: 提取边界框
    # 则: 坐标应在预期范围内
    pass

def test_font_info_extraction():
    """测试字体信息提取"""
    # 给定: 不同字体的文本
    # 当: 提取字体信息
    # 则: 应包含字体名称、大小、样式
    pass
```

**边界条件测试**:
- 空PDF文件
- 损坏的PDF文件
- 只包含图片的PDF
- 超大PDF文件
- 密码保护的PDF

### 2. 文本分块模块测试 (`test_text_chunker.py`)

#### 测试类: `TestTextChunker`

**测试用例2: 文本分块功能**
```python
def test_chunk_creation_basic():
    """测试基本分块功能"""
    # 给定: 文本块列表
    # 当: 创建固定大小的chunk
    # 则: 每个chunk不超过指定大小
    pass

def test_chunk_boundary_preservation():
    """测试分块边界保持"""
    # 给定: 包含完整句子的文本
    # 当: 分块处理
    # 则: 不应在句子中间断开
    pass

def test_merge_blocks_with_spaces():
    """测试块合并时空格处理"""
    # 给定: 多个文本块
    # 当: 合并为字符串
    # 则: 应用空格正确分隔
    pass

def test_empty_blocks_handling():
    """测试空块处理"""
    # 给定: 包含空文本块的列表
    # 当: 处理分块
    # 则: 应跳过空块
    pass

def test_chunk_size_configuration():
    """测试分块大小配置"""
    # 给定: 不同的分块大小设置
    # 当: 创建chunks
    # 则: 应遵循配置的大小限制
    pass
```

### 3. 文本清洗模块测试 (`test_text_cleaner.py`)

#### 测试类: `TestTextCleaner`

**测试用例3: 文本清洗功能**
```python
def test_formula_identification():
    """测试公式识别"""
    # 给定: 包含数学公式的文本
    # 当: 进行清洗处理
    # 则: 公式应被$$符号包裹
    pass

def test_title_identification():
    """测试标题识别"""
    # 给定: 包含标题的文本
    # 当: 清洗处理
    # 则: 标题应被<Title>标签包裹
    pass

def test_unwanted_content_removal():
    """测试无关内容移除"""
    # 给定: 包含作者信息、邮箱等的文本
    # 当: 清洗处理
    # 则: 无关内容应被移除
    pass

def test_paragraph_segmentation():
    """测试段落分割"""
    # 给定: 连续的文本
    # 当: 识别段落边界
    # 则: 应添加<End>标记
    pass

def test_output_post_processing():
    """测试输出后处理"""
    # 给定: 包含标记的清洗文本
    # 当: 后处理转换
    # 则: 标记应转换为Markdown格式
    pass
```

**模拟AI响应测试**:
```python
@patch('openai.ChatCompletion.create')
def test_openai_api_integration(mock_openai):
    """测试OpenAI API集成"""
    # 模拟API响应
    mock_openai.return_value = Mock(...)
    # 测试API调用和响应处理
    pass
```

### 4. 文本排序模块测试 (`test_text_sorter.py`)

#### 测试类: `TestTextSorter`

**测试用例4: 文本排序功能**
```python
def test_semantic_ordering():
    """测试语义排序"""
    # 给定: 顺序混乱的句子
    # 当: 进行语义排序
    # 则: 应返回逻辑连贯的文本
    pass

def test_sentence_order_detection():
    """测试句子顺序检测"""
    # 给定: 正常顺序的文本
    # 当: 检查顺序
    # 则: 应识别为正确顺序
    pass

def test_academic_structure_preservation():
    """测试学术结构保持"""
    # 给定: 学术论文文本
    # 当: 排序处理
    # 则: 应保持学术逻辑结构
    pass
```

### 5. 翻译模块测试 (`test_translator.py`)

#### 测试类: `TestAITranslator`

**测试用例5: 翻译功能**
```python
def test_basic_translation():
    """测试基本翻译功能"""
    # 给定: 英文文本
    # 当: 调用翻译
    # 则: 应返回中文翻译
    pass

def test_latex_formula_preservation():
    """测试LaTeX公式保持"""
    # 给定: 包含LaTeX公式的文本
    # 当: 翻译处理
    # 则: 公式格式应保持不变
    pass

def test_academic_terminology():
    """测试学术术语翻译"""
    # 给定: 包含专业术语的文本
    # 当: 翻译
    # 则: 术语翻译应准确
    pass

def test_batch_translation():
    """测试批量翻译"""
    # 给定: 多个文本块
    # 当: 批量翻译
    # 则: 所有块都应被翻译
    pass
```

### 6. Markdown生成模块测试 (`test_markdown_generator.py`)

#### 测试类: `TestMarkdownGenerator`

**测试用例6: Markdown生成**
```python
def test_title_conversion():
    """测试标题转换"""
    # 给定: 带有Title标签的文本
    # 当: 转换为Markdown
    # 则: 应生成正确的标题格式
    pass

def test_paragraph_formatting():
    """测试段落格式化"""
    # 给定: 带有End标记的文本
    # 当: 格式化处理
    # 则: 应生成正确的段落分隔
    pass

def test_complete_markdown_generation():
    """测试完整Markdown生成"""
    # 给定: 翻译后的文本块
    # 当: 生成Markdown
    # 则: 应产生有效的Markdown文档
    pass
```

## 集成测试计划

### 测试类: `TestIntegration`

#### 集成测试用例

**端到端流程测试**
```python
def test_complete_translation_pipeline():
    """测试完整翻译流程"""
    # 给定: 英文PDF论文
    # 当: 执行完整翻译流程
    # 则: 应生成正确的中文Markdown
    pass

def test_error_handling_integration():
    """测试错误处理集成"""
    # 给定: 各种错误场景
    # 当: 执行翻译流程
    # 则: 应优雅处理错误并继续
    pass

def test_performance_integration():
    """测试性能集成"""
    # 给定: 大型PDF文件
    # 当: 执行翻译
    # 则: 应在合理时间内完成
    pass
```

## 性能测试

### 基准测试

```python
def test_pdf_parsing_performance():
    """PDF解析性能测试"""
    # 测试不同大小PDF的解析时间
    pass

def test_translation_api_performance():
    """翻译API性能测试"""
    # 测试API调用延迟和吞吐量
    pass

def test_memory_usage():
    """内存使用测试"""
    # 监控处理大文件时的内存消耗
    pass
```

## 错误处理测试

### 异常场景测试

```python
def test_network_error_handling():
    """网络错误处理测试"""
    # 模拟网络中断、API限制等场景
    pass

def test_file_corruption_handling():
    """文件损坏处理测试"""
    # 测试损坏PDF文件的处理
    pass

def test_api_rate_limit_handling():
    """API限制处理测试"""
    # 测试API调用频率限制的处理
    pass
```

## 回归测试

### 自动化回归测试套件

```python
def test_output_consistency():
    """输出一致性测试"""
    # 确保代码变更不影响翻译质量
    pass

def test_format_compatibility():
    """格式兼容性测试"""
    # 测试不同PDF格式的兼容性
    pass
```

## 测试覆盖率目标

- **单元测试覆盖率**: ≥ 90%
- **集成测试覆盖率**: ≥ 80%
- **关键路径覆盖率**: 100%

## 测试执行命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html

# 运行性能测试
pytest tests/performance/ --benchmark-only

# 运行特定模块测试
pytest tests/test_pdf_parser.py -v
```

## 测试数据管理

### 测试数据要求

1. **多样性**: 涵盖不同学科、格式的论文
2. **复杂性**: 包含简单到复杂的各种结构
3. **真实性**: 使用真实的学术论文作为测试数据
4. **大小范围**: 从小文件到大文件的全覆盖

### 测试数据维护

- 定期更新测试数据集
- 版本控制测试数据
- 清理和标准化测试数据
- 保护版权和隐私

## 质量门禁

### 测试通过标准

1. 所有单元测试必须通过
2. 集成测试成功率 ≥ 95%
3. 代码覆盖率达到目标
4. 性能测试在基准范围内
5. 内存泄漏检测通过

### CI/CD集成

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 验收标准

### 功能验收

- [ ] 能够成功解析各种格式的PDF文件
- [ ] 正确识别和转换数学公式
- [ ] 准确翻译学术内容
- [ ] 生成格式正确的Markdown文档
- [ ] 错误处理机制工作正常

### 性能验收

- [ ] 10页PDF处理时间 < 5分钟
- [ ] 内存使用 < 1GB
- [ ] API调用成功率 > 95%
- [ ] 翻译质量可接受（人工评估）

### 可靠性验收

- [ ] 7x24小时稳定运行
- [ ] 异常恢复能力正常
- [ ] 日志记录完整准确
- [ ] 配置管理灵活可靠