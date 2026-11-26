#!/usr/bin/env python3
"""Build a smart-course blueprint aligned with the Shantou University guide."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TOPICS = ["课程核心概念", "典型应用任务", "综合问题分析"]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path | None, default: Any) -> Any:
    if not path or not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return [value]


def topic_name(topic: Any) -> str:
    if isinstance(topic, str):
        return topic
    if isinstance(topic, dict):
        return str(topic.get("name") or topic.get("topic") or topic.get("title") or "未命名知识点")
    return str(topic)


def top_topics(course_model: dict[str, Any], fallback_topics: list[str], limit: int) -> list[dict[str, Any]]:
    raw = (
        course_model.get("topics")
        or course_model.get("knowledge_units")
        or course_model.get("course_model", {}).get("knowledge_units")
        or []
    )
    topics = []
    for item in listify(raw)[:limit]:
        if isinstance(item, dict):
            topics.append(dict(item))
        else:
            topics.append({"name": str(item)})
    if not topics:
        topics = [{"name": item} for item in fallback_topics or DEFAULT_TOPICS]
    return topics


def topic_operations(topic: dict[str, Any], course_model: dict[str, Any]) -> list[str]:
    ops = topic.get("exam_operations") or topic.get("operations") or topic.get("assessment_operation")
    if isinstance(ops, str):
        return [item.strip() for item in ops.replace("/", ",").split(",") if item.strip()]
    if isinstance(ops, list):
        return [str(item) for item in ops]
    model_ops = course_model.get("exam_operations") or course_model.get("course_model", {}).get("exam_operations")
    return [str(item) for item in listify(model_ops)] or ["理解", "应用", "迁移"]


def build_blueprint(args: argparse.Namespace) -> dict[str, Any]:
    course_model = load_json(args.course_model, {})
    learning_memory = load_json(args.learning_memory, {})
    strategy_memory = load_json(args.strategy_memory, {})
    topics = top_topics(course_model, args.fallback_topics, args.limit)

    topic_names = [topic_name(topic) for topic in topics]
    knowledge_graph = []
    ability_graph = []
    problem_graph = []
    assessment_bank = []
    layered_tasks = []

    for topic in topics:
        name = topic_name(topic)
        operations = topic_operations(topic, course_model)
        resources = topic.get("sources") or topic.get("materials") or topic.get("linked_resources") or []
        evidence = topic.get("evidence") or topic.get("evidence_strength") or "待教师确认"

        knowledge_graph.append(
            {
                "name": name,
                "brief": topic.get("brief") or topic.get("summary") or "由课程材料、课堂任务和题库共同补充。",
                "learning_objective": f"学生能够解释{name}，并在课程题型中正确识别、应用和迁移。",
                "linked_resources": listify(resources),
                "quiz_items": [f"{name}概念辨认题", f"{name}应用或计算题"],
                "tags": ["知识点", "考点", "待动态更新"],
                "evidence": evidence,
            }
        )
        ability_graph.append(
            {
                "ability": f"运用{name}解决课程问题",
                "linked_knowledge": [name],
                "training_task": f"完成1道{name}基础题、1道变式题，并口述解题依据。",
                "assessment": "按概念准确性、步骤完整性、迁移能力和表达规范评分。",
                "operations": operations,
            }
        )
        problem_graph.append(
            {
                "basic_problem": f"{name}是什么，适用条件是什么？",
                "combined_problem": f"{name}如何与相邻知识点联合考查？",
                "complex_problem": f"在真实案例或综合题中如何识别并应用{name}？",
                "teacher_reference": "由教师课件、教材例题或人工审核后的AI草案补充。",
            }
        )
        assessment_bank.extend(
            [
                {"topic": name, "type": "基础型", "item": f"解释{name}的定义、条件和关键词。", "source": "ai_generated_requires_review"},
                {"topic": name, "type": "提升型", "item": f"完成一道{name}应用、计算或分析题。", "source": "ai_generated_requires_review"},
                {"topic": name, "type": "挑战型", "item": f"把{name}放入综合案例中判断、推理和表达。", "source": "ai_generated_requires_review"},
            ]
        )
        layered_tasks.append(
            {
                "topic": name,
                "basic": f"看1份资源，写出{name}一句话规则，完成1道基础题。",
                "advanced": f"完成{name}变式题并记录错因。",
                "challenge": f"用{name}解释综合问题或讲给同学听。",
                "exam_operation": operations,
            }
        )

    return {
        "version": "smart-course-blueprint-v2",
        "generated_at": now_iso(),
        "course": args.course,
        "guide_alignment": {
            "student_centered": "以学生画像、错题库、疑问库、掌握度和学习节奏生成个性化学习路径。",
            "digital_intelligence": "将AI答疑、作业批改、学习数据、错题归因和教师报告纳入课程运行。",
            "teacher_student_ai": "形成教师设目标与审核、学生主动学习、AI过程支持的师-生-机协同。",
            "hybrid_teaching": "线上预习、资源点播、AI问答与线下讨论、实践、项目任务结合。",
            "personalized_learning": "根据掌握度、错因、剩余时间和历史速度动态调整学习任务。",
            "dynamic_optimization": "用学习行为、测评结果、资源使用和错题复测更新课程图谱与任务。",
        },
        "course_objectives": {
            "school_program_alignment": "课程目标需映射学校和专业培养目标，由教师最终确认。",
            "knowledge": f"识别、解释并应用{args.course}核心知识点。",
            "ability": "完成典型任务、变式任务和综合问题分析。",
            "quality": "形成规范表达、学术诚信、AI合理使用和持续复盘能力。",
            "digital_literacy_ethics": "理解AI辅助学习边界，能标注AI生成内容并保护隐私。",
            "interdisciplinary": "在真实情境中连接本课程与工程、管理、社会或历史问题。",
            "measurable_verbs": ["识别", "解释", "计算", "比较", "分析", "评价", "迁移"],
        },
        "hybrid_teaching_design": {
            "online": ["智能预习", "资源点播", "AI问答", "微测验", "错题复盘"],
            "offline": ["高阶讨论", "实验或实践", "项目任务", "同伴讲解", "教师点评"],
            "handoff_rule": "线上发现的高频错因进入线下回讲，线下表现再写回学生画像。",
        },
        "smart_preview": {
            "before_class": ["10-20分钟预习任务", "先修概念自测", "本节核心问题"],
            "diagnosis": "根据预习答题和疑问生成课堂提醒。",
        },
        "resource_on_demand": {
            "resource_types": ["教材", "课件", "案例", "视频", "作业", "往年题", "错题", "答疑记录"],
            "matching_rule": "按知识点、能力点、问题类型和学生当前卡点推荐资源。",
        },
        "ai_qa_support": {
            "scope": ["概念解释", "例题步骤", "错题订正", "应用场景", "前沿拓展"],
            "boundary": "涉及正式评分、教师要求和开放性主观评价时必须人工审核。",
        },
        "offline_high_order_activities": [
            "案例讨论",
            "实验或工程实践",
            "项目式任务",
            "学生讲解与互评",
        ],
        "knowledge_graph": knowledge_graph,
        "ability_graph": ability_graph,
        "problem_graph": problem_graph,
        "ideological_political_graph": [
            {
                "tag": "课程思政",
                "linked_topics": topic_names[:3],
                "case_resource": "待教师按课程特点补充真实案例。",
                "value_point": "科学精神、工程伦理、社会责任、历史责任或学术诚信。",
            }
        ],
        "ai_case_virtual_simulation_tasks": [
            {
                "task": "AI案例分析或虚拟仿真草案",
                "linked_topics": topic_names[: min(3, len(topic_names))],
                "review_rule": "案例、数据和评分标准由教师审核后进入正式教学。",
            }
        ],
        "learning_behavior_tracking": {
            "events": ["资源打开", "预习测验", "答疑问题", "作业批改", "错题订正", "复测结果"],
            "metrics": ["知识点掌握度", "资源轨迹", "互动数据", "高频错因", "复测间隔"],
        },
        "course_knowledge_base": {
            "materials": ["教材", "课件", "课堂笔记", "案例", "文献", "视频"],
            "student_generated": ["错题", "疑问", "作业批改记录", "复述记录"],
            "governance": "资源标注来源、版本、适用知识点和审核状态。",
        },
        "mooc_video_plan": {
            "unit_videos": [f"{name}微课视频或教师讲解片段" for name in topic_names[:6]],
            "usage": "服务课前预习、课后补救和考前回看。",
        },
        "assessment_bank": assessment_bank,
        "agent_qa_coverage": {
            "concept": "概念解释与辨析",
            "application": "例题、作业和综合题应用",
            "frontier": "课程相关真实案例、行业应用或拓展资料",
        },
        "layered_tasks": layered_tasks,
        "evaluation_design": {
            "formative": ["预习测验", "课堂互动", "作业批改", "错题复测", "阶段自测"],
            "summative": ["期末考试", "项目成果", "综合案例或论文"],
            "multi_subject": ["学生自评", "AI初评", "同伴互评", "教师终评"],
            "ai_initial_human_review": "AI可做初评和反馈草案，正式评价需教师或助教审核。",
        },
        "student_digital_profile": {
            "knowledge_mastery": "每个知识点的掌握状态和置信度。",
            "resource_trajectory": "看过哪些材料、视频、题目和讲解。",
            "interaction_data": "提问、答题、订正、复述和反馈记录。",
            "mistake_profile": "常见错因、正确规则和考前易错提醒。",
        },
        "teacher_student_ai_model": {
            "teacher_role": "设定目标、审核资源、确定评价标准、完成最终评分和教学调整。",
            "student_role": "完成预习、练习、复述、作业订正和学习反馈，保留自主学习责任。",
            "ai_role": "提供个性化辅导、资源推荐、作业批改草案、错题复盘和数据报告。",
            "interaction_loop": "教师设目标-AI支持过程-学生产出证据-教师据数据优化教学。",
        },
        "feedback_loop": {
            "student": ["学习进度", "掌握度", "错题复测", "下一步计划"],
            "teacher": ["班级薄弱点", "高频错因", "未解决疑问", "分层练习建议"],
            "course": ["资源缺口", "题库缺口", "讲解策略有效性", "课程图谱更新点"],
        },
        "resource_lifecycle_management": {
            "versioning": "资源、题目、视频和案例记录版本与来源。",
            "audit": "AI生成内容、正式题库、学生数据和教师反馈分开标注审核状态。",
            "sustainability": "每轮教学后按数据更新知识库、题库、图谱和任务。",
        },
        "ai_ethics_review": {
            "principle": "智能辅助，责任在人。",
            "human_review_required": [
                "AI生成题进入正式题库前",
                "AI对主观成果或开放性作业初评后",
                "AI作业批改结果用于正式评价前",
                "教师报告用于管理或教学决策前",
            ],
            "privacy": "默认匿名聚合，不输出学生可识别身份、原始作业照片或私密聊天。",
            "academic_integrity": "标注AI生成内容，不协助作弊或替代学生完成作业。",
            "ip_compliance": "课程资源、题库、案例和视频需标注来源并遵守知识产权要求。",
        },
        "construction_path": [
            {"stage": "基础梳理", "output": "材料清单、课程模型、知识点索引"},
            {"stage": "核心构建", "output": "知识库、测评库、多元课程图谱、AI助学流程"},
            {"stage": "试点优化", "output": "样例学生数据、教师报告、问题修正清单"},
            {"stage": "常态应用", "output": "动态更新机制、审核制度、持续改进证据"},
        ],
        "evidence_inputs": {
            "course_model": str(args.course_model or ""),
            "learning_memory": str(args.learning_memory or ""),
            "strategy_memory": str(args.strategy_memory or ""),
            "learning_memory_courses": list((learning_memory.get("courses") or {}).keys()),
            "strategy_episode_count": len(strategy_memory.get("episodes", [])),
        },
    }


def write_markdown(data: dict[str, Any], path: Path) -> None:
    lines = [
        f"# {data['course']} 智慧课程建设蓝图",
        "",
        "## 指南对齐摘要",
        "",
    ]
    for key, value in data["guide_alignment"].items():
        lines.append(f"- **{key}**: {value}")
    lines.extend(["", "## 课程目标", ""])
    for key, value in data["course_objectives"].items():
        lines.append(f"- **{key}**: {value}")
    lines.extend(["", "## 知识图谱", "", "| 知识点 | 学习目标 | 关联资源 | 测验题 | 标签 |", "| --- | --- | --- | --- | --- |"])
    for item in data["knowledge_graph"]:
        lines.append(
            f"| {item['name']} | {item['learning_objective']} | {', '.join(map(str, item['linked_resources'])) or '待补充'} | "
            f"{', '.join(item['quiz_items'])} | {', '.join(item['tags'])} |"
        )
    lines.extend(["", "## 分层任务", "", "| 知识点 | 基础型 | 提升型 | 挑战型 |", "| --- | --- | --- | --- |"])
    for item in data["layered_tasks"]:
        lines.append(f"| {item['topic']} | {item['basic']} | {item['advanced']} | {item['challenge']} |")
    lines.extend(["", "## 评价设计", ""])
    for key, value in data["evaluation_design"].items():
        lines.append(f"- **{key}**: {', '.join(value) if isinstance(value, list) else value}")
    lines.extend(["", "## 建设路径", ""])
    for stage in data["construction_path"]:
        lines.append(f"- **{stage['stage']}**: {stage['output']}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a smart-course blueprint aligned with the Shantou University guide.")
    parser.add_argument("--course", required=True)
    parser.add_argument("--course-model", type=Path)
    parser.add_argument("--learning-memory", type=Path)
    parser.add_argument("--strategy-memory", type=Path)
    parser.add_argument("--fallback-topics", nargs="*", default=DEFAULT_TOPICS)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    data = build_blueprint(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(data, args.markdown)
    print(f"wrote {args.output}")
    print(f"wrote {args.markdown}")


if __name__ == "__main__":
    main()
