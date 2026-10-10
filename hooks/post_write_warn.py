#!/usr/bin/env python3
"""lhg-cs-script 硬门②：写入话术文件（.txt/.md）后即时检查禁用语与过度承诺。

触发：PostToolUse / Write|Edit。只处理文本话术文件，其余快速放行。
命中禁用语或"100%"/"绝对"类表述时给出 additionalContext 提醒（不拦截）。

逃生方式：LHG_CS_HOOKS_OFF=1（本次会话内不再提醒）。
设计原则：内部出错 fail-open；纯提醒，不拦截写入。零第三方依赖。
"""

import json
import os
import re
import sys

BANNED = ["爱买不买", "爱用不用", "随便你", "没办法", "你去投诉吧",
          "听不懂", "你急什么", "我很忙", "关我什么事", "就这样"]
OVER = [r"100\s*%", r"百分之百", r"绝对"]


def main() -> int:
    if os.environ.get("LHG_CS_HOOKS_OFF") == "1":
        return 0
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-open

    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""
    if os.path.splitext(path)[1].lower() not in (".txt", ".md", ".markdown"):
        return 0  # 非话术文件：快速放行

    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return 0  # 读不到文件：fail-open

    hits = [w for w in BANNED if w in text]
    over_hits = sorted({m.group(0) for p in OVER for m in re.finditer(p, text)})

    notes = []
    if hits:
        notes.append("发现禁用语（%s）：发给用户前必须改写，见 skill lhg-cs-method" % "、".join(hits))
    if over_hits:
        notes.append("发现过度承诺表述（%s）：改为有条件/有时限的承诺，见 skill lhg-cs-method" % "、".join(over_hits))
    if not notes:
        return 0
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "lhg-cs-script 提醒（话术文件 %s）：\n- %s\n"
                "跑 /lhg-cs-script:cs-check 可得完整分级报告。"
                % (os.path.basename(path), "\n- ".join(notes))
            ),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
