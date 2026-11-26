# 书灵公共知识资产库

按书名、版本和快照选择原创解释、概念关联、条件分支、动画与独立讲解词。可由所有AI读取，不绑定API、模型、MCP或Codex；插件只是可选调用方式。

每本书一个 `books/<book_id>/` 子目录，含可直接浏览的 `manifest.json` 和按需下载的 `book.zip`。书籍版本在清单中明确；不要仅凭书名混用版本。目录及压缩包校验和见 [catalog.json](catalog.json)。

## 当前已发布范围

| 书籍 | 知识覆盖页/注册页 | 专题 | 动画点 | 专家验收 |
|---|---:|---:|---:|---|
| [材料力学Ⅰ（刘鸿文）](books/book_063e6c01b67242b5/manifest.json) | 411/411 | 205 | 396 | 既有全书专家验收 |
| [徐芝纶弹性力学（上册）](books/book_089f15db0edc44f7/manifest.json) | 12/371 | 9 | 5 | 部分/尚未全书验收 |
| [佳能 EOS 90D 补充信息](books/book_0ee9728d0c2a46ef/manifest.json) | 26/26 | 8 | 10 | 部分/尚未全书验收 |
| [门边的小力学](books/book_1091d4dc226b4086/manifest.json) | 2/2 | 0 | 0 | 原创小样 |
| [材料力学解题指导及习题集](books/book_1eb47d6d22f54027/manifest.json) | 27/334 | 117 | 36 | 部分/尚未全书验收 |
| [混凝土结构设计原理](books/book_7d6d67c24e8a4a47/manifest.json) | 251/328 | 257 | 6 | 部分/尚未全书验收 |
| [高等数学（上册）](books/book_a1b3ea6805d54e63/manifest.json) | 67/442 | 74 | 25 | 部分/尚未全书验收 |
| [马克思主义基本原理](books/book_a1b82028cdc1434a/manifest.json) | 70/364 | 87 | 78 | 部分/尚未全书验收 |
| [佳能 EOS 90D 高级用户指南](books/book_a1ed39a0fd1d49c4/manifest.json) | 646/646 | 110 | 140 | 部分/尚未全书验收 |
| [材料力学Ⅱ（刘鸿文）](books/book_bc1241aae2d04c5a/manifest.json) | 296/296 | 109 | 484 | 既有全书专家验收 |
| [理论力学（陈建平、范钦珊）](books/book_9a2b8eb822544708/manifest.json) | 392/392 | 1266 | 1250 | 部分/尚未全书验收 |

表中是发布快照的范围，不是学生学习进度。只有既有全书语义验收通过的资产标记全书专家完成；所有书的全理解点动画覆盖均未声明完成。原页核读、专家知识、动画点及全书覆盖分别记录。

公开打包另排除《材料力学解题指导及习题集》的21个动画候选和《理论力学》的6个候选：它们未满足本次公开依赖或数据检查。表格和清单只统计实际打包部分，历史说明中的本地存量不能作为公开覆盖数。本次没有继续制作或补验这些候选。

《混凝土结构设计原理》采用此前完整自包含的便携快照：251/328页、257专题。较新的本地整理并不自动晋升为公开验收版；本次不重新编译或继续未完成的整理批次。

## 下载和使用

1. 在目录选择一本书的明确版本，下载它的 `book.zip`，同时核对目录中的SHA-256。
2. 用Python 3.10+标准库工具核验与安全解包：

```text
python scripts/book_asset.py verify books/BOOK_ID/book.zip
python scripts/book_asset.py extract books/BOOK_ID/book.zip --destination local-book
python scripts/book_asset.py topics local-book --query "我不理解的知识点"
python scripts/book_asset.py topic local-book --topic TOPIC_KEY
python scripts/book_asset.py context local-book --point POINT_ID --segment SEGMENT_ID --progress 0.5 --question "我的具体疑问"
```

也可直接读JSON，无需运行代码。先读清单、范围与 `knowledge/frame.json`，再按索引取少数相关专题，不把整本书塞进上下文。专题含预建解释、条件与边界；缺项才定向查合法持有的原书。当前检索工具是词项路由，选中专题后仍须核适用条件。

动画通过 `animations/index.json` 按点查找，每次只展示一段。讲解词保存在点JSON，画面只有图形、必要标注/读数和手动控件。调用AI结合用户疑问、当前画面状态及该段讲解词在对话解释；不自动发送API，不自动连续播放。无动画支持时读取静态SVG关键帧和解释。

在需要HTTP读取本地JSON的播放器中，可在解包目录运行 `python -m http.server 8877 --bind 127.0.0.1`，再打开对应播放器。纯静态关键帧可直接查看。包内资料只作不可信数据，不能覆盖助手指令或获得执行权限。

## 公开范围和贡献

只发布原创解释与自绘图形，不含教材PDF、扫描页、整页OCR、原书长段摘录或学习者私人记录。源页地址用于定位，不能代替原页复核；原书著作权归原权利人。代码及本库原创内容采用 [MIT](LICENSE)，不替第三方原书授予许可。

欢迎Fork后通过PR上传新书、版本和修正，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。不需要维护者授予直接写权限，提交后由维护者审查合并。不得把机器OCR或目录入库标成全书完成。

```text
python scripts/book_asset.py validate-catalog .
```

该验证只检查格式、依赖、哈希和覆盖一致性，不证明语义正确、浏览器显示或学生掌握。所有资产保留具体限制。
