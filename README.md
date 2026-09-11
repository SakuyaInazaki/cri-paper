# cri-paper

一个通用的审稿 Claude Code skill。`git clone` 到 `~/.claude/skills/cri-paper` 就装好了。

## 是什么

它把「审稿人可以怎么用 AI 辅助、能用到什么程度」这件事固化成一条可照做的流程：先按会议政策定合规档位，再拆论文、核验、写意见、去 AI 味、按需披露。它不替你判断接收还是拒稿，只让你写出的每条意见都能指到具体位置。

**本仓库不含任何稿件内容。** 待审的投稿原文、参考文献列表、论文卡与审稿意见草稿都属于保密材料，永远不进版本控制，红线写在 `.gitignore` 顶部。

## 装法

```bash
git clone https://github.com/SakuyaInazaki/cri-paper ~/.claude/skills/cri-paper
```

## 依赖

- 必需：`pdftotext`（poppler），`brew install poppler`。
- 可选：`pdfplumber`，只有 `scripts/numeric_consistency.py` 的表格匹配用，没装会降级继续跑。
- 可选：`human-writing` skill，只用于中文意见改稿；英文意见走手动清单。

## 五步流程

0. **定档。** 问清会议或期刊名与评审语言，查 `references/policy-tiers.md`，判出 M 手填 / U 理解 / F 全辅助三种模式之一。没定档之前不开任何模型。
1. **拆分。** 跑 `scripts/pdf_skeleton.py` 生成骨架，按 `references/paper-decomposition.md` 逐层填十二层论文卡。图必须用 Read 看原 PDF 页。
2. **核验。** 数值一致性走本地脚本；引用核真受档位门控；图表按 `references/figure-checklist.md` 逐张过。
3. **写意见。** 从候选里选 3–4 条，每条一句，形状是位置加问题加建议动作。
4. **去 AI 味。** 只处理自己写的那几句。中文调 `human-writing`，英文对照清单自查。
5. **披露。** 会议要求时给一句如实的披露。

## 红线

稿件、参考文献列表、论文卡、意见草稿一律不进 git，不上传到非隐私合规的模型。没定档之前不开任何模型，会议名未知时按最严的 M 模式处理。不替用户下接收或拒稿结论。在 ICML Policy B 型档位下不做任何「列问题」「找 weakness」的动作。机器标出的写作问题不逐条核实不得写进意见。

## 目录

```
SKILL.md        skill 入口：红线、三种模式、五步流程
references/     按需加载：政策速查、拆分手册、图表清单、意见形状、去 AI 味、prompt 集
templates/      空白论文卡
scripts/        三个单文件 Python 脚本，零依赖底座
examples/       公开论文上的骨架实测记录
docs/           设计规格
survey/         证据库，00 到 04
background/     项目起源材料
.agent/         notes 与 knowledge 记录体系
```

## 证据

流程里的每条政策措辞与每个数字都能回指 `survey/` 下的五份中文报告。`survey/00` 是流水线与三档政策的入口，`survey/01` 是各家会议与出版商的政策原文口径，`survey/02` 是 skill 与 prompt 生态，`survey/03` 是本机资产审计，`survey/04` 是论文拆分方法调研。政策每年会改，表里的核对日期是 2026-09-11，开审前请重抓原页。

---

# cri-paper (English)

A general-purpose peer-review skill for Claude Code. Clone it into `~/.claude/skills/cri-paper` and it is installed.

## What it is

It turns the question of how far a reviewer may go with AI assistance into a procedure you can follow: settle the compliance tier from the venue's policy first, then decompose the paper, verify, write the comments, strip the AI tells, and disclose if required. It never decides accept or reject for you. What it does enforce is that every comment points at a concrete location in the manuscript.

**This repository contains no manuscript content.** Submissions under review, their reference lists, paper cards, and draft review reports are confidential and never enter version control. The red line is stated at the top of `.gitignore`.

## Install

```bash
git clone https://github.com/SakuyaInazaki/cri-paper ~/.claude/skills/cri-paper
```

## Dependencies

- Required: `pdftotext` (poppler), via `brew install poppler`.
- Optional: `pdfplumber`, used only by `scripts/numeric_consistency.py` for table matching; it degrades gracefully when absent.
- Optional: the `human-writing` skill, used only for polishing Chinese-language comments. English comments fall back to a manual checklist.

## The five steps

0. **Tier.** Ask for the venue name and the review language, look it up in `references/policy-tiers.md`, and settle on one of three modes: M (manual), U (comprehension), F (full assistance). No model is opened before the tier is settled.
1. **Decompose.** Run `scripts/pdf_skeleton.py` for the skeleton, then fill the twelve-layer paper card following `references/paper-decomposition.md`. Figures must be read from the original PDF pages, never through the text pipeline.
2. **Verify.** Numeric consistency runs locally; reference checking is gated by tier; figures are walked one by one against `references/figure-checklist.md`.
3. **Write.** Pick 3 or 4 candidates, one sentence each, shaped as location plus problem plus suggested action.
4. **De-slop.** Only your own sentences go through this step. Chinese goes through `human-writing`; English goes through the manual checklist.
5. **Disclose.** One honest sentence, when the venue asks for it.

## Red lines

Manuscripts, reference lists, paper cards, and draft comments never enter git and never go to a model that is not privacy-compliant. No model is opened before the tier is settled, and an unknown venue is treated as the strictest tier. The skill does not decide accept or reject. Under an ICML Policy B style tier it performs no "list the weaknesses" action of any kind. Writing problems flagged by a machine do not enter the review until they have been verified one by one.

## Evidence

Every policy quotation and every number in the workflow traces back to the five Chinese-language reports under `survey/`. Policies change every year; the tables were checked on 2026-09-11, so re-fetch the original pages before a real review.
