# src/kube_ai_proxy/executor/helm.py

import logging
import shlex
import asyncio
from asyncio.subprocess import PIPE

from pydantic import Field
from mcp.server.fastmcp import Context

from kube_ai_proxy.cli_executor import execute_command, get_command_help
from kube_ai_proxy.tools import CommandResult, CommandHelpResult
from kube_ai_proxy.config import DEFAULT_TIMEOUT


logger = logging.getLogger(__name__)



async def describe_helm(
    command: str | None = Field(
        default=None,
        description="Specific Helm subcommand to get help for (e.g., 'list')",
    ),
    ctx: Context | None = None,
) -> CommandHelpResult:
    """
    Fetch Helm help text for the given subcommand.
    Returns a CommandHelpResult(help_text, status).
    """
    if ctx:
        await ctx.info(f"Fetching Helm help for '{command or 'general usage'}'")
    # Delegate to our helper
    cmd_help = await get_command_help("helm", command)
    # get_command_help returns a CommandResult; but for help we want CommandHelpResult
    # so if get_command_help returned a status != success, propagate
    if isinstance(cmd_help, dict) and cmd_help.get("status") == "error":
        return CommandHelpResult(
            help_text=cmd_help.get("output", ""),
            status="error",
        )

    # Otherwise it's success—its "output" holds the help text
    return CommandHelpResult(
        help_text=cmd_help["output"],
        status="success",
    )


async def execute_helm(
    command: str = Field(
        description="Complete Helm command to execute (including any pipes and flags)"
    ),
    timeout: int | None = Field(
        default=None,
        description="Maximum execution time in seconds (default: uses DEFAULT_TIMEOUT)",
    ),
    ctx: Context | None = None,
) -> CommandResult:
    """
    Execute Helm commands with validation, piping, timeouts, and proper error handling.
    """
    # Prepend "helm" if missing
    cmd_str = command.strip()
    if not cmd_str.startswith("helm"):
        cmd_str = f"helm {cmd_str}"

    if ctx:
        is_pipe = "|" in cmd_str
        await ctx.info(f"Executing{' piped' if is_pipe else ''} Helm command")

    exec_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    # Delegate to shared executor
    result = await execute_command(cmd_str, exec_timeout)
    return result
