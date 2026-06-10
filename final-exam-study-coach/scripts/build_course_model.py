#!/usr/bin/env python3
"""Infer a universal course model from materials inventory or plan JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_review_plan import generic_course_model, infer_operations_from_topics, load_topics


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    if "topics" in data:
        return data
    if "material_inventory" in data and isinstance(data["material_inventory"], dict):
        merged = dict(data)
        merged["topics"] = data["material_inventory"].get("topics", [])
        return merged
    if "sources" in data and "topics" in data:
        return data
    return data


def knowledge_unit_type(name: str, question_type: str) -> str:
    text = f"{name} {question_type}".lower()
    checks = [
        ("术语/概念", ["概念", "定义", "术语", "原理", "theory", "concept"]),
        ("规则/公式", ["公式", "定理", "规则", "law", "formula"]),
        ("方法/程序", ["方法", "步骤", "流程", "算法", "procedure", "method"]),
        ("案例/材料", ["案例", "材料", "情境", "case"]),
        ("论证框架", ["论述", "证明", "推导", "argument", "prove"]),
        ("文本/作品", ["文本", "作品", "翻译", "阅读", "text"]),
        ("技能表现", ["设计", "实验", "操作", "编程", "design", "lab", "code"]),
    ]
    for label, words in checks:
        if any(word in text for word in words):
            return label
    return "知识点/主题"


def build_model(data: dict[str, Any]) -> dict[str, Any]:
    data = normalize_input(data)
    course = str(data.get("course", "未命名课程"))
    topics = load_topics(data)
    model = generic_course_model(course, topics, data)
    operations = infer_operations_from_topics(topics, data)
    units = [
        {
            "name": topic.name,
            "unit_type": knowledge_unit_type(topic.name, topic.question_type),
            "evidence": topic.evidence,
            "question_type": topic.question_type,
            "assessment_operation": topic.assessment_operation,
            "status": topic.status,
        }
        for topic in topics
    ]
    return {
        "course": course,
        "course_model": {
            "core_problem": model["core"],
            "main_map": model["main_map"],
            "exam_abilities": model["exam"],
            "exam_operations": operations,
            "model_source": model["source"],
            "knowledge_units": units,
            "representation_modes": [
                "文字框架",
                "对比表",
                "流程图",
                "公式/步骤卡",
                "案例链",
                "限时练习记录",
            ],
            "scoring_modes": [
                "关键词",
                "步骤分",
                "依据/证据",
                "结论回扣",
                "边界/单位/格式检查",
            ],
            "practice_ladder": ["identify", "basic", "exam", "transfer"],
            "remediation_rules": [
                "读不懂题先补术语和已知/所求",
                "不会第一步先补触发条件",
                "推不下去先补步骤链或论证桥梁",
                "换题不会先做变式并比较差异",
            ],
        },
    }


def write_markdown(model_data: dict[str, Any], output: Path) -> None:
    course_model = model_data["course_model"]
    lines = [
        f"# {model_data['course']} 通用课程模型",
        "",
        f"- 模型来源：{course_model['model_source']}",
        f"- 核心问题：{course_model['core_problem']}",
        f"- 主线地图：{course_model['main_map']}",
        f"- 考试能力：{course_model['exam_abilities']}",
        f"- 考试操作：{', '.join(course_model['exam_operations'])}",
        "",
        "## 知识单元",
        "",
        "| 知识点 | 类型 | 证据 | 题型 | 考试操作 | 状态 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for unit in course_model["knowledge_units"]:
        lines.append(
            f"| {unit['name']} | {unit['unit_type']} | {unit['evidence']} | "
            f"{unit['question_type']} | {unit['assessment_operation'] or '待诊断'} | {unit['status']} |"
        )
    lines.extend(
        [
            "",
            "## 训练与补救",
            "",
            f"- 表达形式：{', '.join(course_model['representation_modes'])}",
            f"- 评分方式：{', '.join(course_model['scoring_modes'])}",
            f"- 练习阶梯：{', '.join(course_model['practice_ladder'])}",
            "",
        ]
    )
    lines.extend(f"- {rule}" for rule in course_model["remediation_rules"])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Infer a universal course model.")
    parser.add_argument("input", type=Path, help="material_inventory.json or plan input JSON")
    parser.add_argument("--output", "-o", type=Path, help="Write model JSON")
    parser.add_argument("--markdown", type=Path, help="Write model Markdown")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8-sig"))
    model_data = build_model(data)
    text = json.dumps(model_data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.markdown:
        write_markdown(model_data, args.markdown)


if __name__ == "__main__":
    main()
