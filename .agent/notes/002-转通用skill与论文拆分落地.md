# 002 — 转通用 skill 与论文拆分落地

- **日期**：2026-09-11
- **接 notes 001**

## 变更

### 一、定位改了

用户拍板三件事：仓库转 public；定位从「用户个人的审稿工作台」改成**任何审稿人 `git clone` 到 `~/.claude/skills/cri-paper` 即装的通用审稿 skill**；skill 的第一步不是直接写意见，而是**先把整篇论文详细拆开**，拆分优先于其余一切实现。

起源材料 `info-from-others.md` 与 `github-proj.md` 归档进 `background/`，用一句话说明它们是项目起源，不参与流程。notes 001 悬而未决的第 3、4 条到此关闭。

### 二、survey/04 与主会话核实

新增 `survey/04-论文拆分方法调研.md`，覆盖自动审稿系统怎么拆论文、人类审稿方法论（Keshav 三遍法、NeurIPS checklist、各会议 reviewer instructions）、主张证据对齐、本地 PDF 结构化工具、图表逐张清单、对九层草案的逐层差分意见。

主会话对其中三条影响流程的断言做了在线核实：

1. **Crossref REST API 免注册。** 官方 access-and-authentication 页原话 "Anyone can access the REST API, no signup or registration is required."，三个池分别是 Public、Polite（带 mailto）、Plus（订阅）。
2. **OpenAlex 在 2026-02-24 改成按量计费。** 每个 key 每天 1 美元免费额度，单篇 work 精确 lookup 免费，list/filter 0.0001 美元一次，**按标题 search 0.001 美元一次**。旧文档里的「10 万次/天、礼貌池」已作废。结论是核真参考文献用 Crossref 比用 OpenAlex 干净，因为标题搜索正好是它的收费动作。
3. **GROBID 的 `consolidate*` 系列默认关。** 开启后会调 Crossref REST API 或 biblio-glutton 做外部元数据富集，第一档下必须保持关。

另外在 `survey/04 §4.1` 里定下一条对合规判断很关键的区分：引用核查真正外发的不是稿件正文，而是**引用指纹**，即某个 IP 在某时刻把这一组特定文献逐条查了一遍，这组组合在稿件日后发表时可以对上。所以「档一不做引用核查」这条结论成立，但理由不是「喂给了 LLM」。

### 三、两份规格

- `docs/skill-design-v1.md`：仓库布局、五步流程、红线、安装方式。
- `docs/paper-decomposition-spec-v1.md`：十二层拆分规格。v1.1 追加 §6 裁定九条，回应手册线提出的歧义，其中第 1 条定死列结构，第 7 条裁定 **U 模式可以把图页交给模型做事实提取**（图内文字转录、轴标注与单位、图例、误差棒有无、panel 数、图里画的是什么），判断栏仍由人填，M 模式模型不看图。依据是 ICML Policy B 原文允许把稿件喂给隐私合规模型并用于理解论文。

### 四、两条实现线

**脚本线**（`scripts/` 与 `examples/`，本轮已完成）：三个单文件 Python 脚本，`pdf_skeleton.py`、`numeric_consistency.py`、`check_refs.py`，加一份 `scripts/README.md` 合规表。在公开论文 arXiv 2504.09737 上实测，实测数字：

- 30 页，参考文献 68 条，图表编号 11 个，贡献句 3 条，摘要数字 5 个。
- 摘要里的 `12,000` 在正文各页一次都找不到，人工 grep 全文确认属实。这正是脚本该报的那类线索，但是否构成问题要人看。
- `check_refs.py` 默认参数下前 15 条**一个网络请求都没发出**，因为这篇的参考文献表不写 DOI 也不写 arXiv ID，而默认模式只认这两种标识符。开 `--title-search` 做对照：命中 8、未命中 7，其中 Ref1 属标题搜索同名撞车的假阳性。
- 结论之一：默认最小化模式对「引用表不写 DOI」的 ML 会议稿几乎无效。这是已知缺口，不要为了补它擅自开标题搜索。

已知缺陷逐条写在 `examples/2504.09737-README.md`：`pdf_skeleton.py` 7 条、`numeric_consistency.py` 3 条、`check_refs.py` 5 条。最咬人的三条是 URL 被 `pdftotext` 的空格截断、引文里提到的别人的图表编号混进图表清单、`pdfplumber` 的 lines 策略在 booktabs 风格表上基本失效。

**skill 主体线**（本轮本条记录的这条线）：新建 `SKILL.md`（174 行）、`references/policy-tiers.md`、`references/comment-shape.md`、`references/de-ai-checklist.md`、`references/prompts.md`；重写 `README.md` 为中英双语；更新 `AGENT.md` 第 1、2、3、6 节；`.gitignore` 补 `paper-card*.md` 兜底并用否定规则放行空白模板。本机装了符号链接 `~/.claude/skills/cri-paper` 指向工作目录。

**手册线**（并行，本轮未由本条线经手）：`references/paper-decomposition.md`、`references/figure-checklist.md`、`templates/paper-card.md`。

### 五、脚本合规复核（只读，本轮复查）

- `check_refs.py`：`--polite` 默认 `None`，即默认不带 mailto（第 305 行）；`--title-search` 是 `store_true`，默认关（第 307 行）；`--delay` 默认 1.0，第 392 到 393 行逐条串行 `time.sleep`。三条与规格 §3 第 7 层的最小化做法一致。
- `pdf_skeleton.py` 与 `numeric_consistency.py`：import 只有 `argparse`、`os`、`re`、`shutil`、`subprocess`、`sys`、`datetime`，没有 `urllib`、`requests`、`socket`、`urlopen` 任何一个。`pdf_skeleton.py` 里唯一命中 `http` 的是第 197 行的 `URL_RE` 正则，用于从文本里抓链接字符串，不发请求。两个脚本确认零网络，第一档可跑。

## 理由

- 转通用 skill 是用户的决定，理由是这套东西对任何审稿人都成立，没必要只服务一个人。
- 拆分优先是因为整条流程的承重点在「每条意见都能指到具体位置」，而位置来自拆分。拆分不落地，后面的意见形状与去 AI 味都是空的。
- 脚本只产出 `fact` 栏不产出 `judgement`，是为了让同一套工具在三个档位下都能用：档一也能跑零网络脚本，只是两栏都人填。

## 备选

- 引用核真用 OpenAlex：放弃。2026-02-24 改计费之后，按标题 search 是收费动作，且实际需要一个免费 key，不如 Crossref 干净。
- 论文卡每层自定义列：放弃。规格 §6 第 1 条定死列结构，脚本骨架与模板必须逐列一致，否则三方产出粘不到一起。
- `.gitignore` 只靠 `reviews/` 一条挡论文卡：放弃。加了 `paper-card*.md` 兜底，防止卡片被写到别的目录去。空白模板用否定规则放行，`examples/` 下的 `*-skeleton.md` 命名不同不受影响。

## 未做

- 没有 git commit，没有 push。用户要求验收之后另行通知。
- 没有碰 `survey/`、`docs/`、`scripts/`、`examples/`，也没有碰手册线在写的三份文件。
- 没有在任何真实投稿上跑过这套流程。

## 悬而未决

1. **会议或期刊名称仍未知**，合规档位定不了。这是第 0 步。
2. **评审语言未知。** 英文意见这条线本机没有任何去 AI 味资产，只有 `references/de-ai-checklist.md` 的手动清单兜底。
3. **手册线的三份文件待验收**：`references/paper-decomposition.md`、`references/figure-checklist.md`、`templates/paper-card.md`。`SKILL.md` 已经按设计引用了这三个路径，验收时要确认路径与列结构对得上。
4. **skill 从未在真实稿件上跑过。** 全部验证都在公开论文上做的。真实投稿的排版、页限、参考文献格式都可能把脚本打穿，第一次实战要留返工时间。

## 关联

- `SKILL.md`、`references/` 六份、`README.md`、`AGENT.md`、`.gitignore`
- `docs/skill-design-v1.md`、`docs/paper-decomposition-spec-v1.md`
- `survey/04-论文拆分方法调研.md`、`examples/2504.09737-README.md`
- knowledge `003-论文拆分十二层.md`
- 前一条 notes `001-调研阶段交接与仓库建立.md`
