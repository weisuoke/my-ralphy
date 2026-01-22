"""Rich 显示模块"""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from .models import Task, TaskResult, TaskStatus

console = Console()


def show_banner() -> None:
    """显示启动横幅"""
    banner = Text()
    banner.append("🔄 Ralph-Loop v0.1.0\n", style="bold cyan")
    banner.append("   Claude Code 循环执行器", style="dim")

    panel = Panel(
        banner,
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def show_task_loaded(count: int, file_path: str) -> None:
    """显示任务加载信息"""
    console.print(f"📋 已加载 [bold]{count}[/bold] 个任务 ({file_path})")


def show_task_start(task: Task) -> None:
    """显示任务开始执行"""
    console.print(f"\n[bold blue]▶[/bold blue] [{task.id}] {task.title}")


def show_task_complete(task: Task, result: TaskResult) -> None:
    """显示任务完成"""
    if result.success:
        console.print(f"[bold green]✅[/bold green] 完成，耗时 {result.duration:.1f}s")
    else:
        console.print(f"[bold red]❌[/bold red] 失败: {result.error or '未知错误'}")


def show_task_retry(task: Task, attempt: int, max_retries: int) -> None:
    """显示任务重试"""
    console.print(f"[yellow]🔄[/yellow] [{task.id}] 重试 {attempt}/{max_retries}...")


def show_task_skipped(task: Task) -> None:
    """显示任务跳过"""
    console.print(f"[dim]⏭️ [{task.id}] 已跳过[/dim]")


def create_progress() -> Progress:
    """创建进度条"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )


def show_summary_table(tasks: list[Task], results: list[TaskResult]) -> None:
    """显示执行结果汇总表格"""
    table = Table(title="执行结果", show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=6)
    table.add_column("任务", width=30)
    table.add_column("状态", width=10)
    table.add_column("耗时", width=10)

    # 创建结果映射
    result_map = {r.task_id: r for r in results}

    for task in tasks:
        result = result_map.get(task.id)

        # 状态显示
        if task.status == TaskStatus.COMPLETED:
            status = "[green]✅ 完成[/green]"
        elif task.status == TaskStatus.FAILED:
            status = "[red]❌ 失败[/red]"
        elif task.status == TaskStatus.SKIPPED:
            status = "[dim]⏭️ 跳过[/dim]"
        elif task.status == TaskStatus.IN_PROGRESS:
            status = "[yellow]⏳ 进行中[/yellow]"
        else:
            status = "[dim]📋 待办[/dim]"

        # 耗时显示
        duration = f"{result.duration:.1f}s" if result else "-"

        table.add_row(task.id, task.title[:28], status, duration)

    console.print()
    console.print(table)


def show_statistics(tasks: list[Task], results: list[TaskResult]) -> None:
    """显示统计信息"""
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    skipped = sum(1 for t in tasks if t.status == TaskStatus.SKIPPED)
    total_time = sum(r.duration for r in results)

    console.print()
    console.print(
        f"📊 总计: [green]完成 {completed}[/green] | "
        f"[red]失败 {failed}[/red] | "
        f"[dim]跳过 {skipped}[/dim] | "
        f"耗时 {total_time:.1f}s"
    )


def show_error(message: str) -> None:
    """显示错误信息"""
    console.print(f"[bold red]错误:[/bold red] {message}")


def show_warning(message: str) -> None:
    """显示警告信息"""
    console.print(f"[yellow]警告:[/yellow] {message}")


def show_info(message: str) -> None:
    """显示普通信息"""
    console.print(f"[blue]信息:[/blue] {message}")


def ask_continue(prompt: str = "是否继续?") -> bool:
    """询问是否继续"""
    from rich.prompt import Confirm
    return Confirm.ask(prompt)


def ask_choice(prompt: str, choices: list[str]) -> str:
    """询问选择"""
    from rich.prompt import Prompt
    return Prompt.ask(prompt, choices=choices)


def show_output(output: str, title: str = "输出") -> None:
    """显示 Claude 输出"""
    panel = Panel(
        output[:2000] + ("..." if len(output) > 2000 else ""),
        title=title,
        border_style="dim",
    )
    console.print(panel)
