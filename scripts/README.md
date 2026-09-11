# scripts/ —— 论文拆分的机械部分

三个单文件 Python 3 脚本，实现 `docs/paper-decomposition-spec-v1.md` §4 的"零依赖底座"与"轻依赖"两档。
**它们只产出 `fact` 栏，不产出 `judgement`。** 输出表格的 `judgement / severity / confidence / action` 一律留空，由人填。

实测记录见 [`../examples/2504.09737-README.md`](../examples/2504.09737-README.md)。

## 一张表看合规

| 脚本 | 网络 | LLM | 外发什么 | 档一（全禁）可用 |
|---|---|---|---|---|
| `pdf_skeleton.py` | 无 | 无 | — | 可 |
| `numeric_consistency.py` | 无 | 无 | — | 可 |
| `check_refs.py` | **有** | 无 | 参考文献的 DOI / arXiv ID（开 `--title-search` 时还有标题串）→ Crossref、arXiv | **默认不运行** |

`check_refs.py` 外发的不是稿件正文，而是**引用指纹**：某个 IP 在某时刻把这一组特定文献逐条查了一遍，
这组组合可以在稿件日后发表时对上（`survey/04` §4.1）。所以它启动时会先在 stderr 打一行合规提醒。

## 依赖

- **必需**：`pdftotext`（poppler）。脚本按 `/opt/homebrew/bin/pdftotext` → `/usr/local/bin` → `PATH` 顺序找；
  找不到会报错并提示 `brew install poppler`。
- **可选**：`pdfplumber`（只有 `numeric_consistency.py` 的表格匹配用）。没装会在输出头部标"已降级"并继续跑完其余部分。
- 其余全部标准库。三个脚本互不 import，可以单独拷走。
- 三个脚本都有 `--help`。

---

## 1. `pdf_skeleton.py` —— 论文卡骨架（第 1 / 2 / 6 / 7 / 10 层）

```bash
python3 scripts/pdf_skeleton.py PAPER.pdf [-o paper-card-skeleton.md] [--max-contributions N]
```

逐页跑 `pdftotext -layout -f N -l N`，页码即锚点里的 `p{页}`（PDF 物理页，从 1 起）。节号靠 `^\d+(\.\d+)* 标题` 行推断，
锚点形如 `p5 §4.2 Tab2`，配不上的写 `anchor:none`。

产出：

- **第 1 层**：页数、参考文献条数、Supplementary/Appendix、Checklist、Limitations、data/code availability、
  github/gitlab/huggingface 链接、匿名性破坏候选（`Acknowledg*`、`funded by`、`we thank`、指向具名 owner 的仓库链接），每项带页锚点。
- **第 2 层**：引言范围内的候选贡献句（`contribution` / `we propose` / `we present` / `we introduce` / `our main` / `we develop` / `we show`，
  以及 "contributions" 之后的项目符号行），默认最多 10 条，`evidence_locator` 栏留空给人回填。
- **第 6 层**：所有 `Figure N` / `Fig. N` / `Table N`（含 `S1` 这类补充编号）的 caption 首句 + 页码，按号排序去重；
  并统计每个编号在正文（排除 caption 块本身）的引用次数与页码，未被引用的标出。
- **第 7 层**：从 `References` 起逐条切分的原始条目，每条一行，anchor 写 `p{页} Ref{n}`，
  `fact` 打包成 `ref_id=Ref1; raw=<原始条目>; exists=未查; attribution_ok=未查`
  （核真开关默认关时按规格 §6 裁定 8 写"未查"），供 `check_refs.py` 直接读 `raw=` 字段。
  切分终止于附录标题（含 `A   Prompts` 这种单字母编号标题），并要求条目编号单调递增。
- **第 10 层**：摘要里的全部数字（含 `%`、`±`、`×`）及所在句子，以及每个数字在正文各页的出现页码。

输出是 Markdown，分节标题用规格 §3 的层号与层名。列结构按规格 §6（v1.1）裁定 1：
默认六列 `anchor | fact | judgement | severity | confidence | action`；第 2 层七列（多 `evidence_locator`）；
第 6 层十列 `fig_id | anchor | type | caption | cited_at | fact | judgement | severity | confidence | action`。
其余字段在 `fact` 栏按 `key=value; key=value` 打包，键名用规格原名。
第 3、4、5、8、9、11、12 层需要阅读理解，本脚本不生成。

**已知盲区**：摘要上方的 teaser 图抓不到；"Figures 3 and 4" 式合并引用只记前一个；
插图内部的文字会被 `pdftotext` 抽出来当正文；引文里提到的"别人论文的 Figure N"会混进图表清单；
PDF 里被渲染成空格的下划线会截断 URL。图本身必须看原 PDF 页，文本管线丢图。

## 2. `numeric_consistency.py` —— 第 10 层数值对账

```bash
python3 scripts/numeric_consistency.py PAPER.pdf [-o out.md] [--no-tables] [--table-strategy lines|text]
```

抓摘要与结论/讨论里的数字，在正文逐页搜同一数字，输出三块：

1. 「摘要/结论数字 → 正文出现页码」表；
2. 「只在摘要/结论出现、正文找不到」的数字清单；
3. 装了 `pdfplumber` 时，表格里所有数字的候选匹配（标出页与表号；表号按页内 `Table N:` caption 猜）。

匹配规则：去千分位、忽略 `%`；小数位数相差 ≤1 时按较少的位数四舍五入后比较（所以 `27` 与 `27.4` 会匹配上）。
纯页码行已被剔除，年份与编号仍会混入，**全部是候选，须人工确认**。

`--table-strategy text` 能捞回无框线表，但会把正文段落误切成表，噪声极大，只在明知需要时开。

## 3. `check_refs.py` —— 第 7 层引用核真（**会外发**）

```bash
python3 scripts/check_refs.py REFS.txt|skeleton.md \
    [--limit N] [--delay 1.0] [--timeout 20] \
    [--title-search] [--title-min-sim 0.6] [--polite EMAIL] [--offline] [-o out.md]
```

输入可以是 `pdf_skeleton.py` 产出的骨架（自动解析第 7 层表格行里的 `ref_id=` / `raw=` 打包字段，
也兼容旧版骨架的 ```` ```references ```` 代码块），也可以是 `[1] …` 形式的纯文本。

默认行为严格照规格 §3 第 7 层的"最小化做法"：

- 只提取 DOI（正则）与 arXiv ID；
- DOI 走 Crossref 公共池 `https://api.crossref.org/works/{doi}`，**不带 `mailto`**；
- arXiv ID 走 `https://export.arxiv.org/api/query?id_list=`；
- **逐条串行**，条间 `--delay` 秒（默认 1.0）；
- **不用标题搜索**。

输出每条两栏：

- `exists`：命中 / 未命中 / 无标识符 / 查询失败；
- `attribution_ok`：一致 / 部分核对 / 不一致 / 未核（拿不到可比对的姓氏或年份就是"未核"，不等于有问题）。

可选开关：

- `--title-search`：无标识符时用 Crossref `query.bibliographic` 按标题查。**这会多泄露一层（对方能看出你在核对）**，
  且 Crossref 总会返回最接近的一条，所以脚本加了词集相似度阈值 `--title-min-sim`（默认 0.6），低于阈值判为未命中。同名撞车仍挡不住。
- `--polite EMAIL`：走 polite pool，换取更高配额，代价是把邮箱写进对方日志。默认关。
- `--offline`：一个请求都不发，只做本地解析（抽 DOI / arXiv ID / 第一作者姓氏 / 年份）。用来先看看这篇稿子的引用表里到底有没有标识符。

**用之前先定档。** 档一默认不跑；非做不可时就用默认参数（DOI only、无 mailto、串行间隔），别开 `--title-search`。
另：GROBID 的 `consolidate*` 系列参数任何时候都保持关（它会自己去调 Crossref）。

---

## 输出怎么接下一步

三个脚本的输出都是可以直接粘进 `templates/paper-card.md` 的表格行。
顺序建议：`pdf_skeleton.py` 先跑（零网络，得到骨架与参考文献块）→ `numeric_consistency.py` 补第 10 层 →
定档允许时再跑 `check_refs.py` 补第 7 层。判断栏一律人填；机器标出的东西不逐条核实，不得写进审稿意见。
