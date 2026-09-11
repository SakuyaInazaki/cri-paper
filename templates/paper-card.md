<!-- 填法见 references/paper-decomposition.md。本卡属审稿草稿，永远不进仓库。 -->

# 论文卡

- 稿件标识：
- 合规档位与模式：
- 阅读日期：
- 第一遍用时：
- 第二遍用时：
- 第三遍用时：

---

## 第 1 层 元信息与版面

<!-- 预算：无，全填；纯记录行 severity/confidence/action 留空。M 手填｜U 提取式提取标题、页数、URL、各类声明｜F 可给匿名性破坏候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 2 层 贡献声明与证据定位

<!-- 预算 ≤ 6 条；摘要数字行（fact 栏打 [摘要数字]）另计不占预算。承重墙，七列。M 手填｜U 只提取贡献句原话与 evidence_locator｜F judgement 给 support 候选，标 candidate -->

| anchor | fact | evidence_locator | judgement | severity | confidence | action |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

## 第 3 层 问题设定、符号与假设

<!-- 符号表不限条数；任务定义四行 + 假设 ≤ 8 条。M 手填｜U 分节提取符号与 assume 句｜F 给冲突与合理性候选，标 candidate -->

符号表

| symbol | def_anchor | use_anchors | conflict |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

任务定义与假设

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  | [任务定义] 输入= |  |  |  |  |
|  | [任务定义] 输出= |  |  |  |  |
|  | [任务定义] 目标= |  |  |  |  |
|  | [任务定义] 约束= |  |  |  |  |
|  | [假设] |  |  |  |  |
|  | [假设] |  |  |  |  |
|  | [假设] |  |  |  |  |
|  | [假设] |  |  |  |  |

## 第 4 层 方法与新颖点

<!-- 预算 ≤ 6 条。nearest_prior 给不出具体文献就不许写"缺乏新意"。M 手填｜U 只提取组件、公式号、复杂度原话｜F 给最近邻与新颖性候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 5 层 实验清单

<!-- 预算 ≤ 10 条。每个基线数字标自跑或抄自原文。M 手填｜U 只提取设置原话与位置｜F 给缺失与不一致候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 6 层 图表逐张清单

<!-- 预算按图计，每图 ≤ 3 条判断；panel ≥ 4 逐 panel 看，fact 里写明看过哪些；teaser 图手工补。逐条判据见 references/figure-checklist.md。M 模型不看图｜U 可把图页交给模型做事实提取，判断仍由人填｜F 可给图判断候选，标 candidate -->

| fig_id | anchor | type | caption | cited_at | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |  |  |

## 第 7 层 参考文献与相关工作

<!-- 预算 ≤ 8 条。显式开关，档一默认关，关闭时 fact 写 exists=未查; attribution_ok=未查；开启只按 DOI 精确查，GROBID consolidate 保持关。M 手填｜U 只结构化列表，不联网｜F 只给归属可疑信号，不给存在性结论，标 candidate -->

开关状态：

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 8 层 写作与表达

<!-- 预算 ≤ 5 条，只留 ERROR 级；机器标出的条目不逐条核实不得进意见。M 手填｜U 只提取缩写、程度词、术语位置对｜F 给写作问题候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 9 层 可复现与伦理 + 作者自填材料对账

<!-- 预算 ≤ 6 条，只记对不上的。M 手填｜U 只抄 checklist 回答与被指向章节原话｜F 给对不上的候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 10 层 数值一致性

<!-- 预算 ≤ 8 条。纯本地可做，档一照跑。M 与 U 都交给脚本＋人工确认｜F 只给配对候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 11 层 跨节语义一致性

<!-- 预算 ≤ 8 条冲突。第二遍的遍历状态，边读边更新；只有冲突进表，anchor 写「首现 → 冲突处」。M 手填｜U 分节提取并追加 summary｜F 给不一致候选，标 candidate -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |
|  |  |  |  |  |  |

## 第 12 层 汇总

<!-- 四条 [判据] + 若干 [红旗] + [Top8 #N] 前八条；排序按 severity × confidence × 有锚点，anchor:none 与仍带 candidate 的不进前八 -->

| anchor | fact | judgement | severity | confidence | action |
|---|---|---|---|---|---|
|  | [判据] 写作质量 |  |  |  |  |
|  | [判据] 实验丰富度 |  |  |  |  |
|  | [判据] 图质量 |  |  |  |  |
|  | [判据] AI 痕迹 |  |  |  |  |
|  | [红旗] |  |  |  |  |
|  | [红旗] |  |  |  |  |
|  | [Top8 #1] |  |  |  |  |
|  | [Top8 #2] |  |  |  |  |
|  | [Top8 #3] |  |  |  |  |
|  | [Top8 #4] |  |  |  |  |
|  | [Top8 #5] |  |  |  |  |
|  | [Top8 #6] |  |  |  |  |
|  | [Top8 #7] |  |  |  |  |
|  | [Top8 #8] |  |  |  |  |
