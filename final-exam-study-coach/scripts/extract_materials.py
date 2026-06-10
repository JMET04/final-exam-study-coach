#!/usr/bin/env python3
"""Extract a first-pass study inventory from course materials.

Supported without extra dependencies: .txt, .md, .json, .docx, .pptx.
PDF extraction is attempted when pypdf is installed; otherwise PDFs are listed
as sources that need manual excerpts.
"""

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
    "案例分析": r"案例|情境|材料分析|病案|案情|case|scenario|analy[sz]e",
    "设计": r"设计|方案|建模|绘制|构建|design|model|create|draw",
    "评价": r"评价|评析|批判|优缺点|判断|critique|evaluate|assess|judge",
    "翻译/解读": r"翻译|释义|解读|读图|读表|interpret|translate|paraphrase",
    "编程/调试": r"编程|算法|代码|实现|调试|改错|program|algorithm|code|implement|debug",
    "诊断/分类": r"诊断|归类|识别类型|判断类型|diagnose|classify",
    "写作/论证": r"论述|作文|写作|论证|观点|essay|discuss|argue|writing",
    "实验/操作": r"实验|步骤|操作|测量|观察|experiment|lab|procedure",
}

TOPIC_HINTS = [
    "极限", "导数", "积分", "泰勒", "矩阵", "行列式", "特征值", "特征向量", "对角化",
    "概率", "贝叶斯", "分布", "期望", "方差", "假设检验", "链表", "栈", "队列", "树",
    "图", "排序", "动态规划", "递归", "电路", "电流", "电压", "受力", "动量", "能量",
]

GENERIC_STOP_TOPICS = {
    "分布", "期望", "树", "图", "排序", "能量", "概念", "原理", "框架", "模型", "方法",
    "流程", "结构", "文本", "作品", "翻译", "设计", "评价", "规范", "误区", "案例",
}

SOCIAL_SCIENCE_OPS = ["recall", "explain", "compare", "write_argue", "analyze_case"]


def is_social_science_course(course: str) -> bool:
    return any(
        key in course
        for key in ["毛泽东", "中特", "中国近现代史", "近代史", "纲要", "马克思", "思想政治", "思政"]
    )


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        chunks = []
        for name in zf.namelist():
            if name.startswith("word/") and name.endswith(".xml"):
                raw = zf.read(name).decode("utf-8", errors="ignore")
                chunks.append(xml_to_text(raw))
        return "\n".join(chunks)


def read_pptx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        chunks = []
        for name in zf.namelist():
            if name.startswith("ppt/slides/") and name.endswith(".xml"):
                raw = zf.read(name).decode("utf-8", errors="ignore")
                chunks.append(xml_to_text(raw))
        return "\n".join(chunks)


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return ""
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def xml_to_text(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    return unescape(re.sub(r"\s+", " ", raw))


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
    return "", "unsupported"


def infer_role(path: Path, text: str) -> str:
    lower = f"{path.name} {text[:500]}".lower()
    if any(k in lower for k in ["往年", "真题", "past", "exam", "试卷", "试题", "模拟卷"]):
        return "past_paper"
    if any(k in lower for k in ["范围", "考纲", "scope", "syllabus"]):
        return "scope"
    if any(k in lower for k in ["ppt", "课件", "slide"]):
        return "slides"
    if any(k in lower for k in ["错题", "wrong"]):
        return "wrong_questions"
    if any(k in lower for k in ["教材", "textbook"]):
        return "textbook"
    return "notes"


def evidence_for(role: str, count: int) -> str:
    if role == "scope":
        return "explicit"
    if role == "past_paper" or count >= 2:
        return "repeated"
    return "inferred"


def detect_question_type(text: str) -> str:
    hits = [label for label, pattern in QUESTION_PATTERNS.items() if re.search(pattern, text, re.I)]
    return "/".join(hits[:3]) if hits else "综合"


def detect_operations(text: str) -> list[str]:
    operation_map = {
        "记忆": "recall",
        "解释": "explain",
        "比较": "compare",
        "计算": "calculate",
        "推导/证明": "derive_prove",
        "应用": "solve_apply",
        "案例分析": "analyze_case",
        "设计": "design_create",
        "评价": "critique_evaluate",
        "翻译/解读": "translate_interpret",
        "编程/调试": "implement_debug",
        "诊断/分类": "diagnose_classify",
        "写作/论证": "write_argue",
        "实验/操作": "solve_apply",
    }
    labels = detect_question_type(text).split("/")
    return [operation_map[label] for label in labels if label in operation_map]


def clean_topic_name(topic: str) -> str:
    topic = unescape(topic)
    topic = re.sub(r"style\.[A-Za-z_]+.*$", "", topic)
    topic = re.sub(r"ppt_[xy].*$", "", topic)
    topic = re.sub(r"202\d[/-]\d+[/-]?\d*.*$", "", topic)
    topic = re.sub(r"【(?:例|解)[^】]*】.*$", "", topic)
    topic = re.sub(r"图\s*\d+[-—]\d+.*$", "", topic)
    topic = re.sub(r"\s*新土力学.*$", "", topic)
    topic = re.sub(r"\s+", " ", topic).strip()
    topic = re.sub(r"^[•·\-\*\s]+", "", topic)
    topic = re.sub(r"\s*/\s*\d+\s*$", "", topic)
    topic = re.sub(r"\s+[A-Za-z]?\d+\s*$", "", topic)
    topic = re.sub(r"(?<=[\u4e00-\u9fff])[A-Za-z]?\d+\s*$", "", topic)
    topic = re.sub(r"[（(]\s*$", "", topic)
    topic = re.sub(r"[：:。.，,；;、]+$", "", topic).strip()
    return topic


def is_good_topic(topic: str) -> bool:
    topic = clean_topic_name(topic)
    if not topic or topic in GENERIC_STOP_TOPICS:
        return False
    if len(topic) < 3 or len(topic) > 42:
        return False
    if topic.isdigit():
        return False
    if re.fullmatch(r"[A-Za-z0-9\s/.-]+", topic):
        return False
    if re.search(r"[&%#@<>]", topic):
        return False
    if any(token in topic for token in ["style", "visibility", "ppt_", "【解】"]):
        return False
    if len(re.findall(r"[\u4e00-\u9fff]", topic)) < max(2, len(topic) // 2):
        return False
    return True


def context_around(text: str, needle: str, radius: int = 450) -> str:
    index = text.find(needle)
    if index < 0:
        return needle
    start = max(0, index - radius)
    end = min(len(text), index + len(needle) + radius)
    return text[start:end]


def extract_topic_hits(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    headings = re.findall(r"^(?:第[一二三四五六七八九十\d]+[章节]|#+)\s*([^\n]{2,40})", text, re.M)
    for heading in headings:
        cleaned = clean_topic_name(re.sub(r"[：:。.].*$", "", heading))
        if is_good_topic(cleaned):
            found.append((cleaned, context_around(text, heading)))
    inline_headings = re.findall(
        r"(?:第[一二三四五六七八九十\d]+[章节]\s*)([\u4e00-\u9fff][^。；;\n]{2,36})",
        text,
    )
    for heading in inline_headings:
        cleaned = clean_topic_name(re.sub(r"\s+\d+\s+.*$", "", heading))
        if is_good_topic(cleaned):
            found.append((cleaned, context_around(text, heading)))
    numbered_headings = re.findall(
        r"\b\d+(?:\.\d+){1,2}\s*([\u4e00-\u9fff][^。；;\n]{2,32})",
        text,
    )
    for heading in numbered_headings:
        cleaned = clean_topic_name(re.sub(r"\s+\d+(?:\.\d+).*?$", "", heading))
        if is_good_topic(cleaned):
            found.append((cleaned, context_around(text, heading)))
    section_headings = re.findall(
        r"(?:第一节|第二节|第三节|第四节|第五节|一、|二、|三、|四、|五、)\s*([\u4e00-\u9fff][^。；;\n]{2,30})",
        text,
    )
    for heading in section_headings:
        cleaned = clean_topic_name(re.sub(r"\s+\d+\s+.*$", "", heading))
        if is_good_topic(cleaned):
            found.append((cleaned, context_around(text, heading)))
    emphasized = re.findall(r"(?:重点|考点|掌握|理解|熟悉|要求|objective|key point)[：:\s]+([^\n。；;]{2,50})", text, re.I)
    for item in emphasized:
        cleaned = clean_topic_name(re.sub(r"[：:。.；;].*$", "", item))
        if is_good_topic(cleaned):
            found.append((cleaned, context_around(text, item)))
    return found


def extract_topics(text: str) -> list[str]:
    return [name for name, _context in extract_topic_hits(text)]


def extract_filename_topics(path: Path) -> list[tuple[str, str]]:
    stem = path.stem
    stem = re.sub(r"[-_－].*$", "", stem)
    stem = clean_topic_name(stem)
    candidates = [stem]
    without_chapter = clean_topic_name(re.sub(r"^第[一二三四五六七八九十\d]+[章节]\s*", "", stem))
    if without_chapter != stem:
        candidates.append(without_chapter)
    hits = []
    for candidate in candidates:
        if is_good_topic(candidate):
            hits.append((candidate, path.name))
    return hits


def default_operations_for_course(course: str, role: str, question_type: str) -> list[str]:
    if is_social_science_course(course):
        return SOCIAL_SCIENCE_OPS
    if role == "textbook" and question_type == "综合":
        return ["recall", "explain", "compare"]
    return []


def default_question_type_for_course(course: str, role: str, question_type: str) -> str:
    if is_social_science_course(course) and role == "textbook":
        return "记忆/解释/比较/论述"
    if question_type != "综合":
        return question_type
    if role == "textbook":
        return "记忆/解释/应用"
    return question_type
    return found


def build_inventory(materials: Path, course: str, exclude_dir: Path | None = None) -> dict[str, Any]:
    root = materials.resolve() if materials.is_dir() else materials.resolve().parent
    if materials.is_file():
        files = [materials.resolve()]
    else:
        files = [p.resolve() for p in materials.rglob("*") if p.is_file() and not p.name.startswith(".")]
    if exclude_dir:
        exclude_dir = exclude_dir.resolve()
        exclude_is_inside_materials = exclude_dir == root or root in exclude_dir.parents
        if exclude_is_inside_materials:
            files = [p for p in files if p != exclude_dir and exclude_dir not in p.parents]
    sources = []
    topic_sources: dict[str, list[str]] = defaultdict(list)
    topic_text: dict[str, str] = defaultdict(str)
    topic_roles: dict[str, list[str]] = defaultdict(list)

    for path in files:
        text, kind = read_material(path)
        role = infer_role(path, text)
        summary = text[:300].replace("\n", " ") if text else "需要手动摘录或暂不支持自动读取"
        rel = str(path.relative_to(root))
        sources.append({"path": rel, "type": kind, "role": role, "summary": summary})
        for topic, topic_context in extract_filename_topics(path):
            topic_sources[topic].append(rel)
            topic_text[topic] += "\n" + topic_context
            topic_roles[topic].append(role)
        if text:
            for topic, topic_context in extract_topic_hits(text):
                topic_sources[topic].append(rel)
                topic_text[topic] += "\n" + topic_context
                topic_roles[topic].append(role)

    topics = []
    for topic, refs in sorted(topic_sources.items(), key=lambda item: len(item[1]), reverse=True):
        role_counts = Counter(topic_roles[topic])
        main_role = role_counts.most_common(1)[0][0]
        question_type = default_question_type_for_course(
            course, main_role, detect_question_type(topic_text[topic])
        )
        operations = default_operations_for_course(course, main_role, question_type)
        if not operations:
            operations = detect_operations(topic_text[topic])
        topics.append(
            {
                "name": topic,
                "evidence": evidence_for(main_role, len(set(refs))),
                "question_type": question_type,
                "assessment_operations": operations,
                "source_refs": sorted(set(refs))[:8],
                "signals": [f"{role}:{count}" for role, count in role_counts.items()],
                "status": "unknown",
            }
        )

    return {"course": course, "sources": sources, "topics": topics}


def md_cell(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return re.sub(r"\s+", " ", text).strip()


def write_markdown(data: dict[str, Any], output: Path) -> None:
    lines = [f"# {data['course']} 材料初筛", "", "## 材料清单", ""]
    lines.extend(["| 文件 | 类型 | 角色 | 摘要 |", "| --- | --- | --- | --- |"])
    for source in data["sources"]:
        lines.append(
            f"| {md_cell(source['path'])} | {md_cell(source['type'])} | "
            f"{md_cell(source['role'])} | {md_cell(source['summary'])} |"
        )
    lines.extend(["", "## 知识点候选", ""])
    lines.extend(["| 知识点 | 证据 | 题型 | 考试操作 | 来源 |", "| --- | --- | --- | --- | --- |"])
    for topic in data["topics"]:
        refs = ", ".join(topic["source_refs"])
        operations = ", ".join(topic.get("assessment_operations", []))
        lines.append(
            f"| {md_cell(topic['name'])} | {md_cell(topic['evidence'])} | "
            f"{md_cell(topic['question_type'])} | {md_cell(operations)} | {md_cell(refs)} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract first-pass course material inventory.")
    parser.add_argument("materials", type=Path, help="Material file or directory")
    parser.add_argument("--course", default="未命名课程")
    parser.add_argument("--output-dir", type=Path, default=Path("extracted"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data = build_inventory(args.materials, args.course, args.output_dir)
    (args.output_dir / "material_inventory.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(data, args.output_dir / "material_inventory.md")
    print(f"Wrote {args.output_dir / 'material_inventory.json'}")
    print(f"Wrote {args.output_dir / 'material_inventory.md'}")


if __name__ == "__main__":
    main()
