# 去 AI 味

第 4 步用。

## 只喂自己写的句子，不喂稿件原文

这一步处理的对象只有用户自己写的那 3–4 句意见。稿件正文、摘要、参考文献列表在任何档位下都不进润色步骤。第一档连这一步也不做。

还有一件事要先说清楚：不要指望靠改文风过检测。五种主流检测器都会把「人写加 LLM 润色」的评审误判成 AI 生成，「允许润色」这类政策事实上无法执行（见 survey/01 §3 第 4 步、§4.1）。真正管用的是每条意见带上只有读过论文的人才写得出的具体位置。文风清理是收尾，不是主力。

## 中文意见：调用 human-writing

`human-writing` 装在 `~/.claude/skills/human-writing/`。它的 description 里不含「审稿意见」这个场景，不会自动触发，**必须显式调用**（见 survey/03 §1.2、§1.4）。

调用时要带三条豁免，否则会走错流程：

1. **跳过材料门槛。** 它的主线是长文创作，会先做「五件材料」清点，材料不足时要求追问或缩短。审稿意见本来就是 3–4 句，触发这套流程会浪费一轮往返，甚至反过来向你追问。调用时明确声明这是短文改稿任务不是创作任务（见 survey/03 §1.5 第 1 条）。
2. **只跑 human-writing 自带的 `references/revision.md` 第三、四、五遍**，外加它自带的 `references/formats.md` 的「短文」与「观点与评论」两节。这两个路径指的都是 `~/.claude/skills/human-writing/` 下的文件，不是本仓库的 `references/`。不要走完整创作流程。
3. **编号冒号视同机器字段豁免。** 审稿意见常写成 `1. 实验：缺少与 X 的对比` 或 `W1: ...`，而这个 skill 只放行「引出人物原话」的冒号。编号与字段冒号属于机器格式，不在它的禁令范围内（见 survey/03 §1.5 第 2 条）。顺带一提，把冒号小标题改写成自然句其实更不像 AI，能改就改。

完整调用 prompt 见 `references/prompts.md`。

改完跑一遍机械体检：

```bash
python3 ~/.claude/skills/human-writing/scripts/check_prose.py 意见.md
```

它的禁令表与审稿意见的 AI 味重灾区几乎逐条对上：破折号、「值得注意的是」、「不是 X 而是 Y」、三项整齐排比、每条配一个冒号小标题（见 survey/03 §1.5）。

## 英文意见：逐条自查

本机没有任何英文去 AI 味资产，这是已知的最大缺口（见 survey/03 遗留缺口 1）。下面这份清单来自 survey/00 第五部分与 survey/02 §4，逐条打勾。

- [ ] 不加粗。任何 `**...**` 都去掉。
- [ ] 不用破折号。em dash 与 en dash 一律不用，改成句号或逗号断开。
- [ ] 不写 `Overall`、`In summary`、`It is worth noting that` 这类路标。
- [ ] 不用三项排比，两项为限。`not just X, but Y` 这类 negative parallelism 同样删掉。
- [ ] 不写 `future work could further ...` 式收尾。
- [ ] 每条意见的开头句式不要雷同。四条不要都以 `The paper does not ...` 开头。
- [ ] 定位标记一个都不许被改写掉。`Section 3.2`、`Fig. 4`、`Table 2`、公式编号、表里的具体数字，改掉了这条意见就白写了。

另外三类词按 Wikipedia 的 Signs of AI writing 清单顺手清一遍（见 survey/02 §4）：`delve`、`crucial`、`pivotal`、`underscore`、`intricate`、`showcase` 这类形容与动词；用 `serves as`、`functions as`、`boasts`、`features` 替代简单的 `is` 或 `are`；`Despite its success ... faces challenges ... Future investments could enhance` 这种公式化收尾。

想补工具的话，`blader/humanizer` 是这一档的事实标准，46.7k 星，MIT，单文件，专打 em dash 滥用、rule of three、negative parallelism（见 survey/02 §4、§5 Top 4）。本机未装，装不装由用户决定。

## 最后一遍

改完之后，把改前改后两版并排读一遍，只确认一件事：每条意见里的页码、节号、图号、表号、公式号、具体数字，是不是一个不少地还在原地。
