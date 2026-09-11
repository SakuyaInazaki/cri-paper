#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf_skeleton.py —— 论文卡骨架生成器（零网络、零 LLM）。

按 docs/paper-decomposition-spec-v1.md 生成第 1 / 2 / 6 / 7 / 10 层的**事实骨架**：
只抽取，不判断。judgement / severity / confidence / action 四栏一律留空给人填。

依赖：/opt/homebrew/bin/pdftotext（poppler）。无第三方包。
用法：
    python3 scripts/pdf_skeleton.py PAPER.pdf [-o paper-card-skeleton.md]

合规：本脚本零网络、零 LLM，档一（全禁）下也可运行。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date

# --------------------------------------------------------------------------
# 0. pdftotext 定位与逐页抽取
# --------------------------------------------------------------------------

PDFTOTEXT_CANDIDATES = [
    "/opt/homebrew/bin/pdftotext",
    "/usr/local/bin/pdftotext",
]


def find_tool(name, candidates):
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    found = shutil.which(name)
    if found:
        return found
    return None


def die(msg, code=1):
    sys.stderr.write("错误：%s\n" % msg)
    sys.exit(code)


def page_count(pdf_path, pdftotext):
    """优先用 pdfinfo；没有就用二分探测 pdftotext 的可抽页范围。"""
    pdfinfo = find_tool("pdfinfo", ["/opt/homebrew/bin/pdfinfo", "/usr/local/bin/pdfinfo"])
    if pdfinfo:
        try:
            out = subprocess.run([pdfinfo, pdf_path], capture_output=True, text=True, timeout=60)
            m = re.search(r"^Pages:\s+(\d+)", out.stdout, re.M)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    # 兜底：逐步倍增探测
    def has_page(n):
        try:
            r = subprocess.run([pdftotext, "-f", str(n), "-l", str(n), pdf_path, "-"],
                               capture_output=True, text=True, timeout=120)
            return r.returncode == 0
        except Exception:
            return False

    hi = 1
    while has_page(hi) and hi < 4096:
        hi *= 2
    lo = hi // 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if has_page(mid):
            lo = mid
        else:
            hi = mid
    return lo


def extract_pages(pdf_path, pdftotext, n_pages):
    """逐页 pdftotext -layout -f N -l N，返回 1-based 的页文本列表（下标 0 是占位）。"""
    pages = [""]
    for n in range(1, n_pages + 1):
        try:
            r = subprocess.run([pdftotext, "-layout", "-f", str(n), "-l", str(n), pdf_path, "-"],
                               capture_output=True, text=True, timeout=180)
            pages.append(r.stdout if r.returncode == 0 else "")
            if r.returncode != 0:
                sys.stderr.write("提示：第 %d 页抽取失败，按空页处理。\n" % n)
        except Exception as e:
            sys.stderr.write("提示：第 %d 页抽取异常（%s），按空页处理。\n" % (n, e))
            pages.append("")
    return pages


# --------------------------------------------------------------------------
# 1. 文档模型：带页码与节号的扁平行表
# --------------------------------------------------------------------------

HEADING_RE = re.compile(r"^\s{0,20}(\d+(?:\.\d+){0,3})\.?\s+([A-Z][A-Za-z].{0,70})$")
APPENDIX_HEAD_RE = re.compile(r"^\s{0,20}(Appendix\s+[A-Z](?:\.\d+)*)\s*[:.]?\s+(\S.{0,70})?$")


class Line(object):
    __slots__ = ("page", "text", "section")

    def __init__(self, page, text, section):
        self.page = page
        self.text = text
        self.section = section


class Doc(object):
    def __init__(self, pages):
        self.pages = pages
        self.n_pages = len(pages) - 1
        self.lines = []
        cur_sec = ""
        for p in range(1, self.n_pages + 1):
            for raw in pages[p].split("\n"):
                m = HEADING_RE.match(raw.rstrip())
                if m and len(raw.strip()) < 90:
                    cur_sec = m.group(1)
                else:
                    ma = APPENDIX_HEAD_RE.match(raw.rstrip())
                    if ma:
                        cur_sec = ma.group(1).replace("Appendix ", "App ")
                self.lines.append(Line(p, raw, cur_sec))

    def anchor(self, idx, extra=""):
        ln = self.lines[idx]
        a = "p%d" % ln.page
        if ln.section:
            a += " §%s" % ln.section
        if extra:
            a += " " + extra
        return a

    def full_text(self):
        return "\n".join(l.text for l in self.lines)

    def iter_pages(self):
        for p in range(1, self.n_pages + 1):
            yield p, self.pages[p]


# --------------------------------------------------------------------------
# 2. 小工具
# --------------------------------------------------------------------------

def md_cell(s):
    """把任意文本压成一行 markdown 表格单元格。"""
    s = re.sub(r"\s+", " ", (s or "")).strip()
    s = s.replace("|", "\\|")
    return s


def clip(s, n=220):
    s = md_cell(s)
    return s if len(s) <= n else s[: n - 1] + "…"


ABBREV = ("e.g.", "i.e.", "et al.", "cf.", "vs.", "Fig.", "Eq.", "approx.", "resp.",
          "Ref.", "No.", "Dr.", "Prof.", "St.", "Inc.")


def first_sentence(text):
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", text)
    out = parts[0] if parts else text
    i = 1
    while i < len(parts) and out.endswith(ABBREV):
        out = out + " " + parts[i]
        i += 1
    return out


def sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", text)
    out, buf = [], ""
    for s in raw:
        buf = (buf + " " + s).strip() if buf else s
        if not buf.endswith(ABBREV):
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


# --------------------------------------------------------------------------
# 3. 第 1 层：元信息与版面
# --------------------------------------------------------------------------

URL_RE = re.compile(r"https?://[^\s,;)\]}>'\"]+", re.I)
CODE_HOST_RE = re.compile(r"(github\.com|gitlab\.com|huggingface\.co|github\.io|bitbucket\.org)", re.I)
ANON_WORD_RE = re.compile(r"(Acknowledg\w*|funded by|funding from|supported by (?:a |an |the )?(?:grant|NSF|NIH|DARPA|ONR)|"
                          r"grant no\.?|we thank)", re.I)
SUPP_RE = re.compile(r"(Supplementary|Appendix)\b")
CHECKLIST_RE = re.compile(r"\bchecklist\b", re.I)
LIMIT_RE = re.compile(r"\b[Ll]imitations?\b")
DATA_AVAIL_RE = re.compile(r"(data availability|code availability|availability statement)", re.I)


def scan_layer1(doc):
    """返回若干 (item, fact, anchors) 三元组。"""
    hits = {}

    def add(key, fact, idx):
        hits.setdefault(key, []).append((fact, idx))

    for i, ln in enumerate(doc.lines):
        t = ln.text
        if not t.strip():
            continue
        for m in URL_RE.finditer(t):
            u = m.group(0).rstrip(".,);")
            if CODE_HOST_RE.search(u):
                add("code_link", u, i)
        if SUPP_RE.search(t):
            add("supp", SUPP_RE.search(t).group(0), i)
        if CHECKLIST_RE.search(t):
            add("checklist", clip(t, 120), i)
        if LIMIT_RE.search(t):
            add("limitations", clip(t, 120), i)
        if DATA_AVAIL_RE.search(t):
            add("data_avail", clip(t, 120), i)
        m = ANON_WORD_RE.search(t)
        if m:
            add("anon", "命中词 `%s`：%s" % (m.group(0), clip(t, 120)), i)
    return hits


def count_references(doc):
    """从 References 标题起统计条目数，并切出原始条目列表。"""
    start = None
    for i, ln in enumerate(doc.lines):
        s = ln.text.strip()
        if re.match(r"^(References|REFERENCES|Bibliography)\s*$", s):
            start = i
    if start is None:
        return 0, [], None
    # 终止：附录/补充材料大标题，或文末。附录标题既可能是 "Appendix A Prompts"，
    # 也可能只是 "A     Agent Prompts" 这种单字母编号标题（本仓库实测踩过）。
    end = len(doc.lines)
    for i in range(start + 1, len(doc.lines)):
        s = doc.lines[i].text.strip()
        if i <= start + 5 or len(s) > 80:
            continue
        if (re.match(r"^(Appendix\s+[A-Z]\b|Supplementary\s+(Material|Information))", s)
                or re.match(r"^[A-Z](?:\.|\s{2,})\s*[A-Z][A-Za-z]", s)):
            end = i
            break

    entries = []       # (label, text, page)
    cur_label, cur_buf, cur_page = None, [], None
    num_re = re.compile(r"^\s*\[(\d{1,3})\]\s*(.*)$")
    alt_re = re.compile(r"^\s*(\d{1,3})\.\s+([A-Z].*)$")
    last_num = 0
    for i in range(start + 1, end):
        ln = doc.lines[i]
        s = ln.text.rstrip()
        if not s.strip():
            continue
        if re.match(r"^\s*\d{1,3}\s*$", s):     # 页码行
            continue
        m = num_re.match(s) or alt_re.match(s)
        if m and int(m.group(1)) <= last_num:
            # 编号不再递增：说明已经越过参考文献表，进了附录里的编号列表，停
            break
        if m:
            if cur_label is not None:
                entries.append((cur_label, " ".join(cur_buf), cur_page))
            cur_label, cur_buf, cur_page = m.group(1), [m.group(2).strip()], ln.page
            last_num = int(m.group(1))
        elif cur_label is not None:
            cur_buf.append(s.strip())
    if cur_label is not None:
        entries.append((cur_label, " ".join(cur_buf), cur_page))
    return len(entries), entries, doc.lines[start].page


# --------------------------------------------------------------------------
# 4. 第 2 层：候选贡献句
# --------------------------------------------------------------------------

CONTRIB_PATTERNS = [
    (r"\bcontributions?\b", "contribution"),
    (r"\bwe propose\b", "we propose"),
    (r"\bwe present\b", "we present"),
    (r"\bwe introduce\b", "we introduce"),
    (r"\bour main\b", "our main"),
    (r"\bwe develop(?:ed)?\b", "we develop"),
    (r"\bwe show\b", "we show"),
]
BULLET_RE = re.compile(r"^\s*(?:[•·▪∙\-–—*]|\(\d+\)|\d+[.)])\s+(\S.*)$")


def find_intro_range(doc):
    """返回 (start_idx, end_idx)；找不到就退化为前 25% 的行。"""
    start = end = None
    for i, ln in enumerate(doc.lines):
        s = ln.text.strip()
        if start is None and re.match(r"^\s*(1\.?\s+)?Introduction\s*$", s, re.I):
            start = i
        elif start is not None and HEADING_RE.match(ln.text.rstrip()):
            m = HEADING_RE.match(ln.text.rstrip())
            if m and "." not in m.group(1) and m.group(1) != "1":
                end = i
                break
    if start is None:
        return 0, max(1, len(doc.lines) // 4)
    if end is None:
        end = min(len(doc.lines), start + 400)
    return start, end


def collect_contributions(doc, limit=10):
    start, end = find_intro_range(doc)
    results = []
    seen = set()
    # 段落重组：把连续非空行拼成段，记录起始行号
    para, para_start = [], None
    paras = []
    for i in range(start, end):
        t = doc.lines[i].text
        if t.strip():
            if para_start is None:
                para_start = i
            para.append(t.strip())
        else:
            if para:
                paras.append((para_start, " ".join(para)))
            para, para_start = [], None
    if para:
        paras.append((para_start, " ".join(para)))

    contrib_bullet_mode = False
    for idx, text in paras:
        # 紧跟 "contributions" 之后的项目符号行
        if BULLET_RE.match(doc.lines[idx].text) and contrib_bullet_mode:
            s = first_sentence(BULLET_RE.match(doc.lines[idx].text).group(1) if BULLET_RE.match(doc.lines[idx].text) else text)
            key = s[:60]
            if key not in seen:
                seen.add(key)
                results.append((idx, clip(text, 300), "contributions 后的项目符号"))
            continue
        for sent in sentences(text):
            for pat, label in CONTRIB_PATTERNS:
                if re.search(pat, sent, re.I):
                    key = re.sub(r"\W+", "", sent.lower())[:60]
                    if key in seen:
                        break
                    seen.add(key)
                    results.append((idx, clip(sent, 300), label))
                    break
        if re.search(r"\bcontributions?\b\s*[:：]?\s*$", text, re.I) or re.search(r"contributions? (?:are|of this paper)", text, re.I):
            contrib_bullet_mode = True
    return results[:limit]


# --------------------------------------------------------------------------
# 5. 第 6 层：图表骨架
# --------------------------------------------------------------------------

CAPTION_RE = re.compile(r"^\s{0,40}(?:Supplementary\s+|Supp\.\s+|Extended Data\s+)?"
                        r"(Figure|Fig\.|Table|Tab\.)\s*(S?\d{1,3})\s*[:.]\s*(\S.*)$")
# 正文引用允许 panel 字母（Figure 1A / Fig. 3B）
INTEXT_RE = re.compile(r"\b(Figures?|Fig\.|Figs\.|Tables?|Tab\.)\s*(S?\d{1,3})([A-H])?\b")


def norm_kind(word):
    w = word.lower().rstrip(".")
    if w.startswith("fig"):
        return "Fig"
    return "Tab"


def collect_figures(doc):
    caps = {}            # (kind, num) -> dict
    caption_line_idx = set()   # caption 首行与其续行，都不算正文引用
    for i, ln in enumerate(doc.lines):
        m = CAPTION_RE.match(ln.text.rstrip())
        if not m:
            continue
        caption_line_idx.add(i)
        kind, num, rest = norm_kind(m.group(1)), m.group(2), m.group(3)
        # 续行拼接直到空行或下一个 caption
        buf = [rest]
        j = i + 1
        while j < len(doc.lines) and j < i + 12:
            nxt = doc.lines[j].text
            if not nxt.strip():
                break
            if CAPTION_RE.match(nxt.rstrip()):
                break
            if re.match(r"^\s*\d{1,3}\s*$", nxt):
                break
            buf.append(nxt.strip())
            caption_line_idx.add(j)
            j += 1
        key = (kind, num)
        if key in caps:
            continue
        caps[key] = {
            "kind": kind, "num": num, "page": ln.page, "idx": i,
            "caption": first_sentence(" ".join(buf)),
            "section": doc.lines[i].section,
            "refs": [],
        }

    # 正文引用（排除 caption 行本身）
    for i, ln in enumerate(doc.lines):
        if i in caption_line_idx:
            continue
        for m in INTEXT_RE.finditer(ln.text):
            key = (norm_kind(m.group(1)), m.group(2))
            if key in caps:
                caps[key]["refs"].append(ln.page)
            else:
                caps.setdefault(key, {
                    "kind": key[0], "num": key[1], "page": None, "idx": i,
                    "caption": "(未找到 caption)", "section": "", "refs": [],
                })["refs"].append(ln.page)

    def sortkey(k):
        kind, num = k
        s = 1 if num.startswith("S") else 0
        n = int(num[1:]) if num.startswith("S") else int(num)
        return (0 if kind == "Fig" else 1, s, n)

    return [caps[k] for k in sorted(caps.keys(), key=sortkey)]


# --------------------------------------------------------------------------
# 6. 第 10 层：摘要数字
# --------------------------------------------------------------------------

NUM_RE = re.compile(r"(?<![A-Za-z0-9.,])([±~≈]?\s?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s?(%|×)?(?!\d)")
CITE_GROUP_RE = re.compile(r"\[[\d,;\s–\-]+\]")


def find_abstract(doc):
    start = end = None
    for i, ln in enumerate(doc.lines):
        s = ln.text.strip()
        if start is None and re.match(r"^(Abstract|ABSTRACT)\s*$", s):
            start = i + 1
        elif start is not None and re.match(r"^\s*(1\.?\s+)?Introduction\s*$", s, re.I):
            end = i
            break
    if start is None:
        return None, None
    if end is None:
        end = min(len(doc.lines), start + 80)
    return start, end


def find_conclusion(doc):
    start = end = None
    for i, ln in enumerate(doc.lines):
        s = ln.text.strip()
        if re.match(r"^\s*\d?\.?\s*(Discussion|Conclusions?|Concluding Remarks)\s*$", s):
            start = i
        if re.match(r"^(References|REFERENCES|Bibliography)\s*$", s) and start is not None and end is None:
            end = i
    if start is None:
        return None, None
    return start, (end if end else min(len(doc.lines), start + 200))


def numbers_in(text):
    """返回 [(raw, value, unit, decimals)]，已剔除方括号引用组。"""
    text = CITE_GROUP_RE.sub(" ", text)
    out = []
    for m in NUM_RE.finditer(text):
        raw = m.group(0).strip()
        core = m.group(1).replace(",", "").replace(" ", "").lstrip("±~≈")
        try:
            val = float(core)
        except ValueError:
            continue
        dec = len(core.split(".")[1]) if "." in core else 0
        out.append((raw, val, m.group(2) or "", dec))
    return out


def abstract_number_table(doc):
    a0, a1 = find_abstract(doc)
    if a0 is None:
        return []
    # 剔除只含页码的行，否则页眉页脚数字会被当成摘要数字
    text = " ".join(doc.lines[i].text.strip() for i in range(a0, a1)
                    if not re.match(r"^\s*\d{1,3}\s*$", doc.lines[i].text))
    page = doc.lines[a0].page
    rows = []
    seen = set()
    for sent in sentences(text):
        for raw, val, unit, dec in numbers_in(sent):
            key = (round(val, 6), unit)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"raw": raw, "value": val, "unit": unit, "dec": dec,
                         "sentence": sent, "page": page})
    return rows


def locate_number_in_body(doc, value, dec, skip_pages=()):
    """在正文里找同一数字（忽略 %、允许小数位差一位）的页码列表。"""
    hits = []
    for p, text in doc.iter_pages():
        if p in skip_pages:
            continue
        for raw, v, u, d in numbers_in(text):
            if numbers_close(value, dec, v, d):
                hits.append(p)
                break
    return sorted(set(hits))


def numbers_close(a, da, b, db):
    """相等，或小数位数相差 ≤1 且在较少的那个位数上四舍五入后相等。"""
    if a == b:
        return True
    if abs(da - db) > 1:
        return False
    nd = min(da, db)
    return round(a, nd) == round(b, nd)


# --------------------------------------------------------------------------
# 7. 输出
# --------------------------------------------------------------------------

# judgement | severity | confidence | action 四栏留空；行末不再补竖线
EMPTY6 = "  |  |  |  |"


def render(doc, pdf_path, layer1, refs_n, refs_entries, refs_page, contribs, figures, abs_rows):
    out = []
    w = out.append
    name = os.path.basename(pdf_path)
    w("# 论文卡骨架：%s" % name)
    w("")
    w("- 稿件标识：`%s`（如需匿名，替换为内部编号）" % name)
    w("- 合规档位与模式：__（档一 M / 档二 U / 档三 F，开始拆分前手填）__")
    w("- 生成日期：%s" % date.today().isoformat())
    w("- 生成方式：`scripts/pdf_skeleton.py`，零网络零 LLM，仅 `pdftotext -layout` 逐页抽取")
    w("- 说明：本文件**只含自动提取的事实**。`judgement / severity / confidence / action` 四栏一律空白，由人填写。")
    w("- 锚点写法见规格 §0：`p{页} §{节} {Fig|Tab|Eq|Thm|Alg|Ref}{号}`；页码为 PDF 物理页。")
    w("- 列结构按规格 §6（v1.1）裁定 1：默认六列，第 2 层加 `evidence_locator`，第 6 层十列；"
      "其余字段在 `fact` 栏按 `key=value; key=value` 打包，键名用规格原名。")
    w("")

    # ---- 第 1 层 ----
    w("## 第 1 层 元信息与版面")
    w("")
    w("| anchor | fact | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|")
    w("| p1-p%d | 页数：%d 页 |%s" % (doc.n_pages, doc.n_pages, EMPTY6))
    if refs_page:
        w("| p%d | 参考文献条数估计：%d 条（自 References 标题逐条切分） |%s" % (refs_page, refs_n, EMPTY6))
    else:
        w("| anchor:none | 参考文献条数估计：未找到 References 标题 |%s" % EMPTY6)

    def anchors_for(key, limit=6):
        items = layer1.get(key, [])
        pages = []
        for fact, idx in items:
            a = doc.anchor(idx)
            if a not in pages:
                pages.append(a)
        return pages[:limit], len(items)

    for key, label in (("supp", "检测到 Supplementary/Appendix"),
                       ("checklist", "检测到 Checklist"),
                       ("limitations", "检测到 Limitations"),
                       ("data_avail", "检测到 data/code availability 声明")):
        anc, n = anchors_for(key)
        if n:
            w("| %s | %s：全文命中 %d 处（anchor 栏列前 %d 处） |%s"
              % (md_cell("; ".join(anc)), label, n, len(anc), EMPTY6))
        else:
            w("| anchor:none | %s：未检测到 |%s" % (label, EMPTY6))

    links = layer1.get("code_link", [])
    if links:
        uniq = []
        for u, idx in links:
            if u not in [x[0] for x in uniq]:
                uniq.append((u, idx))
        for u, idx in uniq[:10]:
            w("| %s | 代码/模型链接：`%s` ／ 原行：%s |%s"
              % (doc.anchor(idx), md_cell(u), clip(doc.lines[idx].text, 160), EMPTY6))
    else:
        w("| anchor:none | 代码/数据链接：未检测到 github/gitlab/huggingface 链接 |%s" % EMPTY6)

    anon = layer1.get("anon", [])
    personal_repo = []
    for u, idx in links:
        m = re.search(r"github\.com/([A-Za-z0-9_.-]+)/", u)
        if m:
            personal_repo.append((u, idx, m.group(1)))
    if anon or personal_repo:
        for fact, idx in anon[:8]:
            w("| %s | 可能的匿名性破坏（措辞）：%s |%s" % (doc.anchor(idx), clip(fact, 160), EMPTY6))
        for u, idx, owner in personal_repo[:6]:
            w("| %s | 可能的匿名性破坏（指向具名仓库 owner=`%s`）：%s |%s"
              % (doc.anchor(idx), owner, md_cell(u), EMPTY6))
    else:
        w("| anchor:none | 可能的匿名性破坏：未检测到致谢/资金/具名仓库链接 |%s" % EMPTY6)
    w("")
    w("> 机械检测只给候选。双盲稿是否真被破坏、补充材料是否真存在，须翻原 PDF 确认。")
    w("")

    # ---- 第 2 层 ----
    w("## 第 2 层 贡献声明与证据定位")
    w("")
    w("候选贡献句（引言范围内，最多 10 条；`evidence_locator` 留空，由人逐条回填 §/Tab/Fig/Thm）。")
    w("")
    w("| anchor | fact | evidence_locator | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|---|")
    if contribs:
        for idx, sent, label in contribs:
            w("| %s | %s（命中模式：%s） |  |  |  |  |  |" % (doc.anchor(idx), md_cell(sent), label))
    else:
        w("| anchor:none | 未在引言范围内抓到贡献句，须手工补 |  |  |  |  |  |")
    w("")
    w("摘要数字表见第 10 层（规格 §3 第 2 层要求与第 10 层联动）。")
    w("")

    # ---- 第 6 层 ----
    w("## 第 6 层 图表逐张清单")
    w("")
    w("骨架自动生成：caption 首句、所在页、正文引用页列表。判断栏每图 ≤ 3 条，由人填。")
    w("列结构按规格 §6 裁定 1 的第 6 层十列。")
    w("")
    w("| fig_id | anchor | type | caption | cited_at | fact | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    unref = []
    for f in figures:
        tag = "%s%s" % (f["kind"], f["num"])
        if f["page"]:
            a = "p%d" % f["page"]
            if f["section"]:
                a += " §%s" % f["section"]
        else:
            a = "anchor:none"
        ftype = "Figure" if f["kind"] == "Fig" else "Table"
        refs = f["refs"]
        if refs:
            cited_at = ", ".join("p%d" % p for p in sorted(set(refs)))
            facts = ["cited_count=%d" % len(refs)]
        else:
            cited_at = "none"
            facts = ["cited_count=0", "note=未被正文引用"]
            unref.append(tag)
        if f["page"]:
            cap = clip(f["caption"], 260) if f["caption"] else "(caption 抓到但为空)"
        else:
            cap = "(未找到 caption)"
            facts.append("caption_found=no")
        w("| %s | %s | %s | %s | %s | %s |  |  |  |  |"
          % (tag, a, ftype, cap, cited_at, "; ".join(facts)))
    w("")
    w("- 共 %d 个图表编号；未被正文引用：%s" % (len(figures), ("、".join(unref) if unref else "无")))
    w("- 已知盲区：摘要上方的 teaser 图、跨行 caption、\"Figures 3 and 4\" 这类合并引用抓不全，须翻原 PDF 补。")
    w("- 图本身必须看原 PDF 页（视觉），文本管线丢图。")
    w("")

    # ---- 第 7 层 ----
    w("## 第 7 层 参考文献与相关工作")
    w("")
    w("从 References 起逐条切分的原始条目。核真开关默认关，`exists` 与 `attribution_ok` 按规格 §6 裁定 8 写 `未查`；")
    w("要核真跑 `scripts/check_refs.py`（它直接读本表的 `raw=` 字段）。")
    w("合规提醒：核真会向 Crossref/arXiv 外发引用指纹，**档一默认不运行**（规格 §3 第 7 层）。")
    w("")
    w("| anchor | fact | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|")
    if refs_entries:
        for label, text, page in refs_entries:
            anchor = ("p%s Ref%s" % (page, label)) if page else ("anchor:none Ref%s" % label)
            w("| %s | ref_id=Ref%s; raw=%s; exists=未查; attribution_ok=未查 |%s"
              % (anchor, label, md_cell(text), EMPTY6))
    else:
        w("| anchor:none | 未找到 References 标题或切不出条目 |%s" % EMPTY6)
    w("")

    # ---- 第 10 层 ----
    w("## 第 10 层 数值一致性")
    w("")
    w("摘要中的全部数字及其所在句子，以及该数字在正文各页的出现情况（候选匹配，须人工确认）。")
    w("`fact` 打包为 `abstract_number=…; sentence=…; body_pages=…`，正文找不到时 `body_pages=none`。")
    w("")
    w("| anchor | fact | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|")
    if abs_rows:
        for r in abs_rows:
            pages = locate_number_in_body(doc, r["value"], r["dec"], skip_pages=(r["page"],))
            if pages:
                loc = ", ".join("p%d" % p for p in pages[:20])
                if len(pages) > 20:
                    loc += " 等 %d 页" % len(pages)
            else:
                loc = "none"
            w("| p%d Abstract | abstract_number=%s; sentence=%s; body_pages=%s |%s"
              % (r["page"], md_cell(r["raw"]), clip(r["sentence"], 200), loc, EMPTY6))
    else:
        w("| anchor:none | 未定位到摘要，或摘要内无数字 |%s" % EMPTY6)
    w("")
    w("> 匹配规则：去千分位与 `%`，允许小数位差一位的近似。年份、编号、引用序号可能混入，须人工剔除。")
    w("> 更细的摘要↔结论↔表格对账见 `scripts/numeric_consistency.py`。")
    w("")

    w("---")
    w("")
    w("## 未生成的层")
    w("")
    w("第 3、4、5、8、9、11、12 层需要阅读理解，本脚本不生成，按 `templates/paper-card.md` 手填。")
    w("")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="从 PDF 生成论文卡骨架（第 1/2/6/7/10 层事实栏）。零网络、零 LLM。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：python3 scripts/pdf_skeleton.py paper.pdf -o paper-card-skeleton.md")
    ap.add_argument("pdf", help="输入 PDF 路径")
    ap.add_argument("-o", "--output", default="paper-card-skeleton.md", help="输出 Markdown（默认 paper-card-skeleton.md，写 - 输出到 stdout）")
    ap.add_argument("--max-contributions", type=int, default=10, help="贡献句上限（默认 10）")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        die("找不到 PDF：%s" % args.pdf)
    pdftotext = find_tool("pdftotext", PDFTOTEXT_CANDIDATES)
    if not pdftotext:
        die("找不到 pdftotext。macOS 装法：brew install poppler（脚本期望 /opt/homebrew/bin/pdftotext）。")

    n = page_count(args.pdf, pdftotext)
    if n < 1:
        die("无法确定页数，PDF 可能损坏或被加密。")
    sys.stderr.write("读取 %d 页…\n" % n)
    pages = extract_pages(args.pdf, pdftotext, n)
    if not any(p.strip() for p in pages):
        die("全部页面抽不出文本。可能是扫描件/纯图 PDF，本脚本不做 OCR。")

    doc = Doc(pages)
    layer1 = scan_layer1(doc)
    refs_n, refs_entries, refs_page = count_references(doc)
    contribs = collect_contributions(doc, args.max_contributions)
    figures = collect_figures(doc)
    abs_rows = abstract_number_table(doc)

    md = render(doc, args.pdf, layer1, refs_n, refs_entries, refs_page, contribs, figures, abs_rows)
    if args.output == "-":
        sys.stdout.write(md)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        sys.stderr.write("已写出 %s\n" % args.output)
    sys.stderr.write("统计：页数 %d ／ 参考文献 %d 条 ／ 图表 %d 个 ／ 贡献句 %d 条 ／ 摘要数字 %d 个\n"
                     % (n, refs_n, len(figures), len(contribs), len(abs_rows)))


if __name__ == "__main__":
    main()
