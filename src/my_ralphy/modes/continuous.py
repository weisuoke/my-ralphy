"""持续模式"""

import time
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt

from ..display import show_banner, show_output
from ..executor import ClaudeExecutor
from ..logger import get_logger
from ..models import RunConfig, Task

console = Console()


class ContinuousMode:
    """持续模式 - 任务链式执行"""

    def __init__(self, config: RunConfig, initial_task: str = ""):
        self.config = config
        self.initial_task = initial_task
        self.executor = ClaudeExecutor(
            working_dir=Path(config.working_dir),
            timeout=config.timeout,
            skip_permissions=config.skip_permissions,
        )
        self.logger = get_logger()
        self.results = []
        self.iteration = 0

    def run(self) -> None:
        """运行持续模式"""
        show_banner()
        console.print("\n[bold cyan]持续模式[/bold cyan] (Ctrl+C 退出)\n")

        # 获取初始任务
        if self.initial_task:
            current_task = self.initial_task
        else:
            current_task = Prompt.ask("[bold green]📝 输入初始任务[/bold green]")

        if not current_task.strip():
            console.print("[dim]未输入任务，退出[/dim]")
            return

        while self.iteration < self.config.max_iterations:
            try:
                # 执行当前任务
                self._execute_task(current_task)
                self.iteration += 1

                # 询问下一步
                console.print("\n[dim]回车继续相同任务 / 输入新任务 / 'quit' 退出[/dim]")
                next_input = Prompt.ask("[bold green]📝 下一步[/bold green]", default="")

                if next_input.strip().lower() in ("quit", "exit"):
                    console.print("\n[dim]👋 退出持续模式[/dim]")
                    break
                elif next_input.strip():
                    current_task = next_input.strip()
                # 否则继续相同任务

                # 任务间延迟
                time.sleep(self.config.delay)

            except KeyboardInterrupt:
                console.print("\n\n[dim]👋 退出持续模式[/dim]")
                break
            except EOFError:
                console.print("\n\n[dim]👋 退出持续模式[/dim]")
                break

        # 显示最终统计
        self._show_summary()

    def _execute_task(self, prompt: str) -> None:
        """执行任务"""
        console.print(f"\n[bold blue]▶[/bold blue] [{self.iteration + 1}] 执行: {prompt[:50]}...")

        # 创建临时任务
        task = Task(
            id=f"c{self.iteration + 1:03d}",
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
                # 截取输出显示
                output_preview = result.output[:500]
                if len(result.output) > 500:
                    output_preview += "..."
                show_output(output_preview, title="Claude 输出")
        else:
            console.print(f"[bold red]❌[/bold red] 失败: {result.error or '未知错误'}")

    def _show_summary(self) -> None:
        """显示执行摘要"""
        if not self.results:
            return

        console.print("\n[bold]📊 执行摘要[/bold]")
        console.print(f"  总迭代: {self.iteration}")
        console.print(f"  成功: {sum(1 for r in self.results if r.success)}")
        console.print(f"  失败: {sum(1 for r in self.results if not r.success)}")

        total_time = sum(r.duration for r in self.results)
        console.print(f"  总耗时: {total_time:.1f}s")
