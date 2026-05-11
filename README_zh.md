# 中国铁路 12306 Skill

[English README](README.md)

这是一个同时兼容 Codex 和 Claude Code 的 skill，用于个人或 LLM Agent 低频、只读查询中国大陆铁路信息。它可以查询车站 telecode、车次/余票、票价和经停站，不涉及登录、购票或抢票流程。

> 这不是 12306 官方开发者 API。请仅用于个人/Agent 的低频只读查询，不要用于购票、登录、验证码处理、提交订单、绕过限制、抓取或监控。

## 演示

下面的 GIF 展示了真实的交互式 `codex` 运行：Codex 读取本 skill，并调用内置 12306 查询脚本。

![Codex 调用中国铁路 12306 skill](assets/codex-demo.gif)

## 这个仓库包含什么

- `SKILL.md`：Codex 和 Claude Code 可识别的 skill 入口。
- `scripts/rail12306.py`：无第三方依赖的 Python 客户端，Linux/macOS/Windows 都可用。
- `references/endpoints.md`：当前 12306 只读网页端点和字段说明。
- `AGENTS.md` 以及 `CLAUDE.md -> AGENTS.md`：让两类 Agent 读取同一份仓库工作规范。

支持的查询：

- 车站查询：站名、城市名、拼音、拼音缩写、telecode。
- 车次/余票查询：站到站车次、发到时刻、席别余票。
- 票价查询：指定车次区间票价。
- 经停站查询：指定日期、指定车次的完整停靠站。

## 安装

Codex：

```bash
git clone git@github.com:HansBug/china-railway-12306.git \
  ~/.codex/skills/china-railway-12306
```

Claude Code：

```bash
git clone git@github.com:HansBug/china-railway-12306.git \
  ~/.claude/skills/china-railway-12306
```

也可以克隆到任意目录，然后在运行 Codex/Claude Code 时显式指向这个目录。

## 直接用 CLI 查询

内置脚本只依赖 Python 标准库：

```bash
python3 scripts/rail12306.py stations 北京南
python3 scripts/rail12306.py tickets --date 2026-05-20 --from 北京南 --to 上海虹桥 --limit 5
python3 scripts/rail12306.py price --date 2026-05-20 --from 北京南 --to 上海虹桥 --train G1
python3 scripts/rail12306.py stops G1 --date 2026-05-20
```

需要给 Agent 或其他程序消费时，加 `--json`：

```bash
python3 scripts/rail12306.py tickets \
  --date 2026-05-20 \
  --from 北京南 \
  --to 上海虹桥 \
  --train-prefix G \
  --limit 3 \
  --json
```

Windows PowerShell：

```powershell
py scripts\rail12306.py stops G1 --date 2026-05-20 --json
```

## Agent 调用示例

示例提示词：

```text
使用 china-railway-12306 skill 查询 2026-05-20 的 G1 经停站。
返回 train_no 和停靠站列表。
```

在当前仓库里临时测试交互式 Codex：

```bash
codex -C . --dangerously-bypass-approvals-and-sandbox --no-alt-screen
```

然后输入：

```text
使用这个仓库里的 china-railway-12306 skill 查询 2026-05-20 的 G1 经停站。
只返回 train_no 和停靠站列表，不要修改文件。
```

在当前仓库里临时测试 Claude Code：

```bash
claude -p --add-dir . -- \
  "Use the skill in this directory to query G1 stops on 2026-05-20. Do not modify files."
```

## 数据来源

本 skill 在 2026-05-11 实测过以下 12306 公开网页端点：

- 站点字典：`https://kyfw.12306.cn/otn/resources/js/framework/station_name.js`
- 车次/余票：`https://kyfw.12306.cn/otn/leftTicket/queryG`
- 票价：`https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice`
- 经停站：`https://kyfw.12306.cn/otn/czxx/queryByTrainNo`
- 车次搜索：`https://search.12306.cn/search/v1/train/search`

更多请求参数、字段解释和 curl 示例见 [references/endpoints.md](references/endpoints.md)。

## 验证

```bash
python3 -m py_compile scripts/rail12306.py
python3 scripts/rail12306.py stations 北京南 --json
python3 scripts/rail12306.py stops G1 --date 2026-05-20 --json
```

如果本机有 Codex skill validator：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

## 授权和使用边界

本仓库只提供 skill 和一个只读查询客户端。实时铁路数据归中国铁路/12306 所有，并通过当前公开网页端点读取。请保持低频、用户触发、只读使用，并尊重 12306 的服务控制和条款。
