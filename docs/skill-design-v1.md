# 通用审稿 skill 设计 v1

日期 2026-09-11。仓库定位：可 `git clone` 到 `~/.claude/skills/cri-paper` 即装的通用审稿 skill。第一步是论文拆分（规格见 `paper-decomposition-spec-v1.md`），其余步骤沿用 `survey/00` 的流水线。

## 1. 仓库布局

```
SKILL.md                 skill 入口（frontmatter + 五步流程 + 红线），按需加载 references/
README.md                中英双语：是什么、怎么装、怎么用、不含任何稿件
AGENT.md                 维护约定（给后续 agent 会话）
references/
  policy-tiers.md        三档合规政策速查（从 survey/00 一 与 01 §2 提炼，含各会议原文要点与链接）
  paper-decomposition.md 拆分操作手册（12 层）
  figure-checklist.md    图表逐张清单
  comment-shape.md       意见形状：3–4 条、每条一句、位置+问题+建议动作，附正反例
  de-ai-checklist.md     去 AI 味：中文走 human-writing 的调用法，英文手动清单
  prompts.md             可复制 prompt：U 模式提取式提示、审我意见、ARS quick 约束、human-writing 调用
templates/paper-card.md  空白论文卡
scripts/                 pdf_skeleton.py / numeric_consistency.py / check_refs.py / README.md
examples/                公开论文上的骨架示例
docs/                    设计规格（本文件与拆分规格）
survey/                  证据库（00–04）
background/              项目起源材料（同事建议、原始链接）
.agent/                  notes / knowledge 记录体系
```

## 2. SKILL.md 的五步

**frontmatter**：`name: cri-paper`；`description` 用中英文写清触发场景：审稿、写审稿意见、peer review、referee report、manuscript review、reviewer、评审投稿；并声明"先定合规档位再碰稿件"。

**第 0 步 定档。** 问用户会议或期刊名与评审语言，加载 `references/policy-tiers.md` 判出档位与模式（M 手填 / U 理解 / F 全辅助）。档位写进论文卡头部。**M 模式下模型不得读取稿件**，只运行本地脚本、给模板和清单，由人填。用户没说会议名时默认按 M 处理，不默认宽松。

**第 1 步 拆分。** 先跑 `scripts/pdf_skeleton.py` 生成骨架（零网络零 LLM，任何档位可跑）。U/F 模式下模型按 `references/paper-decomposition.md` 逐层填 `fact` 栏，图必须用 Read 看原 PDF 页而不是文本；U 模式提示词只准提取式。论文卡写到 `reviews/<内部编号>/paper-card.md`（gitignore 目录）。

**第 2 步 核验。** `numeric_consistency.py`（本地）；`check_refs.py` 受档位门控，M 模式默认不跑，跑前必须向用户确认并说明会外发引用指纹；图表按 `references/figure-checklist.md` 逐张过。

**第 3 步 写意见。** 从论文卡第 12 层的前 8 条候选里由用户选 3–4 条，按 `references/comment-shape.md` 写成每条一句的"位置 + 问题 + 建议动作"。U 模式下模型不得产出最终意见文字，只能整理用户已写的句子。

**第 4 步 去 AI 味。** 只处理用户写的那几句，不把稿件原文送进润色步骤。中文：若装了 human-writing 则按 `references/prompts.md` 的调用法显式调用，再跑 `check_prose.py`；英文：按 `references/de-ai-checklist.md` 逐条自查。

**第 5 步 披露。** 会议要求披露时，给一句如实的披露模板（做了哪几步、用了什么模式）。

## 3. 红线（写在 SKILL.md 顶部）

- 稿件、参考文献列表、论文卡、意见草稿一律不进 git，不上传到非隐私合规的模型。
- 不替用户下接收或拒稿结论；汇总只给四项判据的一句话与红旗清单。
- 任何"列问题/找 weakness"的用法在 ICML Policy B 型档位下禁止；只做理解与润色。
- 机器标出的写作问题不逐条核实不得写进意见。

## 4. 安装

`git clone https://github.com/SakuyaInazaki/cri-paper ~/.claude/skills/cri-paper`。本机开发用符号链接指向工作目录。依赖：`pdftotext`（poppler），可选 `pdfplumber`。中文去 AI 味依赖可选的 human-writing skill。
