"""CLI 入口"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .logger import init_logger
from .models import ErrorHandling, RunConfig, TaskStatus
from .modes.task_file import TaskFileMode
from .modes.interactive import InteractiveMode
from .modes.continuous import ContinuousMode
from .task_manager import TaskManager

app = typer.Typer(
    name="ralphy",
    help="Ralph-Loop: Claude Code 循环执行器",
    add_completion=False,
)

task_app = typer.Typer(help="任务管理")
app.add_typer(task_app, name="task")

console = Console()


@app.command()
def run(
    file: str = typer.Option("prd.json", "-f", "--file", help="任务文件路径"),
    dir: str = typer.Option(".", "-d", "--dir", help="工作目录"),
    max_iterations: int = typer.Option(100, "-n", "--max-iterations", help="最大迭代次数"),
    delay: float = typer.Option(1.0, "--delay", help="任务间延迟秒数"),
    timeout: int = typer.Option(300, "--timeout", help="单任务超时秒数"),
    on_error: ErrorHandling = typer.Option(ErrorHandling.SKIP, "--on-error", help="错误处理策略"),
    max_retries: int = typer.Option(3, "--max-retries", help="最大重试次数 (仅 retry 模式)"),
    skip_permissions: bool = typer.Option(False, "--dangerously-skip-permissions", help="跳过 Claude 权限确认"),
):
    """从任务文件运行任务"""
    init_logger()

    config = RunConfig(
        task_file=file,
        working_dir=dir,
        max_iterations=max_iterations,
        delay=delay,
        timeout=timeout,
        on_error=on_error,
        max_retries=max_retries,
        skip_permissions=skip_permissions,
    )

    mode = TaskFileMode(config)

    try:
        mode.run()
    except KeyboardInterrupt:
        console.print("\n[dim]👋 已中断[/dim]")


@app.command()
def interactive(
    dir: str = typer.Option(".", "-d", "--dir", help="工作目录"),
    max_iterations: int = typer.Option(100, "-n", "--max-iterations", help="最大迭代次数"),
    timeout: int = typer.Option(300, "--timeout", help="单任务超时秒数"),
    skip_permissions: bool = typer.Option(False, "--dangerously-skip-permissions", help="跳过 Claude 权限确认"),
):
    """进入交互模式"""
    init_logger()

    config = RunConfig(
        working_dir=dir,
        max_iterations=max_iterations,
        timeout=timeout,
        skip_permissions=skip_permissions,
    )

    mode = InteractiveMode(config)
    mode.run()


@app.command()
def continuous(
    initial_task: Optional[str] = typer.Argument(None, help="初始任务"),
    dir: str = typer.Option(".", "-d", "--dir", help="工作目录"),
    max_iterations: int = typer.Option(100, "-n", "--max-iterations", help="最大迭代次数"),
    delay: float = typer.Option(1.0, "--delay", help="任务间延迟秒数"),
    timeout: int = typer.Option(300, "--timeout", help="单任务超时秒数"),
    skip_permissions: bool = typer.Option(False, "--dangerously-skip-permissions", help="跳过 Claude 权限确认"),
):
    """进入持续模式"""
    init_logger()

    config = RunConfig(
        working_dir=dir,
        max_iterations=max_iterations,
        delay=delay,
        timeout=timeout,
        skip_permissions=skip_permissions,
    )

    mode = ContinuousMode(config, initial_task=initial_task or "")
    mode.run()


@app.command()
def status(
    file: str = typer.Option("prd.json", "-f", "--file", help="任务文件路径"),
):
    """查看执行状态"""
    try:
        manager = TaskManager(task_file=file)
        manager.load_tasks()
        stats = manager.get_statistics()

        console.print("\n[bold]📊 任务状态[/bold]")
        console.print(f"  总任务: {stats['total']}")
        console.print(f"  待办: {stats['todo']}")
        console.print(f"  进行中: {stats['in_progress']}")
        console.print(f"  [green]已完成: {stats['completed']}[/green]")
        console.print(f"  [red]失败: {stats['failed']}[/red]")
        console.print(f"  [dim]跳过: {stats['skipped']}[/dim]")

    except FileNotFoundError:
        console.print(f"[red]错误:[/red] 任务文件不存在: {file}")


@task_app.command("add")
def task_add(
    title: str = typer.Argument(..., help="任务标题"),
    desc: str = typer.Option("", "--desc", help="任务描述"),
    acceptance: str = typer.Option("", "--acceptance", help="验收标准"),
    priority: int = typer.Option(0, "--priority", "-p", help="优先级"),
    tags: str = typer.Option("", "--tags", help="标签 (逗号分隔)"),
    file: str = typer.Option("prd.json", "-f", "--file", help="任务文件路径"),
):
    """添加新任务"""
    manager = TaskManager(task_file=file)

    # 尝试加载现有任务，如果文件不存在则创建空列表
    try:
        manager.load_tasks()
    except FileNotFoundError:
        manager.tasks = []

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    task = manager.add_task(
        title=title,
        description=desc,
        acceptance=acceptance,
        priority=priority,
        tags=tag_list,
    )

    console.print(f"[green]✅[/green] 已添加任务 [{task.id}] {task.title}")


@task_app.command("list")
def task_list(
    status_filter: Optional[TaskStatus] = typer.Option(None, "--status", "-s", help="按状态筛选"),
    file: str = typer.Option("prd.json", "-f", "--file", help="任务文件路径"),
):
    """列出任务"""
    try:
        manager = TaskManager(task_file=file)
        manager.load_tasks()

        tasks = manager.tasks
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]

        if not tasks:
            console.print("[dim]没有任务[/dim]")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", width=6)
        table.add_column("标题", width=30)
        table.add_column("状态", width=10)
        table.add_column("优先级", width=6)
        table.add_column("标签", width=15)

        for task in tasks:
            status_str = {
                TaskStatus.TODO: "[dim]📋 待办[/dim]",
                TaskStatus.IN_PROGRESS: "[yellow]⏳ 进行中[/yellow]",
                TaskStatus.COMPLETED: "[green]✅ 完成[/green]",
                TaskStatus.FAILED: "[red]❌ 失败[/red]",
                TaskStatus.SKIPPED: "[dim]⏭️ 跳过[/dim]",
            }.get(task.status, str(task.status))

            table.add_row(
                task.id,
                task.title[:28],
                status_str,
                str(task.priority),
                ", ".join(task.tags)[:13],
            )

        console.print(table)

    except FileNotFoundError:
        console.print(f"[red]错误:[/red] 任务文件不存在: {file}")


@task_app.command("init")
def task_init(
    file: str = typer.Option("prd.json", "-f", "--file", help="任务文件路径"),
):
    """创建示例任务文件"""
    if Path(file).exists():
        overwrite = typer.confirm(f"文件 {file} 已存在，是否覆盖?")
        if not overwrite:
            console.print("[dim]已取消[/dim]")
            return

    manager = TaskManager(task_file=file)
    manager.create_example_file()
    console.print(f"[green]✅[/green] 已创建示例任务文件: {file}")


if __name__ == "__main__":
    app()
