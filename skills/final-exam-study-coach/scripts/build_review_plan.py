#!/usr/bin/env python3
"""Build a deterministic first-pass final-exam review plan."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EVIDENCE_WEIGHT = {"explicit": 4.0, "repeated": 3.0, "inferred": 2.0, "uncertain": 1.0}
STATUS_WEAKNESS = {
    "unknown": 3.0,
    "cannot_start": 4.0,
    "can_recognize": 3.0,
    "can_explain": 2.3,
    "can_solve_slowly": 2.0,
    "exam_ready": 0.2,
}

OPERATION_PROFILES = {
    "recall": ("记忆/识别", "闭卷说出关键词、定义、清单或术语"),
    "explain": ("解释/说明", "用自己的话解释概念、原因、机制和意义"),
    "compare": ("比较/辨析", "区分相似概念，按维度比较并避免混淆"),
    "calculate": ("计算/求解", "判型、代入、计算并检查单位、符号和边界"),
    "derive_prove": ("推导/证明", "写出条件、目标、关键桥梁和每步依据"),
    "solve_apply": ("应用/解决", "把方法迁移到新题、案例或情境"),
    "analyze_case": ("案例/材料分析", "从材料抽取事实并映射到概念、框架或结论"),
    "design_create": ("设计/构建", "在约束下提出方案、模型、结构或流程"),
    "critique_evaluate": ("评价/批判", "给出判断标准、依据、优缺点和限制"),
    "translate_interpret": ("翻译/解读", "把文本、图表、数据或结果转成可解释表达"),
    "implement_debug": ("编程/调试", "写出过程、代码或伪代码并处理边界错误"),
    "diagnose_classify": ("诊断/分类", "识别类型、病因、问题来源或归属类别"),
    "write_argue": ("写作/论证", "组织观点、分论点、证据和结论"),
}

OPERATION_ALIASES = {
    "recall": ["记忆", "背诵", "默写", "列举", "选择", "填空", "recall", "identify"],
    "explain": ["解释", "说明", "定义", "原因", "机制", "define", "explain"],
    "compare": ["比较", "区分", "辨析", "分类", "compare", "contrast"],
    "calculate": ["计算", "求解", "求出", "代入", "calculate", "compute"],
    "derive_prove": ["证明", "推导", "prove", "derive"],
    "solve_apply": ["应用", "运用", "解决", "apply", "solve"],
    "analyze_case": ["案例", "材料分析", "情境", "case", "scenario", "analyze"],
    "design_create": ["设计", "方案", "建模", "绘制", "design", "model"],
    "critique_evaluate": ["评价", "评析", "批判", "优缺点", "evaluate", "critique"],
    "translate_interpret": ["翻译", "解读", "读图", "读表", "interpret", "translate"],
    "implement_debug": ["编程", "算法", "代码", "实现", "调试", "debug", "program"],
    "diagnose_classify": ["诊断", "归类", "识别类型", "diagnose"],
    "write_argue": ["论述", "作文", "写作", "论证", "argue", "essay", "discuss"],
}

COURSE_PROFILES = {
    "土力学": {
        "aliases": ["soil"],
        "core": "研究土体三相组成、渗流、应力、变形和强度如何影响工程稳定与沉降。",
        "map": "三相组成 -> 渗流 -> 有效应力 -> 固结沉降 -> 抗剪强度 -> 地基与边坡问题",
        "exam": "概念辨析、公式计算、步骤推导、试验方法和工程情境判断。",
    },
    "毛泽东思想": {
        "aliases": ["毛概", "毛思"],
        "core": "理解马克思主义中国化第一次历史性飞跃及其理论成果、历史条件和实践意义。",
        "map": "历史背景 -> 理论形成 -> 革命道路 -> 社会主义改造 -> 意义评价 -> 论述表达",
        "exam": "关键词回忆、概念解释、比较辨析、材料分析和规范论述。",
    },
    "中国近现代史纲要": {
        "aliases": ["近代史", "史纲"],
        "core": "把近现代中国历史理解为民族危机、道路选择、社会革命和国家建设的因果链。",
        "map": "时间线 -> 事件 -> 原因 -> 影响 -> 评价 -> 材料/小论文表达",
        "exam": "客观题识别、时间因果、材料分析和观点论证。",
    },
    "工程经济": {
        "aliases": ["工程经济与管理"],
        "core": "用资金时间价值、现金流、评价指标和项目管理方法判断工程方案是否经济可行。",
        "map": "现金流 -> 资金时间价值 -> 评价指标 -> 财务评价 -> 投资控制/进度/质量管理",
        "exam": "公式计算、指标比较、方案评价和项目管理应用。",
    },
}


@dataclass
class Topic:
    name: str
    evidence: str = "inferred"
    point_value: float = 1.0
    status: str = "unknown"
    repairability: float = 1.0
    dependency_value: float = 1.0
    question_type: str = "综合"
    assessment_operation: str = ""
    next_action: str = "主动回忆并做考试风格练习"
    plain_explanation: str = ""
    mnemonic: str = ""
    prerequisites: str = ""
    common_mistake: str = ""
    practice_prompt: str = ""
    visualization: str = ""

    @property
    def priority(self) -> float:
        return (
            EVIDENCE_WEIGHT.get(self.evidence, 2.0)
            * self.point_value
            * STATUS_WEAKNESS.get(self.status, 2.0)
            * self.repairability
            * self.dependency_value
        )

    @property
    def leverage(self) -> str:
        if self.priority >= 24:
            return "高"
        if self.priority >= 10:
            return "中"
        return "低"


def to_float(value: Any, default: float = 1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_evidence(value: Any) -> str:
    text = str(value or "inferred").strip().lower()
    aliases = {"明确": "explicit", "官方": "explicit", "老师说": "explicit", "重复": "repeated", "高频": "repeated", "推断": "inferred", "不确定": "uncertain"}
    return aliases.get(text, text if text in EVIDENCE_WEIGHT else "inferred")


def normalize_status(value: Any) -> str:
    text = str(value or "unknown").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {"未学": "unknown", "不会": "cannot_start", "能认出": "can_recognize", "能解释": "can_explain", "会但慢": "can_solve_slowly", "已掌握": "exam_ready"}
    return aliases.get(str(value).strip(), text if text in STATUS_WEAKNESS else "unknown")


def normalize_operations(value: Any) -> list[str]:
    raw = " ".join(map(str, value)) if isinstance(value, list) else str(value or "")
    found: list[str] = []
    for key, aliases in OPERATION_ALIASES.items():
        if key in raw or any(alias.lower() in raw.lower() for alias in aliases):
            found.append(key)
    return list(dict.fromkeys(found)) or ["recall", "explain", "solve_apply"]


def operation_label(key: str) -> str:
    return OPERATION_PROFILES.get(key, (key, key))[0]


def operation_ability(key: str) -> str:
    return OPERATION_PROFILES.get(key, (key, key))[1]


def load_topics(data: dict[str, Any]) -> list[Topic]:
    raw_topics = data.get("topics") or data.get("material_inventory", {}).get("topics", [])
    topics = []
    for raw in raw_topics:
        if isinstance(raw, str):
            raw = {"name": raw}
        ops = raw.get("assessment_operations", raw.get("assessment_operation", raw.get("operation", raw.get("question_type", ""))))
        topics.append(
            Topic(
                name=str(raw.get("name", "未命名知识点")).strip(),
                evidence=normalize_evidence(raw.get("evidence", "inferred")),
                point_value=to_float(raw.get("point_value", raw.get("weight", 1.0))),
                status=normalize_status(raw.get("status", "unknown")),
                repairability=to_float(raw.get("repairability", 1.0)),
                dependency_value=to_float(raw.get("dependency_value", 1.0)),
                question_type=str(raw.get("question_type", "综合")).strip(),
                assessment_operation="/".join(normalize_operations(ops)),
                next_action=str(raw.get("next_action", "主动回忆并做考试风格练习")).strip(),
                plain_explanation=str(raw.get("plain_explanation", "")).strip(),
                mnemonic=str(raw.get("mnemonic", "")).strip(),
                prerequisites=str(raw.get("prerequisites", "")).strip(),
                common_mistake=str(raw.get("common_mistake", "")).strip(),
                practice_prompt=str(raw.get("practice_prompt", "")).strip(),
                visualization=str(raw.get("visualization", "")).strip(),
            )
        )
    return sorted(topics, key=lambda item: item.priority, reverse=True)


def course_profile(course: str) -> dict[str, str] | None:
    lowered = course.lower()
    for name, profile in COURSE_PROFILES.items():
        if name in course or any(alias.lower() in lowered for alias in profile["aliases"]):
            return profile
    return None


def infer_operations_from_topics(topics: list[Topic], data: dict[str, Any] | None = None) -> list[str]:
    data = data or {}
    found: list[str] = []
    for key in ("exam_operations", "assessment_operations", "operations"):
        found.extend(normalize_operations(data.get(key, "")))
    for topic in topics:
        found.extend(normalize_operations(f"{topic.assessment_operation} {topic.question_type} {topic.name}"))
    return list(dict.fromkeys(found))[:5] or ["recall", "explain", "solve_apply"]


def generic_course_model(course: str, topics: list[Topic], data: dict[str, Any]) -> dict[str, str]:
    explicit = data.get("course_model") if isinstance(data.get("course_model"), dict) else {}
    profile = course_profile(course)
    operations = infer_operations_from_topics(topics, data)
    topic_names = "、".join(topic.name for topic in topics[:5]) or "核心概念、方法和题型"
    return {
        "core": str(explicit.get("core_problem") or data.get("course_core") or (profile or {}).get("core") or f"围绕 {topic_names} 建立解释问题、完成考试操作和拿到步骤分的工具箱。"),
        "main_map": str(explicit.get("main_map") or (profile or {}).get("map") or f"材料证据 -> 知识单元({topic_names}) -> 考试操作 -> 评分点 -> 限时输出"),
        "exam": str(explicit.get("exam_abilities") or (profile or {}).get("exam") or "记忆、理解、应用、限时稳定和规范表达。"),
        "operations": "、".join(operation_label(op) for op in operations),
        "source": "用户提供" if explicit else ("课程专项示例 + 通用模型" if profile else "通用模型推断"),
    }


def load_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = []
    for index, block in enumerate(data.get("study_blocks", []), start=1):
        blocks.append({"label": str(block.get("label", f"学习块{index}")), "minutes": max(10, int(to_float(block.get("minutes", 60), 60))), "energy": str(block.get("energy", "medium"))})
    return blocks


def core_block_count(blocks: list[dict[str, Any]], buffer_ratio: float = 0.25) -> int:
    if len(blocks) <= 1:
        return len(blocks)
    return max(1, min(len(blocks) - 1, int(len(blocks) * (1 - min(max(buffer_ratio, 0.15), 0.35)))))


def default_visualization(topic: Topic, course: str) -> str:
    text = f"{course} {topic.name} {topic.question_type}"
    if any(key in text for key in ["土力学", "渗流", "应力", "沉降", "强度", "工程", "数学", "物理", "算法", "电路"]):
        return "适合用动画或交互图展示动态关系；看完后必须接一道考试题验证。"
    return "不强行动画化；用主线图、时间线、比较表或主动回忆更合适。"


def default_mnemonic(topic: Topic) -> str:
    text = f"{topic.question_type} {topic.assessment_operation}"
    if "calculate" in text or "计算" in text:
        return "先判型，再列式，最后检查单位、符号和边界。"
    if "compare" in text or "比较" in text:
        return "先定维度，再列异同，最后写适用边界。"
    if "write_argue" in text or "论述" in text:
        return "观点先行，分层展开，材料扣回结论。"
    return "是什么、为什么、怎么用、易错点。"


def default_practice(topic: Topic) -> str:
    if "calculate" in topic.assessment_operation:
        return f"完成1道 {topic.name} 计算题，保留步骤分并检查结果。"
    if "write_argue" in topic.assessment_operation:
        return f"用150-300字回答 {topic.name}，包含观点、依据和结论。"
    return f"闭卷解释 {topic.name}，再做1道同类题。"


def block_task(topic: Topic, minutes: int) -> str:
    if minutes <= 35:
        return f"快速修补 {topic.name}：闭卷回忆关键点，订正2-3个易错点。"
    if minutes <= 75:
        return f"攻克 {topic.name}：费曼讲一遍，复现例题或模板，再写错因。"
    return f"深度学习 {topic.name}：理解卡、例题、限时练习和复测安排一起做。"


def build_markdown(data: dict[str, Any]) -> str:
    topics = load_topics(data)
    blocks = load_blocks(data)
    course = str(data.get("course", "未命名课程"))
    model = generic_course_model(course, topics, data)
    total_minutes = sum(block["minutes"] for block in blocks)
    core_count = core_block_count(blocks, to_float(data.get("buffer_ratio", 0.25), 0.25))
    core_minutes = sum(block["minutes"] for block in blocks[:core_count])
    buffer_minutes = total_minutes - core_minutes

    lines = [
        f"# {course} 期末复习初版计划",
        "",
        "## 局势快照",
        "",
        f"- 考试时间：{data.get('exam_date', '未知')}",
        f"- 目标：{data.get('target', '当前时间内尽量提分')}",
        f"- 当前水平：{data.get('current_level', '未知')}",
        f"- 可用学习时间：{total_minutes} 分钟，{len(blocks)} 个学习块",
        f"- 核心完成区：前 {core_count} 个学习块，约 {core_minutes} 分钟",
        f"- 缓冲/复习区：约 {buffer_minutes} 分钟",
        "",
        "## 课程大局观",
        "",
        f"- 模型来源：{model['source']}",
        f"- 一句话核心：{model['core']}",
        f"- 考试操作：{model['operations']}",
        f"- 主线地图：{model['main_map']}",
        f"- 考试真正考：{model['exam']}",
        "",
        "## 提分地图",
        "",
        "| 排名 | 知识点 | 证据 | 题型 | 考试操作 | 状态 | 优先级 | 杠杆 | 下一步 |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for rank, topic in enumerate(topics, start=1):
        lines.append(f"| {rank} | {topic.name} | {topic.evidence} | {topic.question_type} | {topic.assessment_operation} | {topic.status} | {topic.priority:.1f} | {topic.leverage} | {topic.next_action} |")

    lines.extend(["", "## 知识点理解卡", "", "| 知识点 | 通俗理解 | 助记 | 前置关联 | 常见误区 | 可视化/动画 | 练习 |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for topic in topics:
        lines.append(f"| {topic.name} | {topic.plain_explanation or f'把 {topic.name} 当成一种解题工具：先识别适用题型，再按步骤拿分。'} | {topic.mnemonic or default_mnemonic(topic)} | {topic.prerequisites or '按题目需要最小补齐'} | {topic.common_mistake or '只背定义，不会判断何时使用'} | {topic.visualization or default_visualization(topic, course)} | {topic.practice_prompt or default_practice(topic)} |")

    lines.extend(["", "## 学习块安排", ""])
    if not blocks:
        lines.append("还没有提供学习块。请补充每日可用时间。")
    elif not topics:
        lines.append("还没有提供知识点。请先建立材料清单。")
    else:
        active = [topic for topic in topics if topic.status != "exam_ready"] or topics
        for index, block in enumerate(blocks, start=1):
            topic = active[(index - 1) % len(active)]
            phase = "核心完成区" if index <= core_count else "缓冲/复习区"
            task = block_task(topic, block["minutes"]) if index <= core_count else "补救未完成任务；若已完成，则做错题回炉、混合模拟或高分题。"
            lines.extend([
                f"### {block['label']}（{block['minutes']} 分钟，{phase}）",
                "",
                f"- 重点：{topic.name if index <= core_count else '缓冲与回炉'}",
                f"- 任务：{task}",
                f"- 产出：理解卡、题目、回忆清单、错题日志或限时分数至少一种。",
                "- 回报格式：完成内容、正确率/估分、错因、信心1-5、下一段可用时间。",
                "",
            ])

    lines.extend([
        "## 降级规则",
        "",
        "- 时间不够时，保留 explicit/repeated 且优先级高的内容。",
        "- 学生拖延时，优先动用缓冲区；仍不够就砍低证据低分值内容。",
        "- 按时完成时，缓冲区改做错题回炉、间隔复习、混合模拟和高分题。",
        "",
        "## 第一个学习块",
        "",
    ])
    if blocks and topics:
        first = ([topic for topic in topics if topic.status != "exam_ready"] or topics)[0]
        lines.extend([f"现在先做 **{first.name}**，用 {blocks[0]['minutes']} 分钟。", f"先闭卷写一句通俗理解，再执行：{block_task(first, blocks[0]['minutes'])}", f"最后做：{first.practice_prompt or default_practice(first)}"])
    else:
        lines.append("先补齐材料清单或可用时间，再生成第一个学习块。")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a first-pass final-exam review plan.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", "-o", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    markdown = build_markdown(data)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")


if __name__ == "__main__":
    main()
