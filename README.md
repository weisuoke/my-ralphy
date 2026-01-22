# My-Ralphy

Claude Code 循环执行器 - 一个 Python 实现的 Ralph-Loop。

## 安装

```bash
uv pip install -e .
```

## 使用

```bash
# 任务文件模式
ralphy run -f prd.json

# 交互模式
ralphy interactive

# 持续模式
ralphy continuous "初始任务"
```

## 功能

- 三种运行模式：task_file / interactive / continuous
- JSON 格式任务管理
- 可配置的错误处理策略：skip / retry / pause
- Rich 终端美化输出
- 详细的日志记录
