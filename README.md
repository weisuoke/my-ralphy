# My-Ralphy

Claude Code 循环执行器 - 一个 Python 实现的 Ralph-Loop。

## 安装

```bash
cd my-ralphy
uv venv && source .venv/bin/activate
uv pip install -e .
```

## 使用

```bash
# 查看帮助
ralphy --help

# 初始化示例任务文件
ralphy task init

# 从任务文件运行
ralphy run -f prd.json

# 交互模式
ralphy interactive

# 持续模式
ralphy continuous "你的任务"
```

## 命令详解

### `ralphy run` - 任务文件模式

```bash
ralphy run [OPTIONS]

Options:
  -f, --file PATH           任务文件路径 [default: prd.json]
  -d, --dir PATH            工作目录 [default: .]
  -n, --max-iterations INT  最大迭代次数 [default: 100]
  --delay FLOAT             任务间延迟秒数 [default: 1.0]
  --timeout INT             单任务超时秒数 [default: 300]
  --on-error [skip|retry|pause]  错误处理策略 [default: skip]
  --max-retries INT         最大重试次数 [default: 3]
  --dangerously-skip-permissions  跳过 Claude 权限确认
```

### `ralphy task` - 任务管理

```bash
# 添加任务
ralphy task add "任务标题" --desc "描述" --priority 1 --tags "tag1,tag2"

# 列出任务
ralphy task list
ralphy task list --status todo

# 创建示例任务文件
ralphy task init
```

### `ralphy status` - 查看状态

```bash
ralphy status -f prd.json
```

## 任务文件格式

```json
[
  {
    "id": "001",
    "title": "任务标题",
    "status": "todo",
    "description": "详细描述",
    "acceptance": "验收标准",
    "priority": 10,
    "tags": ["tag1", "tag2"],
    "created_at": "2026-01-22T10:00:00",
    "completed_at": null
  }
]
```

## 功能特性

- **三种运行模式**：task_file / interactive / continuous
- **JSON 格式任务管理**：支持优先级、标签、验收标准
- **可配置的错误处理**：skip (跳过) / retry (重试) / pause (暂停询问)
- **Rich 终端美化**：进度条、表格、彩色输出
- **详细的日志记录**：ralph.log 文件 + 控制台输出
- **执行结果保存**：ralph_results.json
