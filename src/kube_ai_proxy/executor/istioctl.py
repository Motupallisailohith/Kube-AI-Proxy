# src/kube_ai_proxy/executor/istioctl.py

"""
Executor module for Istioctl commands.
Defines describe_istioctl and execute_istioctl, to be registered centrally in mcp/__init__.py.
"""

import shlex
import asyncio
from asyncio.subprocess import PIPE

from kube_ai_proxy.config import (
    SUPPORTED_CLI_TOOLS,
    DEFAULT_TIMEOUT,
    K8S_CONTEXT,
    K8S_NAMESPACE,
)
from kube_ai_proxy.security.rbac_checker import RBACChecker
from kube_ai_proxy.tools import CommandResult, CommandHelpResult


async def describe_istioctl(command: str | None = None) -> CommandHelpResult:
    """
    Return istioctl help output for a given subcommand.
    """
    tool_cfg = SUPPORTED_CLI_TOOLS["istioctl"]
    help_flag = tool_cfg["help_flag"]

    cmd = ["istioctl"]
    if command:
        cmd.extend(shlex.split(command))
    cmd.append(help_flag)

    proc = await asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
    out, err = await proc.communicate()
    text = out.decode(errors="replace") or err.decode(errors="replace")

    return CommandHelpResult(help_text=text)


async def execute_istioctl(command: str, timeout: int | None = None) -> CommandResult:
    """
    Execute an istioctl command with RBAC enforcement.
    """
    # 1) RBAC check
    parts = shlex.split(command)
    if len(parts) > 1:
        verb = parts[1]
        resource = parts[2] if len(parts) > 2 else ""
        checker = RBACChecker(context=K8S_CONTEXT, namespace=K8S_NAMESPACE)
        allowed = await checker.can_i_istio(verb, resource)
        if not allowed:
            return CommandResult(
                status="error",
                output=f"RBAC: permission denied for {verb} {resource}",
                exit_code=1,
            )

    # 2) Execute the actual command
    exec_timeout = timeout or DEFAULT_TIMEOUT
    proc = await asyncio.create_subprocess_exec(
        *shlex.split(command), stdout=PIPE, stderr=PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), exec_timeout)
        exit_code = proc.returncode if proc.returncode is not None else -1
        output    = out.decode("utf-8", errors="replace") or err.decode("utf-8", errors="replace")
        status    = "success" if exit_code == 0 else "error"

    except asyncio.TimeoutError:
        proc.kill()
        return CommandResult(
            status="error",
            output=f"Command timed out after {exec_timeout}s",
            exit_code=-1,
        )

    return CommandResult(
        status=status,
        output=output,
        exit_code=exit_code,
    )
