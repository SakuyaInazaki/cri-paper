# 三档合规政策速查

第 0 步用。判出档位，再判出模式，写进论文卡头部。
全部条目来自「见 survey/00 第一部分」与「见 survey/01 §2」，核对日期 2026-09-11。

## 档位与模式的对应

| 档位 | 口径 | 模式 |
|---|---|---|
| 第一档 | 评审任何环节都不许用 LLM，离线模型也点名禁了 | M 手填 |
| 第二档 | 隐私合规模型可以喂稿，只许用于理解与润色，不许让它评判 | U 理解 |
| 第三档 | 只许润色自己写的意见，并且要披露；其中口径宽到「辅助评审」且未禁止让模型列问题的，才可用 F | F 全辅助，其余按 U 或 M 收紧 |

「隐私合规」按 ICML 的定义是不拿日志数据训练并对数据留存有限制，举的例子是机构或企业的 API 订阅、明确关闭了训练数据使用的个人订阅、自托管模型（见 survey/01 §2）。这是 ICML 一家的定义，别的会议未必认，账户设置要用户自己核对。

## 逐家速查

| 机构 | 档位 | 原文要点 | 允许 | 禁止 | 要求披露 | 链接 | 核对日期 |
|---|---|---|---|---|---|---|---|
| NeurIPS 2025 | 介于第一档与第三档之间 | 审稿人 "must not share, discuss, or disclose any information related to submissions with anyone or any LLMs"；提交的代码不得分发给任何人或任何 LLM（见 survey/01 §2） | 不分享稿件的前提下用 LLM 理解概念；检查自己那份评审的语法与措辞 | 把稿件或其任何相关信息给任何 LLM | 未要求 | <https://neurips.cc/Conferences/2025/LLM> | 2026-09-11 |
| ICLR 2026 | 第三档 | 使用 LLM 必须披露并对输出负全责；不得做出虚假或误导性陈述、伪造数据、虚构引用；违反保密的 LLM 使用同时构成道德准则违规（见 survey/01 §2） | 披露前提下的使用 | 违反保密的用法；虚构引用 | 要求 | <https://blog.iclr.cc/2025/11/19/iclr-2026-response-to-llm-generated-papers-and-reviews/> | 2026-09-11 |
| ICML 2026 | 第二档（Policy B）；选 Policy A 的审稿人按第一档 | 审稿人二选一声明。Policy A 写 "Use of LLMs in any stage of reviewing is strictly prohibited"；Policy B 允许把稿件喂给隐私合规的 LLM（见 survey/01 §2） | 用 LLM 帮助理解论文与相关工作；润色已经写好的评审 | 五项：问优缺点；让它列评审要点；让它列评审提纲；让它写整份评审；让它替你拟给作者的问题。另禁止喂给非隐私合规的 LLM。原文没有把「总结论文」单列为禁止项（见 survey/01 §2） | 未要求，但要在系统里声明选 A 还是 B | <https://icml.cc/Conferences/2026/LLM-Policy> | 2026-09-11 |
| CVPR 2026 | 第一档 | "does not allow the use of Large Language Models or online chatbots such as ChatGPT in any part of the reviewing process"；理由里点名离线系统 "e.g., an offline system"（见 survey/01 §2） | 基于 LLM 的语法检查器可用于清晰度 | 用 LLM 生成评审内容；把论文或评审的实质内容交给 LLM；用其翻译评审；本地或离线模型同样不许 | 不适用 | <https://cvpr.thecvf.com/Conferences/2026/ReviewerGuidelines> | 2026-09-11 |
| ECCV 2026 | 第一档 | 与 CVPR 一致，并明确 "whether it is run locally or via an API"（见 survey/01 §2） | 用 LLM 做背景调研；检查短语法 | 评审任何环节用 LLM，本地跑也不行 | 不适用 | <https://eccv.ecva.net/Conferences/2026/ReviewerGuide> | 2026-09-11 |
| ACL / ARR | 第三档 | "The reviewer has to read the paper fully and write the content and argument of the review by themselves... it is not permitted to use generative assistance to create the first draft"；明文写连自己写的评审报告都不能传到非隐私保护的工具（见 survey/01 §2、survey/00 一） | 非英语母语者用写作助手做转述润色 | 用生成式工具产出评审初稿；把稿件或评审报告上传到非私有 AI 工具 | 要求（转述润色须可交代） | <https://aclrollingreview.org/reviewerguidelines> | 2026-09-11 |
| AAAI-26 | 未归档，按 M 处理 | 会议自己给每篇额外生成一份标注清楚的 AI 评审，同时要求人类审稿人不得复制 AI 评审的内容；未见对审稿人自用 LLM 的正面许可（见 survey/01 §1.1、§2） | 可对官方那份 AI 评审表示同意 | 复制官方 AI 评审的内容进自己的评审 | 未见条款 | <https://aaai.org/conference/aaai/aaai-26/instructions-for-aaai-26-reviewers/> | 2026-09-11 |
| Elsevier | 第一档，最严 | "Reviewers should not upload the material/manuscript or any part thereof into a generative AI tool"；并写 "should not be used by reviewers to assist in the review"，理由是评审所需的批判性思维超出该技术范围（见 survey/01 §2） | 无，连润色都不鼓励 | 上传稿件或其任何部分；用 AI 辅助评审本身 | 不适用 | <https://www.elsevier.com/about/policies-and-standards/the-use-of-generative-ai-and-ai-assisted-technologies-in-the-review-process> | 2026-09-11 |
| Springer Nature | 第三档，口径最宽 | "Peer reviewers may use secure or institutionally-approved AI tools to assist them"；同时 "should not upload manuscript content to unsecured or public AI systems"（见 survey/01 §2） | 用安全或机构批准的工具辅助评审，「辅助」没有被限定成只能润色 | 把稿件内容上传到不安全或公开的 AI 系统 | 要求独立评估并对评审内容负责 | <https://group.springernature.com/gp/group/ai/ai-guidance-for-our-researchers-and-communities> | 2026-09-11 |
| Wiley | 第三档 | 不得把稿件或其任何部分（含图与表）传进 GenAI 工具；允许用 AI 提升评审报告的表达质量，但 "must be transparently declared in the report"（见 survey/01 §2） | 润色评审报告的表达 | 上传稿件、图、表 | 要求，且要写在报告里 | <https://authors.wiley.com/Reviewers/journal-reviewers/tools-and-resources/review-confidentiality-policy.html> | 2026-09-11 |
| ACM | 第一档 | "Reviewers may not submit papers to LLMs, plagiarism detectors, summarizers, or other such tools"；"Reviewers may not use generative AI tools to write their reviews"（见 survey/01 §2） | 无正面许可条款 | 把论文交给 LLM 或任何不承诺保密的第三方系统；用生成式工具写评审 | 不适用 | <https://respect.acm.org/2026/index.php/policies-on-generative-ai-llms-and-related-tools/> | 2026-09-11 |
| NIH | 第一档 | NOT-OD-23-149："NIH prohibits NIH scientific peer reviewers from using natural language processors, large language models, or other generative Artificial Intelligence (AI) technologies for analyzing and formulating peer review critiques"，并修订了审稿人保密协议（见 survey/01 §2） | 无 | 用任何语言模型分析和撰写评审意见 | 不适用 | <https://grants.nih.gov/grants/guide/notice-files/NOT-OD-23-149.html> | 2026-09-11 |

## 两条兜底

**未列出的会议默认按 M 手填模式处理。** 表里没有这家，或者用户说不出会议名，就当第一档做：模型不读稿件，只跑本地脚本、给模板与清单。不要按「大概是第二档吧」推测，也不要拿同一出版商旗下别的期刊的口径套过来（Springer Nature 旗下具体期刊另有比集团指引更严的表述，见 survey/01 未核实清单第 2b 条）。

**政策会变，开审前重抓原页。** 本表是 2026-09-11 当天抓的，没有存快照，也没有对比往年版本。每年的会议指南都可能改口径，实际开审时把上面那一列链接打开核对一遍，两分钟。核对结果与本表不符时以原页为准，并回来改这张表。

## 两条不随档位变的规则

- 引用核真在第一档不可做。参考文献列表严格说也是稿件的一部分，而且 `check_refs.py` 外发的引用指纹在稿件日后发表时可以对上（见 survey/04 §4.1）。
- 交叉检查（让模型列问题清单）能不能做，取决于政策措辞而不是档位。ICML Policy B 明文禁止列评审要点、列提纲、拟问题，这一档整步跳过；Springer Nature 那种宽口径「辅助评审」措辞才可以做（见 survey/00 第三部分第 2 步）。
