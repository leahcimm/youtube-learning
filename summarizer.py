"""
Free, no-API-key summarizer.
Uses TF-IDF + jieba (Chinese) to extract key points from a transcript.
"""

import re
import math
from collections import Counter

# Chinese stopwords
ZH_STOPWORDS = set("""
的 了 是 在 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有
他 她 它 们 这 那 之 与 但 而 或 以 于 对 等 如 其 及 可 能 让 把 被 所 因
为 时 来 个 我们 你们 他们 她们 这个 那个 这些 那些 什么 怎么 为什么
因为 所以 如果 但是 而且 然后 所以 还有 已经 可以 应该 需要 一些 这样
那样 当然 只是 真的 非常 特别 其实 虽然 虽然 不过 另外 比较 一直 开始
现在 以前 之后 之前 最后 一样 可能 一种 这种 那种 方式 通过 使用 进行
"""
.split())

EN_STOPWORDS = set("""
a an the is are was were be been being have has had do does did will would shall
should may might must can could ought to of in on at for with by from up about
into through during before after above below between each few more most other
some such no nor not only own same so than too very just but and or as i me my
myself we our ours ourselves you your yours yourself yourselves he him his himself
she her hers herself it its itself they them their theirs themselves what which
who whom this that these those am it's i'm i've i'll i'd we're we've we'll we'd
you're you've you'll you'd he's he'll he'd she's she'll she'd it's they're
they've they'll they'd that's there's here's let's
""".split())


def is_chinese(text: str) -> bool:
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    return chinese_chars / max(len(text), 1) > 0.2


def tokenize(text: str, lang: str) -> list:
    if lang == "zh":
        import jieba
        return [w for w in jieba.cut(text) if w.strip() and w not in ZH_STOPWORDS and len(w) > 1]
    else:
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return [w for w in words if w not in EN_STOPWORDS and len(w) > 2]


def split_sentences(text: str, lang: str) -> list:
    if lang == "zh":
        sentences = re.split(r'[。！？；\n]', text)
    else:
        sentences = re.split(r'[.!?]\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 15]


def tfidf_scores(sentences: list, lang: str) -> list:
    tokenized = [tokenize(s, lang) for s in sentences]
    n = len(sentences)

    # Term frequency per sentence
    tf = [Counter(tokens) for tokens in tokenized]

    # Document frequency
    df = Counter()
    for tokens in tokenized:
        for word in set(tokens):
            df[word] += 1

    # IDF
    idf = {word: math.log(n / (1 + freq)) for word, freq in df.items()}

    # Score each sentence
    scores = []
    for i, tokens in enumerate(tokenized):
        if not tokens:
            scores.append(0.0)
            continue
        score = sum(tf[i][w] * idf.get(w, 0) for w in tokens) / len(tokens)
        scores.append(score)

    return scores


def make_heading(sentence: str, lang: str, max_words: int = 6) -> str:
    tokens = tokenize(sentence, lang)
    if not tokens:
        return sentence[:30]

    if lang == "zh":
        # Take first 8-12 chars of sentence as heading
        clean = re.sub(r'\s+', '', sentence)
        return clean[:12] + ("…" if len(clean) > 12 else "")
    else:
        words = sentence.split()
        return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


TOPIC_EMOJIS = {
    # Chinese keywords
    "下载": "💾", "安装": "⚙️", "介面": "🖥️", "功能": "✨", "设定": "⚙️",
    "档案": "📁", "文件": "📄", "代码": "💻", "程式": "💻", "浏览器": "🌐",
    "网站": "🌐", "费用": "💰", "付费": "💰", "订阅": "💳", "价格": "💰",
    "安全": "🔒", "隐私": "🔏", "学习": "📚", "工作": "💼", "效率": "⚡",
    "自动": "🤖", "AI": "🤖", "助理": "🤖", "操作": "🖱️", "步骤": "📋",
    "结果": "🎯", "重要": "⭐", "注意": "⚠️", "优点": "👍", "缺点": "👎",
    # English keywords
    "download": "💾", "install": "⚙️", "interface": "🖥️", "feature": "✨",
    "file": "📁", "code": "💻", "browser": "🌐", "cost": "💰", "free": "🆓",
    "security": "🔒", "learn": "📚", "work": "💼", "fast": "⚡",
    "auto": "🤖", "ai": "🤖", "step": "📋", "result": "🎯", "tip": "💡",
    "important": "⭐", "warning": "⚠️", "benefit": "👍", "create": "🔨",
}

DEFAULT_EMOJIS = ["💡", "🎯", "📌", "🔑", "📝", "🌟", "⚡", "🔍"]


def pick_emoji(sentence: str, index: int) -> str:
    lower = sentence.lower()
    for keyword, emoji in TOPIC_EMOJIS.items():
        if keyword in lower or keyword in sentence:
            return emoji
    return DEFAULT_EMOJIS[index % len(DEFAULT_EMOJIS)]


def extract_key_points(snippets: list[dict], n_points: int = 7) -> dict:
    """
    snippets: list of {text, start, duration} dicts from youtube_transcript_api
    Returns structured key-points dict.
    """
    # Merge snippets into time-based segments (~60s each)
    segments = []
    current_text = []
    current_start = 0
    window = 60  # seconds

    for s in snippets:
        if s["start"] - current_start > window and current_text:
            segments.append({"text": " ".join(current_text), "start": current_start})
            current_text = []
            current_start = s["start"]
        current_text.append(s["text"])

    if current_text:
        segments.append({"text": " ".join(current_text), "start": current_start})

    # Detect language
    all_text = " ".join(s["text"] for s in snippets)
    lang = "zh" if is_chinese(all_text) else "en"

    # Score each segment
    segment_texts = [s["text"] for s in segments]
    scores = tfidf_scores(segment_texts, lang)

    # Pick top n segments
    ranked = sorted(enumerate(scores), key=lambda x: -x[1])
    top_indices = sorted([i for i, _ in ranked[:n_points]])

    # Build key points
    key_points = []
    for rank, idx in enumerate(top_indices):
        seg = segments[idx]
        sentences = split_sentences(seg["text"], lang)
        if not sentences:
            continue

        # Pick the highest-scoring sentence within this segment
        sent_scores = tfidf_scores(sentences, lang)
        best_sent = sentences[sent_scores.index(max(sent_scores))] if sent_scores else sentences[0]

        key_points.append({
            "emoji": pick_emoji(best_sent, rank),
            "heading": make_heading(best_sent, lang),
            "detail": best_sent[:200],
            "timestamp": int(segments[idx]["start"]),
        })

    # Title: first meaningful sentence
    first_sentences = split_sentences(segment_texts[0] if segment_texts else "", lang)
    title = make_heading(first_sentences[0], lang, max_words=8) if first_sentences else "Video Summary"

    # Summary: top 2 sentences from whole transcript
    all_sentences = split_sentences(all_text, lang)
    all_scores = tfidf_scores(all_sentences, lang)
    if all_scores:
        top2 = sorted(range(len(all_scores)), key=lambda i: -all_scores[i])[:2]
        top2 = sorted(top2)
        summary = " ".join(all_sentences[i] for i in top2)
    else:
        summary = all_text[:200]

    # Takeaway: single highest-scoring sentence
    if all_scores:
        best_idx = all_scores.index(max(all_scores))
        takeaway = all_sentences[best_idx]
    else:
        takeaway = key_points[0]["detail"] if key_points else ""

    return {
        "title": title,
        "summary": summary[:400],
        "key_points": key_points,
        "takeaway": takeaway[:300],
        "lang": lang,
    }
