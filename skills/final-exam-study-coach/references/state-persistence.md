# 学习状态持久化

目标：让复习不是一次性计划，而是能跨多天跟踪“学过什么、哪里不会、下次何时复习”。

## 状态文件

建议每门课维护一个 JSON 状态文件：

```json
{
  "course": "线性代数",
  "exam_date": "2026-06-20",
  "generated_at": "2026-06-18T21:30:00+08:00",
  "last_time_check": "2026-06-18T21:30:00+08:00",
  "target": "80+",
  "current_score_estimate": null,
  "coverage_progress": {
    "mainline_percent": 0,
    "detail_percent": 0,
    "progress_basis": "checklist_count/weighted_estimate/not_built",
    "current_strategy": "先保主线/补细节/回炉错点/考前压缩"
  },
  "coverage_checklist": {
    "mainline_items": [],
    "detail_items": [],
    "high_score_risks": []
  },
  "topics": {
    "特征向量": {
      "status": "can_recognize",
      "last_practiced": "2026-05-28",
      "next_review": "2026-05-29",
      "evidence": ["做了3题，错2题"],
      "mistakes": ["把 P(A|B) 和 P(B|A) 写反"]
    }
  },
  "sessions": []
}
```

## 每次学习后更新

必须更新：

- 当前系统时间戳和本次学习发生时段。
- 完成了什么。
- 主线清单完成了哪些项、细节清单扫过哪些项，主线进度和细节进度如何变化。
- 正确率/估分。
- 错因。
- 相关知识点状态。
- 下次复习日期。
- 当前检查点，确保上下文压缩后能继续。
- 检查点必须包含当前系统时间戳，不能只写日期。恢复时先比较检查点时间与当前时间；如果已经跨天、考试已过、或进入新的倒计时阶段，必须先重排再继续。

## 状态升级规则

- `unknown` -> `can_recognize`：能认出题型或概念。
- `can_recognize` -> `can_explain`：能用自己的话解释。
- `can_explain` -> `can_solve_slowly`：能独立做出基础题。
- `can_solve_slowly` -> `exam_ready`：能限时、闭卷、稳定做考试题。

降级也允许：如果隔几天复测失败，状态下调一级，并安排更近的复习。

## 使用脚本

```bash
python scripts/update_study_state.py state.json --course 线性代数 --topic 特征向量 --result correct --confidence 4 --notes "限时题2/3正确"
```

脚本会更新 `last_practiced`、`next_review`、学习记录，并生成 Markdown 摘要。

如果学生没完成任务：

```bash
python scripts/update_study_state.py state.json --course 线性代数 --topic 特征向量 --result missed --confidence 1 --notes "原计划今晚90分钟未开始"
```

这会记录拖延事件、安排更近的复习，并生成 `state_checkpoint.md`。
