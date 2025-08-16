# ThesisTranslator 使用示例

## 目录结构

```
examples/
├── README.md          # 本文件
├── usage_example.py   # 使用示例代码
└── sample.pdf         # 示例PDF文件（需要自己提供）
```

## 使用说明

### 1. 基本使用

```bash
# 设置OpenAI API密钥
export OPENAI_API_KEY="your-openai-api-key"

# 运行主程序
python -m src.main input.pdf output.md
```

### 2. 运行示例代码

```bash
# 运行使用示例
python examples/usage_example.py
```

### 3. 运行测试

```bash
# 运行所有单元测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_pdf_parser.py -v
```

## 注意事项

1. **API密钥**: 需要有效的OpenAI API密钥才能运行翻译功能
2. **依赖包**: 确保已安装所有依赖包
3. **PDF文件**: 示例中的PDF文件需要自己提供
4. **网络连接**: 需要稳定的网络连接以调用OpenAI API

## 示例输出

运行示例代码后，您将看到类似以下的输出：

```
ThesisTranslator 使用示例
==============================
=== 基本使用示例 ===
=== 高级使用示例 ===
配置已更新:
  model: gpt-4
  chunk_size: 800
  temperature: 0.2
  include_toc: True
  include_metadata: True

=== 错误处理示例 ===
处理结果:
  成功: False
  错误数: 1
  处理时间: 0.00秒

注意: 这些示例需要:
1. 实际的PDF文件
2. 有效的OpenAI API密钥
3. 安装所有依赖包