# 材料处理流水线

目标：把教材、PPT、DOCX、TXT/Markdown、往年题、错题和用户口述转成可排计划的数据，而不是只做摘要。

## 处理顺序

1. **材料登记**
   - 文件名、类型、来源、是否官方、是否往年题、是否有答案。
   - 标出风险：扫描不清、缺页、无答案、来源不可靠。

2. **结构抽取**
   - 教材/PPT：标题、章节、页码、例题、章末题。
   - 往年题：题号、分值、题型、考点、重复模式。
   - 笔记/错题：老师强调词、易错点、学生薄弱点。

3. **主题合并**
   - 把同义主题合并成统一知识点。
   - 例如“特征值”“特征向量”“对角化”可以在同一线代链条里，但做题入口不同，要保留区别。

4. **证据标注**
   - 官方范围：`explicit`
   - 往年题/作业反复出现：`repeated`
   - 课程核心但未直接出现：`inferred`
   - 证据不足：`uncertain`

5. **输出结构化结果**
   - `material_inventory.md`：给人看的材料清单和主题表。
   - `material_inventory.json`：给脚本继续排计划。

## 结构化 JSON 字段

```json
{
  "course": "课程名",
  "sources": [
    {
      "path": "文件路径",
      "type": "pdf/pptx/docx/txt/md/json",
      "role": "textbook/slides/past_paper/notes/scope/wrong_questions",
      "trust": "official/repeated/user/inferred",
      "summary": "材料摘要"
    }
  ],
  "topics": [
    {
      "name": "知识点",
      "evidence": "explicit/repeated/inferred/uncertain",
      "question_type": "计算/证明/简答/编程/论述",
      "source_refs": ["文件:页码或题号"],
      "signals": ["老师强调", "2023大题", "作业重复"],
      "status": "unknown"
    }
  ]
}
```

## 使用脚本

可先运行：

```bash
python scripts/extract_materials.py materials_dir --course 高等数学 --output-dir extracted
```

脚本能处理 `.txt`、`.md`、`.json`，并尽量从 `.docx`、`.pptx` 中抽 XML 文本；PDF 需要本机存在 `pypdf` 才能自动抽取，否则会登记为“需要手动摘录”。

脚本结果只是初筛。最终诊断仍要由 Codex 结合用户目标、考试日期和材料可信度判断。

## 质量门槛

材料处理结果必须至少回答：

- 哪些材料最可信？
- 哪些知识点有明确考试证据？
- 哪些题型重复出现？
- 哪些信息缺失会影响计划？
- 下一步是补材料、做诊断题，还是直接排计划？
