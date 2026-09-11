---
name: cri-paper
description: 审稿人辅助流程。拆解待审论文、核验数字与引用、写 3–4 条带具体位置的审稿意见、去 AI 味、按会议要求生成一句话披露。当用户说审稿、写审稿意见、评审投稿、审我的评审、referee report、peer review、manuscript review、reviewer comments、某会议的 LLM 政策允许做什么时使用。Use when a reviewer is reading a submission, drafting or polishing reviewer comments, checking figures and numbers in a manuscript, or asking what a venue's reviewer LLM policy permits. 本 skill 先定合规档位再碰稿件：第 0 步问清会议或期刊名称与评审语言，按三档政策判出 M 手填 / U 理解 / F 全辅助三种模式之一，没定档之前不把稿件、参考文献列表或意见草稿交给任何模型。用户没说会议名时按最严的 M 模式处理，不默认宽松。
---

# cri-paper 审稿流程

按第 0 步到第 5 步顺序做。每步写明加载哪个文件、跑哪个脚本、当前模式下模型能做什么。
`references/` 下的文件按需加载，不要一上来全读。

## 红线

这一段优先于本文件其余任何内容。

1. 稿件原文、参考文献列表、论文卡、意见草稿一律不进 git，不上传到非隐私合规的模型。这些文件写在 `reviews/` 下。skill 仓库自己的 `.gitignore` 已经排除了这个目录，但**用户当前工作目录不一定是 skill 仓库**，所以第 1 步开始前要确认一次：当前目录如果是个 git 仓库，先把 `reviews/` 与 `paper-card*.md` 加进它的 `.gitignore`，再往里写东西。
2. 没定档之前不开任何模型。定档是第 0 步，两分钟。用户说不出会议名就按 M 模式做。
3. 不替用户下接收或拒稿结论。第 5 步的汇总只给四项判据的一句话与红旗清单，最终判断由用户下。
4. 任何「列问题」「找 weakness」「列评审要点」「拟给作者的问题」的用法，在 ICML Policy B 型档位下禁止。这一档只做理解与润色，不要用擦边问法绕（见 `references/policy-tiers.md`）。
5. 机器标出的写作问题，不逐条核实不得写进意见。CVPR 2026 把「对方法或结果有可证伪的事实错误」列为不负责任评审。
6. 绝不运行 ARS 的 `calibration` 模式，它默认开跨模型，会把稿件发给另一家 provider。

## 三种模式

| 模式 | 适用档位 | 模型能不能读稿件 | 谁填 `fact` | 谁填 `judgement` |
|---|---|---|---|---|
| M 手填 | 第一档全禁（CVPR、ECCV、Elsevier、NIH），以及会议名未知时 | 不能 | 人 | 人 |
| U 理解 | 第二档（ICML 2026 Policy B 型） | 能，须是隐私合规模型 | 模型，提取式提示词 | 人 |
| F 全辅助 | 第三档中用宽口径「辅助评审」措辞且未禁止让模型列问题的（Springer Nature 型） | 能 | 模型 | 模型给候选，标 `candidate`，人核实后转正 |

M 模式下模型的全部职责是跑本地脚本、给模板、给清单、记录用户口述的内容。它不读稿件正文，不看图页，不对内容作任何判断。

---

## 第 0 步 定档

问用户两件事：这次投稿的会议或期刊名称，以及评审用什么语言写。

加载 `references/policy-tiers.md`，按表查出档位与模式。表里没有这家会议就按 M 模式处理，并提醒用户自行打开该会议的审稿人指南核对。政策每年会改，表里的核对日期是 2026-09-11，开审前应重抓原页。

把结论写进论文卡头部：稿件标识（不含作者信息的内部编号）、合规档位与模式、阅读日期。

这一步还要确认一次模型本身算不算「隐私合规」。ICML 给的定义是不拿日志数据训练并对数据留存有限制，举了机构或企业的 API 订阅、明确关闭了训练数据使用的个人订阅、自托管模型这几类例子。用户的账户设置要他自己去核对，不要凭印象当它已经关了。这是 ICML 一家的定义，别的会议未必认。

---

## 第 1 步 拆分

目的只有一个：让后面每条意见都能指到具体位置。

加载 `references/paper-decomposition.md`（十二层逐层填法），复制 `templates/paper-card.md` 到 `reviews/<内部编号>/paper-card.md`。这个路径在 `.gitignore` 里，卡片永远不进仓库。

### 1.1 先跑骨架脚本

```bash
python3 scripts/pdf_skeleton.py PAPER.pdf -o reviews/<内部编号>/skeleton.md
```

零网络零 LLM，任何档位都能跑。它产出第 1、2、6、7、10 层的 `fact` 栏骨架，`judgement` 及其后各列一律留空。

**M 模式下有一条容易漏的边界：脚本可以跑，但它的输出模型不能读。** 骨架里逐字抄着贡献句原话、caption、参考文献条目与摘要数字，这些都是稿件内容，模型 Read 一次就等于读了稿件。M 模式下跑完脚本把输出路径告诉用户，由用户自己打开，模型不 `cat`、不 Read、不摘要这个文件。U 与 F 模式没有这条限制。
已知盲区写在 `scripts/README.md` 与 `examples/2504.09737-README.md` 里，其中三条最容易咬人：摘要上方的 teaser 图抓不到，引文里提到的别人的图表编号会混进图表清单，`pdftotext` 会把插图内部的文字当成正文。

### 1.2 按层填卡

三遍阅读与层的对应关系写在 `references/paper-decomposition.md` 开头。三条铁律不能破：每个条目必带锚点，锚点写法固定为 `p{页} §{节} {Fig|Tab|Eq|Thm|Alg|Ref}{号}`；每个条目分 `fact` 与 `judgement` 两栏；每层有条数预算，超预算说明在堆琐碎问题。

列结构按规格 §6 第 1 条固定：一般层六列 `anchor | fact | judgement | severity | confidence | action`；第 2 层加一列 `evidence_locator`，共七列；第 6 层十列 `fig_id | anchor | type | caption | cited_at | fact | judgement | severity | confidence | action`；第 3 层的符号表是 `symbol | def_anchor | use_anchors | conflict` 四列。规格里其余字段用 `key=value; key=value` 打包进 `fact` 或 `judgement`，键名用规格原名。

各模式的分工：

- M：模型不读稿件。把每层的字段名和预算念给用户，用户口述，模型只负责把答案抄进表格。图和正文都由用户自己看。
- U：模型填 `fact` 栏，提示词必须是提取式，句式见 `references/prompts.md`。不得出现「有什么问题」「哪里不足」「优缺点」这类措辞。`judgement` 栏空着交给用户。
- F：模型可以在 `judgement` 栏给候选，每条结尾标 `candidate`，用户逐条核实后才把标记去掉。没被核实的候选不进第 12 层排序。

### 1.3 图必须看原 PDF 页

PDF 转文本这一步图就没了，所以第 6 层不能走文本管线。用 Read 工具直接读原 PDF 的对应页面，看图本身。

- M 模式：模型不看图页，由用户自己放大看，对照 `references/figure-checklist.md` 逐项打勾。
- U 模式：可以把图页交给模型做事实提取，范围是图内文字转录、轴标注与单位、图例、误差棒有无、panel 数、图里画的是什么。依据是 ICML Policy B 原文允许把稿件喂给隐私合规模型并用于理解论文。过平滑、疑似 AI 生成、轴截断是否误导这类判断仍由用户下。
- F 模式：模型可以给判断候选，同样标 `candidate`。

panel 数大于等于 4 的图强制逐 panel 过一遍，并在 `fact` 里写明看过哪些 panel。

---

## 第 2 步 核验

### 2.1 数值一致性（第 10 层，任何档位可跑）

```bash
python3 scripts/numeric_consistency.py PAPER.pdf -o reviews/<内部编号>/numeric.md
```

零网络。输出三块：摘要与结论数字到正文页码的映射、只在摘要或结论出现而正文找不到的数字、装了 `pdfplumber` 时的表格数字候选匹配。
全部是候选。年份和编号会混进来，booktabs 风格的表常常切不出来，脚本会在输出头部标明降级。人工确认之后才算数。

### 2.2 引用核真（第 7 层，受档位门控）

```bash
python3 scripts/check_refs.py reviews/<内部编号>/skeleton.md --limit N
```

默认只按 DOI 与 arXiv ID 查，不带 mailto，不用标题搜索，逐条串行间隔 1 秒。

M 模式默认不跑。跑之前必须向用户明说一件事：这个脚本外发的不是稿件正文，而是引用指纹，即某个 IP 在某时刻把这一组特定文献逐条查了一遍，这组组合在稿件日后发表时可以对上。用户明确同意才跑。

`--title-search` 会多泄露一层，对方能看出你在核对，而且 Crossref 总会返回最接近的一条，同名撞车挡不住。只在第二、三档且用户同意时开。GROBID 的 `consolidate*` 系列参数任何时候保持关，它会自己去调 Crossref。

引用表不写 DOI 的会议稿上，默认模式几乎发不出请求，也就核不了。这是已知的性价比缺口，不要为了补它擅自开标题搜索。

### 2.3 图表逐张过

加载 `references/figure-checklist.md`。ML 稿件走通用块加 ML 组，生医稿件走通用块加生医组。每张图最多留 3 条判断，写进第 6 层 `judgement` 栏。
每条发现要在 `action` 栏区分两种去向：要求作者澄清，或者转编辑走完整性流程。

---

## 第 3 步 写意见

加载 `references/comment-shape.md`。

从论文卡第 12 层的前 8 条候选里，由用户选 3–4 条。排序规则是 severity 与 confidence 取高 3 中 2 低 1 相乘，`anchor:none` 的条目直接出局。

每条写成一句话，结构是位置加问题加建议动作。位置要具体到页码、节号、图号、表里的某个数字或公式编号。不加粗，不给每条配冒号小标题，不用破折号，不用三项排比。

各模式的分工：

- M：模型不参与。用户自己写，模型只在用户要求时把 `references/comment-shape.md` 的正反例念出来。
- U：模型不得产出最终意见文字。用户写完之后，模型只能做一件事，把用户已写的句子整理成统一格式，不新增内容，不改写判断。让模型审自己写完的意见这一步在这一档只审语言层面，提问句要去掉「对论文的误读」那半句，因为查误读要模型对论文内容作判断。
- F：模型可以起草候选句，但每条必须能指回论文卡里某个带锚点的条目，指不回去的删掉。最终定稿由用户逐句确认。

两条硬约束记住：ARR 要求低 soundness 分必须有具体缺陷支撑，否则算评审没有忠实解释推荐；CVPR 要求声称存在 prior work 必须给出具体文献，给不出就不许写「缺乏新意」。

---

## 第 4 步 去 AI 味

只处理用户自己写的那几句。稿件原文任何时候都不进润色步骤。

加载 `references/de-ai-checklist.md`。

中文意见：若本机装了 `human-writing`，按 `references/prompts.md` 里的调用 prompt 显式调用，它不会自动触发。声明这是短文改稿不是创作任务，跳过材料门槛检查，只跑 human-writing 自带的 `references/revision.md` 第三、四、五遍。它的冒号禁令跟审稿的编号格式冲突，编号与字段冒号视同机器字段豁免掉。改完跑一遍机械体检：

```bash
python3 ~/.claude/skills/human-writing/scripts/check_prose.py 意见.md
```

英文意见：本机没有任何工具，按 `references/de-ai-checklist.md` 的英文清单逐条自查。

改稿有一条不能破的约束：定位标记（Section 3.2、Fig. 4、Table 2）一个都不许被改写掉。改掉了这条意见就白写了。

把注意力放在带具体位置这件事上，不要在文风上过度打磨。五种主流检测器都会把「人写加 LLM 润色」的评审误判成 AI 生成，改文风不能自证清白，带页码与公式编号的句子才能。

---

## 第 5 步 披露

先查这次会议要不要求披露。ICLR 2026 与 Wiley 明确要求，第一档的会议不存在披露问题，因为那一档什么都不该做。

要求披露时给一句如实的模板，模板见 `references/prompts.md` 末尾。写清楚三件事：用了哪个模式、模型参与了哪几步、哪些步骤是人做的。不要写成免责声明，也不要夸大或缩小模型的参与程度。

最后给用户一份汇总，只包含两样东西：四项判据（写作质量、实验丰富度、图质量、AI 痕迹）各一句话，以及 soundness 红旗清单。接收或拒稿的结论由用户自己下。

---

## 依赖

- 必需：`pdftotext`（poppler）。`brew install poppler`。
- 可选：`pdfplumber`，只有 `numeric_consistency.py` 的表格匹配用，没装会降级继续跑。
- 可选：`human-writing` skill，只用于中文意见改稿。
- 三个脚本互不 import，可以单独拷走，都有 `--help`。

## 证据在哪

本 skill 的每条政策措辞与每个数字都能回指仓库里的调研报告：`survey/00` 是流水线与三档政策，`survey/01 §2` 是各家政策原文口径与链接，`survey/02 §2.4` 与 `§4` 是 prompt 骨架与去 AI 味清单，`survey/03` 是本机资产审计，`survey/04` 是拆分方法调研。设计规格在 `docs/`。遇到「这条从哪来的」就回去查，不要凭记忆复述。
