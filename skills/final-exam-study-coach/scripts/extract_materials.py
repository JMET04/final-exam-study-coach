#!/usr/bin/env python3
"""Extract a first-pass study inventory from course materials."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path
from typing import Any


QUESTION_PATTERNS = {
    "记忆": r"默写|背诵|列举|识记|选择|填空|recall|list|identify|recognize",
    "解释": r"定义|解释|说明|机制|原因|为什么|define|explain|describe|why",
    "比较": r"比较|区分|辨析|异同|分类|compare|contrast|distinguish|classify",
    "计算": r"计算|求解|求出|代入|数值|calculate|compute|solve",
    "推导/证明": r"证明|推导|推论|show|prove|derive",
    "应用": r"应用|运用|解决|根据.*处理|apply|use .* to|solve",
    "案例分析": r"案例|情境|材料分析|case|scenario|analy[sz]e",
    "设计": r"设计|方案|建模|绘制|构建|design|model|create|draw",
    "评价": r"评价|评析|批判|优缺点|判断|critique|evaluate|assess|judge",
    "写作/论证": r"论述|作文|写作|论证|观点|essay|discuss|argue|writing",
    "实验/操作": r"实验|步骤|操作|测量|观察|experiment|lab|procedure",
}

TOPIC_HINTS = [
    "有效应力", "达西定律", "水力坡降", "三相组成", "固结", "沉降", "抗剪强度",
    "新民主主义", "社会主义改造", "毛泽东思想", "近代史", "现金流", "资金时间价值",
    "净现值", "内部收益率", "招投标", "合同管理", "进度管理", "质量管理",
]


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def xml_to_text(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = unescape(re.sub(r"\s+", " ", raw))
    text = re.sub(r"\bstyle\.[A-Za-z_.-]+\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        chunks = []
        for name in archive.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                chunks.append(xml_to_text(archive.read(name).decode("utf-8", errors="ignore")))
        return "\n".join(chunks)


def read_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        chunks = []
        for name in archive.namelist():
            if name.startswith("ppt/slides/") and name.endswith(".xml"):
                chunks.append(xml_to_text(archive.read(name).decode("utf-8", errors="ignore")))
        return "\n".join(chunks)


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return ""
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def read_material(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return read_text_file(path), "text"
    if suffix == ".json":
        return json.dumps(json.loads(read_text_file(path)), ensure_ascii=False, indent=2), "json"
    if suffix == ".docx":
        return read_docx(path), "docx"
    if suffix == ".pptx":
        return read_pptx(path), "pptx"
    if suffix == ".pdf":
        text = read_pdf(path)
        return text, "pdf" if text else "pdf_needs_manual_excerpt"
    if suffix == ".ppt":
        return "", "legacy_ppt_filename_only"
    return "", "unsupported"


def infer_role(path: Path, text: str) -> str:
    lower = f"{path.name} {text[:500]}".lower()
    if any(key in lower for key in ["往年", "真题", "past", "exam", "试卷", "试题", "模拟卷"]):
        return "past_paper"
    if any(key in lower for key in ["范围", "考纲", "scope", "syllabus"]):
        return "scope"
    if any(key in lower for key in ["ppt", "课件", "slide"]):
        return "slides"
    if any(key in lower for key in ["错题", "wrong"]):
        return "wrong_questions"
    if any(key in lower for key in ["教材", "textbook"]):
        return "textbook"
    return "notes"


def detect_question_type(text: str) -> str:
    hits = [label for label, pattern in QUESTION_PATTERNS.items() if re.search(pattern, text, re.I)]
    return "/".join(hits[:3]) if hits else "综合"


def detect_operations(question_type: str) -> list[str]:
    mapping = {
        "记忆": "recall", "解释": "explain", "比较": "compare", "计算": "calculate",
        "推导/证明": "derive_prove", "应用": "solve_apply", "案例分析": "analyze_case",
        "设计": "design_create", "评价": "critique_evaluate", "写作/论证": "write_argue",
        "实验/操作": "solve_apply",
    }
    return [mapping[item] for item in question_type.split("/") if item in mapping]


def clean_topic_name(topic: str) -> str:
    topic = unescape(topic)
    topic = re.sub(r"\s+", " ", topic).strip()
    topic = re.sub(r"^[\d.\-、\s第章节]+", "", topic)
    topic = re.split(r"\s+(?:第[一二三四五六七八九十\d]+章|[一二三四五六七八九十]、|小结|思考题|练习题)\s*", topic, maxsplit=1)[0]
    topic = re.sub(r"[：:，,。；;].*$", "", topic)
    return topic[:42].strip()


def is_good_topic(topic: str) -> bool:
    topic = clean_topic_name(topic)
    if len(topic) < 2 or len(topic) > 42:
        return False
    if topic.isdigit() or re.fullmatch(r"[A-Za-z0-9\s/.-]+", topic):
        return False
    return len(re.findall(r"[\u4e00-\u9fff]", topic)) >= 2


def extract_topic_hits(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for hint in TOPIC_HINTS:
        if hint in text:
            found.append((hint, text[max(0, text.find(hint) - 160): text.find(hint) + 220]))
    patterns = [
        r"^(?:第[一二三四五六七八九十\d]+[章节]|#+)\s*([^\n]{2,40})",
        r"\b\d+(?:\.\d+){1,2}\s*([\u4e00-\u9fff][^。；;\n]{2,32})",
        r"(?:重点|考点|掌握|理解|熟悉|要求)[:：\s]+([^。\n；;]{2,40})",
    ]
    for pattern in patterns:
        for item in re.findall(pattern, text, re.M | re.I):
            topic = clean_topic_name(item)
            if is_good_topic(topic):
                index = text.find(item)
                found.append((topic, text[max(0, index - 160): index + 220] if index >= 0 else item))
    return found


def extract_filename_topics(path: Path) -> list[tuple[str, str]]:
    stem = path.stem
    stem = re.sub(r"\s*[（(]\d+[）)]\s*$", "", stem)
    stem = re.sub(r"^\s*\d+(?:[.\-]\d+)*(?:\s*[（(]\d+[）)])?\s*[-_、.：:]*\s*", "", stem)
    stem = clean_topic_name(stem)
    return [(stem, path.name)] if is_good_topic(stem) else []


def evidence_for(role: str, count: int) -> str:
    if role == "scope":
        return "explicit"
    if role == "past_paper" or count >= 2:
        return "repeated"
    return "inferred"


def build_inventory(materials: Path, course: str, exclude_dir: Path | None = None) -> dict[str, Any]:
    root = materials.resolve() if materials.is_dir() else materials.resolve().parent
    files = [materials.resolve()] if materials.is_file() else [p.resolve() for p in materials.rglob("*") if p.is_file() and not p.name.startswith(".")]
    if exclude_dir:
        exclude_dir = exclude_dir.resolve()
        files = [p for p in files if p != exclude_dir and exclude_dir not in p.parents]
    sources = []
    topic_sources: dict[str, list[str]] = defaultdict(list)
    topic_text: dict[str, str] = defaultdict(str)
    topic_roles: dict[str, list[str]] = defaultdict(list)
    for path in files:
        text, kind = read_material(path)
        role = infer_role(path, text)
        rel = str(path.relative_to(root))
        if kind == "legacy_ppt_filename_only":
            summary = "老式PPT正文暂未自动读取；已从文件名提取主题，若要更细知识点请转换为pptx/pdf或提供文字摘录。"
        elif text:
            summary = re.sub(r"\s+", " ", text[:500].replace("\n", " ")).strip()
        else:
            summary = "需要手动摘录或暂不支持自动读取"
        sources.append({"path": rel, "type": kind, "role": role, "summary": summary})
        for topic, context in extract_filename_topics(path) + extract_topic_hits(text):
            topic_sources[topic].append(rel)
            topic_text[topic] += "\n" + context
            topic_roles[topic].append(role)
    topics = []
    for topic, refs in sorted(topic_sources.items(), key=lambda item: len(item[1]), reverse=True):
        role_counts = Counter(topic_roles[topic])
        main_role = role_counts.most_common(1)[0][0]
        qtype = detect_question_type(topic_text[topic])
        topics.append({"name": topic, "evidence": evidence_for(main_role, len(set(refs))), "question_type": qtype, "assessment_operations": detect_operations(qtype), "source_refs": sorted(set(refs))[:8], "signals": [f"{role}:{count}" for role, count in role_counts.items()], "status": "unknown"})
    return {"course": course, "sources": sources, "topics": topics}


def md_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).replace("\n", " ").replace("|", "\\|")).strip()


def write_markdown(data: dict[str, Any], output: Path) -> None:
    lines = [f"# {data['course']} 材料初筛", "", "## 材料清单", "", "| 文件 | 类型 | 角色 | 摘要 |", "| --- | --- | --- | --- |"]
    for source in data["sources"]:
        lines.append(f"| {md_cell(source['path'])} | {md_cell(source['type'])} | {md_cell(source['role'])} | {md_cell(source['summary'])} |")
    lines.extend(["", "## 知识点候选", "", "| 知识点 | 证据 | 题型 | 考试操作 | 来源 |", "| --- | --- | --- | --- | --- |"])
    for topic in data["topics"]:
        lines.append(f"| {md_cell(topic['name'])} | {topic['evidence']} | {md_cell(topic['question_type'])} | {md_cell(', '.join(topic.get('assessment_operations', [])))} | {md_cell(', '.join(topic['source_refs']))} |")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract first-pass course material inventory.")
    parser.add_argument("materials", type=Path)
    parser.add_argument("--course", default="未命名课程")
    parser.add_argument("--output-dir", type=Path, default=Path("extracted"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build_inventory(args.materials, args.course, args.output_dir)
    (args.output_dir / "material_inventory.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(data, args.output_dir / "material_inventory.md")
    print(f"Wrote {args.output_dir / 'material_inventory.json'}")
    print(f"Wrote {args.output_dir / 'material_inventory.md'}")


if __name__ == "__main__":
    main()
