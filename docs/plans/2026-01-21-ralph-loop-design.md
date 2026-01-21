# Ralph-Loop 设计文档

## 项目概述

`my-ralphy` 是一个 Python 实现的 Claude Code 循环执行器，支持自主迭代执行任务。

## 目录结构

```
my-ralphy/
├── src/
│   └── my_ralphy/
│       ├── __init__.py
│       ├── cli.py           # CLI 入口 (typer)
│       ├── executor.py      # Claude Code 执行器
│       ├── task_manager.py  # 任务管理 (JSON 读写、状态更新)
│       ├── models.py        # 数据模型 (Task, TaskResult, Config)
│       ├── modes/
│       │   ├── __init__.py
│       │   ├── task_file.py    # 任务文件模式
│       │   ├── interactive.py  # 交互模式
│       │   └── continuous.py   # 持续模式
│       ├── logger.py        # 日志管理
│       └── display.py       # Rich 进度展示
├── tests/
│   └── ...
├── pyproject.toml           # uv/pip 配置
├── README.md
└── examples/
    └── prd.json             # 示例任务文件
```

## 数据模型

### Task 模型

```python
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Task(BaseModel):
    id: str                          # 任务唯一标识
    title: str                       # 任务标题
    status: TaskStatus = TODO        # 当前状态
    description: str = ""            # 详细描述
    acceptance: str = ""             # 验收标准
    priority: int = 0                # 优先级 (数字越大越优先)
    tags: list[str] = []             # 标签
    created_at: datetime             # 创建时间
    completed_at: datetime | None    # 完成时间
```

### TaskResult 模型

```python
class TaskResult(BaseModel):
    task_id: str                     # 关联的任务 ID
    success: bool                    # 是否成功
    output: str                      # Claude 输出内容
    error: str | None                # 错误信息
    duration: float                  # 执行耗时(秒)
    retry_count: int = 0             # 重试次数
    executed_at: datetime            # 执行时间
```

### ErrorHandling 配置

```python
class ErrorHandling(str, Enum):
    SKIP = "skip"           # 跳过继续
    RETRY = "retry"         # 自动重试
    PAUSE = "pause"         # 暂停询问
```

## CLI 命令设计

### 主命令

```bash
ralphy [OPTIONS] COMMAND [ARGS]
```

### 子命令

| 命令 | 描述 | 示例 |
|------|------|------|
| `run` | 运行任务（默认 task_file 模式） | `ralphy run -f prd.json` |
| `interactive` | 进入交互模式 | `ralphy interactive` |
| `continuous` | 进入持续模式 | `ralphy continuous "初始任务"` |
| `task` | 任务管理 | `ralphy task add/list/status` |
| `status` | 查看执行状态 | `ralphy status` |

### `run` 命令参数

```bash
ralphy run [OPTIONS]

Options:
  -f, --file PATH           任务文件路径 [default: prd.json]
  -d, --dir PATH            工作目录 [default: .]
  -n, --max-iterations INT  最大迭代次数 [default: 100]
  --delay FLOAT             任务间延迟秒数 [default: 1.0]
  --timeout INT             单任务超时秒数 [default: 300]
  --on-error [skip|retry|pause]  错误处理策略 [default: skip]
  --max-retries INT         最大重试次数 (仅 retry 模式) [default: 3]
  --dangerously-skip-permissions  跳过 Claude 权限确认
```

### `task` 子命令

```bash
ralphy task add "任务标题" --desc "描述" --priority 1 --tags "tag1,tag2"
ralphy task list [--status todo|completed|failed]
ralphy task status 001
```

## 执行流程

### Executor 执行器

```python
class ClaudeExecutor:
    def run(self, prompt: str, working_dir: Path, timeout: int) -> ExecuteResult:
        """调用 Claude Code 执行单个任务"""
        cmd = [
            "claude",
            "--print",
            "--dangerously-skip-permissions",
            prompt
        ]
```

### 三种模式

**1. Task File 模式**
```
加载 prd.json → 按优先级排序 → 逐个执行 → 更新状态 → 保存结果
     ↑                                              │
     └──────────── 失败重试/跳过/暂停 ←─────────────┘
```

**2. Interactive 模式**
```
显示欢迎界面 → 等待输入 → 执行任务 → 显示结果 → 循环
                  ↓
            特殊命令: status/quit/help
```

**3. Continuous 模式**
```
输入初始任务 → 执行 → 显示结果 → 询问下一步 → 循环
                                    ↓
                          回车=继续 / 新任务 / quit
```

### 错误处理

```
执行失败
    ├─ skip: 标记 FAILED → 记录日志 → 下一个任务
    ├─ retry: 重试 N 次 → 仍失败则标记 FAILED → 下一个
    └─ pause: 显示错误 → 询问 [r]etry/[s]kip/[q]uit
```

## 日志与进度展示

### 日志格式 (ralph.log)

```
2026-01-21 10:30:15 [INFO] Ralph-Loop 启动，加载 12 个任务
2026-01-21 10:30:16 [INFO] [001] 开始执行: 创建用户认证模块
2026-01-21 10:32:45 [INFO] [001] 完成，耗时 149.2s
2026-01-21 10:32:46 [WARN] [002] 执行失败: 超时
2026-01-21 10:32:46 [INFO] [002] 重试 1/3...
```

### Rich 终端展示

**启动界面**
```
╭─────────────────────────────────────────╮
│         🔄 Ralph-Loop v1.0              │
│       Claude Code 循环执行器             │
╰─────────────────────────────────────────╯
📋 已加载 12 个任务 (prd.json)
```

**实时进度**
```
任务进度 ━━━━━━━━━━━━━━━━━━━━ 3/12 (25%)

当前任务: [003] 实现登录 API
状态: 执行中... ⏱️ 45s
```

**完成统计**
```
┏━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ ID  ┃ 任务               ┃ 状态    ┃ 耗时   ┃
┡━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ 001 │ 创建用户模块       │ ✅ 完成 │ 149.2s │
│ 002 │ 编写单元测试       │ ✅ 完成 │ 89.5s  │
│ 003 │ 实现登录 API       │ ❌ 失败 │ 300.0s │
└─────┴────────────────────┴─────────┴────────┘

📊 总计: 完成 2 | 失败 1 | 跳过 0 | 耗时 538.7s
```

## 输出文件

| 文件 | 内容 |
|------|------|
| `prd.json` | 任务列表 (状态会被更新) |
| `ralph_results.json` | 执行结果详情 |
| `ralph.log` | 运行日志 |

## 示例 prd.json

```json
[
  {
    "id": "001",
    "title": "创建 calculator.py",
    "status": "todo",
    "description": "实现加减乘除四个函数",
    "acceptance": "所有函数可正常调用并返回正确结果",
    "priority": 10,
    "tags": ["core", "math"],
    "created_at": "2026-01-21T10:00:00",
    "completed_at": null
  },
  {
    "id": "002",
    "title": "编写单元测试",
    "status": "todo",
    "description": "为 calculator.py 编写 pytest 测试",
    "acceptance": "测试覆盖率 > 90%",
    "priority": 9,
    "tags": ["test"],
    "created_at": "2026-01-21T10:00:00",
    "completed_at": null
  }
]
```

## 安装方式

```bash
# 开发安装 (使用 uv)
uv pip install -e .

# 或从 PyPI 安装 (发布后)
uv pip install my-ralphy
```

## pyproject.toml

```toml
[project]
name = "my-ralphy"
version = "0.1.0"
description = "Claude Code 循环执行器"
dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.scripts]
ralphy = "my_ralphy.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 技术选型总结

| 特性 | 方案 |
|------|------|
| 运行模式 | task_file / interactive / continuous |
| 任务格式 | JSON (完整字段) |
| 错误处理 | skip / retry / pause (可配置) |
| 输出 | JSON结果 + 日志 + Rich实时进度 |
| 依赖 | typer + rich + pydantic |
| 包管理 | uv + pyproject.toml |
