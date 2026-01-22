"""交互模式"""

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from ..display import show_banner, show_output, show_info, show_statistics
from ..executor import ClaudeExecutor
from ..logger import get_logger
from ..models import RunConfig, Task, TaskStatus
from ..task_manager import TaskManager

console = Console()


class InteractiveMode:
    """交互模式"""

    def __init__(self, config: RunConfig):
        self.config = config
        self.executor = ClaudeExecutor(
            working_dir=Path(config.working_dir),
            timeout=config.timeout,
            skip_permissions=config.skip_permissions,
        )
        self.logger = get_logger()
        self.results = []
        self.iteration = 0

    def run(self) -> None:
        """运行交互模式"""
        show_banner()
        console.print("\n[bold cyan]交互模式[/bold cyan] (输入 'quit' 退出, 'status' 查看状态, 'help' 获取帮助)\n")

        while self.iteration < self.config.max_iterations:
            try:
                # 获取用户输入
                task_input = Prompt.ask("\n[bold green]📝 输入任务[/bold green]")

                if not task_input.strip():
                    continue

                # 处理特殊命令
                command = task_input.strip().lower()

                if command == "quit" or command == "exit":
                    console.print("\n[dim]👋 退出交互模式[/dim]")
                    break

                elif command == "status":
                    self._show_status()
                    continue

                elif command == "help":
                    self._show_help()
                    continue

                # 执行任务
                self._execute_task(task_input)
                self.iteration += 1

            except KeyboardInterrupt:
                console.print("\n\n[dim]👋 退出交互模式[/dim]")
                break
            except EOFError:
                console.print("\n\n[dim]👋 退出交互模式[/dim]")
                break

        # 显示最终统计
        if self.results:
            self._show_status()

    def _execute_task(self, prompt: str) -> None:
        """执行任务"""
        console.print(f"\n[bold blue]▶[/bold blue] 执行中...")

        # 创建临时任务
        task = Task(
            id=f"i{self.iteration + 1:03d}",
            title=prompt[:50] + ("..." if len(prompt) > 50 else ""),
            description=prompt,
        )

        # 执行
        result = self.executor.run_task(task)
        self.results.append(result)

        # 显示结果
        if result.success:
            console.print(f"[bold green]✅[/bold green] 完成，耗时 {result.duration:.1f}s")
            if result.output:
                show_output(result.output, title="Claude 输出")
        else:
            console.print(f"[bold red]❌[/bold red] 失败: {result.error or '未知错误'}")
            if result.output:
                show_output(result.output, title="输出")

    def _show_status(self) -> None:
        """显示状态"""
        console.print("\n[bold]📊 执行状态[/bold]")
        console.print(f"  迭代次数: {self.iteration}/{self.config.max_iterations}")
        console.print(f"  成功任务: {sum(1 for r in self.results if r.success)}")
        console.print(f"  失败任务: {sum(1 for r in self.results if not r.success)}")

        if self.results:
            total_time = sum(r.duration for r in self.results)
            console.print(f"  总耗时: {total_time:.1f}s")

    def _show_help(self) -> None:
        """显示帮助"""
        console.print("\n[bold]📖 帮助[/bold]")
        console.print("  输入任务描述，按回车执行")
        console.print("  [dim]quit[/dim]   - 退出交互模式")
        console.print("  [dim]status[/dim] - 查看执行状态")
        console.print("  [dim]help[/dim]   - 显示此帮助")
