# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ralph-Loop (my-ralphy) is a Python CLI tool that orchestrates Claude Code for autonomous, iterative task execution. It wraps the `claude` CLI to execute tasks from JSON files or interactively.

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv venv && source .venv/bin/activate
uv pip install -e .

# Run the CLI
ralphy run -f prd.json              # Execute tasks from file
ralphy interactive                   # Interactive REPL mode
ralphy continuous "initial task"     # Continuous chaining mode
ralphy status -f prd.json           # Show task statistics
ralphy task list                    # List all tasks
ralphy task add "title"             # Add new task
```

## Architecture

```
src/my_ralphy/
├── cli.py           # Typer-based CLI entry point
├── executor.py      # ClaudeExecutor - wraps `claude --print` invocations
├── task_manager.py  # TaskManager - JSON file I/O and state management
├── models.py        # Pydantic models: Task, TaskResult, RunConfig, enums
├── display.py       # Rich terminal UI components
├── logger.py        # Logging configuration (console + file)
└── modes/           # Execution mode implementations
    ├── task_file.py    # Batch execution from JSON
    ├── interactive.py  # REPL-style execution
    └── continuous.py   # Chained task execution
```

**Data Flow:** CLI commands → Mode handlers → ClaudeExecutor → `claude` CLI subprocess → TaskManager (persist results)

**Key Files:**
- `prd.json` - Task definitions (read/write)
- `ralph_results.json` - Execution results (append-only)
- `ralph.log` - Execution logs

## Task JSON Format

```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "Task name",
      "description": "Detailed description",
      "acceptance": "Completion criteria",
      "priority": 1,
      "status": "TODO",
      "tags": ["tag1"]
    }
  ]
}
```

Tasks execute in priority order (highest first). Status transitions: TODO → IN_PROGRESS → COMPLETED/FAILED/SKIPPED.

## Error Handling Modes

- `skip` - Skip failed task, continue to next
- `retry` - Auto-retry with configurable max attempts
- `pause` - Stop and prompt user for action
