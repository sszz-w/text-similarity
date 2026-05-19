"""
方案三：基于 SimHash 的快速近似重复检测

原理：为每个段落生成一个指纹（SimHash），通过比较指纹的汉明距离
      快速判断两段文本是否近似重复。
优点：计算效率极高，适合大规模文档比对。
适用：快速筛选出可能雷同的段落对，再用精确方法二次确认。
"""
import hashlib
import jieba


def simhash(text: str, hash_bits: int = 64) -> int:
    """计算文本的 SimHash 指纹"""
    tokens = list(jieba.cut(text))
    v = [0] * hash_bits

    for token in tokens:
        token_hash = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(hash_bits):
            if token_hash & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(hash_bits):
        if v[i] > 0:
            fingerprint |= 1 << i
    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """计算两个哈希值的汉明距离"""
    return bin(hash1 ^ hash2).count("1")


def detect_similarity_simhash(
    paragraphs_a: list[str],
    paragraphs_b: list[str],
    max_distance: int = 10,
    hash_bits: int = 64,
) -> list[dict]:
    """
    使用 SimHash 检测段落雷同。

    Args:
        paragraphs_a: 文档A的段落列表
        paragraphs_b: 文档B的段落列表
        max_distance: 最大汉明距离阈值，越小越严格
        hash_bits: 哈希位数

    Returns:
        雷同段落对列表
    """
    hashes_a = []
    for p in paragraphs_a:
        if len(p) >= 10:
            hashes_a.append(simhash(p, hash_bits))
        else:
            hashes_a.append(None)

    hashes_b = []
    for p in paragraphs_b:
        if len(p) >= 10:
            hashes_b.append(simhash(p, hash_bits))
        else:
            hashes_b.append(None)

    results = []
    for i, hash_a in enumerate(hashes_a):
        if hash_a is None:
            continue
        for j, hash_b in enumerate(hashes_b):
            if hash_b is None:
                continue

            distance = hamming_distance(hash_a, hash_b)
            if distance <= max_distance:
                similarity = 1 - distance / hash_bits
                results.append({
                    "para_a_index": i,
                    "para_b_index": j,
                    "text_a": paragraphs_a[i],
                    "text_b": paragraphs_b[j],
                    "similarity": similarity,
                    "hamming_distance": distance,
                    "method": "SimHash",
                })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results
