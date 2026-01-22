"""任务管理模块"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Task, TaskResult, TaskStatus


class TaskManager:
    """任务管理器"""

    def __init__(self, task_file: str = "prd.json", results_file: str = "ralph_results.json"):
        self.task_file = Path(task_file)
        self.results_file = Path(results_file)
        self.tasks: list[Task] = []
        self.results: list[TaskResult] = []

    def load_tasks(self) -> list[Task]:
        """从 JSON 文件加载任务列表"""
        if not self.task_file.exists():
            raise FileNotFoundError(f"任务文件不存在: {self.task_file}")

        with open(self.task_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.tasks = [Task(**item) for item in data]
        return self.tasks

    def save_tasks(self) -> None:
        """保存任务列表到 JSON 文件"""
        data = [task.model_dump(mode="json") for task in self.tasks]
        with open(self.task_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def load_results(self) -> list[TaskResult]:
        """加载执行结果"""
        if not self.results_file.exists():
            return []

        with open(self.results_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.results = [TaskResult(**item) for item in data]
        return self.results

    def save_results(self) -> None:
        """保存执行结果"""
        data = [result.model_dump(mode="json") for result in self.results]
        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def add_result(self, result: TaskResult) -> None:
        """添加执行结果"""
        self.results.append(result)
        self.save_results()

    def get_pending_tasks(self) -> list[Task]:
        """获取待执行任务（按优先级排序）"""
        pending = [t for t in self.tasks if t.status == TaskStatus.TODO]
        return sorted(pending, key=lambda t: t.priority, reverse=True)

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据 ID 获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """更新任务状态"""
        task = self.get_task_by_id(task_id)
        if task:
            task.status = status
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
            self.save_tasks()

    def add_task(
        self,
        title: str,
        description: str = "",
        acceptance: str = "",
        priority: int = 0,
        tags: Optional[list[str]] = None,
    ) -> Task:
        """添加新任务"""
        # 生成新 ID
        existing_ids = [int(t.id) for t in self.tasks if t.id.isdigit()]
        new_id = str(max(existing_ids, default=0) + 1).zfill(3)

        task = Task(
            id=new_id,
            title=title,
            description=description,
            acceptance=acceptance,
            priority=priority,
            tags=tags or [],
            created_at=datetime.now(),
        )

        self.tasks.append(task)
        self.save_tasks()
        return task

    def create_example_file(self) -> None:
        """创建示例任务文件"""
        example_tasks = [
            Task(
                id="001",
                title="创建 calculator.py",
                description="实现加减乘除四个函数",
                acceptance="所有函数可正常调用并返回正确结果",
                priority=10,
                tags=["core", "math"],
            ),
            Task(
                id="002",
                title="编写单元测试",
                description="为 calculator.py 编写 pytest 测试",
                acceptance="测试覆盖率 > 90%",
                priority=9,
                tags=["test"],
            ),
        ]

        self.tasks = example_tasks
        self.save_tasks()

    def get_statistics(self) -> dict:
        """获取任务统计"""
        return {
            "total": len(self.tasks),
            "todo": sum(1 for t in self.tasks if t.status == TaskStatus.TODO),
            "in_progress": sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS),
            "completed": sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks if t.status == TaskStatus.FAILED),
            "skipped": sum(1 for t in self.tasks if t.status == TaskStatus.SKIPPED),
        }
