"""任务文件模式"""

import time
from pathlib import Path
from typing import Optional

from ..display import (
    show_banner,
    show_task_loaded,
    show_task_start,
    show_task_complete,
    show_task_retry,
    show_task_skipped,
    show_summary_table,
    show_statistics,
    show_error,
    ask_choice,
    create_progress,
)
from ..executor import ClaudeExecutor
from ..logger import get_logger
from ..models import ErrorHandling, RunConfig, TaskStatus
from ..task_manager import TaskManager


class TaskFileMode:
    """任务文件模式"""

    def __init__(self, config: RunConfig):
        self.config = config
        self.task_manager = TaskManager(
            task_file=config.task_file,
            results_file="ralph_results.json",
        )
        self.executor = ClaudeExecutor(
            working_dir=Path(config.working_dir),
            timeout=config.timeout,
            skip_permissions=config.skip_permissions,
        )
        self.logger = get_logger()
        self.iteration = 0

    def run(self) -> None:
        """运行任务文件模式"""
        show_banner()

        # 加载任务
        try:
            tasks = self.task_manager.load_tasks()
        except FileNotFoundError as e:
            show_error(str(e))
            return

        show_task_loaded(len(tasks), self.config.task_file)

        # 获取待执行任务
        pending_tasks = self.task_manager.get_pending_tasks()

        if not pending_tasks:
            self.logger.info("没有待执行的任务")
            return

        self.logger.info(f"开始执行 {len(pending_tasks)} 个任务")

        # 执行任务
        for task in pending_tasks:
            if self.iteration >= self.config.max_iterations:
                self.logger.warning(f"达到最大迭代次数 {self.config.max_iterations}")
                break

            self._execute_task(task)
            self.iteration += 1

            # 任务间延迟
            if self.iteration < len(pending_tasks):
                time.sleep(self.config.delay)

        # 显示结果
        show_summary_table(self.task_manager.tasks, self.task_manager.results)
        show_statistics(self.task_manager.tasks, self.task_manager.results)

    def _execute_task(self, task) -> None:
        """执行单个任务"""
        show_task_start(task)

        # 更新状态为进行中
        self.task_manager.update_task_status(task.id, TaskStatus.IN_PROGRESS)

        retry_count = 0
        max_retries = self.config.max_retries if self.config.on_error == ErrorHandling.RETRY else 0

        while True:
            # 执行任务
            result = self.executor.run_task(task)
            result.retry_count = retry_count

            if result.success:
                # 任务成功
                self.task_manager.update_task_status(task.id, TaskStatus.COMPLETED)
                self.task_manager.add_result(result)
                show_task_complete(task, result)
                return

            # 任务失败，根据错误处理策略处理
            if self.config.on_error == ErrorHandling.SKIP:
                # 跳过
                self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
                self.task_manager.add_result(result)
                show_task_complete(task, result)
                return

            elif self.config.on_error == ErrorHandling.RETRY:
                # 重试
                retry_count += 1
                if retry_count <= max_retries:
                    show_task_retry(task, retry_count, max_retries)
                    time.sleep(1)  # 重试前等待
                    continue
                else:
                    # 重试次数用尽
                    self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
                    self.task_manager.add_result(result)
                    show_task_complete(task, result)
                    return

            elif self.config.on_error == ErrorHandling.PAUSE:
                # 暂停询问
                show_task_complete(task, result)
                choice = ask_choice(
                    "选择操作",
                    choices=["r", "s", "q"],
                )

                if choice == "r":
                    # 重试
                    retry_count += 1
                    continue
                elif choice == "s":
                    # 跳过
                    self.task_manager.update_task_status(task.id, TaskStatus.SKIPPED)
                    result.retry_count = retry_count
                    self.task_manager.add_result(result)
                    show_task_skipped(task)
                    return
                else:
                    # 退出
                    self.task_manager.update_task_status(task.id, TaskStatus.FAILED)
                    self.task_manager.add_result(result)
                    raise KeyboardInterrupt("用户选择退出")
