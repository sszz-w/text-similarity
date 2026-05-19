"""
方案一：基于 TF-IDF + 余弦相似度的段落雷同检测

原理：将每个段落转为 TF-IDF 向量，计算两篇文档段落间的余弦相似度。
优点：对语义相近但措辞不同的段落也有一定检测能力。
适用：检测改写、同义替换等较隐蔽的雷同。
"""
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tokenize(text: str) -> str:
    """中文分词，返回空格分隔的词语"""
    return " ".join(jieba.cut(text))


def detect_similarity_tfidf(
    paragraphs_a: list[str],
    paragraphs_b: list[str],
    threshold: float = 0.6,
) -> list[dict]:
    """
    使用 TF-IDF + 余弦相似度检测段落雷同。

    Args:
        paragraphs_a: 文档A的段落列表
        paragraphs_b: 文档B的段落列表
        threshold: 相似度阈值（0-1），超过此值视为雷同

    Returns:
        雷同段落对列表，每项包含段落索引、文本和相似度
    """
    if not paragraphs_a or not paragraphs_b:
        return []

    tokenized_a = [tokenize(p) for p in paragraphs_a]
    tokenized_b = [tokenize(p) for p in paragraphs_b]

    all_texts = tokenized_a + tokenized_b
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    matrix_a = tfidf_matrix[: len(tokenized_a)]
    matrix_b = tfidf_matrix[len(tokenized_a) :]

    sim_matrix = cosine_similarity(matrix_a, matrix_b)

    results = []
    for i in range(len(paragraphs_a)):
        for j in range(len(paragraphs_b)):
            score = sim_matrix[i][j]
            if score >= threshold:
                results.append({
                    "para_a_index": i,
                    "para_b_index": j,
                    "text_a": paragraphs_a[i],
                    "text_b": paragraphs_b[j],
                    "similarity": float(score),
                    "method": "TF-IDF + Cosine",
                })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results
