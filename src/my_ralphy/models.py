"""数据模型定义"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ErrorHandling(str, Enum):
    """错误处理策略枚举"""
    SKIP = "skip"       # 跳过继续
    RETRY = "retry"     # 自动重试
    PAUSE = "pause"     # 暂停询问


class Task(BaseModel):
    """任务模型"""
    id: str = Field(..., description="任务唯一标识")
    title: str = Field(..., description="任务标题")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="当前状态")
    description: str = Field(default="", description="详细描述")
    acceptance: str = Field(default="", description="验收标准")
    priority: int = Field(default=0, description="优先级 (数字越大越优先)")
    tags: list[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

    class Config:
        use_enum_values = True


class TaskResult(BaseModel):
    """任务执行结果模型"""
    task_id: str = Field(..., description="关联的任务 ID")
    success: bool = Field(..., description="是否成功")
    output: str = Field(default="", description="Claude 输出内容")
    error: Optional[str] = Field(default=None, description="错误信息")
    duration: float = Field(..., description="执行耗时(秒)")
    retry_count: int = Field(default=0, description="重试次数")
    executed_at: datetime = Field(default_factory=datetime.now, description="执行时间")


class RunConfig(BaseModel):
    """运行配置模型"""
    task_file: str = Field(default="prd.json", description="任务文件路径")
    working_dir: str = Field(default=".", description="工作目录")
    max_iterations: int = Field(default=100, description="最大迭代次数")
    delay: float = Field(default=1.0, description="任务间延迟秒数")
    timeout: int = Field(default=300, description="单任务超时秒数")
    on_error: ErrorHandling = Field(default=ErrorHandling.SKIP, description="错误处理策略")
    max_retries: int = Field(default=3, description="最大重试次数")
    skip_permissions: bool = Field(default=False, description="跳过 Claude 权限确认")
