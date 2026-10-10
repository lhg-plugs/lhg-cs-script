#!/usr/bin/env python3
"""lhg-cs-script 确定性话术审计：16 条规则，零第三方依赖。

扫描目标目录下的话术文件（.txt/.md），检查禁用语、过度承诺、
差评回复完整度（联系方式/解决方案/情绪分级）与转人工 SOP 完整性。

文件名含 review/差评/评价 → 按"差评回复"规则检查；
其余 → 按"日常话术"规则检查。

用法：
    python3 cs_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

退出码：2=有 blocker，1=仅有 warning，0=干净（仅 nit 或无问题）。
规则文案均为本项目原创。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-cs-script/cs-audit"

SKIP_DIRS = {".git", "node_modules", "__pycache__", "dist", "build"}
SCAN_EXTS = {".txt", ".md", ".markdown"}

# 禁用语：blocker 级（怼客/推诿/不耐烦）
BANNED = ["爱买不买", "爱用不用", "随便你", "没办法", "你去投诉吧",
          "听不懂", "你急什么", "我很忙", "关我什么事", "就这样"]
# 轻度不耐烦表达：warning 级
MILD = ["这不是我的问题", "你没看吗", "早跟你说了", "你自己看", "别问了"]


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line, snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in sorted(files):
            if os.path.splitext(fn)[1].lower() in SCAN_EXTS:
                out.append(os.path.join(root, fn))
    return out


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().split("\n")


def is_review_file(path):
    return re.search(r"review|差评|评价", os.path.basename(path), re.I) is not None


def find_word_line(path, words):
    """返回首个命中禁用词的行 (行号, 词, 行内容)。"""
    for i, ln in enumerate(read_lines(path), 1):
        for w in words:
            if w in ln:
                return i, w, ln.strip()[:80]
    return None


def make_findings(files):
    F = []

    def add(rule_id, severity, category, title, path, line, snippet, detail):
        F.append(Finding(rule_id, severity, category, title,
                         os.path.basename(path), line, snippet, detail))

    for path in files:
        text = "\n".join(read_lines(path))
        review = is_review_file(path)
        has = lambda p, fl=0: re.search(p, text, fl) is not None

        # ---- 禁用语 ----
        loc = find_word_line(path, BANNED)
        if loc:
            ln, word, snip = loc
            cat = "差评回复" if review else "话术"
            add("CS-FBD-001", "blocker", cat, "命中禁用语「%s」" % word,
                path, ln, snip, "禁用语会激化矛盾：改写为共情表达（如「我非常理解您的心情」）。")
        loc = find_word_line(path, MILD)
        if loc:
            ln, word, snip = loc
            add("CS-FBD-002", "warning", "话术", "轻度不耐烦表达「%s」" % word,
                path, ln, snip, "把责任推回给用户的表述：改为「这个问题我来跟进」。")

        # ---- 过度承诺 ----
        if has(r"100\s*%|百分之百"):
            loc = find_word_line(path, ["100", "百分之百"]) or (1, "", "")
            add("CS-PRM-001", "blocker", "承诺", "过度承诺：「100%」类绝对化表述",
                path, loc[0], loc[2], "「100% 退款/解决」做不到就是欺骗：改为「我们会尽力…，预计 X 时间内答复」。")
        if has(r"绝对"):
            loc = find_word_line(path, ["绝对"]) or (1, "", "")
            add("CS-PRM-002", "blocker", "承诺", "过度承诺：「绝对」类表述",
                path, loc[0], loc[2], "「绝对没问题」类表述风险极高：删除或改为有条件的承诺。")
        if has(r"保证.{0,8}(退款|到账|赔偿|解决)"):
            loc = find_word_line(path, ["保证"]) or (1, "", "")
            add("CS-PRM-003", "warning", "承诺", "「保证+退款/到账」类表述缺少条件",
                path, loc[0], loc[2], "保证类表述必须注明条件与时限（如「审核通过后 3 个工作日内到账」），否则改为中性表述。")

        if review:
            # ---- 差评回复专项 ----
            if not has(r"电话|手机|微信|私信|工单|联系|客服热线"):
                add("CS-REV-001", "warning", "差评回复", "差评回复缺少联系方式",
                    path, 1, "", "公开回复必须留私下跟进通道（私信/电话/工单）：否则用户无法被真正安抚。")
            if not has(r"解决|补偿|退款|换货|重新|跟进|上门|处理方案"):
                add("CS-REV-002", "warning", "差评回复", "差评回复缺少解决方案",
                    path, 1, "", "只道歉不给方案等于空话：给出具体解决动作（退款/补偿/重新服务+时限）。")
            loc = find_word_line(path, BANNED)
            if loc:
                add("CS-REV-003", "blocker", "差评回复", "差评回复含怼客语「%s」" % loc[1],
                    path, loc[0], loc[2], "差评是公开的：怼客回复会被截图传播，按 lhg-cs-review 双轨模板重写。")
            if not has(r"轻度|中度|重度|分级"):
                add("CS-REV-004", "warning", "差评回复", "差评回复缺少情绪分级",
                    path, 1, "", "先做情绪分级（轻/中/重度），再选对应回复模板：见 lhg-cs-review 第 3 节。")
        else:
            # ---- 日常话术：转人工 SOP ----
            if not has(r"转人工|转接|升级处理"):
                add("CS-ESC-001", "warning", "转人工", "话术库缺少转人工触发条件",
                    path, 1, "", "明确写出触发转人工的场景（用户要求投诉/升级、超权限、情绪失控），见 lhg-cs-escalate。")
            elif not has(r"记录|交接|工单"):
                add("CS-ESC-002", "warning", "转人工", "转人工缺少交接记录要求",
                    path, 1, "", "转人工必须带上下文交接（记录工单/问题摘要），不许让用户重复描述。")
            if has(r"转人工|转接") and not has(r"投诉|辱骂|超权限|无法解决|要求升级"):
                add("CS-ESC-003", "warning", "转人工", "转人工触发条件缺少具体场景",
                    path, 1, "", "只写「转人工」不够：列出 2-3 个具体触发场景，客服才知道什么时候转。")
            if not has(r"分钟|小时内|及时|尽快"):
                add("CS-TIM-001", "warning", "话术", "缺少响应时效承诺",
                    path, 1, "", "给出明确的响应时效（如「5 分钟内响应」），管理用户预期。")
            if not has(r"您|亲|您好"):
                add("CS-HYG-001", "nit", "话术", "缺少称谓",
                    path, 1, "", "开头加称谓（您好/亲），第一句决定用户愿不愿意继续沟通。")
            if not has(r"谢谢|感谢|祝您|客服|工号"):
                add("CS-HYG-002", "nit", "话术", "缺少结束语/署名",
                    path, 1, "", "结尾加感谢语或客服署名，闭环话术更显专业。")

        # ---- 补偿审批（两类文件通用） ----
        if has(r"补偿") and not has(r"审批|权限|申请"):
            add("CS-CMP-001", "warning", "补偿", "补偿方案缺少审批说明",
                path, 1, "", "补偿涉及成本：写明审批流程/权限（如「补偿需主管审批」），避免客服过度承诺。")

    return F


# ---- 规则注册表（对外口径：16 条） ----
RULES = [
    ("CS-FBD-001", "blocker", "话术"), ("CS-FBD-002", "warning", "话术"),
    ("CS-PRM-001", "blocker", "承诺"), ("CS-PRM-002", "blocker", "承诺"),
    ("CS-PRM-003", "warning", "承诺"),
    ("CS-REV-001", "warning", "差评回复"), ("CS-REV-002", "warning", "差评回复"),
    ("CS-REV-003", "blocker", "差评回复"), ("CS-REV-004", "warning", "差评回复"),
    ("CS-ESC-001", "warning", "转人工"), ("CS-ESC-002", "warning", "转人工"),
    ("CS-ESC-003", "warning", "转人工"),
    ("CS-TIM-001", "warning", "话术"),
    ("CS-CMP-001", "warning", "补偿"),
    ("CS-HYG-001", "nit", "话术"), ("CS-HYG-002", "nit", "话术"),
]

SEV_ORDER = {"blocker": 0, "warning": 1, "nit": 2}


def main():
    ap = argparse.ArgumentParser(description="lhg-cs-script 话术审计")
    ap.add_argument("--target", required=True, help="待扫描目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"], default="blocker")
    args = ap.parse_args()

    files = collect_files(args.target)
    findings = make_findings(files)
    findings.sort(key=lambda f: (SEV_ORDER[f.severity], f.rule_id))
    summary = {
        "tool": TOOL, "version": VERSION, "target": args.target,
        "files_scanned": len(files), "rules_run": len(RULES),
        "blocker": sum(1 for f in findings if f.severity == "blocker"),
        "warning": sum(1 for f in findings if f.severity == "warning"),
        "nit": sum(1 for f in findings if f.severity == "nit"),
    }

    if args.format == "json":
        print(json.dumps({"summary": summary,
                          "findings": [f.to_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print("lhg-cs-script 话术审计  target=%s  文件=%d  规则=%d"
              % (args.target, summary["files_scanned"], summary["rules_run"]))
        print("blocker=%d warning=%d nit=%d"
              % (summary["blocker"], summary["warning"], summary["nit"]))
        for f in findings:
            print("[%s][%s] %s:%d %s" % (f.severity, f.rule_id, f.file, f.line, f.title))
            if f.detail:
                print("    %s" % f.detail)

    if summary["blocker"] > 0:
        return 2
    if args.fail_on in ("warning", "nit") and summary["warning"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
