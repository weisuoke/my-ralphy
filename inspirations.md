# Ralph-Loop 最简实现

## 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ralph-Loop                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│   │  Task Queue  │───▶│  Executor    │───▶│  Result      │     │
│   │  (tasks.txt) │    │  (subprocess)│    │  Collector   │     │
│   └──────────────┘    └──────────────┘    └──────────────┘     │
│          │                   │                    │              │
│          │                   ▼                    │              │
│          │           ┌──────────────┐            │              │
│          │           │ Claude Code  │            │              │
│          │           │   (claude)   │            │              │
│          │           └──────────────┘            │              │
│          │                   │                    │              │
│          └───────────────────┴────────────────────┘              │
│                              │                                   │
│                              ▼                                   │
│                     ┌──────────────┐                            │
│                     │   Loop       │                            │
│                     │   Control    │                            │
│                     └──────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 代码实现

### `ralph_loop.py` - 主脚本

```python
#!/usr/bin/env python3
"""
Ralph-Loop: 一个简单的 Claude Code 循环执行器
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class LoopMode(Enum):
    """循环模式"""
    TASK_FILE = "task_file"      # 从文件读取任务列表
    INTERACTIVE = "interactive"   # 交互式输入任务
    CONTINUOUS = "continuous"     # 持续模式（任务自生成）


@dataclass
class TaskResult:
    """任务执行结果"""
    task: str
    success: bool
    output: str
    duration: float


class RalphLoop:
    """Ralph-Loop 主类"""
    
    def __init__(
        self,
        mode: LoopMode = LoopMode.TASK_FILE,
        task_file: str = "tasks.txt",
        working_dir: Optional[str] = None,
        max_iterations: int = 100,
        delay_between_tasks: float = 1.0,
    ):
        self.mode = mode
        self.task_file = Path(task_file)
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.max_iterations = max_iterations
        self.delay = delay_between_tasks
        self.results: list[TaskResult] = []
        self.iteration = 0
        
    def run_claude(self, prompt: str) -> tuple[bool, str]:
        """调用 Claude Code 执行任务"""
        try:
            # 使用 --print 模式，非交互式执行
            cmd = [
                "claude",
                "--print",           # 直接打印结果，不进入交互
                "--dangerously-skip-permissions",  # 跳过权限确认（谨慎使用）
                prompt
            ]
            
            print(f"\n{'='*60}")
            print(f"🚀 执行任务: {prompt[:50]}...")
            print(f"{'='*60}\n")
            
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            duration = time.time() - start_time
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            self.results.append(TaskResult(
                task=prompt,
                success=success,
                output=output,
                duration=duration
            ))
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "任务执行超时"
        except FileNotFoundError:
            return False, "错误: 未找到 claude 命令，请确保 Claude Code 已安装"
        except Exception as e:
            return False, f"执行错误: {str(e)}"
    
    def load_tasks_from_file(self) -> list[str]:
        """从文件加载任务列表"""
        if not self.task_file.exists():
            print(f"⚠️  任务文件 {self.task_file} 不存在，创建示例文件...")
            self.create_example_task_file()
            return []
        
        tasks = []
        with open(self.task_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if line and not line.startswith('#'):
                    tasks.append(line)
        return tasks
    
    def create_example_task_file(self):
        """创建示例任务文件"""
        example_content = """# Ralph-Loop 任务文件
# 每行一个任务，# 开头的行为注释

# 示例任务：
创建一个 hello.py 文件，内容是打印 "Hello from Ralph-Loop!"
列出当前目录的文件结构
读取 hello.py 的内容并解释
"""
        with open(self.task_file, 'w', encoding='utf-8') as f:
            f.write(example_content)
        print(f"✅ 已创建示例任务文件: {self.task_file}")
    
    def run_task_file_mode(self):
        """任务文件模式"""
        tasks = self.load_tasks_from_file()
        if not tasks:
            print("📋 任务列表为空，请编辑 tasks.txt 添加任务")
            return
        
        print(f"\n📋 加载了 {len(tasks)} 个任务\n")
        
        for i, task in enumerate(tasks, 1):
            if self.iteration >= self.max_iterations:
                print(f"⚠️  达到最大迭代次数 {self.max_iterations}")
                break
            
            print(f"\n[{i}/{len(tasks)}] ", end="")
            success, output = self.run_claude(task)
            
            if success:
                print(f"✅ 任务完成")
            else:
                print(f"❌ 任务失败: {output[:100]}")
            
            self.iteration += 1
            
            if i < len(tasks):
                time.sleep(self.delay)
    
    def run_interactive_mode(self):
        """交互式模式"""
        print("\n🎮 交互式模式 (输入 'quit' 退出, 'status' 查看状态)\n")
        
        while self.iteration < self.max_iterations:
            try:
                task = input("\n📝 输入任务: ").strip()
                
                if not task:
                    continue
                if task.lower() == 'quit':
                    break
                if task.lower() == 'status':
                    self.print_status()
                    continue
                
                success, output = self.run_claude(task)
                print(f"\n📤 输出:\n{output}")
                
                self.iteration += 1
                
            except KeyboardInterrupt:
                print("\n\n👋 退出...")
                break
    
    def run_continuous_mode(self, initial_task: str):
        """持续模式 - 任务链式执行"""
        print("\n🔄 持续模式 (Ctrl+C 退出)\n")
        
        current_task = initial_task
        
        while self.iteration < self.max_iterations:
            try:
                success, output = self.run_claude(current_task)
                print(f"\n📤 输出:\n{output[:500]}...")
                
                self.iteration += 1
                
                # 询问下一个任务
                next_task = input("\n📝 下一个任务 (回车继续上个任务/输入新任务/quit退出): ").strip()
                
                if next_task.lower() == 'quit':
                    break
                elif next_task:
                    current_task = next_task
                # 否则继续相同任务
                
                time.sleep(self.delay)
                
            except KeyboardInterrupt:
                print("\n\n👋 退出...")
                break
    
    def print_status(self):
        """打印执行状态"""
        print(f"\n{'='*40}")
        print(f"📊 执行状态")
        print(f"{'='*40}")
        print(f"迭代次数: {self.iteration}/{self.max_iterations}")
        print(f"成功任务: {sum(1 for r in self.results if r.success)}")
        print(f"失败任务: {sum(1 for r in self.results if not r.success)}")
        if self.results:
            total_time = sum(r.duration for r in self.results)
            print(f"总耗时: {total_time:.2f}秒")
        print(f"{'='*40}\n")
    
    def save_results(self, output_file: str = "ralph_results.json"):
        """保存执行结果"""
        results_data = [
            {
                "task": r.task,
                "success": r.success,
                "output": r.output,
                "duration": r.duration
            }
            for r in self.results
        ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_file}")
    
    def run(self):
        """主运行入口"""
        print("""
╔═══════════════════════════════════════╗
║         🔄 Ralph-Loop v1.0            ║
║   Claude Code 循环执行器               ║
╚═══════════════════════════════════════╝
        """)
        
        try:
            if self.mode == LoopMode.TASK_FILE:
                self.run_task_file_mode()
            elif self.mode == LoopMode.INTERACTIVE:
                self.run_interactive_mode()
            elif self.mode == LoopMode.CONTINUOUS:
                initial = input("📝 输入初始任务: ").strip()
                if initial:
                    self.run_continuous_mode(initial)
        finally:
            self.print_status()
            if self.results:
                self.save_results()


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Ralph-Loop: Claude Code 循环执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ralph_loop.py                      # 从 tasks.txt 读取任务
  python ralph_loop.py -m interactive       # 交互式模式
  python ralph_loop.py -m continuous        # 持续模式
  python ralph_loop.py -f my_tasks.txt      # 指定任务文件
  python ralph_loop.py -d ./my_project      # 指定工作目录
        """
    )
    
    parser.add_argument(
        '-m', '--mode',
        choices=['task_file', 'interactive', 'continuous'],
        default='task_file',
        help='运行模式 (默认: task_file)'
    )
    
    parser.add_argument(
        '-f', '--file',
        default='tasks.txt',
        help='任务文件路径 (默认: tasks.txt)'
    )
    
    parser.add_argument(
        '-d', '--dir',
        default=None,
        help='工作目录 (默认: 当前目录)'
    )
    
    parser.add_argument(
        '-n', '--max-iterations',
        type=int,
        default=100,
        help='最大迭代次数 (默认: 100)'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='任务间延迟秒数 (默认: 1.0)'
    )
    
    args = parser.parse_args()
    
    mode_map = {
        'task_file': LoopMode.TASK_FILE,
        'interactive': LoopMode.INTERACTIVE,
        'continuous': LoopMode.CONTINUOUS,
    }
    
    loop = RalphLoop(
        mode=mode_map[args.mode],
        task_file=args.file,
        working_dir=args.dir,
        max_iterations=args.max_iterations,
        delay_between_tasks=args.delay,
    )
    
    loop.run()


if __name__ == "__main__":
    main()
```

### `tasks.txt` - 示例任务文件

```txt
# Ralph-Loop 任务文件
# 每行一个任务，# 开头的行为注释

# 示例任务序列：
创建一个 Python 文件 calculator.py，实现加减乘除四个函数
为 calculator.py 编写单元测试 test_calculator.py
运行测试并报告结果
如果测试失败，修复代码
```

## 使用方法

```bash
# 1. 保存脚本
chmod +x ralph_loop.py

# 2. 任务文件模式（默认）
python ralph_loop.py

# 3. 交互式模式
python ralph_loop.py -m interactive

# 4. 持续模式
python ralph_loop.py -m continuous

# 5. 指定工作目录和任务文件
python ralph_loop.py -d ./my_project -f ./my_tasks.txt

# 6. 查看帮助
python ralph_loop.py --help
```

## 目录结构

```
ralph-loop/
├── ralph_loop.py        # 主脚本
├── tasks.txt            # 任务文件
└── ralph_results.json   # 执行结果（自动生成）
```

## 核心特性

| 特性 | 说明 |
|------|------|
| 🔄 三种模式 | 任务文件/交互式/持续链式 |
| 📊 结果收集 | JSON 格式保存执行历史 |
| ⏱️ 超时控制 | 防止单任务卡死 |
| 🛡️ 错误处理 | 优雅处理各种异常 |
| 📝 注释支持 | 任务文件支持 # 注释 |

这是一个最简可用的实现，你可以基于此扩展更多功能！