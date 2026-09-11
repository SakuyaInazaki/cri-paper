#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_refs.py —— 第 7 层参考文献核真（会外发网络请求）。

按 docs/paper-decomposition-spec-v1.md §3 第 7 层的「最小化做法」实现：
只按 DOI 走 Crossref 公共池、arXiv ID 走 arXiv export API，默认不带 mailto，
逐条串行、条间 sleep，默认不用标题搜索。

输出每条：
  exists          命中 / 未命中 / 无标识符
  attribution_ok  第一作者姓氏与年份是否与原文条目一致；做不到标「未核」

依赖：仅标准库。
用法：
    python3 scripts/check_refs.py REFS.txt
    python3 scripts/check_refs.py paper-card-skeleton.md --limit 15
    python3 scripts/check_refs.py refs.txt --title-search --polite you@example.com

合规：本脚本向 Crossref / arXiv 外发「引用指纹」，档一（全禁）默认不应运行。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

COMPLIANCE_LINE = ("[合规提醒] 本操作向 Crossref/arXiv 外发本文的引用指纹"
                   "（哪些文献被逐条核对过），档一（全禁）默认不应运行。")

UA_PLAIN = "cri-paper-check-refs/1.0 (peer-review reference verification)"

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9<>]+", re.I)
ARXIV_RE = re.compile(r"(?:arxiv[:\s/]*(?:abs/)?|arxiv\.org/(?:abs|pdf)/)"
                      r"(\d{4}\.\d{4,5})(v\d+)?", re.I)
ARXIV_OLD_RE = re.compile(r"arxiv[:\s]*([a-z\-]+(?:\.[A-Z]{2})?/\d{7})", re.I)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


def die(msg, code=1):
    sys.stderr.write("错误：%s\n" % msg)
    sys.exit(code)


# --------------------------------------------------------------------------
# 输入解析
# --------------------------------------------------------------------------

def load_entries(path):
    """支持 pdf_skeleton.py 产出的 skeleton.md（取 ```references 块）与纯文本 refs.txt。"""
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError as e:
        die("读不了输入文件 %s：%s" % (path, e))

    # 形式 1（骨架 v1.1）：第 7 层表格行 `| p14 Ref1 | ref_id=Ref1; raw=…; exists=…; attribution_ok=… | …`
    packed = re.findall(r"ref_id=(\w+)\s*;\s*raw=(.*?)\s*;\s*exists=", raw)
    if packed:
        out = []
        for rid, body in packed:
            lbl = re.sub(r"^Ref", "", rid)
            body = body.replace("\\|", "|")
            body = re.sub(r"\s+", " ", body).strip()
            body = re.sub(r"([a-z])-\s+([a-z])", r"\1\2", body)
            if body:
                out.append((lbl, body))
        return out

    # 形式 2（骨架 v1.0 遗留）：```references 代码块
    block = None
    m = re.search(r"```references\s*\n(.*?)```", raw, re.S)
    if m:
        block = m.group(1)
    elif path.lower().endswith(".md"):
        sys.stderr.write("提示：%s 里既没有第 7 层的 ref_id=/raw= 表格行，也没有 ```references 代码块，"
                         "按纯文本逐条解析。\n" % path)
    text = block if block is not None else raw

    entries = []
    cur_label, cur_buf = None, []
    label_re = re.compile(r"^\s*\[(\d{1,3})\]\s*(?:\(p\d+\)\s*)?(.*)$")
    alt_re = re.compile(r"^\s*(\d{1,3})\.\s+([A-Z].*)$")
    for line in text.split("\n"):
        if not line.strip():
            if cur_label is not None and cur_buf:
                entries.append((cur_label, " ".join(cur_buf)))
                cur_label, cur_buf = None, []
            continue
        m = label_re.match(line) or alt_re.match(line)
        if m:
            if cur_label is not None:
                entries.append((cur_label, " ".join(cur_buf)))
            cur_label, cur_buf = m.group(1), [m.group(2).strip()]
        elif cur_label is not None:
            cur_buf.append(line.strip())
        else:
            # 没有编号的纯行：每行当一条
            entries.append((str(len(entries) + 1), line.strip()))
    if cur_label is not None and cur_buf:
        entries.append((cur_label, " ".join(cur_buf)))
    out = []
    for lbl, t in entries:
        t = re.sub(r"\s+", " ", t).strip()
        # 修掉 PDF 换行断词：“refine- ment” → “refinement”
        t = re.sub(r"([a-z])-\s+([a-z])", r"\1\2", t)
        if t:
            out.append((lbl, t))
    return out


def parse_local(entry_text):
    """从原文条目里抽 DOI / arXiv ID / 第一作者姓氏 / 年份 / 标题猜测。"""
    doi = None
    m = DOI_RE.search(entry_text)
    if m:
        doi = m.group(0).rstrip(".,;)")
    arxiv = None
    m = ARXIV_RE.search(entry_text)
    if m:
        arxiv = m.group(1)
    else:
        m = ARXIV_OLD_RE.search(entry_text)
        if m:
            arxiv = m.group(1)

    years = YEAR_RE.findall(entry_text)
    year = int(years[-1]) if years else None

    # 第一作者姓氏：取第一个 ", " 或 " and " 之前的人名块，末词当姓氏
    head = re.split(r",| and ", entry_text)[0].strip()
    head = re.sub(r"^\W+", "", head)
    surname = None
    if head and len(head) < 60:
        toks = [t for t in re.split(r"\s+", head) if t]
        if toks:
            cand = toks[-1].strip(".")
            if re.match(r"^[A-Z][A-Za-z'\-]{1,}$", cand):
                surname = cand

    # 标题猜测：按 ". " 切段，取第一段"小写词占比够高"的（作者块几乎全是首字母大写的人名）
    title = None
    parts = [p.strip() for p in re.split(r"\.\s+", entry_text)[1:]]
    for p in parts:
        if len(p) < 15:
            continue
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", p)
        if not words:
            continue
        low = sum(1 for w in words if w[0].islower())
        if low / float(len(words)) >= 0.4:
            title = p
            break
    if title is None:
        cands = [p for p in parts if 20 < len(p) < 250]
        title = max(cands, key=len) if cands else None
    if title:
        # 标题常以 ? 结尾，后面跟的是刊名/会议名，截掉
        m = re.match(r"^(.{15,200}?\?)\s", title)
        if m:
            title = m.group(1)
        title = title[:200].strip(" ,;")
    return {"doi": doi, "arxiv": arxiv, "year": year, "surname": surname, "title": title}


STOP = set("a an the of on in for and or to with by via is are we our this that at as from".split())


def title_similarity(a, b):
    """粗糙的词集 Jaccard，用来判断标题搜索返回的是不是同一篇。"""
    if not a or not b:
        return 0.0
    ta = set(w for w in re.findall(r"[a-z0-9]+", a.lower()) if w not in STOP and len(w) > 2)
    tb = set(w for w in re.findall(r"[a-z0-9]+", b.lower()) if w not in STOP and len(w) > 2)
    if not ta or not tb:
        return 0.0
    jac = len(ta & tb) / float(len(ta | tb))
    # 本地标题常被副标题/刊名截断，词数够多时再看包含度，避免把真命中判成未命中
    if min(len(ta), len(tb)) >= 4:
        jac = max(jac, len(ta & tb) / float(min(len(ta), len(tb))))
    return jac


# --------------------------------------------------------------------------
# 网络查询
# --------------------------------------------------------------------------

def http_get(url, timeout, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": UA_PLAIN, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def crossref_by_doi(doi, timeout, polite=None):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    if polite:
        url += "?mailto=" + urllib.parse.quote(polite)
    try:
        data = json.loads(http_get(url, timeout))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"status": "未命中", "note": "Crossref 404"}
        return {"status": "查询失败", "note": "HTTP %s" % e.code}
    except Exception as e:
        return {"status": "查询失败", "note": type(e).__name__}
    return {"status": "命中", "rec": normalize_crossref(data.get("message", {}))}


def crossref_by_title(title, timeout, polite=None):
    q = {"query.bibliographic": title, "rows": "1",
         "select": "title,author,issued,DOI,container-title"}
    if polite:
        q["mailto"] = polite
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(q)
    try:
        data = json.loads(http_get(url, timeout))
    except Exception as e:
        return {"status": "查询失败", "note": type(e).__name__}
    items = data.get("message", {}).get("items", [])
    if not items:
        return {"status": "未命中", "note": "标题搜索无结果"}
    return {"status": "命中(标题搜索)", "rec": normalize_crossref(items[0])}


def normalize_crossref(msg):
    title = (msg.get("title") or [""])[0]
    authors = msg.get("author") or []
    family = authors[0].get("family") if authors else None
    year = None
    for key in ("issued", "published-print", "published-online", "created"):
        dp = (msg.get(key) or {}).get("date-parts") or []
        if dp and dp[0] and dp[0][0]:
            year = dp[0][0]
            break
    return {"title": title, "family": family, "year": year,
            "id": msg.get("DOI", ""), "source": "Crossref"}


ATOM = "{http://www.w3.org/2005/Atom}"


def arxiv_by_id(aid, timeout):
    url = "https://export.arxiv.org/api/query?id_list=" + urllib.parse.quote(aid)
    try:
        body = http_get(url, timeout, accept="application/atom+xml")
        root = ET.fromstring(body)
    except Exception as e:
        return {"status": "查询失败", "note": type(e).__name__}
    entry = root.find(ATOM + "entry")
    if entry is None:
        return {"status": "未命中", "note": "arXiv 无此 id"}
    title_el = entry.find(ATOM + "title")
    title = re.sub(r"\s+", " ", (title_el.text or "").strip()) if title_el is not None else ""
    if not title or title.lower().startswith("error"):
        return {"status": "未命中", "note": "arXiv 返回 Error"}
    auth = entry.find(ATOM + "author")
    family = None
    if auth is not None:
        nm = auth.find(ATOM + "name")
        if nm is not None and nm.text:
            family = nm.text.strip().split()[-1]
    pub = entry.find(ATOM + "published")
    year = None
    if pub is not None and pub.text:
        try:
            year = int(pub.text[:4])
        except ValueError:
            year = None
    return {"status": "命中", "rec": {"title": title, "family": family, "year": year,
                                     "id": aid, "source": "arXiv"}}


# --------------------------------------------------------------------------
# 归属比对
# --------------------------------------------------------------------------

def check_attribution(local, rec):
    if not rec:
        return "未核", ""
    notes = []
    name_ok = None
    if local["surname"] and rec.get("family"):
        a = local["surname"].lower()
        b = rec["family"].lower()
        name_ok = (a == b) or a.endswith(b) or b.endswith(a)
        if not name_ok:
            notes.append("第一作者 原文=%s 远端=%s" % (local["surname"], rec["family"]))
    year_ok = None
    if local["year"] and rec.get("year"):
        d = abs(local["year"] - rec["year"])
        year_ok = d == 0
        if d == 1:
            notes.append("年份差 1（原文 %d / 远端 %d，预印本与正式发表常见）"
                         % (local["year"], rec["year"]))
            year_ok = None
        elif d > 1:
            notes.append("年份 原文=%d 远端=%d" % (local["year"], rec["year"]))
    if name_ok is None and year_ok is None:
        return "未核", "；".join(notes) or "原文条目里抽不出姓氏或年份"
    if name_ok is False or year_ok is False:
        return "不一致", "；".join(notes)
    if name_ok and year_ok:
        return "一致", "；".join(notes)
    return "部分核对", "；".join(notes) or ("只核了姓氏" if name_ok else "只核了年份")


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="参考文献核真：DOI 走 Crossref、arXiv ID 走 arXiv API，输出 exists 与 attribution_ok。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="合规：会外发引用指纹，档一默认不运行。示例：\n"
               "  python3 scripts/check_refs.py paper-card-skeleton.md --limit 15")
    ap.add_argument("refs", help="REFS.txt 或 pdf_skeleton.py 产出的 skeleton.md")
    ap.add_argument("--polite", metavar="EMAIL", default=None,
                    help="用 Crossref polite pool（把邮箱写进对方日志），默认关")
    ap.add_argument("--title-search", action="store_true",
                    help="无 DOI/arXiv ID 时用 query.bibliographic 按标题查，默认关")
    ap.add_argument("--title-min-sim", type=float, default=0.6, metavar="X",
                    help="标题搜索的最低词集相似度，低于此值判为未命中（默认 0.6）")
    ap.add_argument("--delay", type=float, default=1.0, help="条间 sleep 秒数，默认 1.0")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条，0 表示全部")
    ap.add_argument("--timeout", type=float, default=20.0, help="单次请求超时秒数，默认 20")
    ap.add_argument("--offline", action="store_true",
                    help="只做本地解析（抽 DOI/arXiv/姓氏/年份），一个网络请求都不发")
    ap.add_argument("-o", "--output", default="-", help="输出文件，默认 stdout")
    args = ap.parse_args()

    sys.stderr.write(COMPLIANCE_LINE + "\n")
    if not os.path.isfile(args.refs):
        die("找不到输入文件：%s" % args.refs)

    entries = load_entries(args.refs)
    if not entries:
        die("没解析出任何参考文献条目。检查输入格式（期望 `[1] ...` 或每行一条）。")
    if args.limit > 0:
        entries = entries[: args.limit]

    lines = []
    w = lines.append
    w("# 第 7 层 参考文献核真")
    w("")
    w("- 输入：`%s`，共核 %d 条%s" % (args.refs, len(entries),
                                  "（--limit 截断）" if args.limit else ""))
    w("- 模式：%s；标题搜索 %s；polite pool %s；条间 %.1fs"
      % ("离线（不发请求）" if args.offline else "DOI→Crossref / arXiv ID→arXiv export",
         "开" if args.title_search else "关",
         ("开（%s）" % args.polite) if args.polite else "关", args.delay))
    w("- %s" % COMPLIANCE_LINE)
    w("")
    w("| anchor | fact | judgement | severity | confidence | action |")
    w("|---|---|---|---|---|---|")

    counts = {"命中": 0, "未命中": 0, "无标识符": 0, "查询失败": 0}
    attr_counts = {}
    detail = []
    for i, (label, text) in enumerate(entries, 1):
        local = parse_local(text)
        rec, status, note = None, None, ""
        if args.offline:
            status = "未查（--offline）"
        elif local["doi"]:
            r = crossref_by_doi(local["doi"], args.timeout, args.polite)
            status, note, rec = r["status"], r.get("note", ""), r.get("rec")
        elif local["arxiv"]:
            r = arxiv_by_id(local["arxiv"], args.timeout)
            status, note, rec = r["status"], r.get("note", ""), r.get("rec")
        elif args.title_search and local["title"]:
            r = crossref_by_title(local["title"], args.timeout, args.polite)
            status, note, rec = r["status"], r.get("note", ""), r.get("rec")
            if rec:
                sim = title_similarity(local["title"], rec.get("title"))
                if sim < args.title_min_sim:
                    # Crossref 的 query.bibliographic 总会返回最接近的一条，低相似度即视为未命中
                    status = "未命中(标题搜索)"
                    note = "top-1 标题相似度仅 %.2f，判为未命中" % sim
                    rec = None
                else:
                    note = "标题相似度 %.2f" % sim
        else:
            status, note = "无标识符", "条目里没有 DOI / arXiv ID（未开 --title-search）"

        attr, attr_note = check_attribution(local, rec)
        key = status.split("(")[0]
        counts[key] = counts.get(key, 0) + 1
        attr_counts[attr] = attr_counts.get(attr, 0) + 1

        ident = local["doi"] or (("arXiv:" + local["arxiv"]) if local["arxiv"] else "—")
        remote = ""
        if rec:
            remote = "远端：%s / %s / %s" % (rec.get("family") or "?", rec.get("year") or "?",
                                          (rec.get("title") or "")[:90])
        notes = "；".join(x for x in (note, attr_note) if x)
        fact = ("Ref%s ｜ 标识符 `%s` ｜ exists=%s ｜ attribution_ok=%s %s %s ｜ 原文：%s"
                % (label, ident, status, attr,
                   ("（%s）" % notes) if notes else "",
                   remote, text[:160]))
        fact = fact.replace("|", "｜")
        w("| Ref%s | %s |  |  |  |  |" % (label, re.sub(r"\s+", " ", fact)))
        detail.append((label, ident, status, attr))

        if not args.offline and i < len(entries) and args.delay > 0:
            time.sleep(args.delay)

    w("")
    w("## 小结")
    w("")
    w("- exists：" + "；".join("%s %d" % (k, v) for k, v in counts.items() if v))
    w("- attribution_ok：" + "；".join("%s %d" % (k, v) for k, v in attr_counts.items() if v))
    w("")
    w("> `未核` = 脚本拿不到可比对的姓氏或年份，不等于有问题。")
    w("> 预算：第 7 层写进意见的条目 ≤ 8 条；只有人工复核过的才许进意见。")
    w("")

    md = "\n".join(lines)
    if args.output == "-":
        sys.stdout.write(md)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        sys.stderr.write("已写出 %s\n" % args.output)
    sys.stderr.write("完成：%s\n" % "；".join("%s %d" % (k, v) for k, v in counts.items() if v))


if __name__ == "__main__":
    main()
