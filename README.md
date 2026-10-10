<!-- About 简介（推送后填写到仓库 About 栏）：
客服话术专家：高频场景话术库生成 + 差评管理（review-care）+ 话术自查 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-cs-script
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, customer-service, review-care -->

# lhg-cs-script：客服话术专家

> **一句话介绍**：给 AI 编程助手装上"客服话术一条龙"——高频场景话术库生成（安抚/解释/补偿/转人工 SOP）、**含差评管理（review-care）能力**：差评情绪分级→公开回复+私下跟进双轨→根因归类，16 条确定性规则硬检禁用语与过度承诺。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-cs-script
> /plugin install lhg-cs-script@lhg-plugs
> ```

## 它是什么

`lhg-cs-script` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **3 个命令**（小白入口）：`cs-script` 话术库生成一条龙，`review-care` **差评管理子命令**（差评→情绪分级→双轨回复→跟进 SOP），`cs-check` 话术自查
- **5 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：话术方法论、安抚与共情、转人工 SOP、**差评回复策略**、差评根因归类
- **3 个专家 agent**：话术撰写、差评处理（review-care）、话术自查
- **2 个硬门 hooks**：commit 前话术审计拦截（有 blocker 不让提交）、写话术文件时禁用语即时提醒（均可一键豁免）
- **16 条确定性话术审计规则**：纯 Python、零第三方依赖，5 秒出结果

**含差评管理（review-care）能力**：本插件已合并差评管理全链路——`/lhg-cs-script:review-care` 子命令 + `lhg-cs-review`（公开回复+私下跟进双轨策略）+ `lhg-cs-root`（差评根因归类）+ `review-care-agent` + CS-REV 系列审计规则 + 差评场景 fixtures 坏/好对照。

**边界**：本插件只做话术与流程方法论，**不碰业务系统**（不直连工单/IM 系统、不代发回复）；补偿额度与审批链按你的业务填写；不以利益诱导用户删改差评（平台违规）。

## 3 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-cs-script:cs-script` | 高频场景→话术库生成（安抚/解释/补偿/转人工 SOP） | `/lhg-cs-script:cs-script "生鲜电商售后"` |
| `/lhg-cs-script:review-care` | 差评管理：情绪分级→公开回复+私下跟进双轨→跟进 SOP | `/lhg-cs-script:review-care "等了 10 天还没发货，太差了"` |
| `/lhg-cs-script:cs-check` | 话术自查：禁用语/过度承诺/差评完整度/转人工条件 | `/lhg-cs-script:cs-check ./scripts` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工复核清单（人）：

1. 先跑 `scripts/audit/cs_audit.py`（16 条规则：禁用语、过度承诺、差评回复完整度、转人工 SOP），零 LLM 成本；
2. 发现分三级：**blocker**（禁用语、"100%"/"绝对"、差评回复怼客，commit 前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再按各 skill 人工复核：语气测试（大声读一遍）、转人工三分类覆盖、差评双轨完整性。

blocker 清零才算通过；为清零改规则算作弊，不许。

## 目录结构

```
lhg-cs-script/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 3 个命令：cs-script / review-care / cs-check
├── skills/                  # 5 个平台中立 skill（lhg-cs-method/empathy/escalate/review/root）
├── agents/                  # 3 个专家 agent（script-writer / review-care-agent / cs-auditor）
├── hooks/                   # 2 个硬门（commit 前审计拦截 / 话术文件提醒）+ 豁免说明
├── scripts/audit/           # 16 条确定性话术审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照，含差评场景）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 从 0 到 1 搭建客服话术库，回复质量不稳定时 → 用 `/lhg-cs-script:cs-script`
- 收到公开差评不知道怎么回时 → 用 `/lhg-cs-script:review-care`（情绪分级→双轨回复）
- 差评越回越多，想找到根因时 → 看 `lhg-cs-root`（五类根因标签+月度分布分析）
- 客服动不动就被超出权限的问题卡住时 → 看 `lhg-cs-escalate`（转人工 SOP）
- 话术写完怕有禁用语/过度承诺时 → 审计脚本 5 秒扫一遍

**什么时候不用：**

- 你要的是直连工单/IM 系统的客服机器人开发 → 本插件只做话术方法论，不碰业务系统
- 你只需要单条回复润色 → 直接改那句话，不用整套流程
- 你想用返现诱导用户删差评 → 本插件不支持，平台会封号
- 你的客服场景是纯电话外呼 → 话术结构可借鉴，但示例按文字客服写

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-cs-script](https://github.com/lhg-plugs/lhg-cs-script) | 客服话术专家：话术库生成 + 差评管理（review-care）+ 自查 | `/plugin install lhg-cs-script@lhg-plugs` |
| *（后续插件在此追加，保持表格格式一致）* | | |

## 自检与反馈

- 每次用完任一 skill，按其「自检与反馈」节做轻量自检。
- 标准冒烟用例：`python3 smoke_test.py`（仓库根目录），全绿才算过。
- 反馈渠道：以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-cs-script/issues，正文写清「输入 → 错误输出 → 期望输出」。规则误报/漏报请附最小复现代码。

## 出品

**出品：刘洪光**（安徽合肥），归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
