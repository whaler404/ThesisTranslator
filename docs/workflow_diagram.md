# 英文论文翻译器 - 工作流程图

## 系统架构流程图

```mermaid
graph TD
    A[输入PDF文件] --> B[PDF文本解析模块]
    B --> C[文本分块模块]
    C --> D[文本清洗模块]
    D --> E[文本排序模块]
    E --> F[AI翻译模块]
    F --> G[Markdown生成模块]
    G --> H[输出Markdown文件]
    
    B --> B1[提取文本块<br/>获取位置信息<br/>按阅读顺序排列]
    C --> C1[按1000字符分块<br/>保持文本连续性<br/>空格分隔合并]
    D --> D1[LLM识别公式转LaTeX<br/>标记标题和段落<br/>移除无关内容]
    E --> E1[LLM语义排序<br/>确保句子连贯性<br/>保持逻辑结构]
    F --> F1[LLM英译中<br/>保持学术性<br/>保留格式]
    G --> G1[标签转Markdown<br/>合并所有块<br/>生成完整文档]
    
    I[错误处理] --> B
    I --> C
    I --> D
    I --> E
    I --> F
    I --> G
    
    J[日志记录] --> B
    J --> C
    J --> D
    J --> E
    J --> F
    J --> G
```

## 详细处理流程

### 阶段1: PDF文本解析
```mermaid
graph LR
    A[PDF文件] --> B[PyMuPDF打开]
    B --> C[逐页处理]
    C --> D[get_text dict模式]
    D --> E[提取文本块]
    E --> F[获取位置信息]
    F --> G[按几何位置排序]
    G --> H[生成TextBlock数组]
```

### 阶段2: 文本分块
```mermaid
graph LR
    A[TextBlock数组] --> B[按序遍历]
    B --> C[拼接文本内容]
    C --> D[空格分隔]
    D --> E[按1000字符分割]
    E --> F[生成文本块数组]
```

### 阶段3: 文本清洗
```mermaid
graph LR
    A[文本块] --> B[LLM清洗请求]
    B --> C[公式识别转LaTeX]
    C --> D[标题标记]
    D --> E[段落分割]
    E --> F[内容过滤]
    F --> G[正则处理标记]
    G --> H[清洗后文本]
```

### 阶段4: 文本排序
```mermaid
graph LR
    A[清洗后文本] --> B[LLM排序请求]
    B --> C[语义连贯性分析]
    C --> D[句子重新排列]
    D --> E[保持逻辑结构]
    E --> F[排序后文本]
```

### 阶段5: AI翻译
```mermaid
graph LR
    A[排序后文本] --> B[LLM翻译请求]
    B --> C[英译中处理]
    C --> D[保持格式]
    D --> E[学术术语准确性]
    E --> F[中文译文]
```

### 阶段6: Markdown生成
```mermaid
graph LR
    A[中文译文数组] --> B[处理Title标签]
    B --> C[处理End标签]
    C --> D[合并所有块]
    D --> E[生成Markdown]
    E --> F[输出文件]
```

## 数据流转

### TextBlock数据结构
```mermaid
classDiagram
    class TextBlock {
        +string text
        +tuple bbox
        +int page_num
        +int block_num
        +dict font_info
        +list line_info
    }
```

### 处理管道
```mermaid
sequenceDiagram
    participant PDF as PDF文件
    participant Parser as PDF解析器
    participant Chunker as 文本分块器
    participant Cleaner as 文本清洗器
    participant Sorter as 文本排序器
    participant Translator as AI翻译器
    participant Generator as Markdown生成器
    participant Output as 输出文件
    
    PDF->>Parser: 读取PDF
    Parser->>Chunker: TextBlock数组
    Chunker->>Cleaner: 文本块数组
    Cleaner->>Sorter: 清洗后文本
    Sorter->>Translator: 排序后文本
    Translator->>Generator: 翻译后文本
    Generator->>Output: Markdown文档
```

## 错误处理流程

```mermaid
graph TD
    A[开始处理] --> B{是否出错?}
    B -->|否| C[继续下一步]
    B -->|是| D[记录错误日志]
    D --> E{是否致命错误?}
    E -->|是| F[跳过当前块]
    E -->|否| G[重试处理]
    G --> H{重试次数 < 3?}
    H -->|是| B
    H -->|否| F
    F --> I[继续处理下一块]
    C --> J[处理完成]
    I --> J
```

## 配置管理流程

```mermaid
graph LR
    A[启动程序] --> B{配置文件存在?}
    B -->|是| C[加载配置文件]
    B -->|否| D[使用默认配置]
    C --> E{环境变量存在?}
    D --> E
    E -->|是| F[环境变量覆盖]
    E -->|否| G[使用当前配置]
    F --> G
    G --> H[验证配置有效性]
    H --> I[开始处理]
```

## 并发处理设计

```mermaid
graph TD
    A[主进程] --> B[文本分块]
    B --> C[分配到工作队列]
    C --> D[Worker 1<br/>清洗+排序]
    C --> E[Worker 2<br/>清洗+排序] 
    C --> F[Worker 3<br/>清洗+排序]
    D --> G[翻译队列]
    E --> G
    F --> G
    G --> H[翻译Worker 1]
    G --> I[翻译Worker 2]
    H --> J[收集结果]
    I --> J
    J --> K[Markdown生成]
    K --> L[输出文件]
```

## 性能监控

```mermaid
graph LR
    A[开始处理] --> B[记录开始时间]
    B --> C[各阶段处理]
    C --> D[记录阶段耗时]
    D --> E[更新进度]
    E --> F{处理完成?}
    F -->|否| C
    F -->|是| G[计算总耗时]
    G --> H[生成性能报告]
```

## 缓存机制

```mermaid
graph TD
    A[文本块] --> B{缓存中存在?}
    B -->|是| C[返回缓存结果]
    B -->|否| D[调用LLM处理]
    D --> E[保存到缓存]
    E --> F[返回处理结果]
    C --> G[使用结果]
    F --> G
```

## 日志系统

```mermaid
graph LR
    A[各模块] --> B[生成日志事件]
    B --> C[日志过滤器]
    C --> D[格式化]
    D --> E[控制台输出]
    D --> F[文件输出]
    F --> G[日志轮转]