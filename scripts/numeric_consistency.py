#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""numeric_consistency.py —— 第 10 层数值一致性对账（零网络、零 LLM）。

抓摘要与结论/讨论里的数字，在正文逐页搜同一数字（忽略 `%`，允许小数位差一位的近似），
列出「摘要/结论数字 → 出现页码」与「只在摘要/结论出现、正文找不到」的数字。
若本机有 pdfplumber，再抽全部表格里的数字做候选匹配，标出所在页与表号。

依赖：/opt/homebrew/bin/pdftotext（必需）；pdfplumber（可选，缺了自动降级）。
用法：
    python3 scripts/numeric_consistency.py PAPER.pdf [-o out.md] [--no-tables]

合规：零网络、零 LLM，档一（全禁）下也可运行。
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

PDFTOTEXT_CANDIDATES = ["/opt/homebrew/bin/pdftotext", "/usr/local/bin/pdftotext"]
PDFINFO_CANDIDATES = ["/opt/homebrew/bin/pdfinfo", "/usr/local/bin/pdfinfo"]


def find_tool(name, candidates):
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return shutil.which(name)


def die(msg, code=1):
    sys.stderr.write("错误：%s\n" % msg)
    sys.exit(code)


# --------------------------------------------------------------------------
# 抽取
# --------------------------------------------------------------------------

def page_count(pdf_path, pdftotext):
    pdfinfo = find_tool("pdfinfo", PDFINFO_CANDIDATES)
    if pdfinfo:
        try:
            out = subprocess.run([pdfinfo, pdf_path], capture_output=True, text=True, timeout=60)
            m = re.search(r"^Pages:\s+(\d+)", out.stdout, re.M)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    n = 0
    while n < 2048:
        r = subprocess.run([pdftotext, "-f", str(n + 1), "-l", str(n + 1), pdf_path, "-"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            break
        n += 1
    return n


def extract_pages(pdf_path, pdftotext, n_pages):
    pages = [""]
    for n in range(1, n_pages + 1):
        r = subprocess.run([pdftotext, "-layout", "-f", str(n), "-l", str(n), pdf_path, "-"],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            sys.stderr.write("提示：第 %d 页抽取失败，按空页处理。\n" % n)
        pages.append(r.stdout if r.returncode == 0 else "")
    return pages


NUM_RE = re.compile(r"(?<![A-Za-z0-9.,])([±~≈]?\s?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s?(%|×)?(?!\d)")
CITE_GROUP_RE = re.compile(r"\[[\d,;\s–\-]+\]")
ABBREV = ("e.g.", "i.e.", "et al.", "cf.", "vs.", "Fig.", "Eq.", "approx.", "Ref.", "No.")


def numbers_in(text, drop_citations=True):
    """返回 [(raw, value, unit, decimals)]。"""
    if drop_citations:
        text = CITE_GROUP_RE.sub(" ", text)
    out = []
    for m in NUM_RE.finditer(text):
        core = m.group(1).replace(",", "").replace(" ", "").lstrip("±~≈")
        try:
            val = float(core)
        except ValueError:
            continue
        dec = len(core.split(".")[1]) if "." in core else 0
        out.append((m.group(0).strip(), val, m.group(2) or "", dec))
    return out


def numbers_close(a, da, b, db):
    """相等，或小数位数相差 ≤1 且在较少的那个位数上四舍五入后相等（`%` 不参与比较）。"""
    if a == b:
        return True
    if abs(da - db) > 1:
        return False
    nd = min(da, db)
    return round(a, nd) == round(b, nd)


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
# 定位摘要与结论
# --------------------------------------------------------------------------

def flat_lines(pages):
    out = []
    for p in range(1, len(pages)):
        for t in pages[p].split("\n"):
            out.append((p, t))
    return out


def slice_by(lines, start_re, stop_res, max_len=200):
    start = None
    for i, (p, t) in enumerate(lines):
        if start is None and start_re.match(t.strip()):
            start = i + 1
            continue
        if start is not None:
            for sr in stop_res:
                if sr.match(t.strip()):
                    return start, i
    if start is None:
        return None, None
    return start, min(len(lines), start + max_len)


ABSTRACT_START = re.compile(r"^(Abstract|ABSTRACT)\s*$")
INTRO_START = re.compile(r"^\s*(1\.?\s+)?Introduction\s*$", re.I)
CONC_START = re.compile(r"^\s*\d?\.?\s*(Discussion|Conclusions?|Concluding Remarks)\s*$")
REFS_START = re.compile(r"^(References|REFERENCES|Bibliography|Acknowledg\w*)\s*$")


def collect_source_numbers(lines, start, end, label):
    """把一段文本里的数字按句子收集，返回列表。"""
    rows = []
    if start is None:
        return rows
    # 剔除只含页码的行，否则页眉页脚数字会被当成正文数字
    text = " ".join(t.strip() for _, t in lines[start:end]
                    if not re.match(r"^\s*\d{1,3}\s*$", t))
    page = lines[start][0] if start < len(lines) else None
    seen = set()
    for sent in sentences(text):
        for raw, val, unit, dec in numbers_in(sent):
            key = (round(val, 6), unit)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"where": label, "raw": raw, "value": val, "unit": unit,
                         "dec": dec, "sentence": sent, "page": page})
    return rows


# --------------------------------------------------------------------------
# 表格（pdfplumber 可选）
# --------------------------------------------------------------------------

CAPTION_RE = re.compile(r"^\s{0,40}(?:Supplementary\s+)?(Table|Tab\.)\s*(S?\d{1,3})\s*[:.]", re.M)


def table_numbers(pdf_path, pages_text, strategy="lines"):
    """返回 [(page, table_label, cell_text, value, dec)]；pdfplumber 缺失时返回 None。"""
    try:
        import pdfplumber           # noqa
    except Exception:
        return None
    settings = None
    if strategy == "text":
        settings = {"vertical_strategy": "text", "horizontal_strategy": "text"}
    cells = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pno, page in enumerate(pdf.pages, 1):
                try:
                    tables = page.extract_tables(settings) if settings else page.extract_tables()
                except Exception as e:
                    sys.stderr.write("提示：第 %d 页表格抽取失败（%s）。\n" % (pno, e))
                    continue
                if not tables:
                    continue
                caps = CAPTION_RE.findall(pages_text[pno] if pno < len(pages_text) else "")
                for ti, tbl in enumerate(tables):
                    if len(caps) == len(tables):
                        label = "%s%s" % ("Tab", caps[ti][1])
                    elif len(caps) == 1:
                        label = "Tab%s" % caps[0][1]
                    else:
                        label = "表#%d" % (ti + 1)
                    for row in tbl:
                        for cell in row:
                            if not cell:
                                continue
                            txt = re.sub(r"\s+", " ", str(cell)).strip()
                            for raw, val, unit, dec in numbers_in(txt, drop_citations=False):
                                cells.append((pno, label, txt[:60], val, dec))
    except Exception as e:
        sys.stderr.write("提示：pdfplumber 打开 PDF 失败（%s），跳过表格匹配。\n" % e)
        return None
    return cells


# --------------------------------------------------------------------------

def md_cell(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().replace("|", "\\|")


def clip(s, n=180):
    s = md_cell(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser(
        description="第 10 层数值一致性：摘要/结论数字 ↔ 正文 ↔ 表格。零网络、零 LLM。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：python3 scripts/numeric_consistency.py paper.pdf -o numeric.md")
    ap.add_argument("pdf", help="输入 PDF 路径")
    ap.add_argument("-o", "--output", default="-", help="输出 Markdown，默认 stdout")
    ap.add_argument("--no-tables", action="store_true", help="即使装了 pdfplumber 也不抽表格")
    ap.add_argument("--table-strategy", choices=("lines", "text"), default="lines",
                    help="pdfplumber 切表策略：lines（默认，靠框线，漏无框线表）/ "
                         "text（靠文字对齐，能捞回无框线表但会把正文段落误切成表，噪声大）")
    args = ap.parse_args()

    if not os.path.isfile(args.pdf):
        die("找不到 PDF：%s" % args.pdf)
    pdftotext = find_tool("pdftotext", PDFTOTEXT_CANDIDATES)
    if not pdftotext:
        die("找不到 pdftotext。macOS 装法：brew install poppler。")

    n = page_count(args.pdf, pdftotext)
    if n < 1:
        die("无法确定页数，PDF 可能损坏或被加密。")
    pages = extract_pages(args.pdf, pdftotext, n)
    if not any(p.strip() for p in pages):
        die("全部页面抽不出文本，可能是扫描件；本脚本不做 OCR。")
    lines = flat_lines(pages)

    a0, a1 = slice_by(lines, ABSTRACT_START, [INTRO_START], max_len=80)
    c0, c1 = slice_by(lines, CONC_START, [REFS_START], max_len=200)
    src = collect_source_numbers(lines, a0, a1, "摘要")
    src += collect_source_numbers(lines, c0, c1, "结论/讨论")

    src_pages = set(r["page"] for r in src if r["page"])
    tbl = None if args.no_tables else table_numbers(args.pdf, pages, args.table_strategy)

    out = []
    w = out.append
    w("# 第 10 层 数值一致性对账：%s" % os.path.basename(args.pdf))
    w("")
    w("- 生成方式：`scripts/numeric_consistency.py`，零网络零 LLM")
    w("- 页数 %d ／ 摘要定位 %s ／ 结论定位 %s"
      % (n,
         ("p%d" % lines[a0][0]) if a0 is not None else "**失败**",
         ("p%d" % lines[c0][0]) if c0 is not None else "**失败**"))
    w("- 表格抽取：%s" % ("跳过（--no-tables）" if args.no_tables else
                      ("pdfplumber 可用（策略 %s），命中 %d 个含数字单元格"
                       % (args.table_strategy, len(tbl))) if tbl is not None else
                      "**pdfplumber 未安装，已降级**（`pip3 install pdfplumber` 可开启表格匹配）"))
    w("- 匹配规则：忽略 `%`，小数位数相差 ≤1 时按较少位数四舍五入比较。年份、编号、页码会混入，须人工剔除。")
    w("")

    if not src:
        w("> 摘要与结论都没定位到，或其中没有数字。检查 PDF 的节标题排版。")
    w("## 摘要 / 结论数字 → 正文出现页码")
    w("")
    w("| anchor | fact | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|")
    missing = []
    for r in src:
        hits = []
        for p in range(1, n + 1):
            if p in src_pages:
                continue
            for _, v, _u, d in numbers_in(pages[p]):
                if numbers_close(r["value"], r["dec"], v, d):
                    hits.append(p)
                    break
        if hits:
            loc = "正文出现于 " + ", ".join("p%d" % p for p in hits[:20]) + (" 等" if len(hits) > 20 else "")
        else:
            loc = "**正文未找到**"
            missing.append(r)
        w("| p%s %s | 数字 `%s`（%s）／ 所在句：%s ／ %s |  |  |  |  |"
          % (r["page"], r["where"], md_cell(r["raw"]), r["where"], clip(r["sentence"], 160), loc))
    w("")

    w("## 只在摘要/结论出现、正文找不到的数字")
    w("")
    if missing:
        for r in missing:
            w("- `%s`（%s，p%s）：%s" % (md_cell(r["raw"]), r["where"], r["page"], clip(r["sentence"], 160)))
        w("")
        w("> 常见原因：正文写成了另一种精度或单位；数字只出现在图里（文本管线丢图）；确实对不上。三种都要翻原 PDF 分辨。")
    else:
        w("- 无。全部摘要/结论数字都能在正文找到近似匹配。")
    w("")

    if tbl:
        w("## 表格数字候选匹配（pdfplumber）")
        w("")
        w("| anchor | fact | judgement | severity | confidence | action |")
        w("|---|---|---|---|---|---|")
        any_row = False
        for r in src:
            ms = []
            for (pno, label, cell, val, dec) in tbl:
                if numbers_close(r["value"], r["dec"], val, dec):
                    tag = "p%d %s（单元格 `%s`）" % (pno, label, md_cell(cell))
                    if tag not in ms:
                        ms.append(tag)
            if ms:
                any_row = True
                w("| p%s %s | 数字 `%s` 在表格中的候选位置：%s |  |  |  |  |"
                  % (r["page"], r["where"], md_cell(r["raw"]), clip("；".join(ms[:8]), 400)))
        if not any_row:
            w("| anchor:none | 摘要/结论数字在抽到的表格里都没有候选匹配 |  |  |  |  |")
        w("")
        w("> pdfplumber 的 `extract_tables` 对无框线表格会漏抽或错切；表号是按页内 caption 猜的，须核对。")
        w("")

    w("---")
    w("")
    w("预算提醒：第 10 层写进意见的条目 ≤ 8 条（规格 §3）。以上全是**候选**，未经人工确认不得进意见。")
    w("")

    md = "\n".join(out)
    if args.output == "-":
        sys.stdout.write(md)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        sys.stderr.write("已写出 %s\n" % args.output)
    sys.stderr.write("统计：页数 %d ／ 摘要+结论数字 %d 个 ／ 正文找不到 %d 个 ／ 表格数字单元格 %s\n"
                     % (n, len(src), len(missing), "未抽取" if tbl is None else str(len(tbl))))


if __name__ == "__main__":
    main()
