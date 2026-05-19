"""
方案二：基于 SequenceMatcher 的段落雷同检测（编辑距离/最长公共子序列）

原理：使用 difflib.SequenceMatcher 计算两段文本的相似比率，
      基于最长公共子序列（LCS），能精确定位相同的文本片段。
优点：能精确找出哪些文字是完全一致的，适合检测复制粘贴。
适用：检测直接复制或仅做少量修改的段落。
"""
from difflib import SequenceMatcher


def detect_similarity_sequence(
    paragraphs_a: list[str],
    paragraphs_b: list[str],
    threshold: float = 0.6,
) -> list[dict]:
    """
    使用 SequenceMatcher 检测段落雷同。

    Args:
        paragraphs_a: 文档A的段落列表
        paragraphs_b: 文档B的段落列表
        threshold: 相似度阈值（0-1）

    Returns:
        雷同段落对列表
    """
    results = []

    for i, text_a in enumerate(paragraphs_a):
        for j, text_b in enumerate(paragraphs_b):
            if len(text_a) < 10 or len(text_b) < 10:
                continue

            ratio = SequenceMatcher(None, text_a, text_b).ratio()
            if ratio >= threshold:
                matching_blocks = get_matching_blocks(text_a, text_b)
                results.append({
                    "para_a_index": i,
                    "para_b_index": j,
                    "text_a": text_a,
                    "text_b": text_b,
                    "similarity": ratio,
                    "matching_blocks": matching_blocks,
                    "method": "SequenceMatcher (LCS)",
                })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results


def get_matching_blocks(text_a: str, text_b: str) -> list[str]:
    """提取两段文本中的公共子串"""
    matcher = SequenceMatcher(None, text_a, text_b)
    blocks = []
    for block in matcher.get_matching_blocks():
        if block.size > 5:
            blocks.append(text_a[block.a : block.a + block.size])
    return blocks
