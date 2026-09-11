# AI 审稿 skill / prompt / agent 工作流生态盘点

> 调研日期：2026-09-11。所有 GitHub 条目的 star 数与最近 push 时间均通过 GitHub API 实测，时间戳为当日抓取值。
> 场景约束：审 2–3 篇稿，每篇输出 3–4 条、每条一句话的简洁意见，意见不能有 AI 味（尤其格式上）。

---

## 0. 一句话结论（先看这段）

**现成的审稿 skill 全部是「重型」的**——清一色多 agent、多角色、长报告、带 1–10 分 rubric，天生和「三四条一句话」相反。
所以正确用法不是「让 skill 写审稿意见」，而是 **让 skill 当参谋（内部消化），你自己写那三四条**。
另外有一个必须先知道的硬风险：ICML 2026 用 **PDF 隐藏水印短语** 抓 LLM 代写审稿意见，实测 795 条违规评审、506 名审稿人被查，398 人的投稿被 desk reject（共 497 篇）。把稿件 PDF 直接丢给模型让它出意见，这件事今年已经是可被机器检测的行为，不只是"看起来像 AI"的问题。

---

## 1. Claude Code / Codex / opencode 生态里的审稿 skill 与 agent

### 1.1 官方仓库：没有审稿 skill

[anthropics/skills](https://github.com/anthropics/skills)（175,773★，最近 push 2026-09-10）目前 `skills/` 下只有 19 个：`academy-guide, algorithmic-art, brand-guidelines, canvas-design, claude-api, discernment-nudge, doc-coauthoring, docx, frontend-design, internal-comms, mcp-builder, pdf, pptx, skill-creator, slack-gif-creator, theme-factory, web-artifacts-builder, webapp-testing, xlsx`。
**没有任何 peer review / paper review 相关条目。**能用上的只有 `pdf`（PDF 解析）和 `docx`（带修订与批注，改带批注的稿子时有用）。

### 1.2 最值得看的索引

[O0000-code/awesome-academic-skills](https://github.com/O0000-code/awesome-academic-skills)（24★，push 2026-09-11，CC0，中英双语）——**这是目前唯一按科研生命周期分类、且每条都标注 license / 是否联网 / 是否带 hooks 的学术 skill 索引**，收录 222 个 skill、14 个分类，其中专门有 `Peer Review & Response` 和 `Writing Quality & De-AI` 两节。本报告第 1、4 节的候选池主要来自它 + 独立核实。
泛用大列表（[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 74,855★ / [BehiSecc/awesome-claude-skills](https://github.com/BehiSecc/awesome-claude-skills) 10,118★）star 高但学术条目稀薄，检索审稿类没有增量。

### 1.3 审稿类 skill 逐条核实

| 仓库 | ★ | 最近 push | 流程（角色数 / 输出 / rubric） | 安装 | PDF 输入 | 适合轻量 3–4 条？ |
|---|---|---|---|---|---|---|
| [AlexWortega/ai-peer-review-skill](https://github.com/AlexWortega/ai-peer-review-skill) | 62 | 2026-05-08 | N 个匿名子 agent（NATO 代号 alfa/bravo/…，默认 3–5）并行独立评审 → meta-review 综合 → concern×reviewer 布尔矩阵 CSV。每个 reviewer 先用随机 hex seed 派生「主视角」（统计/实验设计/主张-证据对齐/可复现/相关工作/外部效度）和「立场强度」（怀疑但公允/对抗/先 steelman 再压），强制至少跑一次 arXiv 检索并按 arXiv ID 引用。默认塞一个 Neel Nanda 风格的 alignment 批评者 | `git clone` 后 symlink 到 `~/.claude/skills/paper-review` | **是**（pypdf/pdftotext，也吃 docx/txt/md） | ✗ 直接输出太长，但**它的 reviewer.md 是最好的 prompt 骨架**（见 §2.4） |
| [poldrack/ai-peer-review](https://github.com/poldrack/ai-peer-review) | 154 | 2026-07-05 | 上面那个的上游。Python 工具，调 6 个不同厂商模型（GPT-4o、Claude、Gemini、DeepSeek R1、Llama 4）各出一份，再合成 meta-review | pip/本地跑，需要 4 家 API key | 是 | ✗（还要多付 key） |
| [claesbackman/AI-research-feedback](https://github.com/claesbackman/AI-research-feedback) | 478 | 2026-08-27 | 10 个 skill。`review-paper` = 8 个并行 agent（拼写/内部一致性与交叉引用/无支撑主张/数学记号/图表/referee 综合/贡献辩护者/贡献怀疑者），7 和 8 反向对打后在 synthesis 里对账。支持指定期刊人格（AER/QJE/JPE/Econometrica/REStud/JF/JFE/RFS…）。**另有 `review-paper-light`（2 agent 快检）和 `review-paper-checks`（3 agent 机械检查）** | 单 skill `curl` 一条命令，或整包 `cp -R Skills/. ~/.claude/skills/` | ✗ **只读 LaTeX `.tex` 源**（配套 `pdf-to-markdown` skill 可先转） | `review-paper-light` 最接近，但强经济学取向 |
| [lcrawfurd/claude-skills](https://github.com/lcrawfurd/claude-skills) | 9 | 2026-09-02 | 6 个 skill 纯 markdown。`paper-review` 把 5 套成名框架串起来：Edmans（Contribution/Execution/Exposition 三维编辑评估）、Nyhan 的 9 条方法学 checklist、Humphreys、Blattman、Evans/Bellemare。输出要求分 Major concerns / Minor issues / Strengths | 复制 md 到 `~/.claude/skills/<name>/SKILL.md` | 传路径即可（靠 Claude 自带读取） | **较接近**：框架清单短、无固定长报告模板；**且作者明说同样可当 Codex 的 `AGENTS.md` 用** |
| [Imbad0202/academic-research-skills](https://github.com/imbad0202/academic-research-skills) | 47,621 | 2026-09-11 | `academic-paper-reviewer` v1.10：7 agent（field_analyst 先判领域并动态生成 5 位审稿人身份 → EIC + 方法学 + 领域 + 跨学科 + Devil's Advocate 并行 → editorial_synthesizer 综合）。带 `quality_rubrics.md`、`editorial_decision_standards.md`、`statistical_reporting_standards.md`，输出 Editorial Decision Letter + Revision Roadmap。**有 `quick` 模式：只跑 field_analyst + EIC，产出 15 分钟版「快评 + 关键问题清单」** | 已作为 plugin 装在本机（`~/.claude/plugins/cache/academic-research-skills/.../3.13.0`），命令 `/ars-reviewer` | 传文件即可 | **`quick` 模式是全场最接近的**（详见 §5） |
| [shaowen-ye/manuscript-review-skill](https://github.com/shaowen-ye/manuscript-review-skill) | 21 | 2026-07-16 | 6 个角色化审稿人（架构/理论/方法…），输出**中英双语彩色批注 .docx**，含 1–10 分评分矩阵和优先级修改清单，可对齐目标期刊 | 复制 SKILL.md | — | ✗ 输出格式过重 |
| [xz-liu/mean-reviewer-skill](https://github.com/xz-liu/mean-reviewer-skill) | 59 | 2026-04-12 | 扮演最恶劣的 Reviewer 2：堆砌 weakness、攻击框架、分数固定 reject、rebuttal 阶段寸步不让。半是对 LLM 审稿的檄文，半是压力测试 | 复制 SKILL.md | — | ✗（当红队玩具可以） |
| [richard-kim-79/archora-skills](https://github.com/richard-kim-79/archora-skills) | 48 | 2026-05-20 | 模拟 1 位主编 + 3 位审稿人；厂商（Archora）背景但纯 markdown 可独立跑 | 复制 | — | ✗ |
| [cmertdalli/polisci-review](https://github.com/cmertdalli/polisci-review) | 18 | 2026-03-07 | 政治学专用 9 模块预审（贡献/理论/测量/识别/透明度/期刊契合），带 8 份核实过的期刊政策档案 | 复制 | — | ✗（学科不对口） |
| [stephenturner/skill-peer-review-assistant](https://github.com/stephenturner/skill-peer-review-assistant) | 50 | 2026-06-30 | 接 Consensus MCP 做真实文献检索，查背景主张是否站得住、漏引了什么、方法是否过时；输出 .docx（Summary / Background / Missing citations / Methods / Major / Minor / Recommendation / Audit log） | 下载 `.skill` 或 zip | 上传稿件 | ✗ 需 Consensus 账号；**但「查漏引 + 方法是否过时」这两问最适合不熟悉的领域** |
| [pengkangzhen/academic-writing-toolkit](https://github.com/pengkangzhen/academic-writing-toolkit)（原 `academic-review-skill` 已改名跳转） | 6 | 2026-08-26 | 运筹/管理科学专用，检测领域红旗（不可行的量、平凡的 VSS%），**刻意把批评写成疑问句**以免误杀真结果 | 复制 | — | 思路可借（疑问句化） |
| [ChicagoHAI/OpenAIReview](https://github.com/ChicagoHAI/OpenAIReview) | 165 | 2026-08-13 | UChicago CHAI 出品，非 skill 而是渐进式流水线：顺序读全文并维护 running summary（主张/定义/公式），因此能抓跨节前后矛盾，issue 定位覆盖率 87% | Python 仓库 | 是 | ✗ 但**「跨节一致性」这一路径是多 agent 方案抓不到的** |
| [timpara/opencode-academic-research](https://github.com/timpara/opencode-academic-research) | 62 | 2026-08-30 | 把 academic-research-skills 移植到 **opencode**：4 skill / 13 slash command / 38 agent | opencode 插件 | — | 若主力在 opencode 才考虑 |

**Skill 市场**：skills.sh（Vercel 系，接了 Snyk/Socket 安全审计）与 SkillsMP（号称索引 150 万+ SKILL.md）都能搜到 peer review 类条目，但站点为前端动态渲染，**本次抓取拿不到结构化列表，Top 榜位次与安装量未核实**。skills.rest 上确有 `peer-review-assistant`（即上表 stephenturner 那个）的镜像页。

---

## 2. 经典 prompt 模板与 rubric

### 2.1 ACL ARR review form（最适合抄骨架，因为字段最少最务实）
[官方 review form](https://aclrollingreview.org/reviewform) 字段顺序：Paper Summary → **Summary of Strengths** → **Summary of Weaknesses**（官方鼓励编号列条） → Comments/Suggestions/Typos → Confidence(1–5) → **Soundness(1–5)** → **Excitement(1–5)** → **Overall Assessment(1–5)** → Best Paper Justification → Limitations & Societal Impact → Ethical Concerns → Needs Ethics Review → Reproducibility(1–5) → Datasets(1–5) → Software(1–5) → Author Identity Knowledge(1–5)。
[ARR reviewer guidelines](https://aclrollingreview.org/reviewerguidelines) 三条最有用的：① **不规定长度，但要求具体**——不要写 "X 不清楚"，要写清楚到底缺什么信息；② 低 Soundness 分必须有对应的具体缺陷支撑，否则"你的评审没有忠实解释你的推荐"；③ 差评审的特征被明确列举：含糊、讽刺挖苦、低分无依据、无视作者澄清。
**注意 ARR 明文禁止 LLM 写初稿**："The reviewer has to read the paper fully and write the content and argument of the review by themselves"，只允许非母语者用工具 paraphrase，且**不得把机密材料交给非隐私保护的生成式工具**。

### 2.2 NeurIPS review form（AI Scientist 里那份就是它）
Summary / Strengths & Weaknesses（分 Originality、Quality、Clarity、Significance 四维提问）/ Questions / Limitations / Ethical concerns / Soundness(1–4) / Presentation(1–4) / Contribution(1–4) / Overall(1–10) / Confidence(1–5)。
[NeurIPS 2026 甚至在做官方 AI 辅助评审实验](https://neurips.cc/Conferences/2026/ai-reviewing-experiment)：随机分配到「无 LLM / 开放式 LLM / 结构化 LLM」三组，零数据留存。但同页明确写着：**"Except for this review experiment, NeurIPS does not sanction any other use of LLMs during the review process."**

### 2.3 CVPR reviewer guidelines
一句可以刻在桌上的话：写一份**"你愿意签上自己名字"**的评审（[CVPR 2026 Reviewer Guidelines](https://cvpr.thecvf.com/Conferences/2026/ReviewerGuidelines)）；最有价值的意见是帮作者理解不足并知道怎么改；贬低和讽刺没有位置。CVPR 另有专门的 [How to be a good reviewer 教学 PPT](https://cvpr2022.thecvf.com/sites/default/files/2021-11/How%20to%20be%20a%20good%20reviewer-tutorials%20for%20cvpr2022%20reviewers.pptx.pdf) 和 [2019 program chairs 版 PDF](https://www.cs.ryerson.ca/~wangcs/resources/How-to-Review-for-CVPR.pdf)。

### 2.4 可复用的 prompt 骨架（从 AI Scientist + AlexWortega 提炼）

[SakanaAI/AI-Scientist](https://github.com/SakanaAI/AI-Scientist)（14,529★，push 2025-12-19）`ai_scientist/perform_review.py` 里的 system prompt 极简：
> "You are an AI researcher who is reviewing a paper that was submitted to a prestigious ML venue. Be critical and cautious in your decision."
后接完整 NeurIPS review form + 强制 JSON 输出（THOUGHT 段先自由思考，再吐 JSON）。它还提供 `_neg` / `_pos` 两个变体（不确定就压分 / 不确定就抬分）用于校准偏置。

AlexWortega `prompts/reviewer.md` 里三条值得直接搬走的约束：
1. **"A review that finds nothing wrong with a non-trivial paper is a failed review."**
2. **强制 grounding**："Ground every claim in the paper text below. Do not invent quotes, citations, statistics... If something is unclear or missing from the text, say so explicitly — that itself is a reviewable issue."
3. **Major concern 四段式**：Issue（一句话）/ Where（章节图表位置，缺失则写 "absent"）/ Why it matters（如何影响主张）/ What would address it（作者能做的具体修改）。

这个四段式是**本次调研里最适合改造成「一句话意见」的结构**：把四段压成一句，天然就是「在哪 + 什么问题 + 怎么改」，也正好避开 AI 味的老三样（总分总、加粗小标题、排比）。

---

## 3. 中文社区的实际做法与踩坑

> 说明：本次检索只能拿到知乎/CSDN 的公开索引与可抓取页面；**小红书、B 站、微信公众号正文受登录墙/风控限制，未能直接核实，下列小红书/B 站相关表述从缺**。

**做法层面的共识（来自知乎问答与专栏索引）**
- 主流分层：**「AI 不能替你判断，最多帮你润色」**。多篇讨论把底线划在同一处——审稿人自己已经做完判断，只让 AI 把语言写顺，这属于文字工具；让 AI 直接产出结论就越线了。参见知乎问题[「调查显示超半数审稿人在用 AI 审稿，如何看待？」](https://www.zhihu.com/question/1992965162353780394)、[「能不能用 ChatGPT 回复审稿人意见？」](https://www.zhihu.com/question/582718387)。
- 对比实测类内容（如[「让 AI 当 Nature Commun 审稿人，审稿报告大对比」](https://zhuanlan.zhihu.com/p/12557096425)）给出的一致结论：AI 能挑出"表层"问题（写作、结构、缺失的对照、格式），**但做不了以实验数据为依据的逐步逻辑推导**，指不出具体漏洞。这恰好印证同事那句"从外观因素评估"——AI 参谋的能力区间正好落在外观层。
- 模板党：CSDN/知乎上大量「审稿意见万能模板」类文章（[例](https://blog.csdn.net/wzk4869/article/details/130897113)、[例](https://zhuanlan.zhihu.com/p/468445073)），套路一致为「总体评价 + 具体修改建议 + 推荐结论」。**这类模板是 AI 味的重灾区**——一旦照抄，格式先暴露。

**踩坑与红线**
- **保密**：把作者未发表稿件上传给第三方商用模型，在中文社区已被明确称为"泄密"；Elsevier、NIH 等禁止把稿件交给 AI 系统（[CSDN 综述文](https://blog.csdn.net/Willen_/article/details/136160171)）。知乎另有专栏直接以[《用 AI 生成审稿意见？知名期刊发文：可能泄露学术成果》](https://zhuanlan.zhihu.com/p/2011868255548089794)为题。
- **被抓的真实案例**：上述 CSDN 文记载，一位教授把自己被拒的论文丢进 ChatGPT 要摘要，输出与拒稿意见里的 "contributions" 段**几乎逐字相同**，只换了几个词——审稿人用 AI 代写被这样反向识破。伴随特征是"泛泛的语法批评"（而作者是英语母语者）。
- **"去 AI 味"提示词**：中文社区的去 AI 味攻略（[666 条提示词整理](https://blog.csdn.net/weixin_40780178/article/details/143447095) 等）主张口语化、避开"首先/其次/最后"、加入第一人称与个人经历。**但要注意：这些是为自媒体文案写的，直接套到审稿意见上会矫枉过正**（审稿意见不需要"我上周也踩过这个坑"式的个人经历，需要的是短、准、指位置）。

**今年的新变量（会直接影响"别写得太 AI"这条要求的严重性）**
- [ICLR 2026 官方博客](https://blog.iclr.cc/2025/11/19/iclr-2026-response-to-llm-generated-papers-and-reviews/)：用 LLM 必须披露且自负其责；发低质量 LLM 评审的审稿人"will also face consequences, including the desk rejection of their submitted papers"。第三方（Pangram Labs）对 ICLR 2026 的 76,139 条评审做检测，称 21% 为 AI 生成、超 50% 有 AI 参与（该第三方数字**未经会议方确认，标为未核实**）。
- [ICML 2026 官方博客](https://blog.icml.cc/2026/03/18/on-violations-of-llm-review-policies/)：在投稿 PDF 里**埋隐藏水印短语**（从 17 万条短语库随机抽对），审稿人把 PDF 喂给 LLM 时模型会被诱导把这些短语写进评审，多数模型上检出率 >80%，全部人工复核。结果：约 795 条评审违规、506 名审稿人；其中 398 名互惠审稿人的投稿被 desk reject（共 497 篇），51 人（约 10%）因 LLM 占比超 50% 被删除全部评审。ICML 让审稿人事前二选一：Policy A 完全禁用 LLM / Policy B 允许 LLM 帮助理解论文与润色评审。

> **可操作推论**：如果你审的稿来自埋水印的会议，把 PDF 原文整份丢进模型、再把模型输出当意见交上去，是可被机器检出的。相对安全的姿势是：**自己读 PDF 做判断，只把你自己写的要点（不含原文大段）交给模型做压缩与语气打磨**，并在交稿前通读一遍有没有突兀的、与领域无关的固定搭配短语。

---

## 4. 「去 AI 味」工具/skill 同类盘点

（`KKKKhazix/human-writing` 3,591★ / push 2026-08-11 / MIT，中文通用改稿，本机已装，另一条线在处理，此处只列同类）

| 仓库 | ★ | 最近 push | 定位 | 对审稿意见是否合用 |
|---|---|---|---|---|
| [blader/humanizer](https://github.com/blader/humanizer) | 46,746 | 2026-09-06 | 事实标准。专打 em dash 滥用、rule-of-three、填充词、negative parallelism（"不是 X，而是 Y"）。只用读写工具，定位为"收尾一道" | **合用**，且正好命中"格式上的 AI 味" |
| [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) | 17,024 | 2026-03-17 | star 最高的 de-slop，8 条教条规则；通用文本，非学术向，不管误报 | 可用但偏博客腔 |
| [conorbronsdon/avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | 4,302 | 2026-09-10 | 最"诚实"的一个：引用误报研究，坚持自己的标记是"signals, not proof" | 合用，适合做检查而非改写 |
| [stephenturner/skill-deslop](https://github.com/stephenturner/skill-deslop) | 392 | 2026-03-18 | 科学写作感知型 de-slop，**会放过 Methods 的被动语态等学科惯例** | 学术场景比 stop-slop 更稳 |
| [crabin/paper-humanizer-skill](https://github.com/crabin/paper-humanizer-skill) | 117 | 2026-03-28 | 中英双语学术文本 humanizer，严格保留事实/数字/结论，并报告改了哪些 pattern。无 license | 中文意见可用 |
| [JakobThumm/proofreading](https://github.com/JakobThumm/proofreading) | 40 | 2026-04-23 | 100+ 项稿件检查（结构/数学记号/统计/图/缩写），**还能从带批注 PDF 里提取审稿标记** | 反向用：当"找问题"的 checklist |
| 中文论文降 AIGC 专类：[deai-academic-zh](https://github.com/houlaisan/deai-academic-zh)、[humanizer-academic-zh](https://github.com/cangtianhuang/humanizer-academic-zh)、[aigc-down-skill](https://github.com/yezery/aigc-down-skill)、[anti-aigc-zh](https://github.com/beizi6/anti-aigc-zh) | — | — | 面向知网/维普查 AIGC 率的学位论文改写 | ✗ 场景不对，且属检测规避 |

**非 skill 但最值钱的一份清单**：[Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)。它把 AI 痕迹分四类，其中**格式类**正是同事点名的那条：过度加粗、emoji 当格式、em dash 泛滥、Title Case 小标题、只含子标题的标题、乱用表格。语言类：滥用 "Additionally / delve / crucial / pivotal / underscore / intricate / tapestry / testament / foster / enhance / showcase"；用 "serves as / functions as / boasts / features" 替代简单的 is/are；negative parallelism（"not just X, but Y"）。结构类：僵硬的提纲式骨架、"Despite its success… faces challenges… Future investments could enhance" 这种公式化收尾。
**审稿意见写作直接可用的反向 checklist**：不加粗、不用破折号、不写"总体而言"、不排比三项、不写"未来工作可以进一步…"。

---

## 5. 推荐清单（按你的实际需求排序）

### Top 1｜本机已装的 `academic-research-skills` 的 **quick 模式** — 当参谋，零安装成本
- **为什么**：本机 `~/.claude/plugins/.../academic-research-skills/3.13.0` 已装（命令 `/ars-reviewer`）。它的 `quick` 模式只跑 `field_analyst + eic`，产出"EIC 快评 + 关键问题清单（15 分钟版）"，**正好是"外观因素 + 写作质量 + 实验丰富性"这一层**，不会拖出 5 份长报告。
- **怎么用**：`/ars-reviewer` 后明确说 `quick mode`，或直接说"给我一个 quick look"。它带 `references/quality_rubrics.md` 和 `statistical_reporting_standards.md` 可当红旗清单查。
- **怎么改**：在调用时追加一句约束 —— "只输出不超过 6 条候选问题，每条一句话，标明在第几节/哪张图，不要评分、不要小标题、不要总结段"。然后你从 6 条里挑 3–4 条自己重写。
- **注意**：仓库 47,621★ 但 license 是 NOASSERTION；且它是 plugin，会读全文——见下方"保密"提醒。

### Top 2｜[lcrawfurd/claude-skills 的 `paper-review`](https://github.com/lcrawfurd/claude-skills)（9★，2026-09-02）— 最轻、跨工具
- **为什么**：纯 markdown，无脚本无子 agent，把 Edmans 三维（Contribution / Execution / Exposition）+ Nyhan 9 条方法学 checklist 直接给模型当尺子。输出只要求 Major / Minor / Strengths 三档，没有强制长模板 —— 最容易压成三四条。**作者明确说同样可以贴进 Codex 的 `AGENTS.md`**，你的 Codex/opencode 也能用同一套。
- **怎么装**：把 `paper-review.md` 内容复制到 `~/.claude/skills/paper-review/SKILL.md`，加一行 frontmatter `name` / `description` 即可。
- **怎么改**：删掉 Edmans 以外的 4 套框架（对不熟悉的领域，Contribution/Execution/Exposition 三问足够），末尾加死约束："输出恰好 4 条，每条一句话，句式为『<位置>：<问题>，建议<动作>』，禁止 markdown 加粗、禁止破折号、禁止编号以外的层级"。

### Top 3｜[AlexWortega/ai-peer-review-skill 的 `prompts/reviewer.md`](https://github.com/AlexWortega/ai-peer-review-skill)（62★，2026-05-08，MIT）— **只抄 prompt，不装 skill**
- **为什么**：skill 本身太重（N 个子进程 + CSV 矩阵），但它的 prompt 是全场质量最高的：强制 grounding 反幻觉、"挑不出毛病的评审就是失败的评审"、以及 Major concern 的 Issue/Where/Why/Fix 四段式。把四段压成一句，就是你要的那种意见。
- **怎么用**：不装。直接在对话里粘 reviewer.md 的 §Output format 段，再加"把每条 Major concern 压缩成不超过 30 字的一句话，保留 Where 和 Fix"。
- **怎么改**：关掉它的 arXiv 强制检索（你审 2–3 篇不需要跑文献），关掉 SEED/LENS 那段随机化（那是给多 reviewer 去相关性用的，单人用没意义）。

### Top 4｜[blader/humanizer](https://github.com/blader/humanizer)（46,746★，2026-09-06，MIT）+ [stephenturner/skill-deslop](https://github.com/stephenturner/skill-deslop)（392★）— 最后一道去 AI 味
- **为什么**：同事点名"尤其是一些格式上"。humanizer 的打击面（em dash、rule-of-three、negative parallelism、填充词）与 Wikipedia 那份 signs 清单几乎重合；skill-deslop 学科感知更强，不会把学术惯例一起洗掉。
- **怎么装**：`~/.claude/skills/humanizer/SKILL.md` 复制即可（单文件）。
- **怎么改**：给它加一条白名单——审稿意见里的"Section 3.2""Fig. 4""Table 2"这类定位标记不许改写；同时加禁令"不得加入个人经历、口语语气词、表情"。

### Top 5（仅当领域真的不熟）｜[stephenturner/skill-peer-review-assistant](https://github.com/stephenturner/skill-peer-review-assistant)（50★，2026-06-30，MIT）
- **为什么**：唯一带真实文献检索（Consensus MCP）的，专门回答两个你不熟领域时最难自答的问题——"它是不是漏引了该引的"和"它的方法是不是已经过时了"。这两条恰好是能写成一句话、且显得内行的意见。
- **代价**：需 Consensus 账号 + MCP connector，且**要把稿件上传**——见下面的红线。若不想上传，退而求其次：只把论文的 title/abstract 关键词交给它检索，不传全文。

### 建议的实际流水线（5 步，每篇 20 分钟内）
1. 你自己通读，先在纸上记下 5–8 个直觉问题（AI 之前先有判断，这一步不能省，ARR/ICML 政策的落点都在这里）。
2. 用 Top 1 或 Top 2 跑一遍，**只当交叉检查**：看它有没有指出你漏掉的；它给的它自己也说不清位置的，一律丢掉。
3. 从合集里挑 3–4 条，按 `位置 + 问题 + 建议动作` 各压成一句话。
4. 过一遍 Top 4 去 AI 味，外加人工三查：无加粗、无破折号、无"总体而言/综上所述"、无三项排比、无"未来工作可以进一步"。
5. 接收判断按同事标准走：实验齐全 + 图质量不错 + 无明显 AI 痕迹（尤其图）→ 可接收。

### 三条红线（写进流程，别靠记）
1. **不要把整份 PDF 传给云端模型**——ARR 明令禁止把机密材料交给非隐私保护的生成式工具；ICML 用 PDF 隐藏水印实测抓到 795 条违规评审。
2. **不要让模型产出最终文字**——ICLR/ICML 的处罚落在"LLM 生成的评审"，不落在"用 LLM 帮你理解论文"。ICML 的 Policy B 明确允许的只有两件事：帮助理解论文与相关工作、润色评审。
3. **先查会议政策再动手**——同一件事在 NeurIPS 2026（除官方实验外一律不许）、ICML（二选一）、ARR（禁初稿、许 paraphrase）下结论不同。

---

## 附：未核实 / 存疑清单

1. **skills.sh / SkillsMP / skills.rest 的审稿类条目排名与安装量**：站点动态渲染，抓取只拿到导航壳，未能取得结构化列表。skills.rest 上 `peer-review-assistant` 页面存在但内容未逐条核实。
2. **Pangram Labs 称 ICLR 2026 有 21% 评审为 AI 生成**：来自第三方博客（pebblous.ai）转述，**未在 ICLR 官方博客中找到对应数字**，ICLR 官方文只写了政策与后果，没给比例。
3. **coarse.ink**：lcrawfurd 仓库和 arXiv 2606.19749 均提到它是开源 agentic review 系统，但**未能定位到其 GitHub 仓库**，star/更新时间未核实。
4. **小红书、B 站、微信公众号的中文审稿工作流经验**：受平台风控与登录墙限制，本次只拿到知乎/CSDN。第 3 节的中文社区结论主要基于知乎问答与 CSDN 博客的可抓取内容，**社媒短视频侧的做法未覆盖**。
5. **知乎正文**：`zhuanlan.zhihu.com` 页面返回 403，第 3 节引用的知乎内容来自搜索索引摘要而非正文原文，个别措辞可能与原文有出入。
6. **Imbad0202/academic-research-skills 的 47,621★**：数字来自 GitHub API 实测，但对一个 2026-02 创建的仓库而言异常之高，是否存在刷量未做进一步核查；其 license 为 NOASSERTION。
7. **各 skill 的实际输出质量**：本次全部为静态阅读（README / SKILL.md / prompt 文件），**没有任何一个实际跑过稿子**，"是否适合轻量场景"是基于其流程设计的判断，不是实测。
8. **AI 生成图片/图表痕迹的检测**：不在本次检索范围内（任务未要求），未找到对口 skill；若需要另开一条线。
