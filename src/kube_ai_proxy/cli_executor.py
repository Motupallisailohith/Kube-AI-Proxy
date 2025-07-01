# src/kube_ai_proxy/cli_executor.py

"""
Shared CLI execution utilities for Kube AI Proxy.
This mirrors patterns from k8s-mcp-server:
  - check_cli_installed: discover if a tool is available
  - run_startup_checks: sync wrapper around check_cli_installed
  - execute_command: validate & run (with pipe-support via shell)
  - get_command_help: `<tool> --help`
"""

import asyncio
import logging
import shlex
import time
from asyncio.subprocess import PIPE
from typing import Optional

from kube_ai_proxy.config import DEFAULT_TIMEOUT, SUPPORTED_CLI_TOOLS
from kube_ai_proxy.security.security import validate_command, is_pipe_command
from kube_ai_proxy.tools import CommandResult

logger = logging.getLogger("kube_ai_proxy.cli_executor")


# ─── 1) Tool‐existence checks ────────────────────────────────────────────────────

async def check_cli_installed(cli_tool: str) -> bool:
    """
    Asynchronously verify if `cli_tool` is installed by running its version/check command.
    Expects SUPPORTED_CLI_TOOLS[cli_tool]["check_cmd"] to be defined.
    """
    if cli_tool not in SUPPORTED_CLI_TOOLS:
        logger.warning(f"Unsupported CLI tool in startup check: {cli_tool}")
        return False

    check_cmd = SUPPORTED_CLI_TOOLS[cli_tool].get("check_cmd")
    if not check_cmd:
        logger.warning(f"No `check_cmd` configured for {cli_tool}")
        return False

    args = shlex.split(check_cmd)
    try:
        proc = await asyncio.create_subprocess_exec(*args, stdout=PIPE, stderr=PIPE)
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        logger.warning(f"Error checking {cli_tool}: {e}")
        return False


def run_startup_checks(tools: dict[str, dict]) -> dict[str, bool]:
    """
    Synchronously check installation status of each supported tool.
    Returns a mapping: { tool_name: True|False }
    """
    statuses: dict[str, bool] = {}
    for name in tools:
        try:
            ok = asyncio.run(check_cli_installed(name))
            statuses[name] = ok
            logger.info(f"{name} installed: {ok}")
        except Exception:
            statuses[name] = False
            logger.warning(f"Startup check failed for {name}")
    return statuses


# ─── 2) Command execution ──────────────────────────────────────────────────────

async def _run_shell_pipeline(command: str, timeout: float) -> tuple[int, str]:
    """
    Run a shell pipeline so pipes, redirects, etc. Just Work™.
    Returns (exit_code, combined_output).
    """
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=PIPE,
        stderr=PIPE,
        executable="/bin/bash",
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return -1, f"Command timed out after {timeout}s"

    text = out.decode("utf-8", "replace") or err.decode("utf-8", "replace")
    exit_code = proc.returncode if proc.returncode is not None else -1
    return exit_code, text


async def execute_command(command: str, timeout: Optional[int] = None) -> CommandResult:
    """
    Validate, execute (with pipes via shell), and capture output for a CLI command.
    Always returns an int exit_code and float execution_time.
    """
    # 1) Validate security and syntax
    validate_command(command)

    # 2) Determine timeout
    exec_timeout = float(timeout or DEFAULT_TIMEOUT)
    start_ts = time.time()

    # 3) Dispatch: shell for pipes, exec for simple
    if is_pipe_command(command):
        exit_code, output = await _run_shell_pipeline(command, exec_timeout)
    else:
        args = shlex.split(command)
        proc = await asyncio.create_subprocess_exec(*args, stdout=PIPE, stderr=PIPE)
        try:
            out, err = await asyncio.wait_for(proc.communicate(), exec_timeout)
            exit_code = proc.returncode or 0
            output = out.decode("utf-8", "replace") or err.decode("utf-8", "replace")
        except asyncio.TimeoutError:
            proc.kill()
            exit_code = -1
            output = f"Command timed out after {exec_timeout}s"

    duration = time.time() - start_ts
    status = "success" if exit_code == 0 else "error"

    return {
        "status": status,
        "output": output,
        "exit_code": exit_code,
        "execution_time": duration,
    }


async def get_command_help(cli_tool: str, command: Optional[str] = None) -> CommandResult:
    """
    Run `<cli_tool> [subcommand] --help`.
    """
    if cli_tool not in SUPPORTED_CLI_TOOLS:
        return {
            "status": "error",
            "output": f"{cli_tool} not supported",
            "exit_code": -1,
            "execution_time": 0.0,
        }

    help_flag = SUPPORTED_CLI_TOOLS[cli_tool]["help_flag"]
    cmd = cli_tool + (f" {command}" if command else "") + f" {help_flag}"
    return await execute_command(cmd)
