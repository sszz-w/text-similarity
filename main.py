"""
投标文件文本雷同检测工具 - 主程序

整合四种检测方案，对两个 Word 文档进行全面的文本雷同分析：
1. TF-IDF + 余弦相似度
2. SequenceMatcher (最长公共子序列)
3. SimHash 指纹
4. 共同错别字检测
"""
import argparse
import json
import sys
import time
from pathlib import Path

from doc_parser import extract_all_text, extract_paragraphs
from method_sequence import detect_similarity_sequence
from method_simhash import detect_similarity_simhash
from method_tfidf import detect_similarity_tfidf
from method_typo import (
    find_common_punctuation_errors,
    find_common_typos,
    find_common_unusual_phrases,
)


def run_detection(
    file_a: str,
    file_b: str,
    threshold: float = 0.6,
    include_tables: bool = True,
    methods: list[str] | None = None,
) -> dict:
    """
    执行完整的文本雷同检测。

    Args:
        file_a: 文档A路径
        file_b: 文档B路径
        threshold: 相似度阈值
        include_tables: 是否包含表格内容
        methods: 要使用的检测方法列表，None 表示全部

    Returns:
        检测结果字典
    """
    if methods is None:
        methods = ["tfidf", "sequence", "simhash", "typo"]

    print(f"正在解析文档...")
    if include_tables:
        paragraphs_a = extract_all_text(file_a)
        paragraphs_b = extract_all_text(file_b)
    else:
        paragraphs_a = extract_paragraphs(file_a)
        paragraphs_b = extract_paragraphs(file_b)

    print(f"文档A: {len(paragraphs_a)} 个段落")
    print(f"文档B: {len(paragraphs_b)} 个段落")

    results = {
        "file_a": file_a,
        "file_b": file_b,
        "paragraphs_count_a": len(paragraphs_a),
        "paragraphs_count_b": len(paragraphs_b),
        "threshold": threshold,
        "detections": {},
    }

    if "tfidf" in methods:
        print("\n[方案一] TF-IDF + 余弦相似度检测中...")
        start = time.time()
        tfidf_results = detect_similarity_tfidf(paragraphs_a, paragraphs_b, threshold)
        elapsed = time.time() - start
        results["detections"]["tfidf"] = {
            "method_name": "TF-IDF + 余弦相似度",
            "matches": tfidf_results,
            "match_count": len(tfidf_results),
            "time_seconds": round(elapsed, 2),
        }
        print(f"  发现 {len(tfidf_results)} 对雷同段落 (耗时 {elapsed:.2f}s)")

    if "sequence" in methods:
        print("\n[方案二] SequenceMatcher 检测中...")
        start = time.time()
        seq_results = detect_similarity_sequence(paragraphs_a, paragraphs_b, threshold)
        elapsed = time.time() - start
        results["detections"]["sequence"] = {
            "method_name": "SequenceMatcher (最长公共子序列)",
            "matches": seq_results,
            "match_count": len(seq_results),
            "time_seconds": round(elapsed, 2),
        }
        print(f"  发现 {len(seq_results)} 对雷同段落 (耗时 {elapsed:.2f}s)")

    if "simhash" in methods:
        print("\n[方案三] SimHash 指纹检测中...")
        start = time.time()
        simhash_results = detect_similarity_simhash(paragraphs_a, paragraphs_b)
        elapsed = time.time() - start
        results["detections"]["simhash"] = {
            "method_name": "SimHash 指纹",
            "matches": simhash_results,
            "match_count": len(simhash_results),
            "time_seconds": round(elapsed, 2),
        }
        print(f"  发现 {len(simhash_results)} 对雷同段落 (耗时 {elapsed:.2f}s)")

    if "typo" in methods:
        print("\n[方案四] 共同错别字检测中...")
        start = time.time()
        typo_results = find_common_typos(paragraphs_a, paragraphs_b)
        unusual_phrases = find_common_unusual_phrases(paragraphs_a, paragraphs_b)
        punct_errors = find_common_punctuation_errors(paragraphs_a, paragraphs_b)
        elapsed = time.time() - start
        results["detections"]["typo"] = {
            "method_name": "共同错别字/异常用词检测",
            "common_typos": typo_results,
            "common_unusual_phrases": unusual_phrases[:50],
            "common_punctuation_errors": punct_errors,
            "typo_count": len(typo_results),
            "unusual_phrase_count": len(unusual_phrases),
            "punctuation_error_count": len(punct_errors),
            "time_seconds": round(elapsed, 2),
        }
        print(f"  发现 {len(typo_results)} 个共同错别字")
        print(f"  发现 {len(unusual_phrases)} 个共同异常短语")
        print(f"  发现 {len(punct_errors)} 个共同标点错误")

    results["summary"] = _generate_summary(results)
    return results


def _generate_summary(results: dict) -> dict:
    """生成检测结果摘要"""
    detections = results["detections"]
    total_matches = 0
    high_similarity_count = 0

    for method_key, method_data in detections.items():
        if method_key == "typo":
            total_matches += method_data["typo_count"]
            total_matches += method_data["unusual_phrase_count"]
        else:
            total_matches += method_data["match_count"]
            for match in method_data["matches"]:
                if match["similarity"] >= 0.9:
                    high_similarity_count += 1

    risk_level = "低"
    if high_similarity_count > 5 or total_matches > 20:
        risk_level = "高"
    elif high_similarity_count > 2 or total_matches > 10:
        risk_level = "中"

    return {
        "total_matches": total_matches,
        "high_similarity_count": high_similarity_count,
        "risk_level": risk_level,
    }


def print_report(results: dict) -> None:
    """打印可读的检测报告"""
    print("\n" + "=" * 70)
    print("投标文件文本雷同检测报告")
    print("=" * 70)
    print(f"\n文档A: {results['file_a']}")
    print(f"文档B: {results['file_b']}")
    print(f"段落数: A={results['paragraphs_count_a']}, B={results['paragraphs_count_b']}")
    print(f"相似度阈值: {results['threshold']}")

    summary = results["summary"]
    print(f"\n{'─' * 70}")
    print(f"综合评估: 雷同风险等级 [{summary['risk_level']}]")
    print(f"  总匹配数: {summary['total_matches']}")
    print(f"  高度相似(≥0.9): {summary['high_similarity_count']} 对")
    print(f"{'─' * 70}")

    for method_key, method_data in results["detections"].items():
        print(f"\n{'─' * 70}")
        if method_key == "typo":
            print(f"【{method_data['method_name']}】")
            if method_data["common_typos"]:
                print(f"\n  共同错别字 ({method_data['typo_count']} 个):")
                for item in method_data["common_typos"][:10]:
                    print(f"    - 错别字: '{item['typo']}' (正确: '{item['correct_form']}')")
                    print(f"      文档A上下文: {item['location_a']['context']}")
                    print(f"      文档B上下文: {item['location_b']['context']}")

            if method_data["common_unusual_phrases"]:
                print(f"\n  共同异常短语 ({method_data['unusual_phrase_count']} 个，显示前10):")
                for item in method_data["common_unusual_phrases"][:10]:
                    print(f"    - '{item['phrase']}' (A中{item['count_in_a']}次, B中{item['count_in_b']}次)")

            if method_data["common_punctuation_errors"]:
                print(f"\n  共同标点错误 ({method_data['punctuation_error_count']} 个):")
                for item in method_data["common_punctuation_errors"][:5]:
                    print(f"    - 模式: '{item['pattern']}'")
                    print(f"      文档A: {item['context_a']}")
                    print(f"      文档B: {item['context_b']}")
        else:
            print(f"【{method_data['method_name']}】 共 {method_data['match_count']} 对匹配")
            for item in method_data["matches"][:5]:
                print(f"\n  相似度: {item['similarity']:.2%}")
                text_a = item["text_a"][:80] + ("..." if len(item["text_a"]) > 80 else "")
                text_b = item["text_b"][:80] + ("..." if len(item["text_b"]) > 80 else "")
                print(f"  文档A[{item['para_a_index']}]: {text_a}")
                print(f"  文档B[{item['para_b_index']}]: {text_b}")
            if method_data["match_count"] > 5:
                print(f"\n  ... 还有 {method_data['match_count'] - 5} 对匹配未显示")

    print(f"\n{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(
        description="投标文件文本雷同检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py doc1.docx doc2.docx
  python main.py doc1.docx doc2.docx --threshold 0.7
  python main.py doc1.docx doc2.docx --methods tfidf sequence
  python main.py doc1.docx doc2.docx --output result.json
        """,
    )
    parser.add_argument("file_a", help="第一个 Word 文档路径")
    parser.add_argument("file_b", help="第二个 Word 文档路径")
    parser.add_argument(
        "--threshold", type=float, default=0.6, help="相似度阈值 (默认: 0.6)"
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=["tfidf", "sequence", "simhash", "typo"],
        default=None,
        help="选择检测方法 (默认: 全部)",
    )
    parser.add_argument("--output", "-o", help="输出 JSON 结果文件路径")
    parser.add_argument(
        "--no-tables", action="store_true", help="不包含表格内容"
    )

    args = parser.parse_args()

    for f in [args.file_a, args.file_b]:
        if not Path(f).exists():
            print(f"错误: 文件不存在 - {f}", file=sys.stderr)
            sys.exit(1)

    results = run_detection(
        file_a=args.file_a,
        file_b=args.file_b,
        threshold=args.threshold,
        include_tables=not args.no_tables,
        methods=args.methods,
    )

    print_report(results)

    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存至: {output_path}")


if __name__ == "__main__":
    main()
