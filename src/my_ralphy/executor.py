"""Claude Code 执行器"""

import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .logger import get_logger
from .models import Task, TaskResult


@dataclass
class ExecuteResult:
    """执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    duration: float = 0.0


class ClaudeExecutor:
    """Claude Code 执行器"""

    def __init__(
        self,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        skip_permissions: bool = False,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout
        self.skip_permissions = skip_permissions
        self.logger = get_logger()

    def build_prompt(self, task: Task) -> str:
        """构建任务提示"""
        parts = [f"任务: {task.title}"]

        if task.description:
            parts.append(f"\n描述: {task.description}")

        if task.acceptance:
            parts.append(f"\n验收标准: {task.acceptance}")

        return "\n".join(parts)

    def execute(self, prompt: str) -> ExecuteResult:
        """执行 Claude Code 命令"""
        cmd = ["claude", "--print"]

        if self.skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        cmd.append(prompt)

        self.logger.info(f"执行命令: claude --print ...")
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time
            output = result.stdout + result.stderr
            success = result.returncode == 0

            if success:
                self.logger.info(f"执行成功，耗时 {duration:.1f}s")
            else:
                self.logger.warning(f"执行失败，返回码 {result.returncode}")

            return ExecuteResult(
                success=success,
                output=output,
                error=result.stderr if not success else None,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.logger.error(f"执行超时 ({self.timeout}s)")
            return ExecuteResult(
                success=False,
                output="",
                error=f"执行超时 ({self.timeout}s)",
                duration=duration,
            )

        except FileNotFoundError:
            self.logger.error("未找到 claude 命令，请确保 Claude Code 已安装")
            return ExecuteResult(
                success=False,
                output="",
                error="未找到 claude 命令，请确保 Claude Code 已安装",
                duration=0.0,
            )

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"执行错误: {str(e)}")
            return ExecuteResult(
                success=False,
                output="",
                error=str(e),
                duration=duration,
            )

    def run_task(self, task: Task) -> TaskResult:
        """执行单个任务并返回结果"""
        prompt = self.build_prompt(task)
        result = self.execute(prompt)

        return TaskResult(
            task_id=task.id,
            success=result.success,
            output=result.output,
            error=result.error,
            duration=result.duration,
            executed_at=datetime.now(),
        )
