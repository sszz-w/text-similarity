"""
方案四：共同错别字检测

原理：检测两份文档中是否存在相同的错别字/异常用词。
      如果两份投标文件出现相同的错别字，极大概率是抄袭或串通。
策略：
  1. 使用常见错别字词典进行匹配
  2. 检测两文档中相同的低频异常词（非标准用语）
  3. 检测相同的标点符号误用模式
"""
import re
from collections import Counter
from difflib import SequenceMatcher

import jieba

COMMON_TYPOS = {
    "的": ["得", "地"],
    "得": ["的", "地"],
    "地": ["的", "得"],
    "在": ["再"],
    "再": ["在"],
    "做": ["作", "座"],
    "作": ["做"],
    "已": ["以", "一"],
    "以": ["已"],
    "像": ["象"],
    "象": ["像"],
    "那": ["哪"],
    "哪": ["那"],
    "帐": ["账"],
    "账": ["帐"],
    "份": ["分"],
    "分": ["份"],
    "需": ["须"],
    "须": ["需"],
    "采": ["彩"],
    "彩": ["采"],
    "报": ["抱"],
    "抱": ["报"],
    "按": ["安"],
    "安": ["按"],
    "部署": ["布署"],
    "布署": ["部署"],
    "安装": ["按装"],
    "按装": ["安装"],
    "竣工": ["峻工", "俊工"],
    "峻工": ["竣工"],
    "俊工": ["竣工"],
    "竞标": ["竟标"],
    "竟标": ["竞标"],
    "竞争": ["竟争"],
    "竟争": ["竞争"],
    "投标": ["头标"],
    "中标": ["中彪"],
    "废标": ["费标"],
    "费标": ["废标"],
    "工期": ["工其"],
    "施工": ["实工"],
    "验收": ["验受"],
    "验受": ["验收"],
    "措施": ["错施"],
    "错施": ["措施"],
    "规范": ["规犯"],
    "规犯": ["规范"],
    "方案": ["方按"],
    "方按": ["方案"],
    "质量": ["制量"],
    "制量": ["质量"],
    "合同": ["合童"],
    "合童": ["合同"],
    "签订": ["签定"],
    "签定": ["签订"],
    "制定": ["制订"],
    "制订": ["制定"],
    "订立": ["定立"],
    "定立": ["订立"],
}

SUSPICIOUS_PATTERNS = [
    r"[，。！？；：]{2,}",
    r"[a-zA-Z]\s{2,}[a-zA-Z]",
    r"\d+\s*[。，]",
    r"[（(]\s*[）)]",
]


def find_common_typos(
    paragraphs_a: list[str],
    paragraphs_b: list[str],
) -> list[dict]:
    """
    检测两份文档中相同的错别字。

    Returns:
        共同错别字列表，包含错别字内容、出现位置等
    """
    typos_a = _extract_potential_typos(paragraphs_a)
    typos_b = _extract_potential_typos(paragraphs_b)

    common_typos = []
    for typo_info_a in typos_a:
        for typo_info_b in typos_b:
            if typo_info_a["typo"] == typo_info_b["typo"]:
                context_sim = SequenceMatcher(
                    None, typo_info_a["context"], typo_info_b["context"]
                ).ratio()
                if context_sim > 0.4:
                    common_typos.append({
                        "typo": typo_info_a["typo"],
                        "correct_form": typo_info_a["correct_form"],
                        "location_a": {
                            "para_index": typo_info_a["para_index"],
                            "context": typo_info_a["context"],
                        },
                        "location_b": {
                            "para_index": typo_info_b["para_index"],
                            "context": typo_info_b["context"],
                        },
                        "context_similarity": context_sim,
                    })

    common_typos.sort(key=lambda x: x["context_similarity"], reverse=True)
    return common_typos


def _extract_potential_typos(paragraphs: list[str]) -> list[dict]:
    """从段落中提取可能的错别字"""
    typos = []
    for idx, para in enumerate(paragraphs):
        words = list(jieba.cut(para))
        for i, word in enumerate(words):
            if word in COMMON_TYPOS:
                context_start = max(0, i - 3)
                context_end = min(len(words), i + 4)
                context = "".join(words[context_start:context_end])
                for correct in COMMON_TYPOS[word]:
                    if _is_likely_typo(words, i, word, correct):
                        typos.append({
                            "typo": word,
                            "correct_form": correct,
                            "para_index": idx,
                            "context": context,
                        })
    return typos


KNOWN_TYPO_WORDS = {
    "布署", "按装", "峻工", "俊工", "竟标", "竟争", "头标", "中彪",
    "费标", "工其", "实工", "验受", "错施", "规犯", "方按", "制量",
    "合童", "签定", "定立",
}


def _is_likely_typo(words: list[str], pos: int, word: str, correct: str) -> bool:
    """启发式判断是否为错别字"""
    if word in KNOWN_TYPO_WORDS:
        return True
    if word in ("的", "得", "地"):
        if pos > 0 and pos < len(words) - 1:
            prev = words[pos - 1]
            next_w = words[pos + 1]
            if word == "的" and len(next_w) > 1 and next_w[-1] in "了着过":
                return True
            if word == "地" and len(prev) > 1:
                return True
    return False


def find_common_unusual_phrases(
    paragraphs_a: list[str],
    paragraphs_b: list[str],
    min_phrase_len: int = 4,
) -> list[dict]:
    """
    检测两份文档中相同的异常/低频短语。
    如果两份文档使用了相同的不常见表述，可能暗示抄袭。
    """
    ngrams_a = _extract_ngrams(paragraphs_a, min_phrase_len)
    ngrams_b = _extract_ngrams(paragraphs_b, min_phrase_len)

    common = set(ngrams_a.keys()) & set(ngrams_b.keys())

    results = []
    for phrase in common:
        if len(phrase) >= min_phrase_len and not _is_common_phrase(phrase):
            results.append({
                "phrase": phrase,
                "count_in_a": ngrams_a[phrase],
                "count_in_b": ngrams_b[phrase],
            })

    results.sort(key=lambda x: len(x["phrase"]), reverse=True)
    return results


def _extract_ngrams(paragraphs: list[str], min_len: int) -> dict[str, int]:
    """提取文本中的 n-gram 短语"""
    counter: Counter = Counter()
    for para in paragraphs:
        words = list(jieba.cut(para))
        for n in range(2, 6):
            for i in range(len(words) - n + 1):
                phrase = "".join(words[i : i + n])
                if len(phrase) >= min_len:
                    counter[phrase] += 1
    return dict(counter)


def _is_common_phrase(phrase: str) -> bool:
    """判断是否为常见短语（排除过于普通的表述）"""
    common_phrases = {
        "根据", "按照", "为了", "因此", "所以", "但是", "然而",
        "同时", "并且", "或者", "如果", "虽然", "不过", "而且",
        "的情况", "进行了", "有关的", "以及", "对于", "关于",
        "投标人", "招标人", "招标文件", "投标文件", "中标",
        "合同", "工程", "项目", "施工", "验收", "质量",
    }
    return phrase in common_phrases


def find_common_punctuation_errors(
    paragraphs_a: list[str],
    paragraphs_b: list[str],
) -> list[dict]:
    """检测两份文档中相同的标点符号误用"""
    errors_a = _find_punctuation_errors(paragraphs_a)
    errors_b = _find_punctuation_errors(paragraphs_b)

    common = []
    for err_a in errors_a:
        for err_b in errors_b:
            if err_a["pattern"] == err_b["pattern"]:
                context_sim = SequenceMatcher(
                    None, err_a["context"], err_b["context"]
                ).ratio()
                if context_sim > 0.3:
                    common.append({
                        "pattern": err_a["pattern"],
                        "context_a": err_a["context"],
                        "context_b": err_b["context"],
                        "context_similarity": context_sim,
                    })

    return common


def _find_punctuation_errors(paragraphs: list[str]) -> list[dict]:
    """查找标点符号误用"""
    errors = []
    for idx, para in enumerate(paragraphs):
        for pattern in SUSPICIOUS_PATTERNS:
            matches = re.finditer(pattern, para)
            for match in matches:
                start = max(0, match.start() - 10)
                end = min(len(para), match.end() + 10)
                errors.append({
                    "pattern": match.group(),
                    "context": para[start:end],
                    "para_index": idx,
                })
    return errors
