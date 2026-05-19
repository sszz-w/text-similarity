# 投标文件文本雷同检测工具

对两个 Word 文档进行多维度文本雷同分析，适用于投标文件串通检测场景。

## 检测方案

### 方案一：TF-IDF + 余弦相似度

将每个段落转为 TF-IDF 向量，计算文档间段落的余弦相似度。对语义相近但措辞不同的段落也有检测能力，适合发现改写、同义替换等较隐蔽的雷同。

### 方案二：SequenceMatcher（最长公共子序列）

基于 difflib.SequenceMatcher 计算文本相似比率，能精确定位完全一致的文本片段。适合检测直接复制或仅做少量修改的段落。

### 方案三：SimHash 指纹

为每个段落生成 SimHash 指纹，通过汉明距离快速判断近似重复。计算效率最高，适合大规模文档的快速筛选。

### 方案四：共同错别字/异常用词检测

检测两份文档中是否存在相同的错别字、异常短语和标点误用。如果两份投标文件出现相同的错别字，是串通投标的强有力证据。

## 方案对比

| 方案 | 适用场景 | 时间复杂度 | 特点 |
|------|----------|------------|------|
| TF-IDF + 余弦相似度 | 改写/同义替换 | O(n×m) | 语义层面检测 |
| SequenceMatcher | 直接复制/少量修改 | O(n×m) | 精确定位相同片段 |
| SimHash | 大规模快速筛选 | O(n×m) 但常数小 | 效率最高 |
| 共同错别字 | 串通投标取证 | O(n×m) | 错别字是强证据 |

## 部署与启动

### 环境要求

- Python 3.10+

### 安装步骤

```bash
# 克隆项目
cd text-sim

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 使用方法

```bash
# 基本用法：对比两个文档（使用全部方案）
python main.py 文档A.docx 文档B.docx

# 指定相似度阈值（默认 0.6）
python main.py 文档A.docx 文档B.docx --threshold 0.7

# 仅使用特定方案
python main.py 文档A.docx 文档B.docx --methods tfidf sequence
python main.py 文档A.docx 文档B.docx --methods typo

# 输出 JSON 结果
python main.py 文档A.docx 文档B.docx --output result.json

# 不包含表格内容
python main.py 文档A.docx 文档B.docx --no-tables
```

### 可选方法参数

- `tfidf` — TF-IDF + 余弦相似度
- `sequence` — SequenceMatcher
- `simhash` — SimHash 指纹
- `typo` — 共同错别字检测

### 运行测试

```bash
source .venv/bin/activate
python test_detection.py
```

## 项目结构

```
text-sim/
├── requirements.txt       # Python 依赖
├── doc_parser.py          # Word 文档解析（段落 + 表格）
├── method_tfidf.py        # 方案一：TF-IDF + 余弦相似度
├── method_sequence.py     # 方案二：SequenceMatcher
├── method_simhash.py      # 方案三：SimHash 指纹
├── method_typo.py         # 方案四：共同错别字检测
├── main.py                # 主程序入口
└── test_detection.py      # 测试脚本（含模拟数据）
```

## 输出说明

程序会输出一份检测报告，包含：

- 各方案检测到的雷同段落对及相似度
- 共同错别字及其上下文
- 共同异常短语统计
- 综合风险等级评估（低/中/高）

使用 `--output` 参数可将完整结果保存为 JSON 格式，方便后续处理或集成到其他系统中。
