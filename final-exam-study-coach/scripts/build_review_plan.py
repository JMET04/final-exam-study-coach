#!/usr/bin/env python3
"""Build a first-pass final-exam review plan from structured JSON.

This helper is intentionally deterministic. It ranks topics from exam evidence,
point value, weakness, repairability, and dependency value, then creates a
Chinese Markdown plan with study blocks, review triggers, and report-back
fields. Codex should still refine the output with the student's real materials.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EVIDENCE_WEIGHT = {
    "explicit": 4.0,
    "repeated": 3.0,
    "inferred": 2.0,
    "uncertain": 1.0,
}

STATUS_WEAKNESS = {
    "unknown": 3.0,
    "cannot_start": 4.0,
    "can_recognize": 3.0,
    "can_explain": 2.3,
    "can_solve_slowly": 2.0,
    "exam_ready": 0.2,
}

STATUS_ALIASES = {
    "": "unknown",
    "不知道": "unknown",
    "未知": "unknown",
    "零基础": "cannot_start",
    "不会开始": "cannot_start",
    "cannot start": "cannot_start",
    "cannot-start": "cannot_start",
    "can recognize": "can_recognize",
    "can-recognize": "can_recognize",
    "能认出": "can_recognize",
    "can explain": "can_explain",
    "can-explain": "can_explain",
    "能解释": "can_explain",
    "can solve slowly": "can_solve_slowly",
    "can-solve-slowly": "can_solve_slowly",
    "会但很慢": "can_solve_slowly",
    "exam ready": "exam_ready",
    "exam-ready": "exam_ready",
    "已掌握": "exam_ready",
}

COURSE_PROFILES = {
    "高等数学": {
        "aliases": ["高数", "微积分", "calculus"],
        "core": "用函数、极限、导数和积分描述变化，把复杂变化转成局部近似和累积计算。",
        "map": "函数/极限 -> 导数刻画局部变化 -> 积分刻画累积 -> 应用题拿分步骤",
        "exam": "判型、计算、应用解释、限时稳定",
    },
    "线性代数": {
        "aliases": ["线代", "linear algebra"],
        "core": "用向量和矩阵描述空间变换，核心是结构能不能被拆开、简化、求解。",
        "map": "矩阵运算 -> 方程组/秩 -> 向量空间 -> 特征值/对角化 -> 二次型",
        "exam": "矩阵计算、解空间结构、变换理解、规范步骤",
    },
    "概率论": {
        "aliases": ["概率统计", "数理统计", "probability", "statistics"],
        "core": "在不确定中建模、更新判断，并用分布和统计量做推断。",
        "map": "事件概率 -> 条件/独立 -> 随机变量/分布 -> 数字特征 -> 统计推断",
        "exam": "分布识别、条件更新、期望方差计算、统计结论解释",
    },
    "数据结构": {
        "aliases": ["算法", "data structure", "data structures"],
        "core": "为不同操作选择合适的数据组织方式，让程序在时间和空间上更高效。",
        "map": "复杂度 -> 线性结构 -> 树/图 -> 查找排序 -> 算法过程模拟",
        "exam": "过程模拟、复杂度分析、伪代码、边界条件",
    },
    "大学物理": {
        "aliases": ["物理", "physics"],
        "core": "用力、能量、动量、场和波等少数规律解释系统如何运动和变化。",
        "map": "建模对象 -> 受力/守恒/场方程 -> 求解 -> 物理意义检查",
        "exam": "受力图、方程建立、单位方向检查、极端情况判断",
    },
    "电路": {
        "aliases": ["电路分析", "circuit"],
        "core": "把电压、电流、元件关系和网络约束组合起来，分析能量和信号如何流动。",
        "map": "KCL/KVL -> 等效变换 -> 暂态/稳态 -> 频域与功率",
        "exam": "参考方向、列方程、初稳态判断、相量/时域区分",
    },
}

OPERATION_PROFILES = {
    "recall": {"label": "记忆/识别", "ability": "闭卷说出关键词、定义、清单或术语"},
    "explain": {"label": "解释/说明", "ability": "用自己的话解释概念、原因、机制和意义"},
    "compare": {"label": "比较/辨析", "ability": "区分相似概念，按维度比较并避免混淆"},
    "calculate": {"label": "计算/求解", "ability": "判型、代入、计算并检查单位/边界/结果"},
    "derive_prove": {"label": "推导/证明", "ability": "写出条件、目标、关键桥梁和每步依据"},
    "solve_apply": {"label": "应用/解决", "ability": "把方法迁移到新题、案例或情境"},
    "analyze_case": {"label": "案例/材料分析", "ability": "从材料抽取事实并映射到概念、框架或结论"},
    "design_create": {"label": "设计/建构", "ability": "在约束下提出方案、模型、结构或流程"},
    "critique_evaluate": {"label": "评价/批判", "ability": "给出判断标准、依据、优缺点和限制"},
    "translate_interpret": {"label": "翻译/解读", "ability": "把文本、图表、数据或结果转成可解释表达"},
    "implement_debug": {"label": "编程/调试", "ability": "写出过程、代码或伪代码并处理边界错误"},
    "diagnose_classify": {"label": "诊断/分类", "ability": "识别类型、病因、问题来源或归属类别"},
    "write_argue": {"label": "写作/论证", "ability": "组织观点、分论点、证据和结论"},
}

OPERATION_ALIASES = {
    "recall": ["记忆", "背诵", "默写", "列举", "选择", "填空", "recall", "identify"],
    "explain": ["解释", "说明", "定义", "原因", "机制", "define", "explain"],
    "compare": ["比较", "区分", "辨析", "分类", "compare", "contrast", "classify"],
    "calculate": ["计算", "求解", "求出", "calculate", "compute"],
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


def normalize_key(value: Any, default: str) -> str:
    text = str(value or "").strip()
    lowered = text.lower().replace("_", " ")
    canonical = STATUS_ALIASES.get(lowered)
    if canonical:
        return canonical
    slug = lowered.replace(" ", "_").replace("-", "_")
    return slug if slug else default


def normalize_evidence(value: Any) -> str:
    text = str(value or "inferred").strip().lower()
    aliases = {
        "官方": "explicit",
        "明确": "explicit",
        "老师说": "explicit",
        "重复": "repeated",
        "高频": "repeated",
        "推断": "inferred",
        "不确定": "uncertain",
    }
    return aliases.get(text, text if text in EVIDENCE_WEIGHT else "inferred")


def to_float(value: Any, default: float = 1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_operations(value: Any) -> list[str]:
    if isinstance(value, list):
        raw_text = " ".join(str(item) for item in value)
        explicit = [str(item).strip() for item in value if str(item).strip() in OPERATION_PROFILES]
    else:
        raw_text = str(value or "")
        explicit = [raw_text] if raw_text in OPERATION_PROFILES else []
    text = raw_text.lower()
    found = list(dict.fromkeys(explicit))
    for key, aliases in OPERATION_ALIASES.items():
        if any(alias.lower() in text for alias in aliases):
            found.append(key)
    return list(dict.fromkeys(found))


def operation_label(key: str) -> str:
    return OPERATION_PROFILES.get(key, {"label": key})["label"]


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
        evidence = EVIDENCE_WEIGHT.get(self.evidence, 2.0)
        weakness = STATUS_WEAKNESS.get(self.status, 2.0)
        return evidence * self.point_value * weakness * self.repairability * self.dependency_value

    @property
    def leverage(self) -> str:
        if self.priority >= 24:
            return "高"
        if self.priority >= 10:
            return "中"
        return "低"


def load_topics(data: dict[str, Any]) -> list[Topic]:
    topics: list[Topic] = []
    for raw in data.get("topics", []):
        topic = Topic(
            name=str(raw.get("name", "未命名知识点")).strip(),
            evidence=normalize_evidence(raw.get("evidence", "inferred")),
            point_value=to_float(raw.get("point_value", raw.get("weight", 1.0))),
            status=normalize_key(raw.get("status", "unknown"), "unknown"),
            repairability=to_float(raw.get("repairability", 1.0)),
            dependency_value=to_float(raw.get("dependency_value", 1.0)),
            question_type=str(raw.get("question_type", "综合")).strip(),
            assessment_operation="/".join(
                normalize_operations(
                    raw.get(
                        "assessment_operations",
                        raw.get("assessment_operation", raw.get("operation", raw.get("question_type", ""))),
                    )
                )
            ),
            next_action=str(raw.get("next_action", "主动回忆并做考试风格练习")).strip(),
            plain_explanation=str(
                raw.get("plain_explanation", raw.get("intuitive_explanation", ""))
            ).strip(),
            mnemonic=str(raw.get("mnemonic", "")).strip(),
            prerequisites=str(raw.get("prerequisites", raw.get("prerequisite", ""))).strip(),
            common_mistake=str(raw.get("common_mistake", raw.get("mistake", ""))).strip(),
            practice_prompt=str(raw.get("practice_prompt", raw.get("exercise", ""))).strip(),
            visualization=str(
                raw.get("visualization", raw.get("animation", raw.get("demo", "")))
            ).strip(),
        )
        topics.append(topic)
    return sorted(topics, key=lambda item: item.priority, reverse=True)


def course_profile(course: str) -> dict[str, str] | None:
    lowered = course.lower()
    for name, profile in COURSE_PROFILES.items():
        if name in course or any(alias in lowered for alias in profile["aliases"]):
            return profile
    return None


def infer_operations_from_topics(topics: list[Topic], data: dict[str, Any] | None = None) -> list[str]:
    data = data or {}
    candidates: list[str] = []
    for key in ("exam_operations", "assessment_operations", "operations"):
        candidates.extend(normalize_operations(data.get(key, "")))
    model = data.get("course_model", {})
    if isinstance(model, dict):
        candidates.extend(normalize_operations(model.get("exam_operations", "")))
    for topic in topics:
        candidates.extend(normalize_operations(f"{topic.assessment_operation} {topic.question_type} {topic.name}"))
    if not candidates:
        candidates = ["recall", "explain", "solve_apply"]
    return list(dict.fromkeys(candidates))[:5]


def generic_course_model(course: str, topics: list[Topic], data: dict[str, Any]) -> dict[str, str]:
    model = data.get("course_model", {})
    model = model if isinstance(model, dict) else {}
    profile = course_profile(course)
    operations = infer_operations_from_topics(topics, data)
    op_labels = "、".join(operation_label(operation) for operation in operations)
    op_abilities = "；".join(
        OPERATION_PROFILES.get(operation, {"ability": operation})["ability"] for operation in operations
    )
    topic_names = "、".join(topic.name for topic in topics[:5]) if topics else "核心概念、方法和题型"
    if model.get("core_problem"):
        core = str(model["core_problem"])
    elif data.get("course_core") or data.get("core_idea") or data.get("big_picture"):
        core = str(data.get("course_core", data.get("core_idea", data.get("big_picture", ""))))
    elif profile:
        core = profile["core"]
    else:
        core = f"围绕 `{topic_names}` 建立能解释问题、完成考试操作、拿到评分点的知识工具箱。"
    if model.get("main_map"):
        main_map = str(model["main_map"])
    elif profile:
        main_map = f"{profile['map']} -> {op_labels} -> 评分点"
    else:
        main_map = f"材料证据 -> 知识单元（{topic_names}） -> 考试操作（{op_labels}） -> 评分点 -> 限时输出"
    if model.get("exam_abilities"):
        exam = str(model["exam_abilities"])
    elif profile:
        exam = f"{profile['exam']}；同时按通用操作训练：{op_abilities}"
    else:
        exam = op_abilities
    return {
        "core": core,
        "main_map": main_map,
        "exam": exam,
        "operations": op_labels,
        "source": "用户提供" if model else ("课程专项示例 + 通用模型" if profile else "通用模型推断"),
    }


def fallback_core_idea(course: str, topics: list[Topic]) -> str:
    profile = course_profile(course)
    if profile:
        return profile["core"]
    topic_names = "、".join(topic.name for topic in topics[:4]) if topics else "核心概念和典型题型"
    return f"这门课可以先理解成：围绕 `{topic_names}` 建立一套解释问题、选择方法、稳定得分的工具箱。"


def fallback_main_map(course: str) -> str:
    profile = course_profile(course)
    if profile:
        return profile["map"]
    return "核心问题 -> 关键工具 -> 典型题型 -> 得分动作"


def fallback_exam_abilities(course: str) -> str:
    profile = course_profile(course)
    if profile:
        return profile["exam"]
    return "记忆、理解、应用、限时稳定"


def default_plain_explanation(topic: Topic) -> str:
    return f"把 `{topic.name}` 当成一种解题工具：先识别它适用的题型，再按固定步骤拿到可验证的分。"


def default_mnemonic(topic: Topic) -> str:
    text = f"{topic.question_type} {topic.assessment_operation}"
    if any(key in text for key in ["证明", "推导", "derive_prove"]):
        return "先写条件，再写要证，最后补关键桥梁。"
    if any(key in text for key in ["计算", "calculate"]):
        return "先判型，再套步骤，最后检查单位/符号/边界。"
    if any(key in text for key in ["案例", "analyze_case", "diagnose_classify"]):
        return "事实先分层，概念再匹配，结论要回扣材料。"
    if any(key in text for key in ["比较", "compare"]):
        return "先定维度，再列异同，最后写适用边界。"
    if any(key in text for key in ["设计", "design_create"]):
        return "目标、约束、方案、理由、限制。"
    if any(key in text for key in ["论述", "简答", "write_argue", "explain"]):
        return "概念一句话，原因分层说，例子或影响收尾。"
    return "是什么、为什么、怎么用、易错点。"


def default_practice(topic: Topic) -> str:
    text = f"{topic.question_type} {topic.assessment_operation}"
    if any(key in text for key in ["编程", "implement_debug"]):
        return f"不用看答案，写出 `{topic.name}` 的核心步骤或伪代码，并说明复杂度。"
    if any(key in text for key in ["证明", "推导", "derive_prove"]):
        return f"闭卷写出一道 `{topic.name}` 相关证明题的条件、目标和关键中间结论。"
    if any(key in text for key in ["案例", "analyze_case", "diagnose_classify"]):
        return f"给一个 `{topic.name}` 的案例，先划出事实，再匹配概念，最后写结论和依据。"
    if any(key in text for key in ["比较", "compare"]):
        return f"做一张 `{topic.name}` 对比表，至少列 3 个维度和 1 个易混点。"
    if any(key in text for key in ["设计", "design_create"]):
        return f"围绕 `{topic.name}` 做一个最小方案，写清目标、约束、步骤和评价标准。"
    if any(key in text for key in ["论述", "简答", "write_argue", "explain"]):
        return f"用 150 字解释 `{topic.name}`，包含定义、意义和一个常见误区。"
    return f"做 1 道 `{topic.name}` 的典型题，先写思路再计算。"


def default_visualization(topic: Topic, course: str) -> str:
    text = f"{course} {topic.name} {topic.question_type}".lower()
    if any(key in text for key in ["矩阵", "向量", "特征", "线性代数", "空间"]):
        return "建议用 SVG/Canvas 动画演示向量或网格如何被变换，并暂停观察方向、长度或面积的变化。"
    if any(key in text for key in ["极限", "导数", "积分", "函数", "微分"]):
        return "建议用曲线动画演示点、切线或面积累积的变化，让学生预测下一帧。"
    if any(key in text for key in ["概率", "贝叶斯", "分布", "统计", "随机"]):
        return "建议用样本空间/概率质量流动动画演示条件筛选和概率重新分配。"
    if any(key in text for key in ["算法", "排序", "搜索", "图", "树", "链表", "栈", "队列", "动态规划", "数据结构"]):
        return "建议用分步动画演示状态变化、指针/队列/栈/表格如何更新。"
    if any(key in text for key in ["力", "电路", "电流", "电压", "控制", "热", "流体", "振动", "物理"]):
        return "建议用矢量或系统状态动画演示方向、大小、路径或反馈如何变化。"
    if any(key in text for key in ["化学", "反应", "生物", "细胞", "材料"]):
        return "建议用流程/状态动画演示微观过程或结构变化。"
    return "可先用静态图或流程图；只有学生对过程/空间/步骤仍混乱时再做动画。"


def load_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = []
    for index, block in enumerate(data.get("study_blocks", []), start=1):
        normalized.append(
            {
                "label": str(block.get("label", f"学习块 {index}")).strip(),
                "minutes": max(10, int(to_float(block.get("minutes", 60), 60))),
                "energy": str(block.get("energy", "medium")).strip(),
            }
        )
    return normalized


def core_block_count(blocks: list[dict[str, Any]], buffer_ratio: float = 0.25) -> int:
    if len(blocks) <= 1:
        return len(blocks)
    ratio = min(max(buffer_ratio, 0.15), 0.35)
    core = int(len(blocks) * (1 - ratio))
    return max(1, min(len(blocks) - 1, core))


def time_mode(total_minutes: int) -> str:
    if total_minutes < 6 * 60:
        return "可用时间不足6小时：救急"
    if total_minutes <= 18 * 60:
        return "可用时间6-18小时：冲刺"
    if total_minutes <= 42 * 60:
        return "可用时间18-42小时：系统提分"
    return "可用时间42小时以上：长期节奏"


def block_task(topic: Topic, minutes: int, index: int, total_blocks: int) -> str:
    if index == total_blocks and total_blocks >= 3 and minutes >= 45:
        return "错题回炉 + 快速回忆：复查高优先级错因，闭卷写出公式/框架/步骤，再做短限时测。"
    if minutes >= 90 and index >= max(2, total_blocks // 2):
        return f"限时训练 `{topic.name}`：先复现模板，再做一组混合题，最后估分并写错因。"
    if minutes <= 35:
        return f"快速修补 `{topic.name}`：闭卷回忆关键点，订正 2-3 个关键错误。"
    if minutes <= 75:
        return f"攻克 `{topic.name}`：费曼式讲一遍 -> 例题/模板复现 -> 考试题型练习 -> 错因记录。"
    return f"深度学习 `{topic.name}`：先写通俗理解和助记，必要时看/做演示动画，再做限时题、安排间隔复习。"


def review_trigger(index: int) -> str:
    if index == 1:
        return "学完后10-20分钟闭卷复测，下一学习块开始前再用5分钟复测"
    if index <= 3:
        return "1天后复测；时间紧就压缩到睡前或明早复测"
    return "3天/7天/考前总复盘时复测"


def build_markdown(data: dict[str, Any]) -> str:
    if "topics" not in data and "material_inventory" in data:
        data["topics"] = data["material_inventory"].get("topics", [])
    topics = load_topics(data)
    blocks = load_blocks(data)
    total_minutes = sum(block["minutes"] for block in blocks)
    buffer_ratio = to_float(data.get("buffer_ratio", 0.25), 0.25)
    core_count = core_block_count(blocks, buffer_ratio)
    core_minutes = sum(block["minutes"] for block in blocks[:core_count])
    buffer_minutes = max(0, total_minutes - core_minutes)
    course = str(data.get("course", "未命名课程"))
    exam_date = str(data.get("exam_date", "未知"))
    target = str(data.get("target", "当前时间内尽量提分"))
    current_level = str(data.get("current_level", "未知"))
    course_model = generic_course_model(course, topics, data)
    mode = time_mode(total_minutes)

    lines = [
        f"# {course} 期末复习初版计划",
        "",
        "## 局势快照",
        "",
        f"- 考试时间：{exam_date}",
        f"- 目标：{target}",
        f"- 当前水平：{current_level}",
        f"- 可用学习时间：{total_minutes} 分钟，{len(blocks)} 个学习块",
        f"- 核心完成区：前 {core_count} 个学习块，约 {core_minutes} 分钟",
        f"- 缓冲/复习区：后 {max(0, len(blocks) - core_count)} 个学习块，约 {buffer_minutes} 分钟",
        f"- 时间模式：{mode}",
        "- 说明：这是脚本初排，默认学生会拖延，所以不把全部时间排成核心新任务。",
        "",
        "## 通用课程模型 / 课程大局观",
        "",
        f"- 模型来源：{course_model['source']}",
        f"- 一句话核心：{course_model['core']}",
        f"- 考试操作：{course_model['operations']}",
        f"- 主线地图：{course_model['main_map']}。",
        f"- 考试真正考你：{course_model['exam']}。",
        "- 学习顺序：先能用自己的话解释，再做题验证，最后按间隔复习回炉。",
        "",
        "## 提分地图",
        "",
        "| 排名 | 知识点 | 证据 | 题型 | 考试操作 | 状态 | 优先级 | 杠杆 | 下一步 |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]

    if topics:
        for rank, topic in enumerate(topics, start=1):
            lines.append(
                f"| {rank} | {topic.name} | {topic.evidence} | {topic.question_type} | "
                f"{topic.assessment_operation or '待诊断'} | "
                f"{topic.status} | {topic.priority:.1f} | {topic.leverage} | {topic.next_action} |"
            )
    else:
        lines.append("| - | 暂无 | - | - | - | - | - | - | 先从材料中抽取知识点 |")

    lines.extend(
        [
            "",
            "## 知识点理解卡",
            "",
            "| 知识点 | 通俗理解 | 助记 | 前置关联 | 常见误区 | 可视化/动画 | 练习 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    if topics:
        for topic in topics:
            lines.append(
                f"| {topic.name} | {topic.plain_explanation or default_plain_explanation(topic)} | "
                f"{topic.mnemonic or default_mnemonic(topic)} | {topic.prerequisites or '先按题目需要最小补齐'} | "
                f"{topic.common_mistake or '只背定义，不会判断什么时候用'} | "
                f"{topic.visualization or default_visualization(topic, course)} | "
                f"{topic.practice_prompt or default_practice(topic)} |"
            )
    else:
        lines.append("| 暂无 | 先从材料中提取 | - | - | - | - |")

    lines.extend(["", "## 学习块安排", ""])

    if not blocks:
        lines.append("还没有提供学习块。请补充每天可用时间，例如：今晚90分钟，明天上午120分钟。")
    elif not topics:
        lines.append("还没有提供知识点。先建立材料目录和主题清单，再排学习块。")
    else:
        actionable_topics = [topic for topic in topics if topic.status != "exam_ready"] or topics
        for index, block in enumerate(blocks, start=1):
            topic = actionable_topics[(index - 1) % len(actionable_topics)]
            phase = "核心完成区" if index <= core_count else "缓冲/复习区"
            if index > core_count:
                task = "缓冲补救/二轮复习：如果前面没完成，用本块补高证据高分内容；如果已完成，做错题回炉、混合题或短模拟。"
                topic_name = "缓冲与回炉"
                visualization = "只在动态过程仍混乱时使用动画；否则优先错题和限时练习。"
            else:
                task = block_task(topic, block["minutes"], index, core_count)
                topic_name = topic.name
                visualization = topic.visualization or default_visualization(topic, course)
            lines.extend(
                [
                    f"### {block['label']}（{block['minutes']} 分钟，能量：{block['energy']}，{phase}）",
                    "",
                    f"- 重点：{topic_name}",
                    f"- 任务：{task}",
                    f"- 可视化：{visualization}",
                    "- 产出：通俗解释/助记卡/动画观察结论/题目/回忆清单/错题日志/估分中的至少一种。",
                    f"- 复习触发：{review_trigger(index)}。",
                    "- 回来报告：完成内容、正确率或估分、错因、信心 1-5、下一段可用时间。",
                    "",
                ]
            )

    lines.extend(
        [
            "## 降级规则",
            "",
            "- 如果时间不够，保留 `explicit` 和 `repeated` 且优先级高的内容。",
            "- 如果学生偷懒，优先动用缓冲/复习区；仍不够就砍低证据低分值内容。",
            "- 如果按时完成，缓冲/复习区改做错题回炉、间隔复习、混合模拟和高分题。",
            "- 如果卡住超过 45 分钟，改用例题复现和部分分步骤，不继续硬啃。",
            "- 如果疲劳明显，改成错题回炉、公式回忆或睡眠。",
            "",
            "## 上下文检查点",
            "",
            "- 持续带学时，把本计划的核心完成区、缓冲区、已完成项、未完成项和下一步写入状态文件/检查点。",
            "- 如果对话上下文被压缩，先读检查点和状态文件，再继续下一学习块。",
            "",
            "## 不会时的补救流程",
            "",
            "1. 先判断卡点：读不懂题、不会第一步、推不下去、算错、换题不会。",
            "2. 找相关知识点：只补最小必要前置，不把整章重讲。",
            "3. 用费曼法让学生重新解释。",
            "4. 再出一道相近但不完全一样的新题验证。",
            "5. 如果是理工科动态过程，要求学生预测动画下一帧或改条件后的变化。",
            "",
            "## 第一学习块",
            "",
        ]
    )

    if blocks and topics:
        first_topic = ([topic for topic in topics if topic.status != "exam_ready"] or topics)[0]
        first_block = blocks[0]
        lines.extend(
            [
                f"现在先做 `{first_topic.name}`，用 {first_block['minutes']} 分钟。",
                f"先用自己的话写一句通俗理解：{first_topic.plain_explanation or default_plain_explanation(first_topic)}",
                f"可视化观察：{first_topic.visualization or default_visualization(first_topic, course)}",
                f"再按这个动作执行：{block_task(first_topic, first_block['minutes'], 1, len(blocks))}",
                f"最后做这道检验题：{first_topic.practice_prompt or default_practice(first_topic)}",
                "结束后把完成证据发回来，我再重排下一块。",
            ]
        )
    else:
        lines.append("先补齐材料清单或可用时间，再生成第一学习块。")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a first-pass final-exam review plan.")
    parser.add_argument("input", type=Path, help="JSON file with course, topics, and study_blocks")
    parser.add_argument("--output", "-o", type=Path, help="Write Markdown plan to this path")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    markdown = build_markdown(data)
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")


if __name__ == "__main__":
    main()
